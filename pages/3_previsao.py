import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

st.set_page_config(
    page_title='Previsão de Demanda - Kazkubo',
    page_icon='🔮',
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

st.title('🔮 Previsão de Demanda')
st.caption('Previsões geradas pelo modelo Prophet para as próximas 8 semanas')

st.divider()

with engine.connect() as conn:
    df_produtos = pd.read_sql(
        text("SELECT DISTINCT sku, nome FROM produto ORDER BY sku"),
        conn
    )

df_produtos['label'] = df_produtos['sku'] + ' — ' + df_produtos['nome']
opcoes = df_produtos['label'].tolist()

col_sel, _ = st.columns([2, 2])
with col_sel:
    selecionado = st.selectbox('Selecione o produto', opcoes)

sku_selecionado = selecionado.split(' — ')[0]

st.divider()

with engine.connect() as conn:
    df_historico = pd.read_sql(
        text("""
            SELECT 
                STR_TO_DATE(data_venda, :fmt) AS data,
                SUM(quantidade_vendida)        AS qtd_vendida
            FROM tb_vendas
            WHERE sku = :sku
            GROUP BY STR_TO_DATE(data_venda, :fmt)
            ORDER BY data
        """),
        conn,
        params={"fmt": "%d/%m/%Y", "sku": sku_selecionado}
    )

with engine.connect() as conn:
    df_prev = pd.read_sql(
        text("""
            SELECT 
                data_referencia,
                qtd_prevista,
                intervalo_inferior,
                intervalo_superior
            FROM previsao_demanda
            WHERE sku = :sku
            ORDER BY data_referencia
        """),
        conn,
        params={"sku": sku_selecionado}
    )

col1, col2, col3 = st.columns(3)
col1.metric(
    '📦 Total previsto (8 sem.)',
    f"{int(df_prev['qtd_prevista'].sum())} unid."
)
col2.metric(
    '📈 Média semanal prevista',
    f"{int(df_prev['qtd_prevista'].mean())} unid."
)
col3.metric(
    '🗓️ Histórico disponível',
    f"{len(df_historico)} registros"
)

st.divider()

st.subheader(f'Histórico e previsão — {selecionado.split(" — ")[1]}')

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_historico['data'],
    y=df_historico['qtd_vendida'],
    mode='lines+markers',
    name='Histórico real',
    line=dict(color='#FFFFFF', width=1.5),
    marker=dict(size=4),
    hovertemplate='<b>%{x}</b><br>Vendido: %{y} unid.<extra></extra>'
))

x_intervalo = list(df_prev['data_referencia']) + list(df_prev['data_referencia'][::-1])
y_intervalo = list(df_prev['intervalo_superior']) + list(df_prev['intervalo_inferior'][::-1])

fig.add_trace(go.Scatter(
    x=x_intervalo,
    y=y_intervalo,
    fill='toself',
    fillcolor='rgba(245, 196, 0, 0.15)',
    line=dict(color='rgba(255,255,255,0)'),
    name='Intervalo de confiança (95%)',
    hoverinfo='skip'
))

fig.add_trace(go.Scatter(
    x=df_prev['data_referencia'],
    y=df_prev['qtd_prevista'],
    mode='lines+markers',
    name='Previsão Prophet',
    line=dict(color='#F5C400', width=2.5, dash='dash'),
    marker=dict(size=6),
    hovertemplate='<b>%{x}</b><br>Previsto: %{y:.0f} unid.<extra></extra>'
))
fig.update_layout(
    plot_bgcolor='#2B2B2B',
    paper_bgcolor='#1A1A1A',
    font_color='#FFFFFF',
    xaxis=dict(gridcolor='#3D3D3D', title='Data'),
    yaxis=dict(gridcolor='#3D3D3D', title='Quantidade'),
    legend=dict(
        bgcolor='#2B2B2B',
        bordercolor='#3D3D3D',
        borderwidth=1
    ),
    hovermode='x unified',
    height=500
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader('📋 Detalhamento das previsões')
df_prev_display = df_prev.copy()
df_prev_display.columns = ['Semana', 'Qtd Prevista', 'Mínimo', 'Máximo']
df_prev_display['Semana'] = pd.to_datetime(df_prev_display['Semana']).dt.strftime('%d/%m/%Y')

st.dataframe(
    df_prev_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Qtd Prevista": st.column_config.NumberColumn(format="%d unid."),
        "Mínimo":       st.column_config.NumberColumn(format="%d unid."),
        "Máximo":       st.column_config.NumberColumn(format="%d unid.")
    }
)