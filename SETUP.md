# YouTube to MP3 Converter Setup Guide

This guide will help you set up and use the YouTube to MP3 converter script.

## Prerequisites

### 1. Python 3.6 or higher
Make sure you have Python installed:
```bash
python3 --version
# or
python --version
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
# or
pip install yt-dlp
```

### 3. Install FFmpeg
FFmpeg is required for audio conversion and must be installed separately:

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### On macOS with Homebrew:
```bash
brew install ffmpeg
```

#### On Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH
4. Restart your command prompt

#### Verify FFmpeg installation:
```bash
ffmpeg -version
```

## Usage

### Basic Usage
```bash
python youtube_to_mp3.py <youtube_url>
```

### Examples
```bash
# Download and convert a single video
python youtube_to_mp3.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Specify output directory
python youtube_to_mp3.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o ./downloads

# Get help
python youtube_to_mp3.py --help
```

## Features

- Downloads YouTube videos and converts them to MP3 format
- High-quality audio extraction (192 kbps)
- Automatic dependency checking
- Support for custom output directories
- Preserves original video title as filename
- Error handling and user-friendly messages

## Supported URLs

The script supports various YouTube URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- URLs with additional parameters

## Output

- MP3 files are saved with the original video title as the filename
- Audio quality is set to 192 kbps for good balance of quality and file size
- Files are saved in the current directory by default, or a specified output directory

## Troubleshooting

### Common Issues

1. **"yt-dlp not found" error (especially on Windows)**
   - Install yt-dlp: `pip install yt-dlp`
   - If still not working, try: `python -m pip install --user yt-dlp`
   - The script has been updated to handle Windows user installations automatically
   - Run `python diagnose_windows.py` for detailed diagnostics

2. **Windows-specific yt-dlp issues**
   - If yt-dlp is installed but not found, the script will automatically try `python -m yt_dlp`
   - Make sure Python Scripts directory is in your PATH, or restart your command prompt
   - Use `python test_windows_fix.py` to test the fix

3. **"ffmpeg not found" error**
   - Install FFmpeg following the instructions above
   - Make sure FFmpeg is in your system PATH
   - On Windows, restart command prompt after adding FFmpeg to PATH

4. **Permission errors**
   - Make sure you have write permissions in the output directory
   - On Unix systems, you might need to make the script executable: `chmod +x youtube_to_mp3.py`
   - On Windows, run command prompt as administrator if needed

5. **Network errors**
   - Check your internet connection
   - Some videos might be geo-restricted or have download limitations

6. **Age-restricted videos**
   - The script might not work with age-restricted content due to YouTube's policies
   - Try using `--cookies-from-browser` option (advanced usage)

### Windows-Specific Troubleshooting

If you're on Windows and getting "yt-dlp not found" errors:

1. **Run the diagnostic tool:**
   ```bash
   python diagnose_windows.py
   ```

3. **Common Windows solutions:**
   - Use `python -m pip install --user yt-dlp` instead of just `pip install yt-dlp`
   - Restart your command prompt after installation
   - The script automatically tries both `yt-dlp` and `python -m yt_dlp`

4. **PATH issues on Windows:**
   - Add Python Scripts directory to PATH: `C:\Users\YourUser\AppData\Roaming\Python\Python3X\Scripts`
   - Or use the full Python path: `C:\Users\YourUser\AppData\Local\Programs\Python\Python3X\python.exe`

### Getting More Help

- Run `python youtube_to_mp3.py --help` for usage information
- Check yt-dlp documentation: https://github.com/yt-dlp/yt-dlp
- Ensure you're using the script in compliance with YouTube's Terms of Service

## Legal Notice

Please ensure you have the right to download and convert the content. Respect copyright laws and YouTube's Terms of Service. This tool should only be used for personal use with content you own or have permission to download.
