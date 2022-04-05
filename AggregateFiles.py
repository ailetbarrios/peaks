import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta
from time import process_time

from pandas import DataFrame

from Peak import Peak

DATE_TIME_FORMAT = "%d/%m/%Y %H:%M"
DATE_TIME_FORMAT_SUMMER = "%Y-%m-%d %H:%M:%S"
SEASON = "summer"  # cambiame tambien simone [winter or summer]
CHUNKSIZE = 5000

filepath = Path('csv/out.csv')
filepath.parent.mkdir(parents=True, exist_ok=True)
global pv_index, ep_index

# Readers

# DataFrames

smReader = pd.read_csv('csv/2021-SmartMeter_15min.csv', chunksize=CHUNKSIZE)
fullSmReader = pd.concat(smReader, ignore_index=True)

pvReader = pd.read_csv('csv/2021-PV_15min.csv', chunksize=CHUNKSIZE)
fullPvData = pd.concat(pvReader, ignore_index=True)

colNames = ['date', 'price', 'currency', 'bzn']
epReader = pd.read_csv('csv/Day-ahead Prices_202101010000-202201010000.csv', names=colNames, chunksize=10,
                       header=None, skiprows=1)
fullEpReader = pd.concat(epReader, ignore_index=True)

fullEmissionReader = pd.concat(
    (pd.read_csv(f, names=["startdate", "enddate", "load", "pv", "price", "emission"], header=None, skiprows=1) for f in
     ['csv/AssB_Input_Group4_winter.csv', 'csv/AssB_Input_Group4_summer.csv']), ignore_index=True)

KEEP_MONTHS = [7]  #Simone cambia aca los meses

def to_kw(sumPower):
    return round(sumPower * 0.001, 2)


def to_price_kw(price):
    return round(price * 0.001, 2)


def make_file():
    global nextVal
    counter: int = 4

    # smart meter
    pvIterator = fullPvData.iterrows()
    epIterator = fullEpReader.iterrows()
    counter = 4
    ep = None
    df: DataFrame = DataFrame()
    for index, sm in fullSmReader.iterrows():
        peak: Peak = Peak()
        day: int = sm['Day']
        year: int = sm['Year']
        month: int = sm['MonthNo']
        hour: int = sm['Hour']
        minute: int = sm['Minute']
        sumPower: float = sm["SumPower"]
        # Residential load
        kwValue: float = to_kw(sumPower)
        peak.load = kwValue 
        # 01.01.2021 00:00
        smDateTime = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        if(smDateTime.month not in KEEP_MONTHS):
            continue
        # example format: 2018-01-21 00:00:00
        if SEASON.lower() != 'summer':
            peak.from_date = smDateTime.strftime(DATE_TIME_FORMAT_SUMMER)
            to_date = smDateTime + timedelta(minutes=15)
            peak.to_date = to_date.strftime(DATE_TIME_FORMAT_SUMMER)
        else:
            peak.to_date = smDateTime.strftime(DATE_TIME_FORMAT)

    

        # pv reader
        found: bool = False
        while not found:
            next_pv = next(pvIterator, [])
            if not next_pv:
                found = True
                continue
            pv = next_pv[1]
            pvDay: int = pv.Day
            pvYear: int = pv.Year
            pvMonth: int = pv.MonthNo
            pvHour: int = pv.Hour
            pvMinute: int = pv.Minute
            pvSumPower: float = pv.SumPower
            pvDateTime = datetime(pvYear, pvMonth, pvDay, pvHour, pvMinute, tzinfo=timezone.utc)
            if pvDateTime == smDateTime:
                peak.pv = to_kw(pvSumPower)
                # peak.load = peak.pv + peak.load
            ##comment me simone  
            peak.load = peak.pv + peak.load
            if peak.load < 0:
             #negative
             peak.load = 0
            found = True
        ep_found: bool = False

        # skip head
        while not ep_found:
            if ep is None:
                nextVal = next(epIterator, [])
                if not nextVal:
                    ep_found = True
                    ep = None
                    counter = 4
                    continue
                ep = nextVal[1]

            date: str = ep.date
            # format: 01.01.2021 00:00 - 01.01.2021 01:00
            fromDateTime = date.split(' - ')[0]
            # format: 01.01.2021 00:00
            currentDateTime: datetime = datetime.strptime(fromDateTime, "%d.%m.%Y %H:%M")
            price: float = ep.price
            startOfHourDateTime: datetime = datetime(smDateTime.year, smDateTime.month, smDateTime.day, smDateTime.hour,
                                                     00)
            if startOfHourDateTime == currentDateTime:
                counter = counter - 1
                peak.price = to_kw(price)
                ep_found = True
                if counter == 0:
                    ep = None
                    counter = 4
            else:
                ep = None
                counter = 4
        # emissions
        for index, em in fullEmissionReader.iterrows():
            startDate = datetime.strptime(em['startdate'], "%Y-%m-%d %H:%M:%S")
            emDateTime = datetime(startDate.year, startDate.month, startDate.day, startDate.hour, startDate.minute,
                                  tzinfo=timezone.utc)
            if smDateTime == emDateTime:
                peak.emission = em['emission']
        row = ({
            "Start date/time": peak.from_date,
            "End date/time": peak.to_date,
            "Residential load [kW]": peak.load,
            "PV generation [kW]": peak.pv,
            "Electricity price [euro/kWh]": peak.price,
            "Marginal emission factor [kg CO2eq/kWh]": peak.emission,
        })

        df = df.append(DataFrame(data=row,  index=[0]))
        # else:
        #     df = DataFrame(data=row, columns=OUTPUT_COLS, index=[0])

        print(str(peak))
    df.to_csv("csv/output.csv", index=None)


start = process_time()
make_file()
end = process_time()
print("Elapsed time:", end, start)
print("Elapsed time during the whole program in seconds:", end - start)
