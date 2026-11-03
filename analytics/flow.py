"""Bounded, tenant-scoped lab mutation-burst heuristic; never a rate limiter."""

import hmac
import json
from collections import deque
from datetime import timedelta
from threading import RLock


class FlowMonitor:
    def __init__(self, key, threshold=10, window_seconds=60, capacity=1000):
        if len(key) < 32 or not 1 <= threshold <= 100 or not 1 <= capacity <= 4096:
            raise ValueError("Invalid flow configuration")
        if not 1 <= window_seconds <= 60:
            raise ValueError("Invalid flow window")
        self._key = key
        self.threshold, self.capacity = threshold, capacity
        self.window = timedelta(seconds=window_seconds)
        self._buckets, self._events = {}, {}
        self._last = None
        self._lock = RLock()

    def purge(self, now):
        with self._lock:
            cutoff = now - self.window
            self._events = {
                key: value for key, value in self._events.items() if value[0] > cutoff
            }
            for key, bucket in list(self._buckets.items()):
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if not bucket:
                    del self._buckets[key]

    def observe(self, observation, tenant):
        now = observation.observed_at
        with self._lock:
            if self._last is not None and now < self._last:
                return "unavailable"
            self._last = now
            self.purge(now)
            if observation.event_id in self._events:
                return self._events[observation.event_id][1]
            if len(self._events) >= self.capacity * (self.threshold + 1):
                return "unavailable"
            namespace = json.dumps(
                [tenant, observation.actor_id, "order-status-update"]
            )
            token = hmac.new(
                self._key, b"flow-scope\0" + namespace.encode(), "sha256"
            ).hexdigest()
            if token not in self._buckets:
                if len(self._buckets) >= self.capacity:
                    return "unavailable"
                self._buckets[token] = deque(maxlen=self.threshold + 1)
            bucket = self._buckets[token]
            bucket.append(now)
            result = "burst" if len(bucket) > self.threshold else "quiet"
            self._events[observation.event_id] = (now, result)
            return result
