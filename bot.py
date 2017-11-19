import time
import logging
from hashlib import blake2b
from time import sleep

import telebot
import requests
import eventlet

from config import *
from SQLighter import SQLighter

# CHANGE THIS IF YOU WANT YOUR OWN BEHAVIOR
# Names of vk publics/groups
PUBLICS = ['matobes_maga_2017', 'mmspbu']
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


def get_vk_url(domain, token, count=5):
    return 'https://api.vk.com/method/wall.get?domain={}&count={}&filter=owner&access_token={}'.format(domain,
                                                                                                count,
                                                                                                token)


def get_string_hash(string):
    h = blake2b(key=b'4242', digest_size=10)
    h.update(str.encode(s))
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


def get_data_matmech(website):
    pass


def send_new_posts(items, public):
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


def check_new_posts_vk():
    for pub in PUBLICS:
        logging.info('[VK] Started scanning {} for new posts'.format(pub))

        try:
            feed = get_data_vk(pub, VK_API_TOKEN)
            if feed is not None:
                entries = feed['response'][1:]
                try:
                    pinned = entries[0]['is_pinned']
                    send_new_posts(entries[1:], pub)
                except KeyError:
                    send_new_posts(entries, pub)
        except Exception as ex:
            logging.error('Exception of type {!s} in check_new_posts_vk(): {!s}'.format(type(ex).__name__,
                                                                                        str(ex)))
        logging.info('[VK] Finished scanning {}'.format(pub))


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='bot_log.log',
                        datefmt='%d.%m.%Y %H:%M:%S')

    if not SINGLE_RUN:
        while True:
            check_new_posts_vk()
            logging.info('[App] Script went to sleep.')
            time.sleep(60 * 4)
    else:
        check_new_posts_vk()
    logging.info('[App] Script exited.\n')
