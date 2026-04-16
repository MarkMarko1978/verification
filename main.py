import discord
from discord.ext import commands
from captcha.image import ImageCaptcha
import random
import string
import os
import io

# Словарь для временного хранения сгенерированных капчей
pending_captchas = {}

def generate_captcha():
    """Генерирует текст и картинку капчи"""
    image = ImageCaptcha(width=280, height=90)
    text = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    data = image.generate(text)
    return text, io.BytesIO(data.getvalue())

class CaptchaModal(discord.ui.Modal, title='Проверка на бота'):
    answer = discord.ui.TextInput(
        label='Введите текст с картинки',
        style=discord.TextStyle.short,
        placeholder='Например: Ez8786',
        required=True,
        min_length=6,
        max_length=6
    )

    async def on_submit(self, interaction: discord.Interaction):
        expected_text = pending_captchas.get(interaction.user.id)

        if not expected_text:
            await interaction.response.send_message("Капча устарела. Нажми кнопку верификации еще раз.", ephemeral=True)
            return

        if self.answer.value.lower() == expected_text.lower():
            guild = interaction.guild
            # ТВОИ ID РОЛЕЙ
            role_member_id = 1477584227062255627      # Роль "Участник"
            role_unverified_id = 1486357883800125592  # Роль "Не верифицирован" (от Juniper)

            member_role = guild.get_role(role_member_id)
            unverified_role = guild.get_role(role_unverified_id)

            try:
                if member_role:
                    await interaction.user.add_roles(member_role)
                if unverified_role:
                    await interaction.user.remove_roles(unverified_role)

                await interaction.response.send_message("✅ Верификация успешно пройдена!", ephemeral=True)
                pending_captchas.pop(interaction.user.id, None)
            except discord.Forbidden:
                await interaction.response.send_message("❌ Ошибка: Подними роль бота выше всех остальных в настройках сервера!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Неверно! Попробуй еще раз.", ephemeral=True)

class CaptchaAnswerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label='Ввести капчу', style=discord.ButtonStyle.green)
    async def enter_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CaptchaModal())

class VerifyStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Пройти верификацию', style=discord.ButtonStyle.primary, custom_id='start_verify_btn')
    async def start_verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        text, image_data = generate_captcha()
        pending_captchas[interaction.user.id] = text

        file = discord.File(fp=image_data, filename='captcha.png')
        await interaction.response.send_message(
            "Реши капчу на картинке ниже и нажми кнопку ввода:",
            file=file,
            view=CaptchaAnswerView(),
            ephemeral=True
        )

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyStartView())

    async def on_ready(self):
        print(f'✅ Бот {self.user} запущен!')

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    # Твоя гифка
    gif_url = "https://media.discordapp.net/attachments/1483812220499398717/1491483610291634418/standard_6.gif"
    
    embed = discord.Embed(
        title="🛡️ Верификация", 
        description="Для того чтобы присоединиться к серверу, нажмите кнопку ниже и пройдите капчу.",
        color=discord.Color.green()
    )
    embed.set_image(url=gif_url)
    
    await ctx.send(embed=embed, view=VerifyStartView())

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
