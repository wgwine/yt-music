## YouTube to MP3 Converter

This repository now contains a Python script that downloads YouTube videos and converts them to MP3 format using ffmpeg.

### Files:
- `youtube_to_mp3.py` - Main converter script (updated with playlist support and Windows fixes)
- `requirements.txt` - Python dependencies
- `SETUP.md` - Detailed setup and usage instructions
- `sample_playlist.json` - Example playlist file format
- `diagnose_windows.py` - Windows diagnostic and troubleshooting tool

### Quick Start:
```bash
# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (system dependency)
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/

# Use the script - Single video
python youtube_to_mp3.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Use the script - YouTube playlist URL (NEW!)
python youtube_to_mp3.py "https://www.youtube.com/playlist?list=PLxxxxxx"

# Use the script - JSON playlist file  
python youtube_to_mp3.py sample_playlist.json

# With custom output directory
python youtube_to_mp3.py "https://youtube.com/playlist?list=PLxxxxxx" -o ./downloads
```

### Features:
- Downloads YouTube videos and converts to MP3
- Direct YouTube playlist URL support (no JSON needed!)
- Smart rate limit avoidance (extracts metadata first, only downloads missing)
- Skip existing MP3 files (prevents re-downloading completed files)
- Preserve video files when conversion fails (no data loss)
- High-quality audio extraction (192 kbps)
- Automatic dependency checking (with Windows user installation support)
- User-friendly error handling
- Support for custom output directories
- Windows PATH issue auto-detection and fallback

### Windows Users:
If you get "yt-dlp not found" errors on Windows:
```bash
# Test the fix
python test_windows_fix.py

# Run diagnostics
python diagnose_windows.py

# The script automatically tries both methods:
# 1. yt-dlp (command line)
# 2. python -m yt_dlp (module)
```

### Playlist Support:
**Easy way - Direct YouTube Playlist URLs (NEW!):**
```bash
python youtube_to_mp3.py "https://www.youtube.com/playlist?list=PLxxxxxx"
```

**Advanced way - Custom JSON files:**
Create a JSON file with your video list:
```json
[
  {
    "title": "Video Title",
    "videoUrl": "https://www.youtube.com/watch?v=VIDEO_ID",
    "videoId": "VIDEO_ID"
  }
]
```

See `sample_playlist.json` for a complete example. Then run:
```bash
python youtube_to_mp3.py your_playlist.json
```

See `SETUP.md` for detailed installation and usage instructions.


### Rate Limit Protection (NEW!)
This script now intelligently avoids YouTube's rate limiting that causes "Sign in to confirm you're not a bot" errors:

**How it works:**
1. **Metadata First**: Extracts playlist info with a single request (no downloads)
2. **Offline Comparison**: Compares video titles with existing MP3 files locally
3. **Selective Downloads**: Only downloads videos that don't already exist as MP3s

**Benefits:**
-  Handles large playlists without triggering bot detection
-  Resume interrupted downloads without re-processing completed files  
-  Dramatically reduces YouTube API requests
-  Works with playlists of any size (tested with 100+ videos)

**Example for 100-video playlist:**
- **Before**: 100 download attempts → rate limited after ~10-20 videos
- **After**: 1 metadata request + only missing videos → no rate limits

This makes the tool suitable for large music collections and batch processing!

---
