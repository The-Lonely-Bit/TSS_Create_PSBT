# TSS_Create_PSBT

A simple, open-source API to help you create and send Bitcoin payments using PSBTs (Partially Signed Bitcoin Transactions). This project is designed for both beginners and advanced users who want to automate or scale Bitcoin payments for orders, e-commerce, or any use case.

---

## 🚀 Features
- **Create PSBTs** for Bitcoin transactions
- **Configurable fees** (flat or fee rate)
- **Bulk and single transaction support**
- **Multi-output PSBTs**
- **Easy to run locally or in production**
- **Secure by design** (no private keys handled)

---

## 🛠️ Quick Start (For Beginners)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/TSS_SendBitcoin.git
cd TSS_SendBitcoin
```

### 2. Set Up Python Environment
Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root (or set them in your shell):
```bash
# .env
INDEXER_API_KEY="your_api_key"  # Only needed if you use inscriptionId lookups
INDEXER_BASE="https://open-api-fractal.unisat.io/v1/indexer/inscription/info/"
MIN_UTXO_VALUE="330"
DEFAULT_FLAT_FEE="200"
SKIP_INSCRIPTIONS="false"
SKIP_546_UTXOS="false"
PORT="8000"
```

### 5. Run the Server
```bash
python3 app.py
```
The server will start at `http://localhost:8000` by default.

---

## 🧪 How to Test the API

### A. Test with `curl` (Command Line)
#### **Single Transaction Example**
```bash
curl -X POST http://localhost:8000/create_psbt \
  -H 'Content-Type: application/json' \
  -d '{
        "utxos": [{"txid":"1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef","vout":0,"value":10000,"scriptPubKey":"0014abcdef1234567890abcdef1234567890abcdef12"}],
        "outputs": [{"address":"bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh","amount":9000}],
        "fee":200
      }'
```

#### **Single PSBT with Multiple Outputs Example**
```bash
curl -X POST http://localhost:8000/create_psbt \
  -H 'Content-Type: application/json' \
  -d '{
        "utxos": [{"txid":"1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef","vout":0,"value":10000,"scriptPubKey":"0014abcdef1234567890abcdef1234567890abcdef12"}],
        "outputs": [
          {"address":"bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh","amount":5000},
          {"address":"bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh","amount":3000}
        ],
        "fee":200
      }'
```

#### **Batch/Bulk Transactions**
Prepare a file (e.g. `bulk_requests.json`) with multiple requests (see `examples/bulk_requests.json`):
```json
[
  { "utxos": [...], "outputs": [...], "fee": 200 },
  { "utxos": [...], "outputs": [...], "fee_rate": 1.5 }
]
```
Then loop through them:
```bash
cat bulk_requests.json | jq -c '.[]' | while read req; do
  curl -X POST http://localhost:8000/create_psbt \
    -H 'Content-Type: application/json' \
    -d "$req"
done
```

### B. Test with Postman (GUI)
1. Open Postman
2. Create a new POST request to `http://localhost:8000/create_psbt`
3. Set body to `raw` and `JSON`, then paste your request data
4. Click **Send** and view the response

### C. Run Automated Tests
```bash
python3 -m pytest tests/
```
All tests should pass if your setup is correct.

---

## 📝 API Reference

### `POST /create_psbt`
- **utxos**: List of UTXOs to spend (each with `txid`, `vout`, `value`/`satoshi`, `scriptPubKey`)
- **outputs**: List of outputs (each with `address`, `amount`)
- **fee**: (optional) Flat fee in sats
- **fee_rate**: (optional) Fee rate in sats/vbyte
- **inscriptionId**: (optional) If provided, fetches the UTXO for this inscription

**Returns:**
- `psbt`: The base64-encoded PSBT string
- `fee`: Fee used
- `change`: Change output (if any)
- `inputs_used`: Number of UTXOs used
- `fee_rate` and `vsize` if fee_rate was used

---

## 🔒 Security Best Practices
- **Never expose private keys** to this server
- **Use HTTPS** in production
- **Protect your API keys** (do not commit them)
- **Validate all input** if you modify the code
- **Run behind a firewall** if on a public server

---

## 🧑‍💻 For Developers: How to Build On Top
- Fork or clone this repo
- Add new endpoints or logic in `app.py`
- Write new tests in `tests/`
- Use the PSBT output with your own signing wallet or service

---

## 📂 Project Structure
```
TSS_SendBitcoin/
├── app.py                  # Main Flask API
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
├── tests/                  # Automated tests
│   └── test_psbt_creator.py
├── examples/
│   └── bulk_requests.json  # Example batch requests
└── .gitignore
```

---

## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📜 License
MIT — see [LICENSE](LICENSE)

---

## 💬 Need Help?
- Open an issue on GitHub
- Or start a discussion!

---

**TSS_SendBitcoin makes Bitcoin payments programmable, scalable, and easy for everyone.** 
