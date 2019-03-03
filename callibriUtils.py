import datetime as dt
import numpy as np
from   numpy import nan
import pandas as pd
import QuantLib as ql
import locale
import re
import six


UNITS = {"s":"seconds", "n":"minutes", "h":"hours", "d":"days", "w":"weeks","m":"months","y":"years"}


def convertStringToDate(d):
    return dt.datetime.strptime(d, '%d/%m/%Y')
def convertDateToString(d):
    return dt.datetime.strftime(d, '%d/%m/%Y')

#convertion dates flottantes en intervalles de temps et addition a la date du jour
def convertFloatDateToFixedDate(s):
    count = int(s[:-1])
    unit = UNITS[ s[-1] ]

    if unit=='years' :
        count=count*365.25
        unit='days'
    elif unit=='months' :
        count=count*365.25/12
        unit='days'
    td = dt.timedelta(**{unit: count})
    secondes=td.seconds + 60 * 60 * 24 * td.days
    return  convertStringToDate(convertDateToString(dt.datetime.now()+ dt.timedelta(seconds=secondes)))

#convertion dates flottantes en periode
def convertFloatDateToPeriod(s):
    count = int(s[:-1])
    unit = UNITS[ s[-1] ]

    if unit=='days' :
        resp=ql.Days
    elif unit=='months' :
        resp=ql.Months
    elif unit=='years' :
        resp=ql.Years
    elif unit=='weeks' :
        resp=ql.Weeks
    return  ql.Period(count,resp)


date_re_list = [ \
    # Styles: (1)
    (re.compile("([0-9]+)-([A-Za-z]+)-([0-9]{2,4})"),
     (3, 2, 1)),
    # Styles: (2)
    (re.compile("([0-9]{4,4})([0-9]{2,2})([0-9]{2,2})"),
     (1, 2, 3)),
    # Styles: (3)
    #(re.compile("([0-9]+)/([0-9]+)/([0-9]{2,4})"),
    # (2, 1, 3)),
    # Styles: (4)
    (re.compile("([0-9](1,2))([A-Za-z](3,3))([0-9](2,4))"),
     (3, 2, 1)),
    # Styles: (5)
    (re.compile("([0-9]{2,4})-([0-9]+)-([0-9]+)"),
    (1, 2, 3)),
    # Styles: (6)
    (re.compile("([0-9]+)/([0-9]+)/([0-9]{2,4})"),
    (3, 2, 1))

]






def _partition_date(date):
    """
    Partition a date string into three sub-strings
    year, month, day
    The following styles are understood:
    (1) 22-AUG-1993 or
        22-Aug-03 (2000+yy if yy<50)
    (2) 20010131
    (3) mm/dd/yy or
        mm/dd/yyyy
    (4) 10Aug2004 or
        10Aug04
    (5) yyyy-mm-dd
    (6) dd/m/yyyy
    """

    date = str.lstrip(str.rstrip(date))
    for reg, idx in date_re_list:
        mo = reg.match(date)
        if mo != None:
            return (mo.group(idx[0]), mo.group(idx[1]),
                    mo.group(idx[2]))

    #raise Exception("couldn't partition date: %s" % date)
    la_date = convertFloatDateToFixedDate(date)
    return (str(la_date.year), str(la_date.month), str(la_date.day))

def _parsedate(date):
    """
    Parse a date string and return the tuple
    (year, month, day)
    """
    (yy, mo, dd) = _partition_date(date)
    if len(yy) == 2:
        yy = locale.atoi(yy)
        yy += 2000 if yy < 60 else 1900
    else:
        yy = locale.atoi(yy)

    try:
        mm = locale.atoi(mo)
    except:
        mo = str.lower(mo)
        if not mo in _shortMonthName:
            raise Exception("Bad month name: " + mo)
        else:
            mm = _shortMonthName.index(mo) + 1

    dd = locale.atoi(dd)
    return (yy, mm, dd)

def pydate(date):
    """
    Accomodate date inputs as string or python date
    """

    if isinstance(date, dt.datetime):
        return date
    else:
        yy, mm, dd = _parsedate(date)
    return dt.datetime(yy, mm, dd)

def pydate_to_qldate(date):
    """
    Converts a datetime object or a date string
    into a QL Date.
    """

    if isinstance(date, ql.Date):
        return date

    return ql.Date(date.day, date.month, date.year)

def qldate_to_pydate(date):
    """
    Converts a QL Date to a datetime
    """

    return dt.datetime(date.year(), date.month(), date.dayOfMonth())




#interpolation dataframe
def getExtrapolatedInterpolatedValue(dataGrid, x, y):
    if x not in dataGrid.index:
        dataGrid.loc[x] = nan
        dataGrid = dataGrid.sort_index()
        dataGrid = dataGrid.interpolate(method='index', axis=0).ffill(axis=0).bfill(axis=0)


    if y not in dataGrid.columns.values:
        dt_temp = dataGrid.T
        #dataGrid = dataGrid.reindex(columns=np.append(dataGrid.columns.values, y))
        dt_temp.loc[y] = nan
        dt_temp = dt_temp.sort_index()
        dataGrid=dt_temp.T
        #dateGrid = dateGrid.sort_index(axis=1)
        dataGrid = dataGrid.interpolate(method='index', axis=1).ffill(axis=1).bfill(axis=1)

    return dataGrid.loc[x][y]

#interpolation dataframe 1D
def getExtrapolatedInterpolatedValue1D(dataGrid, x):
    if type(x).__name__ == 'Date' :
        x = qldate_to_pydate(x)


    if x not in dataGrid.index:
        dataGrid.loc[x] = nan
        dataGrid = dataGrid.sort_index()
        dataGrid = dataGrid.interpolate(method='index', axis=0).ffill(axis=0)


    return dataGrid.loc[x][0]

#retourne l'indice de taux
def getRateIndex(curveName='') :
    if curveName =='EONIA' :
        return ql.Eonia()
    elif curveName == '3M' :
        return ql.Euribor3M()
    else:
        pass
    return ql.Euribor6M()


