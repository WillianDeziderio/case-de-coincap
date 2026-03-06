-- DDL para a Tabela Fato (Métricas e Cotações com Bitemporalidade)
CREATE TABLE IF NOT EXISTS `case-de-specialist-gb.raw_crypto_market_data.fato_cotacao_cripto` (
    id_criptomoeda STRING OPTIONS(description="Chave estrangeira ligando à dim_criptomoeda"),
    priceUsd FLOAT64 OPTIONS(description="Preço atual em Dólares (USD)"),
    marketCapUsd FLOAT64 OPTIONS(description="Capitalização de mercado em USD"),
    volumeUsd24Hr FLOAT64 OPTIONS(description="Volume negociado nas últimas 24 horas em USD"),
    changePercent24Hr FLOAT64 OPTIONS(description="Percentual de variação de preço nas últimas 24 horas"),
    data_cotacao TIMESTAMP OPTIONS(description="Tempo da Transação (Valid Time): Data e hora real da cotação no mercado"),
    data_extracao TIMESTAMP OPTIONS(description="Tempo do Sistema (Transaction Time): Data e hora em que o pipeline salvou o dado")
)
PARTITION BY DATE(data_cotacao)
CLUSTER BY id_criptomoeda;
