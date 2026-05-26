import pandas as pd
from sklearn.model_selection import train_test_split

arquivo = "./EXP_2025.csv"

# 1. Ler o CSV
df = pd.read_csv(arquivo, sep=';')

print("Linhas originais:", len(df))

# 2. Remover linhas com valores vazios (NaN)
df = df.dropna()

print("Após remover vazios:", len(df))

# 3. Garantir que ainda temos mais de 200k linhas
if len(df) < 200000:
    raise ValueError("Dataset ficou menor que 200k após limpeza.")

# 4. Reduzir usando train_test_split
df_reduzido, _ = train_test_split(
    df,
    train_size=200000,
    random_state=42,
    shuffle=True
)

print("Linhas finais:", len(df_reduzido))

# 5. Salvar novo CSV
df_reduzido.to_csv("Exportacoes_reduzidos.csv", index=False, sep=';')

print("Arquivo reduzido salvo com sucesso!")