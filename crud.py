from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Cliente, Indirizzo, Categoria, Prodotto, Carrello, VoceCarrello,
    Ordine, RigaOrdine, MetodoPagamento, Pagamento, Corriere, Spedizione,
    Magazzino, Scorta, Coupon, OrdineCoupon, Recensione, Reso,
    IndirizzoTipo, StatoOrdine, EsitoPagamento, StatoSpedizione, CouponTipo, StatoReso
)


def now_dt() -> datetime:
    return datetime.now().replace(microsecond=0)

def to_decimal(x) -> Decimal:
    return Decimal(str(x))

@dataclass
class CheckoutResult:
    ordine_id: int
    totale_lordo: Decimal
    totale_sconti: Decimal
    totale_netto: Decimal


# ----------------------------
# CLIENTE / INDIRIZZO (CRUD)
# ----------------------------
def create_cliente(session: Session, email: str, nome: str, cognome: str, data_reg: date | None = None) -> Cliente:
    data_reg = data_reg or date.today()
    c = Cliente(email=email, nome=nome, cognome=cognome, dataRegistrazione=data_reg)
    session.add(c)
    session.flush()  # assegna idCliente
    # crea carrello 1:1
    cart = Carrello(idCliente=c.idCliente, dataCreazione=now_dt(), dataUltimaModifica=now_dt())
    session.add(cart)
    session.commit()
    return c

def add_indirizzo(
    session: Session,
    id_cliente: int,
    via: str,
    citta: str,
    paese: str,
    tipo: IndirizzoTipo,
    civico: str | None = None,
    cap: str | None = None,
    provincia: str | None = None,
    is_default: bool = False,
) -> Indirizzo:
    a = Indirizzo(
        idCliente=id_cliente, via=via, civico=civico, citta=citta, CAP=cap,
        provincia=provincia, paese=paese, tipo=tipo, isDefault=is_default
    )
    session.add(a)
    session.commit()
    return a

def get_cliente_by_email(session: Session, email: str) -> Cliente | None:
    return session.scalar(select(Cliente).where(Cliente.email == email))

def delete_cliente(session: Session, id_cliente: int) -> None:
    c = session.get(Cliente, id_cliente)
    if not c:
        return
    session.delete(c)
    session.commit()


# ----------------------------
# CATEGORIA / PRODOTTO (CRUD)
# ----------------------------
def create_categoria(session: Session, nome: str, descrizione: str | None = None, id_padre: int | None = None) -> Categoria:
    cat = Categoria(nome=nome, descrizione=descrizione, idCategoriaPadre=id_padre)
    session.add(cat)
    session.commit()
    return cat

def create_prodotto(
    session: Session,
    sku: str,
    id_categoria: int,
    nome: str,
    prezzo_listino: float,
    aliquota_iva: float = 22.0,
    brand: str | None = None,
    descrizione: str | None = None,
) -> Prodotto:
    p = Prodotto(
        sku=sku, idCategoria=id_categoria, nome=nome, brand=brand, descrizione=descrizione,
        prezzoListino=to_decimal(prezzo_listino), aliquotaIVA=to_decimal(aliquota_iva)
    )
    session.add(p)
    session.commit()
    return p

def update_prezzo_prodotto(session: Session, sku: str, nuovo_prezzo: float) -> None:
    p = session.get(Prodotto, sku)
    if not p:
        raise ValueError(f"Prodotto {sku} non trovato")
    p.prezzoListino = to_decimal(nuovo_prezzo)
    session.commit()

def delete_prodotto(session: Session, sku: str) -> None:
    p = session.get(Prodotto, sku)
    if not p:
        return
    session.delete(p)
    session.commit()


# ----------------------------
# CARRELLO (CRUD)
# ----------------------------
def get_carrello_cliente(session: Session, id_cliente: int) -> Carrello:
    cart = session.scalar(select(Carrello).where(Carrello.idCliente == id_cliente))
    if not cart:
        cart = Carrello(idCliente=id_cliente, dataCreazione=now_dt(), dataUltimaModifica=now_dt())
        session.add(cart)
        session.commit()
    return cart

def add_to_cart(session: Session, id_cliente: int, sku: str, quantita: int) -> VoceCarrello:
    if quantita <= 0:
        raise ValueError("quantita deve essere > 0")

    cart = get_carrello_cliente(session, id_cliente)
    prodotto = session.get(Prodotto, sku)
    if not prodotto:
        raise ValueError(f"Prodotto {sku} non trovato")

    voce = session.scalar(
        select(VoceCarrello).where(VoceCarrello.idCarrello == cart.idCarrello, VoceCarrello.sku == sku)
    )
    if voce:
        voce.quantita += quantita
        cart.dataUltimaModifica = now_dt()
        session.commit()
        return voce

    voce = VoceCarrello(
        idCarrello=cart.idCarrello,
        sku=sku,
        quantita=quantita,
        prezzoVisto=prodotto.prezzoListino,
        dataAggiunta=now_dt()
    )
    session.add(voce)
    cart.dataUltimaModifica = now_dt()
    session.commit()
    return voce

def remove_from_cart(session: Session, id_cliente: int, sku: str) -> None:
    cart = get_carrello_cliente(session, id_cliente)
    voce = session.scalar(
        select(VoceCarrello).where(VoceCarrello.idCarrello == cart.idCarrello, VoceCarrello.sku == sku)
    )
    if voce:
        session.delete(voce)
        cart.dataUltimaModifica = now_dt()
        session.commit()


# ----------------------------
# CHECKOUT (Create Ordine + righe) + svuota carrello
# ----------------------------
def checkout(
    session: Session,
    id_cliente: int,
    id_indirizzo_spedizione: int,
    codice_coupon: str | None = None
) -> CheckoutResult:
    cart = get_carrello_cliente(session, id_cliente)
    voci = list(cart.voci)
    if not voci:
        raise ValueError("Carrello vuoto")

    totale_lordo = sum(to_decimal(v.prezzoVisto) * to_decimal(v.quantita) for v in voci)
    totale_sconti = Decimal("0.00")

    coupon = None
    if codice_coupon:
        coupon = session.get(Coupon, codice_coupon)
        if not coupon:
            raise ValueError("Coupon non valido")

        oggi = date.today()
        if not (coupon.dataInizio <= oggi <= coupon.dataFine):
            raise ValueError("Coupon non attivo")
        if totale_lordo < to_decimal(coupon.minimoOrdine):
            raise ValueError("Totale ordine sotto minimo coupon")

        if coupon.tipo == CouponTipo.PERCENTUALE:
            totale_sconti = (totale_lordo * to_decimal(coupon.valore) / Decimal("100.00")).quantize(Decimal("0.01"))
        else:
            totale_sconti = min(to_decimal(coupon.valore), totale_lordo)

    totale_netto = (totale_lordo - totale_sconti).quantize(Decimal("0.01"))

    ordine = Ordine(
        idCliente=id_cliente,
        idIndirizzoSpedizione=id_indirizzo_spedizione,
        dataCreazione=now_dt(),
        statoOrdine=StatoOrdine.CREATO,
        totaleLordo=totale_lordo,
        totaleSconti=totale_sconti,
        totaleNetto=totale_netto
    )
    session.add(ordine)
    session.flush()

    for v in voci:
        session.add(RigaOrdine(
            idOrdine=ordine.idOrdine,
            sku=v.sku,
            quantita=v.quantita,
            prezzoUnitarioApplicato=v.prezzoVisto,
            scontoRiga=Decimal("0.00")
        ))

    if coupon:
        session.add(OrdineCoupon(
            idOrdine=ordine.idOrdine,
            codiceCoupon=coupon.codiceCoupon,
            dataApplicazione=now_dt(),
            importoScontoCalcolato=totale_sconti
        ))

    # svuota carrello
    for v in voci:
        session.delete(v)

    cart.dataUltimaModifica = now_dt()
    session.commit()

    return CheckoutResult(ordine_id=ordine.idOrdine, totale_lordo=totale_lordo, totale_sconti=totale_sconti, totale_netto=totale_netto)


# ----------------------------
# PAGAMENTO (Create) + Update stato ordine
# ----------------------------
def ensure_metodo_pagamento(session: Session, nome: str, provider: str | None = None) -> MetodoPagamento:
    mp = session.scalar(select(MetodoPagamento).where(MetodoPagamento.nomeMetodo == nome))
    if mp:
        return mp
    mp = MetodoPagamento(nomeMetodo=nome, provider=provider)
    session.add(mp)
    session.commit()
    return mp

def pay_order(
    session: Session,
    id_ordine: int,
    metodo_nome: str,
    importo: float,
    esito: EsitoPagamento,
    transaction_id: str | None = None
) -> Pagamento:
    ordine = session.get(Ordine, id_ordine)
    if not ordine:
        raise ValueError("Ordine non trovato")

    metodo = ensure_metodo_pagamento(session, metodo_nome)

    p = Pagamento(
        idOrdine=id_ordine,
        idMetodo=metodo.idMetodo,
        importo=to_decimal(importo),
        dataOra=now_dt(),
        esito=esito,
        transactionId=transaction_id
    )
    session.add(p)

    if esito == EsitoPagamento.OK:
        ordine.statoOrdine = StatoOrdine.PAGATO

    session.commit()
    return p


# ----------------------------
# SPEDIZIONE (Create) + Update stato ordine
# ----------------------------
def ensure_corriere(session: Session, nome: str, customer_care: str | None = None) -> Corriere:
    c = session.scalar(select(Corriere).where(Corriere.nome == nome))
    if c:
        return c
    c = Corriere(nome=nome, customerCare=customer_care)
    session.add(c)
    session.commit()
    return c

def create_shipment(
    session: Session,
    id_ordine: int,
    nome_corriere: str,
    tracking: str,
    stato: StatoSpedizione = StatoSpedizione.PREPARAZIONE
) -> Spedizione:
    ordine = session.get(Ordine, id_ordine)
    if not ordine:
        raise ValueError("Ordine non trovato")

    corriere = ensure_corriere(session, nome_corriere)
    s = Spedizione(
        idOrdine=id_ordine,
        idCorriere=corriere.idCorriere,
        tracking=tracking,
        statoSpedizione=stato,
        dataSpedizione=now_dt(),
    )
    session.add(s)

    if ordine.statoOrdine in {StatoOrdine.PAGATO, StatoOrdine.IN_PREPARAZIONE, StatoOrdine.CREATO}:
        ordine.statoOrdine = StatoOrdine.SPEDITO

    session.commit()
    return s
