import redis
import os
import json

from dotenv import load_dotenv

load_dotenv()


class RedisHandler:
    question, answer, offset, fail, comment = '', '', '', '', ''

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_URL"),
            port=os.getenv("REDIS_PORT"),
            password=os.getenv("REDIS_PASSWORD"),
            charset="utf-8",
            decode_responses=True,
        )

    def initiate_score(self, score_id):
        if self.redis.get(score_id) is None:
            self.redis.set(score_id, 0)
              
    def initiate_new_quiz_block(self, user):
        question_number = self.redis.randomkey()
        redis_value = self.redis.get(question_number)
        quiz_block = json.loads(redis_value)

        self.question = quiz_block['question']
        self.answer = quiz_block['answer']
        self.offset = quiz_block['offset']
        self.fail = quiz_block['fail']
        self.comment = quiz_block['comment']

        user_info = json.dumps({'last_asked_question': question_number})
        self.redis.set(user, user_info)
        
    def set_score(self, score_id, score=0):
        self.redis.set(score_id, (int(self.redis.get(score_id)) + score))
    
    def get_score(self, score_id):
        if self.redis.get(score_id):
            return self.redis.get(score_id)
        else:
            return 0
        