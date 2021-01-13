class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 5*60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.last_close_price = 0.0
        self.close_price_trace = np.array([])
        self.ma_long = 100
        self.ma_middle = 50
        self.ma_short = 4
        self.UP = 1
        self.DOWN = 2
        self.amount_per_trade = 30
        self.counter = 15


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        m_ma = talib.SMA(self.close_price_trace, self.ma_middle)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma) or np.isnan(m_ma):
            return None
        if s_ma < m_ma and m_ma < l_ma:
            return self.DOWN
        if s_ma > m_ma and m_ma > l_ma:
            return self.UP
        return None


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        targetCurrency = pair.split('-')[0]
        baseCurrency = pair.split('-')[1]

        baseCurrency_amount = self['assets'][exchange][baseCurrency]
        targetCurrency_amount = self['assets'][exchange][targetCurrency]

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        self.counter += 1


        # Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # down buy
        # Log('baseCur:'+str(baseCurrency_amount)+'after:'+str(baseCurrency_amount))
        if cur_cross == self.DOWN and (baseCurrency_amount-close_price*self.amount_per_trade)>20000 and self.counter>15:
            Log('buying, baseCurrency:' + str(baseCurrency_amount)+'targetCurrency:'+str(targetCurrency_amount))
            self.counter = 0
            self.last_type = 'buy'
            self.last_close_price = float(close_price)
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': self.amount_per_trade,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # up sell
        elif cur_cross == self.UP  and close_price > (1.03*self.last_close_price) and close_price*targetCurrency_amount>40000:
            Log('selling, baseCurrency:' + str(baseCurrency_amount)+'targetCurrency:'+str(targetCurrency_amount))
            self.counter = 0
            self.last_type = 'sell'
            self.last_close_price = 0.0
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -targetCurrency_amount/2,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
