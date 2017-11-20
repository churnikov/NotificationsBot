import time
import logging
import json
import pickle
from os.path import exists
from os import mkdir
from hashlib import blake2b
from time import sleep

import telebot
import requests
import eventlet
from bs4 import BeautifulSoup

from config import *
from SQLighter import SQLighter

# CHANGE THIS IF YOU WANT YOUR OWN BEHAVIOR
# Names of vk publics/groups
PUBLICS = ['matobes_maga_2017', 'mmspbu']
WEBSITES = ['mm_announcements_website']
# Links to your news from publics and websites.
# Hardcode? yes! But what you gonna do? c:
LINKS = {'matobes_maga_2017' : 'https://vk.com/wall-152791710_',
         'mmspbu' : 'https://vk.com/wall-60204250_',
         'mm_website' : 'http://www.math.spbu.ru/rus/',
         'mm_announcements_website' : 'http://www.math.spbu.ru/rus/study/announcement.html'}
# SOURCES are needed for sqlite database.
# Keys should match with values above
SOURCES = {'matobes_maga_2017':1,
           'mmspbu' : 2,
           'mm_website' : 3,
           'mm_announcements_website' : 4}
# Name of Database.
DATABASE = 'news.sqlite'
# This field affects if script would run only once (good for scheduler in linux)
# Or, if True, would run in infinite loop.
SINGLE_RUN = False

bot = telebot.TeleBot(TELE_TOKEN)


class text_worker:


    def __init__(self, json_name, clf_news_file, clf_target_file,
                 text_transformer_file):
        self.json_name = json_name
        self.clf_news_file = clf_news_file
        self.clf_target_file = clf_target_file
        self.text_transformer_file = text_transformer_file

        self.clf_news = None
        self.clf_target = None
        self.__text_transformer = None


    def get_transformer(self):
        if self.__text_transformer is None:
            with open('models/'+self.text_transformer_file, 'rb') as f:
                self.__text_transformer = pickle.load(f)
        return self.__text_transformer


    def get_target_group(self, text):
        """text should be string"""
        if self.clf_target is None:
            with open('models/'+self.clf_target_file, 'rb') as f:
                self.clf_target = pickle.load(f)
        X = self.get_transformer().transform(text)
        return self.clf_target.predict(X)


    def get_news_group(self, text):
        """text should be string"""
        if self.clf_news is None:
            with open('models/'+self.clf_news_file, 'rb') as f:
                self.clf_news = pickle.load(f)
        X = self.get_transformer().transform(text)
        return self.clf_news.predict(X)


    def write_text_to_json(self, key, target_level, target_news, text):
        """
        Write text data to json
        :key:          (str )-- unique key of text
        :target_level:       -- label of target students
        :target_news:        -- label of target news
        :text:               -- list of strings
        :json_name:          -- name of json file to save.
                          if not exists in folder 'data', will create one
        """
        if not exists('data/'):
            mkdir('data/')

        with open('data/'+self.json_name, 'r') as f:
            data_json = json.load(f)

        data_json['text'].update({key : text})
        data_json['target_level'].update({key : target_level})
        data_json['target_news'].update({key : target_news})

        with open('data/'+self.json_name, 'w') as f:
            json.dump(data_json, f)


text_worker = text_worker(json_name='new_data.json',
                          clf_news_file='news_classifier.pickle',
                          clf_target_file='level_classifier.pickle',
                          text_transformer_file='doc2numbers.pickle')


def get_vk_url(domain, token, count=5):
    return 'https://api.vk.com/method/wall.get?domain={}&count={}&filter=owner&access_token={}'.format(domain,
                                                                                                count,
                                                                                                token)


def get_string_hash(string):
    h = blake2b(key=b'4242', digest_size=10)
    h.update(str.encode(string))
    return h.hexdigest()


def get_data_vk(domain, token):
    vk_url = get_vk_url(domain, token)
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(vk_url)
        return feed.json()
    except:
        logging.warning('Got Timeout while retrieving VK JSON data from `{}`. Canceling...'.format(domain))
        return None
    finally:
        timeout.cancel()


def get_data_web(website, limit=5):
    req = requests.get(website)
    if req.status_code == 200:
        logging.info('MatMech website is working, begining to parse')
        content = req.content
        soup = BeautifulSoup(content, 'lxml')

        content = dict()

        first_post = soup.find('div', {'class' : 'content clearfix'})
        news = []
        for hr in first_post.findChildren():
            if hr.name == 'hr':
                break
            news.append(hr.text)

        key = get_string_hash('\n'.join(news))
        content[key] = news

        for hr in soup.findAll('hr'):
            news = []
            for item in hr.find_next_siblings():
                if item.name == 'hr':
                    break
                news.append(item.text)
            key = get_string_hash('\n'.join(news))
            # Setting limit for news to return
            content[key] = news
            if len(content) > limit:
                break
        return content
    else:
        logging.warning('Could not reach {}'.format(website))
        return None


def send_new_posts_from_vk(items, public):
    db = SQLighter(DATABASE)
    last_id = None
    for item in items:
        if db.add_event((str(item['id']), SOURCES[public])):
            link = '{!s}{!s}'.format(LINKS[public], item['id'])
            bot.send_message(CHANNEL_NAME, link)
        else:
            logging.info('New last_id (VK) in public {} is {!s}'.format(public, item['id']))
            break
        time.sleep(1)
    return


def send_new_posts_from_web(items, sourse_site):
    db = SQLighter(DATABASE)
    last_id = None
    for key, item in items.items():
        if db.add_event((key, SOURCES[sourse_site])):
            bot.send_message(CHANNEL_NAME, '\n'.join(item))
        else:
            logging.info('New last_id (website) in public {!s} is {!s}'.format(sourse_site, key))
            break
        time.sleep(1)
    return


def check_new_posts_vk():
    for pub in PUBLICS:
        logging.info('[VK] Started scanning {} for new posts'.format(pub))

        try:
            feed = get_data_vk(pub, VK_API_TOKEN)
            if feed is not None:
                entries = feed['response'][1:]
                try:
                    pinned = entries[0]['is_pinned']
                    send_new_posts_from_vk(entries[1:], pub)
                except KeyError:
                    send_new_posts_from_vk(entries, pub)
        except Exception as ex:
            logging.error('Exception of type {!s} in check_new_posts_vk(): {!s}'.format(type(ex).__name__,
                                                                                        str(ex)))
        logging.info('[VK] Finished scanning {}'.format(pub))


def check_new_posts_web():
    for sourse_site in WEBSITES:
        try:
            logging.info('[WEBSITE] Started scanning {} for news'.format(sourse_site))
            news = get_data_web(LINKS[sourse_site])
            if news:
                send_new_posts_from_web(news, sourse_site)
        except Exception as ex:
            logging.error('Exception of type {!s} in check_new_posts_web(): {!s}'.format(type(ex).__name__,
                                                                                        str(ex)))
        logging.info('[WEBSITE] Finished scanning {}'.format(sourse_site))


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='bot_log.log',
                        datefmt='%d.%m.%Y %H:%M:%S')

    if not SINGLE_RUN:
        while True:
            check_new_posts_vk()
            check_new_posts_web()
            logging.info('[App] Script went to sleep.\n')
            time.sleep(60 * 10)
    else:
        check_new_posts_vk()
    logging.info('[App] Script exited.\n')
