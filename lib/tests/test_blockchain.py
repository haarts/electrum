import os
import unittest
from unittest.mock import MagicMock
import lib.blockchain
from lib.blockchain import Blockchain


class TestBlockchains(unittest.TestCase):
    def test_find_blockchain_containing_wo_dict_header(self):
        self.assertIsNone(lib.blockchain.find_blockchain_containing("not a dict"))

    def test_find_blockchain_containing_w_dict_header(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=Blockchain, check_header=lambda x: True)}

        self.assertIsNotNone(lib.blockchain.find_blockchain_containing({}))

    def test_find_blockchain_containing_and_failing(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=Blockchain, check_header=lambda x: False)}

        self.assertIsNone(lib.blockchain.find_blockchain_containing({}))

    def test_find_blockchain_to_append(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=Blockchain, can_connect=lambda x: True)}

        self.assertIsNotNone(lib.blockchain.find_blockchain_to_append({}))

    def test_find_blockchain_to_append_and_failing(self):
        lib.blockchain.blockchains = {
            0: MagicMock(autospec=Blockchain, can_connect=lambda x: False)}

        self.assertIsNone(lib.blockchain.find_blockchain_to_append({}))

    def test_read_blockchains(self):
        blockchains = lib.blockchain.read_blockchains(
            os.path.join("lib", "tests", "blockchain"))
        longest_chain = blockchains[0]
        forked_at_height_2 = blockchains[2]
        forked_from_fork_2_at_height_4 = blockchains[4]
        self.assertEqual(3, len(blockchains))

class TestBlockchain(unittest.TestCase):
    def valid_header_after_checkpoints():
        # obtained by 'btcctl getblock 00000000b0b5a018d9fd972aa7516ceb05ef398037496b0e9948a1db82787af5' and cherry picking fields.  # noqa: E501
        return {
            'version': 536870912,
            'prev_block_hash': '00000000348cace1a41b3513748fd4251d84948e8c044d3a4decfec5b5755545',  # noqa: E501
            'merkle_root': '6b4e3c789cbeac01989ffd9d3401dd3ab9f6241f3154949ad0db66ca24222e28',  # noqa: E501
            'timestamp': 1529388060,
            'bits': int('1d00ffff', 16),
            'nonce': 1087293774,
            'block_height': 1325823,
        }

    def test_check_header(self):
        blockchain = Blockchain("", 1, 0)
        blockchain.get_hash = lambda header: lib.blockchain.hash_header(
            TestBlockchain.valid_header_after_checkpoints())

        self.assertTrue(
            blockchain.check_header(
                TestBlockchain.valid_header_after_checkpoints()))

    def test_can_connect(self):
        pass
