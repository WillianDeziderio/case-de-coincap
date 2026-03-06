-- DDL para a Tabela Dimensão (Cadastro)
CREATE TABLE IF NOT EXISTS `case-de-specialist-gb.raw_crypto_market_data.dim_criptomoeda` (
    id STRING OPTIONS(description="Identificador único da criptomoeda na API CoinCap"),
    symbol STRING OPTIONS(description="Símbolo de negociação (ex: BTC, ETH)"),
    name STRING OPTIONS(description="Nome completo da criptomoeda"),
    explorer STRING OPTIONS(description="URL do explorador do blockchain")
);
