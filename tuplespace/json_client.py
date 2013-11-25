#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2001 actzero, inc. All rights reserved.

import os,time
import sys
import socket
from threading import *
from shared import *

sys.path.append('../')

from lovely.jsonrpc import proxy

space =  proxy.ServerProxy('http://127.0.0.1:8080/jsonrpc/tspace')
# ###############################################################################


def __test(space):    
    print 'application started'    
   
    space.login('junphine','erihrofgh')

    space.execute('a=2*4')
    ret,s,data= space.eval('a+2*4')
    assert data[0]==16,'eval'
    for i in xrange(0,20):
        space.store('teacher',[i, (12+i, 3.14),'Zhang 俊峰',15]) 
        if i%2==0:
            space.store('teacher.school',[i, '西北大学']) 
        else:
            space.store('teacher.school',[i, '东北大学']) 
            
    """
    如何实现inner join？按tuple[0]hash存储,并且tuple是不可变的
    执行函数 inner_join(teacher,teacher.school)，生成新的视图teacher&teacher.school
    teacher&teacher.school的数据为[teacher,teacher.school]
    left_join:  teacher>teacher.school
    right_join: teacher<teacher.school
    """
       

if __name__ == "__main__":  
    import tspace        
    b=time.time()
    for i in xrange(1,1000):
        tspace.test_bench(space)
        e=time.time()
        print 'spend',e-b
        b=e
        
    print 'spend',e-b
    
    #__test(space)
    print 'finish'
    raw_input()


