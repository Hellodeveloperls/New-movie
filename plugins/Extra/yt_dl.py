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
        "cookiefile": "mycookies.txt",  # Ensure this file exists and is valid
        "quiet": True,
        "geo_bypass": True,
        "socket_timeout": 60,  # Increased timeout to 60 seconds
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

        await message.reply_audio(
            audio=open(audio_file, "rb"),
            caption="🎶 Powered by [SA Bots](https://t.me/SA_Bots)",
            title=title,
            performer=performer,
            duration=seconds,
            thumb=thumb_name
        )
        await m.delete()
    except Exception as e:
        print("Download error:", e)
        await m.edit("🚫 Error while downloading the song.")
    
    # Cleanup
    for f in (audio_file, thumb_name):
        if os.path.exists(f):
            os.remove(f)


# Video downloader (/video, /mp4)
@Client.on_message(filters.command(["video", "mp4"]) & filters.private)
async def vsong(client, message: Message):
    query = get_text(message)
    if not query:
        return await message.reply("Example: /video your video name or link")

    info_msg = await message.reply(f"🎬 Searching video: `{query}`")
    try:
        search = SearchVideos(query, offset=1, mode="dict", max_results=1)
        result = search.result()["search_result"][0]
        video_link = result["link"]
        video_title = result["title"]
        video_id = result["id"]
        thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        # Save thumbnail
        thumb_file = wget.download(thumb_url)

    except Exception as e:
        print("Search error:", e)
        return await info_msg.edit("❌ Video not found. Try something else.")

    await asyncio.sleep(0.5)

    ydl_opts = {
        "format": "best",
        "cookiefile": "mycookies.txt",  # Ensure cookie file is valid
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "outtmpl": "%(id)s.%(ext)s",
        "quiet": True,
        "socket_timeout": 60,  # Increased timeout for downloading video
        "retries": 3,  # Retry logic in case of failure
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ytdl_data = ydl.extract_info(video_link, download=True)
            video_file = f"{ytdl_data['id']}.mp4"

        caption = f"""🎞️ **TITLE:** [{video_title}]({video_link})\n👤 **Requested by:** {message.from_user.mention}"""

        await client.send_video(
            chat_id=message.chat.id,
            video=open(video_file, "rb"),
            duration=int(ytdl_data.get("duration", 0)),
            file_name=ytdl_data.get("title", "video.mp4"),
            thumb=thumb_file,
            caption=caption,
            supports_streaming=True,
            reply_to_message_id=message.id
        )
        await info_msg.delete()
    except Exception as e:
        print("Video error:", e)
        await info_msg.edit(f"❌ Download failed.\n**Error:** `{str(e)}`")
    finally:
        # Clean up temp files (video and thumbnail)
        for f in (video_file, thumb_file):
            if os.path.exists(f):
                os.remove(f)
