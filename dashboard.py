"""
Dashboard COMEX 2025 — Streamlit
Run: streamlit run dashboard.py
"""

import os
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Config
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

MONTHS_PT = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}


@st.cache_resource
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def query_df(sql):
    try:
        conn = get_connection()
        return pd.read_sql(sql, conn)
    except Exception:
        return pd.DataFrame()


def format_brl(value):
    """Format a number as US$ (FOB values are in USD)."""
    if abs(value) >= 1e9:
        return f"US$ {value / 1e9:,.2f}B"
    if abs(value) >= 1e6:
        return f"US$ {value / 1e6:,.2f}M"
    if abs(value) >= 1e3:
        return f"US$ {value / 1e3:,.1f}K"
    return f"US$ {value:,.0f}"


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="COMEX 2025 — Dashboard", layout="wide", page_icon="📊")

st.title("📊 Balança Comercial do Brasil — 2025")
st.caption("Dados: ComexStat (Ministério do Desenvolvimento, Indústria, Comércio e Serviços)")

st.divider()

# =========================================================================
# Q1: Saldo total da balança comercial em 2025
# =========================================================================
st.header("1. Saldo Total da Balança Comercial em 2025")

q1 = query_df("""
    SELECT
        (SELECT COALESCE(SUM(vl_fob), 0) FROM tb_exportacao WHERE ano = 2025) AS total_exp,
        (SELECT COALESCE(SUM(vl_fob), 0) FROM tb_importacao WHERE ano = 2025) AS total_imp
""")
total_exp = q1['total_exp'].iloc[0]
total_imp = q1['total_imp'].iloc[0]
saldo = total_exp - total_imp

col1, col2, col3 = st.columns(3)
col1.metric("Exportações (FOB)", format_brl(total_exp))
col2.metric("Importações (FOB)", format_brl(total_imp))
col3.metric("Saldo", format_brl(saldo), delta=format_brl(saldo))

fig1 = go.Figure(data=[
    go.Bar(name='Exportações', x=['Exportações'], y=[total_exp], marker_color='#2ecc71',
           width=0.4, text=[format_brl(total_exp)], textposition='outside'),
    go.Bar(name='Importações', x=['Importações'], y=[total_imp], marker_color='#e74c3c',
           width=0.4, text=[format_brl(total_imp)], textposition='outside'),
])
fig1.update_layout(barmode='group', yaxis_title='Valor FOB (US$)', height=380,
                   bargap=0.5, showlegend=False, xaxis_title='')
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# =========================================================================
# Q2: Meses com balança negativa (déficit)
# =========================================================================
st.header("2. Balanço Mensal em 2025")

q2 = query_df("""
    SELECT
        m.mes,
        COALESCE(e.total_exp, 0) AS total_exp,
        COALESCE(i.total_imp, 0) AS total_imp,
        COALESCE(e.total_exp, 0) - COALESCE(i.total_imp, 0) AS saldo
    FROM generate_series(1, 12) AS m(mes)
    LEFT JOIN (
        SELECT mes, SUM(vl_fob) AS total_exp FROM tb_exportacao WHERE ano = 2025 GROUP BY mes
    ) e ON m.mes = e.mes
    LEFT JOIN (
        SELECT mes, SUM(vl_fob) AS total_imp FROM tb_importacao WHERE ano = 2025 GROUP BY mes
    ) i ON m.mes = i.mes
    ORDER BY m.mes
""")
q2['mes_nome'] = q2['mes'].map(MONTHS_PT)
q2['cor'] = q2['saldo'].apply(lambda x: 'Superávit' if x >= 0 else 'Déficit')

fig2 = px.bar(q2, x='mes_nome', y='saldo', color='cor',
              color_discrete_map={'Superávit': '#2ecc71', 'Déficit': '#e74c3c'},
              labels={'mes_nome': 'Mês', 'saldo': 'Saldo (US$)', 'cor': ''},
              title='Saldo Mensal da Balança Comercial')
fig2.add_hline(y=0, line_dash="dash", line_color="gray")
fig2.update_layout(height=400)
st.plotly_chart(fig2, use_container_width=True)

deficit_months = q2[q2['saldo'] < 0]
if deficit_months.empty:
    st.success("Nenhum mês apresentou déficit em 2025.")
else:
    st.warning(f"Meses com déficit: **{', '.join(deficit_months['mes_nome'].tolist())}**")

st.divider()

# =========================================================================
# Q3: Top 5 produtos exportados (por NCM)
# =========================================================================
st.header("3. Top 5 Produtos Mais Exportados (NCM) em 2025")

q3 = query_df("""
    SELECT n.id_ncm, n.nome_ncm_portugues AS produto, SUM(e.vl_fob) AS total
    FROM tb_exportacao e
    JOIN tb_ncm n ON e.id_ncm = n.id_ncm
    WHERE e.ano = 2025
    GROUP BY n.id_ncm, n.nome_ncm_portugues
    ORDER BY total DESC
    LIMIT 5
""")
q3['label'] = q3['id_ncm'].astype(str) + ' - ' + q3['produto'].astype(str).str[:60]

fig3 = px.bar(q3, x='total', y='label', orientation='h',
              labels={'total': 'Valor FOB (US$)', 'label': 'NCM — Produto'},
              color='total', color_continuous_scale='greens')
fig3.update_layout(yaxis={'autorange': 'reversed'}, height=400, showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# =========================================================================
# Q4: NCM com maior gasto em importação
# =========================================================================
st.header("4. Produtos Mais Importados em 2025")

q4 = query_df("""
    SELECT n.id_ncm, n.nome_ncm_portugues AS produto, SUM(i.vl_fob) AS total
    FROM tb_importacao i
    JOIN tb_ncm n ON i.id_ncm = n.id_ncm
    WHERE i.ano = 2025
    GROUP BY n.id_ncm, n.nome_ncm_portugues
    ORDER BY total DESC
    LIMIT 5
""")

col1, col2 = st.columns([1, 2])
with col1:
    if not q4.empty:
        st.metric("NCM", str(q4.iloc[0]['id_ncm']))
        st.metric("Valor Total (FOB)", format_brl(q4.iloc[0]['total']))
        st.write(f"**Descrição:** {q4.iloc[0]['produto']}")
with col2:
    q4['label'] = q4['id_ncm'].astype(str) + ' - ' + q4['produto'].astype(str).str[:50]
    fig4 = px.bar(q4, x='total', y='label', orientation='h',
                  labels={'total': 'Valor FOB (US$)', 'label': 'NCM — Produto'},
                  color='total', color_continuous_scale='reds')
    fig4.update_layout(yaxis={'autorange': 'reversed'}, height=350, showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# =========================================================================
# Q5: Principal bloco econômico destino das exportações
# =========================================================================
st.header("5. Principal Bloco Econômico de Destino das Exportações em 2025")

q5 = query_df("""
    SELECT b.nome_bloco_portugues AS bloco, SUM(e.vl_fob) AS total
    FROM tb_exportacao e
    JOIN tb_pais_bloco pb ON e.id_pais = pb.id_pais
    JOIN tb_bloco b ON pb.id_bloco = b.id_bloco
    WHERE e.ano = 2025
    GROUP BY b.nome_bloco_portugues
    ORDER BY total DESC
    LIMIT 10
""")

fig5 = px.pie(q5, names='bloco', values='total',
              title='Distribuição das Exportações por Bloco Econômico (Top 10)',
              color_discrete_sequence=px.colors.qualitative.Set3)
fig5.update_traces(textinfo='label+percent', textposition='outside')
fig5.update_layout(height=500)
st.plotly_chart(fig5, use_container_width=True)

if not q5.empty:
    st.success(f"Principal destino: **{q5.iloc[0]['bloco']}** — {format_brl(q5.iloc[0]['total'])}")

st.divider()

# =========================================================================
# Q6: Top 5 países de onde o Brasil mais importou
# =========================================================================
st.header("6. Top 5 Países de Origem das Importações em 2025")

q6 = query_df("""
    SELECT p.nome_pais_portugues AS pais, SUM(i.vl_fob) AS total
    FROM tb_importacao i
    JOIN tb_pais p ON i.id_pais = p.id_pais
    WHERE i.ano = 2025
    GROUP BY p.nome_pais_portugues
    ORDER BY total DESC
    LIMIT 5
""")

fig6 = px.bar(q6, x='pais', y='total',
              labels={'pais': 'País', 'total': 'Valor FOB (US$)'},
              color='total', color_continuous_scale='blues')
fig6.update_layout(height=400, showlegend=False)
st.plotly_chart(fig6, use_container_width=True)

st.divider()

# =========================================================================
# Q7: Estado (UF) líder em exportações por valor
# =========================================================================
st.header("7. Exportações por Estado em 2025")

q7 = query_df("""
    SELECT uf.sigla_estado AS uf, uf.nome_estado AS estado, SUM(e.vl_fob) AS total
    FROM tb_exportacao e
    JOIN tb_estado uf ON e.id_estado = uf.id_estado
    WHERE e.ano = 2025
    GROUP BY uf.sigla_estado, uf.nome_estado
    ORDER BY total DESC
""")

fig7 = px.bar(q7.head(10), x='uf', y='total',
              labels={'uf': 'UF', 'total': 'Valor FOB (US$)'},
              color='total', color_continuous_scale='greens',
              title='Top 10 Estados Exportadores')
fig7.update_layout(height=400, showlegend=False)
st.plotly_chart(fig7, use_container_width=True)

if not q7.empty:
    st.success(f"Líder: **{q7.iloc[0]['estado']} ({q7.iloc[0]['uf']})** — {format_brl(q7.iloc[0]['total'])}")

st.divider()

# =========================================================================
# Q8: Top 5 municípios com maior volume de importação
# =========================================================================
st.header("8. Top 5 Municípios com Maior Volume de Importação em 2025")

st.info(
    "**Nota:** Cada registro de importação passa por uma URF (Unidade da Receita Federal) "
    "localizada em um município específico. Utilizamos o `CO_URF` como proxy geográfico "
    "para identificar os municípios com maior volume de importação."
)

q8 = query_df("""
    SELECT u.nome_urf AS municipio, SUM(i.vl_fob) AS total
    FROM tb_importacao i
    JOIN tb_urf u ON i.id_urf = u.id_urf
    WHERE i.ano = 2025
    GROUP BY u.nome_urf
    ORDER BY total DESC
    LIMIT 5
""")

fig8 = px.bar(q8, x='municipio', y='total',
              labels={'municipio': 'Município (URF)', 'total': 'Valor FOB (US$)'},
              color='total', color_continuous_scale='oranges',
              title='Top 5 Municípios Importadores (via URF)')
fig8.update_layout(height=400, showlegend=False, xaxis_tickangle=-25)
st.plotly_chart(fig8, use_container_width=True)

st.divider()

# =========================================================================
# Q9: Modal de transporte mais utilizado nas importações
# =========================================================================
st.header("9. Modal de Transporte Mais Utilizado nas Importações em 2025")

q9 = query_df("""
    SELECT v.nome_via AS modal, COUNT(*) AS registros, SUM(i.vl_fob) AS total
    FROM tb_importacao i
    JOIN tb_via v ON i.id_via = v.id_via
    WHERE i.ano = 2025
    GROUP BY v.nome_via
    ORDER BY total DESC
""")

col1, col2 = st.columns(2)
with col1:
    fig9a = px.pie(q9, names='modal', values='total',
                   title='Por Valor FOB (US$)',
                   color_discrete_sequence=px.colors.qualitative.Pastel)
    fig9a.update_traces(textinfo='label+percent')
    fig9a.update_layout(height=400)
    st.plotly_chart(fig9a, use_container_width=True)
with col2:
    fig9b = px.pie(q9, names='modal', values='registros',
                   title='Por Quantidade de Registros',
                   color_discrete_sequence=px.colors.qualitative.Pastel)
    fig9b.update_traces(textinfo='label+percent')
    fig9b.update_layout(height=400)
    st.plotly_chart(fig9b, use_container_width=True)

if not q9.empty:
    st.success(f"Modal mais utilizado por valor: **{q9.iloc[0]['modal']}** — {format_brl(q9.iloc[0]['total'])}")

st.divider()

# =========================================================================
# Q10: Municípios que só importaram (sem exportações)
# =========================================================================
st.header("10. Municípios que Apenas Importaram (sem Exportações) em 2025")

st.info(
    "**Nota:** Utilizamos o `CO_URF` (Unidade da Receita Federal) como proxy geográfico. "
    "Municípios aqui são URFs que registraram importações mas nenhuma exportação em 2025."
)

q10 = query_df("""
    SELECT u.nome_urf AS municipio, SUM(i.vl_fob) AS total_imp
    FROM tb_importacao i
    JOIN tb_urf u ON i.id_urf = u.id_urf
    WHERE i.ano = 2025
      AND i.id_urf NOT IN (
          SELECT DISTINCT id_urf FROM tb_exportacao WHERE ano = 2025
      )
    GROUP BY u.nome_urf
    ORDER BY total_imp DESC
    LIMIT 5
""")

if q10.empty:
    st.success("Todos os municípios (URFs) que importaram também exportaram em 2025.")
else:
    fig10 = px.bar(q10, x='municipio', y='total_imp',
                   labels={'municipio': 'Município (URF)', 'total_imp': 'Valor Importado (US$)'},
                   color='total_imp', color_continuous_scale='reds',
                   title='Top 5 Municípios Import-Only (via URF)')
    fig10.update_layout(height=400, showlegend=False, xaxis_tickangle=-25)
    st.plotly_chart(fig10, use_container_width=True)

st.divider()
st.caption("Dashboard desenvolvido para a disciplina de Business Intelligence e Data Warehousing — IESB 2026")
