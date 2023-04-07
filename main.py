from AlgorithmImports import *
from DataClass import *
from Alphas.NasdaqAlpha import *
from Alphas.OrderBookAlpha import *
from Alphas.BasisAlpha import *
from PortfolioConstruction import *
from DataModel import *
from Custom import *
import math 
import pandas as pd
from System.Drawing import Color
import pytz

class NasdaqStrategy(QCAlgorithm):


# To check if same Timings work for daylight savings: Note all the MarketOpen SignalStart and other hardcoded values 
# DayLight started on 13th March 


    def Initialize(self):

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        self.DefaultOrderProperties = InteractiveBrokersOrderProperties()
        
        # Order is valid until filled or the market closes
        # self.DefaultOrderProperties.TimeInForce = TimeInForce.Day
        # self.DefaultOrderProperties.OutsideRegularTradingHours = True
        
        # Set a Limit Order to be good until Lumber Close
        self.order_properties = OrderProperties()

        # self.SetStartDate(2023,2,15)        
        self.SetStartDate(2022,12,29)
        self.SetEndDate(2022,12,29)
        # self.SetEndDate(2023,1,5)
        self.SetCash(100000)
        
        self.DataNormalizationMode = DataNormalizationMode.Raw

        # TradeBuilder tracks the trades of your algorithm and calculates some statistics.
        # https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/trade-statistics
        tradeBuilder = TradeBuilder(FillGroupingMethod.FillToFill,FillMatchingMethod.FIFO)    
        self.SetTradeBuilder(tradeBuilder)

        #custom Lumber data
        # self.cash=self.AddData(Cash,"cash",Resolution.Daily).Symbol
        # self.western=self.AddData(Western,"western",Resolution.Daily).Symbol
        # self.settle=self.AddData(Settle,"Settle",Resolution.Daily).Symbol
        # self.disaggregated=self.AddData(Disaggregated,"disaggregated",Resolution.Daily).Symbol

        #custom data mapping dict using this to elminate if else statement
        # key=Symbol as in FuturesSymbol dict ,value=list of custom data
        # customMapping={"Lumber":[self.western],"Nasdaq":None}
        customMapping={"Lumber":None,"Nasdaq":None}

        self.Data = {}
        FutureSymbols = {'Lumber':Futures.Forestry.RandomLengthLumber,'Nasdaq':Futures.Indices.NASDAQ100EMini}
        # FutureSymbols = {'Lumber':Futures.Forestry.RandomLengthLumber}
        # FutureSymbols = {'Nasdaq':Futures.Indices.NASDAQ100EMini}
        
        for key, value in FutureSymbols.items():
            
            dataMappingMode_ = DataMappingMode.FirstDayMonth if key == 'Lumber' \
            else DataMappingMode.OpenInterest if key == 'Nasdaq' else DataMappingMode.LastTradingDay

            # Use BackwardsPanamaCanal or BackwardsRatio or Raw for DataNormalizationMode when "Trade" PROPERTY is able to map to Mapped contract
            future = self.AddFuture(value, Resolution.Tick,dataMappingMode = dataMappingMode_, contractDepthOffset=0, 
            dataNormalizationMode = self.DataNormalizationMode, extendedMarketHours=True, fillDataForward = True)
            
            # passing custom data to dataclass
            self.Data[key] = DataClass(self, future,customMapping[key]) # Initiating DataClass for each Future & Passing our instance of QCAlgorithm Class
        
        # Set alpha model - This also gives you access to the AlphaModel Instance 
        self.NasdaqAlpha     = NasdaqAlpha(self.Data)  # Also Pass the QCAlgorithmn Instance         
        self.OrderBookAlpha  = OrderBookAlpha(self.Data)
        self.BasisModel      = BasisAlpha(self.Data) 
        # self.ModelDataLumber = DataModel(self.Data)
        
        self.AddAlpha(self.NasdaqAlpha)
        # self.AddAlpha(self.OrderBookAlpha)
        # self.AddAlpha(self.BasisModel)

        # This is not an actual Alpha model but used to Update & Save data in Object store so we can access in research
        # self.AddAlpha(self.ModelDataLumber) 
        
        self.SetPortfolioConstruction(SourcePortfolioConstructionModel(self.Data))
        self.Settings.RebalancePortfolioOnInsightChanges = False
        self.Settings.RebalancePortfolioOnSecurityChanges = False

        self.SetExecution(ImmediateExecutionModel()) 

        # If I include Nasdaq, this should be on otherwise I get "Object reference not set to an instance of an object."
        # self.SetWarmUp(timedelta(days=1), Resolution.Tick)
        # self.SetWarmUp(timedelta(days=1), Resolution.Daily)
        
        # Printing Indicator's data 
        self.Schedule.On(self.DateRules.EveryDay(self.Data['Lumber'].Symbol), self.TimeRules.AfterMarketOpen(self.Data['Lumber'].Symbol, -1), self.beforeLumberOpen)        

        # Ideally signal Start & End Time should be picked up from self.Data['Lumber'].currentOpen & currentClose but they won't be initialised at this point
        # Algorithm starts calculating singal values between these 2 times everyday - Market doesn't accept orders 30 seconds b4 Market Open
        self.signalStartTimeDict = {'hour':9,'minute':59,'second':25,'microSecond':0}

        # But due to this we won't be able to view eod close data
        self.signalEndTimeDict = {'hour':16,'minute':5,'second':0,'microSecond':0}

        self.signalStartTime = self.Time.replace(hour=self.signalStartTimeDict['hour'], minute=self.signalStartTimeDict['minute'], second=self.signalStartTimeDict['second'], microsecond=self.signalStartTimeDict['microSecond'])
        self.signalEndTime   = self.Time.replace(hour=self.signalEndTimeDict['hour'], minute=self.signalEndTimeDict['minute'], second=self.signalEndTimeDict['second'], microsecond=self.signalEndTimeDict['microSecond'])

        self.SetTimeZone(TimeZones.NewYork)  # This is a daylight savings time zone.
        # If TimeZone is Chicago - Algo Time and Data End Time are same at 1800 hours
       
       # Remove this once verified
        self.percentChangeDF = pd.DataFrame()

        # Chart
        chart = Chart("NQ vs LBS")
        # How to Add both Index & Color to Series
        chart.AddSeries(Series(name = "Nasdaq", type = SeriesType.Line,  unit = '%', color = Color.Green))
        chart.AddSeries(Series(name = "Lumber", type = SeriesType.Line,  unit = '%', color = Color.Red))
        self.AddChart(chart)

        # Trading Related Global Variables
        self.maxContractLimit = 5


    def beforeLumberOpen(self):

        self.signalStartTime = self.Time.replace(hour=self.signalStartTimeDict['hour'], minute=self.signalStartTimeDict['minute'], second=self.signalStartTimeDict['second'], microsecond=self.signalStartTimeDict['microSecond'])
        self.signalEndTime   = self.Time.replace(hour=self.signalEndTimeDict['hour'], minute=self.signalEndTimeDict['minute'], second=self.signalEndTimeDict['second'], microsecond=self.signalEndTimeDict['microSecond'])

        # if self.IsWarmingUp: return
        
        # Works - Get Indicator's data - For mapped Indicators, keeping in mind Rolled Over Contracts
        for symbol in self.Data.keys():

            # if self.Data[symbol].yesterdayPercentChange is not None:
            #     self.Debug(f"yesterdayPercentChange:{symbol}:{self.Time}:{self.Data[symbol].yesterdayPercentChange}")

            pass
            # self.Debug(f"Yester Time:{self.Time}, {self.Data[symbol].Mapped}.yesterday:{self.Data[symbol].yesterday}")
            # self.Debug(f"{symbol}: Mapped ATR property:{self.Data[symbol].ATR}, {self.Time}")               
            # self.Debug(f"{symbol}: Continuous ATR property:{round(self.Data[symbol]._ContinuousATR.Current.Value,2)}, {self.Time}")    
            # self.Debug(f"{symbol}: Mapped MA2 property:{self.Data[symbol]._MappedMA2.Current.Value}, {self.Time}")    
            # self.Debug(f"{symbol}: Continuous MA2 property:{round(self.Data[symbol]._ContinuousMA2.Current.Value,2)}, {self.Time}") 
            # self.Debug(f"{symbol}: Mapped Yesterday:{self.Data[symbol]._MappedYesterday.Current.Value}, {self.Time}") 
            # self.Debug(f"{symbol}: Timezone:{self.Data[symbol].timezone}") 
            # self.Debug(f"{symbol}: Continuous Yesterday:{self.Data[symbol]._ContinuousYesterday.Current.Value}, {self.Time}") 

        # Works
        # for security in self.ActiveSecurities.Values:
        #     self.Debug(f"self.Time:{self.Time} ActiveSecurity:{security}")


    def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
        
        # NG - at 00:00:00 on 27th when StartDate is 26th
        # LBS - at 01:00:00 on 27th when StartDate is 26th

        # Only runs at the start of program not when Contract rolls 
        for security in changes.AddedSecurities:
            if len(changes.AddedSecurities) == 0: return
            self.Debug(f"In Main: OnSecuritiesChanged: Date:{self.Time}, security:{changes.AddedSecurities[0].Mapped}")


    def OnData(self, data):    
        
        # https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods#03-Warm-Up-Vs-Reality
        # if self.IsWarmingUp: return
        
        # Below code important to compare Ticks with whats reported from DataClass
        tickTradeProps = ['LastPrice','Quantity']
        tickQuoteProps = ['BidPrice','BidSize','AskPrice','AskSize']
        # tickOIProps = ['Value']  # Not Getting Data for OpenInterest
        
        for security in data.Keys:           
            
            # if self.Time < self.signalStartTime or self.Time > self.signalEndTime: return # temporary
            
            if data.Ticks.ContainsKey(security) and data.Ticks[security] is not None:
                ticks = data.Ticks[security]
                for tick in ticks:
                    tick_type = getTickType(tick.TickType)
                    if tick_type == 'Trade' and int(getattr(tick, 'Quantity')) != 0:
                        # For Trade Data
                        dic = {k:getattr(tick, k) for k in tickTradeProps if getattr(tick, k) is not None}
 
                        if security == str(self.Data["Lumber"].Symbol):
                            # self.Debug(f"TradeTick:{self.Time} {dic}, security:{security}")       
                            pass   
                    elif tick_type == 'Quote':
                        # For Best Bid & Ask
                        # dic2 = {k:getattr(self.Securities[security], k) for k in tickQuoteProps} 
                        dic2 = {k:round(getattr(self.Securities[security], k),1) if k in ['BidPrice','AskPrice'] else getattr(self.Securities[security], k) for k in tickQuoteProps} 
                        # self.Debug(f"QuoteTick:{self.Time}, security:{security},  {dic2}")

        # prev_dt = None
        # for symbol in data.Keys: 
        for symbol in self.Data.keys(): 

            # sending updates to dataclass of each security
            # checking for security and custom data symbol within the dataclass
            
            self.Data[symbol].Update(data)



            # if data.ContainsKey(self.Data[symbol].Symbol):
            #     self.Data[symbol].Update(data)
            
            if self.Time < self.signalStartTime or self.Time > self.signalEndTime: return # temporary
            

            # self.Debug(f"{self.Time}:{self.percentChangeDF.tail(1)}")



            # self.Debug(f"++BestBidMapped:{symbol}:{self.Time}:{self.Data[symbol].bestBidMapped}")
            # self.Debug(f"^^BestAskMapped:{symbol}:{self.Time}:{self.Data[symbol].bestAskMapped}")   
            # self.Debug(f"++BestBidContinuous:{symbol}:{self.Time}:{self.Data[symbol].bestBidContinuous}")
            # self.Debug(f"^^BestAskContinuous:{symbol}:{self.Time}:{self.Data[symbol].bestAskContinuous}")   
            
            # if self.Data[symbol].tradeMapped != prev_dt:
            # self.Debug(f"**tradeMapped:{symbol}:{self.Data[symbol].tradeMapped}")
            # prev_dt = self.Data[symbol].tradeMapped

            # self.Debug(f"**tradeContinuous:{symbol}:{self.Data[symbol].tradeContinuous}")


            # self.Debug(f"**WAP:{symbol}:{self.Time}:{self.Data[symbol].WAP}")       
            # if self.Data[symbol].yesterdayPercentChange is not None:
            #     self.Debug(f"yesterdayPercentChange:{symbol}:{self.Time}:{self.Data[symbol].yesterdayPercentChange}")

            # if self.Data[symbol].RollingYesterdayPercentChange:
            #     self.Debug(f"RollingYesterdayPercentChange:{symbol}:{self.Time}:{self.Data[symbol].RollingYesterdayPercentChange[0]}")

            
            # WORKS - Updated several times in a day - Doesn't give last traded price - gives bid or ask
            # self.Debug(f"Todays ____Close:{self.Securities[self.Data['Lumber'].Mapped].Price}, Date:{self.Time}")
       
        # Works
        # if data.Ticks.ContainsKey(self.Data['Lumber'].Symbol):
        #     if data.Ticks[self.Data['Lumber'].Symbol] is not None:                
                # self.Debug(f"**MAIN** Date:{self.Time}, MappedValue:{self.Data['Lumber'].Mapped.Value}, MappedID:{self.Data['Lumber'].Mapped.ID}, ")             

        # https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-futures-security-master#05-Data-Point-Attributes        
        for symbol in self.Data.keys():
            if data.SymbolChangedEvents.ContainsKey(self.Data[symbol].Symbol):
                symbolChangedEvent = data.SymbolChangedEvents[self.Data[symbol].Symbol]
                self.Debug(f"In MAIN Symbol changed: {symbolChangedEvent.OldSymbol} -> {symbolChangedEvent.NewSymbol} \
                EndTime:{symbolChangedEvent.EndTime} DataType:{getDataType(symbolChangedEvent.DataType)}, Expiry: {self.Securities[self.Data[symbol].Mapped].Expiry}")

                          
    # When your algorithm stops executing, LEAN calls the OnEndOfAlgorithm method.
    def OnEndOfAlgorithm(self) -> None:
        # self.Debug(f"self.Alpha.securities:{self.alpha.securities}")
        # self.Debug(f"Total Rows DataFrame:{len(self.percentChangeDF.index)}")
        # self.ObjectStore.Save(f"{14153031}/self.alpha.ModelData", df.reset_index().to_json(date_unit='s'))

        # self.ObjectStore.Save(f"{14153031}/sampleDF", self.alpha.ModelData.to_json(date_unit='s'))
        pass       

    # OnEndOfDay notifies when (Time) each security has finished trading for the day
    def OnEndOfDay(self, symbol: Symbol) -> None:
        # For LBS: Finished Trading on 2023-01-03 15:55:00 
        # For NBS: Finished Trading on 2023-01-03 16:50:00

        # self.Debug(f"Finished Trading on {self.Time} for security {symbol}")

        # dailyFileName =  f"ModelData_{self.Time.date()}"
        # self.ObjectStore.Save(f"{14153031}/{dailyFileName}", self.alpha.ModelData.to_json(date_unit='s'))

        # The OnEndOfDay method is called 10 minutes before closing to allow you to close out your position(s).
        # Clear ModelData DataFrame at end of Day - Issue it it happens 10 minutes or more before market closes so can't capture eod data
        # self.alpha.ModelData = pd.DataFrame()

        # self.Debug(f"OnEndOfDay self.Time:{self.Time}, Symbol:{self.Data['Lumber'].Mapped.Value}")
        pass
                

    def OnWarmUpFinished(self) -> None:
        self.Debug(f"Algorithm Ready@{self.Time}")
        pass


        