from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import select, and_
from sqlalchemy.engine import Engine

from .models import (
    Cliente, Ordine, RigaOrdine, Prodotto,
    Corriere, Spedizione, Magazzino, Scorta,
    OrdineCoupon, Recensione, Categoria
)

def q_ordini_cliente_email(email: str):
    return (
        select(Ordine.idOrdine, Ordine.dataCreazione, Ordine.statoOrdine, Ordine.totaleNetto)
        .join(Cliente, Cliente.idCliente == Ordine.idCliente)
        .where(Cliente.email == email)
        .order_by(Ordine.dataCreazione.desc())
    )

def q_dettaglio_ordine(id_ordine: int):
    return (
        select(Prodotto.sku, Prodotto.nome, RigaOrdine.quantita, RigaOrdine.prezzoUnitarioApplicato, RigaOrdine.scontoRiga)
        .join(RigaOrdine, RigaOrdine.sku == Prodotto.sku)
        .where(RigaOrdine.idOrdine == id_ordine)
        .order_by(Prodotto.sku)
    )

def q_spedizioni_corriere_periodo(nome_corriere: str, dal: datetime, al: datetime):
    return (
        select(Spedizione.tracking, Spedizione.statoSpedizione, Spedizione.dataSpedizione, Ordine.idOrdine, Cliente.email)
        .join(Corriere, Corriere.idCorriere == Spedizione.idCorriere)
        .join(Ordine, Ordine.idOrdine == Spedizione.idOrdine)
        .join(Cliente, Cliente.idCliente == Ordine.idCliente)
        .where(and_(Corriere.nome == nome_corriere, Spedizione.dataSpedizione >= dal, Spedizione.dataSpedizione <= al))
        .order_by(Spedizione.dataSpedizione.desc())
    )

def q_prodotti_sotto_soglia():
    return (
        select(Magazzino.nome, Prodotto.sku, Prodotto.nome, Scorta.giacenza, Scorta.sogliaRiordino)
        .join(Magazzino, Magazzino.idMagazzino == Scorta.idMagazzino)
        .join(Prodotto, Prodotto.sku == Scorta.sku)
        .where(Scorta.giacenza < Scorta.sogliaRiordino)
        .order_by(Magazzino.nome, Prodotto.sku)
    )

def q_clienti_che_hanno_usato_coupon(codice: str):
    return (
        select(Cliente.email, Ordine.idOrdine, OrdineCoupon.dataApplicazione, OrdineCoupon.importoScontoCalcolato)
        .join(Ordine, Ordine.idOrdine == OrdineCoupon.idOrdine)
        .join(Cliente, Cliente.idCliente == Ordine.idCliente)
        .where(OrdineCoupon.codiceCoupon == codice)
        .order_by(OrdineCoupon.dataApplicazione.desc())
    )

def q_recensioni_per_categoria(nome_categoria: str):
    return (
        select(Prodotto.sku, Prodotto.nome, Cliente.email, Recensione.voto, Recensione.titolo, Recensione.dataRecensione)
        .join(Categoria, Categoria.idCategoria == Prodotto.idCategoria)
        .join(Recensione, Recensione.sku == Prodotto.sku)
        .join(Cliente, Cliente.idCliente == Recensione.idCliente)
        .where(Categoria.nome == nome_categoria)
        .order_by(Recensione.dataRecensione.desc())
    )

def compile_sql(engine: Engine, stmt) -> str:
    return str(stmt.compile(engine, compile_kwargs={"literal_binds": True}))

def export_queries_sql(engine: Engine, path: str) -> None:
    dal = datetime.now().replace(microsecond=0) - timedelta(days=30)
    al = datetime.now().replace(microsecond=0)

    statements = {
        "-- Q1 Ordini di un cliente (email)": q_ordini_cliente_email("gabriel.rossi@example.com"),
        "-- Q2 Dettaglio ordine (id=1)": q_dettaglio_ordine(1),
        "-- Q3 Spedizioni corriere nel periodo": q_spedizioni_corriere_periodo("PosteDelivery", dal, al),
        "-- Q4 Prodotti sotto soglia": q_prodotti_sotto_soglia(),
        "-- Q5 Clienti che hanno usato coupon": q_clienti_che_hanno_usato_coupon("WELCOME10"),
        "-- Q6 Recensioni per categoria": q_recensioni_per_categoria("Detersione"),
    }

    lines: list[str] = []
    for title, stmt in statements.items():
        lines.append(title)
        lines.append(compile_sql(engine, stmt) + ";")
        lines.append("")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
