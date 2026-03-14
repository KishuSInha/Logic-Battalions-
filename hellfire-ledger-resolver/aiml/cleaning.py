import pandas as pd
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

SIMILARITY_THRESHOLD = 85

PAYER_ALIASES    = ["payer", "from", "debtor", "who_paid", "paid_by"]
RECEIVER_ALIASES = ["receiver", "to", "creditor", "owed_to", "payee"]
AMOUNT_ALIASES   = ["amount", "amt", "sum", "total", "value", "cost"]


def _find_column(df_columns, aliases):
    lower_cols = {c.strip().lower(): c for c in df_columns}
    for alias in aliases:
        if alias in lower_cols:
            return lower_cols[alias]
    return None


def _safe_str(val):
    """Convert any value to string safely; return None for NaN/null."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    return None if s.lower() in ("nan", "none", "n/a", "") else s


def _build_canonical_names(names):
    """Cluster similar names and map each variant to a canonical form."""
    clean_names = [n.title() for n in names if n]
    unique = list(dict.fromkeys(clean_names))

    canonical_map = {}
    assigned = {}

    for name in unique:
        if name in assigned:
            canonical_map[name] = assigned[name]
            continue

        if assigned:
            candidates = list(assigned.values())
            if RAPIDFUZZ_AVAILABLE:
                best_match, score, _ = process.extractOne(
                    name, candidates, scorer=fuzz.ratio
                )
            else:
                best_match = max(
                    candidates,
                    key=lambda c: SequenceMatcher(None, name.lower(), c.lower()).ratio()
                )
                score = SequenceMatcher(None, name.lower(), best_match.lower()).ratio() * 100

            if score >= SIMILARITY_THRESHOLD:
                canonical_map[name] = best_match
                assigned[name] = best_match
                continue

        canonical_map[name] = name
        assigned[name] = name

    return canonical_map


from intelligence.schema_detector import SchemaDetector

def load_and_clean_data(file_path):
    """Load from CSV and then clean."""
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: '{file_path}'")
    return clean_data_from_df(df)


def clean_data_from_df(df):
    """
    Clean an existing DataFrame using Intelligent Schema Detection.
    Handles:
      - Semantic column mapping (Payer, Receiver, Amount)
      - Synthetic data generation for Personal/Retail datasets
      - Missing/NaN names, currency cleaning, and fuzzy normalization.
    """
    # --- 1. Intelligent Schema Detection ---
    detector = SchemaDetector()
    schema = detector.infer_schema(df)
    
    # --- 2. Synthetic Data Injection ---
    if schema["payer"] == "__SYNTHETIC_USER__":
        df["payer"] = "Authorized_User"
        payer_col = "payer"
    else:
        payer_col = schema["payer"]

    receiver_col = schema["receiver"]
    amount_col = schema["amount"]

    # Basic Validation
    if not (payer_col and receiver_col and amount_col):
        missing = []
        if not payer_col: missing.append("Payer")
        if not receiver_col: missing.append("Receiver/Merchant")
        if not amount_col: missing.append("Amount")
        raise ValueError(
            f"Schema Detection Failed. Missing: {', '.join(missing)}\n"
            f"Detected: Payer->{payer_col}, Receiver->{receiver_col}, Amount->{amount_col}"
        )

    print(f"[cleaning] Intelligent Mapping: {payer_col} → {receiver_col} (Value: {amount_col})")

    # Standardize names for internal processing
    df = df.rename(columns={
        payer_col:    "payer",
        receiver_col: "receiver",
        amount_col:   "amount"
    })

    # --- 3. Data Cleansing ---
    # Drop rows with missing names
    df["payer"]    = df["payer"].apply(_safe_str)
    df["receiver"] = df["receiver"].apply(_safe_str)
    df = df.dropna(subset=["payer", "receiver"])
    
    # Amount cleaning (strip $, commas, €, £, ¥ and handle scientific notation)
    def _parse_amount(val):
        if pd.isna(val): return None
        s = str(val).strip().lower()
        # Remove currency symbols and common non-numeric chars
        clean_s = re.sub(r'[^\d\.\-\+eE]', '', s)
        try:
            return float(clean_s)
        except (ValueError, TypeError):
            return None

    import re
    df["amount"] = df["amount"].apply(_parse_amount)
    
    df = df.dropna(subset=["amount"])
    df = df[df["amount"] > 0]

    # Remove duplicates
    df = df.drop_duplicates(subset=["payer", "receiver", "amount"])

    # --- 4. Fuzzy Name Normalization ---
    # Merge "mike" and "Mike H." - skip if too many unique entities (performance guard)
    all_names_raw = list(df["payer"]) + list(df["receiver"])
    unique_names = list(set(n for n in all_names_raw if n))
    
    if len(unique_names) > 2500:
        print(f"[cleaning] Large dataset detected ({len(unique_names)} entities). Skipping fuzzy normalization to maintain performance.")
        # Just title case them as a basic cleanup
        df["payer"]    = df["payer"].str.title()
        df["receiver"] = df["receiver"].str.title()
    else:
        canonical_map = _build_canonical_names(unique_names)
        def normalize(name):
            s = _safe_str(name)
            if not s: return "Unknown"
            key = s.title()
            return canonical_map.get(key, key)
        
        df["payer"]    = df["payer"].apply(normalize)
        df["receiver"] = df["receiver"].apply(normalize)

    # --- 5. Drop self-payments ---
    df = df[df["payer"] != df["receiver"]]
    
    df = df.reset_index(drop=True)
    print(f"[cleaning] Ready: {len(df)} valid transactions.")
    return df, "amount"