import threading
import pandas as pd

_thread = threading.local()


def _log(src: str):
    """Register a data source path / identifier for the current thread."""
    if not hasattr(_thread, "sources"):
        _thread.sources = []
    _thread.sources.append(str(src))


def activate():
    """Monkey-patch common pandas readers once per process."""

    def wrap(reader):
        def inner(path, *args, **kw):
            _log(path)
            return reader(path, *args, **kw)

        return inner

    pd.read_csv = wrap(pd.read_csv)
    pd.read_excel = wrap(pd.read_excel)
    pd.read_parquet = wrap(pd.read_parquet)
    # add more wrappers if you use read_json, read_feather, …


def consumed() -> list[str]:
    """Return & clear the list of sources read in this thread."""
    paths = getattr(_thread, "sources", [])
    _thread.sources = []
    return paths
