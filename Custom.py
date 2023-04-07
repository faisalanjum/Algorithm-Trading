from AlgorithmImports import *
from AlgorithmImports import *

class Cash(PythonData):
    def GetSource(self,
         config: SubscriptionDataConfig,
         date: datetime,
         isLive: bool) -> SubscriptionDataSource:
        source="https://northamerica-northeast1-cross-asset-other-commodities.cloudfunctions.net/http_api?src=cwpenergy&data=cash&match=true"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile,FileFormat.UnfoldingCollection)

    def Reader(self,
         config: SubscriptionDataConfig,
         line: str,
         date: datetime,
         isLive: bool) -> BaseData:
    
        objects = []
        data = json.loads(line)

        if len(data) == 0:
            return None

        for datum in data:
            
            index = Cash()
            index.Symbol = config.Symbol
            index.Time = datetime.strptime(datum["pubdate"], "%Y-%m-%d")
            index.EndTime = index.Time + timedelta(1)
            index.Value= float(datum["settle_fin"])
            index["code"] = str(datum["code"])
            index["year"] =int(datum["year"])
            index["month"]=int(datum["month"])
            index["week"]=int(datum["week"])
            index["date"]=datetime.strptime(datum["pubdate"], '%Y-%m-%d')
            index["cmeexpiry"]=datetime.strptime(datum["cme_exp"], '%Y-%m-%d')
            index["basis"]=float(datum["basis"])
            index["settlefin"]=float(datum["settle_fin"])
            index["settlephys"]=float(datum["settle_phys"])
            index["shortdesc"]=str(datum["shortdesc"])
            index["season"]=str(datum["season"])
            index["length"]=str(datum["length"])
            index["grade"]=str(datum["grade"])
            index["size"]=str(datum["size"])
            index["season"]=str(datum["season"])
            index["pricepoint"]=str(datum["pricepoint"])
            index["dest"]=str(datum["dest"])
            index["origin"]=str(datum["origin"])
            index["finish"]=str(datum["finish"])
            
            objects.append(index)

        return BaseDataCollection(objects[-1].EndTime, config.Symbol, objects)
      
class Settled(PythonData):
    ''' Settled Price Lumber'''

    def GetSource(self, config, date, isLive):
        source = "http://northamerica-northeast1-cross-asset-other-commodities.cloudfunctions.net/http_api?src=cwpenergy&data=settledprice&contract=1"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile,FileFormat.UnfoldingCollection)

    def Reader(self, config, line, date, isLive):
        objects = []
        data = json.loads(line)
        for datum in data:
            try:
                index = Settled()
                index.Symbol = config.Symbol
                index.Time = datetime.strptime(datum["date"], "%Y-%m-%d")
                index.EndTime = index.Time + timedelta(1)
                index.Value=float(datum["settle_price"])
                index["date"]=datum["date"]
                index["ranking"] = str(datum["ranking"])
                index["openingprice"] =float(datum["opening_price"])
                index["dayhighprice"]=float(datum["day_high_price"])
                index["daylowprice"]=float(datum["day_low_price"])
                index["settleprice"]=float(datum["settle_price"])
                index["prevdayvol"]=float(datum["prev_day_vol"])
                index["prevdayopeninterest"]=float(datum["prev_day_open_interest"])
                index["mmy"]=datetime.strptime(datum["mmy"], '%Y-%m-%d')
                index["maturity"]=datetime.strptime(datum["maturity_date"], '%Y-%m-%d')

                objects.append(index)

            except Exception as e:
                # Do nothing, possible error in json decoding
                raise e

        return BaseDataCollection(objects[0].Time,objects[-1].EndTime, config.Symbol, objects)


class Western(PythonData):
   
    def GetSource(self, config, date, isLive):
        source = "https://northamerica-northeast1-cross-asset-other-commodities.cloudfunctions.net/http_api?src=lumberdatasources&data=wwpa&tbl=barometer_western"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile,FileFormat.UnfoldingCollection)

    def Reader(self, config, line, date, isLive):
        objects = []
        data = json.loads(line)
        for datum in data:
            try:
                index = Western()
                index.Symbol = config.Symbol
                index.Time = datetime.strptime(datum["Timestamp"], "%Y-%m-%d")
                index.EndTime=index.Time + timedelta(1)
                index.Value=float(datum["Inventories"])
                index["date"]=datum["Timestamp"]
                index["Inventories"] = str(datum["Inventories"])
                index["Month"] =int(datum["Month"])
                index["Orders"]=int(datum["Orders"])
                index["Production"]=int(datum["Production"])
                index["Shipments"]=int(datum["Shipments"])
                index["Unfilled"]=int(datum["Unfilled"])
                index["Year"]=int(datum["Year"])
                index["Day"]=int(datum["Day"])
               
                objects.append(index)

            except Exception as e:
                # Do nothing, possible error in json decoding
                raise e

        return BaseDataCollection(objects[0].Time,objects[-1].Time, config.Symbol, objects)


class Disaggregated(PythonData):
    '''Disaggregated Custom Data Class'''
    def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
        report="disaggregated_fut"
        source = f"https://northamerica-northeast1-cross-asset-other-commodities.cloudfunctions.net/http_api?src=lumberdatasources&data=cot&tbl=disaggregated&report={report}"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile,FileFormat.UnfoldingCollection)

    def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:

        objects = []
        data = json.loads(line)

        if len(data) == 0:
            return None

        for datum in data:

            try:
            
                index = Disaggregated()
                index.Symbol = config.Symbol
                index.Time = datetime.strptime(datum["Date"], "%Y-%m-%d")
                index.EndTime = index.Time + timedelta(1)
                index.Value= float(datum["M_Money_Positions_Long_All"])
                index["Date"]=datum["Date"]
                index["Mmoneypositionslongall"]=float(datum["M_Money_Positions_Long_All"])
                index["MMoneyPositionsLongOld"]=float(datum["M_Money_Positions_Long_Old"])
                index["MMoneyPositionsLongOther"]=float(datum["M_Money_Positions_Long_Other"])
                index["MMoneyPositionsShortAll"]=float(datum["M_Money_Positions_Short_All"])
                index["MMoneyPositionsShortOld"]=float(datum["M_Money_Positions_Short_Old"])
                index["MMoneyPositionsShortOther"]=float(datum["M_Money_Positions_Short_Other"])
                index["MMoneyPositionsSpreadAll"]=float(datum["M_Money_Positions_Spread_All"])
                index["MMoneyPositionsSpreadOld"]=float(datum["M_Money_Positions_Spread_Old"])
                index["MMoneyPositionsSpreadOther"]=float(datum["M_Money_Positions_Spread_Other"])
                index["NonReptPositionsLongAll"]=float(datum["NonRept_Positions_Long_All"])
                index["NonReptPositionsLongOld"]=float(datum["NonRept_Positions_Long_Old"])
                index["NonReptPositionsLongOther"]=float(datum["NonRept_Positions_Long_Other"])
                index["NonReptPositionsShortAll"]=str(datum["NonRept_Positions_Short_All"])
                index["NonReptPositionsShortOld"]=float(datum["NonRept_Positions_Short_Old"])
                index["NonReptPositionsShortOther"]=float(datum["NonRept_Positions_Short_Other"])
                index["OpenInterestAll"]=float(datum["Open_Interest_All"])
                index["OpenInterestOld"]=float(datum["Open_Interest_Old"])
                index["OpenInterestOther"]=float(datum["Open_Interest_Other"])
                index["OtherReptPositionsLongAll"]=float(datum["Other_Rept_Positions_Long_All"])
                index["OtherReptPositionsLongOld"]=float(datum["Other_Rept_Positions_Long_Old"])
                index["OtherReptPositionsShortAll"]=float(datum["Other_Rept_Positions_Short_All"])
                index["OtherReptPositionsShortOld"]=float(datum["Other_Rept_Positions_Short_Old"])
                index["OtherReptPositionsShortOther"]=float(datum["Other_Rept_Positions_Short_Other"])
                index["OtherReptPositionsSpreadAll"]=float(datum["Other_Rept_Positions_Spread_All"])
                index["OtherReptPositionsSpreadOld"]=float(datum["Other_Rept_Positions_Spread_Old"])
                index["OtherReptPositionsSpreadOther"]=float(datum["Other_Rept_Positions_Spread_Other"])
                index["ProdMercPositionsLongAll"]=float(datum["Prod_Merc_Positions_Long_All"])
                index["ProdMercPositionsLongOld"]=float(datum["Prod_Merc_Positions_Long_Old"])
                index["ProdMercPositionsLongOther"]=float(datum["Prod_Merc_Positions_Long_Other"])
                index["ProdMercPositionsShortAll"]=float(datum["Prod_Merc_Positions_Short_All"])
                index["ProdMercPositionsShortOld"]=float(datum["Prod_Merc_Positions_Short_Old"])
                index["ProdMercPositionsShortOther"]=float(datum["Prod_Merc_Positions_Short_Other"])
                index["SwapPositionsLongOther"]=float(datum["Swap_Positions_Long_Other"])

                objects.append(index)

            except Exception as e:
                # Do nothing, possible error in json decoding
                raise e

        return BaseDataCollection(objects[-1].EndTime, config.Symbol, objects)


mapped_attr ={

    "DISAGGREGATED.Disaggregated":
    [
    "Date",
    "Mmoneypositionslongall",
    "Mmoneypositionslongold",
    "Mmoneypositionslongother",
    "Mmoneypositionsshortall",
    "Mmoneypositionsshortold",
    "Mmoneypositionsshortother",
    "Mmoneypositionsspreadall",
    "Mmoneypositionsspreadold",
    "Mmoneypositionsspreadother",
    "Nonreptpositionslongall",
    "Nonreptpositionslongold",
    "Nonreptpositionslongother",
    "Nonreptpositionsshortall",
    "Nonreptpositionsshortold",
    "Nonreptpositionsshortother",
    "Openinterestall",
    "Openinterestold",
    "Openinterestother",
    "Otherreptpositionslongall",
    "Otherreptpositionslongold",

    "Otherreptpositionsshortall",
    "Otherreptpositionsshortold",
    "Otherreptpositionsshortother",
    "Otherreptpositionsspreadall",
    "Otherreptpositionsspreadold",
    "Otherreptpositionsspreadother",
    "Prodmercpositionslongall",
    "Prodmercpositionslongold",
    "Prodmercpositionslongother",
    "Prodmercpositionsshortall",
    "Prodmercpositionsshortold",
    "Prodmercpositionsshortother",
    "Swappositionslongother"],
      

    'WESTERN.Western':['Date',
    'Inventories',
    'Month',
    'Orders',
    'Production',
    'Shipments',
    'Unfilled',
    'Year',
    'Day'] ,

    "CASH.Cash":[
    'Code',
    'Year',
    'Month',
    'Week',
    'Date',
    "Cmeexpiry",
    "Basis",
    "Settlefin",
    "Settlephys",
    "Shortdesc",
    "Season",
    "Length",
    "Grade",
    "Size",
    "Season",
    "Pricepoint",
    "Dest",
    "Origin",
    "Finish",
   
   ],


   "SETTLED.Settled":[
    'Date',
    'Ranking',
    'Dayhighprice',
    'Daylowprice',
    'Settleprice',
    'Openingprice',
    'Prevdayvol',
    'Prevdayopeninterest',
    'Mmy',
    'Maturity',
    ],


}



#function to create dict from objects
def create_dict(obj):

    attr=mapped_attr[str(obj.Symbol)]

    dct={}
    dct["Symbol"]=str(obj.Symbol)
    dct["Value"]=float(obj.Value)   
    
    for at in attr:
        dct[at]=getattr(obj,at)

    return dct

