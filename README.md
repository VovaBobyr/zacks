# 📊 VGM Score Comparison Tool

This Python script compares **VGM Scores** across multiple Excel files following the naming pattern `rank_1_*.xls*`. It consolidates data into a single Excel output, showing which symbols appeared in which files along with their corresponding VGM Score.

---

## 🚀 Features

- Automatically detects and processes all Excel files like `rank_1_2025_06_13.xlsx`, `rank_1_2025_06_14.xlsx`, etc.
- Extracts and compares the **VGM Score** (`A`, `B`, `C`, `D`, `E`, `F`) for each symbol across files.
- Adds `Company` and `Industry` columns per symbol — intelligently gathered from any available file.
- Optional filtering to only include symbols with specific VGM Scores (`A`, `B`, etc.).
- Outputs a clean Excel file with merged results.

---

## 📁 Input Format

Each Excel file should have the following columns:

- `Symbol` *(required)*
- `VGM Score` *(required)*
- `Company` *(optional)*
- `Industry` *(optional)*

---

## 📤 Output Format

| Symbol | Company | Industry | rank_1_2025_06_13 | rank_1_2025_06_14 | rank_1_2025_06_15 |
|--------|---------|----------|------------------|------------------|------------------|
| AAPL   | Apple   | Tech     | A                | B                |                  |
| TSLA   | Tesla   | Auto     |                  | A                | A                |

If a symbol is missing in a given file, the corresponding cell is left empty.

---

## ⚙️ Requirements

Install required Python packages:

```bash
pip install pandas openpyxl
```

## 🧪 Usage

1. Place all your Excel files in the working directory and ensure they follow the naming pattern `rank_1_*.xls*`.

2. Run the script:

```bash
python main.py
```

3. Optional: filter by VGM Score (e.g., only include symbols rated A or B in any file):

```bash
python main.py -vgmscore_filter A,B
```

4. Optional: specify custom output filename:
```bash
python main.py -vgmscore_filter A,B -output_file vgm_filtered_AB.xlsx
```

5. Optional: run without any filters and output to a custom file:

```bash
python main.py -output_file full_comparison.xlsx
```

---

## 📦 Example Directory
\

├── main.py

├── rank_1_2025_06_13.xlsx

├── rank_1_2025_06_14.xlsx

├── rank_1_2025_06_15.xlsx

└── vgm_score_comparison.xlsx


---

## 🛠️ TODO / Improvements

- [ ] Highlight highest VGM Score per row
- [ ] Option to export to CSV
- [ ] Add CLI flags for sorting or grouping

---

## 🧠 Author

Built by a data-driven DevOps engineer with a passion for finance and automation.  
Feel free to contribute, fork, or provide suggestions.
