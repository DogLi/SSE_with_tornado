#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Demonstration of server-sent events with Tornado. To see the
stream, you can either point your browser to ``http://localhost:9000``
or use ``curl`` like so::

$ curl http://localhost:9000/events

SSE 对于 websocke 而言，支持自定义 event，SSE 默认有`open`/`message`/`error`三个
事件。默认情况下，服务器发来的数据，总是触发浏览器EventSource实例的message事件。
开发者还可以自定义 SSE 事件，这种情况下，发送回来的数据不会触发message事件。
比如下面 html 中的`ping` event.

"""

import time
import socket,os
import redis_util
from module import SSEModule
from abc import ABCMeta, abstractmethod, abstractproperty
from tornado.options import options, define
from tornado import web, gen
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

html = """
<div id="messages"></div>
<script type="text/javascript">
    if(EventSource == "undefined") {
        alert("sse not support!");
    }
    var sse = new EventSource('/events?channels=sse,test');
    sse.addEventListener('ping', function(e) {
        var div = document.getElementById("messages");
        div.innerHTML = e.data + "<br>" + div.innerHTML;
    }, false);

    //  default event type is "message"
    sse.onmessage = function(e) {
        // console.log(e.id, e.data);
        var div = document.getElementById("messages");
        console.log("xxxxxxxxxxxxxxxx")
        console.log(e.id, e.data);

      if (event.id == 'CLOSE') {
        sse.close();
      }
    };

    // on open
    sse.onopen = function () {
      console.log("sse open!")
    };

    sse.onerror = function () {
      console.log("sse closed!")
    };

</script>"""


class SSEHandler(web.RequestHandler):
    """
    usage: just inherite the class and define the redis_pool method with `@property`
    example:
        ```
        class TestHandler(SSEHandler):
            @property
            def redis_pool(self):
                return redis_util.get_pool()
        ```
    """
    __metaclass__ = ABCMeta
    CHANNEL = "sse"

    def __init__(self, application, request, **kwargs):
        super(SSEHandler, self).__init__(application, request, **kwargs)
        self.sub_obj = None
        self.stream = request.connection.stream


    def prepare(self):
        SSE_HEADERS = (
            ('Content-Type','text/event-stream; charset=utf-8'),
            ('Cache-Control','no-cache'),
            ('Connection','keep-alive'),
            ('Access-Control-Allow-Origin', '*'),
        )
        for name, value in SSE_HEADERS:
            self.set_header(name, value)

    @abstractproperty
    def redis_pool(self):
        """
        this property will be supplied by the inheriting classes individually
        """
        pass

    @property
    def is_alive(self):
        return not self.stream.closed()

    @gen.coroutine
    def get(self, *args, **kwargs):
        """
        channels: 订阅 redis channel 中的数据
        """
        channels = self.get_argument("channels", "sse")
        channels = channels.split(",")
        sub_obj = SSEModule(self.redis_pool)
        sub_obj.set_handler(self)
        sub_obj.subscribe(*channels)
        self.sub_obj = sub_obj
        while self.is_alive:
            yield gen.sleep(1000)
        del sub_obj

    def send_message(self, message):
        self.write(message)
        self.flush()


    def on_connection_close(self):
        # unsubscribe when close the connection
        self.sub_obj.unsubscribe()
        self.stream.close()

class THandler(SSEHandler):
    @property
    def redis_pool(self):
        return redis_util.get_pool()

class MainHandler(web.RequestHandler):
    def get(self):
        self.write(html)

define("port", default=9000, help="run on the given port", type=int)

def run_server():
    options.parse_command_line()

    app = web.Application(
        [
            (r'/', MainHandler),
            (r'/events', THandler)
        ],
        debug=True
    )
    server = HTTPServer(app)
    server.listen(options.port)
    IOLoop.instance().start()

if __name__ == "__main__":
    run_server()
