# GlowHub (E-tivity 4) - SQLAlchemy ORM + CRUD

Questo progetto implementa un applicativo Python basato su SQLAlchemy ORM che usa la base dati "GlowHub" progettata nelle E-tivity 1-2-3.

Include:
- Creazione tabelle via ORM (`init-db`)
- Inserimento dati di esempio (`seed`)
- Operazioni CRUD su entità principali (clienti, prodotti, carrello, ordine, pagamento, spedizione, recensione, reso)
- Interrogazioni "da applicativo" (report) in SQLAlchemy e export SQL

## Setup rapido

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Avvio (SQLite)
```bash
python app.py init-db
python app.py seed
python app.py demo
```

## Avvio (MySQL 8+)
1. Crea il DB (una volta sola):
```sql
CREATE DATABASE glowhub_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
```

2. Imposta `DATABASE_URL` in `.env`, poi:
```bash
python app.py init-db
python app.py seed
python app.py demo
```

## Comandi principali
- `init-db` / `drop-db`
- `seed`
- `demo` (esegue report e stampa anche la SQL compilata)
- `create-client`, `add-address`
- `create-category`, `create-product`
- `add-to-cart`, `checkout`
- `pay-order`
- `create-shipment`

> Per consegna E-tivity 4: carica questa cartella come repository su GitHub e allega il link.

- `update-product-price`, `delete-product`, `delete-client`, `remove-from-cart`
