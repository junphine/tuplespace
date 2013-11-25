#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)

sys.path.append('../lib')
sys.path.append('lib')

ENCODING='utf-8'
sys.setdefaultencoding(ENCODING)

CPYTHON=1
JYTHON=2
PYTHON_NET=3
#set which python
_PYTHON_=CPYTHON
if type(u'')==type(''):
    _PYTHON_=PYTHON_NET

#set 1 if use AOP
_ASPECT_=1

#set debug level 
_DEBUG_=0;
#_DEBUG_=4;
_DEBUG_=8



def printf(text,encoding=ENCODING):    
    if _PYTHON_==CPYTHON:
        if type(text)==type(u''):
            text=text.encode('cp936','ignore')
        elif type(text)==type(''):
            text=unicode(text,encoding).encode('cp936','ignore')
        
    if _PYTHON_==PYTHON_NET:
        pass
    print(text)

def trace(v1, v2='',v3='',v4='',level=3):
    global _DEBUG_
    if _DEBUG_>=level:
        print '<!--Trace: ', v1, ' ', v2,' ', v3,' ',v4, "\n-->"
trace('DEBUG.level=' ,_DEBUG_)    
       
#end

if _PYTHON_==JYTHON:      
    True=1
    False=0
    true=1
    false=0
elif _PYTHON_==CPYTHON:
    true=True
    false=False
else:
    true=True
    false=False

null=None 

MIN_BUFFER_SIZE=1024*4
MAX_BUFFER_SIZE=1024*1024*64
BUFFER_SIZE=1024*8

               
#变量，预定义 $开头代替元组字段变量，后面跟整数，%开头表示后面是正则表达式
out=('%?*')
any=('%*')
out=('$')
ANY=('$')

def between(start,end):
    return ('\%[%s,%s]')%(str(start),str(end))

def contain(s):
    return ('\%*%s*')%(s)



def num_between(s,pat,i=0,j=0):
    pat=pat.replace(' ','') 
    tuple=eval(pat[j:])
    if(tuple[0]==None and tuple[1]!=None):
        if(s<=tuple[1]): return true
        return false
    if(tuple[0]!=None and tuple[1]==None):
        if(s>=tuple[0]): return true
        return false
    if(s>=tuple[0] and s<=tuple[1]):
        return true
    return false
#or re.match(pat, str)
#A string matching function using Tcl's matching rules.
# abdd ~ ab?d*
def str_match(s,pat,i=0,j=0):    
    str_len=len(s)
    pat_len=len(pat)  
    while (true): 
        if (j==pat_len):       
            if (i==str_len):return true;
            else:           return false;
        
        if (i==str_len and pat[j] != '*'): return false;
        
        if (pat[j]=='*'):
            j+=1
            if (pat_len==j): return true;
            while (true):            
                if str_match(s, pat,i,j): return true;
                if (i==str_len): return false;
                i+=1;

        if (pat[j]=='?'):
            i+=1
            j+=1
            continue    
        if (pat[j]=='\\'):   
            j+=1;
            if (pat_len==j): return false;
        if (pat[j]!=s[i]): return false;

        i+=1
        j+=1
    
#end strmatch
                   

import cPickle as pickle
import json

"""当为服务响应消息时，cmd是结果状态{True，False}，table是server_key
"""
def mySend(sock,cmd,table,data,param=None):      
    if data==None:        
        return sock.sendall(str(cmd)+':'+str(table)+':')
        
    buff=pickle.dumps([data,param],1)
    #buff=json.dumps(data,ensure_ascii=True,encoding=ENCODING)
    header=str(cmd)+':'+str(table)+(':%d:'%len(buff))
    #trace('<SEND>',header,data)
    #sock.sendall(header) 
    return sock.sendall(header+buff)  
    

"""当为服务响应消息时，返回（结果状态{True，False}，server_key，result or errmsg）
"""  
def myRecv(sock,size=MIN_BUFFER_SIZE):   
    #trace('<Recv>','begin recv data',size)    
    rdata=sock.recv(8192)    
    if(rdata==None):  return None   
    #trace('<Recv>',rdata[:20])   
    pos=rdata.find(':')
    cmd=rdata[0:pos]
    if(cmd=='True'): cmd=True
    elif(cmd=='False'): cmd=False
    pos2=rdata.find(':',pos+1)    
    table=rdata[pos+1:pos2]
    pos3=rdata.find(':',pos2+1)
    if pos3>0:        
        buffsiz=rdata[pos2+1:pos3]
        buffsiz=int(buffsiz)
        #assert buffsiz<BUFFER_SIZE,'BUFFER_SIZE too small.'
        body=rdata[pos3+1:]
        recved=len(body)
        while buffsiz>recved:            
            #trace('<Notice>','retry data recv')            
            rev=sock.recv(buffsiz-recved)   
            body+=rev
            recved=len(body)   
        try:     
            data,param=pickle.loads(body)
        except Exception,e:
            print e
            trace('<Recv>',rdata[:20])  
            print 'buffsiz=',buffsiz
            print 'len data=',len(body)                   
            raise e
        #data=json.loads(rdata,encoding=ENCODING)       
        #cmd,table,data,param 
        if(param!=None):
            return (cmd,table,data,param)
        else:
            return (cmd,table,data)
        
    else:
        data=None   
        return (cmd,table)
    

    
    



