#!/usr/bin/env python3
"""
YouTube to MP3 Converter

A Python script that downloads YouTube videos and converts them to MP3 format using ffmpeg.
Supports single videos, YouTube playlist URLs, and JSON playlist files.
Requires yt-dlp and ffmpeg to be installed.

Usage:
    python youtube_to_mp3.py <youtube_url_or_playlist_file>

Examples:
    python youtube_to_mp3.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
    python youtube_to_mp3.py "https://www.youtube.com/playlist?list=PLxxxxxx"
    python youtube_to_mp3.py playlist.json
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    # Check yt-dlp (try both as module and command)
    yt_dlp_available = False
    
    # First try importing as Python module
    try:
        import yt_dlp
        yt_dlp_available = True
    except ImportError:
        pass
    
    # If module import failed, try as command line tool
    if not yt_dlp_available:
        try:
            # Try different possible command names
            for cmd in ['yt-dlp', 'python -m yt_dlp']:
                try:
                    if cmd.startswith('python'):
                        subprocess.run(cmd.split() + ['--version'], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL, 
                                     check=True)
                    else:
                        subprocess.run([cmd, '--version'], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL, 
                                     check=True)
                    yt_dlp_available = True
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        except:
            pass
    
    if not yt_dlp_available:
        missing.append('yt-dlp')
    
    # Check ffmpeg
    ffmpeg_available = False
    try:
        subprocess.run(['ffmpeg', '-version'], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL, 
                     check=True)
        ffmpeg_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    if not ffmpeg_available:
        missing.append('ffmpeg')
    
    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print("Please install them using:")
        if 'yt-dlp' in missing:
            print("  pip install yt-dlp")
            print("  (or try: python -m pip install yt-dlp)")
        if 'ffmpeg' in missing:
            print("  Install ffmpeg from https://ffmpeg.org/download.html")
        return False
    
    return True


def download_and_convert(youtube_url, output_dir='./output', title_override=None):
    """
    Download YouTube video and convert to MP3.
    
    Args:
        youtube_url (str): YouTube video URL
        output_dir (str): Directory to save the MP3 file
        title_override (str): Optional title override for filename
    
    Returns:
        str: Path to the converted MP3 file, or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Use title override if provided, otherwise use video title
        if title_override:
            # Clean filename for filesystem compatibility
            safe_title = "".join(c for c in title_override if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            safe_title = safe_title[:100]  # Limit length
            output_template = os.path.join(output_dir, f'{safe_title}.%(ext)s')
        else:
            output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
        
        # Try different ways to call yt-dlp
        commands_to_try = [
            ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '192K', '--output', output_template, '--no-playlist', youtube_url],
            ['python', '-m', 'yt_dlp', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '192K', '--output', output_template, '--no-playlist', youtube_url]
        ]
        
        print(f"Downloading and converting: {youtube_url}")
        if title_override:
            print(f"Title: {title_override}")
        print("This may take a while depending on the video length...")
        
        result = None
        last_error = None
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                break  # Success, exit loop
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                last_error = e
                continue  # Try next command
        
        if result is None:
            raise last_error
        
        # Improved file detection - try multiple methods
        output_lines = result.stdout.split('\n')
        mp3_file = None
        
        # Method 1: Look for ExtractAudio Destination line
        for line in output_lines:
            if '[ExtractAudio]' in line and 'Destination:' in line:
                mp3_file = line.split('Destination:')[1].strip()
                break
        
        # Method 2: Look for other output indicators
        if not mp3_file:
            for line in output_lines:
                if 'Deleting original file' in line:
                    # Extract filename from deletion message
                    parts = line.split()
                    for part in parts:
                        if part.endswith('.mp3'):
                            mp3_file = part
                            break
                    if mp3_file:
                        break
        
        # Method 3: Look for files matching our output pattern
        if not mp3_file:
            # Try to find MP3 files in the output directory that were created recently
            mp3_files = list(Path(output_dir).glob('*.mp3'))
            if mp3_files:
                # Get the most recently created MP3 file
                mp3_file = str(max(mp3_files, key=os.path.getctime))
        
        # Method 4: Parse yt-dlp's verbose output for filename
        if not mp3_file:
            for line in output_lines:
                if line.strip().endswith('.mp3') and ('/' in line or '\\' in line):
                    # This might be a full path to the output file
                    potential_file = line.strip()
                    if os.path.exists(potential_file):
                        mp3_file = potential_file
                        break
        
        if mp3_file and os.path.exists(mp3_file):
            print(f"Successfully converted to MP3: {mp3_file}")
            return mp3_file
        else:
            # Final fallback - look for any MP3 files in output directory
            mp3_files = list(Path(output_dir).glob('*.mp3'))
            if mp3_files:
                recent_file = str(max(mp3_files, key=os.path.getctime))
                print(f"Found MP3 file: {recent_file}")
                return recent_file
            else:
                print("Warning: Conversion may have completed but couldn't locate output file")
                print("Please check the output directory manually.")
                return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error during download/conversion: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def load_playlist_from_json(playlist_file):
    """
    Load playlist data from JSON file.
    
    Args:
        playlist_file (str): Path to JSON playlist file
    
    Returns:
        list: List of video dictionaries, or None if failed
    """
    try:
        with open(playlist_file, 'r', encoding='utf-8') as f:
            playlist_data = json.load(f)
        
        if not isinstance(playlist_data, list):
            print(f"Error: Playlist file must contain a JSON array")
            return None
        
        print(f"Loaded playlist with {len(playlist_data)} videos from {playlist_file}")
        return playlist_data
    
    except FileNotFoundError:
        print(f"Error: Playlist file '{playlist_file}' not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in playlist file: {e}")
        return None
    except Exception as e:
        print(f"Error loading playlist: {e}")
        return None


def process_playlist(playlist_data, output_dir='.'):
    """
    Process a playlist of videos and download/convert each one.
    
    Args:
        playlist_data (list): List of video dictionaries
        output_dir (str): Directory to save MP3 files
    
    Returns:
        tuple: (successful_downloads, failed_downloads)
    """
    successful = []
    failed = []
    total = len(playlist_data)
    
    print(f"\nProcessing playlist with {total} videos...")
    print("=" * 60)
    
    for i, video in enumerate(playlist_data, 1):
        print(f"\n[{i}/{total}] Processing video...")
        
        # Extract video information
        video_url = video.get('videoUrl')
        title = video.get('title', f'Video_{i}')
        video_id = video.get('videoId', '')
        
        if not video_url:
            print(f"❌ Skipping video {i}: No videoUrl found")
            failed.append(title)
            continue
        
        print(f"Title: {title}")
        print(f"URL: {video_url}")
        
        # Download and convert
        result = download_and_convert(video_url, output_dir, title)
        
        if result:
            print(f"✅ Successfully converted: {title}")
            successful.append(title)
        else:
            print(f"❌ Failed to convert: {title}")
            failed.append(title)
        
        # Progress indicator
        print(f"Progress: {len(successful)} successful, {len(failed)} failed")
    
    return successful, failed


def print_playlist_summary(successful, failed):
    """Print a summary of playlist processing results."""
    total = len(successful) + len(failed)
    
    print("\n" + "=" * 60)
    print("PLAYLIST PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total videos: {total}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\n✅ Successfully converted ({len(successful)}):")
        for i, title in enumerate(successful, 1):
            print(f"  {i}. {title}")
    
    if failed:
        print(f"\n❌ Failed to convert ({len(failed)}):")
        for i, title in enumerate(failed, 1):
            print(f"  {i}. {title}")
    
    print("=" * 60)


def is_youtube_playlist_url(url):
    """
    Check if the URL is a YouTube playlist URL.
    
    Args:
        url (str): URL to check
    
    Returns:
        bool: True if it's a YouTube playlist URL
    """
    if not url.startswith('http'):
        return False
    
    # Check for playlist indicators
    playlist_indicators = [
        'list=' in url,  # Standard playlist parameter
        '/playlist?list=' in url,  # Direct playlist URL
        'watch?v=' in url and 'list=' in url  # Video in playlist
    ]
    
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com', 'www.youtube.com']
    
    return any(domain in url for domain in youtube_domains) and any(playlist_indicators)


def extract_playlist_info(playlist_url):
    """
    Extract playlist information using yt-dlp.
    
    Args:
        playlist_url (str): YouTube playlist URL
    
    Returns:
        list: List of video dictionaries with title and URL, or None if failed
    """
    try:
        print(f"Extracting playlist information from: {playlist_url}")
        print("This may take a moment...")
        
        # Try different ways to call yt-dlp for playlist extraction
        commands_to_try = [
            ['yt-dlp', '--flat-playlist', '--print', '%(title)s|%(webpage_url)s|%(id)s', playlist_url],
            ['python', '-m', 'yt_dlp', '--flat-playlist', '--print', '%(title)s|%(webpage_url)s|%(id)s', playlist_url]
        ]
        
        result = None
        last_error = None
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                break  # Success, exit loop
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                last_error = e
                continue  # Try next command
        
        if result is None:
            raise last_error
        
        # Parse the output
        playlist_data = []
        lines = result.stdout.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    title, url, video_id = parts
                    video_info = {
                        'title': title.strip(),
                        'videoUrl': url.strip(),
                        'videoId': video_id.strip(),
                        'author': 'Unknown',
                        'length': 'Unknown',
                        'viewCount': 'Unknown',
                        'publishedDate': 'Unknown',
                        'thumbnailUrl': f'https://i.ytimg.com/vi/{video_id.strip()}/hqdefault.jpg'
                    }
                    playlist_data.append(video_info)
                else:
                    print(f"Warning: Could not parse line {i}: {line}")
        
        if playlist_data:
            print(f"✓ Found {len(playlist_data)} videos in playlist")
            return playlist_data
        else:
            print("❌ No videos found in playlist")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error extracting playlist: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error extracting playlist: {e}")
        return None


def is_playlist_file(input_path):
    """
    Check if the input is a playlist file (JSON).
    
    Args:
        input_path (str): Input path/URL
    
    Returns:
        bool: True if it's a playlist file
    """
    # Check if it's a file path that exists and ends with .json
    if os.path.isfile(input_path) and input_path.lower().endswith('.json'):
        return True
    
    # Check if it looks like a file path even if it doesn't exist yet
    if input_path.lower().endswith('.json') and not input_path.startswith('http'):
        return True
    
    return False


def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description='Download YouTube videos and convert them to MP3. Supports single videos, YouTube playlist URLs, and JSON playlists.',
        epilog='Examples:\n'
               '  Single video: python youtube_to_mp3.py https://www.youtube.com/watch?v=dQw4w9WgXcQ\n'
               '  Playlist URL: python youtube_to_mp3.py "https://www.youtube.com/playlist?list=PLxxxxxx"\n'
               '  JSON file: python youtube_to_mp3.py playlist.json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input', help='YouTube video URL, YouTube playlist URL, or JSON playlist file')
    parser.add_argument('-o', '--output', default='.', 
                       help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Check if dependencies are installed
    if not check_dependencies():
        sys.exit(1)
    
    # Determine input type and process accordingly
    if is_playlist_file(args.input):
        # Process JSON playlist file
        print("📁 Processing JSON playlist file...")
        playlist_data = load_playlist_from_json(args.input)
        if not playlist_data:
            sys.exit(1)
        
        successful, failed = process_playlist(playlist_data, args.output)
        print_playlist_summary(successful, failed)
        
        if failed:
            sys.exit(1)  # Exit with error if any downloads failed
        else:
            print(f"\n🎉 All {len(successful)} videos converted successfully!")
            sys.exit(0)
    
    elif is_youtube_playlist_url(args.input):
        # Process YouTube playlist URL
        print("🎵 Processing YouTube playlist URL...")
        playlist_data = extract_playlist_info(args.input)
        if not playlist_data:
            sys.exit(1)
        
        successful, failed = process_playlist(playlist_data, args.output)
        print_playlist_summary(successful, failed)
        
        if failed:
            sys.exit(1)  # Exit with error if any downloads failed
        else:
            print(f"\n🎉 All {len(successful)} videos converted successfully!")
            sys.exit(0)
    
    else:
        # Process single video URL
        # Validate URL (basic check)
        if 'youtube.com' not in args.input and 'youtu.be' not in args.input:
            print("Error: Please provide a valid YouTube URL (single video or playlist) or JSON playlist file")
            sys.exit(1)
        
        print("🎵 Processing single video...")
        # Download and convert
        result = download_and_convert(args.input, args.output)
        
        if result:
            print(f"\n✓ Conversion completed successfully!")
            print(f"MP3 file saved to: {result}")
            sys.exit(0)
        else:
            print("\n✗ Conversion failed!")
            sys.exit(1)


if __name__ == '__main__':
    main()
