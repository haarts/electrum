import asyncio


class Protocol():
    """ The Protocol class defines all mappings between the Libbitcoin API
    and the internal Electrum API.

    See https://github.com/libbitcoin/libbitcoin-server/wiki/Query-Service
    """

    def subscribe_to_scripthashes(self, hashes, callback=None):
        pass

    def subscribe_to_addresses(self, addresses, callback=None):
        pass

    def broadcast_transaction(self, transaction, callback=None):
        pass

    def get_history_for_address(self, address, callback=None):
        pass

    def get_history_for_scripthash(self, hash, callback=None):
        pass

    def headers(self, start_height, count, callback=None):
        pass

    def subscribe_to_headers(self, callback=None):
        future = asyncio.run_coroutine_threadsafe(
            self.active_server.subscribe_to_headers(),
            self._loop)
        queue = future.result()  # this call blocks, shortly

        if not callback:
            return queue

        return asyncio.run_coroutine_threadsafe(
            self.__process_items(queue.get, callback),
            self._loop)

    async def __process_items(self, get, callback):
        while True:
            result = await get()
            callback(result)

    def get_merkle_for_transaction(self, tx_hash, tx_height, callback=None):
        pass

    def subscribe_to_scripthash(self, scripthash, callback=None):
        pass

    def get_transaction(self, transaction_hash, callback=None):
        pass

    def get_transactions(self, transaction_hashes, callback=None):
        pass

    def listunspent_for_scripthash(self, scripthash, callback=None):
        pass

    def get_balance_for_scripthash(self, scripthash, callback=None):
        pass

    def server_version(self, client_name, protocol_version, callback=None):
        pass
