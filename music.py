import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'files/%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
}
ffmpeg_options = {
    'options': '-vn -b:a 384k',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_autoplay = False
        self.autoplay_ctx = None
        self.last_video_info = None

    @commands.command()
    async def join(self, ctx, *, title=None):
        """Gabung ke voice channel dan play lagu dari URL atau title"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f'```Gabung ke channel: {channel}```')

            if title:
                # Cari video berdasarkan judul
                await self.search_and_play(ctx, title)
            else:
                await ctx.send('```Masukkan judul lagu atau URL untuk diputar!```')
        else:
            await ctx.send('```Join voice channel dulu cuy!```')

    @commands.command()
    async def play(self, ctx, *, title):
        """Play musik berdasarkan URL atau title"""
        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.bot.get_command('join'), title=title)
            vc = ctx.voice_client

        self.is_autoplay = True
        self.autoplay_ctx = ctx
        await self.search_and_play(ctx, title)

    async def search_and_play(self, ctx, title):
        """Cari video berdasarkan judul dan langsung putar"""
        # Cari video berdasarkan title
        search_url = f"ytsearch:{title}"
        data = ytdl.extract_info(search_url, download=False)
        
        if 'entries' in data:
            video = data['entries'][0]  # Ambil video pertama dari hasil pencarian
            audio_url = video['url']
            self.last_video_info = video

            await self.play_audio(ctx, audio_url)
        else:
            await ctx.send(f'```Gak nemu video dengan judul "{title}" cuy.```')

    async def play_audio(self, ctx, url):
        """Mainkan audio dari URL yang diberikan"""
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **ffmpeg_options),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.autoplay_next(), self.bot.loop
            )
        )
        await ctx.send(f'```🎶 Playing Song: {self.last_video_info["title"]}```')

    async def autoplay_next(self):
        """Autoplay lagu berikutnya berdasarkan related video"""
        if not self.is_autoplay:
            return

        related = self.last_video_info.get('related_videos')
        if related:
            next_id = related[0]['id']
            next_url = f"https://www.youtube.com/watch?v={next_id}"
            await self.play_audio(self.autoplay_ctx, next_url)

    @commands.command()
    async def stopautoplay(self, ctx):
        """Stop autoplay"""
        self.is_autoplay = False
        await ctx.send("⛔ Autoplay dimatiin cuy.")

    @commands.command()
    async def pause(self, ctx):
        """Pause musik"""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send("```⏸ Lagu di-pause cuy.```")

    @commands.command()
    async def resume(self, ctx):
        """Resume musik"""
        vc = ctx.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send("```▶️ Lanjut lagi nih lagunya.```")

    @commands.command()
    async def skip(self, ctx):
        """Skip lagu yang lagi diputer"""
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await ctx.send("```⏭ Skip lagunya.```")

    @commands.command()
    async def leave(self, ctx):
        """Leave voice channel"""
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
            await ctx.send("```Keluar dari voice channel.```")

async def setup(bot):
    await bot.add_cog(Music(bot))