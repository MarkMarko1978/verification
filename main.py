import discord
from discord.ext import commands
from captcha.image import ImageCaptcha
import random
import string

# Словарь для временного хранения сгенерированных капчей: {user_id: expected_text}
pending_captchas = {}


def generate_captcha():
    """Генерирует текст и картинку капчи"""
    image = ImageCaptcha(width=280, height=90)
    # Генерируем 6 случайных символов (буквы + цифры)
    text = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    data = image.generate(text)
    return text, data


class CaptchaModal(discord.ui.Modal, title='Проверка на бота'):
    answer = discord.ui.TextInput(
        label='Введите текст с картинки',
        style=discord.TextStyle.short,
        placeholder='Например: Ez87863',
        required=True,
        min_length=6,
        max_length=6
    )

    async def on_submit(self, interaction: discord.Interaction):
        expected_text = pending_captchas.get(interaction.user.id)

        if not expected_text:
            await interaction.response.send_message("Время вышло или капча не найдена. Нажми кнопку еще раз.",
                                                    ephemeral=True)
            return

        # Проверяем ответ (без учета регистра)
        if self.answer.value.lower() == expected_text.lower():
            guild = interaction.guild

            # === ВАЖНО: ВСТАВЬ СЮДА СВОИ ID РОЛЕЙ ===
            role_member_id = 1477584227062255627  # ID роли "Участник"
            role_unverified_id = 1486357883800125592  # ID роли "Не верифицирован" (от Juniper)

            member_role = guild.get_role(role_member_id)
            unverified_role = guild.get_role(role_unverified_id)

            if member_role:
                await interaction.user.add_roles(member_role)
            if unverified_role:
                await interaction.user.remove_roles(unverified_role)  # Забираем роль, которую выдал Juniper

            await interaction.response.send_message("✅ Верификация успешно пройдена! Добро пожаловать на Ez Squad.", ephemeral=True)
            # Удаляем капчу из памяти
            del pending_captchas[interaction.user.id]
        else:
            await interaction.response.send_message("❌ Неверно! Попробуйте еще раз пройти верификацию.", ephemeral=True)
            del pending_captchas[interaction.user.id]


class CaptchaAnswerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Ввести капчу', style=discord.ButtonStyle.green)
    async def enter_captcha(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Открываем модальное окно для ввода текста
        await interaction.response.send_modal(CaptchaModal())


class VerifyStartView(discord.ui.View):
    def __init__(self):
        # timeout=None делает кнопку вечной (после рестарта на Railway она будет работать)
        super().__init__(timeout=None)

    @discord.ui.button(label='Пройти верификацию', style=discord.ButtonStyle.primary, custom_id='start_verify_btn')
    async def start_verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Генерируем новую капчу для пользователя
        text, image_data = generate_captcha()
        pending_captchas[interaction.user.id] = text

        file = discord.File(fp=image_data, filename='captcha.png')
        view = CaptchaAnswerView()

        # Отправляем картинку как ephemeral (видит только нажимающий)
        await interaction.response.send_message(
            "Реши капчу на картинке, чтобы присоедениться к Ez Squad. Нажми кнопку ниже, чтобы ввести ответ.",
            file=file,
            view=view,
            ephemeral=True
        )


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True  # Обязательно для выдачи ролей
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Регистрируем главную кнопку, чтобы она не ломалась при рестарте бота на Railway
        self.add_view(VerifyStartView())

    async def on_ready(self):
        print(f'Бот {self.user} запущен и готов к работе!')


bot = MyBot()


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    """Команда для создания сообщения с кнопкой верификации"""
    embed = discord.Embed(
        title="🛡️ Верификация", 
        description="Для доступа к серверу нажмите кнопку ниже и решите капчу.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=VerifyStartView())

# Берем токен из переменных Railway
TOKEN = os.getenv('TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    print("ОШИБКА: Токен не найден в переменных окружения!")
