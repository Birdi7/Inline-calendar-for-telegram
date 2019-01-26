"""
    Class for creating inline calendar
    Designed as a module for following singleton pattern
    Works with PyTelegramBotApi https://github.com/eternnoir/pyTelegramBotAPI
"""
from telebot import types
import datetime
from calendar import monthrange
import shelve


# constants
_INLINE_CALENDAR_NAME = 'inline_calendar'
CALLBACK_WRONG_CHOICE = '{0}_wrong_choice'.format(_INLINE_CALENDAR_NAME)
CALLBACK_PREVIOUS_MONTH = '{0}_previous_month'.format(_INLINE_CALENDAR_NAME)
CALLBACK_NEXT_MONTH = '{0}_next_month'.format(_INLINE_CALENDAR_NAME)
CALLBACK_DAYS = ['{}_day_{}'.format(_INLINE_CALENDAR_NAME, i) for i in range(32)]

#user vars
_SHELVE_DB_NAME = ''


def _db_read_(chat_id, attr_name):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    with shelve.open(_SHELVE_DB_NAME) as db:
        return db[chat_id][attr_name]


def _db_write_(chat_id, attr_name, data):
    chat_id = str(chat_id)
    attr_name = str(attr_name)
    with shelve.open(_SHELVE_DB_NAME) as db:
        db[chat_id][attr_name] = data


def _create_header():
    result = []
    if _current_date > _min_date:
        result.append(types.InlineKeyboardButton('<<', callback_data=CALLBACK_PREVIOUS_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))
    result.append(types.InlineKeyboardButton(_MONTH_NAMES[_current_date.month] + ' ' + str(_current_date.year),
                                             callback_data=CALLBACK_WRONG_CHOICE))
    if _current_date < _max_date:
        result.append(types.InlineKeyboardButton('>>', callback_data=CALLBACK_NEXT_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))

    return result


def _create_weekdays_buttons():
    return [types.InlineKeyboardButton(_DAYS_NAMES[i], callback_data=CALLBACK_WRONG_CHOICE) for i in range(0, 7)]


def _check_callback(callback):
    if callback == CALLBACK_WRONG_CHOICE:
        return True
    if callback == CALLBACK_NEXT_MONTH or callback == CALLBACK_PREVIOUS_MONTH:
        return True
    if callback in CALLBACK_DAYS:
        return True
    return False


def _inc_month():
    global _current_date
    last_day = _current_date.replace(day=monthrange(_current_date.year, _current_date.month)[1])
    _current_date = last_day+datetime.timedelta(days=1)


def _dec_month():
    global _current_date
    first_day = _current_date.replace(day=1)
    prev_month_lastday = first_day - datetime.timedelta(days=1)
    _current_date = prev_month_lastday.replace(day=1)


def init(base_date, min_date, max_date, month_names=None, days_names=None):
    """
    Default language is English

    :param base_date: a datetime.date object. Parameter 'day' will not be used
    :param min_date: a datetime.date object. Parameter 'day' will not be used
    :param max_date: a datetime.date object. Parameter 'day' will not be used
    :param month_names: 12-element list for month names. If none, then English names will be used
    :param days_names: 7-element list for month names. If none, then English names will be used
    """
    global _current_date, _min_date, _max_date, _MONTH_NAMES, _DAYS_NAMES
    _current_date = base_date
    _min_date = min_date
    _max_date = max_date

    _MONTH_NAMES = ['-']
    if not month_names:
        _MONTH_NAMES.extend(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'])
    else:
        _MONTH_NAMES.extend(month_names)

    if not days_names:
        _DAYS_NAMES = ['Mon', 'Tu', 'Wed', 'Th', 'Fr', 'Sat', 'Sun']
    else:
        _DAYS_NAMES = days_names

    _current_date = _current_date.replace(day=1)
    _max_date = _max_date.replace(day=1)
    _min_date = _min_date.replace(day=1)

    if len(_MONTH_NAMES) != 12+1:
        raise Exception('Length of month names is not 12')
    if len(_DAYS_NAMES) != 7:
        raise Exception('Length of days names is not 7')


def reset():
    global _current_date, _min_date, _max_date
    _current_date = _min_date = _max_date = None


def is_inited():
    global _current_date
    return _current_date is not None


def get_keyboard():
    if not is_inited():
        raise Exception('inline_calendar is not inited properly')

    kb = types.InlineKeyboardMarkup()
    kb.row(*_create_header())
    kb.row(*_create_weekdays_buttons())

    f_row = []
    mrange = monthrange(_current_date.year, _current_date.month)
    for i in range(mrange[0]):
        f_row.append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    rows = [f_row]
    for i in range(1, mrange[1] + 1):
        cdate = datetime.date(day=i, month=_current_date.month, year=_current_date.year)
        if cdate.weekday() == 0:
            rows.append([])

        rows[-1].append(types.InlineKeyboardButton(text=i, callback_data=CALLBACK_DAYS[i]))

    cdate = datetime.date(day=mrange[1], month=_current_date.month, year=_current_date.year)

    for i in range(cdate.weekday() + 1, 7):
        rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    for r in rows:
        kb.row(*r)

    return kb


def is_inline_calendar_callbackquery(query):
    if not is_inited():
        raise Exception('inline_calendar is not inited properly')
    return _check_callback(query.data)


class WrongCallbackException(Exception):
    pass


class WrongChoiceCallbackException(Exception):
    pass


def handler_callback(callback):
    """
    A method for handling callbacks
    :param callback: callback from telebot.types.CallbackQuery
    :return: datetime.date object if some date was picked else None
    """
    if not is_inited():
        raise Exception('inline_calendar is not inited properly')

    if not _check_callback(callback):
        raise WrongCallbackException('Wrong callback is given for handling')

    if callback == CALLBACK_WRONG_CHOICE:
        raise WrongChoiceCallbackException()

    if callback == CALLBACK_PREVIOUS_MONTH:
        _dec_month()
    if callback == CALLBACK_NEXT_MONTH:
        _inc_month()

    if callback in CALLBACK_DAYS:
        return _current_date.replace(day=int(callback.split('_')[-1]))
