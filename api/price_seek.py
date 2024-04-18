import re
from typing import Dict, List
import persiantools.digits as persian_digits
import requests
import asyncio
from time import sleep
import api.api_async as api


class PriceSeek:
    '''This class will get the index page of Irarz.com and extract the USD price in tomans from it. It also can extract other prices by providing the right pattern details.'''
    
    def extract_price(self, html: str) -> List[Dict[str, str|float|int]]:
        results = []
        for match in re.findall(self.price_pattern, html):
            price_fa = match.replace(self.pattern_left_hand, '').replace(self.pattern_right_hand, '')
            price = price_fa.replace(self.digit_separator, '')
            try:
                price = float(persian_digits.fa_to_en(price))
            except:
                pass
            results.append({'fa': price_fa, 'value': price, 'en': f'{price:,}'})

        return results


    @staticmethod
    def GetPattern(price_key: str, parent_html_tag: str) -> str:
        # TODO: GET A PATTERN THAT IS independent to tag type
        left = f'<{parent_html_tag} id="{price_key}">'
        right = f'</{parent_html_tag}>'
        return f'{left}.*?{right}', left, right
    

    def __init__(self, price_key: str = 'usdmax', parent_html_tag: str = 'span', url: str = 'irarz.com', timeout: int = 5) -> None:
        self.digit_separator = ','
        self.parent_html_tag = parent_html_tag
        self.price_key = price_key
        self.price_pattern, self.pattern_left_hand, self.pattern_right_hand = PriceSeek.GetPattern(self.price_key, self.parent_html_tag)
        self.url: str = f'https://{url}' if 'https://' not in url else url
        self.timeout: timeout = timeout
        
    def get_index_sync(self) -> str:
        html = requests.get(self.url)
        return html.text
    
    async def get_index(self):
        req = api.Request(self.url)
        res = await req.get()
        return res.value
    
    async def get_all(self) -> List[Dict[str, str|float|int]]:
        html = await self.get_index()
        result = self.extract_price(html)
        if not result:
            raise ValueError('Can not get price(s).')
        return result
    
    async def get(self) -> Dict[str, str|int|float]:
        results = await self.get_all()
        return results[0]

    async def list_currency_ids(self):
        '''Search though code and find all possible ids'''
        # TODO: write this methid 
        pass

    
def run_async(method):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(method())
    loop.close()


if __name__ == '__main__':
    async def run():
        while True:
            try:
                usd_seeker = PriceSeek()
                print(await usd_seeker.get_all())
                sleep(10)
            except:
                pass
    run_async(run)