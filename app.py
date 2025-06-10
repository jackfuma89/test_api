import os
import re
import logging
from functools import lru_cache
from typing import List, Dict, Any, Tuple

import pandas as pd
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

# ── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH = os.getenv("CSV_PATH", "nlpearl_test_db.csv")
CSV_SEP = ";"
PHONE_COL = os.getenv("PHONE_COL", "phone_number")
CONTRACT_COL = os.getenv("CONTRACT_COL", "contract_code")
DEFAULT_FIELDS = os.getenv(
    "DEFAULT_FIELDS",
    "contract_code,platform,status,average_arpu,service_type,activation_date"
).split(",")

# ── LOGGING ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── PHONE NORMALIZATION ──────────────────────────────────────────────────────
PHONE_REGEX = re.compile(r"^[\d\+]+$")  # basic check: digits and plus

def normalize_phone(phone: str) -> str:
    """
    Normalizza il numero di telefono in formato +<country><number>
    Supporta input con 00, + o senza prefisso.
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not PHONE_REGEX.match(phone):
        return phone  # lascia com'è, fallback

    if phone.startswith("00"):
        return "+" + phone[2:]
    if phone.startswith("+"):
        return phone
    if phone.startswith("39"):
        return "+" + phone
    # Fallback generico: aggiungi +
    return "+" + phone

# ── DATA LOADING ───────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_data() -> Tuple[pd.DataFrame, Dict[str, int], Dict[str, int]]:
    """
    Load and cache the CSV data and build lookup indices with normalized phone numbers.
    """
    try:
        df = pd.read_csv(CSV_PATH, sep=CSV_SEP, dtype=str).fillna("")

        # Normalize phone numbers in CSV
        if PHONE_COL in df.columns:
            df[PHONE_COL] = df[PHONE_COL].apply(normalize_phone)

        # Validate required columns exist
        required_cols = [PHONE_COL, CONTRACT_COL] + DEFAULT_FIELDS
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Overwrite row 50 (index 49) safely if exists
        if len(df) > 49:
            df.loc[49, [CONTRACT_COL, PHONE_COL]] = ["1234566789", normalize_phone("+393478933194")]

        # Build lookup indices
        phone_idx = {val: idx for idx, val in enumerate(df[PHONE_COL])}
        contract_idx = {val: idx for idx, val in enumerate(df[CONTRACT_COL])}

        return df, phone_idx, contract_idx
    except FileNotFoundError:
        raise RuntimeError(f"CSV file not found at {CSV_PATH}")
    except pd.errors.EmptyDataError:
        raise RuntimeError(f"CSV file at {CSV_PATH} is empty")
    except Exception as e:
        raise RuntimeError(f"Error loading data: {str(e)}")

# Load data at startup
try:
    df, phone_idx, contract_idx = load_data()
except Exception as e:
    logger.error(f"Failed to load data: {e}")
    raise


def slice_row(rec: pd.Series, cols: List[str]) -> Dict[str, Any]:
    """Pick only the requested columns that actually exist in the record."""
    return {c: rec[c] for c in cols if c in rec}

# ── FLASK APP ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Per demo, consenti tutte le origini

# Logging requests
@app.before_request
def log_request():
    logger.info(f"Request: {request.method} {request.url}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'detail': error.description}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'detail': 'Internal server error'}), 500

@app.route('/customer/phone/<phone>', methods=['GET'])
def get_by_phone(phone: str):
    # Normalize input phone
    normalized_phone = normalize_phone(phone)

    if normalized_phone not in phone_idx:
        abort(404, description=f"Phone number not found: {normalized_phone}")

    try:
        rec = df.loc[phone_idx[normalized_phone]]
        fields = request.args.get('fields')
        wanted = fields.split(",") if fields else DEFAULT_FIELDS
        return jsonify({'data': slice_row(rec, wanted)})
    except Exception as e:
        logger.error(f"Error retrieving data for {normalized_phone}: {e}")
        abort(500, description="Internal error retrieving phone data")

@app.route('/customer/contract/<contract_code>', methods=['GET'])
def get_by_contract(contract_code: str):
    if not contract_code:
        abort(400, description="Contract code is required")
    if contract_code not in contract_idx:
        abort(404, description="Contract code not found")
    try:
        rec = df.loc[contract_idx[contract_code]]
        fields = request.args.get('fields')
        wanted = fields.split(",") if fields else DEFAULT_FIELDS
        return jsonify({'data': slice_row(rec, wanted)})
    except Exception as e:
        logger.error(f"Error retrieving data for contract {contract_code}: {e}")
        abort(500, description="Internal error retrieving contract data")
@app.route('/customer/numTec/<contract_code>', methods=['GET'])
def get_num_tec(contract_code: str):
    if contract_code not in contract_idx:
        abort(404, description="Contract code not found")
    try:
        rec = df.loc[contract_idx[contract_code]]
        value = int(rec.get("num_contact_tec", 0))
        return jsonify({'num_contact_tec': value})
    except Exception as e:
        logger.error(f"Error retrieving numTec for {contract_code}: {e}")
        abort(500, description="Internal error retrieving numTec")

@app.route('/customer/numAmm/<contract_code>', methods=['GET'])
def get_num_amm(contract_code: str):
    if contract_code not in contract_idx:
        abort(404, description="Contract code not found")
    try:
        rec = df.loc[contract_idx[contract_code]]
        value = int(rec.get("num_contact_amm", 0))
        return jsonify({'num_contact_amm': value})
    except Exception as e:
        logger.error(f"Error retrieving numAmm for {contract_code}: {e}")
        abort(500, description="Internal error retrieving numAmm")

@app.route('/customer/wifiActive/<contract_code>', methods=['GET'])
def get_wifi_active(contract_code: str):
    if contract_code not in contract_idx:
        abort(404, description="Contract code not found")
    try:
        rec = df.loc[contract_idx[contract_code]]
        value = int(rec.get("bb_active", 0))
        return jsonify({'bb_active': value})
    except Exception as e:
        logger.error(f"Error retrieving wifiActive for {contract_code}: {e}")
        abort(500, description="Internal error retrieving wifiActive")

@app.route('/customer/userName/<contract_code>', methods=['GET'])
def get_user_name(contract_code: str):
    if contract_code not in contract_idx:
        abort(404, description="Contract code not found")
    try:
        rec = df.loc[contract_idx[contract_code]]
        value = rec.get("user_name", "")
        return jsonify({'user_name': value})
    except Exception as e:
        logger.error(f"Error retrieving userName for {contract_code}: {e}")
        abort(500, description="Internal error retrieving userName")


@app.route('/phone/numTec/<phone>', methods=['GET'])
def get_num_tec_by_phone(phone: str):
    normalized_phone = normalize_phone(phone)
    if normalized_phone not in phone_idx:
        abort(404, description="Phone number not found")
    try:
        rec = df.loc[phone_idx[normalized_phone]]
        value = int(rec.get("num_contact_tec", 0))
        return jsonify({'num_contact_tec': value})
    except Exception as e:
        logger.error(f"Error retrieving numTec for phone {normalized_phone}: {e}")
        abort(500, description="Internal error retrieving numTec")

@app.route('/phone/numAmm/<phone>', methods=['GET'])
def get_num_amm_by_phone(phone: str):
    normalized_phone = normalize_phone(phone)
    if normalized_phone not in phone_idx:
        abort(404, description="Phone number not found")
    try:
        rec = df.loc[phone_idx[normalized_phone]]
        value = int(rec.get("num_contact_amm", 0))
        return jsonify({'num_contact_amm': value})
    except Exception as e:
        logger.error(f"Error retrieving numAmm for phone {normalized_phone}: {e}")
        abort(500, description="Internal error retrieving numAmm")

@app.route('/phone/wifiActive/<phone>', methods=['GET'])
def get_wifi_active_by_phone(phone: str):
    normalized_phone = normalize_phone(phone)
    if normalized_phone not in phone_idx:
        abort(404, description="Phone number not found")
    try:
        rec = df.loc[phone_idx[normalized_phone]]
        value = int(rec.get("bb_active", 0))
        return jsonify({'bb_active': value})
    except Exception as e:
        logger.error(f"Error retrieving wifiActive for phone {normalized_phone}: {e}")
        abort(500, description="Internal error retrieving wifiActive")

@app.route('/phone/userName/<phone>', methods=['GET'])
def get_user_name_by_phone(phone: str):
    normalized_phone = normalize_phone(phone)
    if normalized_phone not in phone_idx:
        abort(404, description="Phone number not found")
    try:
        rec = df.loc[phone_idx[normalized_phone]]
        value = rec.get("user_name", "")
        return jsonify({'user_name': value})
    except Exception as e:
        logger.error(f"Error retrieving userName for phone {normalized_phone}: {e}")
        abort(500, description="Internal error retrieving userName")



@app.route('/debug/phones', methods=['GET'])
def list_phones():
    return jsonify(list(phone_idx.keys())[:20])

@app.route('/')
def home():
    return 'API is running', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
