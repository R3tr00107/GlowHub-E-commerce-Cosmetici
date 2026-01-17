-- Interrogazioni SQL per l'applicativo (sezione 11 documento)
-- Nota: queste query corrispondono ai report implementati in glowhub/queries.py.
-- I parametri sono indicati come :param.

-- Q1 Ordini di un cliente (email)
SELECT O.idOrdine, O.dataCreazione, O.statoOrdine, O.totaleNetto
FROM ORDINE O
JOIN CLIENTE C ON C.idCliente = O.idCliente
WHERE C.email = :email
ORDER BY O.dataCreazione DESC;

-- Q2 Dettaglio articoli di un ordine
SELECT P.sku, P.nome, R.quantita, R.prezzoUnitarioApplicato, R.scontoRiga
FROM RIGA_ORDINE R
JOIN PRODOTTO P ON P.sku = R.sku
WHERE R.idOrdine = :idOrdine
ORDER BY P.sku;

-- Q3 Spedizioni di un corriere in un periodo
SELECT S.tracking, S.statoSpedizione, S.dataSpedizione, O.idOrdine, C.email
FROM SPEDIZIONE S
JOIN CORRIERE K ON K.idCorriere = S.idCorriere
JOIN ORDINE O ON O.idOrdine = S.idOrdine
JOIN CLIENTE C ON C.idCliente = O.idCliente
WHERE K.nome = :nomeCorriere
  AND S.dataSpedizione BETWEEN :dal AND :al
ORDER BY S.dataSpedizione DESC;

-- Q4 Prodotti sotto soglia riordino
SELECT M.nome, P.sku, P.nome, S.giacenza, S.sogliaRiordino
FROM SCORTA S
JOIN MAGAZZINO M ON M.idMagazzino = S.idMagazzino
JOIN PRODOTTO P ON P.sku = S.sku
WHERE S.giacenza < S.sogliaRiordino
ORDER BY M.nome, P.sku;

-- Q5 Clienti che hanno usato un coupon
SELECT C.email, O.idOrdine, OC.dataApplicazione, OC.importoScontoCalcolato
FROM ORDINE_COUPON OC
JOIN ORDINE O ON O.idOrdine = OC.idOrdine
JOIN CLIENTE C ON C.idCliente = O.idCliente
WHERE OC.codiceCoupon = :codiceCoupon
ORDER BY OC.dataApplicazione DESC;

-- Q6 Recensioni per categoria (nome)
SELECT P.sku, P.nome, C.email, R.voto, R.titolo, R.dataRecensione
FROM PRODOTTO P
JOIN CATEGORIA G ON G.idCategoria = P.idCategoria
JOIN RECENSIONE R ON R.sku = P.sku
JOIN CLIENTE C ON C.idCliente = R.idCliente
WHERE G.nome = :nomeCategoria
ORDER BY R.dataRecensione DESC;
