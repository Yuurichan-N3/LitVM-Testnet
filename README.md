<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=LitVM%20Testnet%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=ETH%20Bridge%20%7C%20Token%20Transfer%20%7C%20Auto%20Claim&descAlign=50&descAlignY=58"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Auto+ETH+Withdrawal+LitVM+%E2%86%92+Sepolia;Auto+Token+Transfer+to+Random+Addresses;Auto+Bridge+Order+Polling+%2B+Claim;Multi+Wallet+Support;Modular+Architecture"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white"/>
  <img alt="network" src="https://img.shields.io/badge/Network-LitVM%20Testnet-111111"/>
  <img alt="bridge" src="https://img.shields.io/badge/Bridge-Caldera%20Metarouter-6E56CF"/>
  <img alt="multi-wallet" src="https://img.shields.io/badge/Multi--Wallet-Supported-111111"/>
  <img alt="modules" src="https://img.shields.io/badge/Modules-18+-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>LitVM Testnet Bot</b> is a full automation bot for the LitVM Testnet.<br/>
  Now featuring a fully modular architecture with 13+ independent protocol modules — covering ETH bridging, token transfers, NFT minting, domain registration, DEX swaps, social interactions, and more.<br/>
  Built and distributed by <b>Yuurisandesu</b>.
</p>

</div>

---

## ⚙️ Requirements

- Python `3.10+`
- Git

---

## 🚀 Installation

**Clone the repository:**

```bash
git clone https://github.com/Yuurichan-N3/LitVM-Testnet.git
cd LitVM-Testnet
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

### 1. Private Keys (.env)

Create a `.env` file in the project root and fill in your wallet private keys:

```env
PRIVATEKEY_1=0x
PRIVATEKEY_2=0x
```

Add as many wallets as needed by incrementing the number.

### 2. Bot Settings (config.json)

Each module has its own config block inside `config.json`. Enable or disable any module independently using `"enable": true/false`. Amount ranges, transaction counts, and other parameters can be tuned per module. Refer to the default `config.json` included in the repo for the full structure.

### 3. Token Contracts (contract.json)

Fill in the token contracts for the **Lester Labs** token transfer module. Each wallet can hold one or more token entries:

```json
{
  "0xYourWalletAddress": [
    {
      "ca": "0xTokenContractAddress",
      "name": "TokenName",
      "ticker": "TKN"
    }
  ]
}
```

The wallet address key must match exactly what is loaded from your private key. The bot will read the current token balance before each transfer and skip if the balance is zero.

---

## ▶️ Running the Bot

```bash
python bot.py
```

---

## ✨ Features

The bot runs all enabled modules sequentially for every wallet in each cycle. Each module is fully independent and can be toggled on or off via `config.json`.

### 🌉 Phase 1 — Caldera Liteforge (ETH Bridge)
Fetches a quote from the Caldera Metarouter, then sends ETH from each wallet on LitVM to the bridge withdrawal contract. The withdrawal amount is randomized within the configured range. Wallets with insufficient balance are skipped. Each submitted order is saved to `order.json` for tracking.

### 🔀 Phase 2 — Lester Labs (Token Transfer)
Reads token contracts from `contract.json` and transfers tokens from each configured wallet to randomly generated addresses. The number of transfers and amount per transfer are both randomized within the configured ranges.

### 🔄 Phase 3 — Ayni Labs (Wrap & Supply)
Handles WETH wrapping and ETH supply operations. Both `wrap` and `supply` sub-modules are independently configurable with their own amount ranges and repeat counts.

### 🖼️ Phase 4 — OmniHub (NFT Mint)
Mints NFTs on the OmniHub protocol. Configurable max NFT count per wallet per cycle.

### 🧹 Phase 5 — Sweep Haus (NFT Mint)
Mints NFTs on the Sweep Haus collection. Configurable max NFT count per wallet per cycle.

### 🏷️ Phase 6 — InfinityName (Domain Registration)
Registers random domain names on the InfinityName protocol. Configurable max name count per wallet per cycle.

### 👋 Phase 7 — OnChainGM (Social)
Two sub-modules: `saygm` posts an on-chain GM message, and `deploy` deploys a contract interaction. Both can be toggled independently.

### 🌐 Phase 8 — ZNZ (Domain & All-In)
Two sub-modules: `domain` registers ZNZ domains with a configurable max per wallet, and `allin` performs a combined ZNZ interaction.

### 💱 Phase 9 — LitVM Swap (DEX)
Swaps ETH for testnet tokens on the LitVM native DEX. Supports three pairs: `BTC`, `ETH`, and `XRP` — each with independent enable toggles, amount ranges, and swap counts.

### 🔁 Phase 10 — Addax Swap (DEX)
Swaps ETH for tokens on the Addax DEX. Supports three token pairs: `YUURISAN`, `TEQOIN`, and `AUSDC` — each independently configurable.

### 🏥 Phase 11 — LitClinic (Social & Activity)
Five sub-modules: `saygm`, `saygn`, `sayhello`, `activity_counter` (with a configurable daily max), and `checkin`. Each can be toggled independently.

### 🎰 Phase 12 — LitLotery
Participates in the LitLotery on-chain lottery. Simple enable/disable toggle.

### 🐱 Phase 13 — Drunken Cats (DEX Swap)
Swaps zkLTC for tokens on the Drunken Cats DEX. Supports two pairs: `cNIP` and `DCAT` — each independently configurable with their own enable toggle, amount ranges, and swap counts. Slippage is calculated automatically from pool reserves using the constant-product formula.

### 🎮 Phase 14 — Onmifun (Swap & Buy Token)
Two sub-modules: `swap` exchanges zkLTC for `YR` token via the Onmifun swap router, and `buy_token` purchases meme tokens (`Pengu`, `Yuri`) via the Onmifun buy router. Each pair is independently configurable. The swap module handles ERC-20 approval automatically before executing.

### 🦸 Phase 15 — Last Hero (Daily Ticket)
Purchases a daily ticket on the Last Hero contract. The bot checks per wallet whether a ticket has already been bought today — if so, the wallet is skipped. Ticket status resets automatically at midnight UTC.

### 🐺 Phase 16 — Wolf DEX (Faucet, Swap, Add LP, Stake)
Four sub-modules in one: `faucet` claims daily tokens (BNB, Monad, HYPE) with per-wallet tracking to prevent double claims; `swap` exchanges zkLTC for those three tokens; `add_lp` adds liquidity to pools with automatic token ratio calculation from reserves; and `stake` stakes LP tokens to the Stake contract. All sub-modules and token pairs are independently toggleable.

### 🌉 Phase 17 — Multyra Bridge (zkLTC → Sepolia)
Bridges zkLTC to Sepolia via the Multyra bridge contract. Amount per bridge transaction is randomized within the configured range (minimum 0.001 zkLTC enforced by the contract). Includes detailed error decoding for contract-level rejections such as bridge cooldown and minimum amount errors.

### 📡 Phase 18 — Bridge Order Polling & Auto Claim
After all wallets complete their cycle, the bot polls the Metarouter API to check the status of each pending bridge order. When an order becomes claimable, the bot automatically submits the claim transaction on Sepolia. Order status is persisted in `order.json` so the bot can resume tracking across restarts. Retry count is configurable via `max_claim_retries`.

---

### 👛 Multi Wallet
All phases run for every wallet loaded from `.env`. Wallets are processed sequentially within each cycle.

### ⏱️ Auto Countdown
After all tasks complete, the bot counts down the configured `sleep_seconds` before starting the next cycle.

---

## 🗂️ File Structure

```text
LitVM-Testnet/
├── bot.py                        # Main bot entrypoint — orchestrates all modules
├── config.json                   # Per-module settings: enable toggles, amounts, counts
├── contract.json                 # Token contracts per wallet (Lester Labs)
├── order.json                    # Auto-generated — tracks bridge order status per wallet
├── .env                          # Wallet private keys
├── requirements.txt              # Python dependencies
│
├── core/
│   ├── abis.py                   # Contract ABIs
│   ├── loader.py                 # Config, keys, orders, contracts loader
│   └── shared.py                 # Shared utilities, RPC connections, logging
│
├── modules/
│   ├── caldera_liteforge/        # ETH bridge withdrawal + order claim (Caldera)
│   ├── lester_labs/              # Token transfer to random addresses
│   ├── ayni_labs/                # WETH wrap + ETH supply
│   ├── omnihub/                  # NFT mint (OmniHub)
│   ├── sweep_haus/               # NFT mint (Sweep Haus)
│   ├── infinityname/             # Domain registration (InfinityName)
│   ├── onchaingm/                # On-chain GM + contract deploy
│   ├── znz/                      # ZNZ domain registration + all-in
│   ├── litvm_swap/               # DEX swap (BTC / ETH / XRP pairs)
│   ├── addax/                    # DEX swap on Addax (YUURISAN / TEQOIN / AUSDC)
│   ├── litclinic/                # Social interactions + check-in
│   ├── litlotery/                # On-chain lottery participation
│   ├── drunken_cats/             # DEX swap zkLTC → cNIP / DCAT (Drunken Cats)
│   ├── onmifun/                  # DEX swap zkLTC → YR + buy token (PENGU / Yuri)
│   ├── last_hero/                # Daily ticket purchase with per-wallet cooldown tracking
│   ├── wolfdex/                  # Faucet + swap + add LP + stake (BNB / Monad / HYPE)
│   ├── multyra/                  # zkLTC → Sepolia bridge via Multyra contract
│   ├── arkada/                   # 🔜 Coming soon
│   ├── dappit/                   # 🔜 Coming soon
│   ├── lendvault/                # 🔜 Coming soon
│   ├── litcash/                  # 🔜 Coming soon
│   ├── liteswap/                 # 🔜 Coming soon
│   ├── penny4thots/              # 🔜 Coming soon
│   └── [more coming soon...]
│
└── utils/
    └── banner.py                 # ASCII banner display
```

---

## ⚠️ Disclaimer

This tool is built for educational and technical exploration purposes on testnet. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>