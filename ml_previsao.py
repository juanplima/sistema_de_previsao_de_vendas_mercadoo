import pandas as pd
import os
import logging
import traceback
from dotenv import load_dotenv
from sqlalchemy import create_engine
from prophet import Prophet

logging.basicConfig(
    filename='previsao.log',       
    level=logging.INFO,            
    format='%(asctime)s | %(levelname)s: %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").disabled = True


load_dotenv()

engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

print("Carregando dados do banco...")
df = pd.read_sql('SELECT * FROM tb_vendas', engine)
df['data_venda'] = pd.to_datetime(df['data_venda'], format='%d/%m/%Y')

print("Agrupando dados por semana...")
df_agg = df.groupby(['sku', pd.Grouper(key='data_venda', freq='W')]).agg(
    qtd_vendida=('quantidade_vendida', 'sum')
).reset_index()


skus = df_agg['sku'].unique()

# pegar ultima data de venda registrada no sistema para previsão
data_max_global = df_agg['data_venda'].max()
print(f"data mais recente: {data_max_global.date()}")
print(f'treinando modelo para {len(skus)} skus. acompanhe o arquivo previsao.log!')
logging.info(f"--- INICIANDO NOVO TREINAMENTO DE {len(skus)} SKUs (SALVANDO POR SKU) ---")

contador = 1
for sku in skus:
    try:
        logging.info(f"Processando [{contador}/{len(skus)}] - SKU: {sku}")
        
        df_sku = df_agg[df_agg['sku'] == sku][['data_venda', 'qtd_vendida']].copy()
        df_sku.columns = ['ds', 'y']
        
        if len(df_sku) < 2:
            logging.warning(f"SKU {sku} ignorado (menos de 2 registros).")
            contador += 1
            continue

        # treinar modelo
        modelo = Prophet(weekly_seasonality=True, yearly_seasonality=True)
        modelo.fit(df_sku)

        dias_defasagem = (data_max_global - df_sku['ds'].max()).days
        
        semanas_defasagem = int(max(0, dias_defasagem) / 7)
    
        periodos_totais = semanas_defasagem + 8
        
        futuro = modelo.make_future_dataframe(periods=periodos_totais, freq='W')
        forecast = modelo.predict(futuro)

        forecast_futuro = forecast[forecast['ds'] > data_max_global][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        
        forecast_futuro = forecast_futuro.head(8)

        forecast_futuro['sku'] = sku
        forecast_futuro['data_referencia'] = forecast_futuro['ds'].dt.date
        forecast_futuro['qtd_prevista'] = forecast_futuro['yhat'].round(3).clip(lower=0)
        forecast_futuro['intervalo_inferior'] = forecast_futuro['yhat_lower'].round(3).clip(lower=0)
        forecast_futuro['intervalo_superior'] = forecast_futuro['yhat_upper'].round(3).clip(lower=0)
        forecast_futuro['confianca'] = 95.0
        forecast_futuro['modelo_versao'] = 'v1'

        colunas = ['sku', 'data_referencia', 'qtd_prevista', 'intervalo_inferior', 'intervalo_superior', 'confianca', 'modelo_versao']
        df_final_sku = forecast_futuro[colunas]
        
        df_final_sku.to_sql('previsao_demanda', engine, if_exists='append', index=False)
        
        logging.info(f"Sucesso - SKU: {sku} finalizado e SALVO.")
        print(f"[{contador}/{len(skus)}] SKU {sku} concluído e salvo no banco.")

    except Exception as e:
        erro = traceback.format_exc()
        logging.error(f"ERRO {sku}:\n{erro}")
        print(f"[{contador}/{len(skus)}] ERRO {sku}. Verifique o log.")
    
    contador += 1

print("\nExecução finalizada! Todos os SKUs que tiveram sucesso já estão no seu banco de dados.")
logging.info("--- FINALIZADO COM SUCESSO ---")