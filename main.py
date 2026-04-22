import discord
from discord.ext import commands
from captcha.image import ImageCaptcha
import random
import string
import os
import io

# Словарь для временного хранения капчей
pending_captchas = {}

def generate_captcha():
    """Генерирует понятную капчу: только цифры, меньше шума"""
    # Делаем картинку чуть шире, чтобы цифры не слипались
    image = ImageCaptcha(width=300, height=100)
    
    # Генерируем 5 цифр (их проще читать, чем буквы)
    text = ''.join(random.choices(string.digits, k=5))
    
    # Генерируем изображение
    data = image.generate(text)
    return text, io.BytesIO(data.getvalue())

class CaptchaModal(discord.ui.Modal, title='Проверка на бота'):
    answer = discord.ui.TextInput(
        label='Введите цифры с картинки',
        style=discord.TextStyle.short,
        placeholder='Например: 12345',
        required=True,
        min_length=5,
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        expected_text = pending_captchas.get(interaction.user.id)

        if not expected_text:
            await interaction.response.send_message("Капча устарела. Нажми кнопку еще раз.", ephemeral=True)
            return

        if self.answer.value == expected_text:
            guild = interaction.guild
            # ТВОИ ID РОЛЕЙ
            role_member_id = 1491087158981693520      # Роль "Участник"
            role_unverified_id = 1491087158579036308  # Роль "Не верифицирован"

            member_role = guild.get_role(role_member_id)
            unverified_role = guild.get_role(role_unverified_id)

            try:
                if member_role:
                    await interaction.user.add_roles(member_role)
                if unverified_role:
                    await interaction.user.remove_roles(unverified_role)

                await interaction.response.send_message("✅ Верификация успешно пройдена! Добро пожаловать.", ephemeral=True)
                pending_captchas.pop(interaction.user.id, None)
            except discord.Forbidden:
                await interaction.response.send_message("❌ Ошибка: Подними роль бота выше в списке ролей!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Неверно! Попробуй еще раз (нажми кнопку заново).", ephemeral=True)

class CaptchaAnswerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label='Ввести ответ', style=discord.ButtonStyle.green)
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
            "Внимательно введи 5 цифр с картинки:",
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
        print(f'✅ Бот {self.user} запущен! Капча теперь понятная.')

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    # Твоя новая гифка
    gif_url = "https://media.discordapp.net/attachments/1273284092309540877/1496209627161825380/standard.gif"
    
    embed = discord.Embed(
        title="🛡️ Верификация Ez Squad", 
        description="Для того чтобы присоединиться к серверу, нажмите кнопку ниже и пройдите капчу.",
        color=0x010101  # Черная полоска
    )
    embed.set_image(url=gif_url)
    
    await ctx.send(embed=embed, view=VerifyStartView())

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
