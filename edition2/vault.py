"""Optional local secrets vault for AicodeX Edition 2.

The vault stores small pieces of sensitive configuration (API keys, tokens,
endpoints) for the per-model job descriptions. It is deliberately simple and
local:

- A single JSON file, created with owner-only permissions (``0o600``).
- Values are stored as-is; the vault provides *storage and retrieval*, not
  encryption. Protect the file with filesystem permissions and OS user
  isolation, the same way ``~/.netrc`` or cloud CLIs' credential files work.

.. warning::

   The vault is **local-only**. Never commit it to version control, sync it to
   shared or cloud storage, or copy it onto machines you do not control. Use
   your CI/secret manager for shared or production secrets instead.
"""

from __future__ import annotations

import json
import os
import stat
import warnings
from pathlib import Path
from typing import Dict, Optional

LOCAL_ONLY_WARNING = (
    "The AicodeX Edition 2 secrets vault is local-only. Do NOT commit it to "
    "version control or sync it to shared/cloud storage."
)


class VaultError(Exception):
    """Raised for vault storage, permission, or lookup problems."""


class SecretsVault:
    """A minimal, local-only, permission-hardened secrets store.

    Parameters
    ----------
    path:
        Filesystem path of the vault JSON file. Parent directories are created
        on demand.
    """

    def __init__(self, path: os.PathLike | str) -> None:
        self.path = Path(path)

    # -- internal helpers -------------------------------------------------

    def _load(self) -> Dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise VaultError(f"Vault file is corrupt: {self.path}") from exc
        if not isinstance(data, dict):
            raise VaultError(f"Vault file must contain a JSON object: {self.path}")
        return data

    def _enforce_permissions(self) -> None:
        """Ensure the vault file is readable/writable only by its owner."""
        try:
            current = stat.S_IMODE(self.path.stat().st_mode)
        except OSError:
            return
        if current != 0o600:
            os.chmod(self.path, 0o600)

    def _warn_if_shared_location(self) -> None:
        """Warn when the vault lives somewhere that is likely synced/shared."""
        lowered = str(self.path).lower()
        shared_markers = ("dropbox", "onedrive", "google drive", "googledrive",
                          "icloud", "nextcloud", "/mnt/", "/media/")
        if any(marker in lowered for marker in shared_markers):
            warnings.warn(LOCAL_ONLY_WARNING, UserWarning, stacklevel=2)

    # -- public API --------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Store ``value`` under ``key``, creating the vault file if needed."""
        if not key:
            raise VaultError("Vault key must be a non-empty string")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = self._load()
        data[key] = value
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True),
                             encoding="utf-8")
        self._enforce_permissions()
        self._warn_if_shared_location()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return the stored value for ``key`` or ``default`` when missing."""
        return self._load().get(key, default)

    def delete(self, key: str) -> bool:
        """Remove ``key`` from the vault. Returns True when it existed."""
        data = self._load()
        if key not in data:
            return False
        del data[key]
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True),
                             encoding="utf-8")
        self._enforce_permissions()
        return True

    def keys(self) -> list:
        """List the stored keys (never the values)."""
        return sorted(self._load().keys())

    def resolve(self, reference: str) -> Optional[str]:
        """Resolve a ``$VAULT:key`` reference, or return ``reference`` unchanged.

        Configuration files reference secrets indirectly (``$VAULT:CLAUDE_API_KEY``)
        so that no secret value ever appears in version-controlled config. Any
        string that does not start with ``$VAULT:`` is returned as-is.
        """
        prefix = "$VAULT:"
        if isinstance(reference, str) and reference.startswith(prefix):
            return self.get(reference[len(prefix):])
        return reference
