"""Durable SQLite-backed store with the same contract as MemoryStore.

Issue #83 asks for audit retention and investigation storage that survives a
restart. This store is an opt-in candidate for that design, not a replacement
default: it persists only the masked summaries MemoryStore would hold, with
the same dedup, conflict, capacity and retention semantics, and the same
masking gate before anything is written. Analytics keeps using MemoryStore
unless a caller explicitly injects this store (e.g. AuditWriter(store=...)).
"""

import hashlib
import hmac
import json
import sqlite3
from datetime import datetime, timedelta
from threading import RLock

from analytics.masking import MaskingError, StorageMasker
from analytics.store import StoreError


class DurableStore:
    def __init__(self, key, db_path, capacity=1000, retention_seconds=300, routes=()):
        if not 1 <= capacity <= 10000 or not 1 <= retention_seconds <= 604800:
            raise ValueError("Invalid store bounds")
        self._key = key
        self.capacity = capacity
        self.retention = timedelta(seconds=retention_seconds)
        self._lock = RLock()
        self.masker = StorageMasker(routes)
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS store_rows ("
            " source TEXT NOT NULL,"
            " event_id TEXT NOT NULL,"
            " digest TEXT NOT NULL,"
            " summary TEXT NOT NULL,"
            " received_at TEXT NOT NULL,"
            " expires_at TEXT NOT NULL,"
            " PRIMARY KEY (source, event_id))"
        )
        self._db.commit()

    def close(self):
        with self._lock:
            self._db.close()

    def digest(self, value):
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(
            self._key, b"event-dedup\0" + canonical, hashlib.sha256
        ).hexdigest()

    def _purge(self, now):
        self._db.execute(
            "DELETE FROM store_rows WHERE expires_at <= ?", (now.isoformat(),)
        )

    def purge(self, now):
        with self._lock:
            self._purge(now)
            self._db.commit()

    def _count(self):
        return self._db.execute("SELECT COUNT(*) FROM store_rows").fetchone()[0]

    def _existing_digest(self, source, event_id):
        row = self._db.execute(
            "SELECT digest FROM store_rows WHERE source = ? AND event_id = ?",
            (source, event_id),
        ).fetchone()
        return row[0] if row else None

    def append(self, items, now):
        """Preflight under a lock; reject conflicts without a partial append."""
        with self._lock:
            try:
                self._purge(now)
                new = {}
                for source, event_id, digest, summary in items:
                    try:
                        summary = self.masker.project(summary)
                    except MaskingError:
                        raise StoreError("MASKING_REJECTED") from None
                    key = (source, str(event_id))
                    if key in new:
                        prior_digest = new[key]["digest"]
                    else:
                        prior_digest = self._existing_digest(*key)
                    if prior_digest is not None:
                        if prior_digest != digest:
                            raise StoreError("EVENT_ID_CONFLICT")
                        continue
                    new[key] = {
                        **summary,
                        "event_id": str(event_id),
                        "digest": digest,
                        "received_at": now,
                        "expires_at": now + self.retention,
                    }
                if self._count() + len(new) > self.capacity:
                    raise StoreError("STORE_CAPACITY")
                for (source, event_id), row in new.items():
                    meta = ("event_id", "digest", "received_at", "expires_at")
                    summary = {
                        name: value
                        for name, value in row.items()
                        if name not in meta
                    }
                    self._db.execute(
                        "INSERT INTO store_rows"
                        " (source, event_id, digest, summary, received_at, expires_at)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            source,
                            event_id,
                            row["digest"],
                            json.dumps(summary, sort_keys=True),
                            row["received_at"].isoformat(),
                            row["expires_at"].isoformat(),
                        ),
                    )
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def snapshot(self, now):
        # Internal test/investigation seam, deliberately not an HTTP read API.
        with self._lock:
            self._purge(now)
            self._db.commit()
            rows = self._db.execute(
                "SELECT event_id, digest, summary, received_at, expires_at"
                " FROM store_rows ORDER BY received_at, event_id"
            ).fetchall()
            result = []
            for event_id, digest, summary_json, received_at, expires_at in rows:
                expires = datetime.fromisoformat(expires_at)
                if expires <= now:
                    continue
                result.append(
                    {
                        **json.loads(summary_json),
                        "event_id": event_id,
                        "digest": digest,
                        "received_at": datetime.fromisoformat(received_at),
                        "expires_at": expires,
                    }
                )
            return result
