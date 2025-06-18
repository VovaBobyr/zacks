import pandas as pd
import os
import argparse
import glob
from collections import defaultdict

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
    file_list = sorted(glob.glob("rank_1_*.xls*"))
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
    df_result.to_excel(output_file, index=False)
    print(f"✅ Output written to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Compare VGM Scores across Excel files.")
    parser.add_argument('-vgmscore_filter', type=str, help='Optional filter: e.g. A,B,C')
    parser.add_argument('-output_file', type=str, default='vgm_score_comparison.xlsx', help='Output Excel file name')

    args = parser.parse_args()
    compare_excel_files(args.vgmscore_filter, args.output_file)

if __name__ == "__main__":
    main()