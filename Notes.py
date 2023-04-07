#region imports
from AlgorithmImports import *
#endregion

# NEED HELP
# 1. Done: Get Yesterday's Close Price for Lumber Contracts - 2 ways to acheive. 
        # 1a. Use history fuction everyday - Works Fine
        # 2a. Use Identity Indicator - Its partially correct when using Resolution.Daily but incorrect On days when the contract rolls.
        # i.e. it still shows yesterday's close for previous contract on RollOverDays. Also would require a day or 2 of warmuP
        #   Secondly, if I use Resolution.Tick in Lumber Contract definition, it shows 2 days ago prices when called before market Open


# 3. Find trading days when both Nasdaq and Lumber were open (keeping in mind yesterday's data) and only trade when both are available atleast for backtesting
# https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/futures/market-hours/cme/mnq
# https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/futures/market-hours/cme/lbs

# 4. Nasdaq data not available on first day since it gets added at 2300 hours while Lumber gets added at 00 hours.

# 5. Didn't check if Nasdaq prices are fine or if Nasdaq yesterday contract prices match the rolled over contract

# 6. Whats the difference between getting Bids & Asks from ticks like below - Is the first one Time&Sales (for quotes) while second one gives Best Bids/Asks?
                # ticks = self.algo.CurrentSlice.Ticks[self.Symbol]
                # for tick in ticks:
                #         tick.AskPrice 

        # versus getting bids/asks from self.Securities[security].AskPrice

# 7.         # Questions on quoteEvent (TickQuoteBarConsolidator): 
        # 1. Does this tell you total number of best bids/asks at any moment in time or are these just seperate orders and their corresponding sizes? 
        # 2. Quotes are for mapped rolled contracts?
        # 3. Also these are not all quotes as placed but only Top Bids/Asks. So for example, they are only generated if someone has topped a previous bid/offer?






# Some other references:

# 1. Tick Data related
        # https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/futures/handling-data#07-Ticks
        # LastPrice - Alias for "Value" - the last sale for this asset. Same as Price 
        # IsFillForward - True if this is a fill forward piece of data 
        # 'Time','EndTime' - for Trade Tick is same as self.Time but for time use this property only
        # 'Symbol' - Not available but has other sub properties 
        # ,'SaleCondition','Suspicious' - Not relevant
        
        # tickTradeProps = ['Price','Quantity']
        # tickQuoteProps = ['BidPrice','BidSize','AskPrice','AskSize']
        # tickOIProps = ['Value']  # Not Getting Data for OpenInterest

# Other Notes to self:
        # 1. Since Resolution is for Ticks, we won't be getting Trade & Quote Bars
        # 2. 'LocalTime': Local time for this market
        # 3. Properties of self.Securities - https://www.quantconnect.com/docs/v2/writing-algorithms/securities/properties#02-Security-Properties
        
        # 4. Nasdaq - closes at 4 pm & opens at 8:30 Chicago, Also trades at 11 pm till not sure when?
                # OnSecuritiesChanged: Date:2022-12-19 23:00:00, security:MNQ Y6URRFPZ86BL

        # 5. # Links to documentation pertaining 

                # Time Modeling
                # https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/time-modeling/timeslices#03-Properties

                # Futures - Handling Data
                # https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/futures/handling-data


                # To get the current Slice object, define an OnData method or use the CurrentSlice property of your algorithm (outside of the OnData method).
                # If the data object doesn't contain any market data but it contains auxiliary data, the slice.ContainsKey(symbol) method can return true while slice[symbol] returns None.


# Indicator Help

# In QuantConnect/Lean, we have shortcut methods for indicators, they belong to the QCAlgorithm class (use self) and name are upper-cased. These helper methods create a new instance of a indicator object and hook it up to a data consolidator so that the indicator is automatically updated by the engine.
# Since these methods create a new instance, we just should only to call it once (normally in Initialize) and assign it to a class variable to be accessed throughout the algorithm.

# 1. AverageTrueRange:
# https://www.quantconnect.com/forum/discussion/7972/using-atr-and-other-039-complex-039-indicators-with-history/p1
# https://www.quantconnect.com/forum/discussion/11457/warmup-atr-with-history
# https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators/average-true-range


# 2. Aplying Indicators to the continuous contract prices:
        # we don't need to reset the indicator when the contract rolls over.
        # The indicator will just continue to reflect the prices of the continuous contract.

# 3. Aplying Indicators to Specific Mapped contract prices:
        #  reset the indicator if we were applying the indicator to a specific contract
        #  and then we switch to a new contract after the rollover.

# 4. Common Mistakes - Creating Automatic Indicators in a Dynamic Universe: - You can't currently remove the consolidator that LEAN creates to update automatic indicators. 
        # If you add consolidators to a dynamic universe, the consolidators build up over time and slow down your algorithm. 
        # To avoid issues, if you algorithm has a dynamic universe, use manual indicators.
        # However, I think since expired contracts expire (say 15 days after we roll over), the consolidators won't have data to fill so won't be as slow?

# https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/manual-indicators#05-Automatic-Updates
# 5. Automatic Updates for Manual Indicators: To configure automatic updates, create a consolidator and then call the RegisterIndicator method. 
        # If your algorithm has a dynamic universe, save a reference to the consolidator so you can remove it when the universe removes the security. 
        # If you register an indicator for automatic updates, don't call the indicator's Update method or else the indicator will receive double updates.

# 6. Looks like if you need an Indicator before market open, then may have to use manual indicators??
        # Since "Once your algorithm reaches the EndTime of a data point, LEAN sends the data to your OnData method. 
                # For bar data, this is the beginning of the next period. "
        # How about if we use consolidated data in Automatic Indicators - consolidated from much lower time frame
        # Not sure but it may also be that using the above solution, the indicator keeps getting updated through the day

        # The consolidators can update your indicators at each time step or with aggregated bars. By default, LEAN updates data point indicators with the close price of the consolidated bars, but you can change it to a custom data field.



# Insights NOTES

        # 1. Insight Properties
        # https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/key-concepts#06-Insights



        # 2. InsightCollection class is a helper class to manage insights
        # https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/key-concepts#07-Insight-Collection
        




# Insight Related Variables 

        # I think they probably changed it:
        # Direction score - when your buy (sell) insight closed, was the security higher (lower) than when you issued the insight? (binary yes/no)
        # Magnitude score - when your insight closed, had the security moved by as much as you had predicted? (continuous 0->1)

        # 1. Magnitude - Get from Regression Analysis - The insight magnitude should be signed.
        # 2. Confidence as below (based on NAasdaq absolute yesterdayPercentChange)
        #   0 - 1% = 15%
        #   1 - 2% = 30%
        #   2 - 3% = 45%
        #   3 - 4% = 60%
        #   4 - 5% = 75%
        #   >5%    = 90%


        # From Old Discussions - perhaps not as valid now?
        # Direction: You predicted up relative to starting price; if its > starting price you get 1. If price < start: 0. Sum(Backtest) => Average Score.
        # Magnitude: You predicted up 10%; price moves up 5% at insight end time. You get magnitude score of 50%. Sum(Backtest) => Average Score.
        # Magnitude is a harder one to set; though arguably more valuable as most firms want an expected return curve. With a universe of magnitude scores, they can build this expected return. 
        # The average insight value being $0 means winning insights earned the same as losing ones lost. This balance of signals nets $0. It is possible to have a near $0 algorithm and still have a positive return curve!
        
        # INISGHT PERIOD - For those of us who know the actual timestamp we want to predict for, how should we go about determining the period to pass into the insight initializer?
        # https://www.quantconnect.com/forum/discussion/4873/insight-expiry-time/p1

        # Buy and hold can be accomplished using Insights. To do this, we can set the Insight duration to an arbitrarily long duration. Furthermore, if an Up Insight is followed by another Up Insight before the previous Insight expires, the previous position is held. This means, as long as we keep emitting insights with the same direction for a stock, we buy and hold that stock until an Insight is either not emitted or the Insight Direction changes for that stock (a Flat insight liquidates, while a Down Insight flips the position). In the algorithm I posted earlier, the latter method is used (note: I accidentally used a Down Insight instead of a Flat Insight, so I'll attach a fixed version).

        # 1. You state we can set an arbitrarily long expiration date for the insight, but the code you posted appears to have expiration set at month-end. That's not long enough. How could we set the expiration for 30 years? 
                # As long as we follow Insight by another Insight with the same direction, the holdings in the previous Insight is extended. To have a 30 year Insight, set the duration to 30 * 252 = 7560 days (~252 trading days in a year). 

        # 2. If the insight expiration is set at 30 years, the stock would be sold if at any point during this timespan a down insight is emitted for that same stock, is that correct? That would be ideal.
                # This is true, however, the best way to liquidate a position is to use a Flat Insight. A Down Insight will liquidate a position, but then also take a short position (please see my previous comment on the Down Insight). When an Up/Down Insight is followed by a Flat Insight, the position will be liquidated.

        # 3. You state: "as long as we keep emitting insights with the same direction for a stock, we buy and hold that stock until an Insight is either not emitted or the Insight Direction changes for that stock" --> If an up insight is emitted for a stock and is therefore purchased, I want that stock to be continued to be held even if we don't continue emitting up direction insights for that stock. For example, if a stock has a ROIC over 0.7 and is in the bottom quartile for EV-to-EBIT, then an up insight is emitted and the stock is initially purchased. But going forward, now that the stock is being held, it will be sold only if ROIC goes below 0.7, but not if it's no longer in the bottom quartile for EV-to-EBIT. We only care about EV-to-EBIT for the initial purchase, but it's not a metric that's looked at to determine when to sell it. How could this be done with insights?
                # Emit an arbitrarily long insight (e.g. 99999999 days) and emit a Flat Insight when the ROIC is below .7, (Fine Fundamental data can now be accessed through the Security object, see this thread)


# ALPHA Model
                # 2nd Alpha Model based on Cash Price - Only active 2 days in a week (Day after Midweek & weekly reporting)
                # - if cash fell since last time while future finished more than say $20 above cash today, generate a negative Insight for tom
                # - Confidence & Magnitude depends on How far we are from expiry as well as how big is the basis.
                # - Period is for full 6 hours

                # 3rd Alpha Model based on COT NSL - Only applicable Once a week 
                # 4th Alpha Model based on WWPA Weekly Inventory Data - Only applicable Once a week 
                
                # TO DO: Use following functions in only 1 of the Alpha Models
                        # updateModelData
                        # clearModelData
                        # saveModelData
                        # & In scheduler
                        # changed_event in data.SymbolChangedEvents.Values: in Update Function
