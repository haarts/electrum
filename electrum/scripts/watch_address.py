#!/usr/bin/env python3

import sys
import time
from electrum import bitcoin
from .. import SimpleConfig, Network
from electrum.util import print_msg, json_encode

try:
    addr = sys.argv[1]
except Exception:
    print("usage: watch_address <bitcoin_address>")
    sys.exit(1)

sh = bitcoin.address_to_scripthash(addr)

# start network
c = SimpleConfig()
network = Network(c)
network.start()

# wait until connected
while network.is_connecting():
    time.sleep(0.1)

if not network.is_connected():
    print_msg("daemon is not connected")
    sys.exit(1)

# 1. translate the Bitcoin address to a scripthash
scripthash = bitcoin.address_to_scripthash(addr)
print_msg("Address '{}' becomes scripthash '{}'".format(addr, scripthash))

# 2. send the subscription
callback = lambda response: print_msg(json_encode(response.get('result')))
network.subscribe_to_scripthash(scripthash, callback)

# 3. wait for results
while network.is_connected():
    time.sleep(1)
