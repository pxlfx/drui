import threading
import time
import typing as t


class Vault:
    """
    A key-value store with TTL (time-to-live) support and automatic cleanup.

    Example:
        >>> vault = Vault()
        >>> vault.set('key', 'value', 60)
        >>> vault.get('key')
    """

    def __init__(self, cleanup_interval: float = 60.0) -> None:
        """
        Initialize the Vault with optional cleanup interval (in seconds).

        :param cleanup_interval: (optional) how often to run cleanup of expired entries
        """
        self._store: t.Dict = {}
        self._expires_heap: list[tuple[float, str]] = []
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()

    def _remove_by_id(self, sid: str) -> bool:
        """
        Remove an entry from the main store by key.

        :param sid: key
        :return: True if the entry existed and was removed, False otherwise
        """
        return sid in self._store and self._store.pop(sid, None) is not None

    def _remove_from_heap(self, sid: str) -> None:
        """Remove all occurrences of a key from the expiry heap.

        :param sid: key
        """
        self._expires_heap = [
            (expires, id_) for expires, id_ in self._expires_heap if id_ != sid
        ]

    def _cleanup_worker(self) -> None:
        """
        Background worker that periodically calls cleanup() to remove expired entries.
        """
        stop_event = threading.Event()
        while not stop_event.wait(self._cleanup_interval):
            self.cleanup()

    def set(self, sid: str, value: t.Any, ttl: float) -> None:
        """
        Store a value with a TTL (time-to-live).

        :param sid: key
        :param value: the value to store
        :param ttl: time-to-live in seconds
        """
        timestamp = time.time()
        expires = timestamp + ttl

        with self._lock:
            self._remove_by_id(sid)
            self._store[sid] = {'value': value, 'expires': expires}
            self._expires_heap.append((expires, sid))
            self._expires_heap.sort()

    def get(self, sid: str, default: t.Optional[t.Any] = None) -> t.Any:
        """
        Return a value by key, checking if it has expired.

        :param sid: key
        :param default: (optional) default value to return if key doesn't exist or has expired
        :return: value or default
        """
        with self._lock:
            if sid not in self._store:
                return default

            item = self._store[sid]
            if time.time() > item['expires']:
                del self._store[sid]
                self._remove_from_heap(sid)
                return default

            return self._store.get(sid)

    def remove(self, sid: str) -> bool:
        """
        Explicitly remove an entry by key.

        :param sid: key
        :return: True if the entry existed and was removed, False otherwise
        """
        with self._lock:
            if self._remove_by_id(sid):
                self._remove_from_heap(sid)
                return True
            return False

    def cleanup(self) -> int:
        """
        Remove all expired entries from the store and heap.

        :return: number of entries that were cleaned up
        """
        current_time = time.time()
        deleted_count = 0

        with self._lock:
            expired_ids = []
            for sid, item in self._store.items():
                if current_time > item['expires']:
                    expired_ids.append(sid)

            for sid in expired_ids:
                del self._store[sid]
                self._remove_from_heap(sid)
                deleted_count += 1

        return deleted_count
