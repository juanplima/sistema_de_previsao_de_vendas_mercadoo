import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

st.set_page_config(
    page_title='Produtos - Kazkubo',
    page_icon='🛍️',
    layout='wide'
)

st.markdown("""
    <style>
        [data-testid="stMetricValue"] {
            color: #F5C400;
            font-size: 2rem;
            font-weight: bold;
        }
        [data-testid="stMetricLabel"] {
            color: #FFFFFF;
        }
        h1, h2, h3 {
            color: #F5C400 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title('🛍️ Análise de Produtos')

# Filtro de período
with engine.connect() as conn:
    df_datas = pd.read_sql(
        text("SELECT DISTINCT DATE_FORMAT(STR_TO_DATE(data_venda, :fmt_br), :fmt_ym) AS ano_mes FROM tb_vendas ORDER BY ano_mes"),
        conn,
        params={"fmt_br": "%d/%m/%Y", "fmt_ym": "%Y-%m"}
    )

opcoes = ['Todos'] + df_datas['ano_mes'].tolist()
col_filtro, _ = st.columns([1, 3])
with col_filtro:
    periodo = st.selectbox('Selecione o mês', opcoes)

st.divider()

# Parâmetros do filtro
params_periodo = {"fmt_br": "%d/%m/%Y", "fmt_ym": "%Y-%m", "periodo": periodo}
where_vend = "" if periodo == "Todos" else "WHERE DATE_FORMAT(STR_TO_DATE(data_venda, :fmt_br), :fmt_ym) = :periodo"

# Top 10 mais vendidos
st.subheader('🏆 Top 10 produtos mais vendidos')
with engine.connect() as conn:
    df_top = pd.read_sql(
        text(f"""
            SELECT 
                produto,
                sku,
                SUM(quantidade_vendida)              AS total_vendido,
                SUM(valor_unitario * quantidade_vendida) AS faturamento
            FROM tb_vendas
            {where_vend}
            GROUP BY sku, produto
            ORDER BY total_vendido DESC
            LIMIT 10
        """),
        conn,
        params=params_periodo if periodo != 'Todos' else {}
    )

fig1 = px.bar(
    df_top,
    x='total_vendido',
    y='produto',
    orientation='h',
    labels={'total_vendido': 'Quantidade Vendida', 'produto': 'Produto'},
    color_discrete_sequence=['#F5C400'],
    text='total_vendido'
)
fig1.update_traces(
    hovertemplate='<b>%{y}</b><br>Qtd vendida: %{x:,}<extra></extra>',
    textposition='outside'
)
fig1.update_layout(
    plot_bgcolor='#2B2B2B',
    paper_bgcolor='#1A1A1A',
    font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D'),
    yaxis=dict(gridcolor='#3D3D3D', categoryorder='total ascending'),
    height=420
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# Produtos com baixa rotatividade
st.subheader('🐢 Produtos com baixa rotatividade')
st.caption('Produtos com menor volume de vendas no período selecionado')
with engine.connect() as conn:
    df_baixo = pd.read_sql(
        text(f"""
            SELECT 
                produto,
                sku,
                categoria,
                SUM(quantidade_vendida)              AS total_vendido,
                SUM(valor_unitario * quantidade_vendida) AS faturamento
            FROM tb_vendas
            {where_vend}
            GROUP BY sku, produto, categoria
            ORDER BY total_vendido ASC
            LIMIT 10
        """),
        conn,
        params=params_periodo if periodo != 'Todos' else {}
    )

fig2 = px.bar(
    df_baixo,
    x='total_vendido',
    y='produto',
    orientation='h',
    labels={'total_vendido': 'Quantidade Vendida', 'produto': 'Produto'},
    color_discrete_sequence=['#FF6B6B'],
    text='total_vendido'
)
fig2.update_traces(
    hovertemplate='<b>%{y}</b><br>Qtd vendida: %{x:,}<extra></extra>',
    textposition='outside'
)
fig2.update_layout(
    plot_bgcolor='#2B2B2B',
    paper_bgcolor='#1A1A1A',
    font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D'),
    yaxis=dict(gridcolor='#3D3D3D', categoryorder='total descending'),
    height=420
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Ranking completo
st.subheader('📋 Ranking completo de produtos')
with engine.connect() as conn:
    df_ranking = pd.read_sql(
        text(f"""
            SELECT 
                sku                                      AS SKU,
                produto                                  AS Produto,
                categoria                                AS Categoria,
                SUM(quantidade_vendida)                  AS "Qtd Vendida",
                ROUND(SUM(valor_unitario * quantidade_vendida), 2) AS "Faturamento (R$)"
            FROM tb_vendas
            {where_vend}
            GROUP BY sku, produto, categoria
            ORDER BY `Qtd Vendida` DESC
        """),
        conn,
        params=params_periodo if periodo != 'Todos' else {}
    )

st.dataframe(
    df_ranking,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Faturamento (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Qtd Vendida": st.column_config.NumberColumn(format="%d unid.")
    }
)