
__version__ = "0.4"

import os
import sys
import urllib

import cgi
from cgi import *;
sys.path.append('../')

def test2(environ=os.environ):
    """Robust test CGI script, usable as main program.

    Write minimal HTTP headers and dump all information provided to
    the script in HTML form.

    """
    print "Content-type: text/html"
    print
    sys.stderr = sys.stdout    

    print "<H1>Second try with a small maxlen...</H1>"

    global maxlen
    maxlen = 50
    try:
        
        from lovely.jsonrpc import proxy
        client =  proxy.ServerProxy('http://127.0.0.1:8080/jsonrpc')
        print client.pow(5,6)

    except Exception,e:
        print_exception(Exception,e)



if __name__ == '__main__':
    test2()

