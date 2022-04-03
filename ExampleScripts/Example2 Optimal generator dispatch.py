# -*- coding: utf-8 -*-
"""
Created on Mon Feb 05 15:26:35 2018

@author: Alska001
"""

import gurobipy as gp
import matplotlib.pyplot as plt
import numpy as np

D = 2 #number of days
T = D*24 # number of 15 minute intervals
t=np.linspace(1, T, num=T) # time, in hours
np.random.seed(1)

d = 8 + 4*np.sin(2*np.pi*t/24) + 0.05*t + 1.5*np.random.randn(T) 

N = 4

Pmax=[4, 5, 9, 2]
Pmin=[1, 1, 1, 0]  
alpha= [1, 1.2, 1.5, 1]


m=gp.Model()

p = m.addVars(N,T,name='p')
  
m.addConstrs(p[n,t] <= Pmax[n] for t in range(T) for n in range(N))
m.addConstrs(p[n,t] >= Pmin[n] for t in range(T) for n in range(N))
m.addConstrs(gp.quicksum(p[n,t] for n in range(N)) >= d[t] for t in range(T))


obj = gp.quicksum(alpha[n]*p[n,t] for n in range(N) for t in range(T))

m.setObjective(obj, gp.GRB.MINIMIZE)
m.optimize()

P=m.getAttr("X")

P=np.reshape(P, (N,T))
p_gen = np.asmatrix(P)

print("p_gen:", p_gen)

#plt.figure(1)
#plt.subplot(2,1,1)
#plt.plot(t, d)
#plt.title('demand')
#plt.subplot(2,1,2)
#plt.plot(t, p_gen.T)
#plt.title('generator powers')
#plt.legend(['g1', 'g2', 'g3', 'g4'],bbox_to_anchor=(1.05, 1),loc=2, borderaxespad=0.)

