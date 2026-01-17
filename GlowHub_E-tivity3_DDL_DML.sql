-- GlowHub - E-tivity 3 (MySQL 8+)
-- Progettazione fisica: base dati, tabelle, PK/FK, vincoli e indici

DROP DATABASE IF EXISTS glowhub_db;
CREATE DATABASE glowhub_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE glowhub_db;

-- =========================
-- ANAGRAFICHE
-- =========================

CREATE TABLE CLIENTE (
  idCliente          INT AUTO_INCREMENT PRIMARY KEY,
  email              VARCHAR(255) NOT NULL,
  nome               VARCHAR(60)  NOT NULL,
  cognome            VARCHAR(60)  NOT NULL,
  dataRegistrazione  DATE         NOT NULL,
  CONSTRAINT uq_cliente_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE INDIRIZZO (
  idIndirizzo   INT AUTO_INCREMENT PRIMARY KEY,
  idCliente     INT NOT NULL,
  via           VARCHAR(120) NOT NULL,
  civico        VARCHAR(10),
  citta         VARCHAR(80)  NOT NULL,
  CAP           VARCHAR(10),
  provincia     VARCHAR(40),
  paese         VARCHAR(60)  NOT NULL,
  tipo          ENUM('SPEDIZIONE','FATTURAZIONE') NOT NULL,
  isDefault     BOOLEAN NOT NULL DEFAULT 0,
  CONSTRAINT fk_indirizzo_cliente
    FOREIGN KEY (idCliente) REFERENCES CLIENTE(idCliente)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_indirizzo_cliente ON INDIRIZZO(idCliente);

-- =========================
-- CATALOGO
-- =========================

CREATE TABLE CATEGORIA (
  idCategoria        INT AUTO_INCREMENT PRIMARY KEY,
  idCategoriaPadre   INT NULL,
  nome               VARCHAR(80)  NOT NULL,
  descrizione        VARCHAR(255),
  CONSTRAINT fk_categoria_padre
    FOREIGN KEY (idCategoriaPadre) REFERENCES CATEGORIA(idCategoria)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE PRODOTTO (
  sku           VARCHAR(32) PRIMARY KEY,
  idCategoria   INT NOT NULL,
  nome          VARCHAR(120) NOT NULL,
  brand         VARCHAR(80),
  descrizione   TEXT,
  prezzoListino DECIMAL(10,2) NOT NULL,
  aliquotaIVA   DECIMAL(5,2)  NOT NULL,
  stato         ENUM('ATTIVO','NON_ATTIVO') NOT NULL DEFAULT 'ATTIVO',
  CONSTRAINT fk_prodotto_categoria
    FOREIGN KEY (idCategoria) REFERENCES CATEGORIA(idCategoria)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_prezzoListino_pos CHECK (prezzoListino >= 0),
  CONSTRAINT ck_aliquotaIVA_pos CHECK (aliquotaIVA >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_prodotto_categoria ON PRODOTTO(idCategoria);

-- =========================
-- CARRELLO
-- =========================

CREATE TABLE CARRELLO (
  idCarrello          INT AUTO_INCREMENT PRIMARY KEY,
  idCliente           INT NOT NULL,
  dataCreazione       DATETIME NOT NULL,
  dataUltimaModifica  DATETIME NOT NULL,
  CONSTRAINT uq_carrello_cliente UNIQUE (idCliente),
  CONSTRAINT fk_carrello_cliente
    FOREIGN KEY (idCliente) REFERENCES CLIENTE(idCliente)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE VOCE_CARRELLO (
  idVoceCarrello  INT AUTO_INCREMENT PRIMARY KEY,
  idCarrello      INT NOT NULL,
  sku             VARCHAR(32) NOT NULL,
  quantita        INT NOT NULL,
  prezzoVisto     DECIMAL(10,2) NOT NULL,
  dataAggiunta    DATETIME NOT NULL,
  CONSTRAINT fk_vocecarrello_carrello
    FOREIGN KEY (idCarrello) REFERENCES CARRELLO(idCarrello)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_vocecarrello_prodotto
    FOREIGN KEY (sku) REFERENCES PRODOTTO(sku)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_vocecarrello_carrello_sku UNIQUE (idCarrello, sku),
  CONSTRAINT ck_vocecarrello_quantita_pos CHECK (quantita > 0),
  CONSTRAINT ck_vocecarrello_prezzo_pos CHECK (prezzoVisto >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_vocecarrello_carrello ON VOCE_CARRELLO(idCarrello);
CREATE INDEX idx_vocecarrello_sku      ON VOCE_CARRELLO(sku);

-- =========================
-- ORDINI
-- =========================

CREATE TABLE ORDINE (
  idOrdine               INT AUTO_INCREMENT PRIMARY KEY,
  idCliente              INT NOT NULL,
  idIndirizzoSpedizione  INT NOT NULL,
  dataCreazione          DATETIME NOT NULL,
  statoOrdine            ENUM('CREATO','PAGATO','IN_PREPARAZIONE','SPEDITO','CONSEGNATO','ANNULLATO') NOT NULL,
  totaleLordo            DECIMAL(10,2) NOT NULL,
  totaleSconti           DECIMAL(10,2) NOT NULL,
  totaleNetto            DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_ordine_cliente
    FOREIGN KEY (idCliente) REFERENCES CLIENTE(idCliente)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_ordine_indirizzo
    FOREIGN KEY (idIndirizzoSpedizione) REFERENCES INDIRIZZO(idIndirizzo)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_totali_nonneg CHECK (totaleLordo >= 0 AND totaleSconti >= 0 AND totaleNetto >= 0),
  CONSTRAINT ck_totaleNetto_coerente CHECK (totaleNetto = totaleLordo - totaleSconti)
) ENGINE=InnoDB;

CREATE INDEX idx_ordine_cliente_data ON ORDINE(idCliente, dataCreazione);

CREATE TABLE RIGA_ORDINE (
  idRigaOrdine             INT AUTO_INCREMENT PRIMARY KEY,
  idOrdine                 INT NOT NULL,
  sku                      VARCHAR(32) NOT NULL,
  quantita                 INT NOT NULL,
  prezzoUnitarioApplicato  DECIMAL(10,2) NOT NULL,
  scontoRiga               DECIMAL(10,2) NOT NULL DEFAULT 0,
  CONSTRAINT fk_rigaordine_ordine
    FOREIGN KEY (idOrdine) REFERENCES ORDINE(idOrdine)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_rigaordine_prodotto
    FOREIGN KEY (sku) REFERENCES PRODOTTO(sku)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_rigaordine_ordine_sku UNIQUE (idOrdine, sku),
  CONSTRAINT ck_rigaordine_quantita_pos CHECK (quantita > 0),
  CONSTRAINT ck_rigaordine_prezzo_pos CHECK (prezzoUnitarioApplicato >= 0),
  CONSTRAINT ck_rigaordine_sconto_pos CHECK (scontoRiga >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_rigaordine_ordine ON RIGA_ORDINE(idOrdine);
CREATE INDEX idx_rigaordine_sku    ON RIGA_ORDINE(sku);

-- =========================
-- PAGAMENTI
-- =========================

CREATE TABLE METODO_PAGAMENTO (
  idMetodo     INT AUTO_INCREMENT PRIMARY KEY,
  nomeMetodo   VARCHAR(50) NOT NULL,
  provider     VARCHAR(80)
) ENGINE=InnoDB;

CREATE TABLE PAGAMENTO (
  idPagamento    INT AUTO_INCREMENT PRIMARY KEY,
  idOrdine       INT NOT NULL,
  idMetodo       INT NOT NULL,
  importo        DECIMAL(10,2) NOT NULL,
  dataOra        DATETIME NOT NULL,
  esito          ENUM('OK','KO') NOT NULL,
  transactionId  VARCHAR(80),
  CONSTRAINT fk_pagamento_ordine
    FOREIGN KEY (idOrdine) REFERENCES ORDINE(idOrdine)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pagamento_metodo
    FOREIGN KEY (idMetodo) REFERENCES METODO_PAGAMENTO(idMetodo)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_pagamento_tx UNIQUE (transactionId),
  CONSTRAINT ck_pagamento_importo_pos CHECK (importo >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_pagamento_ordine_data ON PAGAMENTO(idOrdine, dataOra);

-- =========================
-- LOGISTICA
-- =========================

CREATE TABLE CORRIERE (
  idCorriere    INT AUTO_INCREMENT PRIMARY KEY,
  nome          VARCHAR(80) NOT NULL,
  customerCare  VARCHAR(120)
) ENGINE=InnoDB;

CREATE TABLE SPEDIZIONE (
  idSpedizione          INT AUTO_INCREMENT PRIMARY KEY,
  idOrdine              INT NOT NULL,
  idCorriere            INT NOT NULL,
  tracking              VARCHAR(80) NOT NULL,
  statoSpedizione       ENUM('PREPARAZIONE','IN_TRANSITO','CONSEGNATA','PROBLEMA') NOT NULL,
  dataSpedizione        DATETIME NOT NULL,
  dataStimataConsegna   DATE,
  CONSTRAINT fk_spedizione_ordine
    FOREIGN KEY (idOrdine) REFERENCES ORDINE(idOrdine)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_spedizione_corriere
    FOREIGN KEY (idCorriere) REFERENCES CORRIERE(idCorriere)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_spedizione_tracking UNIQUE (tracking)
) ENGINE=InnoDB;

CREATE INDEX idx_spedizione_ordine   ON SPEDIZIONE(idOrdine);
CREATE INDEX idx_spedizione_corriere ON SPEDIZIONE(idCorriere);

-- =========================
-- INVENTARIO E FORNITORI
-- =========================

CREATE TABLE MAGAZZINO (
  idMagazzino       INT AUTO_INCREMENT PRIMARY KEY,
  nome              VARCHAR(80) NOT NULL,
  indirizzoTestuale VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE SCORTA (
  idMagazzino      INT NOT NULL,
  sku              VARCHAR(32) NOT NULL,
  giacenza         INT NOT NULL,
  sogliaRiordino   INT NOT NULL,
  dataAggiornamento DATETIME NOT NULL,
  PRIMARY KEY (idMagazzino, sku),
  CONSTRAINT fk_scorta_magazzino
    FOREIGN KEY (idMagazzino) REFERENCES MAGAZZINO(idMagazzino)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_scorta_prodotto
    FOREIGN KEY (sku) REFERENCES PRODOTTO(sku)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_scorta_giacenza_nonneg CHECK (giacenza >= 0),
  CONSTRAINT ck_scorta_soglia_nonneg CHECK (sogliaRiordino >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_scorta_sku ON SCORTA(sku);

CREATE TABLE FORNITORE (
  idFornitore     INT AUTO_INCREMENT PRIMARY KEY,
  ragioneSociale  VARCHAR(120) NOT NULL,
  piva            VARCHAR(20) NOT NULL,
  email           VARCHAR(255),
  CONSTRAINT uq_fornitore_piva UNIQUE (piva)
) ENGINE=InnoDB;

CREATE TABLE FORNITURA_PRODOTTO (
  idFornitore     INT NOT NULL,
  sku             VARCHAR(32) NOT NULL,
  prezzoAcquisto  DECIMAL(10,2) NOT NULL,
  leadTimeGiorni  INT NOT NULL,
  PRIMARY KEY (idFornitore, sku),
  CONSTRAINT fk_fornitura_fornitore
    FOREIGN KEY (idFornitore) REFERENCES FORNITORE(idFornitore)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_fornitura_prodotto
    FOREIGN KEY (sku) REFERENCES PRODOTTO(sku)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_fornitura_prezzo_nonneg CHECK (prezzoAcquisto >= 0),
  CONSTRAINT ck_fornitura_leadtime_nonneg CHECK (leadTimeGiorni >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_fornitura_sku ON FORNITURA_PRODOTTO(sku);

-- =========================
-- COUPON, RECENSIONI, RESI
-- =========================

CREATE TABLE COUPON (
  codiceCoupon  VARCHAR(30) PRIMARY KEY,
  tipo          ENUM('PERCENTUALE','FISSO') NOT NULL,
  valore        DECIMAL(10,2) NOT NULL,
  dataInizio    DATE NOT NULL,
  dataFine      DATE NOT NULL,
  minimoOrdine  DECIMAL(10,2) NOT NULL DEFAULT 0,
  maxUtilizzi   INT NOT NULL,
  CONSTRAINT ck_coupon_valore_nonneg CHECK (valore >= 0),
  CONSTRAINT ck_coupon_date_coerenti CHECK (dataFine >= dataInizio),
  CONSTRAINT ck_coupon_maxutilizzi_pos CHECK (maxUtilizzi > 0)
) ENGINE=InnoDB;

CREATE TABLE ORDINE_COUPON (
  idOrdine                 INT PRIMARY KEY,
  codiceCoupon             VARCHAR(30) NOT NULL,
  dataApplicazione         DATETIME NOT NULL,
  importoScontoCalcolato   DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_ordinecoupon_ordine
    FOREIGN KEY (idOrdine) REFERENCES ORDINE(idOrdine)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ordinecoupon_coupon
    FOREIGN KEY (codiceCoupon) REFERENCES COUPON(codiceCoupon)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT ck_ordinecoupon_sconto_nonneg CHECK (importoScontoCalcolato >= 0)
) ENGINE=InnoDB;

CREATE INDEX idx_ordinecoupon_coupon ON ORDINE_COUPON(codiceCoupon);

CREATE TABLE RECENSIONE (
  idRecensione    INT AUTO_INCREMENT PRIMARY KEY,
  idCliente       INT NOT NULL,
  sku             VARCHAR(32) NOT NULL,
  voto            TINYINT NOT NULL,
  titolo          VARCHAR(120),
  testo           TEXT,
  dataRecensione  DATE NOT NULL,
  CONSTRAINT fk_recensione_cliente
    FOREIGN KEY (idCliente) REFERENCES CLIENTE(idCliente)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_recensione_prodotto
    FOREIGN KEY (sku) REFERENCES PRODOTTO(sku)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT uq_recensione_cliente_sku UNIQUE (idCliente, sku),
  CONSTRAINT ck_recensione_voto CHECK (voto BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE INDEX idx_recensione_sku_data ON RECENSIONE(sku, dataRecensione);

CREATE TABLE RESO (
  idReso        INT AUTO_INCREMENT PRIMARY KEY,
  idRigaOrdine  INT NOT NULL,
  motivo        VARCHAR(255) NOT NULL,
  statoReso     ENUM('APERTO','APPROVATO','RIFIUTATO','RIMBORSATO') NOT NULL,
  dataApertura  DATE NOT NULL,
  CONSTRAINT uq_reso_rigaordine UNIQUE (idRigaOrdine),
  CONSTRAINT fk_reso_rigaordine
    FOREIGN KEY (idRigaOrdine) REFERENCES RIGA_ORDINE(idRigaOrdine)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_reso_stato ON RESO(statoReso);

-- =========================
-- DML: dati di esempio (minimi ma coerenti)
-- =========================

-- Clienti
INSERT INTO CLIENTE (email, nome, cognome, dataRegistrazione) VALUES
('gabriel.rossi@example.com', 'Gabriel', 'Rossi', '2025-09-01'),
('chiara.bianchi@example.com', 'Chiara', 'Bianchi', '2025-09-05'),
('luca.verdi@example.com', 'Luca', 'Verdi', '2025-09-10');

-- Indirizzi
INSERT INTO INDIRIZZO (idCliente, via, civico, citta, CAP, provincia, paese, tipo, isDefault) VALUES
(1, 'Via Roma', '10', 'Roma', '00100', 'RM', 'Italia', 'SPEDIZIONE', 1),
(1, 'Via Roma', '10', 'Roma', '00100', 'RM', 'Italia', 'FATTURAZIONE', 1),
(2, 'Corso Milano', '5', 'Milano', '20100', 'MI', 'Italia', 'SPEDIZIONE', 1),
(3, 'Via Napoli', '22', 'Napoli', '80100', 'NA', 'Italia', 'SPEDIZIONE', 1);

-- Categorie
INSERT INTO CATEGORIA (idCategoriaPadre, nome, descrizione) VALUES
(NULL, 'Skincare', 'Prodotti per la cura della pelle'),
(1, 'Detersione', 'Detergenti e struccanti'),
(NULL, 'Make-up', 'Trucco e accessori'),
(NULL, 'Haircare', 'Cura dei capelli');

-- Prodotti
INSERT INTO PRODOTTO (sku, idCategoria, nome, brand, descrizione, prezzoListino, aliquotaIVA, stato) VALUES
('GH-SKIN-001', 2, 'Gel Detergente Delicato', 'GlowBasics', 'Detergente viso per uso quotidiano', 12.90, 22.00, 'ATTIVO'),
('GH-SKIN-002', 1, 'Crema Idratante', 'GlowBasics', 'Crema idratante viso 50ml', 18.50, 22.00, 'ATTIVO'),
('GH-MAKE-001', 3, 'Mascara Volume', 'LuxeLash', 'Mascara effetto volume', 14.90, 22.00, 'ATTIVO'),
('GH-HAIR-001', 4, 'Shampoo Nutriente', 'SilkHair', 'Shampoo nutriente 250ml', 9.90, 22.00, 'ATTIVO');

-- Carrelli (1 per cliente)
INSERT INTO CARRELLO (idCliente, dataCreazione, dataUltimaModifica) VALUES
(1, '2025-10-01 10:00:00', '2025-10-01 10:05:00'),
(2, '2025-10-02 09:30:00', '2025-10-02 09:31:00'),
(3, '2025-10-03 18:10:00', '2025-10-03 18:10:00');

-- Voci carrello
INSERT INTO VOCE_CARRELLO (idCarrello, sku, quantita, prezzoVisto, dataAggiunta) VALUES
(1, 'GH-SKIN-001', 1, 12.90, '2025-10-01 10:01:00'),
(1, 'GH-SKIN-002', 1, 18.50, '2025-10-01 10:02:00'),
(2, 'GH-MAKE-001', 2, 14.90, '2025-10-02 09:30:30');

-- Metodi pagamento
INSERT INTO METODO_PAGAMENTO (nomeMetodo, provider) VALUES
('Carta', 'Stripe'),
('PayPal', 'PayPal');

-- Coupon
INSERT INTO COUPON (codiceCoupon, tipo, valore, dataInizio, dataFine, minimoOrdine, maxUtilizzi) VALUES
('WELCOME10', 'PERCENTUALE', 10.00, '2025-09-01', '2026-09-01', 10.00, 1000),
('FREESHIP5', 'FISSO', 5.00, '2025-09-01', '2026-03-01', 20.00, 500);

-- Corrieri
INSERT INTO CORRIERE (nome, customerCare) VALUES
('PosteDelivery', 'assistenza@postedelivery.it'),
('FastExpress', 'support@fastexpress.example');

-- Ordini
-- Ordine 1 (Gabriel): lordo 31.40 (12.90+18.50), sconto 3.14 (10%), netto 28.26
INSERT INTO ORDINE (idCliente, idIndirizzoSpedizione, dataCreazione, statoOrdine, totaleLordo, totaleSconti, totaleNetto) VALUES
(1, 1, '2025-10-01 10:10:00', 'PAGATO', 31.40, 3.14, 28.26);

-- Righe ordine (Ordine 1)
INSERT INTO RIGA_ORDINE (idOrdine, sku, quantita, prezzoUnitarioApplicato, scontoRiga) VALUES
(1, 'GH-SKIN-001', 1, 12.90, 1.29),
(1, 'GH-SKIN-002', 1, 18.50, 1.85);

-- Applica coupon a Ordine 1
INSERT INTO ORDINE_COUPON (idOrdine, codiceCoupon, dataApplicazione, importoScontoCalcolato) VALUES
(1, 'WELCOME10', '2025-10-01 10:10:10', 3.14);

-- Pagamenti (Ordine 1)
INSERT INTO PAGAMENTO (idOrdine, idMetodo, importo, dataOra, esito, transactionId) VALUES
(1, 1, 28.26, '2025-10-01 10:10:30', 'OK', 'TXN-0001-OK');

-- Spedizione (Ordine 1)
INSERT INTO SPEDIZIONE (idOrdine, idCorriere, tracking, statoSpedizione, dataSpedizione, dataStimataConsegna) VALUES
(1, 2, 'TRACK-FASTE-0001', 'IN_TRANSITO', '2025-10-01 16:00:00', '2025-10-03');

-- Ordine 2 (Chiara): 2 mascara (29.80), sconto 0, netto 29.80
INSERT INTO ORDINE (idCliente, idIndirizzoSpedizione, dataCreazione, statoOrdine, totaleLordo, totaleSconti, totaleNetto) VALUES
(2, 3, '2025-10-02 09:40:00', 'CREATO', 29.80, 0.00, 29.80);

INSERT INTO RIGA_ORDINE (idOrdine, sku, quantita, prezzoUnitarioApplicato, scontoRiga) VALUES
(2, 'GH-MAKE-001', 2, 14.90, 0.00);

-- Pagamento tentativo KO (Ordine 2)
INSERT INTO PAGAMENTO (idOrdine, idMetodo, importo, dataOra, esito, transactionId) VALUES
(2, 2, 29.80, '2025-10-02 09:41:00', 'KO', 'TXN-0002-KO');

-- Magazzini
INSERT INTO MAGAZZINO (nome, indirizzoTestuale) VALUES
('Magazzino Centro', 'Roma - Zona Tiburtina'),
('Magazzino Nord', 'Milano - Hinterland');

-- Scorte
INSERT INTO SCORTA (idMagazzino, sku, giacenza, sogliaRiordino, dataAggiornamento) VALUES
(1, 'GH-SKIN-001', 120, 20, '2025-10-01 08:00:00'),
(1, 'GH-SKIN-002',  40, 15, '2025-10-01 08:00:00'),
(2, 'GH-MAKE-001',  10, 25, '2025-10-01 08:00:00'),
(2, 'GH-HAIR-001',  60, 20, '2025-10-01 08:00:00');

-- Fornitori
INSERT INTO FORNITORE (ragioneSociale, piva, email) VALUES
('CosmoSupply S.r.l.', 'IT12345678901', 'ordini@cosmosupply.example'),
('BeautyWholesale S.p.A.', 'IT98765432109', 'sales@beautywholesale.example');

-- Forniture prodotto (M:N)
INSERT INTO FORNITURA_PRODOTTO (idFornitore, sku, prezzoAcquisto, leadTimeGiorni) VALUES
(1, 'GH-SKIN-001', 5.10, 7),
(1, 'GH-SKIN-002', 7.90, 7),
(2, 'GH-MAKE-001', 6.00, 10),
(2, 'GH-HAIR-001', 3.80, 6);

-- Recensioni (vincolo UQ: 1 recensione per coppia cliente-prodotto)
INSERT INTO RECENSIONE (idCliente, sku, voto, titolo, testo, dataRecensione) VALUES
(1, 'GH-SKIN-001', 5, 'Ottimo detergente', 'Delicato e non secca la pelle.', '2025-10-04');

-- Reso (0..1 per riga ordine) - supponiamo reso per la riga 2 dell'ordine 1 (Crema Idratante)
INSERT INTO RESO (idRigaOrdine, motivo, statoReso, dataApertura) VALUES
(2, 'Prodotto non conforme alle aspettative', 'APERTO', '2025-10-06');
