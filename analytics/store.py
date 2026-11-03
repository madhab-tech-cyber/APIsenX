"""Bounded, volatile masked summaries. No raw payload or disk persistence."""

import copy
import hashlib
import hmac
import json
from datetime import timedelta
from threading import RLock

from analytics.masking import MaskingError, StorageMasker


class StoreError(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


class MemoryStore:
    def __init__(self, key, capacity=1000, retention_seconds=300, routes=()):
        if not 1 <= capacity <= 10000 or not 1 <= retention_seconds <= 604800:
            raise ValueError("Invalid store bounds")
        self._key = key
        self.capacity = capacity
        self.retention = timedelta(seconds=retention_seconds)
        self._rows = {}
        self._lock = RLock()
        self.masker = StorageMasker(routes)

    def digest(self, value):
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(
            self._key, b"event-dedup\0" + canonical, hashlib.sha256
        ).hexdigest()

    def _purge(self, now):
        for key in [key for key, row in self._rows.items() if row["expires_at"] <= now]:
            del self._rows[key]

    def purge(self, now):
        with self._lock:
            self._purge(now)

    def append(self, items, now):
        """Preflight under a lock; reject conflicts without a partial append."""
        with self._lock:
            self._purge(now)
            new = {}
            for source, event_id, digest, summary in items:
                try:
                    summary = self.masker.project(summary)
                except MaskingError:
                    raise StoreError("MASKING_REJECTED") from None
                key = (source, str(event_id))
                prior = new.get(key) or self._rows.get(key)
                if prior is not None:
                    if prior["digest"] != digest:
                        raise StoreError("EVENT_ID_CONFLICT")
                    continue
                new[key] = {
                    **summary,
                    "event_id": str(event_id),
                    "digest": digest,
                    "received_at": now,
                    "expires_at": now + self.retention,
                }
            if len(self._rows) + len(new) > self.capacity:
                raise StoreError("STORE_CAPACITY")
            self._rows.update(new)

    def snapshot(self, now):
        # Internal test/investigation seam, deliberately not an HTTP read API.
        with self._lock:
            self._purge(now)
            return copy.deepcopy(list(self._rows.values()))
