from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session

from . import crud
from .models import IndirizzoTipo, EsitoPagamento, StatoSpedizione, CouponTipo, Coupon

def seed_all(session: Session) -> None:
    # Clienti + carrelli (create_cliente crea anche il carrello)
    g = crud.create_cliente(session, "gabriel.rossi@example.com", "Gabriel", "Rossi", date(2025, 9, 1))
    crud.create_cliente(session, "chiara.bianchi@example.com", "Chiara", "Bianchi", date(2025, 9, 5))
    crud.create_cliente(session, "luca.verdi@example.com", "Luca", "Verdi", date(2025, 9, 10))

    # Indirizzi
    a1 = crud.add_indirizzo(session, g.idCliente, "Via Roma", "Roma", "Italia", IndirizzoTipo.SPEDIZIONE, civico="10", cap="00100", provincia="RM", is_default=True)
    crud.add_indirizzo(session, g.idCliente, "Via Roma", "Roma", "Italia", IndirizzoTipo.FATTURAZIONE, civico="10", cap="00100", provincia="RM", is_default=True)

    # Categorie
    skincare = crud.create_categoria(session, "Skincare", "Prodotti per la cura della pelle")
    detersione = crud.create_categoria(session, "Detersione", "Detergenti e struccanti", id_padre=skincare.idCategoria)
    makeup = crud.create_categoria(session, "Make-up", "Trucco e accessori")
    haircare = crud.create_categoria(session, "Haircare", "Cura dei capelli")

    # Prodotti
    crud.create_prodotto(session, "GH-SKIN-001", detersione.idCategoria, "Gel Detergente Delicato", 12.90, 22.00, brand="GlowBasics",
                        descrizione="Detergente viso per uso quotidiano")
    crud.create_prodotto(session, "GH-SKIN-002", skincare.idCategoria, "Crema Idratante", 18.50, 22.00, brand="GlowBasics",
                        descrizione="Crema idratante viso 50ml")
    crud.create_prodotto(session, "GH-MAKE-001", makeup.idCategoria, "Mascara Volume", 14.90, 22.00, brand="LuxeLash",
                        descrizione="Mascara effetto volume")
    crud.create_prodotto(session, "GH-HAIR-001", haircare.idCategoria, "Shampoo Nutriente", 9.90, 22.00, brand="SilkHair",
                        descrizione="Shampoo nutriente 250ml")

    # Coupon
    session.add(Coupon(
        codiceCoupon="WELCOME10", tipo=CouponTipo.PERCENTUALE, valore=10.00,
        dataInizio=date(2025, 9, 1), dataFine=date(2026, 9, 1),
        minimoOrdine=10.00, maxUtilizzi=1000
    ))
    session.add(Coupon(
        codiceCoupon="FREESHIP5", tipo=CouponTipo.FISSO, valore=5.00,
        dataInizio=date(2025, 9, 1), dataFine=date(2026, 3, 1),
        minimoOrdine=20.00, maxUtilizzi=500
    ))
    session.commit()

    # Aggiunta al carrello + checkout + pagamento + spedizione (workflow minimo)
    crud.add_to_cart(session, g.idCliente, "GH-SKIN-001", 1)
    crud.add_to_cart(session, g.idCliente, "GH-SKIN-002", 1)
    res = crud.checkout(session, g.idCliente, a1.idIndirizzo, codice_coupon="WELCOME10")
    crud.pay_order(session, res.ordine_id, "Carta", float(res.totale_netto), EsitoPagamento.OK, transaction_id="TX-0001")
    crud.create_shipment(session, res.ordine_id, "PosteDelivery", "TRACK-0001", StatoSpedizione.IN_TRANSITO)
