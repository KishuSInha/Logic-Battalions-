import pandas as pd
import re

class SchemaDetector:
    """
    Intelligent Schema Detection Engine v2.0.
    Uses confidence-weighted keyword analysis and data pattern recognition
    to identify (Payer, Receiver, Amount) columns in diverse datasets.
    """

    def __init__(self):
        # HIGH CONFIDENCE KEYWORDS
        self.PAYER_PRIMARY = ["payer", "from", "debtor", "who_paid", "paid_by", "sender", "origin", "source"]
        self.PAYER_SECONDARY = ["nameorig", "user_id", "customer", "acc_from", "client"]
        
        self.RECEIVER_PRIMARY = ["receiver", "to", "creditor", "owed_to", "payee", "destination", "target", "beneficiary"]
        self.RECEIVER_SECONDARY = ["namedest", "merchant", "category", "description", "item", "product", "purpose", "vendor"]
        
        self.AMOUNT_PRIMARY = ["amount", "amt", "sum", "total", "value", "cost", "price", "net"]
        self.AMOUNT_SECONDARY = ["spent", "payment", "balance", "transaction_amount", "volume", "val"]

    def infer_schema(self, df: pd.DataFrame):
        column_scores = {col: {"payer": 0, "receiver": 0, "amount": 0} for col in df.columns}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            series = df[col]
            scores = column_scores[col]
            
            # --- 1. Keyword Scoring with Weights ---
            # Payer
            for k in self.PAYER_PRIMARY:
                if k == col_lower: scores["payer"] += 60
                elif k in col_lower: scores["payer"] += 40
            for k in self.PAYER_SECONDARY:
                if k in col_lower: scores["payer"] += 25

            # Receiver
            for k in self.RECEIVER_PRIMARY:
                if k == col_lower: scores["receiver"] += 60
                elif k in col_lower: scores["receiver"] += 40
            for k in self.RECEIVER_SECONDARY:
                if k in col_lower: scores["receiver"] += 25

            # Amount
            for k in self.AMOUNT_PRIMARY:
                if k == col_lower: scores["amount"] += 70
                elif k in col_lower: scores["amount"] += 50
            for k in self.AMOUNT_SECONDARY:
                if k in col_lower: scores["amount"] += 30

            # --- 2. Data Pattern Scoring ---
            # Amount detection (Numeric priority)
            if pd.api.types.is_numeric_dtype(series):
                scores["amount"] += 35
                # Numeric columns could also be IDs
                scores["payer"] += 5
                scores["receiver"] += 5
                # Likely amount if values vary and include decimals
                if not series.empty:
                    if (series % 1 > 0).any(): scores["amount"] += 20
                    if series.min() >= 0: scores["amount"] += 10
            
            # String identification (Payer/Receiver priority)
            elif pd.api.types.is_object_dtype(series):
                sample = series.dropna().astype(str)
                if not sample.empty:
                    val_len = sample.str.len().mean()
                    # Short strings are more likely to be names or categories
                    if val_len < 40: 
                        scores["payer"] += 20
                        scores["receiver"] += 20
                    
                    uniques = series.nunique()
                    if uniques > 1:
                        scores["payer"] += 10
                        scores["receiver"] += 10
                        
                    # Check for currency symbols in string columns (often amounts stored as text)
                    if sample.str.contains(r'[\$\€\£\¥]', regex=True).any():
                        scores["amount"] += 40

        # --- 3. Best Column Selection (with collision avoidance) ---
        # 1st Priority: Amount (highest confidence usually)
        amount_col = self._pick_best(column_scores, "amount", threshold=40)
        
        # Prevent collisions
        for col in column_scores:
            if col == amount_col:
                column_scores[col]["payer"] = -500
                column_scores[col]["receiver"] = -500

        # 2nd Priority: Payer
        payer_col = self._pick_best(column_scores, "payer", threshold=30)
        if payer_col:
             for col in column_scores:
                 if col == payer_col:
                     column_scores[col]["receiver"] = -500

        # 3rd Priority: Receiver
        receiver_col = self._pick_best(column_scores, "receiver", threshold=30)

        detected = {
            "payer": payer_col,
            "receiver": receiver_col,
            "amount": amount_col
        }

        # --- 4. Structural Logic (The "Blind Guess" Fallback) ---
        # If we found an amount but missing either payer or receiver, 
        # and it's a small dataset, we "blindly" guess based on available columns.
        if detected["amount"] and (not detected["payer"] or not detected["receiver"]):
            remaining_cols = [c for c in df.columns if c != detected["amount"] and c != detected["payer"] and c != detected["receiver"]]
            
            # Fill Payer first if missing
            if not detected["payer"] and remaining_cols:
                # Pick the one with highest potential "payer" score even if below threshold
                fallback_payer = self._pick_best(column_scores, "payer", threshold=0, exclude=[detected["amount"], detected["receiver"]])
                if fallback_payer:
                    detected["payer"] = fallback_payer
                    remaining_cols.remove(fallback_payer)
            
            # Fill Receiver if missing
            if not detected["receiver"] and remaining_cols:
                fallback_receiver = self._pick_best(column_scores, "receiver", threshold=0, exclude=[detected["amount"], detected["payer"]])
                if fallback_receiver:
                    detected["receiver"] = fallback_receiver

        # --- 5. Special Case: Single User Expenses ---

        return detected

    def _pick_best(self, scores_map, key, threshold=25, exclude=None):
        if exclude is None: exclude = []
        best_col = None
        max_score = threshold
        for col, scores in scores_map.items():
            if col in exclude: continue
            if scores[key] > max_score:
                max_score = scores[key]
                best_col = col
        return best_col
