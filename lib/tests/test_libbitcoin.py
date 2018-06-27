import unittest
import asyncio
import asynctest
import pylibbitcoin.client
import zmq.asyncio

from unittest.mock import MagicMock
from lib.simple_config import SimpleConfig
from lib.libbitcoin.libbitcoin import Libbitcoin
from lib.libbitcoin.server import Server


class TestLibbitcoin(unittest.TestCase):
    def setUp(self):
        Libbitcoin._servers_from = lambda x, y: [MagicMock(autospec=Server)]
        self.libbitcoin = Libbitcoin(None)
        self.libbitcoin.disconnect = lambda: None

    def tearDown(self):
        pass

    def test_is_connected(self):
        self.assertFalse(self.libbitcoin.is_connected())

        self.libbitcoin._servers = [MagicMock(autospec=Server, last_height=1)]
        self.assertTrue(self.libbitcoin.is_connected())

    def test_is_connecting(self):
        self.assertFalse(self.libbitcoin.is_connecting())

    def test_servers_wo_recent_servers(self):
        self.assertEqual(1, len(self.libbitcoin.get_servers()))

    @unittest.skip("pending")
    def test_servers_w_recent_servers(self):
        # TODO manipulate ~/.electrum/recent_servers
        self.assertEqual(2, len(self.libbitcoin.get_servers()))

    def test_set_parameters_new_server(self):
        pylibbitcoin.client.Client = MagicMock(autospec=Server)
        self.assertEqual(1, len(self.libbitcoin._servers))
        self.libbitcoin.set_parameters("example.com", "9091", "", None, True)
        self.assertEqual("tcp://example.com:9091", self.libbitcoin.active_server.url)
        self.assertEqual(2, len(self.libbitcoin._servers))

    def test_set_parameters_existing_server(self):
        pylibbitcoin.client.Client = MagicMock(autospec=Server)
        self.assertEqual(1, len(self.libbitcoin._servers))
        self.libbitcoin.set_parameters("example.com", "9091", None, None, True)
        self.libbitcoin.set_parameters("example.com", "9091", None, None, True)
        self.assertEqual(2, len(self.libbitcoin._servers))

    def test_switch_to_interface(self):
        pylibbitcoin.client.Client = MagicMock(autospec=Server)
        self.libbitcoin.switch_to_interface("example.com:9091")
        self.assertEqual(2, len(self.libbitcoin._servers))


class TestServer(asynctest.TestCase):
    def test_initial_api_call(self):
        height = 500_000
        client_mock = asynctest.mock.MagicMock()
        client_mock.return_value.last_height = \
            asynctest.CoroutineMock(return_value=(None, height))
        pylibbitcoin.client.Client = client_mock

        server = Server({"hostname": "smt", "ports": {"public": 9091}}, None)
        self.assertEqual(height, server.last_height()[1])

    def test_is_connected(self):
        server = Server({"hostname": "smt", "ports": {"public": 9091}}, None)
        self.assertFalse(server.is_connected())

        server._last_height = 0
        self.assertTrue(server.is_connected())
