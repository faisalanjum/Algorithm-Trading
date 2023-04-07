from AlgorithmImports import *
from HelperFuncs import *
import pandas as pd
import json
import math

# TO DO: Use following functions in only 1 of the Alpha Models
        # updateModelData
        # clearModelData
        # saveModelData
        # & In scheduler
        # changed_event in data.SymbolChangedEvents.Values: in Update Function


class DataModel(AlphaModel):
    
    def __init__(self, DataDict,symbol="Lumber"):
        self.symbol=symbol
        self.DataDict = DataDict # Passed the Data Dictionary that contains all Futures
       # Contains trades Seconds and Ticks
        self.ModelList={"seconds":[],"ticks":[]}
        #holding trade for nasdaq
        self.NasdaqTrade=[]

      
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
            # pass
            # algorithm.Schedule.On(algorithm.DateRules.EveryDay(self.DataDict[self.symbol].Symbol), algorithm.TimeRules.Every(timedelta(seconds=1)),self.updateModelData)
            # Store Daily file from ModelData
            algorithm.Schedule.On(algorithm.DateRules.EveryDay(self.DataDict[self.symbol].Symbol), algorithm.TimeRules.BeforeMarketClose(self.DataDict[self.symbol].Symbol,-2),self.saveModelData)
            # # clear self.ModelData
            algorithm.Schedule.On(algorithm.DateRules.EveryDay(self.DataDict[self.symbol].Symbol), algorithm.TimeRules.At(23,50,00),self.clearModelData)

        for security in changes.RemovedSecurities:
            pass

    def Update(self, algorithm, data):
        if data.Ticks.ContainsKey(self.DataDict["Nasdaq"].Symbol) and data.Ticks[self.DataDict["Nasdaq"].Symbol] is not None:
            ticks=data.Ticks[self.DataDict["Nasdaq"].Symbol]
            self.NasdaqTrade=[]
            for tick in ticks:
                if tick.TickType == TickType.Trade and int(getattr(tick, 'Quantity')) != 0:
                    #appending to nasdaqTrade so can use the latest trades when lumber trades occur 
                    self.NasdaqTrade.append({"price":tick.LastPrice,"symbol":str(self.DataDict["Nasdaq"].Symbol),"size":tick.Quantity,"time":algorithm.Time})

        # check for lumber ticks  in data
        if data.Ticks.ContainsKey(self.DataDict["Lumber"].Symbol) and data.Ticks[self.DataDict["Lumber"].Symbol] is not None:
            lumber_ticks=data.Ticks[self.DataDict["Lumber"].Symbol]
            for tic in lumber_ticks:
                if tic.TickType == TickType.Trade and int(getattr(tic, 'Quantity')) != 0:
                    self.ModelList["ticks"].append({"price":tic.LastPrice,"symbol":self.DataDict["Lumber"].Symbol,"size":tic.Quantity,"time":algorithm.Time})
                    # algorithm.Debug(f"Inside Data Model Price:{tic.LastPrice},Quantity:{tic.Quantity},Date:{algorithm.Time} symbol:{self.DataDict['Lumber'].Symbol}")
                    
            if len(self.NasdaqTrade) >=1:
                for t in self.NasdaqTrade:
                    # algorithm.Debug(f"Nasdaq Trades Avaliable {t}")
                    self.ModelList["ticks"].append(t)
        insights=[]
        return insights

    # ModelData Related Functions
    def updateModelData(self):
        for symbol in self.DataDict.keys():
            dct={}
            # self.yesterdayPercentChange only updates during Lumber hours
            if self.DataDict[symbol].tradeContinuous["price"] and self.DataDict[symbol].tradeContinuous["price"] != None:
                dct["price"]=self.DataDict[symbol].tradeContinuous["price"]
                dct["size"]=self.DataDict[symbol].tradeContinuous["size"]
                dct["time"]=self.DataDict[symbol].algo.Time
                dct["symbol"]=symbol
                dct["mapped"]=str(self.DataDict[symbol].Mapped)
                dct["yeseterday_mapped"]=self.DataDict[symbol]._MappedYesterday.Current.Value
                if self.DataDict[symbol].yesterdayPercentChange:
                    dct["yesterday_percentage_change"]=list(self.DataDict[symbol]._yesterdayPercentChange.values())[0]

                if symbol == self.symbol:
                    # western custom data added
                    if self.DataDict[symbol].custom and self.DataDict[symbol].custom['WESTERN.Western'] != None:
                        dct["western_barometer_orders"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Orders"]
                        dct["western_barometer_inventories"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Inventories"]
                        dct["western_barometer_production"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Production"]
                        dct["western_barometer_shipment"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Shipments"]
                        dct["western_barometer_report_date"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Date"]
                        dct["western_barometer_unfilled"]=self.DataDict[symbol].custom['WESTERN.Western']["data"]["Unfilled"]

                self.ModelList["seconds"].append(dct) 
              

     #cleans data at the end of day          
    def clearModelData(self):
        self.ModelList["seconds"]=[]
        self.ModelList["ticks"]=[]
        #reset trade list
        self.NasdaqTrade=[]
    
    #saves data in object after market close
    def saveModelData(self):
        for key in self.ModelList.keys():
            if len(self.ModelList[key]) >= 1: 
                dailyFileName =  f"ModelDataTrade_{key}_{self.DataDict[self.symbol].algo.Time.date()}"
                self.DataDict[self.symbol].algo.Debug(f"dailyFileName:{dailyFileName}")
                df=pd.DataFrame(self.ModelList[key])
                self.DataDict[self.symbol].algo.Debug(f"{key} Model Data b4 Saving:{df.shape[0]}")
                self.DataDict[self.symbol].algo.ObjectStore.Save(f"{14153031}/{dailyFileName}",df.to_json(default_handler=str))
