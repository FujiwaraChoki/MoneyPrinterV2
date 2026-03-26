# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

#### Issue 1: Selenium Firefox Binary Import Error
**Error:** `ModuleNotFoundError: No module named 'selenium.webdriver.firefox.firefox_binary'`

**Root Cause:**
- The `selenium-firefox` package (v2.0.8) is an outdated third-party wrapper that hasn't been updated for Selenium 4.x
- It attempts to import `FirefoxBinary` from `selenium.webdriver.firefox.firefox_binary`, which was deprecated and removed in Selenium 4.0+
- The project was using Selenium 4.41.0, causing an incompatibility

**Why It Was Removed:**
- The `selenium-firefox` wrapper is unnecessary - Selenium 4.x includes native Firefox WebDriver support out of the box
- The package hasn't been maintained to keep up with Selenium's API changes
- All Firefox functionality needed by the project is available directly through the standard `selenium` package

**Changes Made:**
- Uninstalled `selenium-firefox` package from virtual environment
- Removed `selenium_firefox` from `requirements.txt`
- Removed unused `from selenium_firefox import *` imports from:
  - `src/classes/Twitter.py`
  - `src/classes/YouTube.py`
  - `src/classes/AFM.py`
- No functional code changes needed - the wildcard import wasn't being used

#### Issue 2: MoviePy Editor Module Not Found
**Error:** `ModuleNotFoundError: No module named 'moviepy.editor'`
**Follow-up Error:** `ModuleNotFoundError: No module named 'moviepy.video.fx.all'`
**Follow-up Error:** `ImportError: cannot import name 'change_settings' from 'moviepy.config'`

**Root Cause:**
- MoviePy underwent a major restructuring in version 2.x
- The `moviepy.editor` module was removed/reorganized
- Classes like `AudioFileClip`, `VideoFileClip`, `TextClip`, etc. are now imported directly from the `moviepy` package
- The `moviepy.video.fx.all` module path was also changed - effects are now in `moviepy.video.fx` directly
- Effect application syntax changed from function calls like `crop(clip, ...)` to using `.with_effects([Effect(...)])` method
- The `change_settings()` function was removed - configuration is now done via environment variables or `.env` files
- The project had MoviePy 2.1.2/2.2.1 installed but was using the old v1.x import and usage syntax

**Why It Was Changed:**
- MoviePy 2.x is the current maintained version with bug fixes and improvements
- The old `moviepy.editor` module structure no longer exists in v2.x
- Downgrading to MoviePy 1.x would mean missing out on updates and potential security fixes
- The new effect system in v2.x is more consistent and object-oriented
- Environment variable-based configuration is more standard and flexible

**Changes Made:**
- Updated `src/classes/YouTube.py` imports from:
  - `from moviepy.editor import *` (v1.x style)
  - `from moviepy.video.fx.all import crop` (v1.x style)
  - `from moviepy.config import change_settings` (v1.x style)
- To explicit imports from the new structure:
  - `from moviepy import AudioFileClip, ImageClip, TextClip, concatenate_videoclips, CompositeAudioClip, CompositeVideoClip, afx`
  - `from moviepy.video.fx import Crop` (v2.x style - note capitalization)
  - `from moviepy.video.tools.subtitles import SubtitlesClip`
- Updated effect application syntax:
  - Old: `clip = crop(clip, width=w, height=h, x_center=x, y_center=y)`
  - New: `clip = clip.with_effects([Crop(width=w, height=h, x_center=x, y_center=y)])`
- Updated ImageMagick configuration:
  - Old: `change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})`
  - New: `os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path` (environment variable approach)
- Replaced wildcard imports with explicit imports for better code clarity and compatibility

### Changed
- `requirements.txt` - Removed `selenium_firefox` package dependency
- `src/classes/Twitter.py` - Removed unused `selenium_firefox` wildcard import
- `src/classes/YouTube.py` - Updated MoviePy imports and effect usage for v2.x API compatibility, removed `selenium_firefox` import, updated `crop` function calls to use new `Crop` effect class with `.with_effects()` method, and replaced `change_settings()` with environment variable configuration for ImageMagick
- `src/classes/AFM.py` - Removed unused `selenium_firefox` wildcard import

### Result
Application now starts successfully with `python3 src/main.py` without any import errors.
