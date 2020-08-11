import os
from dotenv import load_dotenv
import logging
import random
import re
import json

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

from redis_handler import RedisHandler

logger = logging.getLogger(__name__)

NEW＿QUESTION, ANSWER = range(2)

custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
markup = ReplyKeyboardMarkup(custom_keyboard)

redis_base = RedisHandler()


def start(update, context):
    user = f'user_tg_{update.effective_chat.id}'
    redis_base.initiate_score(user)

    update.message.reply_text(
        'Привет! Я бот для викторин\n'
        'Для начала нажми на "Новый вопрос"\n'
        'Для завершения игры /cancel',
        reply_markup=markup)
    
    return NEW_QUESTION


def get_new_question(update, context):
    redis_base.initiate_new_quiz_block()
    print(redis_base.answer)
    update.message.reply_text(text=redis_base.question, reply_markup=markup)

    return ANSWER


def get_answer(update, context):
    message = update.message.text

    if message == redis_base.answer:
        redis_base.score += 1
        redis_base.set_score()
        update.message.reply_text(
            'Правильно!\n'
            'Для продолжения нажми на "Новый вопрос"',
            reply_markup=markup)
        
        return NEW_QUESTION

    elif re.search(message, redis_base.offset):
        redis_base.score += 1
        redis_base.set_score()
        update.message.reply_text(
            'Почти в точку! Правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(redis_base.answer),
            reply_markup=markup)

        return NEW_QUESTION

    else:
        update.message.reply_text(
            'Неверно, попробуй еще',
            reply_markup=markup)
        
        return ANSWER


def give_up(update, context):
    redis_base.set_score()
    update.message.reply_text(
            'Бывает, правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(redis_base.answer),
            reply_markup=markup)
    
    return NEW_QUESTION


def get_score(update, context):
    update.message.reply_text(
            'У вас {} очков\n'
            'Для продолжения нажми на "Новый вопрос"\n'
            'Для завершения игры /cancel'.format(redis_base.score),
            reply_markup=markup)
    
    return NEW_QUESTION


def cancel(update, context):
    redis_base.set_score()
    update.message.reply_text('Пока, увидимся в следующий раз.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    
    updater = Updater(tg_token, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            NEW＿QUESTION: [MessageHandler(Filters.regex(r'^Новый вопрос$'), get_new_question),
            
                           MessageHandler(Filters.regex(r'^Мой счет$'), get_score)],

            ANSWER: [MessageHandler(Filters.regex(r'^Сдаться$'), give_up),
            
                     MessageHandler(Filters.text, get_answer),]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    
    updater.start_polling()
    
    updater.idle()


if __name__ == "__main__":
    main()
