"""
Storage drivers for AicodeX
Provides pluggable storage drivers (local files and mirrored cloud
drives) with a full rollover fallback: writes fan out to every driver,
and reads roll over across drivers until one succeeds, so a failed or
unavailable drive never blocks a save or a load.
"""

import os
import shutil
import tempfile


class DriverError(Exception):
    """Raised when a storage driver fails to read or write a payload."""


class BaseDriver:
    """Base class for storage drivers."""

    name = "base"

    def write(self, key: str, payload: bytes) -> str:
        """Write payload under key, returning a driver-specific handle."""
        raise NotImplementedError

    def read(self, key: str) -> bytes:
        """Read the payload stored under key."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """Return True if a payload is stored under key."""
        raise NotImplementedError

    def delete(self, key: str):
        """Delete the payload stored under key, if present."""
        raise NotImplementedError

    def list_keys(self, prefix: str = ""):
        """List stored keys, optionally filtered by prefix."""
        raise NotImplementedError

    def read_leaves(self):
        """Return the individual readable locations behind this driver.

        Simple drivers return ``[self]``; mirror drivers return one entry
        per underlying mirror so callers can roll over each physical copy
        independently (e.g. when a mirror holds corrupted bytes that only
        fail at decode time).
        """
        return [self]


class LocalFileDriver(BaseDriver):
    """Stores payloads as files in a local directory.

    Writes are atomic: the payload is written to a temporary file in the
    same directory and then moved over the target, so a crash mid-write
    never leaves a half-written file behind.
    """

    name = "local"

    def __init__(self, root):
        """Initialize the driver rooted at the given directory."""
        self.root = os.path.abspath(root)

    def _path(self, key: str) -> str:
        """Resolve a key to a safe path inside the root directory."""
        rel = os.path.normpath(key).lstrip(os.sep)
        path = os.path.abspath(os.path.join(self.root, rel))
        if path != self.root and not path.startswith(self.root + os.sep):
            raise DriverError(f"key escapes storage root: {key}")
        return path

    def write(self, key: str, payload: bytes) -> str:
        path = self._path(key)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=os.path.dirname(path), prefix=".tmp-"
            )
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(bytes(payload))
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
            except BaseException:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except OSError as e:
            raise DriverError(f"local write failed for {key}: {e}") from e
        return path

    def read(self, key: str) -> bytes:
        path = self._path(key)
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError as e:
            raise DriverError(f"local read failed for {key}: {e}") from e

    def exists(self, key: str) -> bool:
        try:
            return os.path.isfile(self._path(key))
        except DriverError:
            return False

    def delete(self, key: str):
        try:
            path = self._path(key)
            if os.path.isfile(path):
                os.remove(path)
        except OSError as e:
            raise DriverError(f"local delete failed for {key}: {e}") from e

    def list_keys(self, prefix: str = ""):
        keys = []
        if not os.path.isdir(self.root):
            return keys
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for filename in filenames:
                if filename.startswith(".tmp-"):
                    continue
                full = os.path.join(dirpath, filename)
                keys.append(os.path.relpath(full, self.root))
        keys = [k.replace(os.sep, "/") for k in keys]
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return sorted(keys)


class MirrorCloudDriveDriver(BaseDriver):
    """Mirrors payloads across one or more cloud drive directories.

    A 'cloud drive' here is any mounted or synced cloud storage location
    (e.g. OneDrive, Dropbox, Google Drive, iCloud, network share) that
    appears as a directory. Writes are mirrored to every drive; reads roll
    over across the mirrors until one succeeds, so the failure of any
    single mirror (unmounted, offline, corrupted) is fully tolerated.
    """

    name = "mirror-cloud"

    def __init__(self, roots):
        """Initialize with a list of cloud drive root directories."""
        if isinstance(roots, (str, bytes, os.PathLike)):
            roots = [roots]
        self.mirrors = [LocalFileDriver(r) for r in roots]

    def available_mirrors(self):
        """Return the mirrors whose root directory currently exists."""
        return [m for m in self.mirrors if os.path.isdir(m.root)]

    def write(self, key: str, payload: bytes) -> str:
        mirrors = self.available_mirrors()
        if not mirrors:
            raise DriverError(
                f"no cloud drive mirrors available for write of {key}"
            )
        errors = []
        written = []
        for mirror in mirrors:
            try:
                written.append(mirror.write(key, payload))
            except DriverError as e:
                errors.append(str(e))
        if not written:
            raise DriverError(
                f"all cloud drive mirrors failed for {key}: "
                + "; ".join(errors)
            )
        return written[0]

    def read(self, key: str) -> bytes:
        errors = []
        for mirror in self.mirrors:
            try:
                return mirror.read(key)
            except DriverError as e:
                errors.append(str(e))
        raise DriverError(
            f"all cloud drive mirrors failed for {key}: " + "; ".join(errors)
        )

    def exists(self, key: str) -> bool:
        return any(m.exists(key) for m in self.mirrors)

    def delete(self, key: str):
        for mirror in self.mirrors:
            try:
                mirror.delete(key)
            except DriverError:
                continue

    def list_keys(self, prefix: str = ""):
        keys = set()
        for mirror in self.mirrors:
            keys.update(mirror.list_keys(prefix))
        return sorted(keys)

    def read_leaves(self):
        """One readable location per underlying mirror drive."""
        return list(self.mirrors)

    def sync(self, key: str = None, prefix: str = ""):
        """Re-mirror payloads so every available mirror holds a copy.

        If key is given only that payload is synced; otherwise every
        payload under prefix is synced. Returns the list of synced keys.
        """
        keys = [key] if key is not None else self.list_keys(prefix)
        synced = []
        for k in keys:
            try:
                payload = self.read(k)
            except DriverError:
                continue
            try:
                self.write(k, payload)
                synced.append(k)
            except DriverError:
                continue
        return synced


class DriverRegistry:
    """Registry of storage drivers with a full rollover fallback.

    Each section is assigned an ordered chain of driver names. Writes fan
    out to every driver in the chain so all mirrors stay up to date, and
    reads roll over across the chain until one driver succeeds. A failure
    in any single driver is tolerated as long as one driver works.
    """

    def __init__(self):
        """Initialize an empty driver registry."""
        self._drivers = {}

    def register(self, alias: str, driver: BaseDriver):
        """Register a driver instance under an alias."""
        self._drivers[alias] = driver

    def get(self, alias: str) -> BaseDriver:
        """Get a driver by alias, raising DriverError if unknown."""
        driver = self._drivers.get(alias)
        if driver is None:
            raise DriverError(f"unknown driver: {alias}")
        return driver

    def available(self):
        """Return the list of registered driver aliases."""
        return sorted(self._drivers.keys())

    def write(self, key: str, payload: bytes, chain) -> str:
        """Write to every driver in the chain, tolerating failures.

        Returns the handle from the first successful driver. Raises
        DriverError only if every driver in the chain fails.
        """
        if not chain:
            chain = list(self._drivers.keys())[:1]
        errors = []
        handle = None
        for alias in chain:
            try:
                result = self.get(alias).write(key, payload)
                if handle is None:
                    handle = result
            except DriverError as e:
                errors.append(str(e))
        if handle is None:
            raise DriverError(
                f"all drivers in rollover chain failed for {key}: "
                + "; ".join(errors)
            )
        return handle

    def read(self, key: str, chain) -> bytes:
        """Read with a full rollover fallback across the chain.

        Tries each driver in order and returns the first successful read.
        Raises DriverError only if every driver in the chain fails.
        """
        if not chain:
            chain = list(self._drivers.keys())[:1]
        errors = []
        for alias in chain:
            try:
                return self.get(alias).read(key)
            except DriverError as e:
                errors.append(str(e))
        raise DriverError(
            f"all drivers in rollover chain failed for {key}: "
            + "; ".join(errors)
        )

    @classmethod
    def from_config(cls, drivers_config):
        """Build a registry from configuration.

        drivers_config maps an alias to a driver spec, e.g.::

            {
              "local": {"type": "local", "path": ".aicodex"},
              "cloud": {"type": "mirror-cloud",
                        "paths": ["/mnt/OneDrive/AicodeX",
                                  "/mnt/Dropbox/AicodeX"]}
            }
        """
        registry = cls()
        for alias, spec in (drivers_config or {}).items():
            kind = spec.get("type", "local")
            if kind == "local":
                registry.register(alias, LocalFileDriver(spec.get("path", ".")))
            elif kind == "mirror-cloud":
                registry.register(
                    alias, MirrorCloudDriveDriver(spec.get("paths", []))
                )
            else:
                raise DriverError(f"unknown driver type: {kind}")
        return registry


def sync_directory(src_root, dst_root):
    """Copy the contents of src_root into dst_root (used for mirror sync)."""
    if not os.path.isdir(src_root):
        return
    os.makedirs(dst_root, exist_ok=True)
    for dirpath, _dirnames, filenames in os.walk(src_root):
        rel = os.path.relpath(dirpath, src_root)
        target_dir = os.path.join(dst_root, rel)
        os.makedirs(target_dir, exist_ok=True)
        for filename in filenames:
            if filename.startswith(".tmp-"):
                continue
            shutil.copy2(
                os.path.join(dirpath, filename),
                os.path.join(target_dir, filename),
            )
