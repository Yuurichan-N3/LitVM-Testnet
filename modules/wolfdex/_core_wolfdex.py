import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
from web3 import Web3
from core.shared import CHAIN_LITVM, short, rpc_call, LG, LR, LY

ROUTER_CA  = Web3.to_checksum_address("0xd28967D75750f477E450Df81C73f34E2713B86B4")
FAUCET_CA  = Web3.to_checksum_address("0x5E0B3DE95ACeeF2d46CEAF3e287370D23d90B603")
STAKE_CA   = Web3.to_checksum_address("0x28c7167ebF6112D5B01396eEeDFe8F990Fcb54bb")
WZKLTC_CA  = Web3.to_checksum_address("0x4fd3765cde8d1d2be4edbaa03940afc56794c304")

TOKENS = {
    "bnb": {
        "token":         Web3.to_checksum_address("0x31351646e2c5479A30f846dFa4297E9Dbe189a63"),
        "pool":          Web3.to_checksum_address("0x02580ba4b52ca612f1625a77127309245a697c25"),
        "stake_pool_id": 1,
        "label":         "BNB",
    },
    "monad": {
        "token":         Web3.to_checksum_address("0xa12c18847c41ece267155ffae112b8951abbca1c"),
        "pool":          Web3.to_checksum_address("0x151e0ba48026c74a133b123775b53aa8d96ebf1e"),
        "stake_pool_id": 2,
        "label":         "Monad",
    },
    "hype": {
        "token":         Web3.to_checksum_address("0xbb3b44eb672650fb4a1cf6d9dc5d3b7494f333ab"),
        "pool":          Web3.to_checksum_address("0x183d349f1cedb3f709985ef8810314571848cb2f"),
        "stake_pool_id": 3,
        "label":         "HYPE",
    },
}

INFO_FILE = os.path.join("modules", "wolfdex", "information.json")

ERC20_APPROVE_SIG   = bytes.fromhex("095ea7b3")
ERC20_ALLOWANCE_SIG = bytes.fromhex("dd62ed3e")
ERC20_BALANCE_SIG   = bytes.fromhex("70a08231")


def _load_info():
    if not os.path.exists(INFO_FILE):
        return {}
    with open(INFO_FILE) as f:
        return json.load(f)


def _save_info(data):
    os.makedirs(os.path.dirname(INFO_FILE), exist_ok=True)
    with open(INFO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _next_day_timestamp():
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def _is_faucet_eligible(record):
    next_ts = record.get("next_claim_timestamp")
    if next_ts is None:
        return True
    return datetime.now(timezone.utc).timestamp() >= next_ts


def _get_reserves(w3, pool_addr):
    try:
        result = rpc_call(lambda: w3.eth.call({"to": pool_addr, "data": "0x0902f1ac"}))
        r0 = int.from_bytes(result[0:32], "big")
        r1 = int.from_bytes(result[32:64], "big")
        return r0, r1
    except Exception:
        return 0, 0


def _get_token0(w3, pool_addr):
    try:
        result = rpc_call(lambda: w3.eth.call({"to": pool_addr, "data": "0x0dfe1681"}))
        return Web3.to_checksum_address("0x" + result[12:32].hex())
    except Exception:
        return None


def _get_min_amount_out(w3, pool_addr, amount_in_wei):
    try:
        r0, r1 = _get_reserves(w3, pool_addr)
        if r0 == 0:
            return 1
        amount_with_fee = amount_in_wei * 997
        numerator       = amount_with_fee * r1
        denominator     = r0 * 1000 + amount_with_fee
        estimated_out   = numerator // denominator
        return int(estimated_out * 990 // 1000)
    except Exception:
        return 1


def _erc20_balance(w3, token_addr, owner_addr):
    try:
        data = ERC20_BALANCE_SIG + bytes.fromhex("000000000000000000000000" + owner_addr.lower()[2:])
        result = rpc_call(lambda: w3.eth.call({"to": token_addr, "data": "0x" + data.hex()}))
        return int.from_bytes(result[:32], "big")
    except Exception:
        return 0


def _erc20_allowance(w3, token_addr, owner_addr, spender_addr):
    try:
        data = (ERC20_ALLOWANCE_SIG
                + bytes.fromhex("000000000000000000000000" + owner_addr.lower()[2:])
                + bytes.fromhex("000000000000000000000000" + spender_addr.lower()[2:]))
        result = rpc_call(lambda: w3.eth.call({"to": token_addr, "data": "0x" + data.hex()}))
        return int.from_bytes(result[:32], "big")
    except Exception:
        return 0


def _erc20_approve(w3, account, token_addr, spender_addr, amount):
    addr = account.address
    try:
        data = (ERC20_APPROVE_SIG
                + bytes.fromhex("000000000000000000000000" + spender_addr.lower()[2:])
                + amount.to_bytes(32, "big"))
        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       token_addr,
            "data":     "0x" + data.hex(),
            "value":    0,
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
        LG(f"[{short(addr)}] Wolf DEX approve: {h}")
        time.sleep(3)
        return True
    except Exception as e:
        LR(f"[{short(addr)}] Wolf DEX approve failed: {type(e).__name__}")
        return False


def _ensure_allowance(w3, account, token_addr, spender_addr, amount_needed):
    addr = account.address
    allowance = _erc20_allowance(w3, token_addr, addr, spender_addr)
    if allowance >= amount_needed:
        return True
    MAX_UINT256 = 2**256 - 1
    return _erc20_approve(w3, account, token_addr, spender_addr, MAX_UINT256)


def _build_swap_calldata(token_out_addr, min_amount_out, recipient, deadline):
    selector = bytes.fromhex("7ff36ab5")
    min_out  = min_amount_out.to_bytes(32, "big")
    offset   = (128).to_bytes(32, "big")
    recip    = bytes.fromhex("000000000000000000000000" + recipient.lower()[2:])
    dl       = deadline.to_bytes(32, "big")
    length   = (2).to_bytes(32, "big")
    wzkltc   = bytes.fromhex("000000000000000000000000" + WZKLTC_CA.lower()[2:])
    token    = bytes.fromhex("000000000000000000000000" + token_out_addr.lower()[2:])
    raw = selector + min_out + offset + recip + dl + length + wzkltc + token
    return "0x" + raw.hex()


def _do_single_swap(w3, account, key, target, amount_wei):
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
        LG(f"[{short(addr)}] Wolf DEX swap {amt_eth:.6f} zkLTC to {label}: {h}")
        return h
    except Exception as e:
        LR(f"[{short(addr)}] Wolf DEX swap to {label} failed: {type(e).__name__}")
        return None


def _do_add_lp(w3, account, key, target, amount_token_wei, amount_eth_wei):
    addr  = account.address
    label = target["label"]
    try:
        # amount_token_wei sudah dihitung oleh caller berdasarkan reserves terbaru,
        # jangan recalculate lagi di sini supaya amount_token_min tidak stale.

        if not _ensure_allowance(w3, account, target["token"], ROUTER_CA, amount_token_wei):
            LR(f"[{short(addr)}] Wolf DEX addLP {label} approve failed, skipping.")
            return None

        amount_token_min = int(amount_token_wei * 900 // 1000)
        amount_eth_min   = int(amount_eth_wei * 900 // 1000)
        deadline         = int(time.time()) + 600

        selector = bytes.fromhex("f305d719")
        token    = bytes.fromhex("000000000000000000000000" + target["token"].lower()[2:])
        data = (selector
                + token
                + amount_token_wei.to_bytes(32, "big")
                + amount_token_min.to_bytes(32, "big")
                + amount_eth_min.to_bytes(32, "big")
                + bytes.fromhex("000000000000000000000000" + addr.lower()[2:])
                + deadline.to_bytes(32, "big"))

        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       ROUTER_CA,
            "data":     "0x" + data.hex(),
            "value":    amount_eth_wei,
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
        amt_eth = Web3.from_wei(amount_eth_wei, "ether")
        LG(f"[{short(addr)}] Wolf DEX add LP {label} {amt_eth:.6f} zkLTC: {h}")
        return h
    except Exception as e:
        LR(f"[{short(addr)}] Wolf DEX add LP {label} failed: {type(e).__name__}")
        return None


def _do_stake(w3, account, token_addr, pool_id, amount_wei, label):
    addr = account.address
    try:
        if not _ensure_allowance(w3, account, token_addr, STAKE_CA, amount_wei):
            LR(f"[{short(addr)}] Wolf DEX stake {label} approve failed, skipping.")
            return None

        selector = bytes.fromhex("e2bbb158")
        data = (selector
                + pool_id.to_bytes(32, "big")
                + amount_wei.to_bytes(32, "big"))

        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       STAKE_CA,
            "data":     "0x" + data.hex(),
            "value":    0,
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
        amt = Web3.from_wei(amount_wei, "ether")
        LG(f"[{short(addr)}] Wolf DEX stake {amt:.6f} {label}: {h}")
        return h
    except Exception as e:
        LR(f"[{short(addr)}] Wolf DEX stake {label} failed: {type(e).__name__}")
        return None


FAUCET_TOKENS = {
    "bnb":   {"arg": 1, "label": "BNB"},
    "monad": {"arg": 2, "label": "Monad"},
    "hype":  {"arg": 3, "label": "HYPE"},
}


def run_wolfdex_faucet(w3, accounts_map, cfg):
    if not cfg.get("enable", False):
        LY("Wolf DEX Faucet disabled, skipping.")
        return

    LY("Wolf DEX: Claim Faucet")
    info = _load_info()

    for addr, account in accounts_map.items():
        addr_lower = addr.lower()
        record     = info.get(addr_lower, {})

        for key, ft in FAUCET_TOKENS.items():
            token_record = record.get(key, {})
            label        = ft["label"]

            if not _is_faucet_eligible(token_record):
                continue

            try:
                data      = bytes.fromhex("95d4063f") + ft["arg"].to_bytes(32, "big")
                nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
                gas_price = rpc_call(lambda: w3.eth.gas_price)
                tx = {
                    "from":     addr,
                    "to":       FAUCET_CA,
                    "data":     "0x" + data.hex(),
                    "value":    0,
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

                ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                LG(f"[{short(addr)}] Wolf DEX Faucet {label} claimed: {h}")

                token_record["address"]              = addr_lower
                token_record["last_claim_tx"]        = h
                token_record["last_claim_at"]        = ts
                token_record["next_claim_timestamp"] = _next_day_timestamp()
                record[key]                          = token_record
                info[addr_lower]                     = record
                _save_info(info)
                time.sleep(2)

            except Exception as e:
                err = type(e).__name__
                if "ContractLogicError" in err or "ContractCustomError" in err:
                    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    LY(f"[{short(addr)}] Wolf DEX Faucet {label} already claimed today, recording next claim.")
                    token_record["address"]              = addr_lower
                    token_record["last_claim_at"]        = ts
                    token_record["next_claim_timestamp"] = _next_day_timestamp()
                    record[key]                          = token_record
                    info[addr_lower]                     = record
                    _save_info(info)
                else:
                    LR(f"[{short(addr)}] Wolf DEX Faucet {label} claim failed: {err} (will retry next cycle)")


def run_wolfdex_swap(w3, accounts_map, cfg):
    any_enabled = any(cfg.get(k, {}).get("enable", False) for k in TOKENS)
    if not any_enabled:
        LY("Wolf DEX Swap disabled, skipping.")
        return

    LY("Wolf DEX: Swap zkLTC")

    for key, target in TOKENS.items():
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
                LR(f"[{short(addr)}] Failed to fetch balance for swap {label}, skipping.")
                continue

            min_swap_wei = Web3.to_wei(min_eth, "ether")
            if balance <= min_swap_wei:
                LR(f"[{short(addr)}] Insufficient balance for swap {label}, skipping.")
                continue

            count = random.randint(min_cnt, max_cnt)
            LY(f"[{short(addr)}] Wolf DEX swap to {label} x{count}")

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
                _do_single_swap(w3, account, key, target, amount_wei)
                time.sleep(2)


def run_wolfdex_addlp(w3, accounts_map, cfg):
    any_enabled = any(cfg.get(k, {}).get("enable", False) for k in TOKENS)
    if not any_enabled:
        LY("Wolf DEX Add LP disabled, skipping.")
        return

    LY("Wolf DEX: Add Liquidity")

    for key, target in TOKENS.items():
        cs = cfg.get(key, {})
        if not cs.get("enable", False):
            continue

        min_eth = cs.get("min_amount_eth", 0.0001)
        max_eth = cs.get("max_amount_eth", 0.0002)
        min_cnt = cs.get("min_count", 1)
        max_cnt = cs.get("max_count", 1)
        label   = target["label"]

        for addr, account in accounts_map.items():
            try:
                balance = rpc_call(lambda: w3.eth.get_balance(addr))
            except Exception:
                LR(f"[{short(addr)}] Failed to fetch balance for addLP {label}, skipping.")
                continue

            min_eth_wei = Web3.to_wei(min_eth, "ether")
            if balance <= min_eth_wei:
                LR(f"[{short(addr)}] Insufficient balance for addLP {label}, skipping.")
                continue

            token_bal = _erc20_balance(w3, target["token"], addr)
            if token_bal == 0:
                LR(f"[{short(addr)}] No {label} token balance for addLP, skipping.")
                continue

            count = random.randint(min_cnt, max_cnt)
            LY(f"[{short(addr)}] Wolf DEX add LP {label} x{count}")

            for _ in range(count):
                try:
                    balance   = rpc_call(lambda: w3.eth.get_balance(addr))
                    token_bal = _erc20_balance(w3, target["token"], addr)
                except Exception:
                    break
                if balance <= min_eth_wei or token_bal == 0:
                    LR(f"[{short(addr)}] Insufficient balance for addLP {label}, stopping.")
                    break
                amount_eth_wei = Web3.to_wei(random.uniform(min_eth, max_eth), "ether")
                if amount_eth_wei > int(balance * 0.8):
                    amount_eth_wei = int(balance * 0.5)
                r0, r1 = _get_reserves(w3, target["pool"])
                if r0 > 0 and r1 > 0:
                    token0 = _get_token0(w3, target["pool"])
                    if token0 and token0.lower() == WZKLTC_CA.lower():
                        # token0=WZKLTC, token1=target token
                        amount_token_wei = amount_eth_wei * r1 // r0
                    else:
                        # token0=target token, token1=WZKLTC (kasus pool BNB)
                        amount_token_wei = amount_eth_wei * r0 // r1
                else:
                    amount_token_wei = int(token_bal * 0.5)
                if amount_token_wei > token_bal:
                    amount_token_wei = token_bal
                _do_add_lp(w3, account, key, target, amount_token_wei, amount_eth_wei)
                time.sleep(2)


def run_wolfdex_stake(w3, accounts_map, cfg):
    any_enabled = any(cfg.get(k, {}).get("enable", False) for k in TOKENS)
    if not any_enabled:
        LY("Wolf DEX Stake disabled, skipping.")
        return

    LY("Wolf DEX: Stake zkLTC")

    for key, target in TOKENS.items():
        cs = cfg.get(key, {})
        if not cs.get("enable", False):
            continue

        pool_id = target.get("stake_pool_id")
        if pool_id is None:
            continue

        min_eth = cs.get("min_amount_eth", 0.0001)
        max_eth = cs.get("max_amount_eth", 0.0002)
        min_cnt = cs.get("min_count", 1)
        max_cnt = cs.get("max_count", 1)
        label      = target["label"]
        token_addr = target["token"]

        for addr, account in accounts_map.items():
            try:
                token_bal = _erc20_balance(w3, token_addr, addr)
            except Exception:
                LR(f"[{short(addr)}] Failed to fetch {label} balance for stake, skipping.")
                continue

            min_stake_wei = Web3.to_wei(min_eth, "ether")
            if token_bal < min_stake_wei:
                LR(f"[{short(addr)}] Insufficient {label} balance for stake, skipping.")
                continue

            count = random.randint(min_cnt, max_cnt)
            LY(f"[{short(addr)}] Wolf DEX stake {label} x{count}")

            for _ in range(count):
                try:
                    token_bal = _erc20_balance(w3, token_addr, addr)
                except Exception:
                    break
                if token_bal < min_stake_wei:
                    LR(f"[{short(addr)}] Insufficient {label} balance remaining, stopping stake.")
                    break
                amount_wei = Web3.to_wei(random.uniform(min_eth, max_eth), "ether")
                if amount_wei > token_bal:
                    amount_wei = int(token_bal * 0.5)
                _do_stake(w3, account, token_addr, pool_id, amount_wei, label)
                time.sleep(2)


def run_wolfdex(w3, accounts_map, cfg):
    run_wolfdex_faucet(w3, accounts_map, cfg.get("faucet", {}))
    run_wolfdex_swap(w3, accounts_map, cfg.get("swap", {}))
    run_wolfdex_addlp(w3, accounts_map, cfg.get("add_lp", {}))
    run_wolfdex_stake(w3, accounts_map, cfg.get("stake", {}))