from AlgorithmImports import *
import math
from collections import deque
from HelperFuncs import *
from functools import wraps
import pandas as pd
import numpy as np
from Custom import create_dict
from QuantConnect.Data.Consolidators import CalendarInfo


class DataClass:

    def __init__(self, Algorithm, continuous_contract,customData=None):
        
        self.algo = Algorithm # This is Our Instance of QCAlgorithm
        self.continuous_contract = continuous_contract
        self.Symbol = self.continuous_contract.Symbol 
        self.tradePriceUpdated = False

        #custom data
        self.customData=customData
        #check if there is custom data for security
        if self.customData:
            #dict to hold custom data points
            self.customDataDict={}
            
            #create empty key for each security value is none for all
            # dict values are updated in Update function below
            for custom in self.customData:
                self.customDataDict[str(custom)]=None

        # Contract Properties
        self.tickSize = self.continuous_contract.SymbolProperties.MinimumPriceVariation

        # Bids, Asks, Trade Prices for both Mapped & Continuous        
        self._bestBidContinuous = dotdict(dict.fromkeys(['time', 'price', 'size']))
        self._bestBidMapped = dotdict(dict.fromkeys(['time', 'price', 'size']))

        self._bestAskContinuous = dotdict(dict.fromkeys(['time','price', 'size']))
        self._bestAskMapped = dotdict(dict.fromkeys(['time','price', 'size']))

        self._tradeContinuous = dotdict(dict.fromkeys(['time','price', 'size']))
        self._tradeMapped = dotdict(dict.fromkeys(['time','price', 'size']))

        self._WAPMapped = None            
        self._yesterdayPercentChange = {}
        self.RollingYesterdayPercentChange = deque(maxlen=6*60*60) # 6 hours * 60 minutes * 60 seconds

        # Market Timings
        self._currentOpen = None
        self._currentClose = None
        self._nextOpen = None

        # Indicators
        self.atrPeriod = 2
        self._ContinuousATR = AverageTrueRange(self.atrPeriod, MovingAverageType.Simple) 
        self._MappedATR = AverageTrueRange(self.atrPeriod, MovingAverageType.Simple)

        self._ContinuousMA2 = SimpleMovingAverage(2)
        self._MappedMA2 = SimpleMovingAverage(2)
        self._MappedYesterday = SimpleMovingAverage(1)
        self._ContinuousYesterday = SimpleMovingAverage(1)

        # History DFs - Using so only call History when not already called before for other Indicators
        self.mappedTradeDailyHistory = None
        self.mappedTradeHistory = None        
        self.continuousDailyHistory = None
        self.continuousHistory = None
        
        # Schedulers

        # Update Yesterday Price 10 minutes before Market Opens - Can even use 'LBS' in TimeRules.AfterMarketOpen
        self.algo.Schedule.On(self.algo.DateRules.EveryDay(self.Symbol), self.algo.TimeRules.AfterMarketOpen(self.Symbol, -10), self.updateDailyIndicators)
        
        # Reset BBO dicts 10 minutes after market close
        self.algo.Schedule.On(self.algo.DateRules.EveryDay(self.Symbol), self.algo.TimeRules.BeforeMarketClose(self.Symbol, -10), self.resetTickDict)

        # Capture Nasdaq %age Change before Lumber Opens  
        # self.algo.Schedule.On(self.algo.DateRules.EveryDay(self.Symbol), self.algo.TimeRules.At(9,59,51),self.updateRollingSeries)
        # Capture %age Change for Nasdaq & Lumber during Lumber Market Hours
        # self.algo.Schedule.On(self.algo.DateRules.EveryDay(self.Symbol), self.algo.TimeRules.Every(timedelta(seconds=1)),self.updateRollingSeries)

        # Calls the property (self.tradeContinuous/tradeMapped) everytime there is a trade so as to update it. 
        self.tradeEvent = TickConsolidator(1)
        self.tradeEvent.DataConsolidated += self.updateTradePrice
        # Not sure if using self.Symbol will only show Trades for front Month or for all Mapped symbols
        self.algo.SubscriptionManager.AddConsolidator(self.Symbol, self.tradeEvent)

    # Change to self.tradeMapped once we find a better way to calculate it rather than using History
    def updateTradePrice(self, sender: object, Tbar: TradeBar) -> None:
        if self.algo.Time < self.algo.signalStartTime or self.algo.Time > self.algo.signalEndTime: return                
        
        self.tradePriceUpdated = True
        self._yesterdayPercentChange = {}
        # self.tradeMapped
        self.tradeContinuous

    @property
    def yesterdayPercentChange(self):
        if self.algo.Time < self.algo.signalStartTime or self.algo.Time > self.algo.signalEndTime: return    

        # Change self._tradeContinuous with self._tradeMapped once we have more efficient way to get self._tradeMapped rather than using History
        # Can use continuous incase using DataNormalizationMode.Raw
        if None not in (self._tradeContinuous.price,self._MappedYesterday.Current.Value) and self.tradePriceUpdated:
            self._yesterdayPercentChange[self._tradeContinuous.time] = round(((self._tradeContinuous.price - self._MappedYesterday.Current.Value)/self._MappedYesterday.Current.Value)*100,2)                   
            self.tradePriceUpdated = False # Ensures that unless new Trade value is updated in UpdateTradePrice func, no need to recalculate
        return self._yesterdayPercentChange        
    
    # To be removed - but first see all other varibles, their uses etc. Compare output with the One in AlphaModel etc. 
    # Moved to Alpha Model - call it updateModelData or percentChangeSeconds
    def updateRollingSeries(self):  

        # self.yesterdayPercentChange only updates during Lumber hours but the above statement is used for 'else' below:
        if self.yesterdayPercentChange:
            
            # Capctures only when data available
            self.RollingYesterdayPercentChange.appendleft(self._yesterdayPercentChange)                                 
            
            # Captures every Second
            self.algo.percentChangeDF.loc[self.algo.Time,self.Symbol] = list(self._yesterdayPercentChange.values())[0]            
            self.algo.Debug(f"{self.algo.Time}:{self.algo.percentChangeDF.tail(1)}")
            
            # Get Latest RollingYesterdayPercentChange fo respective Symbols - only updates when yesterdayPercentChange exists for a symbol
            self.algo.Debug(f"##{self.algo.Time}:{self.Symbol}:{self.RollingYesterdayPercentChange[0]}")
            self.algo.Debug(f"***{self.algo.Time}:{self.Symbol}:{list(self.RollingYesterdayPercentChange[0].values())[0]}")

            # Max, Min and rolling Max for RollingYesterdayPercentChange
            # self.algo.Debug(f"MAX{self.algo.Time}:{self.Symbol}:{max(max(d.values()) for d in self.RollingYesterdayPercentChange)}")           
            # Find the maximum value over the last n data points (in this case, n=3)
            # max_n_value = max(max(d.values()) for d in list(self.RollingYesterdayPercentChange)[:3])
            # self.algo.Debug(f"MIN{self.algo.Time}:{self.Symbol}:{min(min(d.values()) for d in self.RollingYesterdayPercentChange)}")

            # To Do Adjustments to percentChangeDF    
            # self.algo.percentChangeDF= self.algo.percentChangeDF.fillna(method='ffill')
            # corr = self.algo.percentChangeDF['/NQ'].corr(self.algo.percentChangeDF['/LBS'])
            # self.algo.Debug(f"{self.algo.Time}:Correlation{corr}")


        




    # Gets Updated from main
    def Update(self, data):

        # below code updates the custom data dict for particulat data 
        
        #check if custom data is avaliable for security
        if self.customData:
            # Iterate through custom data list
            for key in self.customData:
               #check if data contains particular custom data symbol
               if data.ContainsKey(key):

                    #check if there is any earlier update in custom data dict for this custom symbol
                    if self.customDataDict[str(key)] == None:
                        #set last to None
                        last=None
                    
                    else:
                        #set last to current data in dict
                        last=self.customDataDict[str(key)]["data"]
                    
                    # update the dict with new data
                    # value for dict contains a dict with 
                    # update_at:time at which data is received
                    # data:updated data point for symbol
                    # last:previous data point for symbol
                    self.customDataDict[str(key)]={"updated_at":self.algo.Time,"data":create_dict(data[key]), "last":last }
                    self.algo.Debug(f"{self.customDataDict}")

        if data.SymbolChangedEvents.ContainsKey(self.Symbol):
            # Reset ONLY Mapped Indicators (ones based on Mapped contracts) - This will load History when contract switches
            self._MappedATR.Reset() 
            self._MappedMA2.Reset() 
            self._MappedYesterday.Reset() 
            
            # NOT letting register New Symbol - asking to subscribe to it first.
            # symbolChangedEvent = data.SymbolChangedEvents[self.Symbol]
            # self.algo.SubscriptionManager.AddConsolidator(symbolChangedEvent.NewSymbol, self.tradeEvent)
            # self.algo.SubscriptionManager.RemoveConsolidator(symbolChangedEvent.OldSymbol, self.tradeEvent)
        
        # if self.algo.Time <= self.algo.signalStartTime or self.algo.Time >= self.algo.signalEndTime: return


    @property
    def ATR(self):
        # self.algo.Debug(f"self._MappedATR.IsReady:{self._MappedATR.IsReady} at {self.algo.Time}")
        # self.algo.Debug(f"# of samples{self._MappedATR.Samples}")
        return self._MappedATR.Current.Value


    # Resetting Best Bid/Ask at MarketClose
    def resetTickDict(self):

        # 10 minutes after close
        # NG - 17:10 on 27th (Start date on 26th) 
        # LBS - 16:15 on 27th (Start date on 26th)
        # self.algo.Debug(f"symbol:{self.Symbol},{self.algo.Time}")

        # Emoty the deque
        self.RollingYesterdayPercentChange = deque(maxlen=6*60*60) # 6 hours * 60 minutes * 60 seconds
        
        self._bestAskContinuous = self._bestAskContinuous.fromkeys(self._bestAskContinuous, None)
        self._bestBidContinuous = self._bestBidContinuous.fromkeys(self._bestBidContinuous, None)

        self._bestAskMapped = self._bestAskMapped.fromkeys(self._bestAskMapped, None)
        self._bestBidMapped = self._bestBidMapped.fromkeys(self._bestBidMapped, None)

        self._tradeContinuous = self._tradeContinuous.fromkeys(self._tradeContinuous, None)
        self._tradeMapped = self._tradeMapped.fromkeys(self._tradeMapped, None)

        self._WAPMapped = None
        self._yesterdayPercentChange = {}

        self._currentOpen = None
        self._currentClose = None
        self._nextOpen = None
        

    def getMappedTradeHistory(self,days):
        history = self.algo.History[TradeBar](self.Mapped, days, Resolution.Daily)
        # https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/rolling-window#09-Cast-to-Other-Types
        return self.algo.PandasConverter.GetDataFrame[TradeBar](list(history)) 


    def getContinuousHistory(self,days):
        return self.algo.History(tickers=[self.Symbol], 
        start=self.startBDate(self.algo.Time,days).date(), # Using self.startBDate since if we simply use startdate minus timedelta(self.atrperiod), it doesn't keep holidays in count
        end=self.algo.Time,
        resolution=Resolution.Daily, 
        fillForward=True, 
        extendedMarket=True, 
        dataMappingMode=DataMappingMode.FirstDayMonth,
        dataNormalizationMode = self.algo.DataNormalizationMode, # Got this from Main
        contractDepthOffset=0)


    def updateDailyIndicators(self):        
        
        # NG - 9:20 on 27th (Start date on 26th)
        # LBS - 9:50 on 27th (Start date on 26th)
        # self.algo.Debug(f"symbol:{self.Symbol},{self.algo.Time}")

        # Resetting Every Day
        self.mappedTradeDailyHistory = None
        self.mappedTradeHistory = None        
        self.continuousDailyHistory = None
        self.continuousHistory = None
        
        self.updateDailyMappedIndicators(indicator = self._MappedATR, period = self.atrPeriod+1, updateType =  'TradeBar')        
        self.updateDailyMappedIndicators(indicator = self._MappedYesterday, period = 1, updateType = 'DailyClose')
        self.updateDailyMappedIndicators(indicator = self._MappedMA2, period = 2, updateType = 'DailyClose')
        
        self.updateDailyContinuousIndicators(indicator = self._ContinuousATR, period = self.atrPeriod+1, updateType =  'TradeBar')
        self.updateDailyContinuousIndicators(indicator = self._ContinuousMA2, period = 2, updateType = 'DailyClose')       
        self.updateDailyContinuousIndicators(indicator = self._ContinuousYesterday, period = 1, updateType = 'DailyClose') 


    def updateDailyMappedIndicators(self, indicator, period, updateType): 
        
        # MAPPED INDICATORS 
        if self.Mapped is not None:
            # ATR Update - # All Manual Indicators Updated Manually Here
            if not indicator.IsReady: # Runs (1) At start (2) When contract Rolls
                if self.mappedTradeHistory is None or len(self.mappedTradeHistory) < period:
                    self.mappedTradeHistory = self.getMappedTradeHistory(days = period)                
                
                mappedTradeHistory_ = self.mappedTradeHistory[-period:]
                
                for bar in mappedTradeHistory_.itertuples():
                    if updateType == 'TradeBar':
                        tradebar = TradeBar(bar.Index[1], self.Mapped, float(bar.open), float(bar.high), float(bar.low), float(bar.close), float(bar.volume))
                        # self.algo.Debug(f"Bar1:{tradebar} @ {bar.Index[1]}")
                        indicator.Update(tradebar)
                        # self.algo.Debug(f"1stManual:{tradebar},{bar.Index[1]}")
                    elif updateType == 'DailyClose':
                        indicator.Update(bar.Index[1], bar.close)

            else: # Indicator is ready so just updating it for the day.   
                if self.mappedTradeDailyHistory is None or self.mappedTradeDailyHistory.empty:
                    self.mappedTradeDailyHistory = self.getMappedTradeHistory(days = 1) 
                               
                for bar in self.mappedTradeDailyHistory.itertuples():   
                    if updateType == 'TradeBar':                 
                        tradebar = TradeBar(bar.Index[1], self.Mapped, float(bar.open), float(bar.high), float(bar.low), float(bar.close), float(bar.volume))
                        indicator.Update(tradebar)
                        # self.algo.Debug(f"2ndManual:{tradebar},{bar.Index[1]}")
                    elif updateType == 'DailyClose':
                        indicator.Update(bar.Index[1], bar.close)
                        

    def updateDailyContinuousIndicators(self, indicator, period, updateType): 

        # CONTINUOUS INDICATORS
        if self.Symbol is not None:

            # ATR Update - # All Manual Indicators Updated Manually Here
            if not indicator.IsReady: # Runs (1) At start OnLY     
                if self.continuousHistory is None or len(self.continuousHistory) < period:
                    self.continuousHistory = self.getContinuousHistory(days=period)
                
                continuousHistory_ = self.continuousHistory[-period:]

                for bar in continuousHistory_.itertuples(): 
                    if updateType == 'TradeBar':
                        tradebar = TradeBar(bar.Index[2], bar.Index[1], float(bar.open), float(bar.high), float(bar.low), float(bar.close), float(bar.volume))
                        indicator.Update(tradebar)
                    elif updateType == 'DailyClose':
                        indicator.Update(bar.Index[2], bar.close)
                        
                    # self.algo.Debug(f"1stAuto:{tradebar},{bar.Index[2]}")


            else: # Indicator is ready so just updating it for the day.     
                if self.continuousDailyHistory is None or self.continuousDailyHistory.empty:
                    self.continuousDailyHistory = self.getContinuousHistory(days=1)                            
                
                for bar in self.continuousDailyHistory.itertuples():
                    if updateType == 'TradeBar':
                        # self.algo.Debug(f"2ndAuto:{tradebar},{bar.Index[2]}")
                        tradebar = TradeBar(bar.Index[2], bar.Index[1], float(bar.open), float(bar.high), float(bar.low), float(bar.close), float(bar.volume))
                        indicator.Update(tradebar)
                    elif updateType == 'DailyClose':
                        indicator.Update(bar.Index[2], bar.close)


    @property
    def bestBidMapped(self):

        # Only updating if Bid price and Size changed so as to keep the original Time of last update
        if int(getattr(self.algo.Securities[self.Mapped], 'BidSize')) != 0 and not self.alreadyUpdated('BidPrice', 'BidSize', self._bestBidMapped):
            for key,prop in zip(list(self._bestBidMapped.keys()),['LocalTime','BidPrice', 'BidSize']):
                setattr(self._bestBidMapped,str(key),getattr(self.algo.Securities[self.Mapped], prop))

        return self._bestBidMapped


    @property
    def bestAskMapped(self):        
        # Only updating if Ask price and Size changed so as to keep the original Time of last update
        if int(getattr(self.algo.Securities[self.Mapped], 'AskSize')) != 0 and not self.alreadyUpdated('AskPrice', 'AskSize', self._bestAskMapped):
            for key,prop in zip(list(self._bestAskMapped.keys()),['LocalTime','AskPrice', 'AskSize']):
                setattr(self._bestAskMapped,str(key),getattr(self.algo.Securities[self.Mapped], prop))
        return self._bestAskMapped

    
    @property
    def bestBidContinuous(self):
        # Only updating if Bid price and Size changed so as to keep the original Time of last update
        if int(getattr(self.algo.Securities[self.Symbol], 'BidSize')) != 0 and not self.alreadyUpdated('BidPrice', 'BidSize', self._bestBidContinuous):
            for key,prop in zip(list(self._bestBidContinuous.keys()),['LocalTime','BidPrice', 'BidSize']):
                if key == 'price':
                    setattr(self._bestBidContinuous,str(key),round(getattr(self.algo.Securities[self.Symbol], prop),1))
                else:
                    setattr(self._bestBidContinuous,str(key),getattr(self.algo.Securities[self.Symbol], prop))
        return self._bestBidContinuous



    @property
    def bestAskContinuous(self):       
        # Only updating if Ask price and Size changed so as to keep the original Time of last update
        if int(getattr(self.algo.Securities[self.Symbol], 'AskSize')) != 0 and not self.alreadyUpdated('AskPrice', 'AskSize', self._bestAskContinuous):
            for key,prop in zip(list(self._bestAskContinuous.keys()),['LocalTime','AskPrice', 'AskSize']):
                if key == 'price':
                    setattr(self._bestAskContinuous,str(key),round(getattr(self.algo.Securities[self.Symbol], prop),1))
                else:
                    setattr(self._bestAskContinuous,str(key),getattr(self.algo.Securities[self.Symbol], prop))
        return self._bestAskContinuous

   
    @property
    def tradeContinuous(self):        
        if self.algo.CurrentSlice.Ticks.ContainsKey(self.Symbol) and self.algo.CurrentSlice.Ticks[self.Symbol] is not None:
            ticks = self.algo.CurrentSlice.Ticks[self.Symbol]
            for tick in ticks:
                tick_type = getTickType(tick.TickType)
                if tick_type == 'Trade' and int(getattr(tick, 'Quantity')) != 0 and int(getattr(tick, 'Price')) is not None:
                    for key,prop in zip(list(self._tradeContinuous.keys()),['Time','Price','Quantity']):
                        if key == 'price':
                            setattr(self._tradeContinuous,str(key),round(getattr(tick, prop),1))
                        else:
                            setattr(self._tradeContinuous,str(key),getattr(tick, prop))
                else:
                    pass
        return self._tradeContinuous

    @property
    def tradeMapped(self):

        # Keep these seconds equal to scheduler ??
        # history = self.algo.History[Tick](self.Mapped, timedelta(seconds=60), Resolution.Tick)

        history = self.algo.History[Tick](self.Mapped, timedelta(microseconds=1), Resolution.Tick)
        history = self.algo.PandasConverter.GetDataFrame[Tick](list(history)) 
        for bar in history.itertuples():
            if hasattr(bar,'quantity'):
                if getattr(bar,'quantity') >= 1:
                    self._tradeMapped['time'] = bar.Index[1].to_pydatetime().strftime('%Y-%m-%d %H:%M:%S.%f')
                    self._tradeMapped['price'] = bar.lastprice
                    self._tradeMapped['size'] = bar.quantity

        return self._tradeMapped


    @property
    def WAPMapped(self):
        if None not in (self.bestAskMapped.size,self.bestBidMapped.size):
            self._WAPMapped = round(((self.bestBidMapped.price * self.bestAskMapped.size) + (self.bestAskMapped.price * self.bestBidMapped.size))/(self.bestBidMapped.size + self.bestAskMapped.size),1)
            
        return self._WAPMapped


    @property
    def currentOpen(self):
        marketHoursString = str(self.algo.Securities[self.Mapped].Exchange.Hours.GetMarketHours(self.algo.Time))
        marketOpenString = marketHoursString.split("Market: ")[2].split(" | ")[0].split("-")[0].strip()
        marketOpen = datetime.strptime(marketOpenString, '%H:%M:%S').time()
        # Added extra hour to Make it work with NewYork Time/ Algorithm Time
        self._currentOpen = datetime.combine(self.algo.Time.date(),marketOpen) + timedelta(hours=1) 
        return self._currentOpen 

    @property
    def currentClose(self):
        marketHoursString = str(self.algo.Securities[self.Mapped].Exchange.Hours.GetMarketHours(self.algo.Time))
        marketCloseString = marketHoursString.split("Market: ")[2].split(" | ")[0].split("-")[1].strip()
        marketClose = datetime.strptime(marketCloseString, '%H:%M:%S').time()
        # Added extra hour to Make it work with NewYork Time/ Algorithm Time
        self._currentClose = datetime.combine(self.algo.Time.date(),marketClose) + timedelta(hours=1)     
        return self._currentClose 


    # @property
    # def currentOpen(self):
    #     hours = self.algo.Securities[self.Mapped].Exchange.Hours
    #     # Added extra hour to Make it work with NewYork Time/ Algorithm Time
    #     # False is for not including extended Market Hours
    #     self._currentOpen = hours.GetNextMarketOpen(self.algo.Time + timedelta(hours=24), False) + timedelta(hours=1) 
    #     return self._currentOpen  # 
    

    # Needs to be Checked
    @property
    def nextOpen(self):
        hours = self.algo.Securities[self.Mapped].Exchange.Hours
        # Added extra hour to Make it work with NewYork Time/ Algorithm Time
        self._nextOpen = hours.GetNextMarketOpen(self.algo.Time, False) + timedelta(hours=1) 
        return self._nextOpen  # 


    # RealOnly RealTime 
    @property
    def Mapped(self):
        return getattr(self.continuous_contract, 'Mapped')

    @property
    def Canonical(self):
        return getattr(self.Symbol, 'Canonical')


    @property
    def custom(self):
        if self.customData:
            return self.customDataDict
        else:
            return None
    # @property
    # def timezone(self):
    #     return self.algo.MarketHoursDatabase.GetDataTimeZone(Market.CME, self.Symbol, SecurityType.Future)


    # Genric Functions - Combine both together
    def businessDay(self,dt):
        return 1 if getattr(self.algo.TradingCalendar.GetTradingDay(dt),'BusinessDay') else 0
    
    def startBDate(self,end_dt, lag):  
        count = 0      
        start_dt = end_dt 
        while count!= lag:
            start_dt -= timedelta(days=1)
            count += self.businessDay(start_dt)
        return start_dt
    
    
    # This is not entirely correct as someone may have canceled and others may have added a bid with net being affect 0 
    def alreadyUpdated(self, price, size, dictionary):
        return getattr(self.algo.Securities[self.Mapped], price) == dictionary.price and getattr(self.algo.Securities[self.Mapped], size) == dictionary.size
        

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

