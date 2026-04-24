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
    page_title='Visão Geral - Kazkubo',
    page_icon='📊',
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

st.title('📊 Visão Geral')


with engine.connect() as conn:
    df_datas = pd.read_sql(
        text("SELECT DISTINCT DATE_FORMAT(data, :fmt) AS ano_mes FROM indicador_diario ORDER BY ano_mes"),
        conn,
        params={"fmt": "%Y-%m"}
    )

opcoes = ['Todos'] + df_datas['ano_mes'].tolist()

col_filtro, _ = st.columns([1, 3])
with col_filtro:
    periodo = st.selectbox('Selecione o mês', opcoes)

st.divider()

with engine.connect() as conn:
    if periodo == 'Todos':
        df_metrics = pd.read_sql(
            text("""
                SELECT 
                    COALESCE(SUM(faturamento_total), 0) AS faturamento,
                    COALESCE(SUM(qtd_vendas), 0)        AS total_vendas,
                    COALESCE(AVG(ticket_medio), 0)      AS ticket_medio
                FROM indicador_diario
            """),
            conn
        )
    else:
        df_metrics = pd.read_sql(
            text("""
                SELECT 
                    COALESCE(SUM(faturamento_total), 0) AS faturamento,
                    COALESCE(SUM(qtd_vendas), 0)        AS total_vendas,
                    COALESCE(AVG(ticket_medio), 0)      AS ticket_medio
                FROM indicador_diario
                WHERE DATE_FORMAT(data, :fmt) = :periodo
            """),
            conn,
            params={"fmt": "%Y-%m", "periodo": periodo}
        )

col1, col2, col3 = st.columns(3)
col1.metric('💰 Faturamento Total', f"R$ {df_metrics['faturamento'][0]:,.2f}")
col2.metric('🛒 Total de Vendas',   f"{int(df_metrics['total_vendas'][0]):,}")
col3.metric('🎯 Ticket Médio',      f"R$ {df_metrics['ticket_medio'][0]:,.2f}")

st.divider()


st.subheader('Evolução do faturamento diário')
with engine.connect() as conn:
    if periodo == 'Todos':
        df_evolucao = pd.read_sql(
            text("SELECT data, faturamento_total FROM indicador_diario ORDER BY data"),
            conn
        )
    else:
        df_evolucao = pd.read_sql(
            text("SELECT data, faturamento_total FROM indicador_diario WHERE DATE_FORMAT(data, :fmt) = :periodo ORDER BY data"),
            conn,
            params={"fmt": "%Y-%m", "periodo": periodo}
        )

fig1 = px.line(
    df_evolucao, x='data', y='faturamento_total',
    labels={'data': 'Data', 'faturamento_total': 'Faturamento (R$)'},
    color_discrete_sequence=['#F5C400']
)
fig1.update_traces(hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.2f}<extra></extra>')
fig1.update_layout(
    plot_bgcolor='#2B2B2B', paper_bgcolor='#1A1A1A', font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D'),
    yaxis=dict(gridcolor='#3D3D3D', tickformat=',.2f', tickprefix='R$ ')
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

st.subheader('Faturamento por categoria')
with engine.connect() as conn:
    if periodo == 'Todos':
        df_categoria = pd.read_sql(
            text("""
                SELECT categoria,
                       SUM(valor_unitario * quantidade_vendida) AS faturamento
                FROM tb_vendas
                GROUP BY categoria
                ORDER BY faturamento DESC
            """),
            conn
        )
    else:
        df_categoria = pd.read_sql(
            text("""
                SELECT categoria,
                       SUM(valor_unitario * quantidade_vendida) AS faturamento
                FROM tb_vendas
                WHERE DATE_FORMAT(STR_TO_DATE(data_venda, :fmt_br), :fmt_ym) = :periodo
                GROUP BY categoria
                ORDER BY faturamento DESC
            """),
            conn,
            params={"fmt_br": "%d/%m/%Y", "fmt_ym": "%Y-%m", "periodo": periodo}
        )

fig2 = px.bar(
    df_categoria, x='categoria', y='faturamento',
    labels={'categoria': 'Categoria', 'faturamento': 'Faturamento (R$)'},
    color_discrete_sequence=['#F5C400']
)
fig2.update_traces(hovertemplate='<b>%{x}</b><br>Faturamento: R$ %{y:,.2f}<extra></extra>')
fig2.update_layout(
    plot_bgcolor='#2B2B2B', paper_bgcolor='#1A1A1A', font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D'),
    yaxis=dict(gridcolor='#3D3D3D', tickformat=',.2f', tickprefix='R$ ')
)
st.plotly_chart(fig2, use_container_width=True)