#!/usr/bin/env python3

# A simple script that connects to a server and displays block headers

import time
from .. import SimpleConfig, Network
from electrum.util import print_msg, json_encode

# start network
#c = SimpleConfig()
#network = Network(c)
network = Libbitcoin(asyncio.get_event_loop())
network.start()

print("started")
# wait until connected
while network.is_connecting():
    print("connecting")
    time.sleep(0.5)

if not network.is_connected():
    print_msg("daemon is not connected")
    sys.exit(1)

print("connected")
#print(network.last_height())
# 2. send the subscription
#print(network.headers(500_000, 100))
callback = lambda response: print(response)
#network.server_version("block_headers script", "1.2", callback)
future = network.subscribe_to_headers(callback)
#queue = network.subscribe_to_headers()
#block = asyncio.run_coroutine_threadsafe(queue.get(),asyncio.get_event_loop() )
#print(block.result())

print("future", future)
# 3. wait for results
while network.is_connected():
    print(".", end='', flush=True)
    time.sleep(2)
