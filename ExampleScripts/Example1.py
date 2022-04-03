# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 11:06:06 2017

@author: alska001
Example1: First model

Problem Description

    You want to decide about three activities (do 
    or don’t) and aim for a maximum value
    • The total time limit is 4 hours
    o Activity 1 takes 1 hour
    o Activity 2 takes 2 hours
    o Activity 3 takes 3 hours
    • You need to choose at least activity 1 or 2 (or both)
    • Activity 3 is worth twice as much as 1 and 2

Step 0: Import functions from the gurobipy module
"""
import gurobipy as gp
"""
Step 1: Create a model
"""
m = gp.Model()
"""
Step 2: Define variables
"""
x1=m.addVar(vtype=gp.GRB.BINARY, name="x1")
x2=m.addVar(vtype=gp.GRB.BINARY, name="x2")
x3=m.addVar(vtype=gp.GRB.BINARY, name="x3")

"""
Step 3: Add constraints
"""
con1=m.addConstr(x1*2 + 1*x2 + 3*x3 <= 4) #time limit constraint
con2=m.addConstr(x1 + x2 >= 1) #must do either x1 or x2 constraint

"""
Step 4: Set objective function
"""
m.setObjective(x1 + x2 + 2*x3, gp.GRB.MAXIMIZE)

"""
Step 5: Solve model
"""
m.optimize()
"""
Step 6: Print variable values for optimal solution
"""
for variable in m.getVars():
    print(variable.varName, variable.x)

#another method for getting the results, in a table
m.printAttr('X')
