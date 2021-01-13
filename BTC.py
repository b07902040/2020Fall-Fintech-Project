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
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 20 * 60
        self.options = {}

        # user defined class attribute
        self.close_price_trace = np.array([])
        self.RSIN_short = 6
        self.RSIN_long = 30
        self.multi = 0.5
        self.low_buy_point = 15
        self.high_sell_point = 85
        self.last_RSI6_status = 0
        self.last_RSI12_status = 0
        self.count_turn = 0
        self.first_exchange = 0
        self.last_RSI6 = -1
        self.last_RSI12 = -1
    
    def init_RSI_status(self, RSI):
        if RSI < self.low_buy_point:
            return 1 #'<low'
        elif RSI < 50:
            return 2 #'low<RSI<50'
        elif RSI < self.high_sell_point:
            return 3 #'50<RSI<high'
        elif RSI >= self.high_sell_point:
            return 4 #'>high'
        else:
            return 0 #'none'

    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-31:]

        self.count_turn += 1
        if self.count_turn < (self.RSIN_long+1):
            return []
        RSI6 = talib.RSI(self.close_price_trace, timeperiod=self.RSIN_short)[-1]
        #Log("RSI6= " + str(RSI6))
        RSI12 = talib.RSI(self.close_price_trace, timeperiod=self.RSIN_long)[-1]
        #Log('RSI12=' + str(RSI12))
        # buying : RSI 6和RSI 12同在50下方且一起上涨时，RSI 6向上突破RSI 12。
        if (RSI6 < 50) and (RSI12 < 50) and (self.last_RSI12 > self.last_RSI6) and (RSI6 > RSI12) and (self.last_RSI6 < RSI6) and (self.last_RSI12 < RSI12):
            if self['assets'][exchange]['USDT'] >= 4*self.multi*close_price && self['assets'][exchange]['USDT'] >= 10000:
                self.first_exchange = 1
                return [
                    {
                        'exchange': exchange,
                        'amount': 4*self.multi,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
        # selling : RSI 6和RSI 12同在50上方且一起下跌时，RSI 6跌破RSI 12。
        elif (RSI6 > 50) and (RSI12 > 50) and (self.last_RSI12 < self.last_RSI6) and (RSI6 < RSI12) and (self.last_RSI6 > RSI6) and (self.last_RSI12 > RSI12):
            self.first_exchange = 1
            return [
                {
                    'exchange': exchange,
                    'amount': -4*self.multi,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # buying
        elif (RSI6 < self.low_buy_point) and (self.last_RSI6_status >= 2) :
            if self['assets'][exchange]['USDT'] >= 1*self.multi*close_price && self['assets'][exchange]['USDT'] >= 10000:
                self.last_RSI6_status = 1
                self.first_exchange = 1
                #Log('bying' + exchange + ':' + pair + 'in RSI6=' + str(RSI6))
                return [
                    {
                        'exchange': exchange,
                        'amount': 1*self.multi,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else :
                return []
        
        elif (RSI6 > self.low_buy_point) and (self.last_RSI6_status == 1) :
            if self['assets'][exchange]['USDT'] >= 2*self.multi*close_price && self['assets'][exchange]['USDT'] >= 10000:
                self.last_RSI6_status = 2
                self.first_exchange = 1
                #Log('bying' + exchange + ':' + pair + 'in RSI6=' + str(RSI6))
                return [
                    {
                        'exchange': exchange,
                        'amount': 2*self.multi,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else :
                return []

        # selling
        elif (RSI6 > self.high_sell_point) and (self.last_RSI6_status <= 3):
            if self['assets'][exchange]['BTC'] >= 1*self.multi:
                self.last_RSI6_status = 4
                self.first_exchange = 1
                #Log('selling' + exchange + ':' + pair + 'in RSI6=' + str(RSI6))
                return [
                    {
                        'exchange': exchange,
                        'amount': -1*self.multi,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else:
                return []

        elif (RSI6 < self.high_sell_point) and (self.last_RSI6_status == 4):
            if self['assets'][exchange]['BTC'] >= 2*self.multi:
                self.last_RSI6_status = 3
                self.first_exchange = 1
                #Log('selling' + exchange + ':' + pair + 'in RSI6=' + str(RSI6))
                return [
                    {
                        'exchange': exchange,
                        'amount': -2*self.multi,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            else:
                return []
        
        if self.first_exchange is 0:
            self.last_RSI6_status = self.init_RSI_status(RSI6)
            self.last_RSI12_status = self.init_RSI_status(RSI12)
        self.last_RSI6 = RSI6
        self.last_RSI12 = RSI12
        #Log('not exchange')
        return []
