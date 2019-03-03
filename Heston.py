from QuantLib import *
from callibriUtils import *
'''
from QuantLib.processes.heston_process import *
from QuantLib.quotes import SimpleQuote
from QuantLib.settings import Settings
from QuantLib.termstructures.yields.flat_forward import FlatForward
from QuantLib.time.api import today, TARGET, ActualActual, Date, Period, Years
from QuantLib.models.equity.heston_model import (HestonModel,
                                                 HestonModelHelper)
from QuantLib.pricingengines.api import (AnalyticHestonEngine)
from QuantLib.pricingengines.vanilla.mceuropeanhestonengine import MCEuropeanHestonEngine
from QuantLib.instruments.api import (PlainVanillaPayoff,
                                      EuropeanExercise,
                                      VanillaOption,
                                      EuropeanOption)
from QuantLib.sim.simulate import simulate_process
from QuantLib.time_grid import TimeGrid
'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline
#import seaborn as sns
#sns.set(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})




settings = Settings.instance()
settlement_date = pydate_to_qldate(dt.date.today())
settings.evaluation_date = settlement_date

day_counter = ActualActual()
interest_rate = 0.7
dividend_yield = 0.4

def flat_rate(forward, daycounter):
    return FlatForward(
        forward,
        0,
        TARGET(),
        daycounter
    )


risk_free_ts = flat_rate(interest_rate, day_counter)
dividend_ts = flat_rate(dividend_yield, day_counter)

maturity = Period(10, Years)
exercise_date = settlement_date + maturity


# spot
s0 = SimpleQuote(100.0)

# Available descritizations
#PARTIALTRUNCATION
#FULLTRUNCATION
#REFLECTION
#NONCENTRALCHISQUAREVARIANCE
#QUADRATICEXPONENTIAL
#QUADRATICEXPONENTIALMARTINGALE
#BROADIEKAYAEXACTSCHEMELOBATTO
#BROADIEKAYAEXACTSCHEMELAGUERRE
#BROADIEKAYAEXACTSCHEMETRAPEZOIDAL

# Heston Model params
v0 = 0.05
kappa = 5.0
theta = 0.05
sigma = 1.0e-4
rho = -0.5

def gen_process(desc):
    process = HestonProcess(risk_free_ts,
                            dividend_ts,
                            s0,
                            v0,
                            kappa,
                            theta,
                            sigma,
                            rho,
                            desc)
    return process

processes = {"REFLECTION" : gen_process(REFLECTION),
             "PARTIALTRUNCATION" : gen_process(PARTIALTRUNCATION),
             "QUADRATICEXPONENTIAL" : gen_process(QUADRATICEXPONENTIAL),
             "QUADRATICEXPONENTIALMARTINGALE" : gen_process(QUADRATICEXPONENTIALMARTINGALE),
}

# simulate and plot Heston paths
paths = 200
steps = 100
horizon = 2
seed = 154

grid = TimeGrid(horizon, steps)

fig, axs = plt.subplots(figsize=(14, 12), nrows=2, ncols=2)
flat_axs = axs.reshape(-1)

for i, key in enumerate(processes.keys()):
    flat_axs[i].plot(list(grid), simulate_process(processes[key], paths, grid, seed))
    flat_axs[i].set_xlabel('Time')
    flat_axs[i].set_ylabel('Stock Price')
    flat_axs[i].set_title('%s' % key)