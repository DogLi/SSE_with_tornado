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
        # result = {"id": id, "event": xxx, message: {"a":1, "b": 2}}
        message = self.get_message()
        data = message["data"]
        if isinstance(data, (int, long)):
            return
        data = json.loads(data)
        message = json.dumps(data["message"])
        event = data["event"]
        id_ = data["id"]

        sse = Sse()
        sse.set_event_id(id_)
        sse.add_message(event, message)
        sse_msg = "".join(sse)
        if not self.handler.is_alive:
            logging.info("stream closed, remove handler from ioloop")
            io_loop = IOLoop.current()
            io_loop.remove_handler(self.fd)
        else:
            logging.info("callback callback, now send message")
            self.handler.send_message(sse_msg)
