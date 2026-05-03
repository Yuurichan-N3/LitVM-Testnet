import sys
import time
from datetime import datetime
from eth_account import Account

from core.shared  import LG, LR, LY, fresh_w3, RPC_LITVM, RPC_SEPOLIA, countdown, RED, RESET, BOLD
from core.loader  import load_config, load_private_keys, load_orders, save_orders, load_contracts
from utils.banner import show_banner

from modules.caldera_liteforge import run_withdrawal, poll_orders
from modules.lester_labs       import run_token_transfer
from modules.ayni_labs          import run_wrap, run_supply
from modules.omnihub            import run_mint_nft
from modules.sweep_haus         import run_mint_sweep_haus
from modules.infinityname       import run_register_infinityname
from modules.onchaingm          import run_onchaingm
from modules.znz                import run_znz_domain, run_znz_allin
from modules.litvm_swap         import run_litvm_swap
from modules.addax              import run_addax_swap
from modules.litclinic          import run_litclinic
from modules.litlotery          import run_litlotery
from modules.drunken_cats       import run_drunken_cats_swap
from modules.onmifun            import run_onmifun
from modules.last_hero          import run_last_hero

MY_PROJECT = "LitVM Testnet"

def main():
    show_banner(MY_PROJECT)
    config = load_config()
    keys   = load_private_keys()
    if not keys:
        LR("No private keys found in .env file!")
        return
    accounts_map = {Account.from_key(pk).address: Account.from_key(pk) for pk in keys}
    cycle = 0

    while True:
        cycle += 1
        ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        LY(f"Starting cycle {cycle} at {ts}")

        w3_lit = fresh_w3(RPC_LITVM)
        w3_sep = fresh_w3(RPC_SEPOLIA)

        orders    = load_orders()
        contracts = load_contracts()
        config    = load_config()

        cfg_liteforge = config.get("caldera_liteforge", {})
        orders = run_withdrawal(w3_lit, accounts_map, cfg_liteforge, orders)

        cfg_lester = config.get("lester_labs", {})
        run_token_transfer(w3_lit, accounts_map, cfg_lester, contracts)

        cfg_ayni = config.get("ayni_labs", {})
        run_wrap(w3_lit, accounts_map, cfg_ayni.get("wrap", {}))
        run_supply(w3_lit, accounts_map, cfg_ayni.get("supply", {}))

        cfg_omnihub = config.get("omnihub", {})
        run_mint_nft(w3_lit, accounts_map, cfg_omnihub)

        cfg_sweep = config.get("sweep_haus", {})
        run_mint_sweep_haus(w3_lit, accounts_map, cfg_sweep)

        cfg_infinity = config.get("infinityname", {})
        run_register_infinityname(w3_lit, accounts_map, cfg_infinity)

        cfg_onchaingm = config.get("onchaingm", {})
        run_onchaingm(w3_lit, accounts_map, cfg_onchaingm)

        cfg_znz = config.get("znz", {})
        run_znz_domain(w3_lit, accounts_map, cfg_znz.get("domain", {}))
        run_znz_allin(w3_lit, accounts_map, cfg_znz.get("allin", {}))

        cfg_swap = config.get("litvm_swap", {})
        run_litvm_swap(w3_lit, accounts_map, cfg_swap)

        cfg_addax = config.get("addax", {})
        run_addax_swap(w3_lit, accounts_map, cfg_addax)

        cfg_litclinic = config.get("litclinic", {})
        run_litclinic(w3_lit, accounts_map, cfg_litclinic)

        cfg_litlotery = config.get("litlotery", {})
        run_litlotery(w3_lit, accounts_map, cfg_litlotery)

        cfg_drunken_cats = config.get("drunken_cats", {})
        run_drunken_cats_swap(w3_lit, accounts_map, cfg_drunken_cats)

        cfg_onmifun = config.get("onmifun", {})
        run_onmifun(w3_lit, accounts_map, cfg_onmifun)

        cfg_last_hero = config.get("last_hero", {})
        run_last_hero(w3_lit, accounts_map, cfg_last_hero)

        LY("Phase 17: Monitoring bridge orders until claimed (Caldera Liteforge)")
        max_retries = config.get("max_claim_retries", 2)
        poll_orders(accounts_map, w3_sep, max_retries)

        orders  = load_orders()
        pending = [a for a, e in orders.items() if e.get("tx_hash")]
        if pending:
            LY(f"{len(pending)} wallet(s) still have pending orders, they will be retried next cycle.")
        else:
            LY("All orders cleared. Ready for next cycle.")

        sleep_sec = config.get("sleep_seconds", 3600)
        LG(f"All tasks completed. Sleeping for {sleep_sec} seconds.")
        countdown(sleep_sec, "Next cycle in: ")
        show_banner(MY_PROJECT)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}Script stopped by user.{RESET}")
        sys.exit(0)