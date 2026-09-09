"""
Crash resilience for AicodeX
Ties the codec rollover chains and the mirrored storage drivers together
into a per-section recovery manager: every section is encoded with its
codec chain and mirrored across the driver chain, keeps a rolling history
of backups, and can roll back (restore) any section after a system crash
or at the user's request.
"""

import json
import os
import time

from aicodex_codecs import CodecRegistry, CodecError
from drivers import DriverRegistry, DriverError


class ResilienceError(Exception):
    """Raised when the resilience layer cannot complete an operation."""


class ResilienceManager:
    """Per-section crash recovery with codec and driver rollover.

    Configuration spec example::

        {
          "enabled": true,
          "storage_dir": ".aicodex",
          "backup_count": 5,
          "codecs": {"window": ["zlib", "base64", "utf-8"]},
          "drivers": {"window": ["local", "cloud"]},
          "defaults": {"codecs": ["utf-8", "base64"],
                       "drivers": ["local", "cloud"]}
        }

    Saves are atomic and mirrored: the payload is encoded with the
    section's primary codec and written through every driver in the
    section's chain. Loads roll over: each driver is tried in order and
    each payload is decoded through the section's full codec chain, so
    corrupted or moved data falls back to the mirror cloud drives.
    """

    CLEAN_SHUTDOWN_FILE = "clean_shutdown.marker"
    MANIFEST_KEY = "manifest.json"

    def __init__(self, spec=None, codec_registry=None, driver_registry=None):
        """Initialize the resilience manager from a configuration spec."""
        spec = spec or {}
        self.enabled = bool(spec.get("enabled", False))
        self.backup_count = int(spec.get("backup_count", 5))
        self.defaults = spec.get("defaults", {}) or {}
        self.section_codecs = spec.get("codecs", {}) or {}
        self.section_drivers = spec.get("drivers", {}) or {}

        storage_dir = spec.get("storage_dir", ".aicodex")
        if driver_registry is None:
            drivers_config = dict(spec.get("driver_registry", {}) or {})
            if "local" not in drivers_config:
                drivers_config["local"] = {"type": "local", "path": storage_dir}
            driver_registry = DriverRegistry.from_config(drivers_config)
        self.drivers = driver_registry
        self.codecs = codec_registry or CodecRegistry()

    # ------------------------------------------------------------------
    # Chain resolution
    # ------------------------------------------------------------------
    def codec_chain(self, section: str):
        """Codec rollover chain for a section (defaults to utf-8)."""
        return self.section_codecs.get(
            section, self.defaults.get("codecs", ["utf-8"])
        )

    def driver_chain(self, section: str):
        """Driver rollover chain for a section (defaults to first driver)."""
        return self.section_drivers.get(
            section,
            self.defaults.get("drivers", self.drivers.available()[:1]),
        )

    # ------------------------------------------------------------------
    # Save / load with rollover
    # ------------------------------------------------------------------
    def _data_key(self, section: str) -> str:
        return f"sections/{section}.dat"

    def _backup_key(self, section: str, stamp: str) -> str:
        return f"backups/{section}/{stamp}.dat"

    def save_section(self, section: str, data, backup_current: bool = True) -> bool:
        """Encode and mirror a section, keeping a rolling backup history.

        Returns True on success. The previous payload is first copied into
        the section's backup history (rolling over older backups beyond
        backup_count), then the new payload is written to every driver in
        the section's chain. Pass backup_current=False when writing a
        restored payload so a corrupt live copy is never pushed into the
        backup history.
        """
        try:
            raw = json.dumps(data, indent=2).encode("utf-8")
            encoded = self.codecs.encode(raw, self.codec_chain(section))
            data_key = self._data_key(section)

            # Roll the current payload into the backup history first.
            if backup_current:
                try:
                    previous = self.drivers.read(
                        data_key, self.driver_chain(section)
                    )
                    # Never archive a payload that does not decode back to
                    # valid section data (JSON) through the codec chain.
                    json.loads(
                        self.codecs.decode(
                            previous, self.codec_chain(section)
                        ).decode("utf-8")
                    )
                    stamp = (
                        time.strftime("%Y%m%d%H%M%S")
                        + f"-{time.time_ns() % 10**9:09d}"
                    )
                    self.drivers.write(
                        self._backup_key(section, stamp),
                        previous,
                        self.driver_chain(section),
                    )
                    self._prune_backups(section)
                except (DriverError, CodecError, ValueError):
                    pass  # no readable previous payload to back up

            self.drivers.write(data_key, encoded, self.driver_chain(section))
            self._update_manifest(section)
            return True
        except (CodecError, DriverError, TypeError, ValueError) as e:
            print(f"Resilience: failed to save section '{section}': {e}")
            return False

    def load_section(self, section: str, backup_stamp: str = None):
        """Load a section with full codec and driver rollover fallback.

        With backup_stamp given, that specific backup is loaded instead of
        the live payload (user restore). Each driver in the chain is tried
        in order, and each payload is decoded through the section's full
        codec chain; an unreadable payload (corrupt copy) falls through to
        the next driver mirror. Returns the decoded section data, or None
        if every driver/codec combination in the rollover chain failed.
        """
        key = (
            self._backup_key(section, backup_stamp)
            if backup_stamp
            else self._data_key(section)
        )
        errors = []
        for leaf in self._read_leaves(section):
            try:
                payload = leaf.read(key)
            except DriverError as e:
                errors.append(str(e))
                continue
            try:
                raw = self.codecs.decode(payload, self.codec_chain(section))
                return json.loads(raw.decode("utf-8"))
            except (CodecError, ValueError) as e:
                errors.append(str(e))
        print(
            f"Resilience: failed to load section '{section}': "
            + "; ".join(errors)
        )
        return None

    def _read_leaves(self, section: str):
        """Every individual readable location in the section's chain.

        Mirror drivers are expanded to their underlying drives so a
        corrupted copy on one mirror rolls over to the next physical copy.
        """
        leaves = []
        for alias in self.driver_chain(section):
            try:
                leaves.extend(self.drivers.get(alias).read_leaves())
            except DriverError:
                continue
        return leaves

    # ------------------------------------------------------------------
    # Backup history & user restore
    # ------------------------------------------------------------------
    def list_backups(self, section: str):
        """List available backup stamps for a section, newest last."""
        keys = set()
        for alias in self.driver_chain(section):
            try:
                driver = self.drivers.get(alias)
                keys.update(driver.list_keys(f"backups/{section}/"))
            except DriverError:
                continue
        stamps = sorted(
            os.path.basename(k)[:-len(".dat")]
            for k in keys
            if k.endswith(".dat")
        )
        return stamps

    def _prune_backups(self, section: str):
        """Roll over the backup history, keeping the newest backup_count."""
        stamps = self.list_backups(section)
        excess = len(stamps) - self.backup_count
        if excess <= 0:
            return
        for stamp in stamps[:excess]:
            key = self._backup_key(section, stamp)
            for alias in self.driver_chain(section):
                try:
                    self.drivers.get(alias).delete(key)
                except DriverError:
                    continue

    def restore_section(self, section: str, backup_stamp: str = None) -> bool:
        """Restore a section from a backup (user restore).

        Without backup_stamp, the most recent backup is used. The restored
        payload becomes the live payload on every driver mirror. Returns
        True on success.
        """
        stamp = backup_stamp
        if stamp is None:
            stamps = self.list_backups(section)
            if not stamps:
                print(f"Resilience: no backups available for '{section}'")
                return False
            stamp = stamps[-1]
        data = self.load_section(section, backup_stamp=stamp)
        if data is None:
            return False
        # Don't archive the payload being replaced: it may be the corrupt
        # copy that triggered this restore in the first place.
        return self.save_section(section, data, backup_current=False)

    # ------------------------------------------------------------------
    # Crash detection & recovery
    # ------------------------------------------------------------------
    def mark_start(self):
        """Mark the application as running (clears the clean-shutdown flag)."""
        try:
            self.drivers.write(
                self.CLEAN_SHUTDOWN_FILE, b"running", self._marker_chain()
            )
        except DriverError as e:
            print(f"Resilience: failed to write start marker: {e}")

    def mark_clean_shutdown(self):
        """Mark the application as cleanly shut down."""
        try:
            self.drivers.write(
                self.CLEAN_SHUTDOWN_FILE, b"clean", self._marker_chain()
            )
        except DriverError as e:
            print(f"Resilience: failed to write shutdown marker: {e}")

    def _marker_chain(self):
        return self.defaults.get("drivers", self.drivers.available()[:1])

    def crashed_last_run(self) -> bool:
        """Return True if the previous run did not shut down cleanly.

        A missing marker means the app has never run, which is not a
        crash; an existing marker that does not read 'clean' means the
        previous run ended without a clean shutdown (system crash).
        """
        try:
            payload = self.drivers.read(
                self.CLEAN_SHUTDOWN_FILE, self._marker_chain()
            )
        except DriverError:
            return False
        return payload.strip() != b"clean"

    def recover_after_crash(self, sections=None):
        """Recover sections after a detected crash.

        For each section, the live payload is validated through the full
        codec/driver rollover chain; if it is unreadable, the latest
        backup is restored from the mirror cloud drives. Sections are
        taken from the manifest, falling back to sections discovered on
        the drivers when the manifest itself was lost. Returns a dict of
        section -> 'ok' | 'restored' | 'failed'.
        """
        if sections is None:
            sections = self._manifest_sections() or self._discover_sections()
        report = {}
        for section in sections:
            data = self.load_section(section)
            if data is not None:
                report[section] = "ok"
            elif self.restore_section(section):
                report[section] = "restored"
            else:
                report[section] = "failed"
        return report

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------
    def _update_manifest(self, section: str):
        chain = self._marker_chain()
        try:
            manifest = json.loads(
                self.drivers.read(self.MANIFEST_KEY, chain).decode("utf-8")
            )
        except (DriverError, ValueError):
            manifest = {"sections": []}
        if section not in manifest["sections"]:
            manifest["sections"].append(section)
            manifest["sections"].sort()
        try:
            self.drivers.write(
                self.MANIFEST_KEY,
                json.dumps(manifest, indent=2).encode("utf-8"),
                chain,
            )
        except DriverError as e:
            print(f"Resilience: failed to update manifest: {e}")

    def _manifest_sections(self):
        try:
            manifest = json.loads(
                self.drivers.read(
                    self.MANIFEST_KEY, self._marker_chain()
                ).decode("utf-8")
            )
            return list(manifest.get("sections", []))
        except (DriverError, ValueError):
            return []

    def _discover_sections(self):
        """Discover sections from payloads/backups present on any driver."""
        sections = set()
        for alias in self.drivers.available():
            try:
                driver = self.drivers.get(alias)
            except DriverError:
                continue
            for key in driver.list_keys("sections/"):
                name = os.path.basename(key)
                if name.endswith(".dat"):
                    sections.add(name[:-len(".dat")])
            for key in driver.list_keys("backups/"):
                parts = key.split("/")
                if len(parts) >= 2 and parts[1]:
                    sections.add(parts[1])
        return sorted(sections)
