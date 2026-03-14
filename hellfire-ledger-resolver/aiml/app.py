import json
import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from cleaning import load_and_clean_data
from utils import generate_transactions
from optimizer import optimize_settlements

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

@app.route("/api/v1/resolve", methods=["POST"])
def resolve_ledger():
    if "file" not in request.files:
        return jsonify({"error": "No file shared in request."}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files are authorized."}), 400

    tmp_path = None # Initialize tmp_path outside try block for cleanup
    try:
        # Save to a temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        print(f"[API] Processing uploaded file: {file.filename}")
        
        # 1. Load and Clean (using Intelligent Schema Detection)
        df, amount_column = load_and_clean_data(tmp_path)
        
        # 2. Generate Transactions
        transactions = generate_transactions(df, amount_column)
        
        if not transactions:
            return jsonify({
                "error": "No valid transactions found.",
                "details": "AI could not identify payer/receiver/amount pairs."
            }), 422

        # 3. Optimize Settlements
        settlements = optimize_settlements(transactions)
        
        # Cleanup
        os.remove(tmp_path)

        # 4. Construct Structured Response
        response = {
            "metadata": {
                "filename": file.filename,
                "engine": "Hellfire Resolver v2.1"
            },
            "stats": {
                "raw_transactions": len(transactions),
                "optimized_settlements": len(settlements),
                "savings_pct": f"{((len(transactions) - len(settlements)) / len(transactions) * 100):.1f}%" if transactions else "0%"
            },
            "settlements": [s.to_dict() for s in settlements],
            "ledger": [{"from": t[0], "to": t[1], "amount": t[2]} for t in transactions],
            "visuals": _generate_visuals_data(transactions, settlements)
        }

        return jsonify(response)

    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        return jsonify({"error": str(e)}), 500

def _generate_visuals_data(transactions, settlements):
    from decimal import Decimal
    nodes = set()
    total_volume = 0
    balances = {}
    
    for p, r, amt in transactions:
        nodes.add(p)
        nodes.add(r)
        total_volume += amt
        
        # Calculate net physical balances (Debtors are negative, Creditors are positive)
        balances[p] = balances.get(p, 0.0) - float(amt)
        balances[r] = balances.get(r, 0.0) + float(amt)
        
    # Extract top 5 debtors and creditors
    debtor_list = sorted([(n, -b) for n, b in balances.items() if b < 0], key=lambda x: x[1], reverse=True)
    creditor_list = sorted([(n, b) for n, b in balances.items() if b > 0], key=lambda x: x[1], reverse=True)
    
    debtors = debtor_list[:5]
    creditors = creditor_list[:5]
    
    settled_volume = sum(s.amount for s in settlements)

    return {
        "node_count": len(nodes),
        "total_volume": float(total_volume),
        "settled_volume": float(settled_volume),
        "top_debtors": [{"name": n, "amount": float(b)} for n, b in debtors],
        "top_creditors": [{"name": n, "amount": float(b)} for n, b in creditors]
    }

if __name__ == "__main__":
    # Internal HAWKINS server start
    print("\n[HAWKINS UPLINK] API Server starting on port 5050...")
    app.run(port=5050, debug=True)