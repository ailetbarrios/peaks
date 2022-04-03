    #!/usr/bin/env python3
    # -*- coding: utf-8 -*-
    """
    Created on Tue Mar 29 18:53:24 2022

    @author: simonecoccato
    """

import pandas as pd #for csv reading
    pvReader = pd.read_csv('2021-PV_15min.csv', chunksize=5000)

    smReader = pd.read_csv('2021-SmartMeter_15min.csv', chunksize=5000)

    epReader = pd.read_csv('Day-ahead Prices_202101010000-202201010000.csv', chunksize=5000)

    efReader = pd.read_csv('AssB_Input_Group4_winter.csv', chunksize=5000)

    for i,chunk in smReader:
        # chunk['Day']
        # chunk['Year']
        # chunk['MonthNo'] # datetime for the smartmeter reader
         for y, pv in pvReader:
             if(chunk['Day'] == pv['Day'] && ):
                 print('Bingo'+pv['Day'])
         



