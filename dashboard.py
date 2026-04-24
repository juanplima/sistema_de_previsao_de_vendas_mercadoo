import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

st.set_page_config(
    page_title='Kazkubo - Inteligência de Vendas',
    page_icon='🛒',
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
        .hero {
            padding: 2rem 0 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="hero">
        <h1 style="font-size: 3rem; margin-bottom: 0;">🛒 Kazkubo</h1>
        <p style="color: #AAAAAA; font-size: 1.2rem; margin-top: 0.5rem;">
            Plataforma de Inteligência de Vendas para pequenos comércios
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

with engine.connect() as conn:
    df = pd.read_sql(
        text("""
            SELECT 
                COALESCE(SUM(faturamento_total), 0) AS faturamento,
                COALESCE(SUM(qtd_vendas), 0)        AS total_vendas,
                COALESCE(AVG(ticket_medio), 0)      AS ticket_medio
            FROM indicador_diario
        """),
        conn
    )

with engine.connect() as conn:
    df_skus = pd.read_sql(
        text("SELECT COUNT(DISTINCT sku) AS total_skus FROM produto"),
        conn
    )

with engine.connect() as conn:
    df_prev = pd.read_sql(
        text("SELECT COUNT(DISTINCT sku) AS skus_previstos FROM previsao_demanda"),
        conn
    )

col1, col2, col3, col4 = st.columns(4)
col1.metric('💰 Faturamento total',    f"R$ {df['faturamento'][0]:,.2f}")
col2.metric('🛒 Total de vendas',      f"{int(df['total_vendas'][0]):,}")
col3.metric('🎯 Ticket médio',         f"R$ {df['ticket_medio'][0]:,.2f}")
col4.metric('📦 Produtos monitorados', f"{int(df_skus['total_skus'][0]):,} SKUs")

st.divider()

st.subheader('Navegue pelo sistema')

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div style="background:#2B2B2B; padding:1.5rem; border-radius:12px; border-left: 4px solid #F5C400;">
            <h3 style="color:#F5C400; margin-top:0">📊 Visão Geral</h3>
            <p style="color:#AAAAAA">Faturamento diário, evolução temporal e análise por categoria.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style="background:#2B2B2B; padding:1.5rem; border-radius:12px; border-left: 4px solid #F5C400;">
            <h3 style="color:#F5C400; margin-top:0">🛍️ Produtos</h3>
            <p style="color:#AAAAAA">Top 10 mais vendidos, baixa rotatividade e ranking completo.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div style="background:#2B2B2B; padding:1.5rem; border-radius:12px; border-left: 4px solid #F5C400;">
            <h3 style="color:#F5C400; margin-top:0">🔮 Previsão de Demanda</h3>
            <p style="color:#AAAAAA">Previsões geradas pelo modelo Prophet para as próximas 8 semanas.</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption('Desenvolvido com Python · Prophet · MySQL · Streamlit')