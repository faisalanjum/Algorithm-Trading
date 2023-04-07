from AlgorithmImports import *
from HelperFuncs import *
from itertools import groupby

# TO CHECK - Only First 10 k alphas are being shown in Backtest Insight Tab - For now using TimeInterval of 2 seconds to see everything - change to 1

# Only use for Entry Condition before Market Opens. AfterMarketOpen Insight can be backtested later for Market Order?
class OrderBookAlpha(AlphaModel):
    Name = "OrderBook"
    symbol = 'Lumber'

    def __init__(self, DataDict):
        
        self.DataDict = DataDict # Passed the Data Dictionary that contains all Futures

        # Insights Related Variables       
        self.InsightDirectionDict = lambda s: {0:InsightDirection.Up, 1:InsightDirection.Down, 2:InsightDirection.Flat}[s]
        self.previousBeforeMarketOpenSignals = None
        self.NumberOfConditions = 2  # Using 2 conditions out of 3 (BID,ASK, WAP) compared to YesterdayClose (Before Open) & Last Traded Price (After Open)
        self.BeforeMarketOpenFlag = None
        self.ShouldEmitInsight = RunAfterInterval(interval_seconds= 2) # Class from HelperFuncs

    # Handles security changes in from your universe model.
    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges) -> None:
        
        # This code runs everytime there is a contract rollover but does it know which symbol has switched
        for changed_event in algorithm.CurrentSlice.SymbolChangedEvents.Values:
            algorithm.Debug(f"Contract rollover from (AM- OnSecuritiesChanged) {changed_event.OldSymbol} to {changed_event.NewSymbol}, Time:{algorithm.Time}")
            pass
        
        # This code only runs Once at the very start not when future contracts roll!
        for security in changes.AddedSecurities:
            # algorithm.Debug(f"In OnSecuritiesChanged(AM) @ DateTime:{algorithm.Time}, Mapped/ID: {security.Mapped}, Canonical: {security.Mapped.Canonical} \
            # #  Symbol: {security.Symbol}, Value: {security.Mapped.Value}, SecurityType: {getSecurityType(security.Mapped.SecurityType)}")                          
            pass

        for security in changes.RemovedSecurities:
            pass


    def Update(self, algorithm, data):
        
        for changed_event in data.SymbolChangedEvents.Values:
            pass
        
        # Constructing Insight
        insight = None
        # 1. Insight Position - Up, Down or Flat
        if (insightPosition := self.Signal(algorithm)) is not None and self.ShouldEmitInsight.run(self.symbol, algorithm.UtcTime):
             pass
        else:
            try:
                # algorithm.Debug(f"Close:{self.DataDict[self.symbol].currentClose} at {algorithm.Time}")
                # algorithm.Debug(f"Open:{self.DataDict[self.symbol].currentOpen} at {algorithm.Time}")
                if algorithm.Time > (self.DataDict[self.symbol].currentClose - timedelta(hours=0, minutes =55)):
                    # algorithm.Debug(f"Last 55 minutes at {algorithm.Time}")
                    pass
            except:
                pass
            return []
        # 2. Insight Period: 1 Second Long Insights            
        if self.BeforeMarketOpenFlag:
            insightPeriod = timedelta(seconds = (self.DataDict[self.symbol].currentOpen - algorithm.Time).total_seconds()) + timedelta(seconds = 2)
        else:
            insightPeriod = timedelta(seconds = 1)
        # 3. Insight Symbol
        mappedSymbol = self.DataDict[self.symbol].Mapped

        # 5. Insight Confidence - Using Distance Formula        
        # insightConfidence = NasdaqPercentChangeToConfidence(nasdaqPercent)
        
        insight = Insight(symbol = mappedSymbol, period = insightPeriod, \
        type = InsightType.Price, direction = insightPosition, \
        magnitude  = None, confidence = None, sourceModel= self.Name, weight=None)       

        return [insight]


    def Signal(self, algorithm):    

        # Before Market Opens: Remember Exchange stops accepting orders 30 seoconds b4 Market Opens, yesterdayPercentChange available only after SignalStartTime        
        if self.DataDict['Nasdaq'].yesterdayPercentChange and algorithm.Time < (self.DataDict[self.symbol].currentOpen- timedelta(seconds = 30)):           
            self.BeforeMarketOpenFlag = True
            check_list = [self.DataDict[self.symbol].bestBidMapped['price'],self.DataDict[self.symbol].bestAskMapped['price'],self.DataDict[self.symbol].WAPMapped]           
            condLongPreMarketOpen  = sum(c > self.DataDict[self.symbol]._MappedYesterday.Current.Value for c in check_list) >= self.NumberOfConditions
            condShortPreMarketOpen = sum(c < self.DataDict[self.symbol]._MappedYesterday.Current.Value for c in check_list) >= self.NumberOfConditions
            # The following code is to check if the Signal changed before 30 seconds market Open - if changed (or first time only) then return the InsightDirection else return None
            if (condLongPreMarketOpen, condShortPreMarketOpen) != self.previousBeforeMarketOpenSignals:
                self.previousBeforeMarketOpenSignals = (condLongPreMarketOpen, condShortPreMarketOpen)
                # Returns 1 for Long, 0 for Flat, -1 for Short
                return self.InsightDirectionDict([i for i, x in enumerate([condLongPreMarketOpen,condShortPreMarketOpen,not (condLongPreMarketOpen or condShortPreMarketOpen)]) if x][0])
          
        # After Market Opens to say 1 hour before Market Closes: minutes + 5 since it shows extended timing. 
        # Change tradeContinuous to tradeMapped once we figure out efficient way to calculate Mapped Trade
        elif self.DataDict[self.symbol].yesterdayPercentChange and algorithm.Time >= self.DataDict[self.symbol].currentOpen and algorithm.Time < (self.DataDict[self.symbol].currentClose - timedelta(hours=0, minutes =5)):

            # algorithm.Debug(f"currentOpen:{self.DataDict[self.symbol].currentOpen} at {algorithm.Time}")
            # algorithm.Debug(f"currentClose:  {(self.DataDict[self.symbol].currentClose)} at {algorithm.Time}")
            # algorithm.Debug(f"currentClose - 5 minutes:  {(self.DataDict[self.symbol].currentClose - timedelta(minutes =5))} at {algorithm.Time}")
            # algorithm.Debug(f"currentClose - 1 hour:  {(self.DataDict[self.symbol].currentClose - timedelta(hours=1))} at {algorithm.Time}")
            # algorithm.Debug(f"currentClose - 1 hour & 5 minutes:  {(self.DataDict[self.symbol].currentClose - timedelta(hours=1, minutes =5))} at {algorithm.Time}")

            self.BeforeMarketOpenFlag = False
            check_list = [self.DataDict[self.symbol].bestBidMapped['price'],self.DataDict[self.symbol].bestAskMapped['price'],self.DataDict[self.symbol].WAPMapped]                   
            condLongPostMarketOpen = sum(c > self.DataDict[self.symbol]._tradeContinuous.price for c in check_list) >= self.NumberOfConditions
            condShortPostMarketOpen = sum(c < self.DataDict[self.symbol]._tradeContinuous.price for c in check_list) >= self.NumberOfConditions
               
            return self.InsightDirectionDict([i for i, x in enumerate([condLongPostMarketOpen,condShortPostMarketOpen,not (condLongPostMarketOpen or condShortPostMarketOpen)]) if x][0])             

        return None
        
