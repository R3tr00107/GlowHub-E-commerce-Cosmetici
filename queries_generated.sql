-- Q1 Ordini di un cliente (email)
SELECT "ORDINE"."idOrdine", "ORDINE"."dataCreazione", "ORDINE"."statoOrdine", "ORDINE"."totaleNetto" 
FROM "ORDINE" JOIN "CLIENTE" ON "CLIENTE"."idCliente" = "ORDINE"."idCliente" 
WHERE "CLIENTE".email = 'gabriel.rossi@example.com' ORDER BY "ORDINE"."dataCreazione" DESC;

-- Q2 Dettaglio ordine (id=1)
SELECT "PRODOTTO".sku, "PRODOTTO".nome, "RIGA_ORDINE".quantita, "RIGA_ORDINE"."prezzoUnitarioApplicato", "RIGA_ORDINE"."scontoRiga" 
FROM "PRODOTTO" JOIN "RIGA_ORDINE" ON "RIGA_ORDINE".sku = "PRODOTTO".sku 
WHERE "RIGA_ORDINE"."idOrdine" = 1 ORDER BY "PRODOTTO".sku;

-- Q3 Spedizioni corriere nel periodo
SELECT "SPEDIZIONE".tracking, "SPEDIZIONE"."statoSpedizione", "SPEDIZIONE"."dataSpedizione", "ORDINE"."idOrdine", "CLIENTE".email 
FROM "SPEDIZIONE" JOIN "CORRIERE" ON "CORRIERE"."idCorriere" = "SPEDIZIONE"."idCorriere" JOIN "ORDINE" ON "ORDINE"."idOrdine" = "SPEDIZIONE"."idOrdine" JOIN "CLIENTE" ON "CLIENTE"."idCliente" = "ORDINE"."idCliente" 
WHERE "CORRIERE".nome = 'PosteDelivery' AND "SPEDIZIONE"."dataSpedizione" >= '2025-12-02 10:41:12.000000' AND "SPEDIZIONE"."dataSpedizione" <= '2026-01-01 10:41:12.000000' ORDER BY "SPEDIZIONE"."dataSpedizione" DESC;

-- Q4 Prodotti sotto soglia
SELECT "MAGAZZINO".nome, "PRODOTTO".sku, "PRODOTTO".nome AS nome_1, "SCORTA".giacenza, "SCORTA"."sogliaRiordino" 
FROM "SCORTA" JOIN "MAGAZZINO" ON "MAGAZZINO"."idMagazzino" = "SCORTA"."idMagazzino" JOIN "PRODOTTO" ON "PRODOTTO".sku = "SCORTA".sku 
WHERE "SCORTA".giacenza < "SCORTA"."sogliaRiordino" ORDER BY "MAGAZZINO".nome, "PRODOTTO".sku;

-- Q5 Clienti che hanno usato coupon
SELECT "CLIENTE".email, "ORDINE"."idOrdine", "ORDINE_COUPON"."dataApplicazione", "ORDINE_COUPON"."importoScontoCalcolato" 
FROM "ORDINE_COUPON" JOIN "ORDINE" ON "ORDINE"."idOrdine" = "ORDINE_COUPON"."idOrdine" JOIN "CLIENTE" ON "CLIENTE"."idCliente" = "ORDINE"."idCliente" 
WHERE "ORDINE_COUPON"."codiceCoupon" = 'WELCOME10' ORDER BY "ORDINE_COUPON"."dataApplicazione" DESC;

-- Q6 Recensioni per categoria
SELECT "PRODOTTO".sku, "PRODOTTO".nome, "CLIENTE".email, "RECENSIONE".voto, "RECENSIONE".titolo, "RECENSIONE"."dataRecensione" 
FROM "PRODOTTO" JOIN "CATEGORIA" ON "CATEGORIA"."idCategoria" = "PRODOTTO"."idCategoria" JOIN "RECENSIONE" ON "RECENSIONE".sku = "PRODOTTO".sku JOIN "CLIENTE" ON "CLIENTE"."idCliente" = "RECENSIONE"."idCliente" 
WHERE "CATEGORIA".nome = 'Detersione' ORDER BY "RECENSIONE"."dataRecensione" DESC;
