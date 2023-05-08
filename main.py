import logging
import telebot
import inline_calendar
import db_commands as db
import datetime
from common_constants import *

logging.basicConfig(filename='.log',
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s >> %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['test'], chat_types=['private'])
def test(message):
    """
    Bot command for test purposes. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id into 'developers' var in 'common_constants.py'
    """
    if message.from_user.id == int(MASTER_TG_ID):
        pass


@bot.message_handler(commands=['get_id'], chat_types=['private'])
def get_id(message):
    logging.info(f'id request from {message.from_user.id}')
    bot.send_message(message.from_user.id,
                     f'<code>твій telegram ID: {message.from_user.id}</code>',
                     reply_markup=telebot.types.ReplyKeyboardRemove(),
                     parse_mode='HTML',
                     disable_notification=True)


@bot.message_handler(commands=['start'], chat_types=['private'])
def start(message):
    if db.check_player(message.from_user.id):
        player = db.get_player_by_telegram_id(message.from_user.id)
        logging.info(f"[{player.id}]{player.lastname} {player.name} > '/start'")
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"{event.icon}  {event.date_formatted}",
                                                     callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn)
        btn_exit = telebot.types.InlineKeyboardButton(f"Вийти", callback_data=f'EXIT::')
        keyboard.row(btn_exit)
        bot.send_message(message.from_user.id,
                         '<code>Наступні події:</code>',
                         parse_mode='HTML',
                         reply_markup=keyboard)

    else:
        logging.warning(f"[{message.from_user.id}] unknown user '/start'")
        bot.send_message(message.from_user.id,
                         '<code>Тебе немає в списку гравців. Напиши адміністратору:</code> @dimbaida.',
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(commands=['manage'], chat_types=['private'])
def manage(message):
    if db.check_player(message.from_user.id):
        player = db.get_player_by_telegram_id(message.from_user.id)
        if player.admin:
            logging.info(f"[{player.id}]{player.lastname} {player.name} > '/manage'")
            keyboard = telebot.types.InlineKeyboardMarkup()
            for event in db.upcoming_events():
                btn = telebot.types.InlineKeyboardButton(f"Змінити {event.icon} {event.date_formatted}",
                                                         callback_data=f'MANAGE>>EVENT::{event.id}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Створити", callback_data=f'MANAGE>>CREATE::')
            btn_exit = telebot.types.InlineKeyboardButton(f"Вийти", callback_data=f'EXIT::')
            keyboard.row(btn_new)
            keyboard.row(btn_exit)
            bot.send_message(message.from_user.id,
                             '<code>Наступні події:</code>',
                             parse_mode='HTML',
                             reply_markup=keyboard)

        else:
            logging.warning(f"[{player.id}]{player.lastname} {player.name} '/manage' - not an admin!")
            bot.send_message(message.from_user.id,
                             '<code>Ця секція доступна тільки користувачам з правами адміністратора.</code>',
                             parse_mode='HTML',
                             disable_notification=True)

    else:
        logging.warning(f"[{message.from_user.id}] unknown user '/manage'")
        bot.send_message(message.from_user.id,
                         '<code>Тебе немає в списку гравців. Напиши адміністратору:</code> @dimbaida.',
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(content_types=['text'], chat_types=['private'])
def text(message):
    if db.check_player(message.from_user.id):
        player = db.get_player_by_telegram_id(message.from_user.id)
        cache = player.read_cache()
        if cache:
            menu_state, data = cache.split('::')
            if menu_state == 'INPUT_GUEST':
                event = db.get_event(data)
                guest_name = message.text
                event.add_guest(guest_name, player)
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
                keyboard.row(btn)
                bot.send_message(message.chat.id,
                                 f"<code>Гостьовий гравець — {guest_name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                                 parse_mode='HTML',
                                 reply_markup=keyboard)
                bot.send_message(TS_GROUP_ID,
                                 f"<code>{player.lastname} {player.name} додав гостя {guest_name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                                 parse_mode='HTML')
                player.purge_cache()

            if menu_state == 'EDIT_GUEST':
                guest = db.get_guest(data)
                guest_name = message.text
                guest.change_name(guest_name)
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
                keyboard.row(btn)
                bot.send_message(message.chat.id,
                                 f"<code>Нове ім'я гостя — {guest_name}</code>",
                                 parse_mode='HTML',
                                 reply_markup=keyboard)
                player.purge_cache()

            if menu_state == 'INPUT_NOTE':
                event = db.get_event(data)
                note = message.text
                event.update_note(note, player)
                keyboard = telebot.types.InlineKeyboardMarkup()
                btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
                keyboard.row(btn)
                bot.send_message(message.chat.id,
                                 f'<code>Додана примітка {event.icon} {event.date_formatted}:\n"{note}"</code>',
                                 parse_mode='HTML',
                                 reply_markup=keyboard)
                player.purge_cache()
    else:
        print(f'[Error] Request from [{message.from_user.id}] — unknown player')
        bot.send_message(message.from_user.id,
                         '<code>Тебе немає в списку гравців. Напиши адміністратору:</code> @dimbaida.',
                         parse_mode='HTML',
                         disable_notification=True)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    player = db.get_player_by_telegram_id(call.message.chat.id)
    player.purge_cache()
    logging.info(f'[{player.id}]{player.lastname} {player.name} > {call.data}')
    command, data = call.data.split('::')

    # COMMON SECTION

    if command == 'LIST_EVENTS':
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"{event.icon} {event.date_formatted}",
                                                     callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn)
        btn_exit = telebot.types.InlineKeyboardButton(f"Вийти", callback_data=f'EXIT::')
        keyboard.row(btn_exit)
        bot.edit_message_text('<code>Наступні події:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT':
        event_id, item = data.split(':')
        event = db.get_event(event_id)
        keyboard = telebot.types.InlineKeyboardMarkup()

        btn_01 = telebot.types.InlineKeyboardButton('ТАК', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:yes')
        btn_02 = telebot.types.InlineKeyboardButton('НІ', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:no')
        btn_03 = telebot.types.InlineKeyboardButton('Гості', callback_data=f'LIST_EVENTS>>EVENT>>GUESTS::{event.id}')
        btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')

        if event.type == 'train':
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_03)
        if event.type == 'game' and player.team:
            keyboard.row(btn_01, btn_02)
        keyboard.row(btn_back)

        if item == 'yes':
            att = player.check_attendance(event.id)
            if att is False or att is None:
                player.set_decision(event.id, True)
                bot.send_message(TS_GROUP_ID,
                                 f"<code>{player.lastname} {player.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted} {ICONS['yes']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if item == 'no':
            att = player.check_attendance(event.id)
            if att is True or att is None:
                player.set_decision(event.id, False)
                bot.send_message(TS_GROUP_ID,
                                 f"<code>{player.lastname} {player.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted} {ICONS['no']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        event_text = f'{event.icon} {event.date_formatted}:'
        if event.note:
            event_text += f"\n{event.note}"
        event_text += f'\n\n{event.players_formatted()}'

        try:
            bot.edit_message_text(f'<code>{event_text}</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code != 400:
                logging.critical(e)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS':
        event = db.get_event(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        guests = event.guests()
        if guests:
            for guest in event.guests():
                btn = telebot.types.InlineKeyboardButton(f"[Гість] {guest.name}", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST::{event.id}:{guest.id}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Додати", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST::{event.id}')
            btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn_new)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>Гості на {event.icon} {event.date_formatted}:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)
        else:
            btn_new = telebot.types.InlineKeyboardButton(f"Додати", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST::{event.id}')
            btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn_new)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>{event.icon} {event.date_formatted}\nСписок гостей порожній</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST':
        event_id, guest_id = data.split(':')
        event = db.get_event(event_id)
        guest = db.get_guest(guest_id)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton(f"Змінити ім'я", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>EDIT::{guest.id}')
        btn_02 = telebot.types.InlineKeyboardButton(f"Видалити", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>DELETE::{guest.id}')
        btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS::{event.id}')
        keyboard.row(btn_01, btn_02)
        keyboard.row(btn_back)
        bot.edit_message_text(f"<code>[Гість] {guest.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}:</code>",
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>EDIT':
        guest = db.get_guest(data)
        player.write_cache(f'EDIT_GUEST::{guest.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f"<code>Введи нове ім'я гостя</code>",
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>DELETE':
        guest = db.get_guest(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn)
        if guest.added_by == call.message.chat.id or player.admin:
            name = guest.name
            event = db.get_event(guest.event_id)
            guest.delete()
            bot.edit_message_text(
                f"<code>Гостя видалено</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)
            bot.send_message(TS_GROUP_ID,
                             f"<code>{player.lastname} {player.name} видалив гостя {name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                             parse_mode='HTML')
        else:
            bot.edit_message_text(
                f"<code>Гостя може видалити тільки гравець, що його запросив, або адміністратор</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST':
        event = db.get_event(data)
        player.write_cache(f'INPUT_GUEST::{event.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f"<code>Введи ім'я гостя для {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    # MANAGE SECTION

    if command == 'MANAGE':
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"Змінити {event.icon} {event.date_formatted}", callback_data=f'MANAGE>>EVENT::{event.id}')
            keyboard.row(btn)
        btn_new = telebot.types.InlineKeyboardButton(f"Створити", callback_data=f'MANAGE>>CREATE::')
        btn_exit = telebot.types.InlineKeyboardButton(f"Вийти", callback_data=f'EXIT::')
        keyboard.row(btn_new)
        keyboard.row(btn_exit)
        bot.edit_message_text('<code>Наступні події:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>EVENT':
        event = db.get_event(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton(f"Змінити тип", callback_data=f'MANAGE>>EVENT>>SWITCH_TYPE::{event.id}')
        btn_02 = telebot.types.InlineKeyboardButton(f"Додати примітку", callback_data=f'MANAGE>>EVENT>>INPUT_NOTE::{event.id}')
        btn_03 = telebot.types.InlineKeyboardButton(f"Видалити", callback_data=f'MANAGE>>EVENT>>DELETE::{event.id}')
        btn_04 = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'MANAGE::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        keyboard.row(btn_03)
        keyboard.row(btn_04)
        bot.edit_message_text(f'<code>{event.icon} {event.date_formatted}</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>EVENT>>SWITCH_TYPE':
        event = db.get_event(data)
        old_icon = event.icon
        event.switch_type()
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE>>EVENT::{event.id}')
        keyboard.row(btn)
        bot.edit_message_text(f"<code>Тип події змінено {old_icon} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)
        bot.send_message(TS_GROUP_ID,
                         f"<code>{player.name} {player.lastname} змінив {old_icon} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML')

    if command == 'MANAGE>>EVENT>>INPUT_NOTE':
        event = db.get_event(data)
        player.write_cache(f'INPUT_NOTE::{event.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Введи примітку для {event.icon} {event.date_formatted}</code>',
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    if command == 'MANAGE>>EVENT>>DELETE':
        event = db.get_event(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        if event.date >= datetime.date.today():
            btn_01 = telebot.types.InlineKeyboardButton('Так', callback_data=f'MANAGE>>EVENT>>DELETE>>CONFIRMED::{event.id}')
            btn_02 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE>>EVENT::{event.id}')
            keyboard.row(btn_01, btn_02)
            bot.edit_message_text(
                f'<code>ВПЕВНЕНИЙ? Всі дані про подію будуть видалені! {event.icon} {event.date_formatted}</code>',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)
        else:
            btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE>>EVENT::{event.id}')
            keyboard.row(btn)
            bot.edit_message_text(
                f'<code>Неможна видалити подію, яка відбулася</code>',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)

    if command == 'MANAGE>>EVENT>>DELETE>>CONFIRMED':
        event = db.get_event(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
        btn_02 = telebot.types.InlineKeyboardButton('Вийти', callback_data=f'EXIT::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        event.delete()
        logging.info(f"[{event.id}] {event.date_formatted} was deleted by [{player.id}]{player.lastname} {player.name}")
        bot.edit_message_text(f'<code>Подія {event.icon} {event.date_formatted} видалена</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>CREATE':
        bot.edit_message_text(f'<code>Рік:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_years(command))

    if command == 'MANAGE>>CREATE>>MONTH':
        year = data
        bot.edit_message_text(f'<code>Місяць:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_months(command, year))

    if command == 'MANAGE>>CREATE>>MONTH>>DAY':
        year, month = data.split('-')
        bot.edit_message_text(f'<code>День:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_days(command, year, month))

    if command == 'MANAGE>>CREATE>>MONTH>>DAY>>DATE':
        date = data
        year, month, day = date.split('-')
        if day.isdigit() and datetime.datetime.strptime(date, '%Y-%m-%d') >= datetime.datetime.today():
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Тренування', callback_data=f'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE::{date}:train')
            btn_02 = telebot.types.InlineKeyboardButton('Гра', callback_data=f'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE::{date}:game')
            btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data="MANAGE::")
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>Вибери тип події:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data="MANAGE::")
            keyboard.add(btn_back)
            bot.edit_message_text(f'<code>Неправильна дата</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

    if command == 'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE':
        date, event_type = data.split(':')
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
        btn_02 = telebot.types.InlineKeyboardButton('Вийти', callback_data=f'EXIT::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        event = db.create_event(date, event_type, player.id)
        logging.info(f"[{event.id}]{event.date_formatted} was created by [{player.id}]{player.lastname} {player.name}")
        bot.edit_message_text(f'<code>Подію створено: {event.icon} {event.date_formatted}</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)
        bot.send_message(TS_GROUP_ID,
                         f"<code>{player.lastname} {player.name} створив {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML')

    # GENERAL

    if command == 'EXIT':
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
