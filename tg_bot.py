import os
from dotenv import load_dotenv
import logging
import random
import re

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import redis

from quiz_dict import get_quiz_for_bot
from redis_connection import get_database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

NEW＿QUESTION, ANSWER = range(2)

custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
markup = ReplyKeyboardMarkup(custom_keyboard)

redis_base = get_database()


def start(update, context):
    update.message.reply_text(
        'Привет! Я бот для викторин\n'
        'Для начала нажми на "Новый вопрос"\n'
        'Для завершения игры /cancel',
        reply_markup=markup)
    
    return NEW_QUESTION


def new_question(update, context):
    global quiz_block
    quiz_block = random.choice(QUIZ)
    redis_base.set(update.effective_chat.id, quiz_block['Вопрос'])
    update.message.reply_text(text=quiz_block['Вопрос'], reply_markup=markup)

    return ANSWER


def answer(update, context):
    message = update.message.text

    if message == quiz_block['Ответ']:
        update.message.reply_text(
            'Правильно!\n'
            'Для продолжения нажми на "Новый вопрос"',
            reply_markup=markup)
        
        return NEW_QUESTION

    elif re.search(message, quiz_block['Зачет']):
        update.message.reply_text(
            'Почти в точку! Правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(quiz_block['Ответ']),
            reply_markup=markup)

        return NEW_QUESTION

    else:
        update.message.reply_text(
            'Неверно, попробуй еще',
            reply_markup=markup)
        
        return ANSWER


def give_up(update, context):
    update.message.reply_text(
            'Бывает, правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(quiz_block['Ответ']),
            reply_markup=markup)
    
    return NEW_QUESTION


def score(update, context):
    update.message.reply_text(
            'Пока нет очков\n'
            'Для продолжения нажми на "Новый вопрос"\n'
            'Для завершения игры /cancel',
            reply_markup=markup)
    
    return NEW_QUESTION


def cancel(update, context):
    user = update.message.from_user
    update.message.reply_text('Пока, увидимся в следующий раз.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END



if __name__ == "__main__":
    load_dotenv()
    quiz_files_path = os.getenv('QUIZ_FILES_PATH')
    tg_token = os.getenv('TG_TOKEN')

    QUIZ = get_quiz_for_bot(quiz_files_path)
    
    updater = Updater(tg_token, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            NEW＿QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), new_question),
            
                           MessageHandler(Filters.regex('^Мой счет$'), score)],

            ANSWER: [MessageHandler(Filters.regex('^Сдаться$'), give_up),
            
                     MessageHandler(Filters.text, answer),]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    
    updater.start_polling()
    
    updater.idle()
