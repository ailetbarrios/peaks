# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 16:30:06 2021

@author: NCG
"""

import gurobipy as gp
import csv
import pandas as pd  # for csv reading
import numpy as np
import matplotlib.pyplot as plt  # for plotting

"""
Import your input data for the model
"""
summer = pd.read_csv("Summer_output.csv")
winter = pd.read_csv("Winter_output.csv")

"""
Parameters value
"""
######## Time-step
Delta_t = 0.25  # 15 minute (0.25 hour) intervals
T = int(24 * 3 * 1 / Delta_t)  # number of time-slots (in three days)

######## Limits on grid and max, min, and initial SOC
Pgridmax = 3  # [kW]
Pbatmax = 4  # [kW]

SoC_min = 0.2  # [-] (battery min state of charge)
SoC_max = 1  # [-] (battery max state of charge)
SoC0 = 0.5  # [-] (initial battery state of charge at the beginning of the day)

C_bat = 13.5  # battery capacity parameter for a Tesla Powerwall rated at 13,5 [kWh]
eff_dis = 0.94  # battery discharging efficeicny
eff_ch = 0.94  # battery charging efficeicny

"""Question 3 global vairables"""

EMISSION_CONSTRAINTS_SUMMER = np.linspace(12.889924867969496, -1.435135121e+01, num=10)
EMISSION_CONSTRAINTS_WINTER = np.linspace(26.776254443847375, 6.722496217e-01, num=10)

"""Functions"""


def get_minimal_cost(season):
    # load either summer or winter input variables
    Ppv = season['PV generation [kW]']
    Pdem = season['Residential load [kW]']
    Celec = season['Electricity price [euro/kWh]']
    Emis = season['Marginal emission factor [kg CO2eq/kWh]']

    # Create Model
    m = gp.Model()

    # Add Variables
    Pbat_ch = m.addVars(T, lb=0, ub=Pbatmax, vtype=gp.GRB.CONTINUOUS, name="Pbat_ch")
    Pbat_dis = m.addVars(T, lb=0, ub=Pbatmax, vtype=gp.GRB.CONTINUOUS, name="Pbat_dis")

    Pgrid = m.addVars(T, lb=-Pgridmax, ub=Pgridmax, vtype=gp.GRB.CONTINUOUS, name="Pgrid")

    SoC = m.addVars(T, lb=SoC_min, ub=SoC_max, vtype=gp.GRB.CONTINUOUS, name="SoC")

    # Add Constraints  
    ## Power balance formula
    # m.addConstrs(Pgrid[t] + Ppv[t] + Pbat_dis[t] - Pbat_ch[t] == Pdem[t] for t in range(287))
    ## Battery SoC dynamics constraint 
    m.addConstr(
        SoC[0] == SoC0 + ((Pbat_ch[0] * Delta_t * eff_ch) / C_bat) - (Pbat_dis[0] * Delta_t) / (eff_dis * C_bat))
    m.addConstrs(
        SoC[t] == SoC[t - 1] + ((Pbat_ch[t] * Delta_t * eff_ch) / C_bat) - (Pbat_dis[t] * Delta_t) / (eff_dis * C_bat)
        for t in range(1, 287))
    ## SoC constraints 
    m.addConstrs(SoC_min <= SoC[t] for t in range(287))
    m.addConstrs(SoC_max >= SoC[t] for t in range(287))

    ## EMMISSIONS CONSTRAINTS - Q3
    if season["End date/time"][0] == '07/07/2021 00:15':
        emissionlist = EMISSION_CONSTRAINTS_SUMMER
    elif season["End date/time"][0] == '2021-01-21 00:15:00':
        emissionlist = EMISSION_CONSTRAINTS_WINTER
    else:
        raise Exception('whoops')

    df = pd.DataFrame(columns=['Emissions Constraint', 'Cost', 'Emissions'])

    for i in emissionlist:
        m.addConstr((gp.quicksum(Emis[t] * Pgrid[t] * Delta_t for t in range(287))) <= i)

        m.setParam('OutputFlag', 1)  # dont print all the gurobi output stuff
        obj = gp.quicksum(Celec[t] * Pgrid[t] * Delta_t for t in
                          range(287))  # for the end units to be in euro need to multiply by deltaT
        m.setObjective(obj, gp.GRB.MINIMIZE)
        m.optimize()

        # add the values to the new df
        unroundedcost = m.getObjective().getValue()
        cost = round(unroundedcost, 2)
        emissions = gp.quicksum(Emis[t] * Pgrid[t] * Delta_t for t in range(287)).getValue()
        df.loc[len(df)] = [i, cost, emissions]

    return df


summer_out_constraints = get_minimal_cost(summer)
winter_out_constraints = get_minimal_cost(winter)

ParetoDataFrame = pd.DataFrame(columns=['summercost', 'summeremiss', 'wintercost', 'winteremiss'])
ParetoDataFrame.summercost = summer_out_constraints['Cost']
ParetoDataFrame.summeremiss = summer_out_constraints['Emissions']
ParetoDataFrame.wintercost = winter_out_constraints['Cost']
ParetoDataFrame.winteremiss = winter_out_constraints['Emissions']

fig = plt.figure()
plt.plot(ParetoDataFrame.summeremiss, ParetoDataFrame.summercost, marker='o', label='summer')
plt.plot(ParetoDataFrame.winteremiss, ParetoDataFrame.wintercost, marker='o', label='winter')
plt.legend(loc='center right', bbox_to_anchor=(1, 0.9))
plt.grid()
plt.rc('grid', linestyle="-", color='black')
plt.xlabel('Emissions [kg $CO_2$-eq]')
plt.grid(False)
plt.ylabel('Costs [€]')
plt.ylim(-0.75, 1.5, 0.25)

"""Calculations for write up Q3 """

# rEMISSION_CONSTRAINTS_SUMMER = EMISSION_CONSTRAINTS_SUMMER.round(2)
# rEMISSION_CONSTRAINTS_WINTER = EMISSION_CONSTRAINTS_WINTER.round(2)

medsum = np.median(summer_out_constraints.Emissions)
medwin = np.median(winter_out_constraints.Emissions)
print(' summer emissions ' + str(medsum))
print(' winter emissions ' + str(medwin))
