
import time
from multiprocessing import Pool

def f(x):
    return x*x

def f2(x,l=1):    
    time.sleep(0.2)
    return x*x

def succ(x):
    print 'x=',x
    print 'good!'

if __name__ == '__main__':
    pool = Pool(processes=2)              # start 4 worker processes

 
    print pool.map(f2, range(10))          # prints "[0, 1, 4,..., 81]"
    
    if 1:
        result = pool.map_async(f2, range(10),1,succ)    # evaluate "f(10)" asynchronously
        r= result.get(timeout=1)       
        print r

    it = pool.imap(f, range(10))
    print it.next()                       # prints "0"
    print it.next()                       # prints "1"
    print it.next(timeout=1)              # prints "4" unless your computer is *very* slow

    import time
    #result = pool.applyAsync(time.sleep, (10,))
    #print result.get(timeout=1)           # raises TimeoutError

