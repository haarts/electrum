import unittest
from unittest.mock import MagicMock
import lib.blockchain


class TestBlockchains(unittest.TestCase):
    def test_find_blockchain_for_wo_dict_header(self):
        self.assertIsNone(lib.blockchain.find_blockchain_for("not a dict"))

    def test_find_blockchain_for_w_dict_header(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=lib.blockchain.Blockchain, check_header=lambda x: True)}

        self.assertIsNotNone(lib.blockchain.find_blockchain_for({}))

    def test_find_blockchain_for_and_failing(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=lib.blockchain.Blockchain, check_header=lambda x: False)}

        self.assertIsNone(lib.blockchain.find_blockchain_for({}))

    def test_can_connect(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=lib.blockchain.Blockchain, can_connect=lambda x: True)}

        self.assertTrue(lib.blockchain.can_connect({}))

    def test_can_connect_and_failing(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=lib.blockchain.Blockchain, can_connect=lambda x: False)}

        self.assertFalse(lib.blockchain.can_connect({}))


class TestBlockchain(unittest.TestCase):
    pass
