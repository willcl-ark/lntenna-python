# lntenna-python

## Rationale

Send a Blockstream Blocksat message from an off-grid node, who has a Blockstream Blocksat-connected instance of bitcoind running, via GoTenna meshnet.

There are two general approaches to achieving this using GoTenna meshnet, each involving one WAN-connected node, GATEWAY and one off-grid node, MESH1. GATEWAY can optionally run bitcoind. MESH1 will require bitcoind and optionally a Blocksat receiver to verify sent messages (not integrated into lntenna currently. The two approaches are:

* Both GATEWAY and MESH1 should be running lntenna for each approach

1) Advanced: Whilst MESH1 is online, setup a single lightning channel with some local balance.

   When offline, proxy the Blockstream Blocksat API request via meshnet from MESH1 to GATEWAY to receive the Blocksat quote.
   
   Then send and parse the appropriate HTLC update messages for the channel directly, via GoTenna meshnet, to make the payment and watch for the message.

1) Basic: No online setup required. From MESH1 send a specially formatted "sat_req" message via meshnet to be interpreted by GATEWAY.
   
   GATEWAY will make the Blocksat request on MESH1's behalf and additionally a Submarine Swap request form submarineswaps.org, allowing the payment for the message to be made via an on-chain bitcoin transaction by MESH1.
   
   Passing this information back to MESH1, it can verify the invoice and Swap details to cryptographically ensure they match its request.
   
   MESH1 can reply to GATEWAY with the on-chain transaction hex which GATEWAY can upload to the bitcoin P2P network, optionally via it's own bitcoin instance or via submarineswaps.org' API server.
   
   submarineswaps.org Swap Server will detect the payment and attempt to fulfill the invoice, returning the invoice preimage to MESH1 for final verification, completing the process.


This project is attempting to implement #2 as a stepping stone towards #1, which is the final target.

## Setup

* Clone the repo `git clone https://github.com/willcl-ark/lntenna-python.git`

* If you are sharing a single bitcoind instance between two GoTennas for testing (on a single online machine), you will need to disable automatic broadcasting of bitcoin transactions temporarily (don't forget to revert this after!!!) in your bitcoin.conf file, because the transaction creation method is `bitcoin_rpc.sendtoaddress()` rather than creating a rawtransaction.

  Add the following line to bitcoin.conf in wallet section: `walletbroadcast=0`

* Before first start, in the repo navigate to `lntenna/server/example_config.ini` and modify the settings as appropriate. This file will be copied to `$HOME/.lntenna/config.ini` upon first start. If you need to modify variables again later, modify `$HOME/.lntenna/config.ini` directly.

* If your bitcoin wallet is protected by a passphrase, create file `lntenna/server/bitcoind_password.py` and add a single variable: `BITCOIND_PW ='your_password'`, save and exit.

* Create a python 3.6 venv and activate it

* Install dependencies using pipenv or pip:

    `pipenv install` 
    
    or

    `pip install -r requirements.txt`
    
## Testing

#### GATEWAY node

With the venv active and your GoTenna un-paired, powered off and disconnected run the following terminal command to start the GATEWAY server.

* with the `--debug` flag, the server will attempt to parse `["gotenna"]["DEBUG_GID"]` from config.ini to use as the GoTenna GATEWAY GoTenna GID.

* optionally adding the `--no-api-server` flag will disable the API server, which might be a good idea for testing purposes as it's not fully conceptualised yet.

```bash
python lntenna/server.server.py --debug --no-api-server
```

Once the server is running, you can connect and power on the GoTenna. Watch the terminal logs for connection messages.

The program can be exited via a KeyboardInterrupt


#### MESH1 node

For the off-grid node, MESH1 which is also physically disconnected and not paired to any host, start a second terminal, run the command line utility with the following command:

```bash
python lntenna/cli/cli.py
```

Your SDK token, GID and GEO_REGION should be auto-populated from the config file which will is now found in `$HOME/.lntenna/config.ini`. Once you see them reflected to you in the console, you can connect and power on the second, GoTenna device and watch for the connection messages.

Type `?` to see a list of commands you can use.

#### Sending a blocksat message

In the CLI app run command `send_sat_msg` and you will be prompted for a `message`, a  `refund address` and a `network`. Enter these values and monitor the two terminals for progress updates. Most of the flow is automatic:

1) When GATEWAY receives the formatted satellite request message it will automatically request a quotation from Blockstream's blocksat API. It will then request a swap quote from the submarineswaps.org API.

1) It will store the results of these in the relevant tables in the database located in `$HOME/.lntenna/database.db` and return the relevant parts back to MESH1 via a 'jumbo' (segmented) message.

1) When MESH1 receives the quote response, it will parse the BOLT11 invoice and compare it with hardcoded blockstream blocksat node pubkeys from config.ini, and then compare portions of the redeem script with the blockstream node pubkeys. It will then present user of the MESH1 terminal with input to confirm price (combined total of blocksat quote + swap fees).

1) When MESH1 user agrees to the cost by entering `y`, MESH1 node will connect to local bitcoind instance and create the appropriate transaction using the simple `bitcoin_rpc.sendtoaddress(address, amount)`. This transaction will not be broadcast immediately due to the bitcoin.conf setting `walletbroadcast=0`, but you will see local balance reduced by amount depending on what UTXOs were consumed.

1) The txid and tx_hex will then automatically be returned via jumbo message to GATEWAY, who will attempt to broadcast it using `bitcoin_rpc.sendrawtx(tx_hex)` if bitcoind is running, otherwise it will broadcast it back via the submarineswaps.org `broadcast_tx` API call.

1) Once it has propagated the transaction to the bitcoin network, GATEWAY will start a new thread to monitor the swap status via the submarineswaps.org API. Once a `payment_preimage` is detected in the response, it will verify that the preimage hashes to the `payment_hash` of the BOLT11 invoice, and then return the results via a final jumbo message to MESH1.


### Help

Because of the bitcoin.conf setting `walletbroadcast=0` if the process breaks down, the wallet may display low or zero balance (depending on which UTXOs were consumed by the transaction) until the transaction is broadcast. To manually initiate this, follow these steps in a new terminal:

* List recent transactions using `bitcoin-cli listtransactions`. The bottom entry is the most recent by default. Copy it's `txid` value to your clipboard.

* Lookup the transaction hex using `bitcoin-cli gettransaction $TXID`. Copy its `hex` field to your clipboard.

* Broadcast the transaction using `bitcoin-cli sendrawtransaction $TX_HEX`. This will "restore" the correct wallet balance, obviously minus the swap transaction amount.

N.B.:

The application will not automatically resume following this action, but the swap server _will_ still automatically detect the payment and will attempt to fulfill the blocksat lightning invoice, completing the process in the background.

With the relevant details from the console or database (network, invoice and redeem-script) manual API calls the the submarineswaps.org API can still query swap status.

TODO: add a cli command to query the swap status from MESH1 via GATEWAY
    
    