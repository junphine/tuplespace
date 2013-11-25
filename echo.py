
import sys
reload(sys)

sys.path.append('../lib')
sys.path.append('lib')

ENCODING='utf-8'
sys.setdefaultencoding(ENCODING)

def app(environ, start_response):
    body='echo'
    cl = environ.get('CONTENT_LENGTH', None)
    if cl is not None:
        cl = int(cl)
    
        if cl>0:
            body = environ['wsgi.input'].read(cl)
    env=str(environ)
    environ['sess']=1
    body+=env
    cl = str(len(body))
    start_response(
        '200 OK',
        [('Content-Length', cl), ('Content-Type', 'text/plain')]
        )
    return [body]

if __name__ == '__main__':
    import logging
    class NullHandler(logging.Handler):
        def emit(self, record):
            if record:
                print record
    h = NullHandler()
    logging.getLogger('waitress').addHandler(h)
    from waitress import serve
    serve(app, port=8080, _quiet=True)
    
    
