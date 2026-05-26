-- ============================================================
-- COMEX ETL: Create tables and load CSV data
-- Run this inside the PostgreSQL container or via DBeaver
-- ============================================================

-- ========================
-- DIMENSION TABLES
-- ========================

CREATE TABLE IF NOT EXISTS dim_via (
    co_via VARCHAR(10) PRIMARY KEY,
    no_via VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_uf (
    co_uf VARCHAR(10) PRIMARY KEY,
    sg_uf VARCHAR(5),
    no_uf VARCHAR(100),
    no_regiao VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_ncm_unidade (
    co_unid VARCHAR(10) PRIMARY KEY,
    no_unid VARCHAR(100),
    sg_unid VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS dim_pais (
    co_pais VARCHAR(10) PRIMARY KEY,
    co_pais_ison3 VARCHAR(10),
    co_pais_isoa3 VARCHAR(10),
    no_pais VARCHAR(100),
    no_pais_ing VARCHAR(100),
    no_pais_esp VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_pais_bloco (
    co_pais VARCHAR(10),
    co_bloco VARCHAR(10),
    no_bloco VARCHAR(200),
    no_bloco_ing VARCHAR(200),
    no_bloco_esp VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS dim_uf_mun (
    co_mun_geo VARCHAR(20) PRIMARY KEY,
    no_mun VARCHAR(100),
    no_mun_min VARCHAR(100),
    sg_uf VARCHAR(5)
);

CREATE TABLE IF NOT EXISTS dim_urf (
    co_urf VARCHAR(20) PRIMARY KEY,
    no_urf VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS dim_ncm (
    co_ncm VARCHAR(20) PRIMARY KEY,
    co_unid VARCHAR(10),
    co_sh6 VARCHAR(10),
    co_ppe VARCHAR(10),
    co_ppi VARCHAR(10),
    co_fat_agreg VARCHAR(10),
    co_cuci_item VARCHAR(10),
    co_cgce_n3 VARCHAR(10),
    co_siit VARCHAR(10),
    co_isic_classe VARCHAR(10),
    co_exp_subset VARCHAR(10),
    no_ncm_por TEXT,
    no_ncm_esp TEXT,
    no_ncm_ing TEXT
);

-- ========================
-- FACT TABLES
-- ========================

CREATE TABLE IF NOT EXISTS fato_exportacao (
    co_ano INTEGER,
    co_mes VARCHAR(5),
    co_ncm VARCHAR(20),
    co_unid VARCHAR(10),
    co_pais VARCHAR(10),
    sg_uf_ncm VARCHAR(5),
    co_via VARCHAR(10),
    co_urf VARCHAR(20),
    qt_estat BIGINT,
    kg_liquido BIGINT,
    vl_fob BIGINT
);

CREATE TABLE IF NOT EXISTS fato_importacao (
    co_ano INTEGER,
    co_mes VARCHAR(5),
    co_ncm VARCHAR(20),
    co_unid VARCHAR(10),
    co_pais VARCHAR(10),
    sg_uf_ncm VARCHAR(5),
    co_via VARCHAR(10),
    co_urf VARCHAR(20),
    qt_estat BIGINT,
    kg_liquido BIGINT,
    vl_fob BIGINT,
    vl_frete BIGINT,
    vl_seguro BIGINT
);

-- ========================
-- LOAD DATA (COPY)
-- These commands must be run from INSIDE the container
-- because they reference /tmp/data paths
-- ========================

COPY dim_via(co_via, no_via)
FROM '/tmp/data/VIA.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_uf(co_uf, sg_uf, no_uf, no_regiao)
FROM '/tmp/data/UF.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_ncm_unidade(co_unid, no_unid, sg_unid)
FROM '/tmp/data/NCM_UNIDADE.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_urf(co_urf, no_urf)
FROM '/tmp/data/URF.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_ncm(co_ncm, co_unid, co_sh6, co_ppe, co_ppi, co_fat_agreg, co_cuci_item, co_cgce_n3, co_siit, co_isic_classe, co_exp_subset, no_ncm_por, no_ncm_esp, no_ncm_ing)
FROM '/tmp/data/NCM.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_pais(co_pais, co_pais_ison3, co_pais_isoa3, no_pais, no_pais_ing, no_pais_esp)
FROM '/tmp/data/PAIS.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_pais_bloco(co_pais, co_bloco, no_bloco, no_bloco_ing, no_bloco_esp)
FROM '/tmp/data/PAIS_BLOCO.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY dim_uf_mun(co_mun_geo, no_mun, no_mun_min, sg_uf)
FROM '/tmp/data/UF_MUN.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

-- FACT TABLES (only run after fixing the reduced CSVs with fix_reduced_csvs.py)
COPY fato_exportacao(co_ano, co_mes, co_ncm, co_unid, co_pais, sg_uf_ncm, co_via, co_urf, qt_estat, kg_liquido, vl_fob)
FROM '/tmp/data/Exportacoes_reduzidos.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');

COPY fato_importacao(co_ano, co_mes, co_ncm, co_unid, co_pais, sg_uf_ncm, co_via, co_urf, qt_estat, kg_liquido, vl_fob, vl_frete, vl_seguro)
FROM '/tmp/data/Importacoes_reduzidos.csv'
WITH (FORMAT csv, DELIMITER ';', HEADER true, QUOTE '"', ENCODING 'UTF8');
