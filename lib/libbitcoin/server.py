import asyncio
from urllib.parse import urlparse
import pylibbitcoin.client

class Server:
    def __init__(self, connection_details, settings):
        def url_from(server):
            return "tcp://" + server["hostname"] + ":" + str(server["ports"]["public"])

        self.url = url_from(connection_details)
        self._client = pylibbitcoin.client.Client(self.url, settings=settings)

    async def disconnect(self):
        return await self._client.stop()

    async def connect(self):
        error_code, last_height = await self._client.last_height()
        self.last_height = last_height
        return error_code

    def is_connected(self):
        return self.last_height > 0

    def last_height(self):
        return asyncio.get_event_loop().run_until_complete(self._client.last_height())

    def port(self):
        return urlparse(self.url).port

    def host(self):
        return urlparse(self.url).hostname

    def protocol(self):
        return urlparse(self.url).scheme

    def __eq__(self, other):
        return self.url == other.url

    def __ne__(self, other):
        return self.url != other.url
