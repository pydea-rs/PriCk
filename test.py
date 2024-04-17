from flask import *
from api.price_seek import PriceSeek

usd_seeker = PriceSeek()
app = Flask(__name__)

@app.route('/', methods=['GET'])
async def something():
    '''Special route handler. optional. used for some special purposes, for example if your bot uses payment gateways, you must define payment callback route this way.'''
    res = await usd_seeker.get_all()
    return jsonify({'status': 'ok', 'data': res})

if __name__ == '__main__':
    app.run(debug=True)