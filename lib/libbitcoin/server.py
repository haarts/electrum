""" This module represents ONE libbitcoin backend server
"""
import pylibbitcoin.client
import asyncio


PUBLIC_PORT = "public"
SECURE_PORT = "secure"


class Server:
    def __init__(self, connection_details, settings, loop):
        self._connection_details = connection_details
        self._client = pylibbitcoin.client.Client(
            connection_details["hostname"],
            self.__select_public_ports(connection_details["ports"]),
            settings=settings)
        self._loop = loop
        self._last_height = None

    async def connect(self):
        error_code, last_height = await self._client.last_height()
        self._last_height = last_height
        return error_code

    async def disconnect(self):
        await self._client.stop()

    def is_connected(self):
        return self._last_height is not None

    async def subscribe_addresses(self, hashes):
        coros = [self.subscribe_address(hash_) for hash_ in hashes]

        return await asyncio.gather(*coros, loop=self._loop)

    async def subscribe_address(self, address):
        _, queue = await self._client.subscribe_address(address)
        return queue

    # NOTE: I'm not convinced that the order of the headers is monotomically
    # increasing.
    async def block_headers(self, start_height, count):
        coros = []
        for height in range(start_height, start_height + count):
            coros.append(self.block_header(height))

        return await asyncio.gather(*coros, loop=self._loop)

    async def block_header(self, height):
        _, header = await self._client.block_header(height)
        return header

    def subscribe_to_blocks(self):
        return self._client.subscribe_to_blocks()

    def last_height(self):
        return self._client.last_height()

    def port(self):
        return self.connection_details["ports"]["query"][PUBLIC_PORT]

    def host(self):
        return self.connection_details["hostname"]

    def protocol(self):
        return "tcp://"

    def __select_public_ports(self, connection_details):
        return {
            "query": connection_details["query"][PUBLIC_PORT],
            "block": connection_details["block"][PUBLIC_PORT],
        }

    def __eq__(self, other):
        return self._connection_details == other._connection_details

    def __ne__(self, other):
        return self._connection_details != other._connection_details

    def __str__(self):
        return "libbitcoin.Server(hostname: {}, height: {})" \
            .format(self._connection_details["hostname"], self._last_height)
