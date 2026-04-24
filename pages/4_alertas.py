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
    page_title='Alertas - Kazkubo',
    page_icon='🚨',
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

st.title('🚨 Alertas e Insights')
st.caption('Anomalias e padrões detectados automaticamente na base de vendas')

st.divider()

with engine.connect() as conn:
    df_parados = pd.read_sql(
        text("""
            SELECT 
                p.sku,
                p.nome AS produto,
                p.categoria,
                MAX(STR_TO_DATE(v.data_venda, :fmt)) AS ultima_venda,
                DATEDIFF(CURDATE(), MAX(STR_TO_DATE(v.data_venda, :fmt))) AS dias_parado
            FROM produto p
            LEFT JOIN tb_vendas v 
                ON v.sku COLLATE utf8mb4_unicode_ci = p.sku
            GROUP BY p.sku, p.nome, p.categoria
            HAVING dias_parado > 30 OR ultima_venda IS NULL
            ORDER BY dias_parado DESC
        """),
        conn,
        params={"fmt": "%d/%m/%Y"}
    )

with engine.connect() as conn:
    df_queda = pd.read_sql(
        text("""
            SELECT sku, produto, vendas_recentes, vendas_anteriores
            FROM (
                SELECT 
                    sku,
                    produto,
                    SUM(CASE 
                        WHEN STR_TO_DATE(data_venda, :fmt) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        THEN quantidade_vendida ELSE 0 END) AS vendas_recentes,
                    SUM(CASE 
                        WHEN STR_TO_DATE(data_venda, :fmt) BETWEEN DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                             AND DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                        THEN quantidade_vendida ELSE 0 END) AS vendas_anteriores
                FROM tb_vendas
                GROUP BY sku, produto
            ) AS sub
            WHERE vendas_anteriores > 0
              AND vendas_recentes < vendas_anteriores * 0.5
            ORDER BY (vendas_recentes - vendas_anteriores) ASC
            LIMIT 10
        """),
        conn,
        params={"fmt": "%d/%m/%Y"}
    )

df_queda['queda_pct'] = ((df_queda['vendas_recentes'] - df_queda['vendas_anteriores'])
                          / df_queda['vendas_anteriores'] * 100).round(1)

with engine.connect() as conn:
    df_alta = pd.read_sql(
        text("""
            SELECT 
                pd.sku,
                p.nome AS produto,
                ROUND(SUM(pd.qtd_prevista)) AS total_previsto
            FROM previsao_demanda pd
            JOIN produto p 
                ON p.sku = pd.sku COLLATE utf8mb4_unicode_ci
            GROUP BY pd.sku, p.nome
            ORDER BY total_previsto DESC
            LIMIT 10
        """),
        conn
    )

col1, col2, col3 = st.columns(3)
col1.metric('🐢 Produtos parados (+30 dias)', f"{len(df_parados)}")
col2.metric('📉 Produtos com queda > 50%',   f"{len(df_queda)}")
col3.metric('📈 Produtos com alta previsão',  f"{len(df_alta)}")

st.divider()

st.subheader('🐢 Produtos sem venda nos últimos 30 dias')
if len(df_parados) == 0:
    st.success('Nenhum produto parado no período!')
else:
    st.dataframe(
        df_parados,
        use_container_width=True,
        hide_index=True,
        column_config={
            "sku":          st.column_config.TextColumn("SKU"),
            "produto":      st.column_config.TextColumn("Produto"),
            "categoria":    st.column_config.TextColumn("Categoria"),
            "ultima_venda": st.column_config.DateColumn("Última venda", format="DD/MM/YYYY"),
            "dias_parado":  st.column_config.NumberColumn("Dias parado", format="%d dias")
        }
    )

st.divider()

st.subheader('📉 Produtos com queda de vendas > 50%')
st.caption('Comparando os últimos 30 dias com os 30 dias anteriores')
if len(df_queda) == 0:
    st.success('Nenhuma queda significativa detectada!')
else:
    fig = px.bar(
        df_queda,
        x='queda_pct',
        y='produto',
        orientation='h',
        labels={'queda_pct': 'Variação (%)', 'produto': 'Produto'},
        color_discrete_sequence=['#FF6B6B'],
        text='queda_pct'
    )
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Variação: %{x:.1f}%<extra></extra>',
        texttemplate='%{x:.1f}%',
        textposition='outside'
    )
    fig.update_layout(
        plot_bgcolor='#2B2B2B',
        paper_bgcolor='#1A1A1A',
        font_color='#FFFFFF',
        xaxis=dict(gridcolor='#3D3D3D'),
        yaxis=dict(gridcolor='#3D3D3D', categoryorder='total ascending'),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader('📈 Produtos com maior demanda prevista (próximas 8 semanas)')
fig2 = px.bar(
    df_alta,
    x='total_previsto',
    y='produto',
    orientation='h',
    labels={'total_previsto': 'Qtd prevista total', 'produto': 'Produto'},
    color_discrete_sequence=['#F5C400'],
    text='total_previsto'
)
fig2.update_traces(
    hovertemplate='<b>%{y}</b><br>Previsto: %{x} unid.<extra></extra>',
    textposition='outside'
)
fig2.update_layout(
    plot_bgcolor='#2B2B2B',
    paper_bgcolor='#1A1A1A',
    font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D'),
    yaxis=dict(gridcolor='#3D3D3D', categoryorder='total ascending'),
    height=400
)
st.plotly_chart(fig2, use_container_width=True)