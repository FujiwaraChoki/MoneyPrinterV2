"""Project-wide pytest configuration.

On macOS, WeasyPrint requires GLib/Pango dylibs that Homebrew installs to
/opt/homebrew/lib.  macOS SIP strips DYLD_LIBRARY_PATH from child processes,
so we set it from inside Python before any test module (and thus weasyprint)
is imported.  cffi's dlopen() respects the updated os.environ value because
the loader looks up the environment at call time, not at process start.
"""
import os
import sys

if sys.platform == "darwin":
    homebrew_lib = "/opt/homebrew/lib"
    current = os.environ.get("DYLD_LIBRARY_PATH", "")
    if homebrew_lib not in current.split(":"):
        os.environ["DYLD_LIBRARY_PATH"] = (
            f"{homebrew_lib}:{current}" if current else homebrew_lib
        )
