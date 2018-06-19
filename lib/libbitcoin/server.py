import asyncio
import pylibbitcoin.client

class Server:
    def __init__(self, connection_details):
        def url_from(server):
            return "tcp://" + server["hostname"] + ":" + str(server["ports"]["public"])

        self.url = url_from(connection_details)
        self._client = pylibbitcoin.client.Client(self.url)
        self.last_height = self.last_height()

    async def disconnect(self):
        return self._client.stop()

    def last_height(self):
        return asyncio.get_event_loop().run_until_complete(self._client.last_height())
