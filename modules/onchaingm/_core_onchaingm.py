import os
import json
import time
from datetime import datetime
from web3 import Web3
from core.shared import CHAIN_LITVM, short, rpc_call, LG, LR, LY

SAYGM_CONTRACT  = Web3.to_checksum_address("0xA0692f67ffcEd633f9c5CfAefd83FC4F21973D01")
DEPLOY_CONTRACT = Web3.to_checksum_address("0x59c27c39a126a9b5ecaddd460c230c857e1deb35")
VALUE           = 10000000000000000

INFO_FILE = os.path.join("modules", "onchaingm", "information.json")

SAYGM_INPUT  = "0x84a3bb6b000000000000000000000000000000000000000000000000000000000000000062635f6238337a73676e300b0080218021802180218021802180218021"
DEPLOY_INPUT = "0x775c300c62635f6238337a73676e300b0080218021802180218021802180218021"


def _load_info():
    if not os.path.exists(INFO_FILE):
        return {}
    with open(INFO_FILE) as f:
        return json.load(f)


def _save_info(data):
    os.makedirs(os.path.dirname(INFO_FILE), exist_ok=True)
    with open(INFO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _get_wallet_info(info, addr):
    return info.get(addr.lower(), {"saygm_done": False, "deploy_done": False})


def _check_already_done(w3, addr, contract_addr, input_data):
    try:
        w3.eth.call({
            "from":  addr,
            "to":    contract_addr,
            "value": VALUE,
            "data":  input_data,
        })
        return False
    except Exception:
        return True


def _send_tx(w3, account, to, input_data, label):
    addr = account.address
    try:
        nonce     = rpc_call(lambda: w3.eth.get_transaction_count(addr))
        gas_price = rpc_call(lambda: w3.eth.gas_price)
        tx = {
            "from":     addr,
            "to":       to,
            "value":    VALUE,
            "data":     input_data,
            "nonce":    nonce,
            "chainId":  CHAIN_LITVM,
            "gasPrice": gas_price,
        }
        gas    = rpc_call(lambda: w3.eth.estimate_gas(tx))
        tx["gas"] = int(gas * 1.2)
        signed  = account.sign_transaction(tx)
        tx_hash = rpc_call(lambda: w3.eth.send_raw_transaction(signed.raw_transaction))
        tx_hex  = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        LG(f"[{short(addr)}] {label}: {tx_hex}")
        return tx_hex
    except Exception as e:
        LR(f"[{short(addr)}] {label} failed: {type(e).__name__}")
        return None


def run_onchaingm(w3, accounts_map, cfg):
    saygm_enabled  = cfg.get("saygm", {}).get("enable", False)
    deploy_enabled = cfg.get("deploy", {}).get("enable", False)

    if not saygm_enabled and not deploy_enabled:
        LY("OnchainGM disabled, skipping.")
        return

    LY("OnchainGM: Say GM + Deploy")
    info = _load_info()

    for addr, account in accounts_map.items():
        wallet_info = _get_wallet_info(info, addr)
        addr_lower  = addr.lower()
        ts          = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        updated     = False

        if saygm_enabled:
            if wallet_info.get("saygm_done"):
                LY(f"[{short(addr)}] OnchainGM SayGM already done, skipping.")
            else:
                already = _check_already_done(w3, addr, SAYGM_CONTRACT, SAYGM_INPUT)
                if already:
                    LY(f"[{short(addr)}] OnchainGM SayGM already done on-chain (revert), marking done.")
                    wallet_info["saygm_done"] = True
                    wallet_info["saygm_at"]   = ts
                    updated = True
                else:
                    tx_hex = _send_tx(w3, account, SAYGM_CONTRACT, SAYGM_INPUT, "OnchainGM SayGM")
                    if tx_hex:
                        wallet_info["saygm_done"] = True
                        wallet_info["saygm_tx"]   = tx_hex
                        wallet_info["saygm_at"]   = ts
                        updated = True
                    time.sleep(2)

        if deploy_enabled:
            if wallet_info.get("deploy_done"):
                LY(f"[{short(addr)}] OnchainGM Deploy already done, skipping.")
            else:
                already = _check_already_done(w3, addr, DEPLOY_CONTRACT, DEPLOY_INPUT)
                if already:
                    LY(f"[{short(addr)}] OnchainGM Deploy already done on-chain (revert), marking done.")
                    wallet_info["deploy_done"] = True
                    wallet_info["deploy_at"]   = ts
                    updated = True
                else:
                    tx_hex = _send_tx(w3, account, DEPLOY_CONTRACT, DEPLOY_INPUT, "OnchainGM Deploy")
                    if tx_hex:
                        wallet_info["deploy_done"] = True
                        wallet_info["deploy_tx"]   = tx_hex
                        wallet_info["deploy_at"]   = ts
                        updated = True
                    time.sleep(2)

        if updated:
            info[addr_lower] = wallet_info
            _save_info(info)