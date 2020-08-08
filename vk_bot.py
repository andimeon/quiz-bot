import os
import logging
from dotenv import load_dotenv
import random
import re
from textwrap import dedent

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from quiz_dict import get_quiz_for_bot
from redis_connection import get_database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)

global quiz_block

redis_base = get_database()


def send_message(event, text):
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


if __name__ == "__main__":
    load_dotenv()
    vk_session = vk_api.VkApi(token=os.getenv('VK_TOKEN'))
    quiz_files_path = os.getenv('QUIZ_FILES_PATH')

    QUIZ = get_quiz_for_bot(quiz_files_path)

    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    quiz_block = random.choice(QUIZ)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            if event.text == 'Start':
                text = 'Привет! Для начала игры нажми "Новый вопрос"'
                send_message(event, text)

            if event.text == 'Новый вопрос':
                quiz_block = random.choice(QUIZ)
                print(quiz_block['Ответ'])
                redis_base.set(event.user_id, quiz_block['Вопрос'])
                send_message(event, quiz_block['Вопрос'])

            elif event.text == 'Сдаться':
                text = dedent(f'''
                    Бывает!
                    Правильный ответ - {quiz_block['Ответ']}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif event.text == 'Мой счет':
                text = 'Пока счета нет'
                send_message(event, text)

            elif event.text == quiz_block['Ответ']:
                text = dedent(f'''
                    Правильно!
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif re.search(event.text, quiz_block['Зачет']):
                text = dedent(f'''
                    Почти попал
                    Правильный ответ - {quiz_block['Ответ']}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)
            
            else:
                text = dedent(f'''
                    Упс, неправильно!
                    Попробуй еще раз
                ''')
                send_message(event, text)