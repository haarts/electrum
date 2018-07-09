import os
import threading
import asyncio
import concurrent.futures
import zmq.asyncio

import pylibbitcoin.client

from lib import constants
from lib import blockchain
from lib import blockchains
from lib.triggers import Triggers
from lib.util import DaemonThread
from lib.libbitcoin.protocol import Protocol
from lib.libbitcoin.server import Server

TIMEOUT = 5
CHECKPOINT_SIZE = 2016


class Libbitcoin(DaemonThread, Protocol, Triggers):
    """ Libbitcoin brings everything together.
    """

    def __init__(self, loop, client_settings=None):
        DaemonThread.__init__(self)

        # FIXME passing path like that is an utter hack
        # self._blockchains = blockchain.read_blockchains("/tmp/blockchains")
        self._blockchains = blockchain.read_blockchains(
            "/home/harm/.electrum/testnet")
        # FIXME: This is truly awful:
        blockchain.blockchains = self._blockchains

        self._loop = loop
        self._client_settings = self.__client_settings(client_settings)
        self._auto_connect = True
        self._is_connecting = True
        self._proxy = None
        self._servers = Libbitcoin._servers_from(
            self._client_settings,
            Libbitcoin._servers_from_file(),
            self._loop,
        )
        self.active_server = None

    def run(self):
        """ This method is called when the thread starts.

        Here we don't need to take into account the thread saveness because
        this method is called by the 'start' method which is called on the
        same thread.
        """
        self._loop.run_until_complete(self.__connect())
        asyncio.ensure_future(self.__update_blockchains(), loop=self._loop)
        #asyncio.ensure_future(self.__run_jobs(), loop=self._loop)
        self._loop.call_soon(self.__run_jobs)
        self._loop.run_forever()

    def stop(self):
        """ This method SHOULD be called when stopping the program. Is method
        is overwritten from the DaemonThread super class.

        We can't use a nice `asyncio.gather` or similar because these calls are
        not thread safe.
        """
        for server in self._servers:
            self.__wait_for(server.disconnect)

        self._loop.call_soon_threadsafe(self._loop.stop)
        self.on_stop()

    def get_server_height(self):
        return self.active_server.last_height()[1]

    def is_connected(self):
        return True if next(
            self.__connected_servers(),
            False
        ) else False

    def is_connecting(self):
        return self._is_connecting

    # TODO
    def get_donation_address(self):
        pass

    def get_interfaces(self):
        return [server for server in self._servers if server.is_connected()]

    def get_servers(self):
        """ Return a dictionary compatible with the one returned in the
        lib/network module. That explains the cast to string.
        """
        servers = {}
        for server in self._servers:
            servers[server.connection_details["hostname"]] = {
                't': str(server.connection_details["ports"]["query"]["public"]),  # noqa: E501
                's': str(server.connection_details["ports"]["query"]["secure"])
            }

        return servers

    # FIXME this method is doing a lot of things and should be split into:
    # get_proxy
    # get_autoconnect
    # get_active_server
    def get_parameters(self):
        return self.active_server.host, \
            self.active_server.port, \
            self.active_server.protocol, \
            self.proxy, \
            self.auto_connect

    # FIXME this method is doing a lof of things and should be split into:
    # set_proxy
    # set_autoconnect
    # set_active_server
    def set_parameters(self, host, port, protocol, proxy, auto_connect):
        """ This method is used to change to the specified server.
        This server might be new or might be known already. If unknown add
        the server. In both cases switch to it.

            'protocol' is ElectrumX specific and is dropped.
            'proxy' is TODO
        """
        self.switch_to_interface(":".join([host, port]))

        self._auto_connect = auto_connect

    # NOTE: the name of the method is legacy in a sense. Libbitcoin doesn't
    # have the concept of 'interface'. `switch_to_server` is a better name.
    def switch_to_interface(self, server):
        """ The 'server' argument is a string <host>:<port>:<protocol>
        """
        host, port = server.split(':')
        connection_details = {
            "hostname": host,
            "ports": {"query": {"public": port}, "block": {"public": port}}}
        server = Server(connection_details,
                        self._client_settings,
                        self._loop)
        if server in self._servers:
            server = next(
                (existing for existing in self._servers if existing == server))
        else:
            self._servers.append(server)

        self.active_server = server

    def unsubscribe(self, callback):
        pass

    def fetch_missing_headers_around(self, height):
        """ Fetches the block headers between two checkpoints.

        Arguments:
            height -- the height of a block from which the lower and upper
            boundary is determined.
        """
        start_height = (height // CHECKPOINT_SIZE) * CHECKPOINT_SIZE

        self._loop.call_soon_threadsafe(
            self.active_server.block_headers, start_height, CHECKPOINT_SIZE)

    def blockchain(self):
        """ Returns the local chain which mirrors the chain advertised by the
        active server.

        NOTE: this only works if syncing is complete.
        """
        _, last_height = self.__wait_for(self.active_server.last_height)
        last_header = self.__wait_for(
            self.active_server.block_header, last_height)
        return blockchain.find_blockchain_containing(blockchains.to_local(
            last_header, last_height))

    def blockchains(self):
        """ Returns all the local chains which have a remote advertising it.
        """
        finder = blockchains.Blockchains(
            self.__connected_servers(),
            self._blockchains.values())
        pairs = self.__wait_for(finder.blockchain_servers_pairs)
        out = {}
        for fork_height, chain in self._blockchains.items():
            if len(pairs[chain]) > 0:
                out[fork_height] = chain

        return out

    def get_blockchains(self):
        """ Legacy name from the Network class.
        """
        return self.blockchains()

    # NOTE 'follow_chain' and 'switch_to_interface' really are more of the
    # same. We should consider making it uniform.
    def follow_chain(self, index):
        pass

    def get_local_height(self):
        return self.blockchain().height()

    # private methods
    def __run_jobs(self):
        print("running jobs")
        self.run_jobs()
        self._loop.call_later(3, self.__run_jobs)

    async def __update_blockchains(self):
        synchronizer = blockchains.Blockchains(
            self.__connected_servers(),
            self._blockchains.values())
        asyncio.ensure_future(synchronizer.catch_up(), loop=self._loop)
        asyncio.ensure_future(synchronizer.monitor_servers(), loop=self._loop)

    async def __connect(self):
        self._is_connecting = True
        await asyncio.wait(
            [server.connect() for server in self._servers],
            loop=self._loop,
            return_when=asyncio.FIRST_COMPLETED,
        )

        self.active_server = next(self.__connected_servers())
        self._is_connecting = False

    # TODO 'self' is really dumb here. I should reconsider the constructor.
    def __client_settings(self, client_settings):
        if client_settings is None:
            ctx = zmq.asyncio.Context()
            ctx.linger = 500
            return pylibbitcoin.client.ClientSettings(
                timeout=2,
                context=ctx,
                loop=self._loop,
            )

        return client_settings

    def _servers_from(client_settings, servers, loop):
        return [Server(connection_details, client_settings, loop)
                for connection_details in servers]

    def _servers_from_file():
        # TODO read recent servers OR
        # read packaged servers OR read testnet
        return constants.read_json(
            os.path.join("libbitcoin", "servers_testnet.json"), [])

    def __connected_servers(self):
        return (server for server
                in self._servers if server.is_connected() is True)

    def __wait_for(self, it, *args):
        print("it", it)
        print("main ID", threading.main_thread().ident)
        print("ID", threading.get_ident())
        if threading.main_thread().ident == threading.get_ident():
            return asyncio.run_coroutine_threadsafe(
                    it(*args), self._loop).result(TIMEOUT)

        #return asyncio.ensure_future(it(*args), loop=self._loop)  # doesn't wait for the result
        #return self._loop.run_until_complete(it(*args))  # Event loop already runs
        #return await it(*args)  # __wait_for can't be a coro b/c of the threadsafe call
        #return it(*args)
        future = concurrent.futures.Future()
        def callback():
            asyncio.ensure_future(it(*args), loop=self._loop)
        self._loop.call_soon(callback)
        return future.result(TIMEOUT)
