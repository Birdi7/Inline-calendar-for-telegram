"""
    Class for creating inline calendar
    Designed as a module for following singleton pattern
    Works with PyTelegramBotApi https://github.com/eternnoir/pyTelegramBotAPI
"""
import datetime
import logging
import shelve
from calendar import monthrange

from telebot import types

import config


class WrongCallbackException(Exception):
    pass


class WrongChoiceCallbackException(Exception):
    pass


class NotInitedException(Exception):
    pass


# constants
_INLINE_CALENDAR_NAME = 'inline_calendar'
_MIN_DATE = '_MIN_DATE'
_MAX_DATE = '_MAX_DATE'
_CURRENT_DATE = '_CURRENT_DATE'
_MONTH_NAMES = '_MONTH_NAMES'
_DAYS_NAMES = '_DAYS_NAMES'
CALLBACK_WRONG_CHOICE = '{0}_wrong_choice'.format(_INLINE_CALENDAR_NAME)
CALLBACK_PREVIOUS_MONTH = '{0}_previous_month'.format(_INLINE_CALENDAR_NAME)
CALLBACK_NEXT_MONTH = '{0}_next_month'.format(_INLINE_CALENDAR_NAME)
CALLBACK_DAYS = ['{}_day_{}'.format(_INLINE_CALENDAR_NAME, i) for i in range(32)]

# user vars
_SHELVE_DB_NAME = _INLINE_CALENDAR_NAME+'_shelve_db'


def _db_read(chat_id, attr_name):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    try:
        with shelve.open(_SHELVE_DB_NAME) as db:
            t = db[chat_id]
            return t[attr_name]
    except KeyError:
        logging.log(level=logging.CRITICAL, msg='KeyError was raised while getting attribute {} for {}'
                                                .format(attr_name, chat_id))
        # idk why it happens sometimes. Didn't see any affection on work of calendar
        # if you know how to remove this try-except block, text me or collaborate


def _db_write(chat_id, attr_name, data):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    with shelve.open(_SHELVE_DB_NAME) as db:
        if chat_id not in db.keys():
            # first time creation of dictionary
            db[chat_id] = {}
        t = db[chat_id]
        t[attr_name] = data
        db[chat_id] = t


def _init_db(chat_id):
    chat_id = str(chat_id)
    with shelve.open(_SHELVE_DB_NAME) as db:
        db[chat_id] = {}


def _create_header(chat_id):
    result = []

    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)
    max_date = _db_read(chat_id, _MAX_DATE)
    if c_date > min_date:
        result.append(types.InlineKeyboardButton('<<', callback_data=CALLBACK_PREVIOUS_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))
    result.append(types.InlineKeyboardButton(_db_read(chat_id, _MONTH_NAMES)[c_date.month] + ' ' + str(c_date.year),
                                             callback_data=CALLBACK_WRONG_CHOICE))
    if c_date < max_date:
        result.append(types.InlineKeyboardButton('>>', callback_data=CALLBACK_NEXT_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))

    return result


def _create_weekdays_buttons(chat_id):
    d_names = _db_read(chat_id, _DAYS_NAMES)
    return [types.InlineKeyboardButton(d_names[i], callback_data=CALLBACK_WRONG_CHOICE) for i in range(0, 7)]


def _check_callback(callback):
    if callback == CALLBACK_WRONG_CHOICE:
        return True
    if callback == CALLBACK_NEXT_MONTH or callback == CALLBACK_PREVIOUS_MONTH:
        return True
    if callback in CALLBACK_DAYS:
        return True
    return False


def _inc_month(chat_id):
    c_date = _db_read(chat_id, _CURRENT_DATE)
    last_day = c_date.replace(day=monthrange(c_date.year, c_date.month)[1])
    _db_write(chat_id, _CURRENT_DATE, last_day + datetime.timedelta(days=1))


def _dec_month(chat_id):
    c_date = _db_read(chat_id, _CURRENT_DATE)
    first_day = c_date.replace(day=1)
    prev_month_lastday = first_day - datetime.timedelta(days=1)
    _db_write(chat_id, _CURRENT_DATE, prev_month_lastday.replace(day=1))


def init(chat_id, base_date, min_date, max_date,
         month_names=None,
         days_names=None,
         db_name=None):
    """
    Default language is English
    :param chat_id: chat id
    :param base_date: a datetime.date object.
    :param min_date: a datetime.date object.
    :param max_date: a datetime.date object.
    :param month_names: 12-element list for month names. If none, then English names will be used
    :param days_names: 7-element list fo2r month names. If none, then English names will be used
    :param db_name:
    """
    global _SHELVE_DB_NAME
    if db_name:
        _SHELVE_DB_NAME = db_name

    _init_db(chat_id)
    _db_write(chat_id, _CURRENT_DATE, datetime.date(year=base_date.year, month=base_date.month, day=base_date.day))
    _db_write(chat_id, _MIN_DATE, datetime.date(year=min_date.year, month=min_date.month, day=min_date.day))
    _db_write(chat_id, _MAX_DATE, datetime.date(year=max_date.year, month=max_date.month, day=max_date.day))

    m_names = ['-']
    if not month_names:
        m_names.extend(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'])
    else:
        m_names.extend(month_names)

    if len(m_names) != 12 + 1:
        raise Exception('Length of month names is not 12')

    _db_write(chat_id, _MONTH_NAMES, m_names)

    if not days_names:
        days_names = ['Mon', 'Tu', 'Wed', 'Th', 'Fr', 'Sat', 'Sun']

    if len(days_names) != 7:
        raise Exception('Length of days names is not 7')

    _db_write(chat_id, _DAYS_NAMES, days_names)


def reset(chat_id):
    chat_id = str(chat_id)
    _db_write(chat_id, _CURRENT_DATE, None)
    _db_write(chat_id, _MIN_DATE, None)
    _db_write(chat_id, _MAX_DATE, None)


def is_inited(chat_id):
    chat_id = str(chat_id)
    with shelve.open(_SHELVE_DB_NAME) as db:
        if chat_id not in db.keys():
            return False

    return _db_read(chat_id, _CURRENT_DATE) is not None


def get_keyboard(chat_id):
    if not is_inited(chat_id):
        raise NotInitedException('inline_calendar is not inited properly')
    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)

    kb = types.InlineKeyboardMarkup()
    kb.row(*_create_header(chat_id))
    kb.row(*_create_weekdays_buttons(chat_id))

    f_row = []
    mrange = monthrange(c_date.year, c_date.month)
    for i in range(mrange[0]):
        f_row.append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    rows = [f_row]
    for i in range(1, mrange[1] + 1):
        curr_date = datetime.date(day=i, month=c_date.month, year=c_date.year)
        if curr_date.weekday() == 0:
            rows.append([])
        if curr_date < min_date:
            rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))
        else:
            rows[-1].append(types.InlineKeyboardButton(text=i, callback_data=CALLBACK_DAYS[i]))

    curr_date = datetime.date(day=mrange[1], month=c_date.month, year=c_date.year)

    for i in range(curr_date.weekday() + 1, 7):
        rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    for r in rows:
        kb.row(*r)

    return kb


def is_inline_calendar_callbackquery(query):
    return _check_callback(query.data)


def handler_callback(chat_id, callback):
    """
    A method for handling callbacks
    :param chat_id: chat id of user
    :param callback: callback from telebot.types.CallbackQuery
    :return: datetime.date object if some date was picked else None
    """
    if not is_inited(chat_id):
        raise NotInitedException('inline_calendar is not inited properly')

    if not _check_callback(callback):
        raise WrongCallbackException('Wrong callback is given for handling')

    if callback == CALLBACK_WRONG_CHOICE:
        raise WrongChoiceCallbackException()

    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)
    max_date = _db_read(chat_id, _MAX_DATE)
    if callback == CALLBACK_PREVIOUS_MONTH and c_date > min_date:
        _dec_month(chat_id)
        return None
    if callback == CALLBACK_NEXT_MONTH and c_date < max_date:
        _inc_month(chat_id)
        return None

    if callback in CALLBACK_DAYS:
        return _db_read(chat_id, _CURRENT_DATE).replace(day=int(callback.split('_')[-1]))
