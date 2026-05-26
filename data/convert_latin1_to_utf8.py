"""
Convert LATIN1-encoded CSV files to UTF-8.
Fixes broken characters like � → África, Índia, etc.
"""

import os

def convert_to_utf8(file_path):
    temp_path = file_path + '.tmp'
    with open(file_path, 'r', encoding='latin-1') as f_in:
        content = f_in.read()
    with open(temp_path, 'w', encoding='utf-8', newline='') as f_out:
        f_out.write(content)
    os.replace(temp_path, file_path)
    print(f"Converted to UTF-8: {file_path}")

latin1_files = ['./PAIS.csv', './PAIS_BLOCO.csv']
for f in latin1_files:
    if os.path.exists(f):
        convert_to_utf8(f)

print("Done!")
