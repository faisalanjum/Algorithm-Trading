 
from AlgorithmImports import *
from itertools import groupby
from HelperFuncs import *

class SourcePortfolioConstructionModel(PortfolioConstructionModel):
    symbol = 'Lumber'

    def __init__(self, DataDict, rebalancingFunc = None, portfolioBias = PortfolioBias.LongShort):
        
        self.DataDict = DataDict # Passed the Data Dictionary that contains all Futures

        self.insightCollection = InsightCollection()
        self.ShouldPrint = RunAfterInterval(interval_seconds = 1)  # Class from HelperFuncs        
        # self.portfolioBias = portfolioBias
        
        self.usedInsight = [] # put in ShouldCreateTragetsFromInsights

        self.percentOfPotential = 0.5 # Cutoff to enter Trade before Signal has played out
        self.temp = 0


        # 3 dictionaries for Alpha Models
        self.alphaStrength = {}  
        self.alphaSwitch   = {}
        self.alphaSign  = {}

    # REQUIRED: Will determine the target percent for each insight
    def DetermineTargetPercent(self, activeInsights: List[Insight]) -> Dict[Insight, float]:
        return []

    # Gets the target insights to calculate a portfolio target percent for, they will be piped to DetermineTargetPercent()
    def GetTargetInsights(self) -> List[Insight]:
        return []

    # To combine the active insights differently, override the GetTargetInsights, and return all active insights.
    # https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/portfolio-construction/key-concepts#04-Multi-Alpha-Algorithms
    # def GetTargetInsights(self) -> List[Insight]:
    #     return list(self.InsightCollection.GetActiveInsights(self.Algorithm.UtcTime))

    # Create list of PortfolioTarget objects from Insights
    def CreateTargets(self, algorithm: QCAlgorithm, insights: List[Insight]) -> List[PortfolioTarget]:
        
        # Not Sure if its correct to use here
        if algorithm.Time < self.DataDict[self.symbol].algo.signalStartTime or algorithm.Time > self.DataDict[self.symbol].algo.signalEndTime: 
            # algorithm.Debug("After Signal End Returning Empty Targets")
            return []

        ActiveInsights = []
        LastActiveInsights = []
        MappedCtrct = self.DataDict[self.symbol].Mapped

        # Add Insights to InsightCollection
        for insight in insights:
            if self.ShouldCreateTargetForInsight(insight):
                self.insightCollection.Add(insight)           
        
        # To check if an insight exists in the InsightCollection
        # algorithm.Debug(f"{self.insightCollection.Contains(insight)}")
        
        # To iterate through the InsightCollection
        # for insight in self.insightCollection.GetEnumerator():
        #     algorithm.Debug(f"self.insightCollection.GetEnumerator:{insight}")

        # HasActiveInsight for a Symbol 
        if MappedCtrct is not None:
            # algorithm.Debug(f"MappedCtrct:{MappedCtrct}")
            if self.insightCollection.ContainsKey(MappedCtrct):
                hasActiveInsights = self.insightCollection.HasActiveInsights(MappedCtrct, algorithm.UtcTime)

        # Remove Expired Insights from InsightCollection
        ExpiredInsights = self.insightCollection.RemoveExpiredInsights(algorithm.UtcTime)
        for count, insight in enumerate(ExpiredInsights):
            algorithm.Debug(f"ExpiredInsights#{count+1}:{insight} @ {algorithm.Time}")

        # Get ActiveInsights
        ActiveInsights = self.insightCollection.GetActiveInsights(algorithm.UtcTime)       

        # Remove duplicate Insights from ActiveInsights - Check if neccessary
        ActiveInsights = list(dict.fromkeys(ActiveInsights))

        # Print Active Insight
        for count, insight in enumerate(ActiveInsights[:]):
            # algorithm.Debug(f"ActiveInsights#{count+1}:{insight} @ {algorithm.Time}") 
            pass
                    
        # Get LastActive Insight
        for symbol, g in groupby(ActiveInsights, lambda x:x.Symbol):
            LastActiveInsights.append(sorted(g, key = lambda x:x.GeneratedTimeUtc)[-1])        
        
        # Print Total ActiveInsights, LastActiveInsights & NextExpiryTime
        
        if self.ShouldPrint.run(MappedCtrct,algorithm.UtcTime) and len(ActiveInsights[:]) > 0:
            # algorithm.Debug(f"Total ActiveInsights:{len(ActiveInsights[:])} at {algorithm.Time}") 
            # var1 += 1
            # algorithm.Debug(f"var in ShouldPrint:{var1} at {algorithm.Time}") 
            
            # Get the next Insight expiry time
            NextExpiryTime = self.insightCollection.GetNextExpiryTime() 
            if NextExpiryTime is not None: NextExpiryTime = NextExpiryTime - timedelta(hours=5)
            # algorithm.Debug(f"NextExpiryTime:{NextExpiryTime}")
            
            for insight in LastActiveInsights:
                # algorithm.Debug(f"LastActiveInsight:{insight} at {algorithm.Time}") # from Model:{insight.SourceModel}
                pass

            # Still Some empty values are not being printed for IsExpired & IsActive as they are bound methods
            InsightProperties = []            
            insight_values = [(prop, getattr(insight, prop)) for prop in insight_Properties if hasattr(insight, prop) \
                and getattr(insight, prop) is not None and (not isinstance(getattr(insight, prop), str) or bool(getattr(insight, prop)))]           
            # Convert UTC time to Eastern time for the "GeneratedTimeUtc" and "CloseTimeUtc" properties
            insight_values = [(key, value - timedelta(hours=5)) if key in ["GeneratedTimeUtc", "CloseTimeUtc"] \
                else (key, value) for key, value in insight_values]        
            InsightProperties.extend(insight_values)
            for key, value in InsightProperties:
                if key in ["GeneratedTimeUtc", "CloseTimeUtc"]:
                    # algorithm.Debug(f"Key: {key}, Value: {value}")
                    pass
        
            if len(ExpiredInsights) > 0:
                # algorithm.Debug(f"Total ExpiredInsights:{len(ExpiredInsights)} at {algorithm.Time}") 
                pass
        
        # Actually LastActiveInsights is getting empty everytime this function runs.
        if LastActiveInsights and LastActiveInsights[0] not in self.usedInsight:
            # algorithm.Debug(f"LastActiveInsight:{LastActiveInsights[0]} at {algorithm.Time}") 
            self.DetermineSourceModels(algorithm, LastActiveInsights[0])
            # algorithm.Debug(f"self.alphaStrength:{self.alphaStrength}")
            # algorithm.Debug(f"self.alphaSwitch:{self.alphaSwitch}")
            # algorithm.Debug(f"self.alphaSign:{self.alphaSign}")
            # algorithm.Debug(f"self.alphaSign:{self.alphaSign}")
            # self.alphaStrength[sourceModelName] = getattr(insight,'Magnitude')
            # self.alphaSwitch[sourceModelName] = 1 
            # self.alphaSign[sourceModelName] = getattr(insight,'Direction')*1

            self.usedInsight.append(LastActiveInsights[0])
            return [PortfolioTarget(getattr(LastActiveInsights[0],'Symbol'),getattr(LastActiveInsights[0],'Direction')*1)]
        else:
            return []



    # Determines if the portfolio should be rebalanced base on the provided rebalancing func
    def IsRebalanceDue(self, insights: List[Insight], algorithmUtc: datetime) -> bool:
        return True

    # OPTIONAL: Security change details
    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges) -> None:
        # Security additions and removals are pushed here.
        # This can be used for setting up algorithm state.
        # changes.AddedSecurities:
        # changes.RemovedSecurities:
        pass
    
    def RespectPortfolioBias(self, insight):
        return self.portfolioBias == PortfolioBias().LongShort or insight.Direction == PortfolioBias.Long \
            or insight.Direction == PortfolioBias.Short
    

    # Determine if the portfolio construction model should create a target for this insight
    def ShouldCreateTargetForInsight(self, insight: Insight) -> bool:
        
        sourceModelName = getattr(insight,'SourceModel')
        
        if sourceModelName == 'NasdaqAlpha' and insight is not None:
            direction = getattr(insight,'Direction')*1
            # maxPotential = self.percentOfPotential * getattr(insight,'Magnitude')        
            self.DataDict[self.symbol].algo.Debug(f"reached here #{self.DataDict[self.symbol].algo.Time}")


            if self.DataDict[self.symbol].yesterdayPercentChange and self.DataDict[self.symbol].algo.Time >= self.DataDict[self.symbol].currentOpen:
                lumberPercent = list(self.DataDict[self.symbol]._yesterdayPercentChange.values())[0] if self.DataDict[self.symbol].yesterdayPercentChange else None
                nasdaqPercent = list(self.DataDict['Nasdaq']._yesterdayPercentChange.values())[0]
                maxPotential = self.percentOfPotential * (nasdaqPercent*1.5)

            # lumberPercent is None  - how to remove this
                # if (lumberPercent is None or lumberPercent * direction > 0) and (direction * (lumberPercent - maxPotential) < 0):
                #     return True

                # else:
                #     return False

            # getattr(insight,'Magnitude') is same as (nasdaqPercent*self.lumberBetaToNasdaq)
            # The first expression  translates to:
                # when going Long: lumberPercent < self.percentOfPotential * (nasdaqPercent*self.lumberBetaToNasdaq)
                # when going short: lumberPercent > self.percentOfPotential * (nasdaqPercent*self.lumberBetaToNasdaq)

            # The second expression translates to:
                # when going long:(lumberPercent is None or lumberPercent > 0)
                # when short: (lumberPercent is None or lumberPercent < 0)


        # self.temp += 1
        # self.DataDict[self.symbol].algo.Debug(f"In ShouldCreate#{self.temp}")

        return True


    # Custom Functions

    # Fill all 3 dicts
    def DetermineSourceModels(self, algorithm, insight):
        
        # self.temp += 1
        # self.DataDict[self.symbol].algo.Debug(f"#{self.temp}")


        # Perform check
        sourceModelName = getattr(insight,'SourceModel')

        if sourceModelName == 'NasdaqAlpha':
            self.alphaStrength[sourceModelName] = getattr(insight,'Magnitude')
            self.alphaSwitch[sourceModelName] = 1 
            self.alphaSign[sourceModelName] = getattr(insight,'Direction')*1

        elif sourceModelName == 'OrderBook':
            pass
