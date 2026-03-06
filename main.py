import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import time
import logging

# Configuração de Log para acompanhamento profissional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoinCapAPI:
    def __init__(self):
        self.base_url = "https://api.coincap.io/v2/assets"
        self.headers = {'Accept-Encoding': 'gzip'} # Boa prática para APIs

    def fetch_data(self, limit=100, retries=3):
        """Busca dados da API lidando com possível Rate Limit (HTTP 429)"""
        params = {'limit': limit}
        
        for attempt in range(retries):
            try:
                logging.info(f"Tentativa {attempt + 1} de conectar na API da CoinCap...")
                response = requests.get(self.base_url, headers=self.headers, params=params)
                
                # Se der 429 (Too Many Requests), a gente espera e tenta de novo
                if response.status_code == 429:
                    logging.warning("Rate limit atingido. Aguardando 10 segundos...")
                    time.sleep(10)
                    continue
                
                response.raise_for_status() # Dispara erro se não for 200 OK
                logging.info("Dados extraídos com sucesso!")
                return response.json()['data']
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro ao acessar API: {e}")
                if attempt == retries - 1:
                    raise

class CryptoTransformer:
    @staticmethod
    def process_data(raw_data):
        """Recebe o JSON e divide na modelagem Dimensão e Fato"""
        logging.info("Iniciando a transformação e separação dos dados (Dimensão e Fato)...")
        df_raw = pd.DataFrame(raw_data)
        
        # O momento exato da extração para a nossa tabela fato
        extracted_at = datetime.utcnow()
        
        # 1. Tabela Dimensão (Dados cadastrais)
        df_dim = df_raw[['id', 'symbol', 'name', 'explorer']].copy()
        
        # 2. Tabela Fato (Métricas financeiras)
        # Convertendo as strings da API para numéricos antes de mandar pro BQ
        numeric_cols = ['priceUsd', 'marketCapUsd', 'volumeUsd24Hr', 'changePercent24Hr']
        for col in numeric_cols:
            df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
            
        df_fato = df_raw[['id', 'priceUsd', 'marketCapUsd', 'volumeUsd24Hr', 'changePercent24Hr']].copy()
        df_fato.rename(columns={'id': 'id_criptomoeda'}, inplace=True) # Chave Estrangeira
        df_fato['extracted_at'] = extracted_at # Carimbo de tempo
        
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
            write_disposition=write_disposition, # WRITE_TRUNCATE p/ dimensão, WRITE_APPEND p/ fato
        )
        
        logging.info(f"Iniciando carga na tabela {table_id}...")
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result() # Espera o job terminar
        
        logging.info(f"Carga concluída! {job.output_rows} linhas inseridas em {table_name}.")

def main():
    # ==========================================
    # CONFIGURAÇÕES (Altere para o seu projeto)
    # ==========================================
    GCP_PROJECT_ID = 'case-de-specialist-gb'
    BQ_DATASET_ID = 'crypto_market_data'
    
    try:
        # 1. Extração
        api = CoinCapAPI()
        raw_data = api.fetch_data(limit=100) # Trazendo o top 100 criptomoedas
        
        # 2. Transformação
        transformer = CryptoTransformer()
        df_dim, df_fato = transformer.process_data(raw_data)
        
        # 3. Carga no BigQuery
        loader = BigQueryLoader(GCP_PROJECT_ID, BQ_DATASET_ID)
        
        # Para a dimensão, substituímos tudo (WRITE_TRUNCATE) para atualizar nomes/links
        loader.load_dataframe(df_dim, "dim_criptomoeda", write_disposition="WRITE_TRUNCATE")
        
        # Para a Fato, nós adicionamos o histórico (WRITE_APPEND)
        loader.load_dataframe(df_fato, "fato_cotacao_cripto", write_disposition="WRITE_APPEND")
        
        logging.info("Pipeline finalizado com sucesso!")
        
    except Exception as e:
        logging.error(f"Pipeline falhou: {e}")

if __name__ == "__main__":
    main()
