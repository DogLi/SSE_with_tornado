#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

class SseSender(object):
    def __init__(self, redis, channel="sse"):
        """
        redis 的发布
        channel: 要发布的频道
        """
        self.redis = redis
        self.channel = channel
        self.send_num = 0

    def send(self, data, event="message", id=""):
        """
        event: sse数据格式中的event
        data: 要发送的数据, 发送到 redis 中
        """
        data = {"event": event, "message": data, "id":id}
        send_num = self.redis.publish(self.channel, json.dumps(data))
        self.send_num = send_num

def test():
    """
    启动 server.py 后， 可以用该函数发送数据
    """
    import redis
    r = redis.Redis(host='localhost', port=6379)
    sender = SseSender(r)
    msg = {"a": 1}
    sender.send(msg, "ping")
    msg = ["a", 1]
    sender.send(msg, "ping")
    msg = 1
    sender.send(msg, "ping")
    msg = (1,"a")
    sender.send(msg, "ping")
    msg = "aaa"
    sender.send(msg, "ping")

if __name__ == "__main__":
    test()
