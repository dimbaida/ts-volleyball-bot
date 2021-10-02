import telebot
import config
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from common_constants import ICONS
import scheduler
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
        telegram_ids = scheduler.send_event_reminder()
        bot.send_message(message.from_user.id,
                         f'<code>Напоминание отправлено:\n{telegram_ids}</code>',
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
    player = db.get_player_by_telegram_id(message.chat.id)
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton(f"Список событий", callback_data=f'LIST_EVENTS::')
    btn_02 = telebot.types.InlineKeyboardButton(f"Управление событиями", callback_data=f'MANAGE::')
    btn_03 = telebot.types.InlineKeyboardButton(f"Выход", callback_data=f'EXIT::')
    keyboard.row(btn_01)
    if player.admin:
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
                btn = telebot.types.InlineKeyboardButton(f"{event.icon}  {event.date_formatted}",
                                                         callback_data=f'EVENT::{event.id}')
                keyboard.row(btn)
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_exit)
            bot.edit_message_text('<code>Следующие события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'EVENT':
            event = db.get_event_by_id(data)
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{event.id}')
            btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{event.id}')
            btn_03 = telebot.types.InlineKeyboardButton('Список отметившихся', callback_data=f'LIST_PLAYERS::{event.id}')
            btn_04 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_03)
            keyboard.row(btn_04)
            bot.edit_message_text(f'{event.icon}  <code>{event.date_formatted}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'YES':
            event = db.get_event_by_id(data)
            player = db.get_player_by_telegram_id(call.message.chat.id)
            if player.check_attendance(event.date):
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{event.id}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Ты уже ранее был отмечен на {event.icon}  {event.date_formatted}  {ICONS['yes']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)

            else:
                player.add_decision(event.date, 'YES')
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Отмечено посещение {ICONS['right_arrow']} {event.icon}  {event.date_formatted}  {ICONS['YES']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
                bot.send_message(config.telegram_group_id,
                                 f"<code>{player.name} {player.lastname} {ICONS['RIGHT_ARROW']} {event.icon}  {event.date_formatted}  {ICONS['YES']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'NO':
            event = db.get_event_by_id(data)
            player = db.get_player_by_telegram_id(call.message.chat.id)
            att = player.check_attendance(event.date)
            if not att and att is not None:
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{data}')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Ты уже ранее был отмечен на {event.icon}  {event.date_formatted}  {ICONS['NO']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
            else:
                player.add_decision(event.date, 'NO')
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn_01 = telebot.types.InlineKeyboardButton('Вернуться к списку событий', callback_data=f'LIST_EVENTS::')
                btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
                keyboard.row(btn_01)
                keyboard.row(btn_02)
                bot.edit_message_text(f"<code>Отмечено посещение {ICONS['RIGHT_ARROW']} {event.icon}  {event.date_formatted}: {ICONS['NO']}</code>",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      parse_mode='HTML',
                                      reply_markup=keyboard)
                bot.send_message(config.telegram_group_id,
                                 f"<code>{player.name} {player.lastname} {ICONS['RIGHT_ARROW']} {event.icon}  {event.date_formatted}  {ICONS['NO']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if command == 'LIST_PLAYERS':
            event = db.get_event_by_id(data)
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'EVENT::{event.id}')
            keyboard.row(btn_01)
            bot.edit_message_text(f'<code>{event.icon}  {event.date_formatted}:\n\n{event.players_attendance_list()}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        # MANAGE SECTION

        if command == 'MANAGE':
            keyboard = telebot.types.InlineKeyboardMarkup()
            for event in db.upcoming_events():
                btn = telebot.types.InlineKeyboardButton(f"Изменить {event.icon}  {event.date_formatted}", callback_data=f'MANAGE>>EVENT::{event.id}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Создать", callback_data=f'MANAGE>>CREATE::')
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_new)
            keyboard.row(btn_exit)
            bot.edit_message_text('<code>Следующие события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE>>EVENT':
            event = db.get_event_by_id(data)
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton(f"Удалить", callback_data=f'MANAGE>>EVENT>>DELETE::{event.id}')
            btn_02 = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'MANAGE::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            bot.edit_message_text(f'<code>{event.icon}  {event.date_formatted}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE>>EVENT>>DELETE':
            event = db.get_event_by_id(data)
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_empty = telebot.types.InlineKeyboardButton(' ', callback_data='::')
            btn_01 = telebot.types.InlineKeyboardButton('Подтвердить',
                                                        callback_data=f'MANAGE>>EVENT>>DELETE>>CONFIRMED::{event.id}')
            btn_02 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            keyboard.row(btn_empty)
            keyboard.row(btn_empty, btn_01, btn_empty)
            keyboard.row(btn_empty)
            keyboard.row(btn_02)
            bot.edit_message_text(f'<code>УВЕРЕН? Все данные о событии будут стерты! {event.icon}  {event.date_formatted}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE>>EVENT>>DELETE>>CONFIRMED':
            event = db.get_event_by_id(data)
            player = db.get_player_by_telegram_id(call.message.chat.id)
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            event.delete()
            print(f'[INFO] Event {event.date} was deleted by {player.name} {player.lastname}')
            bot.edit_message_text(f'<code>Событие {event.icon}  {event.date_formatted} удалено</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

        if command == 'MANAGE>>CREATE':
            calendar, step = DetailedTelegramCalendar().build()
            bot.edit_message_text(f'Select {LSTEP[step]}',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=calendar)

        if command == 'MANAGE>>CREATE>>TYPE':
            date, event_type = data.split(':')
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
            btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
            keyboard.row(btn_01)
            keyboard.row(btn_02)
            event = db.create_event(date, event_type)
            player = db.get_player_by_telegram_id(call.message.chat.id)
            print(f'[INFO] Event {event.date} was created by {player.name} {player.lastname}')
            bot.edit_message_text(f'<code>Событие создано: {event.icon}  {event.date_formatted}</code>',
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
            btn_01 = telebot.types.InlineKeyboardButton('Тренировка', callback_data=f'MANAGE>>CREATE>>TYPE::{date}:train')
            btn_02 = telebot.types.InlineKeyboardButton('Игра', callback_data=f'MANAGE>>CREATE>>TYPE::{date}:game')
            keyboard.row(btn_01, btn_02)
            bot.edit_message_text(f"<code>Выбери тип события на {date_str}</code>",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=keyboard,
                                  parse_mode='HTML')


if __name__ == '__main__':
    bot.polling(none_stop=True)
