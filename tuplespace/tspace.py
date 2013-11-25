#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2001 actzero, inc. All rights reserved.

import os
import socket
from threading import *
import traceback
import marshal

from shared import *

import _config as config

class TSpaceError(Exception):
    "This exception indicates a runtime error in 'TSpace' module"
    pass


class TSpaceProxy:
    __doc__ = """
    访问TupleBase的代理,ServerConfig配置集群列表,后面机器是对等的
    为了提高前端性能，可以启用多个FrontServer。
    """    
    def __init__(self, ServerConfig):         
        self.config = {}
        for k,v in  ServerConfig.items():
            self.config[k]=v.copy()                 
        (addr, port) = self.config['default']['addr'];
        self.addr = addr
        self.port = port 
        self.isLogin = 0        
        self.currentConn = None
        self.backend = {}
        self.max_server_no = 0     
    
    def _send_request_to(self, cmd, table, tup, param, server_id_list=None, all_cluster=True):
        #连接所有服务器 
        if(server_id_list == None):
            server_id_list = self.backend.keys()
        result = []
        errors = [] 
        conn_list = []   
        for server_id in server_id_list:
            cluster = self.backend[server_id]
            succ=False
            for server in cluster:
                try:
                    conn = self.__getConnection(server)
                    rv = mySend(conn, cmd, table, tup, param)
                    conn_list.append(conn)
                    succ=True
                    if(not all_cluster): #集群中，只给其中一个发送
                        break
                except Exception, e:
                    print cmd,e
                    pass
            if not succ:
                errors.append((False,'local','There is some mashine is down.'))
        for conn in conn_list:                        
            data = myRecv(conn);
            if data:
                if data[0] == False:                       
                    errors.append(data)
                else:
                    result.append(data)
            else:
                errors.append((False,'local','connect closed by server'))
                #raise TSpaceError('connect closed by server');          
        return (result, errors) 
    
    def _send_request_one_to_one(self, cmd, table, tup, param, server_id_list, all_cluster=False):
        #连接所有服务器 
        if(server_id_list == None):
            server_id_list = self.backend.keys()
        result = []
        errors = []           
        for server_id in server_id_list:
            cluster = self.backend[server_id]
            for server in cluster:
                try:
                    conn = self.__getConnection(server)
                    rv = mySend(conn, cmd, table, tup, param)
                    
                    data = myRecv(conn);
                    if data:
                        if data[0] == False:                       
                            errors.append(data)
                        else:
                            result.append(data)
                            return (result, errors)
                    else:
                        errors.append((False,'local','connect closed by server'))
                        #raise TSpaceError('connect closed by server'); 
                    if(not all_cluster): #集群中，只给其中一个发送
                        break 
                except Exception, e:
                    print cmd,e
                       
        return (result, errors)        
        
    def login(self, user, password, table='*'):
        self.close() 
        result = []
        errors = []       
        for server in self.config.keys():
            server_no = self.config[server]['server_no']
            if(server_no > self.max_server_no):
                self.max_server_no = server_no
                
            try:   
                conn = self.__getConnection(server)
                mySend(conn, 'login', table, (user, password))
                data = myRecv(conn);
                if data:
                    if data[0] == False:
                        del self.config[server]['conn']
                        errors.append(data)                     
                    else:
                        server_config = data[2][1]
                        result.append(data) 
                        print 'ServerConfig:', server, '\n', server_config
                        self.user = user
                        self.password = password
                        self.isLogin = 1  
                        
                        #登陆成功加入后端列表                    
                        if server_no in self.backend:
                            self.backend[server_no].append(server)
                        else:
                            self.backend[server_no] = [server]
                    
            except Exception, e:                
                errMsg='when login %s,%s'%(server,str(e))
                print errMsg
                errors.append([False,server,errMsg])
        
        if(errors):
            return errors[0]
        if(result):
            return result[0] 
    
    #定位该元组的目标集群，并预处理元组.
    #返回None，表示所有集群都发送，否则返回集群id列表[],
    def _get_hash_conn(self, name, tup):        
        if len(tup) < 2: return None
        
        if type(tup[0]) == type([]):#如果是list，转为tuple
            tup[0] = tuple(tup[0])
        elif type(tup[0]) == type({}):
            raise TSpaceError('tuple[0] is dict type, not allowed!');             
        if type(tup)==type([]):
            tup[0]=str(tup[0])
        
        if type(tup[1]) == type([]):#如果是list，转为tuple
            tup[1] = tuple(tup[1])
        elif type(tup[1]) == type({}):
            raise TSpaceError('tuple[1] is dict type, not allowed!');  
            
        key = tup[1]
        if(type(key) == type(u'') or type(key) == type('')):            
            if(key[0] == '%' or key[0] == '$'):
                return None
        elif(type(key) == type((1,))):#是元组
            for k in key:
                if(type(k) == type('') and (k[0] == '%' or k[0] == '$')):
                    return None
            key = str(key)            
        elif(type(key) == type({})):
            key = str(key)
            
        i = hash(key) % (1 + self.max_server_no)
        
        if not self.isLogin:
            raise TSpaceError('you are not login!');                  
        return [i]
    
    """
       所有方法，均返回带结果状态的元组
    """  
    def table(self, name, value):
        if(len(value) < 2):
            raise TSpaceError('tuple length must great than 2,eg (key,group_id) ')
            return false
        result, errors = self._send_request_to('table', name, value, None, None) 
        if(errors):
            return errors[0]
        if(result):
            return result[0]
              
    def store(self, name, value):
        if(len(value) < 2):
            raise TSpaceError('tuple length must great than 2,eg (key,group_id) ')
            return false
        server_list = self._get_hash_conn(name, value)        
        result, errors = self._send_request_to('store', name, value, None, server_list) 
        if(errors):
            return errors[0]
        if(result):
            return result[0]
        return (False,'all','not store any data to server.') 

    #once return a [statu,server_key,tuple]
    def take(self, name, tuple, timeout=0):
        server_list = self._get_hash_conn(name, tuple)
        result, errors = self._send_request_one_to_one('take', name, tuple, timeout, server_list) 
        
        if(result):
            return result[0]
        if(errors):
            return errors[0]
        return (False,'all','not store any data to server.') 
        
    #once return a [statu,server_key,tuple]
    def fetch(self, name, tuple, timeout=0):
        server_list = self._get_hash_conn(name, tuple)
        result, errors = self._send_request_one_to_one('fetch', name, tuple, timeout, server_list) 
        if(result):
            return result[0]
        if(errors):
            return errors[0]  
        return (False,'all','not store any data to server.')  
        
    #once many tuple
    def find(self, name, tuple, max_length=1000):
        results = []
        server_list = self._get_hash_conn(name, tuple)
        result, errors = self._send_request_to('find', name, tuple, max_length, server_list,False) 
        #合并结果
        if(errors):
            return errors[0] 
        if(result):            
            for data in result:             
                results += (data[2])
        return (True,'all',results)   

    #once many tuple
    def remove(self, name, tuple):  
        results = 0
        server_list = self._get_hash_conn(name, tuple)
        result, errors = self._send_request_to('remove', name, tuple, None, server_list) 
        #合并结果
        if(result):            
            for data in result:             
                results += (data[2])
        return (True,'all',results)
        
    def close(self):        
        for server_no,cluster in self.backend.items():
            for server in cluster:
                if self.config[server].has_key('conn'):
                    conn = self.config[server]['conn']
                    conn.close() 
                    del self.config[server]['conn']
        self.backend.clear()

    def __del__(self):
        self.close()
# =================================Map Reduce====================================

    def filter(self, name, code, func):
        result = None
        
        try:            
            #code=compile(code, '<string>','exec')           
            #func = eval(func)  # func    
            #func=marshal.dumps(_func.func_code)          
                
            result, errors = self._send_request_to('filter', name, (code,func),None) 
            #不返回结果，结果存储在space
            if(errors):
                return errors[0]
            if(result):
                results=[]
                for data in result:             
                    results += (data[2])
                return (True,'all',results)   
              
        except Exception, e:             
            traceback.print_exc()           
            return False, 'proxy', str(e)
        
        
        

    def map_reduce(self, name, module_name, class_name,init_value=None):
        results = []
        result, errors = self._send_request_to('reduce', name, (module_name,class_name,init_value),None) 
        #返回结果，结果不存储在space         
        if(errors):
            return errors[0]
        if(result):
            for data in result:             
                results.append(data[2])       
            return (True,'all', results)
        
        
    def map(self, name, code, map_func,reduce_funce=None):
        result = None
        try:
            #code=compile(code, '<string>','exec')  
            """
            exec(code, locals())    
            if map_func:  
                map_func = eval(map_func)  # func 
                map_func=marshal.dumps(map_func.func_code)
            if reduce_funce:
                reduce_funce = eval(reduce_funce) 
                reduce_funce=marshal.dumps(reduce_funce.func_code)
            """                
            result, errors = self._send_request_to('map', name, (code,map_func,reduce_funce),None) 
            #不返回结果，结果存储在space
            if(errors):
                return errors[0]
            if(result):
                return result[0]     
              
        except Exception, e:             
            traceback.print_exc()           
            return False, 'proxy', str(e)
        
                 
           
# ==================================RPC==========================================
#exe不用等执行结果就返回，可以通过eval来获取结果，而且eval操作必然要等exe执行结束，因为他们在同一个线程中
#可以用来给TupleSpace定义自定义函数
    #@void(str,tuple): raise{str}
    def execute(self, fcode, args=None):
        
        """ kb.exe("($B,$C)=(12,4)")
            kb.exe("$A=Numeric.array",([[1,2],[3,4]]))
        """
        
        code = self.__getCode(fcode)
        if(args):         
            assert type(args) == type(()), "Waning:use exe(func,args),args must be tuple type.Example:exe('print',(12,))"             
            code = code + repr(args);    
         
        result, errors = self._send_request_to('exe', '', code,None,None) 
        if(errors):
            return errors[0]
        if(result):
            return result[0]
   

    #data="$q" or "($A,$B)" 
    #@object(str):raise{str}              
    def eval(self, data):             
        code = self.__getCode(data)                 
        result, errors = self._send_request_to('eval', '', code,None,None) 
        if(errors):
            return errors[0]
        if(result): 
            results=[]                     
            for data in result:             
                results.append(data[2])
            return (True,'all',results)
        
        
    def handle_cmd(self, msg):
        base = self          
        if msg[0] == 'store':    
            sdata = base.store(msg[1], msg[2])
            return sdata
            
        elif msg[0] == 'take':
            sdata = base.take(msg[1], msg[2])                   
            return sdata
        
        elif msg[0] == 'remove':
            sdata = base.remove(msg[1], msg[2])                   
            return sdata
        
        elif msg[0] == 'fetch':
            sdata = base.fetch(msg[1], msg[2])                   
            return sdata

        elif msg[0] == 'find':
            sdata = base.find(msg[1], msg[2])                   
            return sdata
        
        elif msg[0] == 'login':                    
            return self.login(msg)        
        else:
            return (False, 'unsuppored message.')
        
    def __getCode(self, data):
        i = 0; code = ''; bIsIn = False;
        while (i < len(data)):
            if data[i] == "'": 
                bIsIn = not bIsIn; code += data[i];
            elif data[i] == '$' and  not bIsIn:
                code += self.user + '_';             
            else:
                code += data[i]
            i += 1   
        return code;
    
    #获取内部服务器的连接，server为服务器标识
    def __getConnection(self, server):
        if self.config.has_key(server):
            conf = self.config[server]            
            if not conf.has_key('conn') or not conf['conn']: 
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(conf['addr'])
                conf['conn'] = s
                return s
            return conf['conn']        
            
        else:
            print 'not find server %s.' % server
        return None
        
#end

# ###############################################################################


def test_1(space):    
    print 'application started'
  
    
    space.login('junphine', 'erihrofgh')

    
    print space.eval('session')
    space.table('teacher',{'fields':'id,school,name,score','shelved':false,'sorted':false,'indexes':[3]})
    
    for i in xrange(0, 20):
        #教师表 编号  姓名
        #space.remove('teacher', [i, ANY, ANY , ANY])
        space.store('teacher', [i, (i/3, 3+i), u'Zhang 俊峰', 45.5+i])
        if i % 2 == 0:
            space.store('school', [i/3, '西北大学',1230]) 
        else:
            space.store('school', [i/3, '东北大学',4232]) 
            
    """
    如何实现inner join？按tuple[0]hash存储,并且tuple是不可变的
    执行函数 inner_join(teacher,teacher.school)，生成新的视图teacher&teacher.school
    teacher&teacher.school的数据为[teacher,teacher.school]
    left_join:  teacher>teacher.school
    right_join: teacher<teacher.school
    """

    print 'fetch'
    for i in xrange(0, 20 - 1):
        rv,server,teacher = space.fetch('teacher', [i, out, '%Zha', '%'])
        if rv:
            print 'teacher=', teacher
            print 'teacher=', teacher.id,teacher.school
        else:
            print 'error',teacher
    
    print 'take'
    for i in xrange(0, 2):
        rv,server,teacher = space.take('teacher', [i, out, out , 45.500+i])       
        print 'teacher=', teacher
        if rv:
            assert teacher[0] == str(i), 'ERR'
    
    func = """
def m(k,x):
    y=list(x)
    y[3]/=100.0 #百分制分值转化为小数
    yield None,y[1],y[3] #除姓名外的字段返回.None表示返回的key保持不变，这样不会垮集群计算
    
def f(x):
    return x[1]> 5 #学校id大于5

"""

    
    print 'test filter:' 
    #复杂查询处理
    rv,s,teachers=space.filter('teacher',func,'f');
    #no generate table teacher.f      
    for teacher in teachers:
        print 'teacher.f=', teacher

   

    #map通过自定义函数调用map or reduce
    space.map('teacher', func,'m');
    
    rv,s,teachers = space.find('teacher.m', ())   
    for teacher in teachers:
        print 'teacher.m=', teacher
    


    init_value = 3  
    #调用已经预定的map-reduce任务
    space.map_reduce('teacher', 'example', 'Example', init_value);
    
    #generate teacher.f.r
    rv,s,no_teacher = space.fetch('teacher.example.Example', ('$'))    
    print 'teacher.f.example.Example=', no_teacher

    res = space.fetch('teacher.example.Example.reduce', (ANY,),1)    
    print 'teacher.example.Example.reduce', res    

    func = """
def school(k,x):    
    yield x[1][0],x[0],x[3] #返回school_id,teacher_id,score
    
def mean(x,v):
    total=0.0
    for y in v:
        total+=y[2]
    mean_value=total/len(v)
    yield x, mean_value
"""
    
    space.map('teacher', func,'school','mean');
    while True:
        res = space.take('teacher.school.mean', (ANY,),1)    
        print 'teacher.school.mean', res 
        if not res[0]:
            break
    input()


step=0
step2=100

#1000 call per run
def test_bench(space):
    global step,step2;
    
    space.eval('session')
    for i in xrange(step, step2):
        #教师表 编号  姓名
        space.store('teacher', [i, (12+i, 3.14), u'Zhang 俊峰', 15]) 
        if i % 2 == 0:
            space.store('teacher_school', [i,i, '西北大学']) 
        else:
            space.store('teacher_school', [i,i, '东北大学']) 
            

    for i in xrange(step, step2):
        rv,server,teacher = space.fetch('teacher', [i, out, '%Zha', '%1'])
        if not rv:
            print 'teacher=', teacher        

    for i in xrange(step, step2):
        rv,server,teacher = space.take('teacher', [i, out, out , 15])  
        if not rv:     
            print 'teacher=', teacher


    for i in xrange(step, step2):
        #教师表 编号  姓名
        space.store('teacher', [i, (12+i, 3.14), u'Zhang 俊峰', 15]) 
        if i % 2 == 0:
            space.store('teacher.school', [i,i, '西北大学']) 
        else:
            space.store('teacher.school', [i,i, '东北大学'])                  
    
    func = """
def m(k,x):
    y=list(x)
    y[3]+=100   
    yield k,y[1],y[3]
    
def f(x):
    return x[0]>15

"""

  
    func2 = """
def mean(x,v):
    y=[0]
    y[0]=0
    yield x, y,2,3,4,5
"""
   
    
    #select
    for i in xrange(step, step2):
        rv,s,teachers=space.filter('teacher', func, 'f');
       
    
    #map 通过函数调用map
    space.map('teacher', func, 'm');
    for i in xrange(step, step2):
        rv,s,teachers = space.find('teacher.m', (ANY,(12+i, 3.14)))
        pass

    
   
    init_value = 3  
    #调用已经预定的map-reduce任务
    for i in xrange(step, step2):
        reduce=space.map_reduce('teacher', 'example', 'Example', init_value);    
        space.map('teacher.example.Example.reduce', func2,'mean');
        
     
        
    res,s,result= space.fetch('teacher.example.Example.reduce', (ANY,),1)    

    
    #space.close()
    #raw_input()
    step+=100
    step2+=100

def test_2(tb):
   
    tb.store('translate', [u'china', 1, u'中国'])
    tb.store('translate', [u'USA', 0, ''])    
    r = tb.take('translate', [u'USA',1,'$']);
    print '=======', r
    r = tb.take('translate', [u'$key',1,'$']);
    print '=======', r
    r = tb.store('translate', r);
    
      


if __name__ == "__main__":
    import time
    space = TSpaceProxy(config.ServerConfig)
    print space.login.__name__
    space.login('junphine', 'erihrofgh')
    
    test_1(space)
    b=time.time()
    for i in xrange(1,1000):
        test_bench(space)
        e=time.time()        
        print 'spend',e-b
        b=e
    #__test2(space) 
       
    print 'finish'
    raw_input()


