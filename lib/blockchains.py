""" The blockchains module manages the construction of the local representation
of all blockchains advertised by the remote backends.
"""
from typing import List
import asyncio

from lib.libbitcoin.server import Server
import lib.blockchain


class Blockchains:
    """
    There are two public methods:
    - catch_up: for each local blockchain finds a server and syncs
    - monitor_servers: subscribes to the headers of all servers and appends
      where possible.
    """

    def __init__(self,
                 servers: List[Server],
                 blockchains: List[lib.blockchain.Blockchain]):
        self._servers = servers
        self._blockchains = blockchains

    async def catch_up(self):
        [await self.__catch_up(blockchain) for blockchain in self._blockchains]

    async def monitor_servers(self):
        queues = [await self.__monitor(server) for server in self._servers]
        [await self.__process_headers_for(queue) for queue in queues]

    async def __process_headers_for(self, queue):
        while True:
            header = await queue.get()
            blockchain = lib.blockchain.find_blockchain_to_append(header)

            # Simple case: append the header to an existing chain
            if blockchain:
                blockchain.save_header(header)
                continue

            # The header received is already stored, we can safely ignore it
            if self.__is_header_already_stored(header):
                continue

            # A header is received which can not be tied to a local
            # representation.

    async def __monitor(self, server) -> asyncio.Queue:
        return await server.subscribe_to_headers()

    def __is_header_already_stored(self, header):
        if lib.blockchain.find_blockchain_containing(header):
            return True

        return False

    async def __catch_up(self, blockchain):
        server = await self.__find_server(blockchain)
        if not server:
            return

        server_height = await server.last_height()
        for missing in range(blockchain.height() + 1, server_height + 1):
            header = await server.block_header(missing)
            blockchain.save_header(header)

    async def __find_server(self, blockchain):
        for server in self._servers:
            if await self.__is_matching(server, blockchain):
                return server

        return None

    async def __is_matching(self, server, blockchain):
        next_header = await server.block_header(blockchain.height())
        return blockchain.can_connect(next_header)
