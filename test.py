#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json
import time

pool=redis.ConnectionPool(host='ubuntu',port=6379,db=0, password="cljslrl0620")
r = redis.StrictRedis(connection_pool=pool)
input = {"id": "aaa", "event": "ping", "message": {"a": time.time(), "b": 2}}

num = r.publish('test', json.dumps(input))
print num
# r.publish('test', input)
