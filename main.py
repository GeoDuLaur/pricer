'''
Created on 9 oct. 2018

@author: Vincent Sudre
'''

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import utils
import datetime as dt

from parametres import *
from instrument import *
from QuantLib import *
from callibriUtils import *
from graphe import *


Settings.instance().evaluationDate =  pydate_to_qldate(dt.date.today())

'''
#essai quantlib
dateQL = ql.Date(31,3,2018)
usCalendar = ql.UnitedStates()
targetCalendar = ql.TARGET()

print("%d-%d-%d" %(dateQL.month(),dateQL.dayOfMonth(),dateQL.year()))

dateQL2 = targetCalendar.advance(dateQL, ql.Period(2,ql.Years))
print("%d-%d-%d" %(dateQL2.month(),dateQL2.dayOfMonth(),dateQL2.year()))

us_busdays = usCalendar.businessDaysBetween(dateQL,dateQL2)
print("Business days US: {0}".format(us_busdays))

#schedule
effective_date = ql.Date(7, 1, 2019)
termination_date = targetCalendar.advance(effective_date, ql.Period(2,ql.Years))
tenor = ql.Period(ql.Monthly)
#calendar = UnitedStates()
business_convention = ql.Following
termination_business_convention = ql.Following
date_generation = ql.DateGeneration.Forward
end_of_month = False
cal = ql.Schedule(effective_date, termination_date, tenor, targetCalendar, business_convention, termination_business_convention, date_generation, end_of_month)
print(pd.DataFrame({'date': list(cal)}))


#taux interet
annual_rate = 0.05
day_count = ql.ActualActual()
compound_type = ql.Compounded
frequency = ql.Annual
interest_rate = ql.InterestRate(annual_rate, day_count, compound_type, frequency)
print(interest_rate)
t = 2.0
print(interest_rate.compoundFactor(t))
print((1+annual_rate)*(1.0+annual_rate))
print(interest_rate.discountFactor(t))
print(1.0/interest_rate.compoundFactor(t))
new_frequency = ql.Semiannual
new_interest_rate = interest_rate.equivalentRate(compound_type, new_frequency, t)
print(new_interest_rate)
print(interest_rate.discountFactor(t))
print(new_interest_rate.discountFactor(t))


#instrument
#Settings.instance().evaluationDate = ql.todaysDate ()
aujourdhui = ql.Date.todaysDate()
print(ql.Date.todaysDate())

#construction du payoff
echeance = targetCalendar.advance(aujourdhui, ql.Period(6,ql.Months))
option = ql.EuropeanOption(ql.PlainVanillaPayoff(ql.Option.Call, 100.0),ql.EuropeanExercise(echeance))
print(option)

#donees marche
u = ql.SimpleQuote(100.0)
r = ql.SimpleQuote(0.01)
sigma = ql.SimpleQuote(0.20)

#process
riskFreeCurve = ql.FlatForward(0, targetCalendar, ql.QuoteHandle(r), ql.Actual360())
volatility = ql.BlackConstantVol(0, targetCalendar, ql.QuoteHandle(sigma), ql.Actual360())
process = ql.BlackScholesProcess(ql.QuoteHandle(u), ql.YieldTermStructureHandle(riskFreeCurve),ql.BlackVolTermStructureHandle(volatility))

#moteur
engine = ql.AnalyticEuropeanEngine(process)
option.setPricingEngine(engine)

print(option.NPV())
print(option.delta())
print(option.gamma())
print(option.vega())

u.setValue(105)
print(option.NPV())



#affichage
f, ax = plt.subplots(1,1)
ax2 = ax.twinx()
xs = np.linspace(60.0, 140.0, 400)
prix = []
delta =[]
for x in xs:
    u.setValue(x)
    prix.append(option.NPV())
    delta.append(option.vega())
ax.set_title('Option value')
ax.plot(xs, prix);
ax2.plot(xs, delta,'--');
plt.xlabel('Spot')
plt.ylabel('Prix call')
plt.title("Valeur option")
#plt.savefig('tatayoyo.png')
#plt.show()

#heston
model = ql.HestonModel(ql.HestonProcess(ql.YieldTermStructureHandle(riskFreeCurve),
                        ql.YieldTermStructureHandle(ql.FlatForward(0, targetCalendar,0.0, ql.Actual360())),
                        ql.QuoteHandle(u),
                        0.04, 0.1, 0.01, 0.05, -0.75))
engine = ql.AnalyticHestonEngine(model)
option.setPricingEngine(engine)
print("HESTON : " + str(option.NPV()))

#monte carlo
engine = ql.MCEuropeanEngine(process, "PseudoRandom", timeSteps=20, requiredSamples=250000)
option.setPricingEngine(engine)
print("MONTE CARLO : " + str(option.NPV()))
print("MONTE CARLO : " + str(option.NPV()))
u.setValue(105)
print("MONTE CARLO : " + str(option.NPV()))


class Option :
    name = "toto"

    def __init__(self) :
        print (self.name)

    def changeNom(self,nouveauNom):
        self.name=nouveauNom


class Autocall(Option):
    pdiBarrier=0
    def setPDI(self) :
        pdiBarrier= 0.7

'''

#courbe 3M
courbeDeTaux=CCourbeTaux('EONIA', '3M')
courbeDeTaux.loadCurve()

#swap 10y avec fundings spreads
swap = CSwap(courbeDeTaux.getCourbeTaux())
swap.calcSwap(10, Period(2,Weeks), 'SPREADS_EUR')

#ZC 8y par exemple
zc = CZC(courbeDeTaux.getDiscountCurve())
print(zc.getZC(8))

#chargement des divs
div = CDividende('SX5E')
div.loadDivs()
div.applyDiscount(zc)
print(div.getSumDiscountAmount(Date(31, 3, 2025)))
print(div.getDivPropAtDate(Date(26, 5, 2025)))
print(div.getDivPropAtDate(dt.datetime(2025,5,26)))


#lecture fichier vol et interpolation
vol=CVolatilite('SX5E')
vol.loadVolFromFile1('SX5E.txt')
#vol.loadVolFromFile2('SX5E1.txt', 3123.21)
print("PIVOT VOL : " + str(vol.getPivolVol()))
print("Vol(3000,'26/02/2023) : " + str(vol.getVol(3000,'08/02/2020')))
surfaceBlack = vol.getBlackVarianceSurface()
surfaceBlack.setInterpolation("bicubic")
surfaceBlack.enableExtrapolation()
strike = 2500
expiry = 0.1 # years
print(surfaceBlack.blackVol(Date(2,1,2020), strike))

afficheSurfaceVol(surfaceBlack)


#surfaceBlack.setInterpolation("bicubic")
flat_ts = YieldTermStructureHandle(
    FlatForward(Settings.instance().evaluationDate, 0.01, Actual365Fixed()))
dividend_ts = YieldTermStructureHandle(
    FlatForward(Settings.instance().evaluationDate, 0, Actual365Fixed()))

local_vol_surface = LocalVolSurface(
    BlackVolTermStructureHandle(surfaceBlack),
    courbeDeTaux.getProjectionCurveHandle(),
    div.getTSDividend(),
    3000)
'''
local_vol_surface = LocalVolSurface(
    BlackVolTermStructureHandle(surfaceBlack),
    flat_ts,
    dividend_ts,
    3000)
'''

plot_years = np.arange(2, 5, 1)
plot_strikes = np.arange(3000, 3300, 10)
fig = plt.figure()
ax = fig.gca(projection='3d')
X, Y = np.meshgrid(plot_strikes, plot_years)
Z = np.array([local_vol_surface.localVol(float(y), float(x))
              for xr, yr in zip(X, Y)
                  for x, y in zip(xr,yr) ]
             ).reshape(len(X), len(X[0]))

surf = ax.plot_surface(Y,X, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                linewidth=0.1)
fig.colorbar(surf, shrink=0.5, aspect=5)



#chargement des repos
repos = CRepos('SX5E')
repos.loadRepos()
print("Repo : " + str(repos.getRepoAtDate(dt.datetime(2025,5,26))))
'''
# create and print array of discount factors for every 3M up to 15Y
times = np.linspace(0.0, 15.0, 16)
c = courbeDeTaux.getDiscountCurve()
dfs = np.array([c.discount(t) for t in times])
for t in times :
    print(str(t) + "    :   " + str(c.discount(t)))'''


#dessindiv_amount
'''today = courbe3M.mCurve.referenceDate()
end = today + Period(15,Years)
dates = [ Date(serial) for serial in range(today.serialNumber(), end.serialNumber()+1) ]

rates_c = [ courbe3M.mCurve.forwardRate(d, TARGET().advance(d,1,Days), Actual360(), Simple).rate()
            for d in dates
            ]

f, ax = matplotlib.pyplot.subplots(1,1)

def ql_to_datetime(d):
    z=[]
    for x in d :
        z.append(datetime.datetime(x.year(), x.month(), x.dayOfMonth()))
    return z

toto =  ql_to_datetime(dates)

ax.plot(toto, rates_c);
matplotlib.pyplot.show()'''








#print(courbe3M.dfTaux)


#df=pd.read_table("data/SX5E.txt", sep = '\t',header = 0)

#afficher les premieres lignes du jeu de donnees
#print(df.head())
#énumération des colonnes
#print(df.columns)
#informations sur les donnees
#print(df.info())

#description des donnees
#print("***************************")
#print(df.describe(include='all'))

#print("***************************")
#print(df[['1y','5y']])
#print(df.iloc[0]['2m'])
#print(df.iloc[1]['2m'])

#print (df.columns[2])
#df.columns = ['Name1', 'Name2', 'Name3'...]


#vol=CVolatilite('SX5E')
#print(vol.getPivolVol())
#print(vol.getAllStrikes())