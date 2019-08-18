# General
connection = None

# Bitcoin
BTC_CONF_PATH = "/Users/will/Library/Application Support/Bitcoin/testnet3/bitcoin.conf"

# Database
DB_DIR = "/.lntenna/"

# Swap Server API URL
SUBMARINE_API = "https://submarineswaps.org/api/v0"
# SUBMARINE_API = "http://localhost:9889/api/v0"

# Blocksat details
SATELLITE_API = "https://api.blockstream.space"
TESTNET_SATELLITE_API = "https://api.blockstream.space/testnet"
BLOCKSAT_NODE_PUBKEYS = [
    "039d2201586141a3fff708067aa270aa4f6a724227d5740254d4e34da262a79c2a",
    "03f21fc2e8ab0540eeb74dd715b5b66638ec1cd392db00009b320b3ed8c409bd57",
]

# logging
FORMAT = "[%(levelname)s - %(funcname)s] - %(message)s"