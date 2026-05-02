import time
import random
from web3 import Web3
from core.shared import CHAIN_LITVM, short, rpc_call, LG, LR, LY

ROUTER_CA = Web3.to_checksum_address("0x35e8FE95948E1F589751121085c044C6094d993b")

WLTC_TOKEN = Web3.to_checksum_address("0xeb29947d9c1cd59af2b413b47505bf89a47be0d4")

SWAP_TARGETS = {
    "cnip": {
        "token": Web3.to_checksum_address("0xe620955450d97ddad261abf355a7a17f58d2ffb2"),
        "pool":  Web3.to_checksum_address("0xcd47c26cab66852596a3252eb1498f2b955d7cfd"),
        "label": "cNIP",
    },
    "dcat": {
        "token": Web3.to_checksum_address("0xca118cd143ca92bd9505e9bce3f5eb1552c81012"),
        "pool":  Web3.to_checksum_address("0x4450305e295b08671c11ad8623d6367986e8a1f4"),
        "label": "DCAT",
    },
}

FACTORY_CA = Web3.to_checksum_address("0xe8adcf45c359eb63aaf0e0a129463600151a0291")


def _get_min_amount_out(w3, pool_addr, amount_in_wei):
    try:
        result = rpc_call(lambda: w3.eth.call({"to": pool_addr, "data": "0x0902f1ac"}))
        r0 = int.from_bytes(result[0:32], "big")
        r1 = int.from_bytes(result[32:64], "big")
        amount_with_fee = amount_in_wei * 997
        numerator       = amount_with_fee * r1
        denominator     = r0 * 1000 + amount_with_fee
        estimated_out   = numerator // denominator
        return int(estimated_out * 990 // 1000)
    except Exception:
        return 1


def _build_swap_calldata(token_out_addr, min_amount_out, recipient, deadline):
    selector = bytes.fromhex("7ff36ab5")
    min_out  = min_amount_out.to_bytes(32, "big")
    offset   = (128).to_bytes(32, "big")
    recip    = bytes.fromhex("000000000000000000000000" + recipient.lower()[2:])
    dl       = deadline.to_bytes(32, "big")
    length   = (2).to_bytes(32, "big")
    wltc     = bytes.fromhex("000000000000000000000000" + WLTC_TOKEN.lower()[2:])
    token    = bytes.fromhex("000000000000000000000000" + token_out_addr.lower()[2:])
    raw = selector + min_out + offset + recip + dl + length + wltc + token
    return "0x" + raw.hex()


def _do_single_swap(w3, account, target, amount_wei):
    addr  = account.address
    label = target["label"]
    try:
        min_out  = _get_min_amount_out(w3, target["pool"], amount_wei)
        deadline = int(time.time()) + 600
        calldata = _build_swap_calldata(target["token"], min_out, addr, deadline)

        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       ROUTER_CA,
            "data":     calldata,
            "value":    amount_wei,
            "nonce":    nonce,
            "chainId":  CHAIN_LITVM,
            "gasPrice": gas_price,
        }
        gas       = rpc_call(lambda: w3.eth.estimate_gas(tx))
        tx["gas"] = int(gas * 1.2)
        signed    = account.sign_transaction(tx)
        tx_hash   = rpc_call(lambda: w3.eth.send_raw_transaction(signed.raw_transaction))
        h = tx_hash.hex()
        if not h.startswith("0x"):
            h = "0x" + h
        amt_eth = Web3.from_wei(amount_wei, "ether")
        LG(f"[{short(addr)}] Drunken Cats swap {amt_eth:.6f} zkLTC to {label}: {h}")
        return h
    except Exception as e:
        LR(f"[{short(addr)}] Drunken Cats swap to {label} failed: {type(e).__name__}: {e}")
        return None


def run_drunken_cats_swap(w3, accounts_map, cfg):
    any_enabled = any(cfg.get(k, {}).get("enable", False) for k in SWAP_TARGETS)
    if not any_enabled:
        LY("Drunken Cats disabled, skipping.")
        return

    LY("Drunken Cats: Swap zkLTC")

    for key, target in SWAP_TARGETS.items():
        cs = cfg.get(key, {})
        if not cs.get("enable", False):
            continue

        min_eth = cs.get("min_amount_eth", 0.0001)
        max_eth = cs.get("max_amount_eth", 0.0002)
        min_cnt = cs.get("min_count", 1)
        max_cnt = cs.get("max_count", 3)
        label   = target["label"]

        for addr, account in accounts_map.items():
            try:
                balance = rpc_call(lambda: w3.eth.get_balance(addr))
            except Exception:
                LR(f"[{short(addr)}] Failed to fetch balance for {label}, skipping.")
                continue

            min_swap_wei = Web3.to_wei(min_eth, "ether")
            if balance <= min_swap_wei:
                LR(f"[{short(addr)}] Insufficient balance for {label} swap, skipping.")
                continue

            count = random.randint(min_cnt, max_cnt)
            LY(f"[{short(addr)}] Swapping to {label} x{count}")

            for _ in range(count):
                try:
                    balance = rpc_call(lambda: w3.eth.get_balance(addr))
                except Exception:
                    break
                if balance <= min_swap_wei:
                    LR(f"[{short(addr)}] Insufficient balance remaining, stopping {label} swap.")
                    break
                amount_wei = Web3.to_wei(random.uniform(min_eth, max_eth), "ether")
                if amount_wei > int(balance * 0.8):
                    amount_wei = int(balance * 0.5)
                _do_single_swap(w3, account, target, amount_wei)
                time.sleep(2)