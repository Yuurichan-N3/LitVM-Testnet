<div align="center">

<img width="100%" alt="header" src="https://capsule-render.vercel.app/api?type=waving&height=210&text=LitVM%20Testnet%20Bot&fontAlign=50&fontAlignY=36&fontSize=56&desc=ETH%20Bridge%20%7C%20Token%20Transfer%20%7C%20Auto%20Claim&descAlign=50&descAlignY=58"/>

<img alt="typing" src="https://readme-typing-svg.demolab.com?font=Inter&size=18&duration=3000&pause=650&center=true&vCenter=true&width=900&lines=Auto+ETH+Withdrawal+LitVM+%E2%86%92+Sepolia;Auto+Token+Transfer+to+Random+Addresses;Auto+Bridge+Order+Polling+%2B+Claim;Multi+Wallet+Support"/>

<p>
  <img alt="python" src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white"/>
  <img alt="network" src="https://img.shields.io/badge/Network-LitVM%20Testnet-111111"/>
  <img alt="bridge" src="https://img.shields.io/badge/Bridge-Caldera%20Metarouter-6E56CF"/>
  <img alt="multi-wallet" src="https://img.shields.io/badge/Multi--Wallet-Supported-111111"/>
  <img alt="author" src="https://img.shields.io/badge/by-Yuurisandesu-111111"/>
</p>

<p>
  <b>LitVM Testnet Bot</b> is a full automation bot for the LitVM Testnet.<br/>
  It handles ETH withdrawal via the Caldera bridge (LitVM → Sepolia), token transfers to random addresses, and automatic bridge order polling with auto-claim on Sepolia — all in one cycle.<br/>
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

```json
{
  "min_amount": 1,
  "max_amount": 1,
  "min_count": 1,
  "max_count": 1,
  "sleep_seconds": 3600,
  "min_eth_wd": 0.01,
  "max_eth_wd": 0.05,
  "enable_token_transfer": true
}
```

`min_eth_wd` and `max_eth_wd` control the random ETH amount (in ether) sent to the bridge per wallet. `min_count` and `max_count` set how many token transfer transactions run per wallet per cycle. `min_amount` and `max_amount` define the random token amount per transfer. `sleep_seconds` is the fixed delay between cycles. Set `enable_token_transfer` to `false` to skip the token transfer phase entirely.

### 3. Token Contracts (contract.json)

Fill in the token contracts you want to transfer per wallet address. Each wallet can hold one or more token entries:

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

### 🌉 Phase 1 — ETH Withdrawal via Bridge
The bot fetches a quote from the Caldera Metarouter, then sends ETH from each wallet on LitVM to the bridge withdrawal contract. The withdrawal amount is randomized within the configured `min_eth_wd` and `max_eth_wd` range. If balance is too low, the wallet is skipped. Each submitted order is saved to `order.json` for tracking.

### 🔀 Phase 2 — Token Transfer to Random Addresses
If `enable_token_transfer` is enabled, the bot reads token contracts from `contract.json` and transfers tokens from each configured wallet to randomly generated addresses. The number of transfers and the amount per transfer are both randomized within the configured ranges.

### 📡 Phase 3 — Bridge Order Polling and Auto Claim
After all wallets complete their withdrawals, the bot polls the Metarouter API every 60 seconds to check the status of each pending bridge order. When an order becomes claimable, the bot automatically submits the claim transaction on Sepolia using the same wallet. Order status is persisted in `order.json` so the bot can resume tracking across restarts.

### 👛 Multi Wallet
All three phases run for every wallet loaded from `.env`. Wallets are processed sequentially within each cycle.

### ⏱️ Auto Countdown
After all tasks complete, the bot counts down the configured `sleep_seconds` before starting the next cycle.

---

## 🗂️ File Structure

```text
LitVM-Testnet/
├── bot.py            # Main bot — bridge, token transfer, order polling
├── config.json       # Amount ranges, tx count, sleep, and feature toggles
├── contract.json     # Token contracts per wallet for transfer phase
├── order.json        # Auto-generated — tracks bridge order status per wallet
├── .env              # Wallet private keys
└── requirements.txt  # Python dependencies
```

---

## ⚠️ Disclaimer

This tool is built for educational and technical exploration purposes on testnet. Use it wisely and at your own responsibility.

---

<div align="center">
<img width="100%" alt="footer" src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer"/>
</div>