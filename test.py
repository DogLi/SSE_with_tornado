#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json
import time
import redis_util
from module import ModulePubSub


r=redis_util.redis_connect()
input = {"event": "ping", "message": {"a": time.time(), "b": 2}}

num = r.publish('test', json.dumps(input))
print num
# r.publish('test', input)
