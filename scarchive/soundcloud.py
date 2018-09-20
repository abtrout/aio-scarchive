import asyncio
import aiohttp
import logging
import math

from .track import Track
from .user import User


class Client(object):

    def __init__(self, client_id):

        self.base_url = "https://api.soundcloud.com"
        self.client_id = client_id
        self.crawl_page_size = 25
        self.max_attempts = 3

    async def crawl_user_tracks(self, user_id):
        url = "/".join([self.base_url, "users", str(user_id), "tracks"])
        async for item in self.__crawl_pages(url):
            if item["kind"] == "track":
                yield Track.from_json(item)

    async def crawl_user_followings(self, user_id):
        url = "/".join([self.base_url, "users", str(user_id), "followings"])
        async for item in self.__crawl_pages(url):
            if item["kind"] == "user":
                yield User.from_json(item)

    async def resolve_user(self, user_url):
        async with aiohttp.ClientSession() as session:
            url = "/".join([self.base_url, "resolve"])
            user_json = await self.__fetch_json(url, params={"url": user_url})
            return User.from_json(user_json)

    async def save_track_to_file(self, track, fd):
        if not track.is_downloadable and not track.is_streamable:
            logging.warning("user_id={} track_id={} is_downloadable={} is_streamable={} Track not downloadable".format(
                track.user_id, track.id, track.is_downloadable, track.is_streamable))
            return

        url = "/".join([self.base_url, "tracks", str(track.id), "download" if track.is_downloadable else "stream"])
        for attempt in range(self.max_attempts):
            try:
                async with aiohttp.ClientSession(raise_for_status=True) as session:
                    async with session.get(url, params={"client_id": self.client_id}) as r:
                        while True:
                            chunk = await r.content.read()
                            if not chunk:
                                break
                            fd.write(chunk)
                        return
            except aiohttp.ClientResponseError as e:
                logging.error("attempt={} url={} Failed to save_track_to_file: {}".format(attempt, url, e))
                await asyncio.sleep(math.pow(2, attempt))

    async def __crawl_pages(self, url):
        page_params = {"limit": self.crawl_page_size, "linked_partitioning": 1}
        while url is not None:
            data = await self.__fetch_json(url, params=page_params)
            if data is not None and "collection" in data:
                for item in data["collection"]:
                    yield item
                url = data.get("next_href")
            else:
                logging.error("url={} Unexpected response from __crawl_pages: {}".format(url, data))
                    
    async def __fetch_json(self, url, params={}):
        params.update(client_id=self.client_id)
        for attempt in range(self.max_attempts):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as r:
                    if r.status == 200:
                        return await r.json()
                    else:
                        logging.error("attempt={} url={} status={} Failed to __fetch_json: {}".format(attempt, url, r.status, await r.text()))
                        await asyncio.sleep(math.pow(2, attempt))
