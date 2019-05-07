
from pymongo import MongoClient
from itertools import groupby
import time


class DataService(object):
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client['crawler']
        # collection은 게시판 별로 (지금은 allsell으로 고정)
        self.collections = ['allsell']
        self.crawl_collection = self.db['crawl_info']

    def insert_new_crawl_info(self, board, url):
        return self.crawl_collection.insert_one({
            'board': board, 'url': url, 'latest_sn': 0
        }).inserted_id

    def select_crawl_info(self, board):
        return self.crawl_collection.find_one({'board': board})

    def update_latest_sn(self, board, latest_sn):
        updated = self.crawl_collection.find_one_and_update(
            {'board': board}, {'$set': {'latest_sn': latest_sn}})
        return updated['_id']

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

    def select_all_chat_ids(self):
        # 모든 chat_id 가져오기 (공지 발송용)
        chat_ids = []
        for board in self.collections:
            collection = self.db[board]
            for item in collection.find():
                chat_ids.append(item['chat_id'])
        # remove duplication
        return list(set(chat_ids))

    # {'chat_id': xxx, 'keywords': []} 형태를 {'keyword': xxx, 'chat_ids': []}로 변경하는 method
    def pivot_all(self, board):
        collection = self.db[board]
        raw_list = []
        for item in collection.find():
            for keyword in item['keywords']:
                raw_list.append({'keyword': keyword, 'chat_id': item['chat_id']})

        raw_list = sorted(raw_list, key=lambda x: x['keyword'])
        pivot_list = []
        for k, group in groupby(raw_list, lambda x: x['keyword']):
            pivot_list.append({
                'keyword': k,
                'chat_ids': [m['chat_id'] for m in group]
            })
        return pivot_list
