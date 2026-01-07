"""AicodeX Python Package.

A companion overlay code engine with hotkey support and high customizability.
"""

__version__ = "0.1.0"
__author__ = "NaTo1000"


def get_version() -> str:
    """Return the current version of AicodeX."""
    return __version__


def greet(name: str = "World") -> str:
    """Return a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting string.
    """
    return f"Hello, {name} from AicodeX!"
