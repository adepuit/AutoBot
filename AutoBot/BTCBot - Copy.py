import time
import AutoBot

#wsClient = gdax.WebsocketClient(url="wss://ws-feed.gdax.com", products="BTC-USD", channels=["ticker"])

#wsClient.start()

order_book = AutoBot.AutoBot(product_id='BTC-USD')
order_book.start()
input("Press Enter to end...\n")
order_book.close()