import backtrader as bt
import pandas as pd
import datetime
import yfinance as yf

#customized indicator: set upper bound for breakout signal
class UpDownBars(bt.Indicator):
    lines = ("up","down")
    
    def __init__(self):
        self.addminperiod(4)
        self.plotinfo.plotmaster = self.data
    
    def next(self):
        self.up[0] = max(max(self.data.close.get(ago = -1,size = 3)),max(self.data.open.get(ago = -1,size = 3)))
        #self.down[0] = min(min(self.data.close.get(ago = -1,size = 3)),min(self.data.open.get(ago = -1,size = 3)))  

class Rebalance(bt.Strategy):
    params = (('Pct',0.1),('Tickers',[]))

    def __init__(self) -> None:
        self.up_down = UpDownBars(self.data)
        
        #add indicators to each data feed
        self.ud_inds = dict()
        for d in self.datas:
            up = bt.indicators.CrossOver(d,self.up_down.up)
            #down = bt.indicators.CrossDown(d,self.up_down.down)
            self.ud_inds[d] = dict()
            self.ud_inds[d]["up"] = up
            #self.ud_inds[d]["down"] = down
            
    def nextstart(self):
        # Buy the available cash
        print("set cash!")
        print(self.data)
        #self.order_target_value(target=self.broker.get_cash())
    
    def next(self):
        #go buy if signal is triggered
        for d in self.datas:
            if self.ud_inds[d]["up"]:
                self.order = self.buy(data=d)
        
        #rebalance portfolio
        today = self.data.datetime.date()
        year, month = today.year,today.month
        if month == 12:
            this_month_length = (datetime.datetime(year+1,1,1) - datetime.datetime(year,month,1)).days
        else:
            this_month_length = (datetime.datetime(year,month + 1,1) - datetime.datetime(year,month,1)).days
            
        if today.day == this_month_length:
            for d in self.datas:
                self.order_target_percent(target=self.p.Pct,data=d)
     
    #print out stats at the end           
    def stop(self):
        print("Pct: {}, Value: {},Cash: {}".format(self.p.Pct,self.broker.getvalue(),self.broker.get_cash()))
    
#download data and save down as csv
def Downloads(tickers,start,end):
    for ticker in tickers:
        data = yf.download(ticker,start,end)
        data.index = pd.to_datetime(data.index)
        data.to_csv("./StockData/{}.csv".format(ticker))

if __name__ == '__main__':
    tickers = ["NVDA","AMZN","AMD","META","SE","SHOP","TSLA","SPYD"]
    pct= 1/(len(tickers))
    
    Downloads(tickers,'2018-01-01','2022-06-01')

    cerebro = bt.Cerebro()
    cerebro.addsizer(bt.sizers.PercentSizer,percents=90)
    cerebro.addstrategy(Rebalance,Tickers=tickers,Pct = pct)
    #cerebro.optstrategy(Rebalance,Pct = [x/10 for x in range(len(tickers))])
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.Cash)
    
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)
    # cerebro.addanalyzer(bt.analyzers.TimeReturn,fund=True)
    
    cerebro.addwriter(bt.WriterFile,csv=True,out="rebalance_result.csv")
    
    for ticker in tickers:
        data = pd.read_csv("./StockData/{}.csv".format(ticker),index_col="Date",parse_dates=True)
        datafeed = bt.feeds.PandasData(dataname = data)
        cerebro.adddata(datafeed,name = ticker)
        
    cerebro.run()
    print("Value: ",cerebro.broker.get_value())
    cerebro.plot(volume=False)
    
    
    
    
    
    