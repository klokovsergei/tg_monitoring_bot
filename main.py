import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.filters import BaseFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import ChatMemberUpdated

BOT_TOKEN = os.getenv('BOT_TOKEN')

TEXT_START = ('Для начала работы нажмите кнопку «Поделиться номером». '
              'Мы используем ваш номер телефона только для регистрации и '
              'уведомлений о статусе интернет-каналов. '
              'Это займет всего несколько секунд!')
TEXT_HELP = ('/start - используется 1 раз только для регистрации\n'
             '/help - вызвать подсказку по управлению ботом')

# список админов бота
admin_ids: list[int] = [214904629]

users = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


# Этот фильтр будет проверять наличие неотрицательных чисел
# в сообщении от пользователя, передавать в хэндлер их список
class NumbersInMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool | dict[str, list[int]]:
        numbers = []
        # Сплитуем сообщение по пробелам, нормализуем кажду часть, удаляя
        # лишние знаки препинания и невидимые символы, проверяем на то,
        # что в таких словах только фицры, приводим к целым числам
        # и добавляем их в список
        for word in message.text.split():
            normalized_word = word.replace('.', '').replace(',', '').strip()
            if normalized_word.isdigit():
                numbers.append(int(normalized_word))
        # Если в списке есть числа - возвращаем словарь со списком чисел по ключу 'numbers'
        if numbers:
            return {'numbers': numbers}
        return False


# функция для создания клавиатуры с кнопкой для запроса номера
async def create_contact_keyboard():
    button = [[KeyboardButton(text="📞 Отправить номер", request_contact=True)]]
    keyboard = ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True, one_time_keyboard=True)
    return keyboard


@dp.message(IsAdmin(admin_ids) and Command(commands='alarm'))
async def process_alarm_all_users(message: Message):
    await bot.send_message(chat_id='-1002492032591', text='Админ инициировал АЛАРМ для всех клиентов')


async def process_start_command(message: Message):
    print('здесь')
    if message.from_user.id not in users:
        users[message.from_user.id] = {
            'ip_adresses': None,
            'web_services': None,
            'mode': None,
            'active': True,
            'def': None
        }
    if users[message.from_user.id]['def'] is None:
        await message.answer(text=TEXT_START)
        markup = await create_contact_keyboard()
        await message.answer('Регистрация по номеру телефона', reply_markup=markup)
    else:
        await message.answer(text='Вы уже зарегистрированы.\n'
                                  'Для справки нажмите /help')


@dp.message(F.contact)
async def get_contact(message: Message):
    contact = message.contact
    await message.answer(f"Спасибо{', ' + contact.first_name if contact.first_name else ''}. "
                         f"Ваш номер {contact.phone_number} был получен.", reply_markup=ReplyKeyboardRemove())
    users[message.from_user.id]['def'] = contact.phone_number
    print(contact)


async def process_help_command(message: Message):
    await message.answer(text=TEXT_HELP)


# сработает, если есть числа в сообщении
@dp.message(F.text.lower().startswith('найди числа'),
            NumbersInMessage())
async def process_if_numbers(message: Message, numbers: list[int]):
    await message.answer(text=f'Нашёл: {", ".join(str(num) for num in numbers)}')


# сработает, если НЕ нашел числа в сообщении
@dp.message(F.text.lower().startswith('найди числа'))
async def process_if_numbers(message: Message):
    await message.answer(text='Не нашёл что-то здесь чисел 😨')


async def print_update(message: Message):
    txt = (f'{'=' * 10}\nID пользователя - {message.from_user.id}\n'
           f'Login пользователя - {message.from_user.username}\n'
           f'Message:\n'
           f'{'-' * 10}\n{message.text}\n{'=' * 10}')
    await bot.send_message(chat_id='-1002492032591', text=txt)
    print(message)


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def process_user_blocked_bot(event: ChatMemberUpdated):
    await bot.send_message(chat_id='-1002492032591',
                           text=f'Пользователь {event.from_user.id} запустил 🟢 бота Neuron.')


@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated):
    await bot.send_message(chat_id='-1002492032591',
                           text=f'Пользователь {event.from_user.id} заблокировал 🔴 бота Neuron.')


dp.message.register(process_start_command, Command(commands='start'))
dp.message.register(process_help_command, Command(commands='help'))
dp.message.register(print_update)

if __name__ == '__main__':
    dp.run_polling(bot)
