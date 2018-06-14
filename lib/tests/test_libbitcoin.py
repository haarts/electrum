import unittest
import asyncio
import asynctest
import pylibbitcoin

from lib.simple_config import SimpleConfig
from lib.libbitcoin.libbitcoin import Libbitcoin
from lib.libbitcoin.server import Server

class TestLibbitcoin(unittest.TestCase):
    def setUp(self):
        self.libbitcoin = Libbitcoin(SimpleConfig())

    def tearDown(self):
        self.libbitcoin.disconnect()

    def test_is_connected(self):
        self.assertTrue(self.libbitcoin.is_connected())

    def test_servers_wo_recent_servers(self):
        self.assertEqual(4, len(self.libbitcoin.get_servers()))

    @unittest.skip("pending")
    def test_servers_w_recent_servers(self):
        # TODO manipulate ~/.electrum/recent_servers
        self.assertEqual(2, len(self.libbitcoin.get_servers()))


class TestServer(asynctest.TestCase):
    def test_initial_api_call(self):
        height = 500_000
        client_mock = asynctest.mock.MagicMock()
        client_mock.return_value.last_height = asynctest.CoroutineMock(return_value=height)
        pylibbitcoin.client.Client = client_mock

        server = Server({"dns": "smt", "ports": {"public": 9091}})
        self.assertEqual(height, server.last_height)
