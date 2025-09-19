import telebot
from config import *
from extensions import *
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

bot = telebot.TeleBot(TOKEN)
user_data = {}



def create_currency_keyboard(stage: str):
    markup = InlineKeyboardMarkup(row_width=3)
    for key in keys.keys():
        callback_data = f"{stage}:{key}"
        markup.add(InlineKeyboardButton(key.capitalize(), callback_data=callback_data))
    return markup

@bot.message_handler(commands=['values'])
def values(message: telebot.types.Message):
    text = 'Доступные валюты:\n' + '\n'.join([f'- {key}' for key in keys.keys()])
    markup = create_currency_keyboard('base')
    bot.send_message(message.chat.id, text + '\n\nВыберите исходную валюту:', reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start', 'help'])
def help(message: telebot.types.Message):
    text = 'Формат: <base> <quote> <amount>\nДоступные валюты: /values'
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/values'), KeyboardButton('/help'))
    bot.reply_to(message, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call: telebot.types.CallbackQuery):
    user_id = call.from_user.id
    data = call.data.split(':')
    stage, currency = data[0], data[1]

    if user_id not in user_data:
        user_data[user_id] = {}

    if stage == 'base':
        user_data[user_id]['base'] = currency
        markup = create_currency_keyboard('quote')
        bot.answer_callback_query(call.id, f"Валюта, цену которой надо узнать: {currency.capitalize()}")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f'\n\nВыбрано: *{currency.capitalize()}*. \nТеперь выберите целевую валюту:',
            reply_markup=markup,
            parse_mode='Markdown'
        )
    elif stage == 'quote':
        user_data[user_id]['quote'] = currency
        bot.answer_callback_query(call.id, f"Валюта, цену в которой надо узнать: {currency.capitalize()}")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + f'\nВыбрано: *{currency.capitalize()}*. \nВведите количество:',
            reply_markup=None,
            parse_mode='Markdown'
        )


@bot.message_handler(content_types=['text'])
def convert(message: telebot.types.Message):
    user_id = message.from_user.id
    try:
        if user_id in user_data and 'base' in user_data[user_id] and 'quote' in user_data[user_id]:

            amount = message.text.strip()
            base = user_data[user_id]['base']
            quote = user_data[user_id]['quote']
            total_base = Converter.get_price(base, quote, amount)
            rate = total_base / float(amount)
            text = f'💰 *Цена {amount} {base.upper()} в {quote.upper()}:* {total_base:.2f} {quote.upper()}\n📈 *Курс:* 1 {base.upper()} = {rate:.4f} {quote.upper()}'
            bot.send_message(message.chat.id, text, parse_mode='Markdown')
            del user_data[user_id]
        else:
            values = message.text.split()
            if len(values) != 3:
                raise APIException("Неверное количество параметров. Формат: <валюта> <её цена в другой валюте> <количество>")
            base, quote, amount = values
            if float(amount) < 1:
                raise APIException('Неверное количество: {amount} (должно быть больше 0).')
            total_base = Converter.get_price(base,quote, amount)
            rate = total_base / float(amount)
            text = f'💰 *Цена {amount} {base.upper()} в {quote.upper()}:* {total_base:.2f} {quote.upper()}\n📈 *Курс:* 1 {base.upper()} = {rate:.4f} {quote.upper()}'
            bot.send_message(message.chat.id, text, parse_mode='Markdown')
    except APIException as e:
        bot.reply_to(message, f'Ошибка пользователя.\n{e}')
    except requests.RequestException as e:
        bot.reply_to(message, f'Ошибка сети или API: {e}. Попробуйте позже.')
    except Exception as e:
        bot.reply_to(message, f'Не удалось обработать команду\n{e}')




bot.polling(none_stop=True)



