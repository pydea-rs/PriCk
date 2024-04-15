import re
from typing import Dict, List
import requests


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
    

    def __init__(self, price_key: str = 'usdmax', parent_html_tag: str = 'span', url: str = 'irarz.com') -> None:
        self.digit_separator = ','
        self.parent_html_tag = parent_html_tag
        self.price_key = price_key
        self.price_pattern, self.pattern_left_hand, self.pattern_right_hand = PriceStealer.GetPattern(self.price_key, self.parent_html_tag)
        self.url: str = f'https://{url}' if 'https://' not in url else url

    def get_index(self) -> str:
        html = requests.get(self.url)
        # TODO: use async here
        return html
    
    def get_all(self) -> List[Dict[str, str|float|int]]:
        html = self.get_index()
        result = self.extract_price(html)
        if not result:
            raise ValueError('Can not get price(s).')
        return result
    
    def get(self) -> Dict[str, str|int|float]:
        return self.get_all()[0]