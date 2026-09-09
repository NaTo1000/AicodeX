"""
Tests for AicodeX storage drivers with mirror cloud drives
"""

import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from drivers import (
    DriverError,
    DriverRegistry,
    LocalFileDriver,
    MirrorCloudDriveDriver,
)


@pytest.fixture
def storage(tmp_path):
    return tmp_path / "store"


def test_local_roundtrip(storage):
    """Local driver writes and reads a payload"""
    driver = LocalFileDriver(storage)
    driver.write("sections/window.dat", b"payload")
    assert driver.exists("sections/window.dat")
    assert driver.read("sections/window.dat") == b"payload"


def test_local_write_is_atomic(storage):
    """Local driver does not leave temp files behind after a write"""
    driver = LocalFileDriver(storage)
    driver.write("a.dat", b"x")
    assert os.listdir(storage) == ["a.dat"]


def test_local_read_missing_raises(storage):
    """Reading a missing key raises DriverError"""
    driver = LocalFileDriver(storage)
    with pytest.raises(DriverError):
        driver.read("missing.dat")


def test_local_key_escape_blocked(storage):
    """Keys cannot escape the storage root"""
    driver = LocalFileDriver(storage)
    with pytest.raises(DriverError):
        driver.write("../../etc/evil", b"x")


def test_local_list_keys(storage):
    """List keys returns relative paths filtered by prefix"""
    driver = LocalFileDriver(storage)
    driver.write("sections/a.dat", b"1")
    driver.write("sections/b.dat", b"2")
    driver.write("backups/a/x.dat", b"3")
    assert driver.list_keys("sections/") == ["sections/a.dat", "sections/b.dat"]
    assert len(driver.list_keys()) == 3


def test_local_delete(storage):
    """Delete removes a stored payload"""
    driver = LocalFileDriver(storage)
    driver.write("a.dat", b"x")
    driver.delete("a.dat")
    assert not driver.exists("a.dat")


def test_mirror_write_fans_out(tmp_path):
    """Mirror driver writes to every available mirror"""
    roots = [tmp_path / "cloud1", tmp_path / "cloud2"]
    roots[0].mkdir()
    roots[1].mkdir()
    driver = MirrorCloudDriveDriver(roots)
    driver.write("k.dat", b"data")
    assert (roots[0] / "k.dat").read_bytes() == b"data"
    assert (roots[1] / "k.dat").read_bytes() == b"data"


def test_mirror_write_tolerates_unavailable_mirror(tmp_path):
    """Write succeeds when one mirror is unavailable (not mounted)"""
    available = tmp_path / "cloud1"
    available.mkdir()
    unavailable = tmp_path / "not-mounted"
    driver = MirrorCloudDriveDriver([unavailable, available])
    driver.write("k.dat", b"data")
    assert (available / "k.dat").read_bytes() == b"data"


def test_mirror_write_all_unavailable_raises(tmp_path):
    """Write raises when every mirror is unavailable"""
    driver = MirrorCloudDriveDriver([tmp_path / "m1", tmp_path / "m2"])
    with pytest.raises(DriverError):
        driver.write("k.dat", b"data")


def test_mirror_read_rollover(tmp_path):
    """Read rolls over mirrors until one succeeds"""
    roots = [tmp_path / "cloud1", tmp_path / "cloud2"]
    for r in roots:
        r.mkdir()
    (roots[1] / "k.dat").write_bytes(b"from-second-mirror")
    driver = MirrorCloudDriveDriver(roots)
    assert driver.read("k.dat") == b"from-second-mirror"


def test_mirror_read_all_fail_raises(tmp_path):
    """Read raises when no mirror holds the key"""
    roots = [tmp_path / "cloud1", tmp_path / "cloud2"]
    for r in roots:
        r.mkdir()
    driver = MirrorCloudDriveDriver(roots)
    with pytest.raises(DriverError):
        driver.read("missing.dat")


def test_mirror_sync(tmp_path):
    """Sync re-mirrors payloads to every available mirror"""
    roots = [tmp_path / "cloud1", tmp_path / "cloud2"]
    roots[0].mkdir()
    (roots[0] / "k.dat").write_bytes(b"data")
    driver = MirrorCloudDriveDriver(roots)
    roots[1].mkdir()  # second mirror comes online later
    synced = driver.sync()
    assert synced == ["k.dat"]
    assert (roots[1] / "k.dat").read_bytes() == b"data"


def test_mirror_single_path_convenience(tmp_path):
    """A single path is accepted as a one-mirror list"""
    root = tmp_path / "cloud"
    root.mkdir()
    driver = MirrorCloudDriveDriver(root)
    driver.write("k.dat", b"data")
    assert driver.read("k.dat") == b"data"


def test_registry_rollover_read(tmp_path):
    """Registry read rolls over the driver chain"""
    d1 = LocalFileDriver(tmp_path / "s1")
    d2 = LocalFileDriver(tmp_path / "s2")
    d2.write("k.dat", b"from-d2")
    registry = DriverRegistry()
    registry.register("first", d1)
    registry.register("second", d2)
    assert registry.read("k.dat", ["first", "second"]) == b"from-d2"


def test_registry_write_fans_out(tmp_path):
    """Registry write stores the payload on every driver in the chain"""
    d1 = LocalFileDriver(tmp_path / "s1")
    d2 = LocalFileDriver(tmp_path / "s2")
    registry = DriverRegistry()
    registry.register("first", d1)
    registry.register("second", d2)
    registry.write("k.dat", b"data", ["first", "second"])
    assert d1.read("k.dat") == b"data"
    assert d2.read("k.dat") == b"data"


def test_registry_write_all_fail_raises(tmp_path):
    """Registry write raises when every driver fails"""
    registry = DriverRegistry()
    registry.register("none", MirrorCloudDriveDriver([tmp_path / "x"]))
    with pytest.raises(DriverError):
        registry.write("k.dat", b"data", ["none"])


def test_registry_unknown_driver():
    """Unknown driver alias raises DriverError"""
    registry = DriverRegistry()
    with pytest.raises(DriverError):
        registry.get("nope")


def test_registry_from_config(tmp_path):
    """Registry builds from a configuration spec"""
    registry = DriverRegistry.from_config({
        "local": {"type": "local", "path": str(tmp_path / "s")},
        "cloud": {"type": "mirror-cloud",
                  "paths": [str(tmp_path / "c1"), str(tmp_path / "c2")]},
    })
    assert registry.available() == ["cloud", "local"]
    with pytest.raises(DriverError):
        DriverRegistry.from_config({"bad": {"type": "unknown-type"}})
