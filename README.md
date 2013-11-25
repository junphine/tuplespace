tuplespace
==========

Distributed Computing Systems，The Lightweight map reduce system 


map-reduce job example:


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
