#!/usr/bin/env python

import aiohttp
import asyncio
import logging
import os

from mutagen import MutagenError
from mutagen.id3 import APIC, TALB, TPE1, TIT2, ID3
from mutagen.mp3 import MP3

from scarchive import Archive, Client

async def crawl_tracks(client, archive, userq, trackq, worker_id):
    while True:
        user = await userq.get()
        new_tracks_count = await crawl_new_tracks(client, archive, trackq, user)
        logging.info("user_id={} new_tracks_count={} worker_id={} Finished new crawling tracks".format(user.id, new_tracks_count, worker_id))
        userq.task_done()


async def crawl_new_tracks(client, archive, queue, user):
    logging.info("user_id={} Crawling new tracks for user".format(user.id))
    new_tracks_count = 0
    async for track in client.crawl_user_tracks(user.id):
        if archive.find_track(track.id):
            return new_tracks_count
        await queue.put(track)
        new_tracks_count += 1


async def archive_tracks(client, archive, queue, worker_id, base_dir):
    while True:
        track = await queue.get()
        track.uri = await download_track(track, client, base_dir)
        if track.uri is not None:
            await add_tags_to_track_file(track.uri, track)
            archive.add_track(track)
            logging.info("user_id={} track_id={} worker_id={} Archived track".format(track.user_id, track.id, worker_id))
        queue.task_done()


async def download_track(track, client, base_dir):
    # Tracks are saved to disk at base_dir/user_id/track_id.mp3.
    user_dir = "/".join([base_dir, str(track.user_id)])
    track_file = "{}/{}.mp3".format(user_dir, track.id)
    # Create user directories if they do not exist.
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    with open(track_file, "wb") as fd:
        # TODO: this could throw an exception (??)
        await client.save_track_to_file(track, fd)

    return track_file


async def add_tags_to_track_file(track_file, track):
    try:
        mp3 = MP3(track_file, ID3=ID3)
    except Exception as e:
        logging.warning(
            "user_id={} track_id={} uri={} Failed to parse MP3 from track file".format(track.user_id, track.id, track.uri))
        return
            
    # Make sure this MP3 has valid ID3 tags header, etc. If the file already
    # has valid ID3 tags, Mutagen will thrown an Exception, and we'll ignore it!
    try:
        mp3.add_tags()
    except MutagenError:
        logging.warning(
            "user_id={} track_id={} uri={} Track file already has ID3 tags".format(track.user_id, track.id, track.uri))
        #pass

    # Set title, artist, and album (which is hardcoded to "Soundcloud Tracks").
    mp3.tags.add(TIT2(encoding=3, text=track.title))
    mp3.tags.add(TPE1(encoding=3, text=track.username))
    mp3.tags.add(TALB(encoding=3, text=u"Soundcloud Tracks"))

    # Add artwork if the track has it. We use the 500x500 image variant rather than the "large" default.
    if track.artwork_url:
        artwork_url = track.artwork_url.replace("-large.jpg", "-t500x500.jpg")
        async with aiohttp.ClientSession() as session:
            async with session.get(artwork_url) as r:
                mp3.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, data=await r.read()))

    mp3.save()


async def main(archive, client, archive_dir):
    # Create a queue and consumers to archive tracks from the queue.
    user_queue = asyncio.Queue(maxsize=25)
    tracks_queue = asyncio.Queue(maxsize=100)

    user_workers = [
        asyncio.ensure_future(crawl_tracks(client, archive, user_queue, tracks_queue, worker_id))
        for worker_id in range(8)]

    archive_workers = [
        asyncio.ensure_future(archive_tracks(client, archive, tracks_queue, worker_id, archive_dir))
        for worker_id in range(4)]

    # Find new tracks for users in the archive and add them to the queue.
    for user in archive.list_all_users():
        #crawl_new_tracks(client, archive, tracks_queue, user)
        await user_queue.put(user)

    # Wait until they've all been archived, then clean up.
    await user_queue.join()
    for worker in user_workers:
        worker.cancel()

    await tracks_queue.join()
    for worker in archive_workers:
        worker.cancel()


if __name__ == "__main__":
    # TODO: better logging configuration.
    logging.basicConfig(level=logging.INFO)

    archive_db = os.environ.get("SC_ARCHIVE_DB", "archive.db")
    archive_dir = os.environ.get("SC_ARCHIVE_DIR", "data")
    archive = Archive(db_file=archive_db)

    client_id = os.environ.get("SC_CLIENT_ID")
    client = Client(client_id=client_id)

    try:
        loop = asyncio.get_event_loop()
        loop.set_debug(enabled=True)
        loop.run_until_complete(main(archive, client, archive_dir))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
