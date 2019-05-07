
import time

from pymongo import MongoClient


class DataService(object):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['crawler']
        # collection은 게시판 별로 (지금은 allsell으로 고정)
        self.collections = ['allsell']
        self.crawl_collection = self.db['crawl_info']

    def insert_new_chat_id(self, chat_id):
        # TODO: 모든 게시판(collection) 대상으로 추가
        inserted_ids = []
        for board in self.collections:
            collection = self.db[board]
            if collection.count_documents(filter={'chat_id': chat_id}) < 1:
                res = collection.insert_one({
                    'chat_id': chat_id, 'keywords': [],
                    'created_at': time.time()
                })
                inserted_ids.append(res.inserted_id)
        return inserted_ids

    def delete_chat_id(self, chat_id):
        # TODO: 모든 게시판(collection) 대상으로 chat_id 삭제
        # allsell에서 chat_id 가진 모든 documents 삭제
        for board in self.collections:
            collection = self.db[board]
            collection.delete_many({'chat_id': chat_id})

    def update_keywords(self, chat_id, board, keywords):
        # keywords key의 값을 통째로 교체
        collection = self.db[board]
        updated = collection.find_one_and_update({'chat_id': chat_id},
                                                 {'$set': {'keywords': keywords}})
        return updated['_id']

    def clear_keywords(self, chat_id, board):
        # keywords list의 모든 원소 제거
        return self.update_keywords(chat_id, board, [])

    def select_keywords(self, chat_id, board):
        # TODO: keywords 가져오기
        collection = self.db[board]
        found = collection.find_one({'chat_id': chat_id})
        if 'keywords' in found:
            return found['keywords']
        return []
