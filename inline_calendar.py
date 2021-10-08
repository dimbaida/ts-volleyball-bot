import datetime
import calendar
from keyboa import Keyboa, Button
from telebot import types


def keyboard_years(command: str) -> types.InlineKeyboardMarkup():
    """
    Assemble a keyboard with two buttons: current year and the following one
    :param command: the string command for callback_data
    :return: Keyboard with two years
    """
    keyboard = types.InlineKeyboardMarkup()
    year_curr = datetime.datetime.today().year
    btn_year_curr = types.InlineKeyboardButton(year_curr, callback_data=f'{command}>>MONTH::{year_curr}')
    btn_year_next = types.InlineKeyboardButton(year_curr + 1, callback_data=f'{command}>>MONTH::{year_curr + 1}')
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::")
    keyboard.row(btn_year_curr, btn_year_next)
    # keyboard.row(btn_back)
    return keyboard


def keyboard_months(command: str, year:str) -> types.InlineKeyboardMarkup():
    keyboard = types.InlineKeyboardMarkup()
    btn_jan = types.InlineKeyboardButton('JAN', callback_data=f"{command}>>DAY::{year}-1")
    btn_feb = types.InlineKeyboardButton('FEB', callback_data=f"{command}>>DAY::{year}-2")
    btn_mar = types.InlineKeyboardButton('MAR', callback_data=f"{command}>>DAY::{year}-3")
    btn_apr = types.InlineKeyboardButton('APR', callback_data=f"{command}>>DAY::{year}-4")
    btn_may = types.InlineKeyboardButton('MAY', callback_data=f"{command}>>DAY::{year}-5")
    btn_jun = types.InlineKeyboardButton('JUN', callback_data=f"{command}>>DAY::{year}-6")
    btn_jul = types.InlineKeyboardButton('JUL', callback_data=f"{command}>>DAY::{year}-7")
    btn_aug = types.InlineKeyboardButton('AUG', callback_data=f"{command}>>DAY::{year}-8")
    btn_sep = types.InlineKeyboardButton('SEP', callback_data=f"{command}>>DAY::{year}-9")
    btn_oct = types.InlineKeyboardButton('OCT', callback_data=f"{command}>>DAY::{year}-10")
    btn_nov = types.InlineKeyboardButton('NOV', callback_data=f"{command}>>DAY::{year}-11")
    btn_dec = types.InlineKeyboardButton('DEC', callback_data=f"{command}>>DAY::{year}-12")
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::")
    keyboard.row(btn_jan, btn_feb, btn_mar, btn_apr)
    keyboard.row(btn_may, btn_jun, btn_jul, btn_aug)
    keyboard.row(btn_sep, btn_oct, btn_nov, btn_dec)
    # keyboard.row(btn_back)
    return keyboard


def keyboard_days(command, year, month):
    num_days = calendar.monthrange(int(year), int(month))[1]
    days = list(range(1, num_days + 1))
    for i in range(32 - len(days)):
        days.append('.')
    days_btns = Keyboa(items=days, items_in_row=8, front_marker=f"{command}>>DATE::{year}-{month}-")
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::{year}")
    keyboard = days_btns.keyboard
    # keyboard.row(btn_back)
    return keyboard



