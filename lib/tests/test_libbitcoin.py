import unittest
import asyncio
import asynctest
import pylibbitcoin.client
import bitcoin.core

from unittest.mock import MagicMock

import lib.blockchain
import lib.blockchains
from lib.libbitcoin.libbitcoin import Libbitcoin
from lib.libbitcoin.server import Server


class TestLibbitcoin(asynctest.TestCase):
    def setUp(self):
        Libbitcoin._servers_from = lambda x, y, z: [MagicMock(spec=Server)]
        lib.blockchain.read_blockchains = lambda header_dir: {}
        self.libbitcoin = Libbitcoin(None)

    def tearDown(self):
        pass

    def test_is_connected(self):
        self.assertFalse(self.libbitcoin.is_connected())

        server = MagicMock(autospec=Server)
        server.is_connected.return_value = True
        self.libbitcoin._servers = [server]
        self.assertTrue(self.libbitcoin.is_connected())

    def test_is_connecting(self):
        self.assertTrue(self.libbitcoin.is_connecting())

    def test_servers_wo_recent_servers(self):
        server = MagicMock(autospec=Server)
        server.connection_details = {
            "hostname": "some-host",
            "ports": {"query": {"public": 9091, "secure": 9093}}}
        self.libbitcoin._servers = [server]

        servers = self.libbitcoin.get_servers()
        self.assertEqual(1, len(servers))
        self.assertEqual("some-host", list(servers.keys())[0])
        self.assertEqual("9091", servers["some-host"]["t"])

    @unittest.skip("pending")
    def test_servers_w_recent_servers(self):
        # TODO manipulate ~/.electrum/recent_servers
        self.assertEqual(2, len(self.libbitcoin.get_servers()))

    def test_set_parameters_new_server(self):
        pylibbitcoin.client.Client = MagicMock()
        self.assertEqual(1, len(self.libbitcoin._servers))
        self.libbitcoin.set_parameters("example.com", "9091", "", None, True)
        self.assertEqual(
            "example.com",
            self.libbitcoin.active_server._connection_details["hostname"])
        self.assertEqual(2, len(self.libbitcoin._servers))

    def test_set_parameters_existing_server(self):
        pylibbitcoin.client.Client = MagicMock()
        self.assertEqual(1, len(self.libbitcoin._servers))
        self.libbitcoin.set_parameters("example.com", "9091", None, None, True)
        self.libbitcoin.set_parameters("example.com", "9091", None, None, True)
        self.assertEqual(2, len(self.libbitcoin._servers))

    def test_switch_to_interface(self):
        pylibbitcoin.client.Client = MagicMock(autospec=Server)
        self.libbitcoin.switch_to_interface("example.com:9091")
        self.assertEqual(2, len(self.libbitcoin._servers))

    def test_blockchain(self):
        lib.blockchain.blockchains[0] = MagicMock(
            spec=lib.blockchain.Blockchain,
            check_header=MagicMock(return_value=True))
        self.libbitcoin._Libbitcoin__wait_for = MagicMock(
            side_effect=[(None, 1), (None, bitcoin.core.CBlockHeader())])
        self.libbitcoin.active_server = MagicMock(
            spec=lib.libbitcoin.server.Server)

        self.assertEqual(
            self.libbitcoin._blockchains[0],
            self.libbitcoin.blockchain())

    def test_get_blockchains(self):
        local_chain = MagicMock()
        orphaned_chain = MagicMock()
        self.libbitcoin._blockchains = {0: local_chain, 1: orphaned_chain}
        lib.blockchains.Blockchains = MagicMock(
            spec=lib.blockchains.Blockchains)
        self.libbitcoin._Libbitcoin__wait_for = MagicMock(
            return_value={local_chain: [MagicMock()], orphaned_chain: []})

        chains = self.libbitcoin.get_blockchains()
        self.assertEqual({0: local_chain}, chains)


class TestServer(asynctest.TestCase):
    connection_details = {
        "hostname": "smt",
        "ports": {
            "query": {
                "public": 9091,
            },
            "block": {
                "public": 9093,
            }
        }
    }

    def test_initial_api_call(self):
        expected_height = 500_000
        client_mock = asynctest.mock.MagicMock()
        client_mock.return_value.last_height = \
            asynctest.CoroutineMock(return_value=(None, expected_height))
        pylibbitcoin.client.Client = client_mock

        server = Server(self.connection_details, None, self.loop)
        remote_height = asyncio.get_event_loop().run_until_complete(
            server.last_height())[1]

        self.assertEqual(expected_height, remote_height)

    def test_is_connected(self):
        server = Server(self.connection_details, None, self.loop)
        self.assertFalse(server.is_connected())

        server._last_height = 0
        self.assertTrue(server.is_connected())

    def test_block_headers(self):
        client_mock = asynctest.mock.MagicMock()
        client_mock.return_value.block_header = asynctest.CoroutineMock(
            return_value=(None, 1))
        pylibbitcoin.client.Client = client_mock
        server = Server(self.connection_details, None, self.loop)

        # starting from header 500_000 get the next 100
        asyncio.get_event_loop().run_until_complete(
            server.block_headers(500_000, 100))

        self.assertEqual(100, client_mock.return_value.block_header.call_count)

    def test_subscribe_addresses(self):
        client_mock = asynctest.mock.MagicMock()
        client_mock.return_value.subscribe_address = asynctest.CoroutineMock(
            return_value=(None, MagicMock(spec=asyncio.Queue)))
        pylibbitcoin.client.Client = client_mock
        server = Server(self.connection_details, None, self.loop)

        asyncio.get_event_loop().run_until_complete(
            server.subscribe_addresses(['a', 'b', 'c']))

        self.assertEqual(
            3,
            client_mock.return_value.subscribe_address.call_count)
