import time
import random
from web3 import Web3
from core.shared import CHAIN_LITVM, short, rpc_call, LG, LR, LY

MULTYRA_BRIDGE_CA = Web3.to_checksum_address("0x6Bb77c1f465a18Bd16686330173B32821E59FD12")
LOCK_SELECTOR = bytes.fromhex("f435f5a7")

KNOWN_ERRORS = {
    "0xbd49034f": "Bridge cooldown active or amount too low (min 0.001 zkLTC)",
}


def _decode_contract_error(error_data: str) -> str:
    if not error_data or not isinstance(error_data, str):
        return "Unknown contract error"
    selector = error_data[:10].lower()
    if selector in KNOWN_ERRORS:
        raw = error_data[10:]
        try:
            cooldown_hex = raw[:64]
            amount_hex   = raw[64:128]
            cooldown_ts  = int(cooldown_hex, 16)
            amount_wei   = int(amount_hex, 16)
            amount_eth   = Web3.from_wei(amount_wei, "ether")
            readable_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(cooldown_ts)) if cooldown_ts > 1_000_000_000 else str(cooldown_ts)
            return f"{KNOWN_ERRORS[selector]} | Cooldown until: {readable_time} | Amount sent: {amount_eth:.6f} zkLTC"
        except Exception:
            return KNOWN_ERRORS[selector]
    return f"Contract custom error [{selector}]"


def _build_lock_calldata(recipient_addr: str) -> str:
    padded = bytes.fromhex("000000000000000000000000" + recipient_addr.lower()[2:])
    return "0x" + LOCK_SELECTOR.hex() + padded.hex()


def _do_bridge(w3, account, amount_wei: int) -> str | None:
    addr = account.address
    calldata = _build_lock_calldata(addr)

    try:
        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       MULTYRA_BRIDGE_CA,
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
        LG(f"[{short(addr)}] Multyra Bridge {amt_eth:.6f} zkLTC Sepolia : {h}")
        return h

    except Exception as e:
        err_msg = str(e)
        if "ContractCustomError" in type(e).__name__ or "ContractCustomError" in err_msg:
            try:
                import re
                hex_match = re.search(r"0x[0-9a-fA-F]+", err_msg)
                raw_hex = hex_match.group(0) if hex_match else err_msg
                decoded = _decode_contract_error(raw_hex)
                LR(f"[{short(addr)}] Multyra Bridge failed -> {decoded}")
            except Exception:
                LR(f"[{short(addr)}] Multyra Bridge failed -> Contract rejected the transaction")
        elif "insufficient funds" in err_msg.lower():
            LR(f"[{short(addr)}] Multyra Bridge failed -> Insufficient funds for gas + amount")
        elif "nonce" in err_msg.lower():
            LR(f"[{short(addr)}] Multyra Bridge failed -> Invalid nonce, retrying next cycle")
        elif "timeout" in err_msg.lower() or "connection" in err_msg.lower():
            LR(f"[{short(addr)}] Multyra Bridge failed -> RPC connection timeout")
        else:
            LR(f"[{short(addr)}] Multyra Bridge failed -> {type(e).__name__}: {e}")
        return None


def run_multyra_bridge(w3, accounts_map, cfg: dict):
    if not cfg.get("enable", False):
        LY("Multyra Bridge disabled, skipping.")
        return

    LY("Multyra Bridge: zkLTC -> Sepolia")

    min_eth = cfg.get("min_amount_eth", 0.001)
    max_eth = cfg.get("max_amount_eth", 0.002)
    min_cnt = cfg.get("min_count", 1)
    max_cnt = cfg.get("max_count", 1)

    if min_eth < 0.001:
        LY(f"Multyra Bridge: min_amount_eth ({min_eth}) is below contract minimum, forcing to 0.001")
        min_eth = 0.001
    if max_eth < min_eth:
        max_eth = min_eth

    for addr, account in accounts_map.items():
        try:
            balance = rpc_call(lambda: w3.eth.get_balance(addr))
        except Exception:
            LR(f"[{short(addr)}] Multyra Bridge: failed to fetch balance, skipping.")
            continue

        min_bridge_wei = Web3.to_wei(min_eth, "ether")
        if balance <= min_bridge_wei:
            LR(f"[{short(addr)}] Multyra Bridge: insufficient balance (min {min_eth} zkLTC), skipping.")
            continue

        count = random.randint(min_cnt, max_cnt)
        LY(f"[{short(addr)}] Multyra Bridge x{count}")

        for i in range(count):
            try:
                balance = rpc_call(lambda: w3.eth.get_balance(addr))
            except Exception:
                break

            if balance <= min_bridge_wei:
                LR(f"[{short(addr)}] Multyra Bridge: insufficient balance remaining, stopping.")
                break

            amount_wei = Web3.to_wei(random.uniform(min_eth, max_eth), "ether")
            if amount_wei > int(balance * 0.8):
                amount_wei = int(balance * 0.5)

            _do_bridge(w3, account, amount_wei)

            if i < count - 1:
                time.sleep(2)


def run_multyra(w3, accounts_map, cfg: dict):
    run_multyra_bridge(w3, accounts_map, cfg.get("bridge", {}))