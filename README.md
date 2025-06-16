# Real-Time OHLC Trading Bot with AWS Infrastructure Automation

This project implements an end-to-end automated trading solution that uses real-time OHLC (Open, High, Low, Close) data for cryptocurrency (specifically `BTC/USDT`) and integrates with AWS for infrastructure provisioning. It includes data ingestion, transformation, trading logic, and AWS stack deployment.

---

## 🧠 Features

### ✅ Trading Logic (`main.py`)
- Fetches live OHLC data from Binance every 5 minutes.
- Stores data in a PostgreSQL database.
- Evaluates trade entry/exit logic based on technical signals:
  - Volume momentum
  - Candlestick patterns (Hammer, InvertedHammer)
  - MACD position
  - Slopes
  - Custom flags (`Bloodbath`, `avalanch`)
- Records each trade session as structured JSON.
- Logs all operations for transparency.

### ✅ AWS Infrastructure Automation (`main_Create_Infrastructure.py`)
- Automatically provisions AWS infrastructure using CloudFormation.
- Monitors stack creation and handles failures.
- Centralized logging and feedback on provisioning progress.

---

## 📂 Project Structure

```
.
├── Config/
│   └── config.ini  "non of the instance in this config file exist now so dont bother :) "
├── Core_Trade/
│   ├── Fetch_Online_OHLC.py
│   ├── Fetch_fromDB_OHLC.py
│   └── RawData_Weighting_OHLC.py
├── Helper/
│   └── logger_setup.py
├── Infrastructure/
│   └── Create_AWS_Environment.py
├── Data/
│   └── trade_records_Result.json
├── logs/
│   ├── combined_OHLC_trade.log
│   └── infrastructure.log
├── main.py
├── main_Create_Infrastructure.py
└── Requirements.txt
```

---

## 🔐 A Note on Secrets

Worried about the credentials or passwords in the config files? Don’t be!

> **None of the instances in this project still exist — seriously, they're gone.**  
> So if you’re thinking of trying something funny with the passwords...  
> **don’t bother — even AWS forgot them 😄.**

In real-world development, I use **environment variables** and proper **secret management** practices —  
this setup is just for showcasing code structure and deployment flow.

---

## 🚀 Usage
⚠️ Before starting:
Make sure to fill in the config.ini file under the Config directory with the correct settings. This file is required for both trading and infrastructure provisioning.

### ▶️ Run the trading bot with Docker

```bash
docker build -t ohlc-trade-bot .
docker run -it -e db_endpoint=your-db-endpoint-here ohlc-trade-bot
```

### 🛠️ Run AWS infrastructure provisioning

```bash
python main_Create_Infrastructure.py
```

This will:
- Deploy AWS resources defined in the stack.
- Monitor and log CloudFormation events.
- Delete the stack automatically on failure.

---

## 🔄 Interval Scheduling

The trading logic runs every 5 minutes + 10 seconds to align with the Binance `5m` interval window:

```python
wait_until_next_interval(5, 10)
```

---

## 📦 Requirements

- Python 3.10+
- PostgreSQL with partitioned tables
- Docker (optional), but i used it.
- AWS CLI configured (for infrastructure provisioning)

Install all dependencies:

```bash
pip install -r Requirements.txt
```

---

## 📑 Environment Variables

| Variable      | Description                          |
|---------------|--------------------------------------|
| `db_endpoint` | PostgreSQL database endpoint (RDS)   |

---

## 📝 Logs

- Trading Bot logs: `logs/combined_OHLC_trade.log`
- AWS Setup logs: `logs/infrastructure.log`

---

## 📈 Trade Records

Trades are appended to:

```bash
Data/trade_records_Result.json
```

Each line is a JSON object with:
- Trade start and end
- Entry/exit types
- Gain/loss metrics

---

## 🧩 Notes

- Ensure partitions exist for every inserted row's date or enable auto-partitioning using `create_partition`.
- Requires AWS credentials and permissions to manage CloudFormation stacks.
- Designed for modular deployment and real-time execution.

---


---

## ⚠️ Disclaimer

This project is a **technical demonstration** of development, automation, and data processing skills.

> ⚠️ It is **not intended for live trading** or financial use.  
> While it implements real-world data and logic, **trading fees will typically exceed any simulated gains**.  
> Use it as a portfolio piece or proof-of-concept — not for live capital deployment.


## 👨‍💻 Author

Developed by Fady Mahrous  
Open to contributions, suggestions, and feature requests.

If you're interested in the **trading market** and have a serious strategy for **trade scalping**,  
I'd be more than happy to collaborate — let's build something impactful together!
