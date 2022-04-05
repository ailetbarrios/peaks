# -*- coding: utf-8 -*-
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

#for now setting up just for summer as thinking when we make it a function can specify summer or winter

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


def get_minimal_cost(season):
    
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
    
     ## EMMISSIONS CONSTRAINTS - Q3
    #m.addConstr((gp.quicksum(Emis[t]*Pgrid[t]*Delta_t for t in range(T))) <= 13.724252032773677)
    
    # Set objective function and solve
    m.setParam('OutputFlag', 0) #remove all the gurobi output stuff we don't need
    obj = gp.quicksum(Celec[t]*Pgrid[t]*Delta_t for t in range(T)) #for the end units to be in euro need to multiply by deltaT
    m.setObjective(obj, gp.GRB.MINIMIZE)
    m.optimize()
    
    # Add the outcomes to the season dataframe
    season['Pgrid'] = m.getAttr("X", Pgrid).values()
    season['Pbat_ch'] = m.getAttr("X", Pbat_ch).values()
    season['Pbat_dis'] = m.getAttr("X", Pbat_dis).values()
    season['Pbat'] = season['Pbat_ch'] - season['Pbat_dis'] #query, maybe other way around is nicer for explaining?
    season['SoC'] = m.getAttr("X", SoC).values()

    emissions = gp.quicksum(Emis[t]*Pgrid[t]*Delta_t for t in range(T)).getValue() 
    #print the cost and emissions associted with the model run
    print('emissions = ' + str(emissions)) 
    print("cost = " + str(m.getObjective().getValue()))
    
    return season

summer_out_costmin = get_minimal_cost(summer)
winter_out_costmin = get_minimal_cost(winter)
print("Cbat "+ str(C_bat)) #was playing with effects of changing Cbat

#find mac Pbat and Pgrid to investigate constraint activation
max_pbat_row = winter_out_costmin.iloc[winter_out_costmin['Pbat_dis'].idxmax(axis=0)]
print("max bat row" + str(max_pbat_row,))
max_grid =  summer_out_costmin.iloc[summer_out_costmin['Pgrid'].idxmin(axis=0)]
print("max grid row" + str(max_grid))

#%%

"""Creating the plots"""

def get_plots_Pbat_Pgrid_elecprice(season1, season2):

        fig, axs = plt.subplots(nrows =2, ncols=1, sharex=True, sharey=True)
        labels = ['0:00', '12:00', '0:00', '12:00', '0:00', '12:00', '00:00']
        plt.xticks(np.arange(289, step=48), labels)
        plt.ylim(-4,4)
        plt.yticks(np.arange(-4, 5, 1.0))
       
        fig.tight_layout()
        
        plot1 = axs[0].plot(season1.Pbat, label = 'Battery Power', color = 'C0')
        plot2 = axs[0].plot(season1.Pgrid, label = 'Grid Power', color = 'C2')
        axs[0].set(xlabel='', title='Summer')
        axs[0].set_ylabel('Power [kW]')

        ax0t = axs[0].twinx()
        plot3 = ax0t.plot(season1['Electricity price [euro/kWh]'], label = 'Electricity Price', color ='C1')
        ax0t.set_ylabel('Electricity price [€/kWh]')

        
        allplots = plot1 + plot2 + plot3
        labels2 = [plot.get_label() for plot in allplots]
        ax0t.legend(allplots, labels2, bbox_to_anchor=(
            1.12, 1), loc='upper left')
        
        plot4 = axs[1].plot(season2.Pbat, label = 'Battery Power', color = 'C0')
        plot5 = axs[1].plot(season2.Pgrid, label = 'Grid Power', color = 'C2')
        axs[1].set(xlabel='', title='Winter')
        axs[1].set_ylabel('Power [kW]')

        ax1t = axs[1].twinx()
        plot6 = ax1t.plot(season2['Electricity price [euro/kWh]'], label = 'Electricity Price', color ='C1')
        ax1t.set_ylabel('Electricity price [€/kWh]')

        allplots2 = plot4 + plot5 + plot6
        labels3 = [plot.get_label() for plot in allplots2]
        ax1t.legend(allplots2, labels3, bbox_to_anchor=(
            1.12, 1), loc='upper left')
         
        axs[1].set_xlabel('Time [hour]')
        
get_plots_Pbat_Pgrid_elecprice(summer_out_costmin, winter_out_costmin)

#%%

def get_plots_SOC(season1,season2):
    
    fig, axs = plt.subplots(nrows =2, ncols=1, sharex=True, sharey=True,)
    xlabels = ['0:00', '12:00', '0:00', '12:00', '0:00', '12:00', '00:00']
    plt.xticks(np.arange(289, step=48), xlabels)

   
    #fig.tight_layout()
        
    axs[0].plot(season1.SoC, label = 'SoC')
    axs[0].set(ylabel='SoC', xlabel='', title='Summer')
    axs[1].plot(season2.SoC, label = 'SoC')
    axs[1].set(ylabel='SoC', xlabel='Time [hour]', title='Winter')
          
get_plots_SOC(summer_out_costmin, winter_out_costmin)

def get_plots_pv_dem(season1, season2):

        fig, axs = plt.subplots(nrows =2, ncols=1, sharex=True, sharey=True,)
        xlabels = ['0:00', '12:00', '0:00', '12:00', '0:00', '12:00', '00:00']
        plt.xticks(np.arange(289, step=48), xlabels)
       
        fig.tight_layout()
            
        axs[0].plot(season1['PV generation [kW]'], label = 'PV Generation')
        axs[0].plot(season1['Residential load [kW]'], label = 'Household Demand')
 
        axs[0].legend(loc='upper right', bbox_to_anchor=(1.4,1))
        axs[0].set(ylabel='Power [kW]', xlabel='', title='Summer')
        

        axs[1].plot(season2['PV generation [kW]'], label = 'PV Generation')
        axs[1].plot(season2['Residential load [kW]'], label = 'Household Demand')
        
        axs[1].legend(loc='upper right', bbox_to_anchor=(1.4,1))
        axs[1].set(ylabel='Power [kW]', xlabel='Time [hour]', title='Winter')
          
get_plots_pv_dem(summer_out_costmin, winter_out_costmin)