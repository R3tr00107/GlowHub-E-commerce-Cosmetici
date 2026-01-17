from __future__ import annotations

import enum
from datetime import date, datetime
from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --------------------
# ENUMs (come da DDL E-tivity 3)
# --------------------
class IndirizzoTipo(str, enum.Enum):
    SPEDIZIONE = "SPEDIZIONE"
    FATTURAZIONE = "FATTURAZIONE"


class ProdottoStato(str, enum.Enum):
    ATTIVO = "ATTIVO"
    NON_ATTIVO = "NON_ATTIVO"


class StatoOrdine(str, enum.Enum):
    CREATO = "CREATO"
    PAGATO = "PAGATO"
    IN_PREPARAZIONE = "IN_PREPARAZIONE"
    SPEDITO = "SPEDITO"
    CONSEGNATO = "CONSEGNATO"
    ANNULLATO = "ANNULLATO"


class EsitoPagamento(str, enum.Enum):
    OK = "OK"
    KO = "KO"


class StatoSpedizione(str, enum.Enum):
    PREPARAZIONE = "PREPARAZIONE"
    IN_TRANSITO = "IN_TRANSITO"
    CONSEGNATA = "CONSEGNATA"
    PROBLEMA = "PROBLEMA"


class CouponTipo(str, enum.Enum):
    PERCENTUALE = "PERCENTUALE"
    FISSO = "FISSO"


class StatoReso(str, enum.Enum):
    APERTO = "APERTO"
    APPROVATO = "APPROVATO"
    RIFIUTATO = "RIFIUTATO"
    RIMBORSATO = "RIMBORSATO"


# --------------------
# TABELLE
# --------------------
class Cliente(Base):
    __tablename__ = "CLIENTE"

    idCliente: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    cognome: Mapped[str] = mapped_column(String(60), nullable=False)
    dataRegistrazione: Mapped[date] = mapped_column(Date, nullable=False)

    indirizzi: Mapped[list["Indirizzo"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    carrello: Mapped["Carrello"] = relationship(
        back_populates="cliente",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ordini: Mapped[list["Ordine"]] = relationship(back_populates="cliente")
    recensioni: Mapped[list["Recensione"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Cliente(id={self.idCliente}, email={self.email!r})"


class Indirizzo(Base):
    __tablename__ = "INDIRIZZO"

    idIndirizzo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCliente: Mapped[int] = mapped_column(ForeignKey("CLIENTE.idCliente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    via: Mapped[str] = mapped_column(String(120), nullable=False)
    civico: Mapped[str | None] = mapped_column(String(10))
    citta: Mapped[str] = mapped_column(String(80), nullable=False)
    CAP: Mapped[str | None] = mapped_column(String(10))
    provincia: Mapped[str | None] = mapped_column(String(40))
    paese: Mapped[str] = mapped_column(String(60), nullable=False)
    tipo: Mapped[IndirizzoTipo] = mapped_column(Enum(IndirizzoTipo), nullable=False)
    isDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="indirizzi")
    ordini_spediti: Mapped[list["Ordine"]] = relationship(back_populates="indirizzo_spedizione")

    __table_args__ = (
        Index("idx_indirizzo_cliente", "idCliente"),
    )

    def __repr__(self) -> str:
        return f"Indirizzo(id={self.idIndirizzo}, citta={self.citta!r}, tipo={self.tipo.value})"


class Categoria(Base):
    __tablename__ = "CATEGORIA"

    idCategoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCategoriaPadre: Mapped[int | None] = mapped_column(
        ForeignKey("CATEGORIA.idCategoria", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True
    )

    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    descrizione: Mapped[str | None] = mapped_column(String(255))

    padre: Mapped["Categoria | None"] = relationship(remote_side=[idCategoria], back_populates="figli")
    figli: Mapped[list["Categoria"]] = relationship(back_populates="padre")

    prodotti: Mapped[list["Prodotto"]] = relationship(back_populates="categoria")

    def __repr__(self) -> str:
        return f"Categoria(id={self.idCategoria}, nome={self.nome!r})"


class Prodotto(Base):
    __tablename__ = "PRODOTTO"

    sku: Mapped[str] = mapped_column(String(32), primary_key=True)
    idCategoria: Mapped[int] = mapped_column(ForeignKey("CATEGORIA.idCategoria", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(80))
    descrizione: Mapped[str | None] = mapped_column(Text)
    prezzoListino: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    aliquotaIVA: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    stato: Mapped[ProdottoStato] = mapped_column(Enum(ProdottoStato), nullable=False, default=ProdottoStato.ATTIVO)

    categoria: Mapped["Categoria"] = relationship(back_populates="prodotti")
    voci_carrello: Mapped[list["VoceCarrello"]] = relationship(back_populates="prodotto")
    righe_ordine: Mapped[list["RigaOrdine"]] = relationship(back_populates="prodotto")
    recensioni: Mapped[list["Recensione"]] = relationship(back_populates="prodotto")
    scorte: Mapped[list["Scorta"]] = relationship(back_populates="prodotto")
    forniture: Mapped[list["FornituraProdotto"]] = relationship(back_populates="prodotto")

    __table_args__ = (
        Index("idx_prodotto_categoria", "idCategoria"),
        CheckConstraint("prezzoListino >= 0", name="ck_prezzoListino_pos"),
        CheckConstraint("aliquotaIVA >= 0", name="ck_aliquotaIVA_pos"),
    )

    def __repr__(self) -> str:
        return f"Prodotto(sku={self.sku!r}, nome={self.nome!r})"


class Carrello(Base):
    __tablename__ = "CARRELLO"

    idCarrello: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCliente: Mapped[int] = mapped_column(ForeignKey("CLIENTE.idCliente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)

    dataCreazione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dataUltimaModifica: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="carrello")
    voci: Mapped[list["VoceCarrello"]] = relationship(
        back_populates="carrello",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"Carrello(id={self.idCarrello}, idCliente={self.idCliente})"


class VoceCarrello(Base):
    __tablename__ = "VOCE_CARRELLO"

    idVoceCarrello: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCarrello: Mapped[int] = mapped_column(ForeignKey("CARRELLO.idCarrello", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(ForeignKey("PRODOTTO.sku", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    quantita: Mapped[int] = mapped_column(Integer, nullable=False)
    prezzoVisto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dataAggiunta: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    carrello: Mapped["Carrello"] = relationship(back_populates="voci")
    prodotto: Mapped["Prodotto"] = relationship(back_populates="voci_carrello")

    __table_args__ = (
        UniqueConstraint("idCarrello", "sku", name="uq_vocecarrello_carrello_sku"),
        Index("idx_vocecarrello_carrello", "idCarrello"),
        Index("idx_vocecarrello_sku", "sku"),
        CheckConstraint("quantita > 0", name="ck_vocecarrello_quantita_pos"),
        CheckConstraint("prezzoVisto >= 0", name="ck_vocecarrello_prezzo_pos"),
    )


class Ordine(Base):
    __tablename__ = "ORDINE"

    idOrdine: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCliente: Mapped[int] = mapped_column(ForeignKey("CLIENTE.idCliente", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    idIndirizzoSpedizione: Mapped[int] = mapped_column(ForeignKey("INDIRIZZO.idIndirizzo", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    dataCreazione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    statoOrdine: Mapped[StatoOrdine] = mapped_column(Enum(StatoOrdine), nullable=False)
    totaleLordo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    totaleSconti: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    totaleNetto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="ordini")
    indirizzo_spedizione: Mapped["Indirizzo"] = relationship(back_populates="ordini_spediti")
    righe: Mapped[list["RigaOrdine"]] = relationship(
        back_populates="ordine",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    pagamenti: Mapped[list["Pagamento"]] = relationship(
        back_populates="ordine",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    spedizioni: Mapped[list["Spedizione"]] = relationship(
        back_populates="ordine",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    ordine_coupon: Mapped["OrdineCoupon | None"] = relationship(
        back_populates="ordine",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        Index("idx_ordine_cliente_data", "idCliente", "dataCreazione"),
        CheckConstraint("totaleLordo >= 0 AND totaleSconti >= 0 AND totaleNetto >= 0", name="ck_totali_nonneg"),
        CheckConstraint("ABS(totaleNetto - (totaleLordo - totaleSconti)) < 0.01", name="ck_totaleNetto_coerente"),
    )


class RigaOrdine(Base):
    __tablename__ = "RIGA_ORDINE"

    idRigaOrdine: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idOrdine: Mapped[int] = mapped_column(ForeignKey("ORDINE.idOrdine", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(ForeignKey("PRODOTTO.sku", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    quantita: Mapped[int] = mapped_column(Integer, nullable=False)
    prezzoUnitarioApplicato: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    scontoRiga: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    ordine: Mapped["Ordine"] = relationship(back_populates="righe")
    prodotto: Mapped["Prodotto"] = relationship(back_populates="righe_ordine")
    reso: Mapped["Reso | None"] = relationship(back_populates="riga_ordine", uselist=False, cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("idOrdine", "sku", name="uq_rigaordine_ordine_sku"),
        Index("idx_rigaordine_ordine", "idOrdine"),
        Index("idx_rigaordine_sku", "sku"),
        CheckConstraint("quantita > 0", name="ck_rigaordine_quantita_pos"),
        CheckConstraint("prezzoUnitarioApplicato >= 0", name="ck_rigaordine_prezzo_pos"),
        CheckConstraint("scontoRiga >= 0", name="ck_rigaordine_sconto_pos"),
    )


class MetodoPagamento(Base):
    __tablename__ = "METODO_PAGAMENTO"

    idMetodo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nomeMetodo: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(80))

    pagamenti: Mapped[list["Pagamento"]] = relationship(back_populates="metodo")


class Pagamento(Base):
    __tablename__ = "PAGAMENTO"

    idPagamento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idOrdine: Mapped[int] = mapped_column(ForeignKey("ORDINE.idOrdine", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    idMetodo: Mapped[int] = mapped_column(ForeignKey("METODO_PAGAMENTO.idMetodo", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    importo: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dataOra: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    esito: Mapped[EsitoPagamento] = mapped_column(Enum(EsitoPagamento), nullable=False)
    transactionId: Mapped[str | None] = mapped_column(String(80), unique=True)

    ordine: Mapped["Ordine"] = relationship(back_populates="pagamenti")
    metodo: Mapped["MetodoPagamento"] = relationship(back_populates="pagamenti")

    __table_args__ = (
        Index("idx_pagamento_ordine_data", "idOrdine", "dataOra"),
        CheckConstraint("importo >= 0", name="ck_pagamento_importo_pos"),
    )


class Corriere(Base):
    __tablename__ = "CORRIERE"

    idCorriere: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    customerCare: Mapped[str | None] = mapped_column(String(120))

    spedizioni: Mapped[list["Spedizione"]] = relationship(back_populates="corriere")


class Spedizione(Base):
    __tablename__ = "SPEDIZIONE"

    idSpedizione: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idOrdine: Mapped[int] = mapped_column(ForeignKey("ORDINE.idOrdine", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    idCorriere: Mapped[int] = mapped_column(ForeignKey("CORRIERE.idCorriere", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    tracking: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    statoSpedizione: Mapped[StatoSpedizione] = mapped_column(Enum(StatoSpedizione), nullable=False)
    dataSpedizione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dataStimataConsegna: Mapped[date | None] = mapped_column(Date)

    ordine: Mapped["Ordine"] = relationship(back_populates="spedizioni")
    corriere: Mapped["Corriere"] = relationship(back_populates="spedizioni")

    __table_args__ = (
        Index("idx_spedizione_ordine", "idOrdine"),
        Index("idx_spedizione_corriere", "idCorriere"),
    )


class Magazzino(Base):
    __tablename__ = "MAGAZZINO"

    idMagazzino: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    indirizzoTestuale: Mapped[str | None] = mapped_column(String(255))

    scorte: Mapped[list["Scorta"]] = relationship(back_populates="magazzino", cascade="all, delete-orphan", passive_deletes=True)


class Scorta(Base):
    __tablename__ = "SCORTA"

    idMagazzino: Mapped[int] = mapped_column(ForeignKey("MAGAZZINO.idMagazzino", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    sku: Mapped[str] = mapped_column(ForeignKey("PRODOTTO.sku", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)

    giacenza: Mapped[int] = mapped_column(Integer, nullable=False)
    sogliaRiordino: Mapped[int] = mapped_column(Integer, nullable=False)
    dataAggiornamento: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    magazzino: Mapped["Magazzino"] = relationship(back_populates="scorte")
    prodotto: Mapped["Prodotto"] = relationship(back_populates="scorte")

    __table_args__ = (
        Index("idx_scorta_sku", "sku"),
        CheckConstraint("giacenza >= 0", name="ck_scorta_giacenza_nonneg"),
        CheckConstraint("sogliaRiordino >= 0", name="ck_scorta_soglia_nonneg"),
    )


class Fornitore(Base):
    __tablename__ = "FORNITORE"

    idFornitore: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ragioneSociale: Mapped[str] = mapped_column(String(120), nullable=False)
    piva: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(255))

    forniture: Mapped[list["FornituraProdotto"]] = relationship(back_populates="fornitore", cascade="all, delete-orphan", passive_deletes=True)


class FornituraProdotto(Base):
    __tablename__ = "FORNITURA_PRODOTTO"

    idFornitore: Mapped[int] = mapped_column(ForeignKey("FORNITORE.idFornitore", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    sku: Mapped[str] = mapped_column(ForeignKey("PRODOTTO.sku", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)

    prezzoAcquisto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    leadTimeGiorni: Mapped[int] = mapped_column(Integer, nullable=False)

    fornitore: Mapped["Fornitore"] = relationship(back_populates="forniture")
    prodotto: Mapped["Prodotto"] = relationship(back_populates="forniture")

    __table_args__ = (
        Index("idx_fornitura_sku", "sku"),
        CheckConstraint("prezzoAcquisto >= 0", name="ck_fornitura_prezzo_nonneg"),
        CheckConstraint("leadTimeGiorni >= 0", name="ck_fornitura_leadtime_nonneg"),
    )


class Coupon(Base):
    __tablename__ = "COUPON"

    codiceCoupon: Mapped[str] = mapped_column(String(30), primary_key=True)
    tipo: Mapped[CouponTipo] = mapped_column(Enum(CouponTipo), nullable=False)
    valore: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dataInizio: Mapped[date] = mapped_column(Date, nullable=False)
    dataFine: Mapped[date] = mapped_column(Date, nullable=False)
    minimoOrdine: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    maxUtilizzi: Mapped[int] = mapped_column(Integer, nullable=False)

    ordini_coupon: Mapped[list["OrdineCoupon"]] = relationship(back_populates="coupon")

    __table_args__ = (
        CheckConstraint("valore >= 0", name="ck_coupon_valore_nonneg"),
        CheckConstraint("dataFine >= dataInizio", name="ck_coupon_date_coerenti"),
        CheckConstraint("maxUtilizzi > 0", name="ck_coupon_maxutilizzi_pos"),
    )


class OrdineCoupon(Base):
    __tablename__ = "ORDINE_COUPON"

    # PK su idOrdine: massimo 1 coupon per ordine
    idOrdine: Mapped[int] = mapped_column(ForeignKey("ORDINE.idOrdine", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    codiceCoupon: Mapped[str] = mapped_column(ForeignKey("COUPON.codiceCoupon", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    dataApplicazione: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    importoScontoCalcolato: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    ordine: Mapped["Ordine"] = relationship(back_populates="ordine_coupon")
    coupon: Mapped["Coupon"] = relationship(back_populates="ordini_coupon")

    __table_args__ = (
        Index("idx_ordinecoupon_coupon", "codiceCoupon"),
        CheckConstraint("importoScontoCalcolato >= 0", name="ck_ordinecoupon_sconto_nonneg"),
    )


class Recensione(Base):
    __tablename__ = "RECENSIONE"

    idRecensione: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idCliente: Mapped[int] = mapped_column(ForeignKey("CLIENTE.idCliente", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(ForeignKey("PRODOTTO.sku", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    voto: Mapped[int] = mapped_column(Integer, nullable=False)
    titolo: Mapped[str | None] = mapped_column(String(120))
    testo: Mapped[str | None] = mapped_column(Text)
    dataRecensione: Mapped[date] = mapped_column(Date, nullable=False)

    cliente: Mapped["Cliente"] = relationship(back_populates="recensioni")
    prodotto: Mapped["Prodotto"] = relationship(back_populates="recensioni")

    __table_args__ = (
        UniqueConstraint("idCliente", "sku", name="uq_recensione_cliente_sku"),
        Index("idx_recensione_sku_data", "sku", "dataRecensione"),
        CheckConstraint("voto BETWEEN 1 AND 5", name="ck_recensione_voto"),
    )


class Reso(Base):
    __tablename__ = "RESO"

    idReso: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idRigaOrdine: Mapped[int] = mapped_column(ForeignKey("RIGA_ORDINE.idRigaOrdine", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)

    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    statoReso: Mapped[StatoReso] = mapped_column(Enum(StatoReso), nullable=False)
    dataApertura: Mapped[date] = mapped_column(Date, nullable=False)

    riga_ordine: Mapped["RigaOrdine"] = relationship(back_populates="reso")

    __table_args__ = (
        Index("idx_reso_stato", "statoReso"),
    )
