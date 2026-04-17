from __future__ import annotations

import hashlib
import os
import shutil
from tempfile import mkstemp
from typing import TYPE_CHECKING

from anyio import Path

from litestar.concurrency import sync_to_thread

from .base import NamespacedStore, StorageObject

__all__ = ("FileStore",)


if TYPE_CHECKING:
    from datetime import timedelta
    from os import PathLike


def _safe_file_name(name: str) -> str:
    return hashlib.blake2s(name.encode()).hexdigest()


class FileStore(NamespacedStore):
    """File based, thread and process safe, asynchronous key/value store.

    .. note::

        To ensure arbitrary keys can safely be stored on any file system without
        potentially causing issues due to path separators or collisions, they are
        hashed with BLAKE2 before being interpreted as a file path. This means that the
        cache key becomes opaque inside the store, and a key does not translate to a
        file with that name on the file system.
    """

    __slots__ = {"create_directories": "flag to create directories in path", "path": "file path"}

    def __init__(self, path: PathLike[str], *, create_directories: bool = False) -> None:
        """Initialize ``FileStorage``.

        Args:
            path: Path to store data under
            create_directories: Create the directories in ``path`` if they don't exist
                Default: ``False``

                .. versionadded:: 2.9.0
        """
        self.path = Path(path)
        self.create_directories = create_directories

    async def __aenter__(self) -> None:
        if self.create_directories:
            await self.path.mkdir(exist_ok=True, parents=True)
        return

    def with_namespace(self, namespace: str) -> FileStore:
        """Return a new instance of :class:`FileStore`, using  a sub-path of the current store's path."""
        pass

    def _path_from_key(self, key: str) -> Path:
        return self.path / _safe_file_name(key)

    @staticmethod
    async def _load_from_path(path: Path) -> StorageObject | None:
        try:
            data = await path.read_bytes()
            return StorageObject.from_bytes(data)
        except FileNotFoundError:
            return None

    def _write_sync(self, target_file: Path, storage_obj: StorageObject) -> None:
        pass

    async def _write(self, target_file: Path, storage_obj: StorageObject) -> None:
        pass

    async def set(self, key: str, value: str | bytes, expires_in: int | timedelta | None = None) -> None:
        """Set a value.

        Args:
            key: Key to associate the value with
            value: Value to store
            expires_in: Time in seconds before the key is considered expired

        Returns:
            ``None``
        """
        pass

    async def get(self, key: str, renew_for: int | timedelta | None = None) -> bytes | None:
        """Get a value.

        Args:
            key: Key associated with the value
            renew_for: If given and the value had an initial expiry time set, renew the
                expiry time for ``renew_for`` seconds. If the value has not been set
                with an expiry time this is a no-op

        Returns:
            The value associated with ``key`` if it exists and is not expired, else
            ``None``
        """
        path = self._path_from_key(key)
        storage_obj = await self._load_from_path(path)

        if not storage_obj:
            return None

        if storage_obj.expired:
            await path.unlink(missing_ok=True)
            return None

        if renew_for and storage_obj.expires_at:
            await self.set(key, value=storage_obj.data, expires_in=renew_for)

        return storage_obj.data

    async def delete(self, key: str) -> None:
        """Delete a value.

        If no such key exists, this is a no-op.

        Args:
            key: Key of the value to delete
        """
        path = self._path_from_key(key)
        await path.unlink(missing_ok=True)

    async def delete_all(self) -> None:
        """Delete all stored values.

        Note:
            This deletes and recreates :attr:`FileStore.path`
        """
        pass

    async def delete_expired(self) -> None:
        """Delete expired items.

        Since expired items are normally only cleared on access (i.e. when calling
        :meth:`.get`), this method should be called in regular intervals
        to free disk space.
        """
        pass

    async def exists(self, key: str) -> bool:
        """Check if a given ``key`` exists."""
        path = self._path_from_key(key)
        return await path.exists()

    async def expires_in(self, key: str) -> int | None:
        """Get the time in seconds ``key`` expires in. If no such ``key`` exists or no
        expiry time was set, return ``None``.
        """
        pass
