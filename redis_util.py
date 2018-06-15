#!/usr/bin/env python
# -*- coding: utf-8 -*-
import redis as Redis


def get_pool(db=0):
    pool = Redis.ConnectionPool(
        host="localhost",
        port="6379",
        password=None,
        db=db)

    return pool


def redis_connect(db=0, pool=None):
    if not pool:
        pool = get_pool(db)
    return Redis.Redis(connection_pool=pool)
