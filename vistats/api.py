import os
import json

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.autoreload
from tornado.options import define, options

import tabular as tb

define("port", default=30312, help="run on the given port", type=int)

RESULTS_ROOT = '/home/render/vistats/vistats/results'
'

class App(tornado.web.Application):
    """
        Tornado app which serves the API.
    """
    def __init__(self):
        handlers = [(r"/vistats_blog", BlogHandler)
                   ]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)
        
        
HTML_TEMPLATE = """
<html>
<head>
Hello.
</head>
<body>
<div> Chanel: %s </div>
</div> Not Chanel %s </div>
</body>
</html>
"""
        
class BlogHandler(tornado.web.RequestHandler):
    def get(self):
        meta = tb.tabarray(SVfile=os.path.join(RESULTS_ROOT, 'meta_with_margin_test.tsv'))
        
        N = 5
        chaneltext = ''.join(['<img src="http://ec2-23-20-203-208.compute-1.amazonaws.com:8081/%s">' % x for x in meta[:N]['filename']])
        notchaneltext = ''.join(['<img src="http://ec2-23-20-203-208.compute-1.amazonaws.com:8081/%s">' % x for x in meta[-N:]['filename']])
        
        html = HTML_TEMPLATE % (chaneltext, notchaneltext)
        
        self.write(html)

        self.finish()


def main():    
    """
        function which starts up the tornado IO loop and the app. 
    """
    tornado.options.parse_command_line()
    ioloop = tornado.ioloop.IOLoop.instance()
    http_server = tornado.httpserver.HTTPServer(App())
    http_server.listen(options.port)
    tornado.autoreload.start()
    ioloop.start()
    

if __name__ == "__main__":
    main()
