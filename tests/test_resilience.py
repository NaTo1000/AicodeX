"""
Tests for AicodeX crash resilience: per-section codec/driver rollover,
mirror cloud drives, backup history and user restore
"""

import json
import os
import sys

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from resilience import ResilienceManager


@pytest.fixture
def spec(tmp_path):
    """A resilience spec with a local driver and two mirror cloud drives"""
    cloud1 = tmp_path / "cloud1"
    cloud2 = tmp_path / "cloud2"
    cloud1.mkdir()
    cloud2.mkdir()
    return {
        "enabled": True,
        "storage_dir": str(tmp_path / "local"),
        "backup_count": 3,
        "codecs": {"window": ["zlib", "base64", "utf-8"]},
        "drivers": {"window": ["local", "cloud"]},
        "driver_registry": {
            "local": {"type": "local", "path": str(tmp_path / "local")},
            "cloud": {"type": "mirror-cloud",
                      "paths": [str(cloud1), str(cloud2)]},
        },
        "defaults": {"codecs": ["utf-8", "base64"],
                     "drivers": ["local", "cloud"]},
    }


@pytest.fixture
def manager(spec):
    return ResilienceManager(spec)


def test_save_and_load_section(manager):
    """A section round-trips through the codec and driver chains"""
    data = {"width": 400, "height": 600}
    assert manager.save_section("window", data)
    assert manager.load_section("window") == data


def test_save_mirrors_to_cloud_drives(manager, spec, tmp_path):
    """Every save is mirrored to the local driver and both cloud drives"""
    manager.save_section("window", {"width": 1})
    for path in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        assert (path / "sections" / "window.dat").is_file()


def test_section_uses_configured_primary_codec(manager, tmp_path):
    """The window section is encoded with zlib (its primary codec)"""
    import zlib as _zlib
    manager.save_section("window", {"width": 1})
    payload = (tmp_path / "local" / "sections" / "window.dat").read_bytes()
    assert _zlib.decompress(payload) == json.dumps({"width": 1}, indent=2).encode("utf-8")


def test_default_section_uses_utf8(manager, tmp_path):
    """Sections without a configured chain use the utf-8 default"""
    manager.save_section("theme", {"background": "#000"})
    payload = (tmp_path / "local" / "sections" / "theme.dat").read_bytes()
    assert payload == json.dumps({"background": "#000"}, indent=2).encode("utf-8")


def test_load_rollover_when_local_copy_corrupt(manager, tmp_path):
    """A corrupted local payload rolls over to the cloud mirrors"""
    manager.save_section("window", {"width": 42})
    (tmp_path / "local" / "sections" / "window.dat").write_bytes(b"corrupt!")
    assert manager.load_section("window") == {"width": 42}


def test_load_rollover_when_a_mirror_corrupt(manager, tmp_path):
    """A corrupted first mirror rolls over to the second mirror"""
    manager.save_section("window", {"width": 7})
    (tmp_path / "local" / "sections" / "window.dat").unlink()
    (tmp_path / "cloud1" / "sections" / "window.dat").write_bytes(b"junk")
    assert manager.load_section("window") == {"width": 7}


def test_backup_history_rolls_over(manager):
    """Backups are kept for each save and pruned to backup_count"""
    for i in range(6):
        manager.save_section("window", {"width": i})
    stamps = manager.list_backups("window")
    assert len(stamps) == 3  # backup_count
    # Live payload is the newest save
    assert manager.load_section("window") == {"width": 5}


def test_user_restore_latest_backup(manager):
    """User restore rolls the live payload back to the latest backup"""
    manager.save_section("window", {"width": 1})
    manager.save_section("window", {"width": 2})
    manager.save_section("window", {"width": 3})
    assert manager.restore_section("window")
    # Latest backup holds the previous payload (width 2)
    assert manager.load_section("window") == {"width": 2}


def test_user_restore_specific_backup(manager):
    """User restore can pick a specific backup stamp"""
    manager.save_section("window", {"width": 1})
    manager.save_section("window", {"width": 2})
    manager.save_section("window", {"width": 3})
    stamps = manager.list_backups("window")
    assert manager.restore_section("window", backup_stamp=stamps[0])
    assert manager.load_section("window") == {"width": 1}


def test_restore_without_backups_fails(manager):
    """Restore fails cleanly when no backups exist"""
    assert not manager.restore_section("nonexistent")


def test_crash_detection(manager):
    """A run without a clean shutdown is detected as a crash"""
    assert not manager.crashed_last_run()  # never run before
    manager.mark_start()
    assert manager.crashed_last_run()  # started but not cleanly stopped
    manager.mark_clean_shutdown()
    assert not manager.crashed_last_run()


def test_recover_after_crash_restores_corrupt_sections(manager, tmp_path):
    """Crash recovery restores unreadable sections from the mirror drives"""
    manager.save_section("window", {"width": 1})
    manager.save_section("window", {"width": 2})
    manager.save_section("theme", {"accent": "#fff"})
    # Corrupt the live window payload on every drive
    for path in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        (path / "sections" / "window.dat").write_bytes(b"dead beef")
    report = manager.recover_after_crash()
    assert report == {"theme": "ok", "window": "restored"}
    assert manager.load_section("window") == {"width": 1}
    assert manager.load_section("theme") == {"accent": "#fff"}


def test_recover_after_crash_reports_unrecoverable(manager, spec):
    """Recovery reports known sections that have no payload or backup left"""
    manager.save_section("window", {"width": 1})
    # Remove all payloads and backups from every drive
    import shutil
    for path in (spec["driver_registry"]["local"]["path"],
                 *spec["driver_registry"]["cloud"]["paths"]):
        shutil.rmtree(path)
        os.makedirs(path)
    report = manager.recover_after_crash(sections=["window"])
    assert report == {"window": "failed"}


def test_recover_after_crash_discovers_sections_without_manifest(manager, tmp_path):
    """When the manifest is lost, sections are discovered from the drives"""
    manager.save_section("window", {"width": 1})
    manager.save_section("theme", {"accent": "#fff"})
    # Lose only the manifest on every drive
    for path in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        (path / "manifest.json").unlink()
    report = manager.recover_after_crash()
    assert report == {"theme": "ok", "window": "ok"}


def test_manifest_tracks_sections(manager):
    """Saved sections are tracked in the manifest"""
    manager.save_section("window", {})
    manager.save_section("theme", {})
    manager.save_section("window", {})
    assert manager._manifest_sections() == ["theme", "window"]


def test_load_missing_section_returns_none(manager):
    """Loading a section that was never saved returns None"""
    assert manager.load_section("ghost") is None


def test_corrupt_live_payload_never_enters_backup_history(manager, tmp_path):
    """A corrupt live payload is never archived into the backup history"""
    manager.save_section("window", {"width": 1})
    manager.save_section("window", {"width": 2})
    # Corrupt the live payload on every drive
    for path in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        (path / "sections" / "window.dat").write_bytes(b"dead beef")
    manager.save_section("window", {"width": 3})
    # Every backup in history must still decode to a real value
    for stamp in manager.list_backups("window"):
        assert manager.load_section("window", backup_stamp=stamp) is not None
    assert manager.load_section("window") == {"width": 3}


def test_restore_after_crash_recovery(manager, tmp_path):
    """User restore still works after crash recovery restored a section"""
    manager.save_section("window", {"width": 1})
    manager.save_section("window", {"width": 2})
    manager.save_section("window", {"width": 3})
    # Corrupt every live copy, then recover (restores from backup)
    for path in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        (path / "sections" / "window.dat").write_bytes(b"corrupt")
    report = manager.recover_after_crash()
    assert report == {"window": "restored"}
    assert manager.load_section("window") == {"width": 2}
    # User can still roll back further through the untouched history
    stamps = manager.list_backups("window")
    assert manager.restore_section("window", backup_stamp=stamps[0])
    assert manager.load_section("window") == {"width": 1}
