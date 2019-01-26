import datetime
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import telebot
from telebot import types
import inline_calendar


YOUR_TOKEN = ''
bot = telebot.TeleBot(token=YOUR_TOKEN)


@bot.message_handler(commands=['calendar'])
def calendar_test(msg: types.Message):
    inline_calendar.init(msg.from_user.id,
                         datetime.date.today(),
                         datetime.date(year=2018, month=11, day=1),
                         datetime.date(year=2019, month=4, day=1))
    bot.send_message(msg.from_user.id, text='test', reply_markup=inline_calendar.get_keyboard(msg.from_user.id))


@bot.callback_query_handler(func=inline_calendar.is_inline_calendar_callbackquery)
def calendar_callback_handler(q: types.CallbackQuery):
    try:
        return_data = inline_calendar.handler_callback(q.from_user.id, q.data)
        if return_data is None:
            bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                          reply_markup=inline_calendar.get_keyboard(q.from_user.id))
        else:
            picked_data = return_data
            bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard(q.from_user.id))

    except inline_calendar.WrongChoiceCallbackException:
        bot.edit_message_text(text='Wrong choice', chat_id=q.from_user.id, message_id=q.message.message_id,
                              reply_markup=inline_calendar.get_keyboard(q.from_user.id))
    bot.answer_callback_query(q.id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
