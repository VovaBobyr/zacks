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
    file_list = sorted(glob.glob("backend/excels/rank_1_*.xls*"))
    if not file_list:
        print("❌ No files matching pattern 'rank_1_*.xls*' found in current directory.")
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
    output_file = os.path.join("backend/output", output_file)
    df_result.to_excel(output_file, index=False)
    print(f"✅ Output written to: {output_file}")

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
    file_list = sorted(glob.glob("backend/excels/rank_1_*.xls*"))
    if not file_list:
        print("❌ No files matching pattern 'rank_1_*.xls*' found in current directory.")
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
    output_file = os.path.join("backend/output", output_file)
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_result.to_excel(writer, index=False, header=False, startrow=2)
        ws = writer.sheets['Sheet1']
        # Write header rows manually
        for col_num, value in enumerate(header_row_1, 1):
            ws.cell(row=1, column=col_num, value=value)
        for col_num, value in enumerate(header_row_2, 1):
            ws.cell(row=2, column=col_num, value=value)
    print(f"✅ Accumulated output written to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Compare or accumulate VGM Scores across Excel files.")
    parser.add_argument('-vgmscore_filter', type=str, help='Optional filter: e.g. A,B,C')
    parser.add_argument('-output_file', type=str, default='vgm_score_comparison.xlsx', help='Output Excel file name')
    parser.add_argument('-accumulate_scores', action='store_true', help='Accumulate all scores for all symbols across files')

    args = parser.parse_args()
    if args.accumulate_scores:
        accumulate_scores_across_files(args.output_file)
    else:
        compare_excel_files(args.vgmscore_filter, args.output_file)

if __name__ == "__main__":
    main()