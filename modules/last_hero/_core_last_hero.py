import os
import json
import time
from datetime import datetime, timezone, timedelta
from web3 import Web3
from core.shared import CHAIN_LITVM, short, rpc_call, LG, LR, LY

LAST_HERO_CONTRACT = Web3.to_checksum_address("0x5C8c991E75c44E008b6D5798650187BB87Ef8F45")
LAST_HERO_VALUE    = 0x2386f26fc10000
LAST_HERO_INPUT    = "0xedca914c"

INFO_FILE = os.path.join("modules", "last_hero", "information.json")


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


def _is_eligible(record):
    next_ts = record.get("next_buy_timestamp")
    if next_ts is None:
        return True
    return datetime.now(timezone.utc).timestamp() >= next_ts


def _send_tx(w3, account):
    addr = account.address
    try:
        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       LAST_HERO_CONTRACT,
            "value":    LAST_HERO_VALUE,
            "data":     LAST_HERO_INPUT,
            "nonce":    nonce,
            "chainId":  CHAIN_LITVM,
            "gasPrice": gas_price,
        }
        gas       = rpc_call(lambda: w3.eth.estimate_gas(tx))
        tx["gas"] = int(gas * 1.2)
        signed    = account.sign_transaction(tx)
        tx_hash   = rpc_call(lambda: w3.eth.send_raw_transaction(signed.raw_transaction))
        tx_hex    = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        LG(f"[{short(addr)}] Last Hero buyTicket: {tx_hex}")
        return tx_hex
    except Exception as e:
        LR(f"[{short(addr)}] Last Hero buyTicket failed: {type(e).__name__}: {e}")
        return None


def run_last_hero(w3, accounts_map, cfg):
    enabled = cfg.get("enable", False)

    if not enabled:
        LY("Last Hero disabled, skipping.")
        return

    LY("Last Hero: Buy Daily Ticket")
    info = _load_info()

    for addr, account in accounts_map.items():
        addr_lower = addr.lower()
        record     = info.get(addr_lower, {})
        ts         = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        if not _is_eligible(record):
            next_dt  = datetime.fromtimestamp(record["next_buy_timestamp"], tz=timezone.utc)
            next_str = next_dt.strftime("%d-%m-%Y %H:%M:%S UTC")
            LG(f"[{short(addr)}] Last Hero ticket already bought today")
            continue

        tx_hex = _send_tx(w3, account)
        if tx_hex:
            record["address"]            = addr_lower
            record["last_buy_tx"]        = tx_hex
            record["last_buy_at"]        = ts
            record["next_buy_timestamp"] = _next_day_timestamp()
            info[addr_lower]             = record
            _save_info(info)
            time.sleep(2)
