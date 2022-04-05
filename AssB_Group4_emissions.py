# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 12:07:19 2021

@author: NCG
"""

"""
% Energy in the Built Environment
% Assignment 2: Optimal Home Energy Management
% Dr. Tarek AlSkaif

"""
import gurobipy as gp
import csv
import pandas as pd #for csv reading
import numpy as np 
import matplotlib.pyplot as plt #for plotting

"""
Import your input data for the model
"""
summer = pd.read_csv("AssB_Input_Group4_summer.csv")
winter = pd.read_csv("AssB_Input_Group4_winter.csv")

"""
Parameters value
"""
######## Time-step
Delta_t = 0.25 # 15 minute (0.25 hour) intervals
T=int(24*3*1/Delta_t) #number of time-slots (in three days)

######## Limits on grid and max, min, and initial SOC
Pgridmax = 3 #[kW]
Pbatmax = 4 #[kW]

SoC_min = 0.2 #[-] (battery min state of charge)
SoC_max = 1 #[-] (battery max state of charge)
SoC0 = 0.5 #[-] (initial battery state of charge at the beginning of the day)

C_bat = 13.5 #battery capacity parameter for a Tesla Powerwall rated at 13,5 [kWh]
eff_dis = 0.94 #battery discharging efficeicny
eff_ch = 0.94 #battery charging efficeicny


"""Question 3 - getting minimum emissions in order to set up Parerto """

def get_minimal_emissions(season):
    
    #load either summer or winter input variables
    Ppv = season['PV generation [kW]']
    Pdem = season['Residential load [kW]']
    Celec = season['Electricity price [euro/kWh]']
    Emis = season['Marginal emission factor [kg CO2eq/kWh]']
    
    # Create Model
    m=gp.Model()
    
    # Add Variables
    Pbat_ch = m.addVars(T, lb= 0, ub= Pbatmax, vtype= gp.GRB.CONTINUOUS, name= "Pbat_ch")
    Pbat_dis = m.addVars(T, lb= 0, ub= Pbatmax, vtype= gp.GRB.CONTINUOUS, name= "Pbat_dis")
    
    Pgrid = m.addVars(T, lb= -Pgridmax, ub= Pgridmax, vtype= gp.GRB.CONTINUOUS, name= "Pgrid")
    
    SoC = m.addVars(T, lb= SoC_min, ub= SoC_max, vtype= gp.GRB.CONTINUOUS, name= "SoC")
        
    # Add Constraints  
    ## Power balance formula
    m.addConstrs(Pgrid[t] + Ppv[t] + Pbat_dis[t] - Pbat_ch[t] == Pdem[t] for t in range(T))      
    ## Battery SoC dynamics constraint 
    m.addConstr(SoC[0] == SoC0 + ((Pbat_ch[0]*Delta_t*eff_ch)/C_bat) - (Pbat_dis[0]*Delta_t)/(eff_dis*C_bat))
    m.addConstrs(SoC[t] == SoC[t-1] + ((Pbat_ch[t]*Delta_t*eff_ch)/C_bat) - (Pbat_dis[t]*Delta_t)/(eff_dis*C_bat) for t in range(1,T))
    ## SoC constraints 
    m.addConstrs(SoC_min <= SoC[t] for t in range(T))
    m.addConstrs(SoC_max >= SoC[t] for t in range(T))
    
    # Set objective function and solve
    obj = gp.quicksum(Emis[t]*Pgrid[t]*Delta_t for t in range(T)) #for the end units to be in euro need to multiply ??? by deltaT
    m.setObjective(obj, gp.GRB.MINIMIZE)
    m.optimize()
    
    # Add the outcomes to the season dataframe
    season['Pgrid'] = m.getAttr("X", Pgrid).values()
    season['Pbat_ch'] = m.getAttr("X", Pbat_ch).values()
    season['Pbat_dis'] = m.getAttr("X", Pbat_dis).values()
    season['Pbat'] = season['Pbat_ch'] - season['Pbat_dis'] #query, maybe other way around is nicer for explaining?
    season['SoC'] = m.getAttr("X", SoC).values()
    
    cost = gp.quicksum(Celec[t]*Pgrid[t]*Delta_t for t in range(T)).getValue()
    print('cost = ' + str(cost))
    
    return season

summer_out_emismin = get_minimal_emissions(summer)
winter_out_emismin = get_minimal_emissions(winter)

def get_plots_emissions(season1, season2):

        fig, axs = plt.subplots(2)
        fig.tight_layout()
        
        axs[0].plot(season1['PV generation [kW]'], label = 'Ppv')
        axs[0].plot(season1.Pgrid, label = 'Pgrid')
        axs[0].plot(season1.Pbat, label = 'Pbat')
        axs[0].plot(season1.SoC, label = 'SoC')
        axs[0].plot(season1['Residential load [kW]'], label = 'Pdem')
        axs[0].legend(loc='upper right', bbox_to_anchor=(1.2,1))
        axs[0].set(ylabel='Power (kW)', title='Summer')
        
        axs[1].plot(season2['PV generation [kW]'], label = 'Ppv')
        axs[1].plot(season2.Pgrid, label = 'Pgrid')
        axs[1].plot(season2.Pbat, label = 'Pbat')
        axs[1].plot(season2.SoC, label = 'SoC')
        axs[1].plot(season2['Residential load [kW]'], label = 'Pdem')
        axs[1].legend(loc='upper right', bbox_to_anchor=(1.2,1))
        axs[1].set(ylabel='Power (kW)',xlabel='Time (hours/4)', title='Winter')
         
#get_plots_emissions(summer_out_emismin, winter_out_emismin)

