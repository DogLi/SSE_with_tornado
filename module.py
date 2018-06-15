#!/usr/bin/env python
# -*- coding: utf-8 -*-
import abc
import logging
import json
from sse import Sse
from tornado.ioloop import IOLoop
from redis.client import PubSub

class ModulePubSub(PubSub):
    """Module PubSub class"""
    def __init__(self,
                 connection_pool,
                 shard_hint=None,
                 ignore_subscribe_messages=False):
        self.fd = None
        super(ModulePubSub, self).__init__(connection_pool, shard_hint, ignore_subscribe_messages)

    def on_connect(self, connection):

        super(ModulePubSub, self).on_connect(connection)
        self.fd = connection._sock
        io_loop = IOLoop.current()
        io_loop.add_handler(connection._sock, self.loop_callback, IOLoop.READ)
        logging.info("add ioloop socket fileno: %s", self.fd.fileno())

    def loop_callback(self, fd, events):
        """Deail with subscribe messages"""
        self.callback()

    @abc.abstractmethod
    def callback(self):
        pass


class SSEModule(ModulePubSub):

    def set_handler(self, handler):
        """
        set the sse request handler
        """
        self.handler = handler

    def callback(self):
        """
        从 redis 中获取数据, 格式为：
        {"id": id, "event": xxx, message: {"a":1, "b": 2}}
        将数据转换为 sse 数据格式:
        * data:  数据内容用data字段表示, 如果数据很长，可以分成多行，最后一行用\n\n结尾，前面行都用\n结尾
          sse 模块中使用 add_message/flush 来设置/清空
        * id: 数据标识符用id字段表示，相当于每一条数据的编号。浏览器用 `lastEventId`属性读取这个值。
          一旦连接断线，浏览器会发送一个 HTTP 头，里面包含一个特殊的Last-Event-ID头信息，将这个值发送回来，
          用来帮助服务器端重建连接。因此，这个头信息可以被视为一种同步机制。
          sse 模块中 set_event_id / reset_event_id 来设置/清空
        * event: event 字段表示自定义的事件类型，默认是message事件。浏览器可以用addEventListener()监听该事件,
          sse 模块中用 set_event_id / set_event_id 来设置/清空
        * retry: 服务器可以用retry字段，指定浏览器重新发起连接的时间间隔。
           sse 模块中使用 `set_retry`设置，默认2000
        """
        message = self.get_message()
        data = message["data"]
        if isinstance(data, int):
            return
        data = json.loads(data)
        message = json.dumps(data["message"])
        event = data.get("event")
        id_ = data.get("id")

        sse = Sse()
        if id_:
            sse.set_event_id(id_)
        sse.add_message(event, message)
        sse_msg = str(sse)
        if not self.handler.is_alive:
            logging.info("stream closed, remove handler from ioloop")
            io_loop = IOLoop.current()
            io_loop.remove_handler(self.fd)
        else:
            logging.info("callback callback, now send message")
            self.handler.send_message(sse_msg)
