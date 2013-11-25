#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2001 actzero, inc. All rights reserved.

from tspace import *;

def get_proxy_instance():
    proxy = TSpaceProxy(config.ServerConfig)
    proxy.login('junphine','erihrofgh')
    return proxy
    
proxy= get_proxy_instance()

def init():    
    print 'application started'
    for i in xrange(0,20):
         proxy.store('person',[i,i,12,(12, 3.14),'Zhang 俊峰',15]) 
    for i in xrange(0,20):
         proxy.take('person',[i,i,15,(12, 3.14),any,any])  
 
init()


import bottle
from bottle import get, post, request

# default configuration
_config = {
    'root_dir': None,
}

cfg = _config.copy()

app = bottle.Bottle()


    
@app.route('/report/<table>')
def report(table):      
    return table    


"""
  http://127.0.0.1:8080/rest/table/login/user/pwd
  http://127.0.0.1:8080/rest/table/find/12/%/df
"""    



@app.route('/rest/<table>/<path:path>', method='GET')
def do_GET(table,path):
    """Serve a GET request."""  
    try:       
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]          
        words = path.split('/')             
        print words
        cmd=words[0]       
        tups=words[1:]        
        #self.clientid=self.headers.getheaders('cookie')
        #print self.clientid
        #self.client='guest'       
        data=proxy.handle_cmd((cmd,table,tups))
        response=json.dumps(data,ensure_ascii=True,encoding=ENCODING) 
        return response
        
    except Exception,e:
        traceback.print_exc()
        abort(404, "Sorry, access denied."+str(e))        
        
    
@app.route('/rest/<table>/<path:path>', method='POST')
def do_POST(table,path):
    """Serve a POST request."""    
    try:
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]          
        words = path.split('/')             
        print words
        cmd=words[0]       
        tups=words[1:]        
       
        rdata=request.body
        print rdata
        tups=json.loads(rdata,encoding=ENCODING)
        print tups;
        data=proxy.handle_cmd((cmd,table,tups))
        response=json.dumps(data,ensure_ascii=True,encoding=ENCODING)       
        return (response)
       
    except Exception,e:
        traceback.print_exc()
        abort(404, "Sorry, access denied."+str(e))



def main(argv):
    if len(sys.argv) > 1:
        root_dir = os.path.abspath(sys.argv[1])
    else:
        root_dir = os.path.abspath('.')
    
    print 'jsonrpc serving in : ', root_dir    
    
    from lovely.jsonrpc import dispatcher;
    from lovely.jsonrpc import wsgi;
    
    rpc = dispatcher.JSONRPCDispatcher()
    rpc.register_method(pow,'pow')
    rpc.register_instance(proxy)
    
    jsonrpc = wsgi.WSGIJSONRPCApplication({'':rpc})
    
    jsonrpc.deploy('tspace',get_proxy_instance)
    
    app.mount('/jsonrpc', jsonrpc)
    bottle.run(app,server='auto')
    #bottle.run(app)

    
if __name__ == '__main__':
    import sys
    main(sys.argv)
    