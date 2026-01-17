from __future__ import annotations

import argparse
from pathlib import Path

from glowhub.db import make_engine, get_session
from glowhub.models import Base, IndirizzoTipo, EsitoPagamento, StatoSpedizione
from glowhub import crud, queries
from glowhub.seed import seed_all


def cmd_init_db(_args):
    engine = make_engine()
    Base.metadata.create_all(engine)
    print("✅ Tabelle create (ORM).")

def cmd_drop_db(_args):
    engine = make_engine()
    Base.metadata.drop_all(engine)
    print("🧨 Tabelle eliminate (ORM).")

def cmd_seed(_args):
    engine = make_engine()
    Base.metadata.create_all(engine)
    with get_session(engine) as session:
        seed_all(session)

    out_sql = Path("sql") / "queries_generated.sql"
    queries.export_queries_sql(engine, str(out_sql))
    print(f"✅ Dati di esempio inseriti. SQL query esportate in: {out_sql}")

def cmd_demo(_args):
    engine = make_engine()
    with get_session(engine) as session:
        stmt = queries.q_ordini_cliente_email("gabriel.rossi@example.com")
        print("\n--- Q1 Ordini cliente ---")
        for row in session.execute(stmt).all():
            print(row)
        print("\nSQL:")
        print(queries.compile_sql(engine, stmt))

        stmt = queries.q_prodotti_sotto_soglia()
        print("\n--- Q4 Prodotti sotto soglia ---")
        for row in session.execute(stmt).all():
            print(row)
        print("\nSQL:")
        print(queries.compile_sql(engine, stmt))

def cmd_create_client(args):
    engine = make_engine()
    with get_session(engine) as session:
        c = crud.create_cliente(session, args.email, args.nome, args.cognome)
        print(f"✅ Creato cliente: {c}")

def cmd_add_address(args):
    engine = make_engine()
    with get_session(engine) as session:
        a = crud.add_indirizzo(
            session,
            args.id_cliente,
            via=args.via,
            civico=args.civico,
            citta=args.citta,
            cap=args.cap,
            provincia=args.provincia,
            paese=args.paese,
            tipo=IndirizzoTipo[args.tipo],
            is_default=args.default,
        )
        print(f"✅ Aggiunto indirizzo: {a}")

def cmd_create_category(args):
    engine = make_engine()
    with get_session(engine) as session:
        cat = crud.create_categoria(session, args.nome, args.descrizione, args.id_padre)
        print(f"✅ Creata categoria: {cat}")

def cmd_create_product(args):
    engine = make_engine()
    with get_session(engine) as session:
        p = crud.create_prodotto(session, args.sku, args.id_categoria, args.nome, args.prezzo, args.iva, args.brand, args.descrizione)
        print(f"✅ Creato prodotto: {p}")

def cmd_add_to_cart(args):
    engine = make_engine()
    with get_session(engine) as session:
        v = crud.add_to_cart(session, args.id_cliente, args.sku, args.quantita)
        print(f"✅ Aggiunto al carrello: sku={v.sku} qta={v.quantita}")

def cmd_checkout(args):
    engine = make_engine()
    with get_session(engine) as session:
        res = crud.checkout(session, args.id_cliente, args.id_indirizzo, args.coupon)
        print(f"✅ Ordine creato: id={res.ordine_id} lordo={res.totale_lordo} sconti={res.totale_sconti} netto={res.totale_netto}")

def cmd_pay_order(args):
    engine = make_engine()
    with get_session(engine) as session:
        p = crud.pay_order(session, args.id_ordine, args.metodo, args.importo, EsitoPagamento[args.esito], args.tx)
        print(f"✅ Pagamento registrato: idPagamento={p.idPagamento}, esito={p.esito.value}")

def cmd_create_shipment(args):
    engine = make_engine()
    with get_session(engine) as session:
        s = crud.create_shipment(session, args.id_ordine, args.corriere, args.tracking, StatoSpedizione[args.stato])
        print(f"✅ Spedizione creata: tracking={s.tracking}, stato={s.statoSpedizione.value}")

def cmd_update_product_price(args):
    engine = make_engine()
    with get_session(engine) as session:
        crud.update_prezzo_prodotto(session, args.sku, args.prezzo)
        print(f"✅ Prezzo aggiornato per {args.sku}: {args.prezzo}")

def cmd_delete_product(args):
    engine = make_engine()
    with get_session(engine) as session:
        crud.delete_prodotto(session, args.sku)
        print(f"✅ Prodotto eliminato (se esisteva): {args.sku}")

def cmd_delete_client(args):
    engine = make_engine()
    with get_session(engine) as session:
        crud.delete_cliente(session, args.id_cliente)
        print(f"✅ Cliente eliminato (se esisteva): idCliente={args.id_cliente}")

def cmd_remove_from_cart(args):
    engine = make_engine()
    with get_session(engine) as session:
        crud.remove_from_cart(session, args.id_cliente, args.sku)
        print(f"✅ Rimosso dal carrello: idCliente={args.id_cliente}, sku={args.sku}")


def build_parser():
    p = argparse.ArgumentParser(prog="glowhub", description="GlowHub - SQLAlchemy ORM (E-tivity 4)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db").set_defaults(func=cmd_init_db)
    sub.add_parser("drop-db").set_defaults(func=cmd_drop_db)
    sub.add_parser("seed").set_defaults(func=cmd_seed)
    sub.add_parser("demo").set_defaults(func=cmd_demo)

    sp = sub.add_parser("create-client")
    sp.add_argument("--email", required=True)
    sp.add_argument("--nome", required=True)
    sp.add_argument("--cognome", required=True)
    sp.set_defaults(func=cmd_create_client)

    sp = sub.add_parser("add-address")
    sp.add_argument("--id-cliente", type=int, required=True, dest="id_cliente")
    sp.add_argument("--via", required=True)
    sp.add_argument("--civico")
    sp.add_argument("--citta", required=True)
    sp.add_argument("--cap")
    sp.add_argument("--provincia")
    sp.add_argument("--paese", required=True)
    sp.add_argument("--tipo", choices=["SPEDIZIONE", "FATTURAZIONE"], required=True)
    sp.add_argument("--default", action="store_true")
    sp.set_defaults(func=cmd_add_address)

    sp = sub.add_parser("create-category")
    sp.add_argument("--nome", required=True)
    sp.add_argument("--descrizione")
    sp.add_argument("--id-padre", type=int, dest="id_padre")
    sp.set_defaults(func=cmd_create_category)

    sp = sub.add_parser("create-product")
    sp.add_argument("--sku", required=True)
    sp.add_argument("--id-categoria", type=int, required=True, dest="id_categoria")
    sp.add_argument("--nome", required=True)
    sp.add_argument("--prezzo", type=float, required=True)
    sp.add_argument("--iva", type=float, default=22.0)
    sp.add_argument("--brand")
    sp.add_argument("--descrizione")
    sp.set_defaults(func=cmd_create_product)

    sp = sub.add_parser("add-to-cart")
    sp.add_argument("--id-cliente", type=int, required=True, dest="id_cliente")
    sp.add_argument("--sku", required=True)
    sp.add_argument("--quantita", type=int, required=True)
    sp.set_defaults(func=cmd_add_to_cart)

    sp = sub.add_parser("checkout")
    sp.add_argument("--id-cliente", type=int, required=True, dest="id_cliente")
    sp.add_argument("--id-indirizzo", type=int, required=True, dest="id_indirizzo")
    sp.add_argument("--coupon")
    sp.set_defaults(func=cmd_checkout)

    sp = sub.add_parser("pay-order")
    sp.add_argument("--id-ordine", type=int, required=True, dest="id_ordine")
    sp.add_argument("--metodo", required=True)
    sp.add_argument("--importo", type=float, required=True)
    sp.add_argument("--esito", choices=["OK", "KO"], required=True)
    sp.add_argument("--tx")
    sp.set_defaults(func=cmd_pay_order)

    sp = sub.add_parser("create-shipment")
    sp.add_argument("--id-ordine", type=int, required=True, dest="id_ordine")
    sp.add_argument("--corriere", required=True)
    sp.add_argument("--tracking", required=True)
    sp.add_argument("--stato", choices=["PREPARAZIONE", "IN_TRANSITO", "CONSEGNATA", "PROBLEMA"], default="PREPARAZIONE")
    sp.set_defaults(func=cmd_create_shipment)

    sp = sub.add_parser("update-product-price")
    sp.add_argument("--sku", required=True)
    sp.add_argument("--prezzo", type=float, required=True)
    sp.set_defaults(func=cmd_update_product_price)

    sp = sub.add_parser("delete-product")
    sp.add_argument("--sku", required=True)
    sp.set_defaults(func=cmd_delete_product)

    sp = sub.add_parser("delete-client")
    sp.add_argument("--id-cliente", type=int, required=True, dest="id_cliente")
    sp.set_defaults(func=cmd_delete_client)

    sp = sub.add_parser("remove-from-cart")
    sp.add_argument("--id-cliente", type=int, required=True, dest="id_cliente")
    sp.add_argument("--sku", required=True)
    sp.set_defaults(func=cmd_remove_from_cart)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
