import os
import logging
from dotenv import load_dotenv
import random
import re
from textwrap import dedent
import json

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from redis_handler import RedisHandler

logger = logging.getLogger(__name__)

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)

redis_base = RedisHandler()


def send_message(event, text):
    vk.messages.send(
        user_id=event.obj.from_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    load_dotenv()
    vk_session = vk_api.VkApi(token=os.getenv('VK_TOKEN'))
    longpoll = VkBotLongPoll(vk_session, group_id=os.getenv('VK_GROUP_ID'))

    vk = vk_session.get_api()

    for event in longpoll.listen():
        user = f'user_vk_{event.obj.from_id}'
        score_id = f'score_tg_{event.obj.from_id}'

        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.text == 'Start':
                redis_base.initiate_score(score_id)
                text = 'Привет! Для начала игры нажми "Новый вопрос"'
                send_message(event, text)
                continue

            if event.obj.text == 'Новый вопрос':
                redis_base.initiate_new_quiz_block(user)
                print(redis_base.answer)
                send_message(event, redis_base.question)

            elif event.obj.text == 'Сдаться':
                redis_base.set_score(score_id)
                text = dedent(f'''
                    Бывает!
                    Правильный ответ - {redis_base.answer}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif event.obj.text == 'Мой счет':
                text = f'Ваш счет {redis_base.get_score(score_id)}'
                send_message(event, text)

            elif event.obj.text == redis_base.answer:
                redis_base.set_score(score_id, 1)
                text = dedent(f'''
                    Правильно!
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif re.search(event.obj.text, redis_base.offset):
                redis_base.set_score(score_id, 1)
                text = dedent(f'''
                    Почти попал
                    Правильный ответ - {redis_base.answer}
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