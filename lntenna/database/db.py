import os
from os.path import expanduser

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Boolean,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import or_, select


home = expanduser("~")
db_path = home + "/.lntenna/"
if not os.path.exists(db_path):
    os.makedirs(db_path)
engine = create_engine("sqlite:///{}".format(db_path + "database.db"))
metadata = MetaData()

orders = Table(
    "orders",
    metadata,
    Column("uuid", String(32), primary_key=True),
    Column("message", String),
    Column("network", String(10)),
    Column("refund_address", String),
    Column("txid", String),
)

blocksat = Table(
    "blocksat",
    metadata,
    Column("uuid", String(32), ForeignKey(orders.c.uuid), primary_key=True),
    Column("satellite_url", String),
    Column("blocksat_uuid", String),
    Column("auth_token", String),
    Column("created_at", Integer),
    Column("description", String),
    Column("expires_at", Integer),
    Column("id", String),
    Column("sha256_message_digest", String),
    Column("msatoshi", String),
    Column("payreq", String),
    Column("rhash", String),
    Column("status", String),
)

swaps = Table(
    "swaps",
    metadata,
    Column("uuid", String(32), ForeignKey("orders.uuid"), primary_key=True),
    Column("destination_public_key", String),
    Column("fee_tokens_per_vbyte", Integer),
    Column("invoice", String),
    Column("payment_hash", String),
    Column("redeem_script", String),
    Column("refund_address", String),
    Column("refund_public_key_hash", String),
    Column("swap_amount", Integer),
    Column("swap_fee", Integer),
    Column("swap_key_index", Integer),
    Column("swap_p2sh_address", String),
    Column("swap_p2sh_p2wsh_address", String),
    Column("swap_p2wsh_address", String),
    Column("timeout_block_height", Integer),
    Column("payment_secret", String),
)

# a mesh table which will be utilised by offgrid nodes who won't get full responses
mesh = Table(
    "mesh",
    metadata,
    Column("uuid", String(32), ForeignKey("orders.uuid"), primary_key=True),
    Column("destination_public_key", String),
    Column("invoice", String),
    Column("payment_hash", String),
    Column("redeem_script", String),
    Column("refund_address", String),
    Column("swap_amount", Integer),
    Column("swap_p2sh_address", String),
    Column("preimage", String),
    Column("tx_hash", String),
    Column("tx_hex", String),
    Column("swap_complete", Boolean),
    Column("network", String),
    Column("message", String),
)


# This will check for the presence of each table first before creating, so it's safe to
# call multiple times
def init():
    metadata.create_all(engine)


def add_order(uuid, message, network):
    conn = engine.connect()
    ins = orders.insert()
    try:
        conn.execute(ins, uuid=uuid, message=message, network=network)
    except IntegrityError as e:
        raise e


def add_blocksat(uuid, satellite_url, result):
    conn = engine.connect()
    ins = blocksat.insert()
    try:
        conn.execute(
            ins,
            uuid=uuid,
            satellite_url=satellite_url,
            blocksat_uuid=result["uuid"],
            auth_token=result["auth_token"],
            created_at=result["lightning_invoice"]["created_at"],
            description=result["lightning_invoice"]["description"],
            expires_at=result["lightning_invoice"]["expires_at"],
            id=result["lightning_invoice"]["id"],
            sha256_message_digest=result["lightning_invoice"]["metadata"][
                "sha256_message_digest"
            ],
            msatoshi=result["lightning_invoice"]["msatoshi"],
            payreq=result["lightning_invoice"]["payreq"],
            rhash=result["lightning_invoice"]["rhash"],
            status=result["lightning_invoice"]["status"],
        )
    except IntegrityError as e:
        raise e


def add_refund_addr(uuid, refund_addr):
    conn = engine.connect()
    up = orders.update().where(orders.c.uuid == uuid).values(refund_address=refund_addr)
    try:
        conn.execute(up)
    except IntegrityError as e:
        raise e


def add_swap(uuid, result):
    conn = engine.connect()
    ins = swaps.insert()
    # add uuid to the result
    result["uuid"] = uuid
    try:
        # now we can pass result as a dict() as it matches table exactly
        conn.execute(ins, result)
    except IntegrityError as e:
        raise e


def add_txid(uuid, txid):
    conn = engine.connect()
    up = orders.update().where(orders.c.uuid == uuid).values(txid=txid)
    try:
        conn.execute(up)
    except IntegrityError as e:
        raise e


def check_swap(uuid, preimage):
    conn = engine.connect()
    up = swaps.update().where(swaps.c.uuid == uuid).values(preimage=preimage)
    try:
        conn.execute(up)
    except IntegrityError as e:
        raise e


def lookup_bump(uuid):
    conn = engine.connect()
    s = select(
        [blocksat.c.blocksat_uuid, blocksat.c.auth_token, blocksat.c.satellite_url]
    ).where(blocksat.c.uuid == uuid)
    return conn.execute(s).fetchone().values()


def lookup_refund_addr(uuid):
    conn = engine.connect()
    s = select([orders.c.refund_address]).where(orders.c.uuid == uuid)
    return conn.execute(s).fetchone().values()[0]


def lookup_network(uuid):
    conn = engine.connect()
    s = select([orders.c.network]).where(orders.c.uuid == uuid)
    return conn.execute(s).fetchone().values()[0]


def lookup_pay_details(uuid):
    conn = engine.connect()
    s = select([swaps.c.swap_amount, swaps.c.swap_p2sh_address]).where(
        swaps.c.uuid == uuid
    )
    return conn.execute(s).fetchone().values()


def orders_lookup_swap_details(uuid):
    conn = engine.connect()
    s = select([orders.c.network, swaps.c.invoice, swaps.c.redeem_script]).where(
        or_(swaps.c.uuid == uuid, orders.c.uuid == uuid)
    )
    return conn.execute(s).fetchone().values()


def mesh_add_sat_request(message, refund_addr, network, uuid):
    with engine.connect() as conn:
        ins = mesh.insert()
        try:
            conn.execute(
                ins,
                message=message,
                refund_address=refund_addr,
                network=network,
                uuid=uuid,
            )
        except IntegrityError as e:
            raise e


def mesh_add_verify_quote(
    uuid, inv, amt, addr, r_s, pubkey, payment_hash, tx_hash, tx_hex
):
    with engine.connect() as conn:
        up = (
            mesh.update()
            .where(mesh.c.uuid == uuid)
            .values(
                destination_public_key=pubkey,
                invoice=inv,
                payment_hash=payment_hash,
                redeem_script=r_s,
                swap_amount=amt,
                swap_p2sh_address=addr,
                tx_hash=tx_hash,
                tx_hex=tx_hex,
                swap_complete=False,
            )
        )
        try:
            conn.execute(up)
        except IntegrityError as e:
            raise e


def swap_lookup_payment_hash(uuid):
    conn = engine.connect()
    s = select([mesh.c.payment_hash]).where(mesh.c.uuid == uuid)
    return conn.execute(s).fetchone().values()[0]


def swap_add_preimage(uuid, preimage):
    conn = engine.connect()
    up = (
        mesh.update()
        .where(mesh.c.uuid == uuid)
        .values(preimage=preimage, swap_complete=True)
    )
    try:
        conn.execute(up)
    except IntegrityError as e:
        raise e


def cli_lookup_swap_tx(uuid):
    conn = engine.connect()
    s = select([mesh.c.tx_hash, mesh.c.tx_hex]).where(mesh.c.uuid == uuid)
    return conn.execute(s).fetchone().values()


def cli_lookup_network(uuid):
    conn = engine.connect()
    s = select([mesh.c.network]).where(mesh.c.uuid == uuid)
    return conn.execute(s).fetchone().values()


def cli_lookup_uuid(uuid):
    conn = engine.connect()
    s = select([c for c in mesh.columns]).where(mesh.c.uuid == uuid)
    r = conn.execute(s).fetchone()
    d = dict(zip(r.keys(), r.values()))
    return d
