import telebot
import config
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import common_constants as cc
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
    btn_02 = telebot.types.InlineKeyboardButton(f"Управление событиями", callback_data=f'MANAGE::')
    btn_03 = telebot.types.InlineKeyboardButton(f"Выход", callback_data=f'EXIT::')
    keyboard.row(btn_01)
    if db.check_admin(message.chat.id):
        keyboard.row(btn_02)
    keyboard.row(btn_03)
    bot.send_message(message.chat.id,
                     '<code>Следующие события:</code>',
                     reply_markup=keyboard,
                     parse_mode='HTML',
                     disable_notification=True)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    try:
        command, data = call.data.split('::')

        # COMMON SECTION

        if command == 'LIST_EVENTS':
            keyboard = telebot.types.InlineKeyboardMarkup()
            for event in db.upcoming_events():
                event_date = event[0]
                event_type = event[1]
                event_date_str = event_date.strftime('%d.%m.%Y')
                btn = telebot.types.InlineKeyboardButton(f"{cc.ICONS[event[1]]}  {event_date_str}",
                                                         callback_data=f'EVENT::{event_date}:{event_type}')
                keyboard.row(btn)
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_exit)
            bot.edit_message_text('<code>Следующие события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'EVENT':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{data}')
            btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{data}')
            btn_03 = telebot.types.InlineKeyboardButton('Список отметившихся', callback_data=f'LIST_PLAYERS::{data}')
            btn_04 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_03)
            keyboard.row(btn_04)
            bot.edit_message_text(f'{cc.ICONS[event_type]}  <code>{event_date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'YES':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            decision = db.check_attendance(call.message.chat.id, event_date)
            if decision == 'YES':
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{data}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Ты уже ранее был отмечен на {cc.ICONS[event_type]}  {event_date_str}: {cc.ICONS['YES']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)

            else:
                db.add_decision(call.message.chat.id, event_date, 'YES')
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Отмечено посещение {cc.ICONS[event_type]}  {event_date_str}: {cc.ICONS['YES']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
                player = db.player_by_telegram_id(call.message.chat.id)
                bot.send_message(config.ts_bot_group_id,
                                 f"<code>{player[0]} {player[1]} отметил, что придет {cc.ICONS[event_type]}  {event_date_str}  {cc.ICONS['YES']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'NO':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            decision = db.check_attendance(call.message.chat.id, event_date)
            if decision == 'NO':
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{data}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Ты уже ранее был отмечен на {cc.ICONS[event_type]}  {event_date_str}  {cc.ICONS['NO']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
            else:
                db.add_decision(call.message.chat.id, event_date, 'NO')
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Отмечено посещение {cc.ICONS[event_type]}  {event_date_str}: {cc.ICONS['NO']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
                player = db.player_by_telegram_id(call.message.chat.id)
                bot.send_message(config.ts_bot_group_id,
                                 f"<code>{player[0]} {player[1]} отметил, что пропустит {cc.ICONS[event_type]}  {event_date_str}  {cc.ICONS['NO']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'LIST_PLAYERS':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{data}')
            keyboard.row(btn_01)
            players = db.event_players(event_date)
            bot.edit_message_text(f'<code>Список на {event_date_str}:\n\n{players}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        # MANAGE SECTION

        if command == 'MANAGE':
            keyboard = telebot.types.InlineKeyboardMarkup()
            for event in db.upcoming_events():
                date_str = event[0].strftime('%d.%m.%Y')
                date = event[0]
                event_type = event[1]
                btn = telebot.types.InlineKeyboardButton(f"Изменить {cc.ICONS[event_type]}  {date_str}", callback_data=f'MANAGE_EVENT::{date}:{event_type}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Создать", callback_data=f'MANAGE_CREATE::')
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_new)
            keyboard.row(btn_exit)
            bot.edit_message_text('<code>Следующие события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE_EVENT':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton(f"Удалить", callback_data=f'MANAGE_EVENT>>DELETE::{data}')
            btn_02 = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'MANAGE::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            bot.edit_message_text(f'{cc.ICONS[event_type]}  <code>{event_date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE_EVENT>>DELETE':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_empty = telebot.types.InlineKeyboardButton(' ', callback_data='::')
            btn_01 = telebot.types.InlineKeyboardButton('Подтвердить',
                                                        callback_data=f'MANAGE_EVENT>>DELETE>>CONFIRMED::{data}')
            btn_02 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            keyboard.row(btn_empty)
            keyboard.row(btn_empty, btn_01, btn_empty)
            keyboard.row(btn_empty)
            keyboard.row(btn_02)
            bot.edit_message_text(f'<code>УВЕРЕН? Все данные о событии будут стерты! {cc.ICONS[event_type]}  {event_date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE_EVENT>>DELETE>>CONFIRMED':
            event_date, event_type = data.split(':')
            event_date_str = datetime.datetime.strptime(event_date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            db.delete_event(event_date, telegram_id=call.message.chat.id)
            bot.edit_message_text(f'<code>Событие {cc.ICONS[event_type]}  {event_date_str} удалено</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE_CREATE':
            calendar, step = DetailedTelegramCalendar().build()
            bot.edit_message_text(f'Select {LSTEP[step]}',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=calendar)

        if command == 'MANAGE_CREATE>>TYPE':
            date, event_type = data.split(':')
            date_str = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            db.create_event(date, event_type, telegram_id=call.message.chat.id)
            bot.edit_message_text(f'<code>Событие создано: {cc.ICONS[event_type]} {date_str}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'EXIT':
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)

    except ValueError:  # This is due to telegram_bot_calendar can't handle custom callbacks

        # CALENDAR SECTION

        date, key, step = DetailedTelegramCalendar().process(call.data)

        if not date and key:
            bot.edit_message_text(f"Select {LSTEP[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif date:
            date_str = date.strftime("%d.%m.%Y")
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Тренировка', callback_data=f'MANAGE_CREATE>>TYPE::{date}:train')
            btn_02 = telebot.types.InlineKeyboardButton('Игра', callback_data=f'MANAGE_CREATE>>TYPE::{date}:game')
            keyboard.row(btn_01, btn_02)
            bot.edit_message_text(f"<code>Выбери тип события на {date_str}</code>",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=keyboard,
                                  parse_mode='HTML')


if __name__ == '__main__':
    bot.polling(none_stop=True)
