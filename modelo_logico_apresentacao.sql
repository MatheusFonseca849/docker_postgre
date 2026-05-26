/*-------------------------------------------------------------------------------------------------------------------------
Disciplina: Business Intelligence e Data Warehousing
Autor....: Isabela Vitoria, Natalia Rodrigues, Vitoria Ribeiro, Matheus Guilherme
Objetivo..: Data manipulation samples - CRUD. (Exemplos de DDL e DML)
Bimestre.: 2 Bimestre 2026
Objeto....: modelo_logico_apresentacao.sql

Data Criação...................: 21/05/2026
Data Alteração................. :26/04/2024 nome: Matheus
Alteração Feita: migração de sintaxe para PostgreSQL e adequação de chaves e constraints
--------------------------------------------------------------------------------------------------------------------------
Versão 1.1
*/

-- =========================================
-- TABELA: tb_via
-- =========================================
CREATE TABLE tb_via (
    id_via INT NOT NULL,
    nome_via VARCHAR(250),

    CONSTRAINT pk_tb_via PRIMARY KEY (id_via)
);

-- =========================================
-- TABELA: tb_urf
-- =========================================
CREATE TABLE tb_urf (
    id_urf INT NOT NULL,
    nome_urf VARCHAR(250) NOT NULL,

    CONSTRAINT pk_tb_urf PRIMARY KEY (id_urf)
);

-- =========================================
-- TABELA: tb_estado
-- =========================================
CREATE TABLE tb_estado (
    id_estado INT NOT NULL,
    nome_estado VARCHAR(300) NOT NULL,
    sigla_estado VARCHAR(2) NOT NULL,
    nome_regiao VARCHAR(250) NOT NULL,

    CONSTRAINT pk_tb_estado PRIMARY KEY (id_estado)
);

-- =========================================
-- TABELA: tb_municipio
-- =========================================
CREATE TABLE tb_municipio (
    id_municipio INT NOT NULL,
    id_estado INT NOT NULL,
    nome_municipio VARCHAR(800) NOT NULL,

    CONSTRAINT pk_tb_municipio PRIMARY KEY (id_municipio),

    CONSTRAINT fk_tb_municipio_estado
        FOREIGN KEY (id_estado)
        REFERENCES tb_estado(id_estado)
);

-- =========================================
-- TABELA: tb_ncm
-- =========================================
CREATE TABLE tb_ncm (
    id_ncm BIGINT NOT NULL,
    nome_ncm_portugues TEXT NOT NULL,
    nome_ncm_ingles TEXT NOT NULL,
    nome_ncm_espanhol TEXT NOT NULL,

    CONSTRAINT pk_tb_ncm PRIMARY KEY (id_ncm)
);

-- =========================================
-- TABELA: tb_unidade
-- =========================================
CREATE TABLE tb_unidade (
    id_unidade INT NOT NULL,
    nome_unidade VARCHAR(300) NOT NULL,
    sigla_unidade VARCHAR(10) NOT NULL,

    CONSTRAINT pk_tb_unidade PRIMARY KEY (id_unidade)
);

-- =========================================
-- TABELA: tb_pais
-- =========================================
CREATE TABLE tb_pais (
    id_pais INT NOT NULL,
    nome_pais_portugues VARCHAR(200) NOT NULL,
    nome_pais_ingles VARCHAR(200) NOT NULL,
    nome_pais_espanhol VARCHAR(200) NOT NULL,

    CONSTRAINT pk_tb_pais PRIMARY KEY (id_pais)
);

-- =========================================
-- TABELA: tb_bloco
-- =========================================
CREATE TABLE tb_bloco (
    id_bloco INT NOT NULL,
    nome_bloco_portugues VARCHAR(255) NOT NULL,
    nome_bloco_ingles VARCHAR(255) NOT NULL,
    nome_bloco_espanhol VARCHAR(255) NOT NULL,

    CONSTRAINT pk_tb_bloco PRIMARY KEY (id_bloco)
);

-- =========================================
-- TABELA: tb_pais_bloco (tabela de junção)
-- =========================================
CREATE TABLE tb_pais_bloco (
    id_pais INT NOT NULL,
    id_bloco INT NOT NULL,

    CONSTRAINT pk_tb_pais_bloco PRIMARY KEY (id_pais, id_bloco),

    CONSTRAINT fk_tb_pais_bloco_pais
        FOREIGN KEY (id_pais)
        REFERENCES tb_pais(id_pais),

    CONSTRAINT fk_tb_pais_bloco_bloco
        FOREIGN KEY (id_bloco)
        REFERENCES tb_bloco(id_bloco)
);

-- =========================================
-- TABELA: tb_exportacao
-- =========================================
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

    CONSTRAINT fk_tb_exportacao_ncm
        FOREIGN KEY (id_ncm)
        REFERENCES tb_ncm(id_ncm),

    CONSTRAINT fk_tb_exportacao_via
        FOREIGN KEY (id_via)
        REFERENCES tb_via(id_via),

    CONSTRAINT fk_tb_exportacao_urf
        FOREIGN KEY (id_urf)
        REFERENCES tb_urf(id_urf),

    CONSTRAINT fk_tb_exportacao_unidade
        FOREIGN KEY (id_unidade)
        REFERENCES tb_unidade(id_unidade),

    CONSTRAINT fk_tb_exportacao_pais
        FOREIGN KEY (id_pais)
        REFERENCES tb_pais(id_pais),

    CONSTRAINT fk_tb_exportacao_estado
        FOREIGN KEY (id_estado)
        REFERENCES tb_estado(id_estado)
);

-- =========================================
-- TABELA: tb_importacao
-- =========================================
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

    CONSTRAINT fk_tb_importacao_ncm
        FOREIGN KEY (id_ncm)
        REFERENCES tb_ncm(id_ncm),

    CONSTRAINT fk_tb_importacao_via
        FOREIGN KEY (id_via)
        REFERENCES tb_via(id_via),

    CONSTRAINT fk_tb_importacao_urf
        FOREIGN KEY (id_urf)
        REFERENCES tb_urf(id_urf),

    CONSTRAINT fk_tb_importacao_unidade
        FOREIGN KEY (id_unidade)
        REFERENCES tb_unidade(id_unidade),

    CONSTRAINT fk_tb_importacao_pais
        FOREIGN KEY (id_pais)
        REFERENCES tb_pais(id_pais),

    CONSTRAINT fk_tb_importacao_estado
        FOREIGN KEY (id_estado)
        REFERENCES tb_estado(id_estado)
);
