import re
from typing import Dict, List
import requests
import aiohttp
import asyncio
from time import sleep


class PriceStealer:
    '''This class will get the index page of Irarz.com and extract the USD price in tomans from it. It also can extract other prices by providing the right pattern details.'''
    
    def extract_price(self, html: str) -> List[Dict[str, str|float|int]]:
        results = []
        for match in re.findall(self.price_pattern, html):
            price_fa = match.replace(self.pattern_left_hand, '').replace(self.pattern_right_hand, '')
            price = price_fa.replace(self.digit_separator, '')
            results.append({'fa': price_fa, 'value': price})

        return results


    @staticmethod
    def GetPattern(price_key: str, parent_html_tag: str) -> str:
        left = f'<{parent_html_tag} id="{price_key}">'
        right = f'</{parent_html_tag}>'
        return f'{left}.*?{right}', left, right
    

    def __init__(self, price_key: str = 'usdmax', parent_html_tag: str = 'span', url: str = 'irarz.com', timeout: int = 5) -> None:
        self.digit_separator = ','
        self.parent_html_tag = parent_html_tag
        self.price_key = price_key
        self.price_pattern, self.pattern_left_hand, self.pattern_right_hand = PriceStealer.GetPattern(self.price_key, self.parent_html_tag)
        self.url: str = f'https://{url}' if 'https://' not in url else url
        self.timeout: timeout = timeout
        
    def get_index_sync(self) -> str:
        html = requests.get(self.url)
        # TODO: use async here
        return html.text
    
    async def get_index(self):
        async with aiohttp.ClientSession(trust_env=True, timeout=aiohttp.ClientTimeout(self.timeout)) as session:
            async with session.get(self.url) as response:
                return await response.text()
            
    async def get_all(self) -> List[Dict[str, str|float|int]]:
        html = await self.get_index()
        result = self.extract_price(html)
        if not result:
            raise ValueError('Can not get price(s).')
        return result
    
    async def get(self) -> Dict[str, str|int|float]:
        return await self.get_all()[0]

async def run():
    while True:
        try:
            usd_stealer = PriceStealer()
            print(await usd_stealer.get_all())
            sleep(10)
        except:
            pass
    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())