# Telegram bot for notifications for Computer Science students at Mathematics and Mechanics department (2017).

## Usage
### Easy way
- open this [channel](https://t.me/matobes2017_19) and enjoy

### A bit harder way (for now)
If you don't want to get notifications from our [public group](https://vk.com/matobes_maga_2017) or want to set your own, you need then do the following:
1. Create your bot with [@BotFather](https://telegram.me/BotFather)
2. In bot.py file change `PUBLICS`, `LINKS` and `SOURCES`.
3. Create config.py file and write there:
  - `VK_API_TOKEN` - how to get, described [here](https://vk.com/dev/access_token) (it's easy)
  - `TELE_TOKEN` - token of that [@BotFather](https://telegram.me/BotFather) gave you
  - `CHANNEL_NAME` [@Your_chanel_name](https://telegram.org/blog/channels)
    - if you don't have one, create and add this bot as **admin** of the channel
4. Install requirements `pip install -r requirements.txt`
5. Seems like you are good to go)
  - If you want to schedule your posts, set `SINGLE_RUN` to `True`
  - If you want to run this script in infinite loop, set `SINGLE_RUN` to `False`

## TODO:
- Add [matmech website](http://www.math.spbu.ru/rus/) to check list (**DONE**)
- Modify this bot, so that one doesn't have to set all paremeters by hand.
- Add some other stuff (timetable, trains, e.t.c.)
  - duno how, for now
- In parsing of notifications from website, add filter for irrelevant news (like, not for our group)
  - Add named entity recognition
- Move to server (mb [here](https://wiki.python.org/moin/FreeHosts))
- Add "do not disturb" from 24 till 6 o'clock
- Don't notify over mmspbu and some irrelevant classes of news. (**Done**)
- Make better formatted text with markdown
