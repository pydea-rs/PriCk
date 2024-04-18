import requests
from decouple import config


bot_token = config("BOT_TOKEN")
webhook_url = config('HOST_URL')
def set_webhook():
    url = f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}'
    print(url)
    response = requests.get(url)
    print(response.text)

if __name__ == '__main__':
    set_webhook()
