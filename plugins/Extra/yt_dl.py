from __future__ import unicode_literals

import os, requests, asyncio, wget
from pyrogram import filters, Client
from pyrogram.types import Message
from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL

# Text extractor
def get_text(message: Message) -> [None, str]:
    if not message.text or " " not in message.text:
        return None
    return message.text.split(None, 1)[1]

# Song downloader (/song, /mp3)
@Client.on_message(filters.command(['song', 'mp3']) & filters.private)
async def song(client, message):
    query = get_text(message)
    if not query:
        return await message.reply("Example: `/song Vaathi Coming`")
    
    m = await message.reply(f"🎧 Searching your song...\n**Query:** `{query}`")
    
    ydl_opts = {
        "format": "bestaudio[ext=m4a]",
        "cookiefile": "cookies.txt",  # <-- Make sure this file is valid
        "quiet": True,
        "geo_bypass": True,
        "socket_timeout": 60,  # Increased timeout (60 seconds)
        "retries": 3,  # Retry logic in case of failure
    }

    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        result = results[0]
        link = f"https://youtube.com{result['url_suffix']}"
        title = result["title"][:40]
        thumbnail = result["thumbnails"][0]
        duration = result["duration"]
        performer = "VJ NETWORKS™"

        # Save thumbnail
        thumb_name = f'thumb_{title}.jpg'.replace('/', '_')
        thumb = requests.get(thumbnail, allow_redirects=True)
        with open(thumb_name, 'wb') as f:
            f.write(thumb.content)

    except Exception as e:
        print("Search error:", e)
        return await m.edit("❌ Failed to find the song.\nTry another query.")

    await m.edit("📥 Downloading your song...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict)

        # Convert duration to seconds
        secmul, seconds = 1, 0
        for t in reversed(duration.split(':')):
            seconds += int(t) * secmul
            secmul *= 60

        await
