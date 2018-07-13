""" The blockchains module manages the construction of the local representation
of all blockchains advertised by the remote backends.
"""
from typing import List
import asyncio

import bitcoin.core

from lib.libbitcoin.server import Server
import lib.blockchain


def to_local(cblock_header, height):
    """ Convert a bitcoin.core.CBlockHeader to a lib.blockchain compatible
    header"""
    return lib.blockchain.deserialize_header(
        cblock_header.serialize(), height)


def to_local_from_block(cblock, height):
    """ Convert a bitcoin.core.CBlock to a lib.blockchain compatible
    header"""
    return lib.blockchain.deserialize_header(
        bitcoin.core.CBlockHeader(
            cblock.nVersion,
            cblock.hashPrevBlock,
            cblock.hashMerkleRoot,
            cblock.nTime,
            cblock.nBits,
            cblock.nNonce,
        ).serialize(), height)


class Blockchains:
    """
    There are three public methods:
    - catch_up: for each local blockchain finds a server and syncs
    - monitor_servers: subscribes to the headers of all servers and appends
      where possible.
    - blockchain_servers_pairs: returns a dict of local blockchains
      and their mirroring servers. Eg: {chain1: [serverA, serverB], ...}
    """

    def __init__(self,
                 servers: List[Server],
                 blockchains: List[lib.blockchain.Blockchain]):
        self._servers = servers
        self._blockchains = blockchains

    async def blockchain_servers_pairs(self):
        blockchains = {}
        for chain in self._blockchains:
            blockchains[chain] = await self.__find_servers(chain)

        return blockchains

    async def catch_up(self):
        [await self.__catch_up(blockchain) for blockchain in self._blockchains]

    async def monitor_servers(self):
        queues = [await self.__monitor(server) for server in self._servers]
        [await self.__process_blocks_for(queue) for queue in queues]

    async def __process_blocks_for(self, queue):
        while True:
            _, height, block = await queue.get()
            compatible_header = to_local_from_block(
                block,
                self.__fix_libbitcoin_bug(height))
            blockchain = lib.blockchain.find_blockchain_to_append(
                compatible_header)

            # Simple case: append the header to an existing chain
            if blockchain:
                blockchain.save_header(compatible_header)
                continue

            # The header received is already stored, we can safely ignore it
            if self.__is_header_already_stored(compatible_header):
                continue

            # A header is received which can not be tied to a local
            # representation.

    async def __monitor(self, server) -> asyncio.Queue:
        return await server.subscribe_to_blocks()

    def __is_header_already_stored(self, header):
        if lib.blockchain.find_blockchain_containing(header):
            return True

        return False

    # NOTE: this fetches headers one by one and could be upgraded later to
    # fetch batches.
    async def __catch_up(self, blockchain):
        servers = await self.__find_servers(blockchain)
        if not servers:
            return

        server = servers[0]
        _, server_height = await server.last_height()
        for missing in range(blockchain.height() + 1, server_height + 1):
            header = await server.block_header(missing)
            compatible_header = to_local(header, missing)
            blockchain.save_header(compatible_header)

    # NOTE: It feel wrong to do these awaits sequential. Ideally I would like
    # to have a generator.
    async def __find_servers(self, blockchain):
        return [server for server
                in self._servers
                if await self.__is_matching(server, blockchain)]

    async def __is_matching(self, server, blockchain):
        next_header = await server.block_header(blockchain.height())
        compatible_header = to_local(next_header, blockchain.height())
        return blockchain.can_connect(compatible_header, check_height=False)

    @staticmethod
    def __fix_libbitcoin_bug(height):
        """ Make the fact we are fixing a temporary bug stupidly obvious
        """
        return height + 1
