# -----------------------------------------------------------------------------
# Example usage:
#   python main.py
#   python main.py -vgmscore_filter A,B,C
#   python main.py -output_file my_output.xlsx
#   python main.py -vgmscore_filter A,B -output_file filtered.xlsx
#   python main.py -accumulate_scores -output_file accumulated.xlsx+
#   python backend/main.py -accumulate_scores -output_file output/accumulated.xlsx
# -----------------------------------------------------------------------------

import pandas as pd
import os
import argparse
import glob
from collections import defaultdict
import requests
import time
import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
import threading

# Define a consistent data directory. This will be the mount point for our persistent disk.
DATA_DIR = os.environ.get('ZACKS_DATA_DIR', 'backend/data')
EXCELS_DIR = os.path.join(DATA_DIR, 'excels')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

def make_unique_headers(headers):
    """Ensures all column headers are unique by appending a counter to duplicates."""
    seen = {}
    unique_headers = []
    for header in headers:
        original_header = header
        if header in seen:
            seen[header] += 1
            header = f"{header}_{seen[original_header]}"
        else:
            seen[header] = 1
        unique_headers.append(header)
    return unique_headers

def run_daily_tasks():
    """Wrapper function to run all daily file generation tasks."""
    print("--- Running daily tasks ---")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    print("--- Generating accumulated.xlsx ---")
    accumulate_scores_across_files("accumulated.xlsx")
    
    print("--- Generating vgm_filtered_A.xlsx ---")
    compare_excel_files("A", "vgm_filtered_A.xlsx")

    print("--- Generating vgm_filtered_AB.xlsx ---")
    compare_excel_files("A,B", "vgm_filtered_AB.xlsx")
    
    print("--- Daily tasks finished ---")


def create_app():
    # Ensure data directories exist on startup
    os.makedirs(EXCELS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file:
            filename = secure_filename(file.filename)
            if "rank_1_" in filename and filename.endswith('.xlsx'):
                save_path = os.path.join(EXCELS_DIR, filename)
                file.save(save_path)
                
                # Run processing in a background thread to avoid blocking the request
                thread = threading.Thread(target=run_daily_tasks)
                thread.daemon = True
                thread.start()

                return jsonify({"message": f"File {filename} uploaded successfully. Reports are being regenerated in the background."}), 202
            else:
                return jsonify({"error": "Invalid filename. Must start with 'rank_1_' and be an .xlsx file."}), 400

    @app.route('/api/files', methods=['GET'])
    def list_files():
        try:
            if not os.path.exists(OUTPUT_DIR) or not os.listdir(OUTPUT_DIR):
                run_daily_tasks()

            files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.xlsx')]
            return jsonify(files)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/file/<filename>', methods=['GET'])
    def get_file_data(filename):
        try:
            file_path = os.path.join(OUTPUT_DIR, filename)
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found"}), 404

            df = pd.read_excel(file_path, header=None)

            # Check if there are merged header rows
            if df.shape[0] > 1 and df.iloc[1].isnull().sum() > df.iloc[0].isnull().sum():
                 # Multi-level header
                header1 = df.iloc[0].ffill()
                header2 = df.iloc[1]
                headers = [f"{h1}_{h2}" if pd.notna(h2) and str(h2).strip() else str(h1) for h1, h2 in zip(header1, header2)]
                df.columns = make_unique_headers(headers)
                data_df = df.iloc[2:]
            else:
                # Single header
                headers = df.iloc[0]
                df.columns = headers
                data_df = df.iloc[1:]

            # Sanitize the data: replace NaN with empty strings for JSON compatibility
            data_df = data_df.fillna('')
            data = data_df.to_dict(orient='records')
            return jsonify({"filename": filename, "headers": list(df.columns), "data": data})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Schedule the daily tasks
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_daily_tasks, 'cron', hour=11, minute=0)
    scheduler.start()
    
    return app

def collect_symbol_data(file_list):
    symbol_data = defaultdict(dict)
    symbol_metadata = {}

    for file_path in file_list:
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            continue

        has_company = 'Company' in df.columns
        has_industry = 'Industry' in df.columns

        for _, row in df.iterrows():
            symbol = row.get('Symbol')
            if pd.isna(symbol):
                continue

            symbol = str(symbol).strip()
            vgm_score = str(row.get('VGM Score', '')).strip().upper()

            symbol_data[symbol][file_name] = vgm_score

            if symbol not in symbol_metadata:
                company = str(row.get('Company', '')).strip() if has_company else ''
                industry = str(row.get('Industry', '')).strip() if has_industry else ''
                if company or industry:
                    symbol_metadata[symbol] = {
                        'Company': company,
                        'Industry': industry
                    }

    return symbol_data, symbol_metadata

def compare_excel_files(vgmscore_filter=None, output_file='vgm_score_comparison.xlsx'):
    file_list = sorted(glob.glob(os.path.join(EXCELS_DIR, "rank_1_*.xls*")))
    if not file_list:
        print("❌ No files matching pattern 'rank_1_*.xls*' found in excels directory.")
        return

    print(f"ℹ️ Found {len(file_list)} file(s):")
    for f in file_list:
        print(f" - {f}")

    symbol_data, symbol_metadata = collect_symbol_data(file_list)
    all_symbols = set(symbol_data.keys())

    if vgmscore_filter:
        allowed_scores = set(score.strip().upper() for score in vgmscore_filter.split(','))
        filtered_symbols = {
            symbol for symbol, scores in symbol_data.items()
            if any(score in allowed_scores for score in scores.values())
        }
        all_symbols = filtered_symbols

    file_columns = [os.path.splitext(os.path.basename(f))[0] for f in file_list]
    result_data = {
        'Symbol': [],
        'Company': [],
        'Industry': [],
    }
    for col in file_columns:
        result_data[col] = []

    for symbol in sorted(all_symbols):
        result_data['Symbol'].append(symbol)
        result_data['Company'].append(symbol_metadata.get(symbol, {}).get('Company', ''))
        result_data['Industry'].append(symbol_metadata.get(symbol, {}).get('Industry', ''))
        for file_col in file_columns:
            result_data[file_col].append(symbol_data[symbol].get(file_col, ''))

    df_result = pd.DataFrame(result_data)
    output_path = os.path.join(OUTPUT_DIR, output_file)
    df_result.to_excel(output_path, index=False)
    print(f"✅ Output written to: {output_path}")

def get_finnhub_rank(symbol, api_key):
    """Fetch the most recent rating for a symbol from Finnhub.io."""
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={api_key}"
    for attempt in range(3):  # Retry up to 3 times if rate limited
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 429:
                print(f"Rate limit hit, waiting 60 seconds before retrying for {symbol}...")
                time.sleep(60)
                continue
            response.raise_for_status()
            data = response.json()
            time.sleep(1)  # Respect Finnhub's free tier rate limit
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get('rating', '') or str(data[0].get('strongBuy', ''))
            else:
                return ''
        except Exception as e:
            print(f"Warning: Could not fetch Finnhub rank for {symbol}: {e}")
            return ''
    return ''

def get_yahoo_rank(symbol):
    """Fetch the most recent recommendation trend from Yahoo Finance using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        recommendations = ticker.recommendations
        if recommendations is not None and not recommendations.empty:
            latest = recommendations.tail(1)
            # If the expected columns are present, summarize them
            cols = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
            if all(col in latest.columns for col in cols):
                values = [f"{col}:{int(latest[col].values[0])}" for col in cols]
                return ", ".join(values)
            # Fallback: just show the whole row as string
            return latest.to_string(index=False)
        else:
            return ''
    except Exception as e:
        print(f"Warning: Could not fetch Yahoo rank for {symbol}: {e}")
        return ''

def accumulate_scores_across_files(output_file='accumulated_scores.xlsx'):
    API_KEY = 'd1apbjhr01qjhvtqhljgd1apbjhr01qjhvtqhlk0'
    file_list = sorted(glob.glob(os.path.join(EXCELS_DIR, "rank_1_*.xls*")))
    if not file_list:
        print("❌ No files matching pattern 'rank_1_*.xls*' found in excels directory.")
        return

    print(f"ℹ️ Found {len(file_list)} file(s):")
    for f in file_list:
        print(f" - {f}")

    # Read all files and accumulate data
    all_symbols = set()
    file_data = []
    for idx, file_path in enumerate(file_list):
        df = pd.read_excel(file_path)
        df['__file__'] = os.path.basename(file_path)
        file_data.append(df)
        all_symbols.update(df['Symbol'].dropna().astype(str).str.strip())

    all_symbols = sorted(all_symbols)
    # Use the first file for Company/Industry info
    first_df = file_data[0]
    symbol_info = {}
    for _, row in first_df.iterrows():
        symbol = str(row['Symbol']).strip()
        symbol_info[symbol] = {
            'Company': row.get('Company', ''),
            'Industry': row.get('Industry', '')
        }

    file_score_cols = ['Value Score', 'Growth Score', 'Momentum Score', 'VGM Score']
    file_names = [
        os.path.splitext(os.path.basename(f))[0].replace("rank_1_", "")
        for f in file_list
    ]

    # Prepare two header rows
    header_row_1 = ['Symbol', 'Company', 'Industry', 'Rank', 'Yahoo Rank']
    header_row_2 = ['', '', '', '', '']
    for fname in file_names:
        for col in file_score_cols:
            header_row_1.append(fname)
            header_row_2.append(col)

    # Build data rows, now with Rank and Yahoo Rank
    data_rows = []
    total_symbols = len(all_symbols)
    for idx, symbol in enumerate(all_symbols, 1):
        print(f"Fetching ratings for {symbol}... ({idx} of {total_symbols})", flush=True)
        finnhub_rank = get_finnhub_rank(symbol, API_KEY)
        yahoo_rank = get_yahoo_rank(symbol)
        row = [
            symbol,
            symbol_info.get(symbol, {}).get('Company', ''),
            symbol_info.get(symbol, {}).get('Industry', ''),
            finnhub_rank,
            yahoo_rank
        ]
        for df in file_data:
            df_symbol = df[df['Symbol'].astype(str).str.strip() == symbol]
            if not df_symbol.empty:
                for col in file_score_cols:
                    row.append(df_symbol.iloc[0].get(col, ''))
            else:
                row.extend([''] * len(file_score_cols))
        data_rows.append(row)

    df_result = pd.DataFrame(data_rows)
    output_path = os.path.join(OUTPUT_DIR, output_file)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_result.to_excel(writer, index=False, header=False, startrow=2)
        ws = writer.sheets['Sheet1']
        # Write header rows manually
        for col_num, value in enumerate(header_row_1, 1):
            ws.cell(row=1, column=col_num, value=value)
        for col_num, value in enumerate(header_row_2, 1):
            ws.cell(row=2, column=col_num, value=value)
    print(f"✅ Accumulated output written to: {output_path}")

def main():
    # The script is now primarily a web server, so we can simplify the main function.
    # Gunicorn will be used in production to call create_app()
    print("Starting Flask app...")
    app = create_app()
    app.run(debug=True, port=5001, use_reloader=False) # use_reloader=False is important for scheduler

if __name__ == "__main__":
    main()