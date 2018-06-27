import asyncio
from unittest.mock import MagicMock, Mock

import asynctest
from asynctest.mock import CoroutineMock

import lib.blockchain
from lib.blockchains import Blockchains


class TestBlockchains(asynctest.TestCase):
    @staticmethod
    def header():
        """ Taken from block 529438
        """
        return {'version': 536870912, 'prev_block_hash': '0000000000000000003627505d1d859d86dbb60d2fabc03d185ff2711b1cd665', 'merkle_root': '153ce6fde6d9e749a87177f3f8fbe81338e5d580f3c1e289a8e53ea9d6ae0ca6', 'timestamp': 1530083119, 'bits': 389508950, 'nonce': 1167100690, 'block_height': 529438}  # noqa: E501

    def test_simple_append_header(self):
        queue = MagicMock(
            spec=asyncio.Queue,
            get=CoroutineMock(side_effect=[self.header()]))
        servers = [
            MagicMock(subscribe_to_headers=CoroutineMock(return_value=queue))]

        chains = [MagicMock(spec=lib.blockchain.Blockchain)]
        lib.blockchain.blockchains = chains

        lib.blockchain.find_blockchain_to_append = lambda _: chains[0]

        blockchains = Blockchains(servers, chains)

        try:
            asyncio.get_event_loop().run_until_complete(
                blockchains.monitor_servers())
        except RuntimeError:
            # Normal test termination occurred
            pass

        chains[0].save_header.assert_called_with(self.header())

    def test_header_already_present(self):
        queue = MagicMock(
            spec=asyncio.Queue,
            get=CoroutineMock(side_effect=[self.header()]))
        servers = [
            MagicMock(subscribe_to_headers=CoroutineMock(return_value=queue))]

        chains = [MagicMock(spec=lib.blockchain.Blockchain)]
        lib.blockchain.blockchains = chains

        lib.blockchain.find_blockchain_to_append = lambda _: None
        lib.blockchain.find_blockchain_containing = lambda _: Mock()

        blockchains = Blockchains(servers, chains)
        try:
            asyncio.get_event_loop().run_until_complete(
                blockchains.monitor_servers())
        except RuntimeError:
            # Normal test termination occurred
            pass

        chains[0].assert_not_called()

    def test_catch_up(self):
        chain = MagicMock(
            spec=lib.blockchain.Blockchain,
            height=Mock(return_value=100),
            can_connect=Mock(return_value=True)
        )
        server = MagicMock(
            last_height=CoroutineMock(return_value=200),
            block_header=CoroutineMock(),
        )

        blockchains = Blockchains([server], [chain])
        asyncio.get_event_loop().run_until_complete(blockchains.catch_up())

        server.block_header.assert_any_call(101)

    def test_catch_up_wo_suitable_server(self):
        chain = MagicMock(
            spec=lib.blockchain.Blockchain,
            can_connect=Mock(return_value=False),
        )
        server = MagicMock(
            block_header=CoroutineMock(return_value=200),
        )

        blockchains = Blockchains([server], [chain])
        asyncio.get_event_loop().run_until_complete(blockchains.catch_up())

        chain.save_header.assert_not_called()

    def test_blockchain_has_difficulty(self):
        pass
