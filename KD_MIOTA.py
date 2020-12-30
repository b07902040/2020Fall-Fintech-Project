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
            'Bitfinex': {
                'pairs': ['MIOTA-USDT'],
            },
        }
        self.period = 8 * 60 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = 2
        self.close_price_trace = np.array([])
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.RSIlist = np.array([])
        self.buypoint = 0
        self.ma_long = 50
        self.ma_short = 5
        self.K_long = 14
        self.K = 50
        self.D = 0
        self.RSI = 5
        self.l_ma = None
        self.UP = 1
        self.DOWN = 2
        self.last_buy = 0
        self.amount = 0


    def get_RSI(self):
        rsi = talib.RSI(self.close_price_trace, self.RSI)[-1]
        if np.isnan(rsi):
            return None
        return rsi

    def get_KD(self):
        if self.close_price_trace.shape[0] < self.K_long:
            return None
        # Log('minmax:' + str(min(self.low_price_trace[-self.K_long:])) + ',' + str(max(self.high_price_trace[-self.K_long:])))
        rsv = (self.close_price_trace[-1] - min(self.low_price_trace[-self.K_long:]))/(max(self.high_price_trace[-self.K_long:]) - min(self.low_price_trace[-self.K_long:]))*100.
        # rsv = max(0., rsv)
        # rsv = min(100., rsv)
        self.K = self.K*2/3 + rsv*1/3
        self.D = self.D*2/3 + self.K*1/3
        if self.K > self.D:
            return self.UP
        else:
            return self.DOWN

    def isOverGood(self):
        cnt = 0
        if self.RSIlist.shape[0] < 3:
            return False
        for i in range(1, 6):
            if self.RSIlist[-i] > 70:
                cnt += 1
        if cnt > 2:
            return True
        else:
            return False

    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        high_price = information['candles'][exchange][pair][0]['high']
        low_price = information['candles'][exchange][pair][0]['low']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        self.high_price_trace = np.append(self.high_price_trace, [float(high_price)])
        self.high_price_trace = self.high_price_trace[-self.K_long:]
        self.low_price_trace = np.append(self.low_price_trace, [float(low_price)])
        self.low_price_trace = self.low_price_trace[-self.K_long:]
         
        # calculate current ma cross, RSI status
        cur_cross = self.get_KD()
        cur_RSI = self.get_RSI()

        if cur_RSI is not None:
            self.RSIlist = np.append(self.RSIlist, [cur_RSI])
            self.RSIlist = self.RSIlist[-self.ma_long:]

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['MIOTA']))
        # Log(str(float(low_price)) + ',' + str(float(high_price)) + ',' + str(float(close_price)))
        Log('KD:' + str(self.K) + ',' + str(self.D))
        Log('RSI:' + str(cur_RSI))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # cross up
        if cur_cross == self.UP and self.last_cross_status == self.DOWN:
            amount = self['assets'][exchange]['USDT'] * 0.5 / information['candles'][exchange][pair][0]['close']
            if cur_RSI is not None:
                if cur_RSI > 70:
                    amount *= 0.5
            Log('buying for KD, ' + exchange + ':' + pair)
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.amount += amount
            self.last_buy = self.close_price_trace[-1]
            return [
                {
                    'exchange': exchange,
                    'amount': amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            
        # cross down
        elif self['assets'][exchange]['MIOTA'] > 0 and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            if cur_RSI is not None:
                if cur_RSI < 30:
                    amount = self['assets'][exchange]['MIOTA'] * 0.5
                else:
                    amount = self['assets'][exchange]['MIOTA']
            Log('selling for KD, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            self.amount -= amount
            self.last_buy = 0
            return [
                {
                    'exchange': exchange,
                    'amount': -1*amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            
        elif self.last_buy != 0 and self.amount > 0:
            if (self.close_price_trace[-1] - self.last_buy) / self.last_buy * 1.0 < -2.0/100:
                Log('selling for bad market, ' + exchange + ':' + pair)
                self.last_type = 'sell'
                self.last_cross_status = cur_cross
                self.amount = 0
                self.last_buy = 0
                return [
                    {
                        'exchange': exchange,
                        'amount': -1*self['assets'][exchange]['MIOTA'],
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            if (self.close_price_trace[-1] - self.last_buy) / self.last_buy * 1.0 > 2.0 and self.isOverGood():
                Log('selling for good market, ' + exchange + ':' + pair)
                self.last_type = 'sell'
                self.last_cross_status = cur_cross
                self.amount = 0
                self.last_buy = 0
                return [
                    {
                        'exchange': exchange,
                        'amount': -1*self['assets'][exchange]['MIOTA'],
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
        self.last_cross_status = cur_cross
        return []
