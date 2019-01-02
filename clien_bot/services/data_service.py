
from pymongo import MongoClient
from flask import Flask


class DataService(object):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['clien_bot']
        # collection은 게시판 별로 (지금은 allsell으로 고정)
        self.collections = ['allsell']

    def insert_new_chat_id(self, chat_id):
        # TODO: 모든 게시판(collection) 대상으로 추가
        inserted_ids = []
        for board in self.collections:
            collection = self.db[board]
            if collection.count_documents(filter={'chat_id': chat_id}) < 1:
                res = collection.insert_one({'chat_id': chat_id, 'keywords': []})
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

    def select_all_chat_ids(self):
        # 모든 chat_id 가져오기 (공지 발송용)
        chat_ids = []
        for board in self.collections:
            collection = self.db[board]
            for item in collection.find():
                chat_ids.append(item['chat_id'])
        # remove duplication
        return list(set(chat_ids))
