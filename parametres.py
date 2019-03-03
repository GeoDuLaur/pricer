'''
Created on 24 nov. 2018

@author: Vincent Sudre
'''

import datetime as dt
import numpy as np
import pandas as pd
from QuantLib import *
from callibriUtils import *



class CParametre:

    mCalendar = TARGET()
    mDateDuJour = pydate_to_qldate(dt.date.today())
    _mSousJacent=SJ = ""

    def __init__(self,SJ) :
        self._mSousJacent=SJ
        #Settings.instance().evaluationDate = self.mDateDuJour


##############################################################################
##############################################################################
#          TAUX
##############################################################################
##############################################################################
#recupere courbe de taux, calcule differents trucs
class CCourbeTaux(CParametre):

    _mDiscountCurveName = ""
    _mProjectionCurveName = ""
    _mSettlementDays = 2
    _mDiscountCurveDF = pd.DataFrame()
    _mProjectionCurveDF = pd.DataFrame()

    #create re-linkable handles for discounting and projection curves
    _mDiscountCurveHandle = RelinkableYieldTermStructureHandle()
    _mProjectionCurveHandle = RelinkableYieldTermStructureHandle()

    #indices de taux
    _mDiscountIndex = ""
    _mProjectionIndex = ""

    #rate curves
    _mDiscountCurve = ""
    _mProjectionCurve = ""

    #helpers
    _mHelpersDiscount = []
    _mHelpersProjection = []



    _mSettlementDate = "";

    def __init__(self, discountCurve='', projectionCurve=''):
        #intiation classe mere
        CParametre.__init__(self,discountCurve)
        self._mDiscountCurveName = discountCurve;
        if projectionCurve == '' :
            projectionCurve = discountCurve
        self._mProjectionCurveName = projectionCurve

        #on cree l index adequat
        self._mDiscountIndex = getRateIndex(self._mDiscountCurveName)
        #self._mProjectionIndex = getRateIndex(self._mProjectionCurveName)
        self._mProjectionIndex = Euribor3M(self._mProjectionCurveHandle)

        self._mSettlementDate = self.mCalendar.advance(self.mDateDuJour, Period(2,Days))

    #load curve from text file
    def _loadCurveFromFile(self, curveName) :

        #mise en dataframe de la matrice
        dfTaux=pd.read_table("data/"+curveName+".txt", sep = '\t',header = 0)
        dfTaux = dfTaux.dropna(how='all')

        #suppression colonnes de merde
        dfTaux.drop('Enable/Disable', axis=1, inplace=True)
        dfTaux.drop('Rate code', axis=1, inplace=True)

        #transforme les taux en float
        dfTaux['Rate']=dfTaux['Rate'].apply(lambda x: float(x.replace(',','.')))

        #si type eonia
        if curveName == "EONIA" :
            dfTaux['Type']='ois'
        else :
            dfTaux['Type']='swap'


        #remplacement de la premiere valeur par la date en QantLib date
        #et determination du type de taux : deposit, future, swap
        for index, row in dfTaux.iterrows():
            dateToTransform = dfTaux.iloc[index, dfTaux.columns.get_loc('Date')]
            d = pydate_to_qldate(pydate(dateToTransform))

            dateDansUnAn = self.mCalendar.advance(self.mDateDuJour, Period(7,Months))
            if d < dateDansUnAn :
                dfTaux.iloc[index, dfTaux.columns.get_loc('Type')]='deposit'

            #avance de 2 jours pour etre sur la bonne maturite du futur EUR3M
            dfTaux.iloc[index, dfTaux.columns.get_loc('Date')]=self.mCalendar.advance(d, Period(2,Days))


            if dfTaux.iloc[index, dfTaux.columns.get_loc('Rate')] > 80 :
               dfTaux.iloc[index, dfTaux.columns.get_loc('Type')]='future'
            else:
                #return a period as date instead of Date
                dfTaux.iloc[index, dfTaux.columns.get_loc('Date')]=convertFloatDateToPeriod(dateToTransform)
                dfTaux.iloc[index, dfTaux.columns.get_loc('Rate')]=dfTaux.iloc[index, dfTaux.columns.get_loc('Rate')]/100


        return dfTaux

    #reload rates from market and read them from firebase
    def _loadCurveFromLive(self) :
        print("coneexion firebase")

    #construction ratehelper
    def _constructRateHelper(self, dfTaux, rateIndex) :

        #construction du dictionnaire taux future
        dfTemp = dfTaux[dfTaux['Type']=='future'].copy()
        list1=dfTemp['Date']
        list2=dfTemp['Rate']
        futuresDict=dict(list(zip(list1, list2)))

        #construction du dictionnaire taux deposit
        dfTemp = dfTaux[dfTaux['Type']=='deposit'].copy()
        list1=dfTemp['Date']
        list2=dfTemp['Rate']
        depositDict=dict(list(zip(list1, list2)))

        #construction du dictionnaire taux swap
        dfTemp = dfTaux[dfTaux['Type']=='swap'].copy()
        list1=dfTemp['Date']
        list2=dfTemp['Rate']
        swapDict=dict(list(zip(list1, list2)))

        #construction du dictionnaire taux ois
        dfTemp = dfTaux[dfTaux['Type']=='ois'].copy()
        list1=dfTemp['Date']
        list2=dfTemp['Rate']
        oisDict=dict(list(zip(list1, list2)))


        # convert them to Quote objects
        for n in depositDict.keys():
            depositDict[(n)] = SimpleQuote(depositDict[(n)])
        #for n,m in FRAs.keys():
        #    FRAs[(n,m)] = SimpleQuote(FRAs[(n,m)])
        for d in futuresDict.keys():
            futuresDict[d] = SimpleQuote(futuresDict[d])
        for n in swapDict.keys():
            swapDict[(n)] = SimpleQuote(swapDict[(n)])
        for n in oisDict.keys():
            oisDict[(n)] = SimpleQuote(oisDict[(n)])

        # build rate helpers
        depositHelpers = []
        for n in depositDict.keys() :
            drh = DepositRateHelper(QuoteHandle(depositDict[(n)]),
                                                n, rateIndex.fixingDays(),
                                                rateIndex.fixingCalendar(), rateIndex.businessDayConvention(),
                                                rateIndex.endOfMonth(), rateIndex.dayCounter())
            depositHelpers.append(drh)

        oisHelpers = []
        for n in oisDict.keys() :
            drh = OISRateHelper(self._mSettlementDays,
                    n,
                    QuoteHandle(oisDict[(n)]),
                    rateIndex)
            oisHelpers.append(drh)

        '''dayCounter = Actual360()
        settlementDays = 2
        fraHelpers = [ FraRateHelper(QuoteHandle(FRAs[(n,m)]),
                                    n, m, settlementDays,
                                    calendar, ModifiedFollowing,
                                    False, dayCounter)
                    for n, m in FRAs.keys() ]'''


        months = 3
        futuresHelpers = [ FuturesRateHelper(QuoteHandle(futuresDict[d]),
                                            d,
                                            months,
                                            self.mCalendar,
                                            rateIndex.businessDayConvention(),
                                            rateIndex.endOfMonth(),
                                            rateIndex.dayCounter(),
                                            QuoteHandle(SimpleQuote(0.0)))
                        for d in futuresDict.keys()]




        swapHelpers = [ SwapRateHelper(QuoteHandle(swapDict[(n)]),
                                            n,
                                            self.mCalendar,
                                            Annual,
                                            ModifiedFollowing,
                                            Actual360(),
                                            rateIndex,
                                            QuoteHandle(), Period(0, Days), self._mDiscountCurveHandle)
                        for n in swapDict.keys()
                        ]


        # term-structure construction
        return depositHelpers + futuresHelpers + oisHelpers + swapHelpers

    #chargement de la curve en fonction de la source et construction
    def loadCurve(self) :
        self._mDiscountCurveDF = self._loadCurveFromFile(self._mDiscountCurveName)
        self._mProjectionCurveDF= self._loadCurveFromFile(self._mProjectionCurveName)

        #print (self._mDiscountCurveDF)
        #print (self._mProjectionCurveDF)

        #construction de la courbe de discount
        self._mHelpersDiscount = self._constructRateHelper(self._mDiscountCurveDF, self._mDiscountIndex)
        self._mDiscountCurve = PiecewiseFlatForward (0, self._mDiscountIndex.fixingCalendar(), self._mHelpersDiscount, self._mDiscountIndex.dayCounter())
        self._mDiscountCurve.enableExtrapolation()
        # link discount curve to eonia curve
        self._mDiscountCurveHandle.linkTo(self._mDiscountCurve);


        #construction de la courbe de projection
        self._mHelpersProjection = self._constructRateHelper(self._mProjectionCurveDF, self._mProjectionIndex)
        #self.mCurve = PiecewiseFlatForward(self.mDateDuJour, helpers, Actual360())
        self._mProjectionCurve = PiecewiseFlatForward(0, self._mProjectionIndex.fixingCalendar(), self._mHelpersProjection, self._mProjectionIndex.dayCounter())
        self._mProjectionCurve.enableExtrapolation()
        # link projection curve to euribor curve
        self._mProjectionCurveHandle.linkTo(self._mProjectionCurve)


    def getDiscountCurveHandle(self) :
        return self._mDiscountCurveHandle


    def getProjectionCurveHandle(self) :
        return self._mProjectionCurveHandle


    def getDiscountIndex(self) :
        return self._mDiscountIndex


    def getProjectionIndex(self) :
        return self._mProjectionIndex

    def getDiscountCurve(self) :
        return self._mDiscountCurve

    def getProjectionCurve(self) :
        return self._mProjectionCurve

    def getCourbeTaux(self) :
        return [self._mDiscountCurveHandle,self._mProjectionCurveHandle,self._mDiscountIndex,self._mProjectionIndex,self._mDiscountCurve,self._mProjectionCurve]


    #retourne le dataframe
    def getRateMatrix(self) :
        return dfTaux



##############################################################################
##############################################################################
#          VOLATILITE
##############################################################################
##############################################################################
#recupere surface de vol et interpole
class CVolatilite(CParametre):

    def __init__(self, SJ):

        #intiation classe mere
        CParametre.__init__(self, SJ)

        #... et parametres
        self._mPivotVol = 100
        self._mDfVol = []


    def loadVolFromFile1(self, fileName) :

        #mise en dataframe de la matrice
        self._mDfVol=pd.read_table("data/"+fileName, sep = '\t',header = 0)

        #recuperation du spot equivalent a 100%
        s=self._mDfVol.T.iloc[0]
        s2=s.str.contains('100,00%', regex=False)
        self._mPivotVol = float(s[s2.tolist().index(True)].split('-')[1].replace(',','.'))

        #remplacement de la premiere valeur par les strikes spots
        self._mDfVol.index.names = ['Strikes']
        for index, row in self._mDfVol.iterrows():
            self._mDfVol.iloc[[index], [0]]=float(self._mDfVol.iloc[index][0].split('-')[1].replace(',','.'))


        #les strikes sont definis comme index de la matrice
        self._mDfVol.rename(columns={'Unnamed: 0': 'Strikes'}, inplace=True)
        self._mDfVol.set_index('Strikes', inplace=True)

        #changement d'en-tete des colonnes : transformation des dates flottantes en date fixes
        for col in self._mDfVol.columns:
            toto=convertFloatDateToFixedDate(col)
            #toto=convertDateToString(toto)
            self._mDfVol.rename(columns={col: toto}, inplace=True)

        self._mDfVol=self._mDfVol.applymap(lambda x: float(x.replace(',','.')))


    def loadVolFromFile2(self, fileName, pivot) :

        #mise en dataframe de la matrice
        self._mDfVol=pd.read_table("data/"+fileName, sep = '\t',header = 0)

        self._mPivotVol = pivot


        #remplacement de la premiere valeur par les strikes spots
        #self._mDfVol.index.names = ['Strikes']
        for index, row in self._mDfVol.iterrows():
            self._mDfVol.iloc[[index], [0]]=float(self._mDfVol.iloc[index][0])*self._mPivotVol/100

        #les strikes sont definis comme index de la matrice
        self._mDfVol.rename(columns={'Euro Stoxx 50': 'Strikes'}, inplace=True)

        self._mDfVol.set_index('Strikes', inplace=True)
        #print(self._mDfVol.head())

        #changement d'en-tete des colonnes : transformation des dates flottantes en date fixes
        for col in self._mDfVol.columns:
            toto=convertStringToDate(col)
            #toto=convertDateToString(toto)
            self._mDfVol.rename(columns={col: toto}, inplace=True)

        self._mDfVol=self._mDfVol.applymap(lambda x: float(x.replace(',','.')))
        print(self._mDfVol.head())


    #retourne une vol interpolee
    def getVol(self, strike, maturite, percent=False, datetype='Fixed') :
        d=convertStringToDate(maturite)
        return getExtrapolatedInterpolatedValue(self._mDfVol.copy(), strike, d)


    def getNBMaturities(self):
        return len(self._mDfVol.axes[1])-1

    def getNBStrikes(self):
        return len(self._mDfVol.axes[0])



    #renvoie le spot pivot de la vol
    def getPivolVol(self):
        return self._mPivotVol

    def getAllStrikes(self,inPercent=''):
        if inPercent=='': return self.spotStrikes
        else : return self.percentStrikes

    #retourne en vol black
    def getBlackVarianceSurface(self) :


        #for col in self._mDfVol.columns:
        #    dateToTransform = self._mDfVol.columns(col)
        expiration_dates = list(self._mDfVol)
        expiration_dates_ql = expiration_dates.copy()
        for col in range(len(expiration_dates)):
            expiration_dates_ql[col] = pydate_to_qldate(expiration_dates[col])



        strikes = list(self._mDfVol.index.values)

        implied_vols = Matrix(len(strikes), len(expiration_dates_ql))
        i=0
        for index, row in self._mDfVol.iterrows():
            for col in range(len(expiration_dates)):
                implied_vols[i][col] = self._mDfVol.iloc[i, col]
            i=i+1




        return BlackVarianceSurface(self.mDateDuJour,
                                        self.mCalendar,
                                        expiration_dates_ql,
                                        strikes,
                                        implied_vols,
                                    Actual365Fixed())


##############################################################################
##############################################################################
#          DIVIDENDES
##############################################################################
##############################################################################
#recupere courbe de dividende et construit un tableau
class CDividende(CParametre) :
    _mDFDivs = []
    _mDFDivsProg = []
    _mPivotDiv = 100
    _mDivCurve =None

    def __init__(self, SJ):
        #intiation classe mere
        CParametre.__init__(self,SJ)
        self._mDFDivs=pd.read_table("data/DIVS_"+self._mSousJacent+".txt", sep = '\t',header = 0)
        self._mDFDivsProg=pd.read_table("data/TSEPSILON_"+self._mSousJacent+".txt", sep = '\t',header = 0)

    def loadDivs(self) :

        ##############################################################################
        #          on complete le tableau a partir de celui des progressions
        ##############################################################################
        #menage
        self._mDFDivs = self._mDFDivs.dropna(how='all')
        #transformation en date quantlib
        self._mDFDivs.rename(columns = {'Comment':'Stock'}, inplace = True)
        self._mDFDivs.rename(columns = {'Ex-Div Date':'Ex-Date'}, inplace = True)
        for index, row in self._mDFDivs.iterrows():
            dateToTransform = self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Ex-Date')]
            self._mDFDivs.loc[index, 'Ex-Date (util)'] = dateToTransform
            d = pydate_to_qldate(pydate(dateToTransform))
            self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Ex-Date')] = d
            self._mDFDivs.loc[index, 'Year'] = d.year()


        #suppression colonnes de merde
        self._mDFDivs.drop('Date', axis=1, inplace=True)
        self._mDFDivs.drop('Pay Date', axis=1, inplace=True)
        self._mDFDivs.drop('Nature', axis=1, inplace=True)
        self._mDFDivs.drop('Ref. Year', axis=1, inplace=True)
        self._mDFDivs.drop('Identifier', axis=1, inplace=True)

        #on remplace le div par le div x AllIn
        self._mDFDivs['Brut Amount'] = self._mDFDivs['Amount'].apply(lambda x: float(x.replace(',','.')))
        self._mDFDivs['Amount'] = self._mDFDivs['Amount'].apply(lambda x: float(x.replace(',','.'))) * self._mDFDivs['All-In (%)'].apply(lambda x: float(x.replace(',','.')))/100
        self._mDFDivs.drop('All-In (%)', axis=1, inplace=True)



        #recuperation des progressions dans df a part
        dfTemp = self._mDFDivs[self._mDFDivs['Type']=='Progression'].copy()
        #suppression de ces lignes
        self._mDFDivs = self._mDFDivs[self._mDFDivs['Type']!='Progression']
        #suppression colone cash/progression
        self._mDFDivs.drop('Type', axis=1, inplace=True)

        #print(self._mDFDivs)

        dfTemp.drop('Type', axis=1, inplace=True)
        dfTemp['Amount'] = dfTemp['Amount'].apply(lambda x: 1+x/100)

        ##############################################################################
        #          on complete le tableau a partir de celui des progressions
        ##############################################################################
        dfTemp.reset_index(inplace=True)
        for index, row in dfTemp.iterrows():
            d = dfTemp.iloc[index, dfTemp.columns.get_loc('Ex-Date')]
            #si c'est la premiere date  on drope dans l autre dataframe toutes les ates d un avant
            if (index == 0) :
                backDate = self.mCalendar.advance(d, Period(-1,Years))
                backDate = min(backDate, self.mDateDuJour)
                self._mDFDivs.drop(self._mDFDivs[self._mDFDivs['Ex-Date'] < backDate].index, inplace=True)

            #on ajoute au tableau le div de l an dernier x progression
            progression = dfTemp.iloc[index, dfTemp.columns.get_loc('Amount')]
            #on extrait l anne du tableau precedent et on la joute au tableau
            dfOneYear = self._mDFDivs[self._mDFDivs['Year']==d.year()].copy()
            dfOneYear['Ex-Date'] = dfOneYear['Ex-Date'].apply(lambda x: self.mCalendar.advance(x, Period(1,Years)))
            dfOneYear['Year'] = dfOneYear['Year'].apply(lambda x: x+1)
            dfOneYear['Amount'] = dfOneYear['Amount'].apply(lambda x: x*progression)
            dfOneYear['Brut Amount'] = dfOneYear['Brut Amount'].apply(lambda x: x*progression)
            self._mDFDivs = self._mDFDivs.append(dfOneYear)
            #print (dfOneYear)
        self._mDFDivs.reset_index(inplace=True)
        self._mDFDivs.drop('index', axis=1, inplace=True)

        #print(self._mDFDivs)
        #recuperation de la dynamique epsilon
        self._mDFDivsProg = self._mDFDivsProg.dropna(how='all')
        #recuperation pivot dividendes
        self._mPivotDiv = self._mDFDivsProg.iloc[len(self._mDFDivsProg)-1][0].replace(',','.')
        self._mDFDivsProg.drop([(len(self._mDFDivsProg)-1)],axis=0,inplace=True)
        #self._mDFDivsProg = self._mDFDivsProg.iloc[-1,]

        #remise aux normes du tableau
        for index, row in self._mDFDivsProg.iterrows():
            dateToTransform = self._mDFDivsProg.iloc[index, self._mDFDivsProg.columns.get_loc('Term')]
            #d = pydate_to_qldate(pydate(dateToTransform))
            d = pydate(pydate(dateToTransform))
            self._mDFDivsProg.iloc[index, self._mDFDivsProg.columns.get_loc('Term')] = d
        #self._mDFDivsProg.fillna(0)
        self._mDFDivsProg['Value'] = self._mDFDivsProg['Value'].apply(lambda x: float(x.replace(',','.')))
        liste1 = self._mDFDivsProg['Term'].values.tolist()
        liste2 = self._mDFDivsProg['Value'].values.tolist()
        self._mDFDivsProg.set_index('Term', inplace=True)



    #retourne le taux de proporionnalite a une date
    def getDivPropAtDate(self, d) :
        return getExtrapolatedInterpolatedValue1D(self._mDFDivsProg.copy(), d)


    #applique le courbe de discount sur chaque div
    def applyDiscount(self, zc) :
        for index, row in self._mDFDivs.iterrows():
            a = self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Amount')]
            aBrut = self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Brut Amount')]
            aZC = zc.getZC(self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Ex-Date')])

            self._mDFDivs.loc[index, 'Discount Amount'] = a*aZC
            self._mDFDivs.loc[index, 'Discount Brut Amount'] = aBrut*aZC
            if index == 0 :
                self._mDFDivs.loc[index, 'Sum Discount Amount'] = a*aZC
            else :
                self._mDFDivs.loc[index, 'Sum Discount Amount'] = a*aZC + self._mDFDivs.loc[index-1, 'Sum Discount Amount']


        '''print(self._mDFDivs)
        toto = self._mDFDivs.copy()
        toto.set_index('Ex-Date (util)', inplace=True)
        print(toto.groupby('Year')['Brut Amount'].sum())'''
        #print(self._mDFDivs.columns.tolist())


    def getTSDividend(self) :
        dates2 = []
        divs2 = []

        if self._mDivCurve is None :
            dates = self._mDFDivs['Ex-Date'].tolist()
            divs = self._mDFDivs['Amount'].tolist()

            i=0
            previous_d = None
            for d in dates :
                if previous_d is not None and d == previous_d :
                    divs2[-1] = divs2[-1] + divs[i]
                else :
                    dates2.append(dates[i])
                    divs2.append(divs[i])

                previous_d = d
                i=i+1


            dc = ZeroCurve(dates2, divs2, Actual360(),TARGET())
            dc.enableExtrapolation()


            # Setup the yield termstructure
            self._mDivCurve = YieldTermStructureHandle(dc)

        return self._mDivCurve

    def getSumDiscountAmount(self, maturity) :
        #df = self._mDFDivs.drop(self._mDFDivs[self._mDFDivs['Ex-Date'] < maturity].index)
        return self._mDFDivs['Discount Amount'][self._mDFDivs['Ex-Date'] <= maturity].sum()


##############################################################################
##############################################################################
#          REPOS
##############################################################################
##############################################################################
#recupere courbe de dividende et construit un tableau
class CRepos(CParametre) :
    _mDFRepos = []

    def __init__(self, SJ):
        #intiation classe mere
        CParametre.__init__(self,SJ)
        self._mDFRepos=pd.read_table("data/REPOS_"+self._mSousJacent+".txt", sep = '\t',header = 0)


    def loadRepos(self) :

        ##############################################################################
        #          on complete le tableau a partir de celui des progressions
        ##############################################################################
        #menage
        self._mDFRepos = self._mDFRepos.dropna(how='all')
        #transformation en date quantlib
        '''self._mDFDivs.rename(columns = {'Comment':'Stock'}, inplace = True)
        self._mDFDivs.rename(columns = {'Ex-Div Date':'Ex-Date'}, inplace = True)
        for index, row in self._mDFDivs.iterrows():
            dateToTransform = self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Ex-Date')]
            self._mDFDivs.loc[index, 'Ex-Date (util)'] = dateToTransform
            d = pydate_to_qldate(pydate(dateToTransform))
            self._mDFDivs.iloc[index, self._mDFDivs.columns.get_loc('Ex-Date')] = d
            self._mDFDivs.loc[index, 'Year'] = d.year()
        '''
        #transforme les taux en float
        self._mDFRepos['Repo rate'] = self._mDFRepos['Repo rate'].apply(lambda x: float(x.replace(',','.')))/100
        #suppression colonnes de merde
        self._mDFRepos.drop('Bid', axis=1, inplace=True)
        self._mDFRepos.drop('Ask', axis=1, inplace=True)

        for index, row in self._mDFRepos.iterrows():
            dateToTransform = self._mDFRepos.iloc[index, self._mDFRepos.columns.get_loc('Date')]
            self._mDFRepos.iloc[index, self._mDFRepos.columns.get_loc('Date')] = pydate(dateToTransform)

        self._mDFRepos.set_index('Date', inplace=True)
        #print(self._mDFRepos)

    #retourne le repo a une date
    def getRepoAtDate(self, d) :
        return getExtrapolatedInterpolatedValue1D(self._mDFRepos.copy(), d)
