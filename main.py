import sys
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery

# Configuração de Log para acompanhamento profissional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoinCapAPI:
    def __init__(self):
        self.base_url = "https://api.coincap.io/v2/assets"
        self.headers = {'Accept-Encoding': 'gzip'}

    def fetch_data(self, limit=100, retries=3):
        """Busca dados da API lidando com Rate Limit e falhas de rede"""
        params = {'limit': limit}
        
        for attempt in range(retries):
            try:
                logging.info(f"Tentativa {attempt + 1} de conectar na API da CoinCap...")
                # Adicionado timeout de 15 segundos para evitar travamentos de rede
                response = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
                
                if response.status_code == 429:
                    logging.warning("Rate limit atingido. Aguardando 10 segundos...")
                    time.sleep(10)
                    continue
                
                response.raise_for_status()
                logging.info("Dados extraídos com sucesso!")
                return response.json()['data']
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro ao acessar API: {e}")
                if attempt == retries - 1:
                    raise # Se foi a última tentativa, explode o erro
                
                # Aguarda 5 segundos antes de tentar de novo (ajuda em quedas de DNS)
                logging.info("Aguardando 5 segundos antes da próxima tentativa...")
                time.sleep(5) 

class CryptoTransformer:
    @staticmethod
    def process_data(raw_data):
        """Recebe o JSON e divide na modelagem Dimensão e Fato"""
        logging.info("Iniciando a transformação e separação dos dados (Dimensão e Fato)...")
        df_raw = pd.DataFrame(raw_data)
        
        extracted_at = datetime.utcnow()
        
        # 1. Tabela Dimensão (Dados cadastrais)
        df_dim = df_raw[['id', 'symbol', 'name', 'explorer']].copy()
        
        # 2. Tabela Fato (Métricas financeiras)
        numeric_cols = ['priceUsd', 'marketCapUsd', 'volumeUsd24Hr', 'changePercent24Hr']
        for col in numeric_cols:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
            
        df_fato = df_raw[['id', 'priceUsd', 'marketCapUsd', 'volumeUsd24Hr', 'changePercent24Hr']].copy()
        df_fato.rename(columns={'id': 'id_criptomoeda'}, inplace=True)
        df_fato['extracted_at'] = extracted_at
        
        logging.info("Transformação concluída com sucesso.")
        return df_dim, df_fato

class BigQueryLoader:
    def __init__(self, project_id, dataset_id):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id

    def load_dataframe(self, df, table_name, write_disposition="WRITE_TRUNCATE"):
        """Carrega o DataFrame para o BigQuery"""
        table_id = f"{self.client.project}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
        )
        
        logging.info(f"Iniciando carga na tabela {table_id}...")
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logging.info(f"Carga concluída! {job.output_rows} linhas inseridas em {table_name}.")

def main():
    # ==========================================
    # CONFIGURAÇÕES DA CAMADA RAW
    # ==========================================
    GCP_PROJECT_ID = 'case-de-specialist-gb'
    BQ_DATASET_ID = 'raw_crypto_market_data'
    
    try:
        # 1. Extração
        api = CoinCapAPI()
        raw_data = api.fetch_data(limit=100)
        
        # 2. Transformação
        transformer = CryptoTransformer()
        df_dim, df_fato = transformer.process_data(raw_data)
        
        # 3. Carga no BigQuery
        loader = BigQueryLoader(GCP_PROJECT_ID, BQ_DATASET_ID)
        
        # Dimensão (Substitui tudo) e Fato (Faz Append histórico)
        loader.load_dataframe(df_dim, "dim_criptomoeda", write_disposition="WRITE_TRUNCATE")
        loader.load_dataframe(df_fato, "fato_cotacao_cripto", write_disposition="WRITE_APPEND")
        
        logging.info("Pipeline finalizado com sucesso!")
        
    except Exception as e:
        logging.error(f"Pipeline falhou de forma crítica: {e}")
        sys.exit(1) # Agora o GitHub Actions VAI mostrar vermelho se falhar!

if __name__ == "__main__":
    main()
