#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from sseclient import SSEClient

# messages = SSEClient('http://localhost/event')
# for msg in messages:
    # print msg
import json
import pprint
import sseclient


def with_requests(url):
    """Get a streaming response for the given event feed using requests."""
    import requests
    return requests.get(url, stream=True)

url = 'http://localhost:9000/events'
response = with_requests(url)  # or with_requests(url)
client = sseclient.SSEClient(response)
for event in client.events():
    pprint.pprint(json.loads(event.data))
