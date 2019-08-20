# lntenna-python


* Clone the repo `git clone https://github.com/willcl-ark/lntenna-python.git`

* If you are sharing a single bitcoind instance between two GoTennas for testing (on a single online machine), you will need to disable automatic broadcasting of bitcoin transactions temporarily (don't forget to revert this after!!!) in your bitcoin.conf file, because the transaction creation method is `bitcoin_rpc.sendtoaddress()` rather than creating a rawtransaction. Add the following line to bitcoin.conf in wallet section: `walletbroadcast=0`

* In the repo navigate to `lntenna/server/example_config.ini` and modify the settings as appropriate. This file will be copied to `$HOME/.lntenna/config.ini` upon first start. If you need to modify variables again later, modify `$HOME/.lntenna/config.ini` directly.

* If your bitcoin wallet is protected by a passphrase, create file `lntenna/server/bitcoind_password.py` and add a single variable: `BITCOIND_PW ='your_password'`, save and exit.

* Create a python 3.6 venv and activate it

* Install dependencies using pipenv or pip:

    `pipenv install` 
    
    or

    `pip install -r requirements.txt`
    
## Testing

#### GATEWAY node

With the venv active, open a python3 console for the GATEWAY, WAN-connected GoTenna device, and connect to it. The GoTenna device should not be paired to any host and should be physically disconnected from the host:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
from lntenna.gotenna import connection
c = connection.Connection()
c.sdk_token(sdk_token='your_sdk_token')
c.set_gid(gid='unique_GID')
c.set_geo_region(region=2)
```

When these variables are set you can physically connect, then power on the GoTenna device and watch for the DEBUG messages indicating successful connection.

#### MESH1 node

For the off-grid node, MESH1 which is also physically disconnected and not paired to any host, start a second terminal, run the command line app:

```bash
python lntenna/cli/cli.py
```

Your SDK token, GID and GEO_REGION should be auto-populated from the config file which will be copied to `$HOME/.lntenna/config.ini`. Once you see them reflected to you in the console, you can connect and power on the second, GoTenna device and watch for the connection messages.

Type `?` to see a list of commands you can use.

#### Sending a blocksat message

In the CLI app run command `send_sat_msg` and you will be prompted for a `message`, a  `refund address` and a `network`. Enter these values and monitor the two terminals for progress updates. Most of the flow is automatic.

When GATEWAY receives the formatted satellite request message it will automatically request a quotation from Blockstream's blocksat API. It will then request a swap quote from the submarineswaps.org API.

It will store the results of these in the relevant tables in the database located in `$HOME/.lntenna/database.db` and return the relevant parts back to MESH1 via a 'jumbo' (segmented) message.

When MESH1 receives the quote response, it will parse the BOLT11 invoice and compare it with hardcoded blockstream blocksat node pubkeys from config.ini, and then compare portions of the redeem script with the blockstream node pubkeys. It will then present user of the MESH1 terminal with input to confirm price (combined total of blocksat quote + swap fees).

When MESH1 user agrees to the cost by entering `y`, MESH1 node will connect to local bitcoind instance and create the appropriate transaction using the simple `bitcoin_rpc.sendtoaddress(address, amount)`. This transaction will not be broadcast immediately due to the bitcoin.conf setting `walletbroadcast=0`, but you will see local balance reduced by amount depending on what UTXOs were consumed.

The txid and tx_hex will then automatically be returned via jumbo message to GATEWAY, who will attempt to broadcast it using `bitcoin_rpc.sendrawtx(tx_hex)` if bitcoind is running, otherwise it will broadcast it back via the submarineswaps.org `broadcast_tx` API call.

Once it has propagated the transaction to the bitcoin network, GATEWAY will start a new thread to monitor the swap status via the submarineswaps.org API. Once a `payment_preimage` is detected in the response, it will verify that the preimage hashes to the `payment_hash` of the BOLT11 invoice, and then return the results via a final jumbo message to MESH1.


### Help

Because of the bitcoin.conf setting `walletbroadcast=0` if the process breaks down, the wallet may display low or zero balance until the transaction is broadcast. To manually initiate this, follow these steps in a new terminal:

* list recent transactions using `bitcoin-cli listtransactions`. The bottom entry is the most recent by default. Copy it's `txid` value to your clipboard.

* Lookup the transaction hex using `bitcoin-cli gettransaction $TXID`. Copy it's `hex` field to your clipboard.

* Broadcast the transaction using `bitcoin-cli sendrawtransaction $TX_HEX` to restore wallet balance (minus transaction amount)

N.B.:

The application will not automatically resume this action, but the swap server will still detect the payment and will attempt to fulfill the blocksat lightning invoice, completing the process in the background.

With the relevant details from the console or database (network, invoice and redeem-script) manual API calls the the submarineswaps.org API can still query swap status.
    
    