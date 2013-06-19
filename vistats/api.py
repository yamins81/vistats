import os
import json

import numpy as np

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


class App(tornado.web.Application):
    """
        Tornado app which serves the API.
    """
    def __init__(self):
        handlers = [(r"/vistats_blog", BlogHandler),
                    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "www/"}),
                   ]
        settings = dict(debug=True)
        tornado.web.Application.__init__(self, handlers, **settings)
        
        
HTML_TEMPLATE = """
<html>
<head>
<title>Vistats Chanel Blog!</title>
<link href='http://fonts.googleapis.com/css?family=Arimo:400,700' rel='stylesheet' type='text/css'>
<script type="text/javascript">
  WebFontConfig = {
    google: { families: [ 'Arimo:400,700:latin' ] }
  };
  (function() {
    var wf = document.createElement('script');
    wf.src = ('https:' == document.location.protocol ? 'https' : 'http') +
      '://ajax.googleapis.com/ajax/libs/webfont/1/webfont.js';
    wf.type = 'text/javascript';
    wf.async = 'true';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(wf, s);
  })(); </script>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

<link rel="stylesheet" href="http://thechrisellefactor.com/wp-content/themes/karappo-style/fonts.css" type="text/css" />
<link rel="stylesheet" href="http://thechrisellefactor.com/wp-content/themes/karappo-style/reset.css" type="text/css" />
<!-- <link rel="stylesheet" href="http://thechrisellefactor.com/wp-content/themes/karappo-style/style.css" type="text/css" media="screen" /> -->
<link rel="stylesheet" href="/static/style.css" type="text/css" media="screen" />
<script type="text/javascript" src="http://thechrisellefactor.com/wp-content/themes/karappo-style/js/jquery-1.3.2.min.js"></script>
<script type="text/javascript" src="http://thechrisellefactor.com/wp-content/themes/karappo-style/js/jquery.easing.1.3.js"></script>
<script type="text/javascript" src="http://thechrisellefactor.com/wp-content/themes/karappo-style/js/jquery.page-scroller-306.js"></script>
<script type="text/javascript" src="http://thechrisellefactor.com/wp-content/themes/karappo-style/js/bookmarker.js"></script>
</head>
<body>
<div id="container">
<div id="inner">
<div id="header">
<a href="/vistats_blog"><img src="/static/logo.png"></a>
Hi! Welcome to Vistats Chanel- and non-Chanel blog.   Here I'll be showing some of my favorite chanel related (and other images).
</div>
<div id="main">
%s
</div>
</div>
</div>
</body>
</html>
"""
        

IMG_ROOT = "http://ec2-50-19-109-25.compute-1.amazonaws.com:8081"

class BlogHandler(tornado.web.RequestHandler):
    def get(self):
        meta = tb.tabarray(SVfile=os.path.join(RESULTS_ROOT, 'meta_with_margin_test.tsv'))
        
        N = 2
        days = 6
        text = ''
        NP = 200
        NN = 200
        mdp = meta[:NP]
        mdp = mdp[np.random.RandomState(None).permutation(NP)]['filename']
        mdn = meta[-NN:]
        mdn = mdn[np.random.RandomState(None).permutation(NN)]['filename']

        for d in range(days):
            text += '<div class="entry" id="day_header_%d"><h2 class="entrytitle">Day %d</h2>' % (d, d)
            text += '<div class="date">posted by <a href="/vistats_blog">Vistats</a> on 2013.06.19</div>'
            ctext = "So, here are my Chanel pics of the day :)"
            text += '<p class="chanel_header" id="chanel_header_day_%d">%s</p><br/>' % (d, ctext)
            chaneltext = '<div class="img_div" id="chanel_img_div_day_%d">' % d + ''.join(['<div class="show_img" id="chanel_img_day_%d_img_%d"><img src="%s/%s"></div>' % (d, _i, IMG_ROOT,x.split('/')[-1]) for _i, x in enumerate(mdp[d*N:(d+1)*N])]) + '</div>'
            text += chaneltext
            notchaneltext = '<div class="img_div" id="not_chanel_img_div_day_%d">' % d + ''.join(['<div class="show_img" id="not_chanel_img_day_%d_img_%d"><img src="%s/%s"></div>' % (d, _i, IMG_ROOT, x.split('/')[-1]) for _i, x in enumerate(mdn[d*N:(d+1)*N])]) + '</div>'
            nctext = "Hey, and of course I also have a life <b>outside</b> of Chanel :)"
            text += '<p class="not_chanel_header" id="not_chanel_header_day_%d">%s</p><br/>' % (d, nctext) + notchaneltext
            text += '</div>'

        html = HTML_TEMPLATE % text
        
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
