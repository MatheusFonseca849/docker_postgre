"""
ETL Script — COMEX 2025
Cleans CSV data, creates PostgreSQL tables, and loads everything.
Run: python etl.py
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import csv
import io
import os
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def get_db_config():
    """Build DB config from DATABASE_URL or individual env vars, with local fallbacks."""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        from urllib.parse import urlparse
        url = database_url.replace('postgres://', 'postgresql://', 1)
        r = urlparse(url)
        return {'host': r.hostname, 'port': r.port or 5432,
                'database': r.path.lstrip('/'), 'user': r.username, 'password': r.password}
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '5433')),
        'database': os.environ.get('DB_NAME', 'comex_db'),
        'user': os.environ.get('DB_USER', 'professor_iesb'),
        'password': os.environ.get('DB_PASSWORD', 'senha_comex'),
    }

DB_CONFIG = get_db_config()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# ---------------------------------------------------------------------------
# DDL — matches modelo_logico_apresentacao.sql (corrected for PostgreSQL)
# ---------------------------------------------------------------------------
DROP_SQL = """
DROP TABLE IF EXISTS tb_importacao CASCADE;
DROP TABLE IF EXISTS tb_exportacao CASCADE;
DROP TABLE IF EXISTS tb_pais_bloco CASCADE;
DROP TABLE IF EXISTS tb_municipio CASCADE;
DROP TABLE IF EXISTS tb_bloco CASCADE;
DROP TABLE IF EXISTS tb_pais CASCADE;
DROP TABLE IF EXISTS tb_ncm CASCADE;
DROP TABLE IF EXISTS tb_unidade CASCADE;
DROP TABLE IF EXISTS tb_estado CASCADE;
DROP TABLE IF EXISTS tb_urf CASCADE;
DROP TABLE IF EXISTS tb_via CASCADE;
"""

CREATE_SQL = """
CREATE TABLE tb_via (
    id_via INT NOT NULL,
    nome_via VARCHAR(250),
    CONSTRAINT pk_tb_via PRIMARY KEY (id_via)
);

CREATE TABLE tb_urf (
    id_urf INT NOT NULL,
    nome_urf VARCHAR(250) NOT NULL,
    CONSTRAINT pk_tb_urf PRIMARY KEY (id_urf)
);

CREATE TABLE tb_estado (
    id_estado INT NOT NULL,
    nome_estado VARCHAR(300) NOT NULL,
    sigla_estado VARCHAR(2) NOT NULL,
    nome_regiao VARCHAR(250) NOT NULL,
    CONSTRAINT pk_tb_estado PRIMARY KEY (id_estado)
);

CREATE TABLE tb_municipio (
    id_municipio INT NOT NULL,
    id_estado INT NOT NULL,
    nome_municipio VARCHAR(800) NOT NULL,
    CONSTRAINT pk_tb_municipio PRIMARY KEY (id_municipio),
    CONSTRAINT fk_tb_municipio_estado FOREIGN KEY (id_estado) REFERENCES tb_estado(id_estado)
);

CREATE TABLE tb_ncm (
    id_ncm BIGINT NOT NULL,
    nome_ncm_portugues TEXT NOT NULL,
    nome_ncm_ingles TEXT NOT NULL,
    nome_ncm_espanhol TEXT NOT NULL,
    CONSTRAINT pk_tb_ncm PRIMARY KEY (id_ncm)
);

CREATE TABLE tb_unidade (
    id_unidade INT NOT NULL,
    nome_unidade VARCHAR(300) NOT NULL,
    sigla_unidade VARCHAR(10) NOT NULL,
    CONSTRAINT pk_tb_unidade PRIMARY KEY (id_unidade)
);

CREATE TABLE tb_pais (
    id_pais INT NOT NULL,
    nome_pais_portugues VARCHAR(200) NOT NULL,
    nome_pais_ingles VARCHAR(200) NOT NULL,
    nome_pais_espanhol VARCHAR(200) NOT NULL,
    CONSTRAINT pk_tb_pais PRIMARY KEY (id_pais)
);

CREATE TABLE tb_bloco (
    id_bloco INT NOT NULL,
    nome_bloco_portugues VARCHAR(255) NOT NULL,
    nome_bloco_ingles VARCHAR(255) NOT NULL,
    nome_bloco_espanhol VARCHAR(255) NOT NULL,
    CONSTRAINT pk_tb_bloco PRIMARY KEY (id_bloco)
);

CREATE TABLE tb_pais_bloco (
    id_pais INT NOT NULL,
    id_bloco INT NOT NULL,
    CONSTRAINT pk_tb_pais_bloco PRIMARY KEY (id_pais, id_bloco),
    CONSTRAINT fk_tb_pais_bloco_pais FOREIGN KEY (id_pais) REFERENCES tb_pais(id_pais),
    CONSTRAINT fk_tb_pais_bloco_bloco FOREIGN KEY (id_bloco) REFERENCES tb_bloco(id_bloco)
);

CREATE TABLE tb_exportacao (
    id_exportacao SERIAL NOT NULL,
    id_ncm BIGINT NOT NULL,
    id_via INT NOT NULL,
    id_urf INT NOT NULL,
    id_unidade INT NOT NULL,
    id_pais INT NOT NULL,
    id_estado INT NOT NULL,
    kg_liquido BIGINT NOT NULL DEFAULT 0,
    qt_estat BIGINT NOT NULL DEFAULT 0,
    vl_fob BIGINT NOT NULL DEFAULT 0,
    ano INT NOT NULL,
    mes INT NOT NULL,
    CONSTRAINT pk_tb_exportacao PRIMARY KEY (id_exportacao),
    CONSTRAINT fk_tb_exportacao_ncm FOREIGN KEY (id_ncm) REFERENCES tb_ncm(id_ncm),
    CONSTRAINT fk_tb_exportacao_via FOREIGN KEY (id_via) REFERENCES tb_via(id_via),
    CONSTRAINT fk_tb_exportacao_urf FOREIGN KEY (id_urf) REFERENCES tb_urf(id_urf),
    CONSTRAINT fk_tb_exportacao_unidade FOREIGN KEY (id_unidade) REFERENCES tb_unidade(id_unidade),
    CONSTRAINT fk_tb_exportacao_pais FOREIGN KEY (id_pais) REFERENCES tb_pais(id_pais),
    CONSTRAINT fk_tb_exportacao_estado FOREIGN KEY (id_estado) REFERENCES tb_estado(id_estado)
);

CREATE TABLE tb_importacao (
    id_importacao SERIAL NOT NULL,
    id_ncm BIGINT NOT NULL,
    id_via INT NOT NULL,
    id_urf INT NOT NULL,
    id_unidade INT NOT NULL,
    id_pais INT NOT NULL,
    id_estado INT NOT NULL,
    kg_liquido BIGINT NOT NULL DEFAULT 0,
    qt_estat BIGINT NOT NULL DEFAULT 0,
    vl_fob BIGINT NOT NULL DEFAULT 0,
    vl_frete BIGINT NOT NULL DEFAULT 0,
    vl_seguro BIGINT NOT NULL DEFAULT 0,
    ano INT NOT NULL,
    mes INT NOT NULL,
    CONSTRAINT pk_tb_importacao PRIMARY KEY (id_importacao),
    CONSTRAINT fk_tb_importacao_ncm FOREIGN KEY (id_ncm) REFERENCES tb_ncm(id_ncm),
    CONSTRAINT fk_tb_importacao_via FOREIGN KEY (id_via) REFERENCES tb_via(id_via),
    CONSTRAINT fk_tb_importacao_urf FOREIGN KEY (id_urf) REFERENCES tb_urf(id_urf),
    CONSTRAINT fk_tb_importacao_unidade FOREIGN KEY (id_unidade) REFERENCES tb_unidade(id_unidade),
    CONSTRAINT fk_tb_importacao_pais FOREIGN KEY (id_pais) REFERENCES tb_pais(id_pais),
    CONSTRAINT fk_tb_importacao_estado FOREIGN KEY (id_estado) REFERENCES tb_estado(id_estado)
);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fix_mojibake(text):
    """Fix double-encoded text (LATIN1 bytes interpreted as UTF-8 then saved again)."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def has_mojibake(df):
    """Detect mojibake patterns in a DataFrame (e.g., 'Ã¡' instead of 'á')."""
    sample = ' '.join(df.head(50).astype(str).values.flatten())
    patterns = ['Ã¡', 'Ã©', 'Ã­', 'Ã³', 'Ãº', 'Ã£', 'Ãµ', 'Ã§', 'Ã\x89', 'Ã\xad',
                'Ã¢', 'Ãª', 'Ã®', 'Ã´', 'Ã»', 'Ã\x81', 'Ã\x93', 'Ã\x9a']
    return any(p in sample for p in patterns)


def read_csv_smart(filename):
    """Read a CSV auto-detecting encoding and handling malformed single-column files."""
    filepath = os.path.join(DATA_DIR, filename)

    # Try semicolon-separated with UTF-8, then LATIN-1
    for enc in ('utf-8', 'latin-1'):
        try:
            df = pd.read_csv(filepath, sep=';', encoding=enc, dtype=str)
            if len(df.columns) > 1:
                # Detect and fix double-encoding (mojibake)
                if enc == 'utf-8' and has_mojibake(df):
                    print(f"  Read {filename} (utf-8, fixing mojibake, {len(df)} rows)")
                    str_cols = df.select_dtypes(include='object').columns
                    for col in str_cols:
                        df[col] = df[col].apply(fix_mojibake)
                    return df
                print(f"  Read {filename} ({enc}, {len(df)} rows)")
                return df
        except Exception:
            continue

    # Malformed single-column CSV (from bad reducao.py)
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                reader = csv.reader(f, delimiter=',')
                lines = [row[0] for row in reader]
            text = '\n'.join(lines)
            df = pd.read_csv(io.StringIO(text), sep=';', dtype=str)
            if len(df.columns) > 1:
                print(f"  Read {filename} ({enc}, fixed malformed, {len(df)} rows)")
                return df
        except Exception:
            continue

    raise ValueError(f"Could not read {filename}")


def safe_int(value, default=0):
    """Convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def bulk_insert(conn, table, columns, rows):
    """Bulk-insert rows into a table using execute_values."""
    if not rows:
        return
    cur = conn.cursor()
    cols = ', '.join(columns)
    template = '(' + ', '.join(['%s'] * len(columns)) + ')'
    query = f"INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cur, query, rows, template=template, page_size=2000)
    conn.commit()
    cur.close()
    print(f"  -> {table}: {len(rows)} rows inserted")


# ---------------------------------------------------------------------------
# Dimension loaders
# ---------------------------------------------------------------------------

def load_via(conn):
    df = read_csv_smart('VIA.csv')
    rows = [(safe_int(r['CO_VIA']), r['NO_VIA']) for _, r in df.iterrows()]
    bulk_insert(conn, 'tb_via', ['id_via', 'nome_via'], rows)


def load_urf(conn):
    df = read_csv_smart('URF.csv')
    rows = [(safe_int(r['CO_URF']), r['NO_URF']) for _, r in df.iterrows()]
    bulk_insert(conn, 'tb_urf', ['id_urf', 'nome_urf'], rows)


def load_estado(conn):
    df = read_csv_smart('UF.csv')
    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_int(r['CO_UF']),
            str(r.get('NO_UF', '')).strip(),
            str(r.get('SG_UF', '')).strip(),
            str(r.get('NO_REGIAO', '')).strip(),
        ))
    bulk_insert(conn, 'tb_estado', ['id_estado', 'nome_estado', 'sigla_estado', 'nome_regiao'], rows)
    return df  # return for SG_UF -> id_estado mapping


def load_municipio(conn, uf_df):
    df = read_csv_smart('UF_MUN.csv')
    # Build SG_UF -> id_estado lookup
    sg_to_id = {}
    for _, r in uf_df.iterrows():
        sg_to_id[str(r['SG_UF']).strip()] = safe_int(r['CO_UF'])

    rows = []
    for _, r in df.iterrows():
        co_mun = str(r['CO_MUN_GEO']).strip()
        id_estado = sg_to_id.get(str(r.get('SG_UF', '')).strip())
        if id_estado is None:
            # Fallback: first 2 digits of CO_MUN_GEO
            id_estado = safe_int(co_mun[:2])
        nome = str(r.get('NO_MUN_MIN', r.get('NO_MUN', ''))).strip()
        rows.append((safe_int(co_mun), id_estado, nome))
    bulk_insert(conn, 'tb_municipio', ['id_municipio', 'id_estado', 'nome_municipio'], rows)


def load_unidade(conn):
    df = read_csv_smart('NCM_UNIDADE.csv')
    rows = [
        (safe_int(r['CO_UNID']), r['NO_UNID'].strip(), r['SG_UNID'].strip())
        for _, r in df.iterrows()
    ]
    bulk_insert(conn, 'tb_unidade', ['id_unidade', 'nome_unidade', 'sigla_unidade'], rows)


def load_ncm(conn):
    df = read_csv_smart('NCM.csv')
    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_int(r['CO_NCM']),
            str(r.get('NO_NCM_POR', '')).strip(),
            str(r.get('NO_NCM_ING', '')).strip(),
            str(r.get('NO_NCM_ESP', '')).strip(),
        ))
    bulk_insert(conn, 'tb_ncm', ['id_ncm', 'nome_ncm_portugues', 'nome_ncm_ingles', 'nome_ncm_espanhol'], rows)


def load_pais(conn):
    df = read_csv_smart('PAIS.csv')
    rows = []
    for _, r in df.iterrows():
        rows.append((
            safe_int(r['CO_PAIS']),
            str(r.get('NO_PAIS', '')).strip(),
            str(r.get('NO_PAIS_ING', '')).strip(),
            str(r.get('NO_PAIS_ESP', '')).strip(),
        ))
    bulk_insert(conn, 'tb_pais', ['id_pais', 'nome_pais_portugues', 'nome_pais_ingles', 'nome_pais_espanhol'], rows)


def load_bloco_and_junction(conn):
    df = read_csv_smart('PAIS_BLOCO.csv')

    # Extract distinct blocs
    bloco_df = df[['CO_BLOCO', 'NO_BLOCO', 'NO_BLOCO_ING', 'NO_BLOCO_ESP']].drop_duplicates(subset=['CO_BLOCO'])
    bloco_rows = [
        (safe_int(r['CO_BLOCO']),
         str(r.get('NO_BLOCO', '')).strip(),
         str(r.get('NO_BLOCO_ING', '')).strip(),
         str(r.get('NO_BLOCO_ESP', '')).strip())
        for _, r in bloco_df.iterrows()
    ]
    bulk_insert(conn, 'tb_bloco',
                ['id_bloco', 'nome_bloco_portugues', 'nome_bloco_ingles', 'nome_bloco_espanhol'],
                bloco_rows)

    # Junction table — filter to only valid FK references
    cur = conn.cursor()
    cur.execute("SELECT id_pais FROM tb_pais")
    valid_pais = set(row[0] for row in cur.fetchall())
    cur.execute("SELECT id_bloco FROM tb_bloco")
    valid_bloco = set(row[0] for row in cur.fetchall())
    cur.close()

    all_pairs = set(
        (safe_int(r['CO_PAIS']), safe_int(r['CO_BLOCO']))
        for _, r in df.iterrows()
    )
    junction_rows = [
        (p, b) for p, b in all_pairs
        if p in valid_pais and b in valid_bloco
    ]
    skipped = len(all_pairs) - len(junction_rows)
    if skipped:
        print(f"  ⚠ Skipped {skipped} pais_bloco rows (invalid FK references)")
    bulk_insert(conn, 'tb_pais_bloco', ['id_pais', 'id_bloco'], junction_rows)


# ---------------------------------------------------------------------------
# Fact loaders
# ---------------------------------------------------------------------------

def build_uf_lookup(conn):
    """Build SG_UF -> id_estado mapping from the already-loaded tb_estado."""
    cur = conn.cursor()
    cur.execute("SELECT id_estado, sigla_estado FROM tb_estado")
    lookup = {row[1]: row[0] for row in cur.fetchall()}
    cur.close()
    return lookup


def build_existing_pks(conn):
    """Build sets of valid PKs for FK validation."""
    cur = conn.cursor()
    pks = {}
    for table, col in [('tb_ncm', 'id_ncm'), ('tb_via', 'id_via'), ('tb_urf', 'id_urf'),
                        ('tb_unidade', 'id_unidade'), ('tb_pais', 'id_pais'), ('tb_estado', 'id_estado')]:
        cur.execute(f"SELECT {col} FROM {table}")
        pks[table] = set(row[0] for row in cur.fetchall())
    cur.close()
    return pks


def load_exportacao(conn, uf_lookup, pks):
    df = read_csv_smart('Exportacoes_reduzidos.csv')
    rows = []
    skipped = 0
    for _, r in df.iterrows():
        id_estado = uf_lookup.get(str(r.get('SG_UF_NCM', '')).strip())
        id_ncm = safe_int(r.get('CO_NCM'))
        id_via = safe_int(r.get('CO_VIA'))
        id_urf = safe_int(r.get('CO_URF'))
        id_unidade = safe_int(r.get('CO_UNID'))
        id_pais = safe_int(r.get('CO_PAIS'))

        # Skip rows with invalid FKs
        if (id_estado is None or id_ncm not in pks['tb_ncm']
                or id_via not in pks['tb_via'] or id_urf not in pks['tb_urf']
                or id_unidade not in pks['tb_unidade'] or id_pais not in pks['tb_pais']
                or id_estado not in pks['tb_estado']):
            skipped += 1
            continue

        rows.append((
            id_ncm, id_via, id_urf, id_unidade, id_pais, id_estado,
            safe_int(r.get('KG_LIQUIDO')), safe_int(r.get('QT_ESTAT')),
            safe_int(r.get('VL_FOB')),
            safe_int(r.get('CO_ANO')), safe_int(r.get('CO_MES')),
        ))

    bulk_insert(conn, 'tb_exportacao',
                ['id_ncm', 'id_via', 'id_urf', 'id_unidade', 'id_pais', 'id_estado',
                 'kg_liquido', 'qt_estat', 'vl_fob', 'ano', 'mes'], rows)
    if skipped:
        print(f"  ⚠ Skipped {skipped} export rows (invalid FK references)")


def load_importacao(conn, uf_lookup, pks):
    df = read_csv_smart('Importacoes_reduzidos.csv')
    rows = []
    skipped = 0
    for _, r in df.iterrows():
        id_estado = uf_lookup.get(str(r.get('SG_UF_NCM', '')).strip())
        id_ncm = safe_int(r.get('CO_NCM'))
        id_via = safe_int(r.get('CO_VIA'))
        id_urf = safe_int(r.get('CO_URF'))
        id_unidade = safe_int(r.get('CO_UNID'))
        id_pais = safe_int(r.get('CO_PAIS'))

        if (id_estado is None or id_ncm not in pks['tb_ncm']
                or id_via not in pks['tb_via'] or id_urf not in pks['tb_urf']
                or id_unidade not in pks['tb_unidade'] or id_pais not in pks['tb_pais']
                or id_estado not in pks['tb_estado']):
            skipped += 1
            continue

        rows.append((
            id_ncm, id_via, id_urf, id_unidade, id_pais, id_estado,
            safe_int(r.get('KG_LIQUIDO')), safe_int(r.get('QT_ESTAT')),
            safe_int(r.get('VL_FOB')), safe_int(r.get('VL_FRETE')),
            safe_int(r.get('VL_SEGURO')),
            safe_int(r.get('CO_ANO')), safe_int(r.get('CO_MES')),
        ))

    bulk_insert(conn, 'tb_importacao',
                ['id_ncm', 'id_via', 'id_urf', 'id_unidade', 'id_pais', 'id_estado',
                 'kg_liquido', 'qt_estat', 'vl_fob', 'vl_frete', 'vl_seguro', 'ano', 'mes'], rows)
    if skipped:
        print(f"  ⚠ Skipped {skipped} import rows (invalid FK references)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("COMEX 2025 — ETL Pipeline")
    print("=" * 60)

    # 1. Connect
    print("\n[1/4] Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        print("  Connected!")
    except Exception as e:
        print(f"  ERROR: Could not connect — {e}")
        print("  Make sure Docker is running: docker compose up -d")
        sys.exit(1)

    # 2. Create tables
    print("\n[2/4] Creating tables...")
    cur = conn.cursor()
    cur.execute(DROP_SQL)
    cur.execute(CREATE_SQL)
    conn.commit()
    cur.close()
    print("  Tables created!")

    # 3. Load dimensions
    print("\n[3/4] Loading dimension tables...")
    load_via(conn)
    load_urf(conn)
    uf_df = load_estado(conn)
    load_municipio(conn, uf_df)
    load_unidade(conn)
    load_ncm(conn)
    load_pais(conn)
    load_bloco_and_junction(conn)

    # 4. Load facts
    print("\n[4/4] Loading fact tables...")
    uf_lookup = build_uf_lookup(conn)
    pks = build_existing_pks(conn)
    load_exportacao(conn, uf_lookup, pks)
    load_importacao(conn, uf_lookup, pks)

    conn.close()
    print("\n" + "=" * 60)
    print("ETL complete! You can now run: streamlit run dashboard.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
