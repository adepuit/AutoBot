from decimal import Decimal
from _collections import deque
import numpy as np
from decimal import Decimal

from gdax.public_client import PublicClient
from gdax.websocket_client import WebsocketClient

class AutoBot(WebsocketClient):
    def __init__(self, product_id='BTC-USD',windowSize=30):
        super(AutoBot, self).__init__(products=product_id,channels=['ticker'])
        self._client = PublicClient()
        self._sequence = -1
        self._current_ticker = None
        self._queue = deque([], windowSize)
        self._window_size = windowSize
        self._last_average = 0;
        self._ownedCoins = 0


    @property
    def product_id(self):
        ''' Currently AutoBot only supports a single product even though it is stored as a list of products. '''
        return self.products[0]

    def on_open(self):
        self._sequence = -1
        print("-- Subscribed to AutoBot! --\n")

    def on_close(self):
        print("\n-- AutoBot Socket Closed! --")

    def reset_book(self):
        self._sequence = res['sequence']

    def on_message(self, message):
        if message['type'] == 'subscriptions':
            return

        sequence = message['sequence']
        if self._sequence == -1:
            self._sequence = sequence
            return
        if sequence <= self._sequence:
            # ignore older messages (e.g. before order book initialization from getProductOrderBook)
            return

        msg_type = message['type']
        if msg_type == 'match' or msg_type == 'ticker':
            self._current_ticker = message
            self._current_price = float(self._current_ticker['price'])
            #print('{} {:.2f}'.format(message['time'], float(message['price'])))
            
            self._queue.append(float(message['price']))

            #TODO: Calculate SMA 
            if len(self._queue) == self._queue.maxlen:
                #print('{} -- {}'.format(self._queue, self.moving_average(self._queue, self._window_size)))
                #print('SMA{}: {}'.format(self._window_size, self.movingAverage(self._queue, self._window_size)))
                #print('EMA{}: {:.2f}'.format(self._window_size, self.ExpMovingAverage(self._queue, self._window_size)))

                #ema9 = self.ExpMovingAverage(self._queue, 9)
                
                #print('EMA9: {}'.format(ema9))
                #macd = self.computeMACD(self._queue)
                
                #print('MACD and EMA9: {} {}'.format(macd, ema9))

                #currAverage = self.ExpMovingAverage(self._queue, self._window_size)
                currAverage = self.movingAverage(self._queue, self._window_size)

                #print('MA: {}'.format(lastCalculatedAvg))

                #first calculated value, just return
                if self._last_average == 0:
                    self._last_average = currAverage
                    self._positive_moves = 0
                    self._negative_moves = 0
                    self._last_buy_price = 0
                    self._last_sell_price = 100000000
                    return

                if currAverage - self._last_average < -.01:
                    self._positive_moves = 0
                    self._negative_moves += 1
                elif currAverage - self._last_average > .01:
                    self._positive_moves += 1
                    self._negative_moves = 0
                    
                self._last_average = currAverage

# ('''(self._current_price > self._last_buy_price * 1.005) or '''(self._current_price < self._last_buy_price * .995)) and 


                if  (
                        self._positive_moves >= 5 and 
                        self._ownedCoins <= 5 and 
                        (self._last_buy_price == 0 or self._current_price < self._last_buy_price * .95) and 
                        self._current_price * .995 < self._last_sell_price
                    ):
                    self._positive_moves = 0;
                    print('Buy at {}'.format(self._current_price))
                    self._ownedCoins += 1
                    self._last_buy_price = self._current_price
                    self._last_sell_price = 100000000
                    #buying opportunity

                if self._negative_moves > 5 and self._ownedCoins > 0 and self._current_price > self._last_buy_price * 1.005:
                    self._negative_moves = 0                    
                    print('Sell at {}'.format(self._current_price))
                    self._ownedCoins -= 1
                    self._last_sell_price = self._current_price
                    self._last_buy_price = 0
                    #selling opportunity                

        self._sequence = sequence

    def get_current_ticker(self):
        return self._current_ticker
        self._bids.insert(price, bids)

    def movingAverage(self, values, window):
        weigths = np.repeat(1.0, window)/window
        smas = np.convolve(values, weigths, 'valid')
        return smas[0] # as a numpy array
    
    def ExpMovingAverage(self, values, window):
        weights = np.exp(np.linspace(-1., 0., window))
        weights /= weights.sum()
        #a = np.convolve(values, weights, mode='full')
        a = np.convolve(values, weights, mode='full')[:len(values)]
        a[:window-1] = a[window-1]
        return float(a[len(a)-1])
    
    def computeMACD(self, x, slow=26, fast=12):
        """
        compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
        return value is emaslow, emafast, macd which are len(x) arrays
        """
        emaslow = self.ExpMovingAverage(x, slow)
        emafast = self.ExpMovingAverage(x, fast)
        return emaslow, emafast, emafast - emaslow


if __name__ == '__main__':
    import sys
    import time
    import datetime as dt


    class OrderBookConsole(OrderBook):
        ''' Logs real-time changes to the bid-ask spread to the console '''

        def __init__(self, product_id=None):
            super(OrderBookConsole, self).__init__(product_id=product_id)

            # latest values of bid-ask spread
            self._bid = None
            self._ask = None
            self._bid_depth = None
            self._ask_depth = None

        def on_message(self, message):
            super(OrderBookConsole, self).on_message(message)

            # Calculate newest bid-ask spread
            bid = self.get_bid()
            bids = self.get_bids(bid)
            bid_depth = sum([b['size'] for b in bids])
            ask = self.get_ask()
            asks = self.get_asks(ask)
            ask_depth = sum([a['size'] for a in asks])

            if self._bid == bid and self._ask == ask and self._bid_depth == bid_depth and self._ask_depth == ask_depth:
                # If there are no changes to the bid-ask spread since the last update, no need to print
                pass
            else:
                # If there are differences, update the cache
                self._bid = bid
                self._ask = ask
                self._bid_depth = bid_depth
                self._ask_depth = ask_depth
                print('{} {} bid: {:.3f} @ {:.2f}\task: {:.3f} @ {:.2f}'.format(
                    dt.datetime.now(), self.product_id, bid_depth, bid, ask_depth, ask))

    order_book = OrderBookConsole()
    order_book.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        order_book.close()

    if order_book.error:
        sys.exit(1)
    else:
        sys.exit(0)

