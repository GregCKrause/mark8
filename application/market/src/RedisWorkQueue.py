# Based on https://github.com/kubernetes/website/blob/main/content/en/examples/application/job/redis/rediswq.py
# Licensed under Creative Commons Attribution 4.0 International

# Standard library
import uuid
import hashlib

# Third party
import redis

class RedisWorkQueue(object):
    def __init__(self, name):
       self._db = redis.StrictRedis(host="redis")
       self._session = str(uuid.uuid4())
       self._main_q_key = name
       self._processing_q_key = name + ":processing"
       self._lease_key_prefix = name + ":leased_by_session:"


    def _main_qsize(self):
        return self._db.llen(self._main_q_key)


    def _processing_qsize(self):
        return self._db.llen(self._processing_q_key)


    def _itemkey(self, item):
        """Returns a string that uniquely identifies an item (bytes)."""
        return hashlib.sha224(item).hexdigest()


    def _lease_exists(self, item):
        return self._db.exists(self._lease_key_prefix + self._itemkey(item))


    def sessionID(self):
        return self._session


    def empty(self):
        return self._main_qsize() == 0 and self._processing_qsize() == 0


    def lease(self, lease_secs=60, block=True, timeout=None):
        if block:
            item = self._db.brpoplpush(
                self._main_q_key,
                self._processing_q_key,
                timeout=timeout
            )
        else:
            item = self._db.rpoplpush(
                self._main_q_key,
                self._processing_q_key
            )
        if item:
            itemkey = self._itemkey(item)
            self._db.setex(
                self._lease_key_prefix + itemkey,
                lease_secs,
                self._session
            )
        return item

    def complete(self, value):
        self._db.lrem(self._processing_q_key, 0, value)
        itemkey = self._itemkey(value)
        self._db.delete(self._lease_key_prefix + itemkey)
