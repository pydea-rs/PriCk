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


class PriCKerBot(TelegramBot):
    
    def __init__(self, token: str, username: str, host_url: str, text_resources: dict, _main_keyboard: Dict[str, Keyboard] | Keyboard = None) -> None:
        super().__init__(token, username, host_url, text_resources, _main_keyboard)
        self.__changers: Dict[int, str] = []
        self.__intervallers : Dict[int, str]= []
        self.__prev_prices = []
        self.__seeker = PriceSeek()
        self.seek = self.__seeker.get_all
        self.to_string = lambda prices: "\n".join([str(price) for price in prices])

    def has_price_changed(self, prices) -> bool:
        try:
            if self.__prev_prices[0]['value'] != prices[0]['value']:
                self.__prev_prices = prices
                return True
        except:
            self.__prev_prices = prices
            return True
        return False
    
    def update_change_subscribers(self, chat_id: int):
        if chat_id not in self.__changers:
            self.__changers[chat_id] = "usd"
            return
        del self.__changers[chat_id]
        
    def update_interval_subscribers(self, chat_id: int):
        if chat_id not in self.__intervallers:
            self.__intervallers[chat_id] = "usd"
            return
        del self.__intervallers[chat_id]

    def subscribers(self) -> list[int]:
        return list(self.__intervallers.keys()).extend(list(self.__changers.keys()))

    async def seek_to_string(self) -> str:
        prices = await self.seek()
        return self.to_string(prices)
                            
    async def send_to_all(self):
        prices = await self.seek_to_string()
        for chat_id in self.subscribers():
            await self.send(GenericMessage(chat_id, prices))
        return prices
    async def send_price_to_changers(self):
        prices = self.to_string(self.__prev_prices)

        for chat_id in self.__changers:
            await self.send(GenericMessage.Text(chat_id, prices))

    @property
    def intervallers(self):
        return self.__intervallers
    
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
    bot.update_change_subscribers(chat_id=message.chat_id)

def subscribe_by_interval_job(bot: PriCKerBot, message: GenericMessage) -> Union[GenericMessage, Keyboard|InlineKeyboard]:
    bot.update_interval_subscribers(chat_id=message.chat_id)

   
main_keyboard = {
    'en': Keyboard(text_resources["keywords"]["SubscribeChanges"]["en"], text_resources["keywords"]["SubscribeByInterval"]["en"]),
    'fa': Keyboard(text_resources["keywords"]["SubscribeChanges"]["fa"], text_resources["keywords"]["SubscribeByInterval"]["fa"])
}

bot = PriCKerBot(token=BOT_TOKEN, username=BOT_USERNAME, host_url=HOST_URL, text_resources=text_resources, _main_keyboard=main_keyboard)
bot.add_message_handler(message=bot.keyword('SubscribeChanges'), handler=subscribe_changes_job)
bot.add_message_handler(message=bot.keyword('SubscribeByInterval'), handler=subscribe_by_interval_job)

bot.add_command_handler(command='uptime', handler=lambda bot, message: (GenericMessage.Text(message.by.chat_id, bot.get_uptime()), None))
# Parallel Jovbs:
async def send_usd_price_job(bot: PriCKerBot)-> Union[GenericMessage, Keyboard|InlineKeyboard]:
    '''Parallel jobs are optional methods that will run by an special interval simultaniouesly with users requests.'''
    usd_seeker = PriceSeek()
    prices = await usd_seeker.get_all()
    textmsg = bot.to_string(prices)
    for chat_id in bot.intervallers:
        await bot.send(GenericMessage.Text(chat_id, textmsg))
    if bot.has_price_changed(prices):
        await bot.send_price_to_changers()
    return prices

job = bot.prepare_new_parallel_job(1, send_usd_price_job, bot)

bot.start_clock()  # optional, but mandatory if you defined at least one parallel job. also if you want to calculate bot uptime.
bot.config_webhook()  # automatically writes the webhook path route handler, so that users messages(requests), all be passed to bot.handle method

@bot.app.route('/fire', methods=['GET'])
async def fire():
    '''Bypass schedular and send prices to all subscribers'''
    prices = await bot.send_to_all(bot)
    return jsonify({'status': 'ok', 'prices': prices})


if __name__ == '__main__':
    bot.go(debug=False)
