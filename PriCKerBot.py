import logging
from payagraph.bot import *
from payagraph.containers import *
from payagraph.keyboards import *
from payagraph.keyboards import Keyboard
from payagraph.tools import *
from decouple import config
from tools import manuwriter
from typing import Dict, Union
from tools.exceptions import *
from api.price_seek import PriceSeek
from typing import Dict
from tools.mathematix import timestamp


class PriCKerBot(TelegramBot):
    
    def load_subscribers(self):
        for user in User.GetAll():
            if user.is_intervaller:
                self.__intervallers[user.chat_id] = "usd"
            if user.is_changer:
                self.__changers[user.chat_id] = "usd"
                
    def __init__(self, token: str, username: str, host_url: str, text_resources: dict, _main_keyboard: Dict[str, Keyboard] | Keyboard = None) -> None:
        super().__init__(token, username, host_url, text_resources, _main_keyboard)
        self.__changers: Dict[int, str] = {}
        self.__intervallers : Dict[int, str]= {}
        self.__current_prices = []
        self.__seeker = PriceSeek()
        self.seek = self.__seeker.get_all
        self.to_string = lambda prices: "\n".join([str(price) for price in prices])

    def has_price_changed(self, prices) -> bool:
        try:
            if self.__current_prices[0]['value'] != prices[0]['value']:
                self.__current_prices = prices
                return True
        except:
            self.__current_prices = prices
            return True
        return False
    
    def update_change_subscribers(self, user: User):
        if user.chat_id not in self.__changers:
            self.__changers[user.chat_id] = "usd"
            user.is_changer = True
            return
        del self.__changers[user.chat_id]
        user.is_changer = False
        
    def update_interval_subscribers(self, user: User):
        if user.chat_id not in self.__intervallers:
            self.__intervallers[user.chat_id] = "usd"
            user.is_intervaller = True
            
            return
        del self.__intervallers[user.chat_id]
        user.is_intervaller = False
        
    def subscribers(self) -> list[int]:
        return list(self.__intervallers.keys()) + list(self.__changers.keys())
        
    async def seek_to_string(self) -> str:
        prices = await self.seek()
        return self.to_string(prices)
           
    async def send_to_all(self):
        prices = await self.seek_to_string()
        subscribers = self.subscribers()
        for chat_id in subscribers:
            await self.send(GenericMessage.Text(chat_id, prices))
        return prices
    
    async def send_price_to_changers(self):
        for chat_id in self.__changers:
            user = User.Get(chat_id, no_cache=True)
            textmsg = (bot.text("price_is", user.language) % (bot.current_prices[0][user.language])) + "\n\n" + timestamp(user.language)
            await self.send(GenericMessage.Text(chat_id, textmsg))
            user.previous_message_id = None
            
    def main_keyboard(self, user: User = None) -> Keyboard:
        '''Get the keyboard that must be shown in most cases and on Start screen.'''
        return Keyboard(self.text_resources["keywords"][("un" if user.is_changer else "") + "subscribe_changes"][user.language],
                        self.text_resources["keywords"][("un" if user.is_intervaller else "") + "subscribe_by_interval"][user.language],
                        self.text_resources["keywords"]["change_language"][user.language])
    
    @property
    def intervallers(self):
        return self.__intervallers
    
    
    @property
    def current_prices(self):
        return self.__current_prices
    
    @property
    def changers(self):
        return self.__changers
    
    
# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# read .env configs
# You bot data
BOT_TOKEN = config('BOT_TOKEN')
HOST_URL = config('HOST_URL')
BOT_USERNAME = config('BOT_USERNAME')

# Read the text resource containing the multilanguage data for the bot texts, messages, commands and etc.
# Also you can write your texts by hard coding but it will be hard implementing multilanguage texts that way,
text_resources = manuwriter.load_json('texts', 'resources')

def subscribe_changes_job(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    bot.update_change_subscribers(user=message.by)
    message.by.save()
    return GenericMessage.Text(message.chat_id, bot.text("subscribed_as_changer" if message.by.is_changer else "unsubscribed_as_changer", message.by.language)), None

def subscribe_by_interval_job(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    bot.update_interval_subscribers(user=message.by)
    message.by.save()
    return GenericMessage.Text(message.chat_id, bot.text("subscribed_as_intervaller" if message.by.is_intervaller else "unsubscribed_as_intervaller", message.by.language)), None

def change_language_handler(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    user = message.by
    user.language = "en" if user.language.lower() == 'fa' else 'fa'
    user.save()
    return GenericMessage.Text(message.chat_id, bot.text("default_message", message.by.language)), None


def send_whole_data(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    user = message.by
    textmsg = bot.to_string(bot.current_prices)
    message = GenericMessage.Text(user.chat_id, textmsg)
    user.previous_message_id = None
    return GenericMessage.Text(message.chat_id, textmsg), None


async def check_prices(bot: PriCKerBot):
    '''Job for retreiving prices everyminute, and notify changers if needed.'''
    usd_seeker = PriceSeek()
    prices = await usd_seeker.get_all()
    if bot.has_price_changed(prices):
        await bot.send_price_to_changers()
        
# Parallel Jovbs:
async def send_usd_price_job(bot: PriCKerBot):
    '''Job for sending price fto intervallers every 5 minutes.'''
    for chat_id in bot.intervallers:
        user = User.Get(chat_id)
        textmsg = (bot.text("price_is", user.language) % (bot.current_prices[0][user.language])) + "\n\n" + timestamp(user.language)
        message = GenericMessage.Text(chat_id, textmsg)
        response = None
        if not user.previous_message_id:
            message.text += f"\n- - - - - - - - - - - - - - - - - - - - -\n{bot.text('follow_this_message', user.language)}"
            response = await bot.send(message)
        else:
            message.id = user.previous_message_id
            response = await bot.edit(message)
        user.previous_message_id = response['result']['message_id']

    return bot.current_prices


bot = PriCKerBot(token=BOT_TOKEN, username=BOT_USERNAME, host_url=HOST_URL, text_resources=text_resources)
bot.add_message_handler(message=bot.keyword('subscribe_changes'), handler=subscribe_changes_job)
bot.add_message_handler(message=bot.keyword('unsubscribe_changes'), handler=subscribe_changes_job)
bot.add_message_handler(message=bot.keyword('subscribe_by_interval'), handler=subscribe_by_interval_job)
bot.add_message_handler(message=bot.keyword('unsubscribe_by_interval'), handler=subscribe_by_interval_job)

bot.add_message_handler(message=bot.keyword('change_language'), handler=change_language_handler)

bot.add_command_handler(command='uptime', handler=lambda bot, message: (GenericMessage.Text(message.by.chat_id, bot.get_uptime()), None))
bot.add_command_handler(command='data', handler=send_whole_data)

job = bot.prepare_new_parallel_job(1, check_prices, bot)

job = bot.prepare_new_parallel_job(10, send_usd_price_job, bot)

def fast_interval(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    job.interval = 1
    return GenericMessage.Text(message.chat_id, "Interval set on 1 minute."), None

def normal_interval(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    job.interval = 1
    return GenericMessage.Text(message.chat_id, "Interval set on 10 minutes."), None

def hourly_interval(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    job.interval = 60
    return GenericMessage.Text(message.chat_id, "Interval set on 1 hour."), None

bot.add_command_handler(command='fast', handler=fast_interval)
bot.add_command_handler(command='normal', handler=normal_interval)
bot.add_command_handler(command='hourly', handler=hourly_interval)

bot.load_subscribers()
bot.start_clock()  # optional, but mandatory if you defined at least one parallel job. also if you want to calculate bot uptime.
# bot.config_webhook()  # automatically writes the webhook path route handler, so that users messages(requests), all be passed to bot.handle method

@bot.app.route('/fire', methods=['GET'])
async def fire():
    '''Bypass schedular and send prices to all subscribers'''
    prices = await bot.send_to_all()
    return jsonify({'status': 'ok', 'prices': prices})


if __name__ == '__main__':
    bot.go(polling=True)