#! /usr/bin/env python3

# Copied from Rusty Russell's lightning-payencode repository
# https://github.com/rustyrussell/lightning-payencode

# Copyright (c) 2017    Rusty Russell
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Master functions and command line tool for decoding and encoding lightning
invoices"""

import argparse
import time
from binascii import hexlify, unhexlify

from lntenna.lightning.lnaddr import LnAddr, lndecode, lnencode


def encode(options):
    """ Convert options into LnAddr and pass it to the encoder
    """
    addr = LnAddr()
    addr.currency = options.currency
    addr.fallback = options.fallback if options.fallback else None
    if options.amount:
        addr.amount = options.amount
    if options.timestamp:
        addr.date = int(options.timestamp)

    addr.paymenthash = unhexlify(options.paymenthash)

    if options.description:
        addr.tags.append(("d", options.description))
    if options.description_hashed:
        addr.tags.append(("h", options.description_hashed))
    if options.expires:
        addr.tags.append(("x", options.expires))

    if options.fallback:
        addr.tags.append(("f", options.fallback))

    for r in options.route:
        splits = r.split("/")
        route = []
        while len(splits) >= 5:
            route.append(
                (
                    unhexlify(splits[0]),
                    unhexlify(splits[1]),
                    int(splits[2]),
                    int(splits[3]),
                    int(splits[4]),
                )
            )
            splits = splits[5:]
        assert len(splits) == 0
        addr.tags.append(("r", route))
    print(lnencode(addr, options.privkey))


def decode(options):
    a = lndecode(options.lnaddress, options.verbose)

    def tags_by_name(name, tags):
        return [t[1] for t in tags if t[0] == name]

    print("Signed with public key:", hexlify(a.pubkey.serialize()))
    print("Currency:", a.currency)
    print("Payment hash:", hexlify(a.paymenthash))
    if a.amount:
        print("Amount:", a.amount)
    print("Timestamp: {} ({})".format(a.date, time.ctime(a.date)))

    for r in tags_by_name("r", a.tags):
        print("Route: ", end="")
        for step in r:
            print(
                "{}/{}/{}/{}/{} ".format(
                    hexlify(step[0]), hexlify(step[1]), step[2], step[3], step[4]
                ),
                end="",
            )
        print("")

    fallback = tags_by_name("f", a.tags)
    if fallback:
        print("Fallback:", fallback[0])

    description = tags_by_name("d", a.tags)
    if description:
        print("Description:", description[0])

    dhash = tags_by_name("h", a.tags)
    if dhash:
        print("Description hash:", hexlify(dhash[0]))

    expiry = tags_by_name("x", a.tags)
    if expiry:
        print("Expiry (seconds):", expiry[0])

    for t in [t for t in a.tags if t[0] not in "rdfhx"]:
        print("UNKNOWN TAG {}: {}".format(t[0], hexlify(t[1])))


parser = argparse.ArgumentParser(description="Encode lightning address")
subparsers = parser.add_subparsers(dest="subparser_name", help="sub-command help")

parser_enc = subparsers.add_parser("encode", help="encode help")
parser_dec = subparsers.add_parser("decode", help="decode help")

parser_enc.add_argument("--currency", default="bc", help="What currency")
parser_enc.add_argument(
    "--route",
    action="append",
    default=[],
    help="Extra route steps of form pubkey/channel/feebase/feerate/cltv+",
)
parser_enc.add_argument("--fallback", help="Fallback address for onchain payment")
parser_enc.add_argument("--description", help="What is being purchased")
parser_enc.add_argument(
    "--description-hashed", help="What is being purchased (for hashing)"
)
parser_enc.add_argument("--expires", type=int, help="Seconds before offer expires")
parser_enc.add_argument(
    "--timestamp", type=int, help="Timestamp (seconds after epoch) instead of now"
)
parser_enc.add_argument("--no-amount", action="store_true", help="Don't encode amount")
parser_enc.add_argument("amount", type=float, help="Amount in currency")
parser_enc.add_argument("paymenthash", help="Payment hash (in hex)")
parser_enc.add_argument("privkey", help="Private key (in hex)")
parser_enc.set_defaults(func=encode)

parser_dec.add_argument("lnaddress", help="Address to decode")
parser_dec.add_argument(
    "--rate", type=float, help="Convfersion amount for 1 currency unit"
)
parser_dec.add_argument("--pubkey", help="Public key for the chanid")
parser_dec.add_argument(
    "--verbose", help="Print out extra decoding info", action="store_true"
)
parser_dec.set_defaults(func=decode)

if __name__ == "__main__":
    options = parser.parse_args()
    if not options.subparser_name:
        parser.print_help()
    else:
        options.func(options)
