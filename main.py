import datetime
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import telebot
from telebot import types


bot = telebot.TeleBot()


import inline_calendar
@bot.message_handler(commands=['calendar'])
def calendar_test(msg: types.Message):
    inline_calendar.init_new(datetime.date.today(), datetime.date(year=2018, month=11, day=1), datetime.date(year=2019, month=4, day=1),
                             month_names=[str(i) for i in range(0, 12)],
                             days_names=['Mon', 'Tu', 'Wed', 'Th', 'Fr', 'Sat', 'Sun'])
    bot.send_message(msg.from_user.id, text='test', reply_markup=inline_calendar.get_keyboard())


@bot.callback_query_handler(func=inline_calendar.is_inline_calendar_callbackquery)
def calendar_callback_handler(q: types.CallbackQuery):
    try :
        r = inline_calendar.handler_callback(q.data)
        if r is None:
            bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id, reply_markup=inline_calendar.get_keyboard())
        else:
            logging.log(level=logging.DEBUG, msg='R is not None')

            bot.edit_message_text(text=r, chat_id=q.from_user.id, message_id=q.message.message_id, reply_markup=inline_calendar.get_keyboard())

    except inline_calendar.WrongChoiceCallbackException:
        logging.log(level=logging.DEBUG, msg='Wrong choice')

        if q.message.text != 'Wrong choice':
            bot.edit_message_text(text='Wrong choice', chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard())


if __name__ == '__main__':
    bot.polling(none_stop=True)
