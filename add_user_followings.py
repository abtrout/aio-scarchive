#!/usr/bin/env python

import asyncio
import logging
import os
import sys

from scarchive import Archive, Client


async def main(archive, client, url):
    crawl_for_user = await client.resolve_user(url)
    async for user in client.crawl_user_followings(crawl_for_user.id):
        if archive.find_user(user.id) is None:
            archive.add_user(user)
            logging.info("username={} user_id={} Added user".format(user.username, user.id))
        else:
            logging.debug("username={} user_id={} User exists".format(user.username, user.id))


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("USAGE: {} https://soundcloud.com/username".format(sys.argv[0]))
        sys.exit(1)

    archive = Archive(db_file=os.environ.get("SC_ARCHIVE_DB", "archive.db"))
    client = Client(client_id=os.environ.get("SC_CLIENT_ID"))
    logging.basicConfig(level=logging.INFO)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(archive, client, sys.argv[1]))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
