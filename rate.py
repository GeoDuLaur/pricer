
import datetime as dt
import numpy as np
import pandas as pd
from QuantLib import *
from callibriUtils import *

# create common data
todaysDate=Date(7, 7, 2017)
print(todaysDate)
dayCounter = Actual360()
calendar = TARGET()
settlementDate = calendar.advance(todaysDate, Period(2, Days))
settlementDays = 2
Settings.instance().evaluationDate = todaysDate

#create re-linkable handles for discounting and projection curves
discountCurve = RelinkableYieldTermStructureHandle()
projectionCurve = RelinkableYieldTermStructureHandle()

# create container for all rate helpers
rateHelpers=[]

#create required indices
eoniaIndex = Eonia()
#forward euribor fixings are requested from dual-curve-bootstrapped projection curve
euriborIndex = Euribor6M(projectionCurve)


#eonia curve
#create first cash instrument for eonia curve using deposit rate helper
rateHelpers.append(DepositRateHelper(QuoteHandle(SimpleQuote(-0.0036)),
                    Period(1, Days), eoniaIndex.fixingDays(),
                    eoniaIndex.fixingCalendar(), eoniaIndex.businessDayConvention(),
                    eoniaIndex.endOfMonth(), eoniaIndex.dayCounter()))


# create source data for eonia swaps (period, rate)
eoniaSwapData ={  Period(6, Months): -0.00353,
                  Period(1, Years):-0.00331,
                  Period(2, Years):-0.00248,
                  Period(3, Years):-0.00138,
                  Period(4, Years):-0.0001245,
                  Period(5, Years):0.0011945,
                  Period(7, Years):0.00387,
                  Period(10, Years): 0.007634}


#create other instruments for eonia curve using ois rate helper
for n in eoniaSwapData.keys() :
  drh = OISRateHelper(settlementDays,
        n,
        QuoteHandle(SimpleQuote(eoniaSwapData[(n)])),
        eoniaIndex)
  rateHelpers.append(drh)


#create eonia curve
eoniaCurve = PiecewiseFlatForward (0, eoniaIndex.fixingCalendar(), rateHelpers, eoniaIndex.dayCounter())
eoniaCurve.enableExtrapolation()
# link discount curve to eonia curve
discountCurve.linkTo(eoniaCurve);

# clear rate helpers container
#rateHelpers.clear();


# euribor curve
# cash part
rateHelpers2 = []
rateHelpers2.append(DepositRateHelper(QuoteHandle(SimpleQuote(-0.00273)),
                                    Period(6, Months),
                                    settlementDays, calendar, euriborIndex.businessDayConvention(),
                                    euriborIndex.endOfMonth(), euriborIndex.dayCounter()))

# fra part
#rateHelpers2.append(FraRateHelper(QuoteHandle(SimpleQuote(-0.00194)), Period(6, Months), euriborIndex))

# swap part
rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(-0.00119)), Period(2, Years),
                    calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
  # in order to use dual-curve bootstrapping, discount curve handle must
  # be given as one argument for swap rate helper (along with dummy handle
  # for quote and dummy zero period for technical reasons)
  QuoteHandle(), Period(0, Days), discountCurve))

rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(0.00019)), Period(3, Years),
                      calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
                      QuoteHandle(), Period(0, Days), discountCurve))

rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(0.00167)), Period(4, Years),
                      calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
                      QuoteHandle(), Period(0, Days), discountCurve))


rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(0.00317)), Period(5, Years),
                      calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
                      QuoteHandle(), Period(0, Days), discountCurve))


rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(0.00598)), Period(7, Years),
                      calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
                      QuoteHandle(), Period(0, Days), discountCurve))


rateHelpers2.append(SwapRateHelper(QuoteHandle(SimpleQuote(0.00966)), Period(10, Years),
                      calendar, Annual, ModifiedFollowing, Actual360(), euriborIndex,
                      QuoteHandle(), Period(0, Days), discountCurve))


# create euribor curve
euriborCurve = PiecewiseFlatForward(0, euriborIndex.fixingCalendar(), rateHelpers2, euriborIndex.dayCounter())
euriborCurve.enableExtrapolation()
# link projection curve to euribor curve
projectionCurve.linkTo(euriborCurve)


# create seasoned vanilla swap
pastSettlementDate=Date(5, 7, 2015)

fixedSchedule=Schedule(pastSettlementDate, pastSettlementDate + Period(5, Years),
                        Period(Annual), calendar, Unadjusted, Unadjusted,
                        DateGeneration.Backward, False)

floatSchedule = Schedule(pastSettlementDate, pastSettlementDate + Period(5, Years),
  Period(Semiannual), calendar, Unadjusted, Unadjusted,
  DateGeneration.Backward, False)

swap=VanillaSwap(VanillaSwap.Payer, 100.0, fixedSchedule, 0.0285,
  dayCounter, floatSchedule, euriborIndex, 0.0, dayCounter)

# add required 6M euribor index fixing for floating leg valuation
euriborIndex.addFixing(Date(1, 6, 2017), -0.0025)
euriborIndex.addFixing(Date(3, 7, 2017), -0.0025)
# create pricing engine, request swap pv
pricer = DiscountingSwapEngine(discountCurve)

swap.setPricingEngine(pricer)

print(swap.NPV())


