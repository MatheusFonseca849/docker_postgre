"""
Fix malformed reduced CSVs.
The original reducao.py used pd.read_csv() without sep=';',
so each row became a single quoted column. This script
reads that broken format and writes proper semicolon-delimited CSVs.
"""

import csv

def fix_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f_in:
        # Read as comma-separated (default) — each row is a single column
        reader = csv.reader(f_in, delimiter=',')
        rows = [row[0] for row in reader]  # extract the single column value

    with open(output_path, 'w', encoding='utf-8', newline='') as f_out:
        for row in rows:
            f_out.write(row + '\n')

    print(f"Fixed: {output_path} ({len(rows) - 1} data rows)")

fix_csv('./Importacoes_reduzidos.csv', './Importacoes_reduzidos.csv')
print("Done!")
