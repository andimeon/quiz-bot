import redis
import os
import json

from dotenv import load_dotenv

load_dotenv()


class RedisHandler:
    question, answer, offset, fail, comment = '', '', '', '', ''
    question_number, user = '', ''
    score = 0

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_URL"),
            port=os.getenv("REDIS_PORT"),
            password=os.getenv("REDIS_PASSWORD"),
            charset="utf-8",
            decode_responses=True,
        )

    def initiate_score(self, user):
        self.user = user
        if self.redis.get(user):
            user_info_str = self.redis.get(user)
            user_info = json.loads(user_info_str)
            self.score = user_info['score']
    
    def initiate_new_quiz_block(self):
        self.question_number = self.redis.randomkey()
        redis_value = self.redis.get(self.question_number)
        quiz_block = json.loads(redis_value)

        self.question = quiz_block['question']
        self.answer = quiz_block['answer']
        self.offset = quiz_block['offset']
        self.fail = quiz_block['fail']
        self.comment = quiz_block['comment']
    
    def set_score(self):
        user_info = json.dumps({
            'last_asked_question': self.question_number,
            'score': self.score})

        self.redis.set(self.user, user_info)
        