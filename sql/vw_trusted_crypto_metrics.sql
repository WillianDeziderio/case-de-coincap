-- Criação da Camada Trusted (View para o Dataviz)
CREATE OR REPLACE VIEW `case-de-specialist-gb.crypto_market_data.vw_trusted_crypto_metrics` AS
SELECT 
    DATE(f.extracted_at) AS data_referencia,
    f.extracted_at AS data_hora_extracao,
    d.name AS nome_moeda,
    d.symbol AS simbolo,
    f.priceUsd AS preco_usd,
    f.marketCapUsd AS valor_mercado_usd,
    f.volumeUsd24Hr AS volume_24h_usd,
    f.changePercent24Hr AS variacao_24h_pct,
    d.explorer AS link_blockchain
FROM `case-de-specialist-gb.crypto_market_data.fato_cotacao_cripto` f
LEFT JOIN `case-de-specialist-gb.crypto_market_data.dim_criptomoeda` d
    ON f.id_criptomoeda = d.id;
