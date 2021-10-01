import telebot
import config
import datetime
import scheduled_messages as sm
import db_commands as db

bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['test'], chat_types=['private'])
def test(message):
    """
    Bot command for test purposes. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id to 'developers' var in 'config.py'
    """
    if message.from_user.id in config.developers:
        pass


@bot.message_handler(commands=['send_reminder'], chat_types=['private'])
def send_reminder(message):
    """
    Manually send the reminder for upcoming event. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id to 'developers' var in 'config.py'
    """
    if message.from_user.id in config.developers:
        telegram_ids = sm.send_event_reminder()
        bot.send_message(message.from_user.id,
                         f'Напоминание отправлено:<code>\n{telegram_ids}</code>',
                         reply_markup=telebot.types.ReplyKeyboardRemove(),
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(commands=['get_id'], chat_types=['private'])
def get_id(message):
    bot.send_message(message.from_user.id,
                     f'<code>твой telegram ID: {message.from_user.id}</code>',
                     reply_markup=telebot.types.ReplyKeyboardRemove(),
                     parse_mode='HTML',
                     disable_notification=True)


@bot.message_handler(commands=['start'], chat_types=['private'])
def start(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton(f"Список событий", callback_data=f'LIST_EVENTS::')
    btn_02 = telebot.types.InlineKeyboardButton(f"Создать новое событие", callback_data=f'CREATE_EVENT::')
    keyboard.row(btn_01)
    keyboard.row(btn_02)
    bot.send_message(message.chat.id,
                     '<code>Следующие события:</code>',
                     reply_markup=keyboard,
                     parse_mode='HTML',
                     disable_notification=True)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    command, data = call.data.split('::')

    if command == 'LIST_EVENTS':
        keyboard = telebot.types.InlineKeyboardMarkup()
        naming = {'train': '\U0001F3D0', 'game': '\U0001F3C5'}
        for event in db.upcoming_events():
            date_str = event[0].strftime('%d.%m.%Y')
            date = event[0]
            event_type = naming[event[1]]
            btn = telebot.types.InlineKeyboardButton(f"{event_type}  {date_str}",
                                                     callback_data=f'EVENT::{date}')
            keyboard.row(btn)
        btn_exit = telebot.types.InlineKeyboardButton(f"Выйти",
                                                      callback_data=f'EXIT::')
        keyboard.row(btn_exit)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         '<code>Следующие события:</code>',
                         reply_markup=keyboard,
                         parse_mode='HTML',
                         disable_notification=True)

    if command == 'EVENT':
        date = data
        date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{date}')
        btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{date}')
        btn_03 = telebot.types.InlineKeyboardButton('Список отметившихся', callback_data=f'LIST_PLAYERS::{date}')
        btn_04 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn_01, btn_02)
        keyboard.row(btn_03)
        keyboard.row(btn_04)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>{date_str}</code>',
                         reply_markup=keyboard,
                         parse_mode='HTML',
                         disable_notification=True)

    if command == 'YES':
        date = data
        date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        db.add_decision(call.message.chat.id, date, command)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Отмечено посещение {date_str}: YES</code>',
                         reply_markup=telebot.types.ReplyKeyboardRemove(),
                         parse_mode='HTML',
                         disable_notification=True)
        player = db.player_by_telegram_id(call.message.chat.id)
        bot.send_message(config.ts_bot_group_id,
                         f"<code>{player[0]} {player[1]} отметил, что придет {date_str}</code>",
                         parse_mode='HTML',
                         disable_notification=True)

    if command == 'NO':
        date = data
        date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        db.add_decision(call.message.chat.id, date, command)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Отмечено посещение {date_str}: NO</code>',
                         reply_markup=telebot.types.ReplyKeyboardRemove(),
                         parse_mode='HTML',
                         disable_notification=True)
        player = db.player_by_telegram_id(call.message.chat.id)
        bot.send_message(config.ts_bot_group_id,
                         f"<code>{player[0]} {player[1]} отметил, что пропустит {date_str}</code>",
                         parse_mode='HTML',
                         disable_notification=True)

    if command == 'LIST_PLAYERS':
        date = data
        date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{date}')
        keyboard.row(btn_01)
        players = db.event_players(date)
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Список на {date_str}:\n\n{players}</code>',
                         reply_markup=keyboard,
                         parse_mode='HTML',
                         disable_notification=True)

    if command == 'CREATE_EVENT':
        pass

    if command == 'EXIT':
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
