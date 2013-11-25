#!/usr/bin/env python
# -*- coding: utf-8 -*-

data = ["Humpty Dumpty sat on a wall",
        "Humpty Dumpty had a great fall",
        "All the King's horses and all the King's men",
        "Couldn't put Humpty together again",
        ]
# The data source can be any dictionary-like object
datasource = dict(enumerate(data))

class Example:
    def __init__(self,init_value=None):
        pass
        #print 'start map reduce.',init_value
        
    #yeild tupid,v1,v2,...
    def map(self,i,x):
        tup=list(x)
        tup[3]+=100   
        k=tup[1][0]+10000
        y=tup[3]
        yield (str(k),y,4)
    
    # combine before reduce
    def combine(self,k,ys):
        return ys

    def reduce(self,k,ys):
        sumv=0
        for y in ys:
            sumv+=y[1];
        yield k,sumv,2,4
    

def mapfn(k, v):
    for w in v.split():
        yield w, 1

def reducefn(k, vs):
    result = sum(vs)
    return result

