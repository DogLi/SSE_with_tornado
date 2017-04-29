#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""748783Demonstration of server-sent events with Tornado. To see the
stream, you can either point your browser to ``http://localhost:9000``
or use ``curl`` like so::
  $ curl http://localhost:9000/events

SSE 数据格式：
    先发送event（可选）： 'event: event_name' + u'\n'
    发送数据： u'data: encoded_data' + u'\n\n'
"""
import redis
import json
import time
import json
import socket,os
import logging
import uuid
import redis_util
from module import SSEModule
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
        console.log(e.id, e.data);
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

switch = True
CHANNEL = "sse"

class SSEHandler(web.RequestHandler):
    handlers = 0

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

    @property
    def cls(self):
        return self.__class__

    @property
    def is_alive(self):
        return not self.stream.closed()

    @gen.coroutine
    def get(self, *args, **kwargs):
        channels = self.get_argument("channels", "sse")
        channels = channels.split(",")
        sub_obj = SSEModule(redis_util.get_pool())
        sub_obj.set_handler(self)
        sub_obj.subscribe(*channels)
        self.sub_obj = sub_obj
        while self.is_alive:
            yield gen.sleep(1)
        del sub_obj

    def send_message(self, message):
        self.write(message)
        self.flush()


    def on_connection_close(self):
        self.sub_obj.unsubscribe()
        self.stream.close()

class MainHandler(web.RequestHandler):
    def get(self):
        self.write(html)

define("port", default=9000, help="run on the given port", type=int)

def run_server():
    options.parse_command_line()

    app = web.Application(
        [
            (r'/', MainHandler),
            (r'/events', SSEHandler)
        ],
        debug=True
    )
    server = HTTPServer(app)
    server.listen(options.port)
    IOLoop.instance().start()

if __name__ == "__main__":
    run_server()
