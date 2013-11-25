#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2001 actzero, inc. All rights reserved.


import string
import sys, time, array
import traceback
import shelve
import bsddb
import os
import random
import thread
from threading import *
from multiprocessing import Pool

from socket import *
from SocketServer import *
from BaseHTTPServer import *
import logging

try:
    from  collections import OrderedDict;
except:
    from  odict import OrderedDict;
import collections

from shared import *
import _config as config
import tspace;

sys.path.append('./jobs')

__version__ = "2.6"

# default configuration
_config = {
    'NCPU':2,  # CPU Number
    'root_dir': "tbase",
    'users_file':'users.txt',
    'server_key':'default',
    'user':     'junphine',
    'password': 'erihrofgh'
}



userAuthMap = { }  
 
userfd = open(_config['users_file'], 'r')

users = userfd.readlines();
for user in users:
    items = user.split(':')
    if len(items) >= 2:
        for i in xrange(0, len(items)):
            items[i] = items[i].strip()        
        userAuthMap[items[0]] = items;
# print userAuthMap  

logging.basicConfig(level=logging.WARN)
running = True
    

def namedtuple2(typename, field_names, verbose=False):
    """Returns a new subclass of tuple with named fields.

    >>> Point = namedtuple('Point', 'x y')
    >>> Point.__doc__                   # docstring for the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate with positional args or keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessable by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert from a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    # Parse and validate the field names.  Validation serves two purposes,
    # generating informative error messages and preventing template injection attacks.
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', ' ').split() # names separated by whitespace and/or commas
    field_names = tuple(map(str, field_names))
    for name in (typename,) + field_names:
        if not all(c.isalnum() or c=='_' for c in name):
            raise ValueError('Type names and field names can only contain alphanumeric characters and underscores: %r' % name)
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a keyword: %r' % name)
        if name[0].isdigit():
            raise ValueError('Type names and field names cannot start with a number: %r' % name)
    seen_names = set()
    for name in field_names:
        if name.startswith('_'):
            raise ValueError('Field names cannot start with an underscore: %r' % name)
        if name in seen_names:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen_names.add(name)

    # Create and fill-in the class template
    numfields = len(field_names)
    argtxt = repr(field_names).replace("'", "")[1:-1]   # tuple repr without parens or quotes
    reprtxt = ', '.join('%s=%%r' % name for name in field_names)
    dicttxt = ', '.join('%r: t[%d]' % (name, pos) for pos, name in enumerate(field_names))
    template = '''class %(typename)s(tuple):
        '%(typename)s(%(argtxt)s)' \n
        __slots__ = () \n
        _fields = %(field_names)r \n
        def __new__(cls, %(argtxt)s):
            return tuple.__new__(cls, (%(argtxt)s)) \n
        @classmethod
        def _make(cls, iterable, new=tuple.__new__, len=len):
            'Make a new %(typename)s object from a sequence or iterable'
            result = new(cls, iterable)
            if len(result) != %(numfields)d:
                raise TypeError('Expected %(numfields)d arguments, got %%d' %% len(result))
            return result \n
        def __repr__(self):
            return '%(typename)s(%(reprtxt)s)' %% self \n
        def _asdict(t):
            'Return a new dict which maps field names to their values'
            return {%(dicttxt)s} \n
        def _replace(self, **kwds):
            'Return a new %(typename)s object replacing specified fields with new values'
            result = self._make(map(kwds.pop, %(field_names)r, self))
            if kwds:
                raise ValueError('Got unexpected field names: %%r' %% kwds.keys())
            return result \n
        def __getnewargs__(self):
            return tuple(self) \n\n''' % locals()
    for i, name in enumerate(field_names):
        template += '        %s = property(itemgetter(%d))\n' % (name, i)
    if verbose:
        print template

    # Execute the template string in a temporary namespace and
    # support tracing utilities by setting a value for frame.f_globals['__name__']
    namespace = dict(itemgetter=_itemgetter, __name__='namedtuple_%s' % typename)
    try:
        exec template in namespace
    except SyntaxError, e:
        raise SyntaxError(e.message + ':\n' + template)
    result = namespace[typename]

    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in enviroments where
    # sys._getframe is not defined (Jython for example).
    if hasattr(_sys, '_getframe'):
        result.__module__ = _sys._getframe(1).f_globals['__name__']

    return result

class Table:
    
    def __init__(self, name, shelved=False, queue=False):
        global _config;
        self.name = name
        self.shelved = shelved 
        self.queue = queue
        self.condition = Condition()
        self.keys = {}  # key
        self.indexs = {}  # 对tuple【2】的索引
        self.count = 0       
        self.scheme=None
        if shelved:
            # open db   
            path = '%s/%s_%s.bsd' % (_config['root_dir'], _config['server_key'], name)
            if self.queue:
                bsd = bsddb.rnopen(path, 'c')
            else:                
                bsd = bsddb.btopen(path, 'c')
                
            self.db = shelve.BsdDbShelf(bsd)
            # self.db['中文']='test'
            # print self.db.keys()
            # del self.db['中文']
           
        else:
            if self.queue:
                self.db = OrderedDict()  # memery db
            else:
                self.db = {}  # memery db
            
    def add_tuple(self, tuple):
        key = tuple[0]        
        if self.db.has_key(key):
            return False 
        if self.queue:
            if key == None:
                key = self.count       
        self.db[key] = tuple
        self.count += 1
        return True
    
    def add_indexs(self, value, i=2):
        return            
        if len(value) > i:
            index_field = value[i]
            if index_field == None:
                return  # 空值不建立索引，节约内存空间    
            if(type(index_field) == type([])):  # 是list，则转为tuple
               index_field = tuple(index_field)
               return
            if type(index_field) != type({}) :  # 需要索引value[0]
                if self.indexs.has_key(index_field):
                    self.indexs[index_field].append(value[0])
                else:
                    self.indexs[index_field] = [value[0]]
            else:
                # TODO@byron 对map建立索引
                pass
        pass
    
    def get_tuple(self, k):
        return self.db.get(k, None)
  
    
    def tuples(self, k=None):       
        if self.shelved:
            r = []            
            if type(k) == type([]):           
                for i in k:
                   tup = self.db.get(i, None)
                   if(tup): r.append(tup)
                return r            
        
            try:
                self.condition.acquire()
                tup = self.db.first();
                while(tup):
                    r.append(tup[1])
                    tup = self.db.next()
                self.condition.release()
            except Exception, e:
                self.condition.release()
                pass
            return r
        else:
            if type(k) == type([]):
                r = []           
                for i in k:
                   tup = self.db.get(i, None)
                   if tup: r.append(tup)
                return r            
            return self.db.values()

 
    def clear(self):
        self.keys = {}  # key:index for partion
        self.tuples = []
        self.indexs = {} 
        self.count = 0
        self.db.clear()
        
    def sync(self):
        pass      
                    
    def __str__(self):
        string = "";        
        for item in self.tuples()[0:10]:
            string += '%s\n' % (str(item))            
        return string
            
        
class TupleBase:
    def __init__(self, _config, shelved=False):        
                
        self.space = {}  # string->Table
        self.glock = Lock()
        self.shelved = shelved        
        # open meda db      
        self.tables = Table('information_schema.tables', shelved)            
        self.tables.db['system'] = ['system', 1]
        self.space['information_schema.tables'] = self.tables
        if self.tables.db:
            
            keys = self.tables.db.keys()
            for name in keys:
                record = self.tables.db[name]
                tab = self._create_table(name, shelved)
                tab.count = record[1]
                print 'load table ', tab.name   
            
        # for map reduce    
        tab = self._create_table('system.map_jobs', false, True) 
        tab = self._create_table('system.reduce_jobs', false, True) 
        tab = self._create_table('system.map_reduce_status', false)                              
        
        # self.event=Event()   
        # self.event.set()        
        # self.condition=Condition()
        """
        """
    def _create_table(self, key, shelved, queue=False):
        self.glock.acquire()
        if self.space.has_key(key):
            self.glock.release()
            return self.space[key]
        # 创建一个table
        tab = Table(key, shelved, queue)
        self.tables.db[key] = [key, tab.count]
        self.space[key] = tab
        self.glock.release()  
        return tab
    
    # 元组的field是否为实体，即非变量，模式，这些都是字符串类型
    def _has_key_field(self, value, i=0):
        if value[i] == None:
            return false  # None虽然也是实体，但系统不会为空建立索引，所以这里返回false。
        if type(value[i]) == type('')  and (value[i][0] == '$'  or value[i][0] == '%'):
            return false
        if type(value[i]) == type(u'')  and (value[i][0] == u'$'  or value[i][0] != u'%'):
            return false                     
        return true 
       
    def table(self, key, info):
        if key.startswith('system.'):            
            shelved = info.get('shelved', False)
        else:
            shelved = info.get('shelved', self.shelved)
        queue = info.get('sorted', False)
        tab = self._create_table(key, shelved, queue)
        fields=info.get('fields',None)
        if fields:
            tab.scheme=collections.namedtuple(key,fields,True)            
        return (True,(tab.name,tab.count))
        
    def store(self, key, value):        
        """space={key:[count,[tup1,tup2,tup3],condition,index]}
        """
        if not value or not value[0]:
            return (False, "tuple[0] is empty.")
        if not key:
            return (False, "table name is empty.") 
        
        if self.space.has_key(key):
            # self.space[key][1].insert(0,value)
            info = self.space[key] 
            info.condition.acquire()
            if info.scheme:
                value=info.scheme(*value)
                buff=pickle.dumps(value)
                input()
            else:
                value = tuple(value) #todo
            rv = info.add_tuple(value)
            if(not rv):
                info.condition.release()
                return (False, 'tuple %s already exist.' % value[0])
            
            # info.add_indexs(value) 
            info.condition.notifyAll()
            info.condition.release()
            return (True, info.count)
        else:                   
            
            if key.startswith('system.'):            
                shelved = False
            else:
                shelved = self.shelved
            tab = self._create_table(key,shelved)
            
            tab.condition.acquire()
              
            rv = tab.add_tuple(value)            
            if(rv):  tab.add_indexs(value) 
            
            tab.condition.notifyAll()
            tab.condition.release()
            if(not rv):
                return (False, 'tuple %s already exist.' % value[0])
            return (True, 1)

    def find(self, key, value, session):
        if not self.space.has_key(key):                
            return (False, "not find table.",)  
        info = self.space[key]
        valueR = []
        
        index = info.indexs
        if not value:
            valueR = info.tuples()            
            return (True, valueR)  
           
        if index and len(value) > 2 and self._has_key_field(value, 2):
            
            if index.has_key(value[2]):  # 全索引，不能建立部分索引
                valuelist = index[value[2]]
                valuelist = info.tuples(valuelist) 
            else:
                valuelist = []
        else:
            valuelist = info.tuples()         
        
        for it in valuelist:
            bR = self.__matched(it, value)
            if bR:
                valueR.append(it)
        
        return (True, valueR)   
         
    # 按照堆栈方式，后进先读   
    def fetch(self, key, value, timeval, session={}):
        if not value:
            return (False, "value is empty.",)        
        is_running = 0      
        while(is_running < 2): 
            if not self.space.has_key(key):
                return (False, "not find table " + key)   
            
            info = self.space[key]
            condition = info.condition            
            flags = info.count
            index = info.indexs                            
            if self._has_key_field(value):
                tup = info.get_tuple(value[0]) 
                bR = self.__matched(tup, value)
                if bR:                   
                    return (True, tup)
                else:                    
                    pass
            elif index and len(value) > 2 and self._has_key_field(value, 2):
                
                if index.has_key(value[2]):
                    valuelist = index[value[2]]                    
                    for it in valuelist:   
                        tup = info.get_tuple(it)             
                        bR = self.__matched(tup, value)
                        if bR:
                             valueR = tup;                                             
                             return (True, valueR)
            else:
                valuelist = info.db.keys()                             
                for it in valuelist:
                    tup = info.get_tuple(it)              
                    bR = self.__matched(tup, value)
                    if bR:
                         valueR = tup;                                           
                         return (True, valueR)
            # trace(".take not find value:",key,value)
            
            if is_running == 0 and timeval > 0:
                condition.acquire()
                info.condition.wait(timeval)
                condition.release()
            else:
                is_running += 1
            is_running += 1
            
        return (False, 'tuple %s not exist.' % value[0]) 
    
    # 删除所有的符合模式的元组  
    def remove(self, key, value=[]):        
        if(key):
            if not self.space.has_key(key):                
                return (False, "not find table.",) 
            valueR = []
            info = self.space[key] 
            flags = info.count   
            index = info.indexs           
            if not value:
                self.glock.acquire()
                info.condition.acquire()
                info.clear()
                del self.space[key]
                if self.tables.db.has_key(key):
                    del self.tables.db[key]
                info.condition.notifyAll()
                info.condition.release()
                self.glock.release()
                return (True, flags)
            
            if self._has_key_field(value):
                it = info.get_tuple(value[0])                        
                bR = self.__matched(it, value)
                if bR:
                     valueR.append(it)
                   
            elif index and len(value) > 2 and self._has_key_field(value, 2): 
                valuelist = [] 
                if index.has_key(value[2]):          
                    valuelist = index[value[2]]
                    valuelist = info.tuples(valuelist)
                    for it in valuelist:                
                        bR = self.__matched(it, value)
                        if bR:
                             valueR.append(it)                
            else:
                valuelist = info.tuples()               
                for it in valuelist:                
                    bR = self.__matched(it, value)
                    if bR:
                         valueR.append(it)
            info.condition.acquire()
            for it in valueR:
                if index.has_key(it[2]):
                    index[it[2]].remove(it[0])
                try:
                    del info.db[it[0]]  
                except:
                    pass              
            info.condition.notifyAll()              
            info.condition.release()                
        return (True, len(valueR))
    
    # 按照队列方式，先进先出       
    def take(self, key, value, timeval, session={}):
        if not value:
            return (False, "value is empty.",)        
        is_running = 0      
        while(is_running < 2): 
            if not self.space.has_key(key):
                return (False, "not find table " + key)   
            
            info = self.space[key]
            condition = info.condition            
            flags = info.count
            index = info.indexs                            
            if self._has_key_field(value):
                tup = info.get_tuple(value[0]) 
                bR = self.__matched(tup, value)
                if bR:
                    condition.acquire()
                    if index and len(tup) > 2 and index.has_key(tup[2]):
                        index[tup[2]].remove(it)   
                    del info.db[tup[0]]
                    condition.release()
                    return (True, tup)
                else:                    
                    pass
            elif index and len(value) > 2 and self._has_key_field(value, 2):
                
                if index.has_key(value[2]):
                    valuelist = index[value[2]]                    
                    for it in valuelist:   
                        tup = info.get_tuple(it)             
                        bR = self.__matched(tup, value)
                        if bR:
                             valueR = tup;
                             condition.acquire()                             
                             valuelist.remove(it)
                             try:  
                                 del info.db[it]
                             except:
                                 pass              
                             condition.release()                   
                             return (True, valueR)
            else:
                valuelist = info.db.keys()                             
                for it in valuelist:
                    tup = info.get_tuple(it)              
                    bR = self.__matched(tup, value)
                    if bR:
                         valueR = tup;
                         condition.acquire()
                         if index and len(tup) > 2 and index.has_key(tup[2]):
                            index[tup[2]].remove(it) 
                         try:
                             del info.db[it]
                         except:
                             pass
                         condition.release()                     
                         return (True, valueR)
            # trace(".take not find value:",key,value)
            
            if is_running == 0 and timeval > 0:
                condition.acquire()
                info.condition.wait(timeval)
                condition.release()
            else:
                is_running += 1
            is_running += 1            
                
        return (False, 'tuple %s not exist.' % value[0]) 
    
    def close(self):
        print 'begin save data.' 
        for key in self.space.keys():
            info = self.space[key] 
            condition = info.condition
            condition.acquire()
            condition.notifyAll()
            condition.release()
            if(info.shelved):
                print 'begin close table ' + info.name 
                info.db.close()        

    def __matched(self, srcTup, destTup):
        # import pdb   
        if srcTup==None: return False     
        i = 0        
        ilen = min(len(destTup), len(srcTup))
        while i < ilen:
            src = srcTup[i]  # 原元组            
            if(type(src) == type('')):
                src_str = unicode(src, 'utf-8', 'ignore')
            else:
                src_str = unicode(src)
            dest = destTup[i]  # 模式元组
            i += 1        
            if(dest != '' and src != dest and src_str != dest):
                # pdb.set_trace()
                if type(dest) == type(''):
                    if (dest[0] == '$'):  # 是变量,可以考虑类型匹配                        
                        continue
                    if (dest[0] == '%' and src_str.find(dest[1:]) >= 0):  # 是匹配串                        
                        continue
                elif type(dest) == type(u''):
                    if (dest[0] == u'$'):  # 是变量                        
                        continue
                    if (dest[0] == u'%' and src_str.find(dest[1:]) >= 0):  # 是匹配串                        
                        continue                
                return False                    

        return True
    
    

# 为false是内存TupleBase，为True是持久化的TupleBase

tuple_space = None
server = None

random.seed()


     

class MapReduceThread(Thread):
    
    def __init__(self, tuple_space):
        global _config  
        Thread.__init__(self)
        self.server_key = _config['server_key'];  
        self.space_proxy = None
        self.tuple_space = tuple_space        
        
    def run(self):
        global running;     
        # 处理何种task    
        tmp_map_process = True
        last_job_key=''
        while(running):
            try:
                if tmp_map_process:
                    while True:
                        rv, job = tuple_space.take('system.map_jobs', ('$',), 2)
                        if(rv and job):
                            tup_job_key, table, tup_map_func, tup_combine_func, tup_reduce_func = job            
                            succ = self.do_map(tup_job_key, table, tup_map_func, tup_combine_func, tup_reduce_func)
                        else:
                            tmp_map_process = False
                            break
                        
                        
                else:
                    
                    while True:
                        rv, job = tuple_space.take('system.reduce_jobs', ('$',), 4)
                        if(rv and job):                
                            tup_job_key, table, tup_reduce_func, tmp = job     
                                               
                            succ = self.do_reduce(tup_job_key, table, tup_reduce_func)                        
                            if not succ:
                                tuple_space.store('system.reduce_jobs', job)                            
                                if last_job_key==tup_job_key: 
                                    tmp_map_process=True
                                    break
                                last_job_key=tup_job_key                                              
                        else:
                            tmp_map_process = True
                            break
            except Exception,e:
                logging.error("MapReduceThread %s" % str(e))
                traceback.print_exc()
    
            
    def do_map(self, tup_job_key, table, tup_map_func, tup_combine_func=None, tup_reduce_func=None): 
        
        if tup_map_func:
            
            result_map_list = self.tuple_space.space[table].tuples()
   
            logging.info("Mapping %s" % tup_job_key)
            results = {}
            local_result = {}
            for data in result_map_list:
                for v in tup_map_func(data[0], data):
                    k = v[0]
                    if k == None:  # 本地存储
                        k = data[0]
                        if k not in local_result:
                            local_result[k] = []
                        local_result[k].append(v)
                    else:
                        if k not in results:
                            results[k] = []
                        results[k].append(v)
                    
            if tup_combine_func:  # for performence
                for k in results:
                    result = results[k]
                    results[k] = tup_combine_func(k, result)
                for k in local_result:
                    result = local_result[k]
                    local_result[k] = tup_combine_func(k, result)
                    
            for k in local_result:
                result = local_result[k]  
                # 不需要异地交换数据，key 为空的话，本地直接存储          
                self.tuple_space.store(tup_job_key, (k, k, result))          
            
            if tup_reduce_func:
                # 给所有集群发送start状态    
                while True:                   
                    rv, msg = self.tuple_space.store('system.map_reduce_status', (tup_job_key, ANY, self.server_key, 'start'))                   
                    if rv:  # 另一个相同任务已经运行，需要等待
                        break
                    self.tuple_space.fetch('system.map_reduce_status', (tup_job_key, ANY, self.server_key, '___no_match___'), 60)  
                    
             # 加锁，防止发送数据出错
           
            if not self.space_proxy:
                logging.info("Begin to connect all tuple space.")   
                self.space_proxy = tspace.TSpaceProxy(config.ServerConfig)    
                self.space_proxy.login(_config['user'], _config['password'])
                
            rv = True  
            for k in results:
                result = results[k]
                rv, s, data = self.space_proxy.store(tup_job_key, (k, k, result)) 
                if not rv: #already exists  
                    logging.info("Mapping: %s" % data) 
                    #break                
            if tup_reduce_func:            
                self.tuple_space.remove('system.map_reduce_status', (tup_job_key, ANY, self.server_key, 'start'))                    
            
            # if not rv:
                # self.space_proxy=None
                # logging.info("Mapping Failed %s,%s" %(tup_job_key,'there is some mashine is down in cluster!'))   
                
            logging.info("Mapping Done %s" % tup_job_key)   
            return True
       
            
    def do_reduce(self, tup_job_key, table, tup_reduce_func): 
            
        if tup_reduce_func:
            
            if not self.space_proxy:
                logging.info("Begin to connect all tuple space.")   
                self.space_proxy = tspace.TSpaceProxy(config.ServerConfig)    
                self.space_proxy.login(_config['user'], _config['password'])
                        
            while True:                
                rv, s, result = self.space_proxy.find('system.map_reduce_status', (tup_job_key, ANY, ANY, 'start'))                
                if rv:
                    if result == []:  # 没有__map_key start的记录，则表示所有map任务结束
                        break
                    return False
                else:
                    self.tuple_space.store('system.map_reduce_status', (tup_job_key, ANY, self.server_key, 'error', 'there is some mashine is down in cluster!')) 
                    self.space_proxy = None
                    return False
            
            result_map_list = []  
            if self.tuple_space.space.has_key(tup_job_key):
                result_map_list = self.tuple_space.space[tup_job_key].tuples()  
                
            tup_job_key += '.' + tup_reduce_func.func_name
            
            logging.info("Reducing %s" % tup_job_key)     
            # 等待所有map任务结束   
       
            for data in result_map_list:   
                for v in tup_reduce_func(data[0], data[2]):
                    k = v[0]
                    self.tuple_space.store(tup_job_key, v)
            logging.info("Reducing Done %s" % tup_job_key)     
            return True  
  

class TupleBaseRequestHandler:
    def __init__(self):    
        global tuple_space  
        global _config  
        self.server_key = _config['server_key'];  
        self.client = ''
        self.clientid = 0
        self.session = {}
        
        self.tuple_space = tuple_space
        self.threaded = False
       
        
    def handle_login(self, msg):
        global userAuthMap;  
        if(len(msg) > 2):
            try:
                table = msg[1]
                login = msg[2]  # (user,password)
                if login[1] == userAuthMap[login[0]][1]:  # password check
                    try:
                        import uuid
                        self.clientid = uuid.uuid1().hex
                    except:
                        pass 
                    
                    self.client = login[0]                        
                    logging.info('%s from (%s) has logined.' % (self.client, self.client_address))
                    return (True, (self.clientid, config.ServerConfig));                       
                    
                else:
                    return(False, 'password error.');
            except Exception, e:                        
                print >> sys.stderr, e
                traceback.print_exc()       
                return(False, str(e));
                  
        return(False, 'login failed.')
    
    def handle_logout(self, msg):
        global userAuthMap; 
        if(len(msg) > 2):
            client = msg[2]
            if(client[0] == self.client and client[1] == self.clientid):                     
                self.client = None
                self.clientid = None
                self.session = {}
                return (True, 'logout OK.',)
        return(False, 'logout failed.')       
                    
    def handle_filter(self, msg):
        global tuple_space; 
        table = msg[1] 
        if not tuple_space.space.has_key(table):
            return (False, 'table %s not exist!' % table)
            
        code = msg[2][0]  # code
        tup_map_func = None
        try:            
            if code:
                exec(code, locals())
            tup_map_func = eval(msg[2][1])  # func             
            
        except Exception, e:             
            traceback.print_exc()
            mySend(self.request, False, self.server_key, str(e))
            return
        # TODO 异步执行
        table = msg[1]                           
        result_map_list = self.tuple_space.space[table].tuples()
        __map_value = filter(tup_map_func, result_map_list)
        
        """
        tup_job_key = table + '.' + msg[2][0]
        tup_job_key = str(tup_job_key)
        tab = self.tuple_space._create_table(tup_job_key, false)
        for tup in __map_value:
            tab.add_tuple(tup)
        """
        mySend(self.request, True, self.server_key, __map_value)

                    
    def handle_map(self, msg):
        global tuple_space;        
        table = msg[1] 
        if not tuple_space.space.has_key(table):
            return (False, 'table %s not exist!' % table)
            
        code = msg[2][0]  # code
        tup_map_func = None 
        tup_reduce_func = None       
        try:
            if code:
                exec(code, locals())            
            if msg[2][1]:
                tup_map_func = eval(msg[2][1])  # func 
            if msg[2][2]:
                tup_reduce_func = eval(msg[2][2])  # func  
              
        except Exception, e:             
            traceback.print_exc()
            mySend(self.request, False, self.server_key, str(e))
            return
        
        # 应该创建线程异步调用
        table = msg[1]        
        result_map_list = self.tuple_space.space[table].tuples()                  
        # print result_map_list                    
        tup_job_key = table + '.' + tup_map_func.func_name  # key.map
        tup_job_key = str(tup_job_key)
        # condition = tuple_space.space[table].condition
        # condition.acquire()        
        if tup_map_func: 
            tab = self.tuple_space._create_table(tup_job_key, false)
            
        # 注册map reduce任务
        if tup_map_func:            
            job = (tup_job_key, table, tup_map_func, None, tup_reduce_func)
            rv, data = self.tuple_space.store('system.map_jobs', job)           
            if not rv:
                mySend(self.request, rv, self.server_key, data)      
            else:   
                if tup_reduce_func:                   
                    tab = self.tuple_space._create_table(tup_job_key + '.' + tup_reduce_func.func_name, false)                       
                    job = (tup_job_key, tup_job_key, tup_reduce_func, None)
                    rv, data = self.tuple_space.store('system.reduce_jobs', job)           
                    if not rv:
                        mySend(self.request, rv, self.server_key, data)
                    else:
                        mySend(self.request, True, self.server_key, 'installed map and reduce') 
                else: 
                    mySend(self.request, True, self.server_key, 'installed map')                         
                
        else:
            mySend(self.request, False, self.server_key, 'nothing to install')      
           
 
        # condition.notifyAll()
        # condition.release()
        # print __map_value
        
      
            
    def handle_reduce(self, msg):
        global tuple_space; 
        table = msg[1] 
        if not tuple_space.space.has_key(table):
            return (False, 'table %s not exist!' % table)
            
        module_name = msg[2][0]  # code
        map_reduce_class = msg[2][1]
        init_value = msg[2][2]

        try:
           
            mod = __import__(module_name)
            reload(mod)
            
            map_reduce_cls = getattr(mod, map_reduce_class)
            
            if init_value == None:
                object = map_reduce_cls() 
            else:
                object = map_reduce_cls(init_value)            
            
            tup_map_func = getattr(object, 'map', None);
            tup_combine_func = getattr(object, 'combine', None);
            tup_reduce_func = getattr(object, 'reduce', None);  
                  
        except Exception, e:             
            traceback.print_exc()
            mySend(self.request, False, self.server_key, str(e))
            return
        # 应该创建线程异步调用
        table = msg[1] 
        tup_job_key = table + '.' + module_name + '.' + map_reduce_class
        tup_job_key = str(tup_job_key)       
      
        rv = False
        # 注册map reduce任务
        if tup_map_func:
            tab = self.tuple_space._create_table(tup_job_key, false)          
            job = (tup_job_key, table, tup_map_func, tup_combine_func, tup_reduce_func)       
            rv, data = self.tuple_space.store('system.map_jobs', job)
            if not rv:
                mySend(self.request, rv, self.server_key, data) 
                return
          
        if tup_reduce_func: 
            tab = self.tuple_space._create_table(tup_job_key + '.' + tup_reduce_func.func_name, false)    
            job = (tup_job_key, tup_job_key, tup_reduce_func, None)
            rv, data = self.tuple_space.store('system.reduce_jobs', job)    
            if not rv:
                mySend(self.request, rv, self.server_key, data)
                return
          
        if rv:  
            mySend(self.request, True, self.server_key, 'installed map or reduce')               
        else: 
            mySend(self.request, False, self.server_key, 'nothing installed')   

    def handle_cmd(self, msg):
        global tuple_space, running;            
        if msg[0] == 'store':    
            sdata = tuple_space.store(msg[1], msg[2])
            return sdata
        
        elif msg[0] == 'table':
            sdata = tuple_space.table(msg[1], msg[2])                
            return sdata 
        
        elif msg[0] == 'take':
            sdata = tuple_space.take(msg[1], msg[2], msg[3], self.session)                   
            return sdata
        
        elif msg[0] == 'remove':
            sdata = tuple_space.remove(msg[1], msg[2])                   
            return sdata
        
        elif msg[0] == 'fetch':
            sdata = tuple_space.fetch(msg[1], msg[2], msg[3], self.session)                   
            return sdata

        elif msg[0] == 'find':
            sdata = tuple_space.find(msg[1], msg[2], self.session)                   
            return sdata
        
        elif msg[0] == 'filter':                    
            return self.handle_filter(msg)
        
        elif msg[0] == 'map':                    
            return self.handle_map(msg)
        
        elif msg[0] == 'reduce':                    
            return self.handle_reduce(msg) 
        else:
            return (False, 'unsuppored message.')
          

class RequestHandler(BaseRequestHandler, TupleBaseRequestHandler):
    connCounter = 0    
    def setup(self):        
        TupleBaseRequestHandler.__init__(self)
        print 'Get a new connection!'          
        self.clientid = RequestHandler.connCounter
        RequestHandler.connCounter += 1        
        
    def handle(self):
        global running;
        session = self.session
        session['cmd'] = 'exe'
        while running:                        
            try:
               
                msg = myRecv(self.request) 
                if not msg or msg[0] == None:                    
                    logging.warn('CLOSE BY PEER,so msg is empty!')
                    break      
#================================================================================  
                elif msg[0] == 'login':
                    data = self.handle_login(msg)
                    
                    mySend(self.request, data[0], self.server_key, data[1])
                    
                elif msg[0] == 'logout':
                    data = self.handle_logout(msg)
                    mySend(self.request, data[0], self.server_key, data[1])

#================================================================================            
                elif msg[0] == 'exe':             
                    code = msg[2]   
                    
                    print('\t<work name="EXE" >')
                    print '\t\t<code>\n%s\n\t\t</code>' % code
                    print '\t\t<result>'
                    try:
                        exec(code, locals())
                        data = (True, '')  
                    except Exception, e: 
                        traceback.print_exc()
                        data = (False, str(e))        
                    print '\t\t</result>'
                    print '\t</work>'
                                         
                    mySend(self.request, data[0], self.server_key, data[1])        
                                
                elif msg[0] == 'eval':    
                    code = msg[2]                     
                    try:
                        ret = eval(code, locals()) 
                        data = (True, ret)                             
                    except Exception, e:             
                        traceback.print_exc()
                        data = (False, str(e))                     
                    mySend(self.request, data[0], self.server_key, data[1])    
                    
                else:
                    data = self.handle_cmd(msg)  
                    if data != None:          
                        mySend(self.request, data[0], self.server_key, data[1])
                    
                        
            except IOError, e:               
                logging.info(str(e))
                break
            except Exception, e:                
                logging.error(str(e))
            	traceback.print_exc()
            	mySend(self.request, False, self.server_key, 'Internal Server Error: ' + str(e) + ',and message is ' + str(msg))

        self.request = None    
    


    def finish(self):        
        print 'RequestHandler Processed. \n'
        RequestHandler.connCounter -= 1
        

     

class Console(Thread):
    def __init__(self):
        Thread.__init__(self)
        
    def run(self):
        global tuple_space, running, server;       
        while(running):
            cmd = raw_input('>>')
            cmd = cmd.strip()
            if(cmd == 'help()'):
                print ['clear([table])', 'show([table])', 'eval(expr)']
            elif(cmd.startswith('clear(')):
                count = 0
                table=cmd[6:-1]                     
                if table:
                    tables=[table]
                else:
                    tables=tuple_space.space.keys()
                for key in tables:               
                    r,c = tuple_space.remove(key)   
                    count += 1                 
                    print 'clear table %s, %s tuples' %(key,str(c))               
            
            elif(cmd.startswith('show(')):
                table=cmd[5:-1]
                print "\n<TupleBase>" 
                count = 0
                if table:
                    tables=[table]
                else:
                    tables=tuple_space.space.keys()
                for key in tables:
                    info = tuple_space.space[key]
                    print '\t<key name="%s" >' % key
                    print str(info)                   
                    print '\t</key>'
                    count += 1                    
                print '</TupleBase>'

            elif cmd.startswith('eval('):
                try:
                    print eval(cmd[4:]); 
                except Exception, e:
                    print >> sys.stderr, e
                
            elif(cmd == 'quit()'):
                running = False       
                server.shutdown()
                tuple_space.close()                  
                print 'process exit.'                

                # sys.exit(0)
                break



def main():
    global server, _config, tuple_space;
    
    tuple_space = TupleBase(_config, config.Shelve)

    console = Console()
    print 'Server Console Started.\n'
    console.start(); 
    
    server_key = _config['server_key'];
    
    Addr = config.ServerConfig[server_key]['addr']
    server = ThreadingTCPServer(Addr, RequestHandler)
    print 'TupleSpaceServer Started On %s:%d\n' % Addr
    
    for n in xrange(0, int(_config['NCPU'])):
        map_reduce_thread = MapReduceThread(tuple_space)
        map_reduce_thread.start()

    server.serve_forever()
    


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        server_key = sys.argv[1]
        _config['server_key'] = server_key       
    else:
        print "%s serverkey ip port " % sys.argv[0] 
   
    main()
   
