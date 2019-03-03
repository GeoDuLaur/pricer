import datetime as dt
import numpy as np
import pandas as pd
from QuantLib import *
from callibriUtils import *

class CInstrument :

    mCalendar = TARGET()
    mDateDuJour = pydate_to_qldate(dt.date.today())
    _mSousJacent=SJ = ""

    def __init__(self,SJ) :
        self._mSousJacent=SJ
        Settings.instance().evaluationDate = self.mDateDuJour
        print(self.mDateDuJour)





#prend en charge les instrument de taux
class CRateInstrument(CInstrument) :
    #create re-linkable handles for discounting and projection curves
    _mDiscountCurveHandle = ""
    _mProjectionCurveHandle = ""

    #indices de taux
    _mDiscountIndex = ""
    _mProjectionIndex = ""

    #rate curves
    _mDiscountCurve = ""
    _mProjectionCurve = ""

    def __init__(self, discountCurveHandle, projectionCurveHandle, discountIndex, projectionIndex, discountCurve, projectionCurve):

        #intiation classe mere
        CInstrument.__init__(self,"toto")
        self._mDiscountCurveHandle = discountCurveHandle
        self._mProjectionCurveHandle = projectionCurveHandle

        #indices de taux
        self._mDiscountIndex = discountIndex
        self._mProjectionIndex = projectionIndex

        #rate curves
        self._mDiscountCurve = discountCurve
        self._mProjectionCurve = projectionCurve

        self._mSettlementDate = self.mCalendar.advance(self.mDateDuJour, Period(2,Days))


#recupere courbe de taux, calcule differents trucs
class CZC(CRateInstrument):


    def __init__(self, discountCurve) :
        self._mDiscountCurve = discountCurve


    def getZC(self, maturity) :
        return self._mDiscountCurve.discount(maturity)

#recupere courbe de taux, calcule differents trucs
class CSwap(CRateInstrument):


    def __init__(self, courbeTaux) :

        #intiation classe mere
        CRateInstrument.__init__(self,courbeTaux[0], courbeTaux[1], courbeTaux[2], courbeTaux[3], courbeTaux[4], courbeTaux[5])

    #construction du swap
    def calcSwap(self, mat, startDate, typeSpread='') :

        nominal = 100
        settleDate = self.mCalendar.advance(self.mDateDuJour, startDate)
        maturity = self.mCalendar.advance(settleDate,mat,Years)

        payFixed = True
        fixedLegFrequency = Annual
        fixedLegAdjustment = ModifiedFollowing
        fixedLegDayCounter = Actual360()
        fixedRate = 0


        spread=0.0
        #spreads=[0.001 + x for x in range(mat) ]
        spreads=[0.001] *40

        fixingDays = 2
        floatingLegDayCounter = Actual360()

        fixedLegTenor = Period(1,Years)
        floatingLegTenor = Period(3,Months)


        fixedSchedule = Schedule(settleDate, maturity,
                                fixedLegTenor, self.mCalendar,
                                fixedLegAdjustment, fixedLegAdjustment,
                                DateGeneration.Backward, False)

        #print(pd.DataFrame({'date': list(fixedSchedule)}))
        floatingSchedule = Schedule(settleDate, maturity,
                                    floatingLegTenor, self.mCalendar,
                                    ModifiedFollowing, ModifiedFollowing,
                                    DateGeneration.Backward, False)

        #print(pd.DataFrame({'date': list(floatingSchedule)}))
        ir_swap = VanillaSwap(VanillaSwap.Receiver, nominal,
                        fixedSchedule, fixedRate, fixedLegDayCounter,
                        floatingSchedule, self._mProjectionIndex, spread,
                        floatingLegDayCounter)

        pricer = DiscountingSwapEngine(self._mDiscountCurveHandle)
        ir_swap.setPricingEngine(pricer)



        '''print ('-----leg 0 ----------------------')
        for i, cf in enumerate(ir_swap.leg(0)):
            print ("%2d    %-18s  %10.4f"%(i+1, cf.date(), cf.amount()))

        print ('-----leg 1 ----------------------')
        for i, cf in enumerate(ir_swap.leg(1)):
            print ("%2d    %-18s  %10.4f"%(i+1, cf.date(), cf.amount()))'''

        print(ir_swap.NPV())
        #print(ir_swap.fixedLegBPS())


        if typeSpread != '' :
            #contruction des listes de spreads
            df=pd.read_table("data/"+typeSpread+".txt", sep = '\t',header = None)
            df.dropna(how='all')
            df.columns = ["Date","Spread"]

            for index, row in df.iterrows():
                dateToTransform = df.iloc[index, df.columns.get_loc('Date')]
                #df.iloc[index, df.columns.get_loc('Date')] = convertFloatDateToPeriod(dateToTransform)
                d=pydate_to_qldate(pydate(dateToTransform))
                df.iloc[index, df.columns.get_loc('Date')] = d
                df.iloc[index, df.columns.get_loc('Spread')]=QuoteHandle(SimpleQuote(df.iloc[index, df.columns.get_loc('Spread')]/100))

            #verificationque la date max des spreads depasse la maturite du swap
            nbLignes = df['Date'].count()
            if df.iloc[nbLignes -1 , df.columns.get_loc('Date')] < maturity :
                #df.set[nbLignes-1 , df.columns.get_loc('Date')] = maturity
                #df.iloc[nbLignes, df.columns.get_loc('Spread')]=df.iloc[nbLignes-1, df.columns.get_loc('Spread')]
                df=df.append([{'Date':maturity, 'Spread':df.iloc[nbLignes-1, df.columns.get_loc('Spread')]}], ignore_index=True)


            list1=df['Date'].tolist()
            list2=df['Spread'].tolist()

            shift = 0.01
            temp_fyc_handle = YieldTermStructureHandle(self._mDiscountCurve)
            temp_dyc_handle = YieldTermStructureHandle(self._mProjectionCurve)
            shiftedForwardCurve = ZeroSpreadedTermStructure(temp_fyc_handle, QuoteHandle(SimpleQuote(shift)))
            #shiftedDiscountCurve = ZeroSpreadedTermStructure(temp_dyc_handle, QuoteHandle(SimpleQuote(shift)))

            spread21 = SimpleQuote(0.01)
            spread22 = SimpleQuote(0.01)
            start_date = self.mDateDuJour
            end_date = self.mCalendar.advance(start_date, Period(11, Years))

            #list1=[start_date, end_date]
            #list2=[QuoteHandle(spread21), QuoteHandle(spread22)]
            #print(list2)
            #print(list1)

            shiftedDiscountCurve = SpreadedLinearZeroInterpolatedTermStructure(
                temp_dyc_handle,
                list2,
                list1
            )
            #self._mDiscountCurveHandle.linkTo(shiftedDiscountCurve)
            self._mProjectionCurveHandle.linkTo(shiftedDiscountCurve)

        print(ir_swap.NPV())


        '''forwardStart = calendar.advance(settlementDate,1,Years)
        forwardEnd = calendar.advance(forwardStart,length,Years)
        fixedSchedule = Schedule(forwardStart, forwardEnd,
                                fixedLegTenor, calendar,
                                fixedLegAdjustment, fixedLegAdjustment,
                                DateGeneration.Forward, False)
        floatingSchedule = Schedule(forwardStart, forwardEnd,
                                    floatingLegTenor, calendar,
                                    floatingLegAdjustment, floatingLegAdjustment,
                                    DateGeneration.Forward, False)

        forward = VanillaSwap(VanillaSwap.Payer, nominal,
                            fixedSchedule, fixedRate, fixedLegDayCounter,
                            floatingSchedule, index, spread,
                            floatingLegDayCounter)
        forward.setPricingEngine(swapEngine)
        '''




