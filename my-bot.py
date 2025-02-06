import yt_dlp
import datetime
from discord.ext import commands, tasks
import discord
from discord import FFmpegPCMAudio
from dataclasses import dataclass
import collections
from collections import deque


#BOT_TOKEN = #cant share
CHANNEL_ID = 1326803032490508352
MAX_TIME = 5
SONG_QUEUE = deque()
replaying = False

@dataclass
class Session:
    is_active: bool = False
    start_time: int = 0

bot = commands.Bot(command_prefix = "!", intents = discord.Intents.all())
session = Session()

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.event
async def on_ready():
    print("Hello, I am Bot")
    await bot.change_presence(activity = discord.Game(name = "use !readme"))
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("Hello, I am a Bot")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def add(ctx, *arr):
    result = 0
    for i in arr:
        result += int(i)
    await ctx.send(f"= {result}")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def summaryofseth(ctx):
    await ctx.send("Seth bullies me :(")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def join(ctx):
    if ctx.author.voice and ctx.voice_client:
        await leave(ctx)
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"I have joined {channel}")
    else:
        await ctx.send("Sooooo, you're not in a channel")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@tasks.loop(minutes = MAX_TIME, count = 2)
async def leavevc(ctx):
    #Ignores first loop
    if leavevc.current_loop == 0:
        return
    if ctx.voice_client and ctx.voice_client.is_playing():
        leavevc.stop()
        return
    channel = bot.get_channel(CHANNEL_ID)
    await ctx.voice_client.disconnect()
    await channel.send(f"**SEE YA LOSERS!**\n{MAX_TIME} mins have passed since the last song played")
    leavevc.stop()

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

skip_in_progress = False

@bot.command()
async def play(ctx, *args):
    if not ctx.voice_client:
        await join(ctx)
    
    #Queue
    url = " ".join(args)
    SONG_QUEUE.append(url)
    await ctx.send(f"Added to queue: {url}")
    if len(SONG_QUEUE) == 1:
        await ctx.send(f"There is now 1 song in the queue")
    else:
        await ctx.send(f"There are now {len(SONG_QUEUE)} songs in the queue")

    if not ctx.voice_client.is_playing():
        await play_next_song(ctx)

async def play_next_song(ctx):
    global skip_in_progress, current_song_path

    if not SONG_QUEUE:
        await ctx.send("No song to play!")
        leavevc.stop()
        if not leavevc.is_running():
            leavevc.start(ctx)
        return

    url = SONG_QUEUE.popleft()

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'default_search': 'ytsearch',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                info = info['entries'][0]
            
            if 'url' not in info:
                raise ValueError("Could not find a valid audio URL.")

            url2 = info['url']
            title = info.get('title', 'Unknown Title')
        
        before_options = (
            "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )

        current_song_path = url2
        source = FFmpegPCMAudio(url2, before_options=before_options)

        if leavevc.is_running():
            leavevc.stop()

        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(source, after=lambda e: after_song(ctx, e))
            await ctx.send(f"Now playing: {title}")
        else:
            await ctx.send("Already playing audio. Skipping to next song...")

        if SONG_QUEUE:
            await ctx.send(f"Next Song: {SONG_QUEUE[0]}")
            await ctx.send(f"There are now {len(SONG_QUEUE)} songs in the queue")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"Error: {e}")
        await play_next_song(ctx)

def after_song(ctx, error):
    global skip_in_progress

    if error:
        print(f"Error during playback: {error}")
    
    if not skip_in_progress:
        bot.loop.create_task(play_next_song(ctx))

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def skip(ctx):
    global skip_in_progress
    global replaying

    if ctx.voice_client and ctx.voice_client.is_playing():
        skip_in_progress = True
        ctx.voice_client.stop() 
        if not replaying:
            await ctx.send("Skipping...")
        await play_next_song(ctx)
        skip_in_progress = False
    elif not ctx.voice_client.is_playing() and replaying:
        skip_in_progress = True 
        await play_next_song(ctx)
        skip_in_progress = False
    else:
        await ctx.send("No song is currently playing.")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("I leave now")

    else:
        await ctx.send("Already gone, retard")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Song paused")
    else:
        await ctx.send("No song to be paused")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Song resumed")
    else:
        await ctx.send("No song is paused")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def replay(ctx):
    global current_song_path, replaying 

    leavevc.stop()
    SONG_QUEUE.insert(0, current_song_path)
    await ctx.send("Replaying...")
    replaying = True
    await skip(ctx)
    replaying = False

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

@bot.command()
async def readme(ctx):
    await ctx.send("**!add** x y = adds any amount of numbers together")
    await ctx.send("**!summaryofseth** = reveals a summary of seth")
    await ctx.send("**!join** = joins your vc")
    await ctx.send("**!leave** = leaves your vc")
    await ctx.send("**!play** x = plays any song from youtube using text or url")
    await ctx.send("**!skip** = skips the song")
    await ctx.send("**!pause** = pauses the song")
    await ctx.send("**!resume** = resumes the song")
    await ctx.send("**!replay** = replays/restarts the most recently played song")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

bot.run(BOT_TOKEN)