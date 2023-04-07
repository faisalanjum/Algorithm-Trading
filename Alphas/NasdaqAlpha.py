from AlgorithmImports import *
from HelperFuncs import *
import pandas as pd
import math

# TO DO: Use following functions in only 1 of the Alpha Models
        # updateModelData
        # clearModelData
        # saveModelData
        # & In scheduler
        # changed_event in data.SymbolChangedEvents.Values: in Update Function

class NasdaqAlpha(AlphaModel):
    Name = "NasdaqAlpha"
    symbol = 'Lumber'

    
    def __init__(self, DataDict):
        
        self.DataDict = DataDict # Passed the Data Dictionary that contains all Futures
        self.ModelData = pd.DataFrame() # Contains percentChangeSeconds

        # Insights Related Variables       
        self.InsightDirectionDict = lambda s: {0:InsightDirection.Up, 1:InsightDirection.Down, 2:InsightDirection.Flat}[s]
        self.previousBeforeMarketOpenSignals = None
        self.previousAfterMarketOpenSignals = None
        self.BeforeMarketOpenFlag = None
        self.ShouldEmitInsight = RunAfterInterval(interval_seconds= 1 ) # Class from HelperFuncs
        
        # Signal Paremeters - To be Optimised
        self.nasdaqCutoff = 1 # Nasdaq Cutoff before we go Long/Short    
        self.lumberBetaToNasdaq = 1.5 # This should be calculated based on regression coefficient        
        self.percentOfPotential = 0.5 # Cutoff to enter Trade before Signal has played out
        self.temp = 0

    # Handles security changes in from your universe model.
    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges) -> None:
        
        # This code runs everytime there is a contract rollover but does it know which symbol has switched
        for changed_event in algorithm.CurrentSlice.SymbolChangedEvents.Values:
            algorithm.Debug(f"Contract rollover from (AM- OnSecuritiesChanged) {changed_event.OldSymbol} to {changed_event.NewSymbol}, Time:{algorithm.Time}")
            pass
        
        # Everytime Contract rollsOver (any Lumber or Nasdaq), the following line runs, but ...
        # algorithm.Debug(f"Count AM: {changes.Count}, changes:{changes}")
        
        # .. this code only runs Once at the very start not when future contracts roll!
        for security in changes.AddedSecurities:
            # algorithm.Debug(f"In OnSecuritiesChanged(AM) @ DateTime:{algorithm.Time}, Mapped/ID: {security.Mapped}, Canonical: {security.Mapped.Canonical} \
            # #  Symbol: {security.Symbol}, Value: {security.Mapped.Value}, SecurityType: {getSecurityType(security.Mapped.SecurityType)}")                          
            pass
            # Capture Nasdaq %age Change before Lumber Opens  
            # algorithm.Schedule.On(algorithm.DateRules.EveryDay('/LBS'), algorithm.TimeRules.At(9,59,51),self.updateModelData)
            # Capture %age Change for Nasdaq & Lumber during Lumber Market Hours
            # algorithm.Schedule.On(algorithm.DateRules.EveryDay('/LBS'), algorithm.TimeRules.Every(timedelta(seconds=1)),self.updateModelData)
            # Store Daily file from ModelData
            # algorithm.Schedule.On(algorithm.DateRules.EveryDay('/LBS'), algorithm.TimeRules.At(16,10,00),self.saveModelData)
            # clear self.ModelData
            # algorithm.Schedule.On(algorithm.DateRules.EveryDay('/LBS'), algorithm.TimeRules.At(23,50,00),self.clearModelData)

        for security in changes.RemovedSecurities:
            pass

    def Update(self, algorithm, data):
        
        # https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-futures-security-master#05-Data-Point-Attributes
        # This Code runs everytime there is a futures rollover
        # algorithm.Debug(f"data.SymbolChangedEvents.Keys:{data.SymbolChangedEvents.Keys}")

        # if data.Keys[0] == self.lumberDataClass.Symbol:
        for changed_event in data.SymbolChangedEvents.Values:
            algorithm.Debug(f"Contract rollover (AM- Update Method) from {changed_event.OldSymbol} to {changed_event.NewSymbol}")
            security  = data.Keys[0]             
            algorithm.Debug(f"In Update (AM) @ DateTime:{algorithm.Time}, security:{security}, ID:{security.ID},Canonical:{security.Canonical} \
                + Value:{security.Value},Underlying:{security.Underlying}. SecurityType:{getSecurityType(security.SecurityType)}")

        # Constructing Insight
        insight = None
        # 1. Insight Position - Up, Down or Flat        
        if (insightPosition := self.Signal(algorithm)) is None or not self.ShouldEmitInsight.run(self.symbol, algorithm.UtcTime):
            return []
        
        # 2. Insight Period: 1 Second Long Insights 
        if self.BeforeMarketOpenFlag:
            # insightPeriod = timedelta(seconds = (self.DataDict[self.symbol].currentOpen - algorithm.Time).total_seconds()) + timedelta(seconds = 60)
            insightPeriod = timedelta(seconds = (self.DataDict[self.symbol].currentClose - self.DataDict[self.symbol].currentOpen).total_seconds()) - timedelta(hours = 1)
        else:
            insightPeriod = timedelta(seconds = (self.DataDict[self.symbol].currentClose - timedelta(hours=1, minutes =5) - algorithm.Time).total_seconds())
        
        # 3. Insight Symbol
        mappedSymbol = self.DataDict[self.symbol].Mapped
        nasdaqPercent = list(self.DataDict['Nasdaq']._yesterdayPercentChange.values())[0]

        # 4. Insight Magnitude
        insightMagnitude = round(NasdaqPercentChangeToMagnitude(nasdaqPercent,self.lumberBetaToNasdaq)/100,3)                

        # 5. Insight Confidence
        insightConfidence = NasdaqPercentChangeToConfidence(nasdaqPercent)

        insight = Insight(symbol = mappedSymbol, period = insightPeriod, type = InsightType.Price, direction = insightPosition, \
        magnitude  = insightMagnitude, confidence = insightConfidence, sourceModel=self.Name, weight=None)

        algorithm.Debug(f"Insight:{insight}::{algorithm.Time}")

        return [insight]


    def Signal(self, algorithm):    
        # Before Market Opens: Remember Exchange stops accepting orders 30 seoconds b4 Market Opens, yesterdayPercentChange available only after SignalStartTime        
        if self.DataDict['Nasdaq'].yesterdayPercentChange and algorithm.Time < (self.DataDict[self.symbol].currentOpen- timedelta(seconds = 30)):   
            
            self.BeforeMarketOpenFlag = True
            nasdaqPercent = list(self.DataDict['Nasdaq']._yesterdayPercentChange.values())[0]            
            condLongPreMarketOpen  = nasdaqPercent > self.nasdaqCutoff
            condShortPreMarketOpen = nasdaqPercent < -self.nasdaqCutoff

            # Only Send new Insight if Changed from before else return None
            if (condLongPreMarketOpen, condShortPreMarketOpen) != self.previousBeforeMarketOpenSignals:
                # algorithm.Debug(f"1 Works in NASDAQALPHA :::{algorithm.Time}")
                self.previousBeforeMarketOpenSignals = (condLongPreMarketOpen, condShortPreMarketOpen)
                # returns 1 for Long, 0 for Flat, -1 for Short
                return self.InsightDirectionDict([i for i, x in enumerate([condLongPreMarketOpen,condShortPreMarketOpen,not (condLongPreMarketOpen or condShortPreMarketOpen)]) if x][0])
               

        # After Market Opens to say 1 hour before Market Closes - minutes + 5 since it shows extended timing. 
        # Note that if no Traded Value for Lumber, yesterdayPercentChange will be empty and this code won't execute
        elif self.DataDict[self.symbol].yesterdayPercentChange and algorithm.Time >= self.DataDict[self.symbol].currentOpen and algorithm.Time < (self.DataDict[self.symbol].currentClose - timedelta(hours=0, minutes =5)):
            
            self.BeforeMarketOpenFlag = False
            nasdaqPercent = list(self.DataDict['Nasdaq']._yesterdayPercentChange.values())[0]
            lumberPercent = list(self.DataDict[self.symbol]._yesterdayPercentChange.values())[0] if self.DataDict[self.symbol].yesterdayPercentChange else None
            
            # Note if lumberPercent is None, it won't affect the following 2 conditions:
            condLongPostMarketOpen = nasdaqPercent > self.nasdaqCutoff             \
            and (lumberPercent is None or lumberPercent > 0) \
            and lumberPercent < self.percentOfPotential * (nasdaqPercent*self.lumberBetaToNasdaq)

            condShortPostMarketOpen = nasdaqPercent < -self.nasdaqCutoff            \
            and (lumberPercent is None or lumberPercent < 0) \
            and lumberPercent > self.percentOfPotential * (nasdaqPercent*self.lumberBetaToNasdaq)

            # The following code is to check if the Signal changed after market Open - if changed (or first time only) then return the InsightDirection else return None
            if (condLongPostMarketOpen, condShortPostMarketOpen) != self.previousAfterMarketOpenSignals:

                self.temp += 1 
                algorithm.Debug(f"Start:{self.temp} at {algorithm.Time}")
                algorithm.Debug(f"condLongPostMarketOpen:{condLongPostMarketOpen} at {algorithm.Time}")
                algorithm.Debug(f"condShortPostMarketOpen:{condShortPostMarketOpen} at {algorithm.Time}")
                algorithm.Debug(f"nasdaqPercent:{nasdaqPercent} at {algorithm.Time}")
                algorithm.Debug(f"lumberPercent:{lumberPercent} at {algorithm.Time}")
                algorithm.Debug(f"percentOfPotential * (nasdaqPercent*lumberBetaToNasdaq):{self.percentOfPotential * (nasdaqPercent*self.lumberBetaToNasdaq)} at {algorithm.Time}")
                algorithm.Debug(f"Return from InsighTdICT:{self.InsightDirectionDict([i for i, x in enumerate([condLongPostMarketOpen,condShortPostMarketOpen,not (condLongPostMarketOpen or condShortPostMarketOpen)]) if x][0])} at {algorithm.Time}")
                algorithm.Debug(f"Stop:{self.temp} at {algorithm.Time}")
                algorithm.Debug(f"2 Works in NASDAQALPHA :::{algorithm.Time}")

                self.previousAfterMarketOpenSignals = (condLongPostMarketOpen, condShortPostMarketOpen)
                # returns 1 for Long, 0 for Flat, -1 for Short
                return self.InsightDirectionDict([i for i, x in enumerate([condLongPostMarketOpen,condShortPostMarketOpen,not (condLongPostMarketOpen or condShortPostMarketOpen)]) if x][0])

        return None




    # ModelData Related Functions
    def updateModelData(self):
        
        for symbol in self.DataDict.keys():
            # self.yesterdayPercentChange only updates during Lumber hours
            if self.DataDict[symbol].yesterdayPercentChange:               
                # Captures every Second
                self.ModelData.loc[self.DataDict[symbol].algo.Time,symbol] = list(self.DataDict[symbol]._yesterdayPercentChange.values())[0]            
                # self.DataDict[symbol].algo.Debug(f"In AlphaModel{self.DataDict[symbol].algo.Time}:{self.ModelData.tail(1)}")
                
                # Chart Added
                self.DataDict[symbol].algo.Plot("NQ vs LBS", symbol, self.ModelData.loc[self.DataDict[symbol].algo.Time,symbol])

    def clearModelData(self):
        self.ModelData = pd.DataFrame()

    def saveModelData(self):
        dailyFileName =  f"ModelData_{self.DataDict[self.symbol].algo.Time.date()}"
        self.DataDict[self.symbol].algo.Debug(f"dailyFileName:{dailyFileName}")
        self.DataDict[self.symbol].algo.Debug(f"Length of ModelData b4 saving:{len(self.ModelData)}")
        self.DataDict[self.symbol].algo.ObjectStore.Save(f"{14153031}/{dailyFileName}", self.ModelData.to_json(date_unit='s'))
