import os
import math
import requests
from flask import Flask, request, jsonify
from embit.transaction import Transaction, TransactionInput, TransactionOutput
from embit.psbt import PSBT
from embit.script import address_to_scriptpubkey, Script

app = Flask(__name__)

# ───────── Configuration (via environment variables) ─────────
INDEXER_API_KEY  = os.getenv("INDEXER_API_KEY")
INDEXER_BASE     = os.getenv(
    "INDEXER_BASE",
    "https://open-api.unisat.io/v1/indexer/inscription/info/"
)
MIN_UTXO_VALUE   = int(os.getenv("MIN_UTXO_VALUE", "330"))
DEFAULT_FLAT_FEE = int(os.getenv("DEFAULT_FLAT_FEE", "200"))
SKIP_INSCRIPTIONS = os.getenv("SKIP_INSCRIPTIONS", "false").lower() == "true"
SKIP_546_UTXOS    = os.getenv("SKIP_546_UTXOS", "false").lower() == "true"


@app.route("/create_psbt", methods=["POST"])
def create_psbt():
    try:
        data = request.get_json() or {}

        # ───── Optionally fetch inscription UTXO ─────
        if data.get("inscriptionId") and not data.get("utxos"):
            if not INDEXER_API_KEY:
                return jsonify({"error": "Missing INDEXER_API_KEY env var"}), 500
            try:
                hdr  = {"Authorization": f"Bearer {INDEXER_API_KEY}"}
                resp = requests.get(f"{INDEXER_BASE}{data['inscriptionId']}", headers=hdr)
                resp.raise_for_status()
                ut = resp.json()["data"]["utxo"]
                data.setdefault("utxos", []).insert(0, {
                    "txid": ut["txid"],
                    "vout": ut["vout"],
                    "value": ut["satoshi"],
                    "scriptPubKey": ut["scriptPk"],
                    "inscriptions": ut.get("inscriptions", [])
                })
            except Exception as e:
                return jsonify({"error": f"Indexer fetch failed: {e}"}), 500

        utxos     = data.get("utxos", [])
        outputs   = data.get("outputs", [])
        flat_fee  = data.get("fee")
        fee_rate  = data.get("fee_rate")

        if not utxos or not outputs:
            return jsonify({"error": "utxos and outputs are required"}), 400

        # ───── Filter / normalise UTXOs ─────
        candidates = []
        for u in utxos:
            sat = u.get("value", u.get("satoshi", 0))
            spk = u.get("scriptPubKey") or u.get("scriptPk")
            if not u.get("txid") or spk is None:
                continue
            if SKIP_INSCRIPTIONS and u.get("inscriptions"):
                continue
            if SKIP_546_UTXOS and sat == 546:
                continue
            if sat < MIN_UTXO_VALUE:
                continue
            candidates.append({
                "txid": u["txid"],
                "vout": u["vout"],
                "satoshi": sat,
                "scriptPubKey": spk
            })

        if not candidates:
            return jsonify({"error": "No UTXOs meet filter requirements"}), 400

        # ───── Greedy UTXO selection ─────
        total_out = sum(o.get("amount", 0) for o in outputs)
        sorted_utxos = sorted(candidates, key=lambda x: x["satoshi"], reverse=True)
        selected, acc = [], 0
        for u in sorted_utxos:
            selected.append(u)
            acc += u["satoshi"]
            if acc >= total_out:
                break
        if acc < total_out:
            return jsonify({"error": "Insufficient funds"}), 400

        # ───── Build inputs & base outputs ─────
        txins  = [TransactionInput(bytes.fromhex(u["txid"]), u["vout"]) for u in selected]
        txouts = [
            TransactionOutput(o["amount"], address_to_scriptpubkey(o["address"]))
            for o in outputs
        ]

        # ───── Accurate fee calculation ─────
        if fee_rate is not None:
            # helper: estimate vbytes for current tx layout
            def estimate_vsize(n_in, outs):
                v_overhead = 10                        # version/lock/varints
                v_in       = 68                        # P2WPKH input
                v_outs     = 0
                for addr in outs:
                    if addr.startswith("bc1p"):        # assume Taproot
                        v_outs += 43
                    else:                              # assume P2WPKH
                        v_outs += 31
                return v_overhead + n_in * v_in + v_outs

            # first estimate without change
            vsize = estimate_vsize(len(txins), [o["address"] for o in outputs])
            fee   = math.ceil(float(fee_rate) * vsize)

            # compute change and see if it is worth adding
            change = acc - total_out - fee
            if change >= MIN_UTXO_VALUE:
                vsize += 31                            # add one P2WPKH change output
                fee    = math.ceil(float(fee_rate) * vsize)
                change = acc - total_out - fee         # recalc after fee bump
                if change < MIN_UTXO_VALUE:            # still dust ➜ drop change
                    change = 0
                    vsize -= 31
                    fee    = math.ceil(float(fee_rate) * vsize)
        else:
            fee    = int(flat_fee) if flat_fee is not None else DEFAULT_FLAT_FEE
            change = acc - total_out - fee

        # ───── Append change output if any ─────
        if change > 0:
            spk_bytes = bytes.fromhex(selected[0]["scriptPubKey"])
            txouts.append(TransactionOutput(change, Script(spk_bytes)))

        # ───── Wrap into PSBT ─────
        tx   = Transaction(vin=txins, vout=txouts)
        psbt = PSBT(tx)
        for i, u in enumerate(selected):
            spk_bytes = bytes.fromhex(u["scriptPubKey"])
            psbt.inputs[i].witness_utxo = TransactionOutput(u["satoshi"], Script(spk_bytes))

        # ───── Response ─────
        response = {
            "psbt": psbt.to_string(),
            "fee": fee,
            "change": change,
            "inputs_used": len(selected)
        }
        if fee_rate is not None:
            response.update({"fee_rate": float(fee_rate), "vsize": vsize})

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Error creating PSBT: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ───────── Stand-alone runner (for dev) ─────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
