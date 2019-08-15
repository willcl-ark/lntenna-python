# lntenna payment flow

## Nodes

* MESH1
* GATEWAY


## Flow

#### MESH1 ---> GATEWAY

Broadcast (or private msg) to GATEWAY of form "sat_req" which includes:

1) a message (? Bytes)
2) a bitcoin refund address (34 Bytes)

-----

#### GATEWAY ---> WAN API calls

GATEWAY will process the message and initiate a blockstream_blocksat request.
With a successful response it will query Submarine Swap Server (SSS) for a swap quote.

-----

#### GATEWAY ---> MESH1

GATEWAY will return to MESH1 via private message:

1) the lntenna order UUID (36 Bytes, could be reduced?),
2) BOLT11 invoice (328 Bytes)
3) SSS amount (2 Bytes)
4) SSS P2SH_address (35 Bytes)
3) SSS redeem script (~ 186 Bytes)

      Total ~= 691 Bytes including json formatting, e.g. in string form:

`"{"addr": "n34WJgCn8yXPSRh1tfcvkFVWueK87Rm3uX", "uuid": "126a7971-c4fd-44f2-b91f-c834e74f49aa", "inv": "lntb100n1pw42d55pp5caurehps22d96a49wep73xf8ls8txyaepusvc3r2mpzyf5fstwksdphgfkx7cmtwd68yetpd5s9xct5v4kxc6t5v5s9gunpdeek66tnwd5k7mscqp2rzjqw5ety2rq8d8gya3dd8fsk3vuec8f4qrynpxh054pzzmfxujcm0vw9efu5qqpzqqqyqqqqqpqqqqqzsqqcc2700jv09khkk52de2ftflr0j04tra7cpc4j74zjt4a9wzmxn59patu274a5p0szafqf0due6092hpgsljj50nynr9ztzrxj6a9qmrgqvza68t", "rs": "76a914e07908f23613e055adb70f6e76e5080afa6880ba8763752102fee228c49daf287be737c37a8946d502895bb2a6f2e643464443bb4e9655eb1c6703d20e18b17576a914ec5241eafca59aba49744a7ac0ccc5aff1bff1db8868ac"}"`

This will be contained in 3 GoTenna text messages, if you get lucky!.

GATEWAY should start a thread to monitor swap_status() every 15 seconds (until invoice
expiry?)

-----

#### MESH1 ---> VERIFY

MESH1 will then be able to verify that:

1) invoice is payable to Blockstream's node_id
2) invoice signature of the human-readable part verifies
3) terms of the SSS match Blockstream node_id

The pubkey can be extracted from the signature or supplied as an 'n' tagged field.
Either way is fine with us

-----

#### MESH1 ---> Bitcoin P2P network via txtenna Meshnet

After verification, a txtenna payment can be made, fulfilling the SSS request.

#### GATEWAY ---> monitoring ---> MESH1

When GATEWAY detects 'payment_preimage' in swap_status, return preimage to MESH1 via
priavte message


COMPLETE.

