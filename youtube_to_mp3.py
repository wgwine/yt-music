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


def download_and_convert(youtube_url, output_dir='.', title_override=None):
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
        
        # Check if MP3 already exists (skip if it does)
        if title_override:
            # Clean filename for filesystem compatibility
            safe_title = "".join(c for c in title_override if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            safe_title = safe_title[:100]  # Limit length
            expected_mp3_path = Path(output_dir) / f'{safe_title}.mp3'
            
            if expected_mp3_path.exists():
                print(f"⏭️  Skipping (MP3 already exists): {expected_mp3_path.name}")
                return str(expected_mp3_path)
            
            output_template = os.path.join(output_dir, f'{safe_title}.%(ext)s')
        else:
            # For non-override titles, we need to get the video title first to check if MP3 exists
            try:
                temp_result = subprocess.run(
                    ['yt-dlp', '--get-title', youtube_url], 
                    capture_output=True, text=True, check=True
                )
                video_title = temp_result.stdout.strip()
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                safe_title = safe_title[:100]  # Limit length
                expected_mp3_path = Path(output_dir) / f'{safe_title}.mp3'
                
                if expected_mp3_path.exists():
                    print(f"⏭️  Skipping (MP3 already exists): {expected_mp3_path.name}")
                    return str(expected_mp3_path)
            except:
                # If we can't get the title, continue with normal download
                pass
            
            output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
        
        # Step 1: Download video first (without conversion)
        video_download_template = output_template.replace('.%(ext)s', '.%(ext)s')
        
        download_commands_to_try = [
            ['yt-dlp', '--format', 'bestaudio/best', '--output', video_download_template, '--no-playlist', youtube_url],
            ['python', '-m', 'yt_dlp', '--format', 'bestaudio/best', '--output', video_download_template, '--no-playlist', youtube_url]
        ]
        
        print(f"Downloading video: {youtube_url}")
        if title_override:
            print(f"Title: {title_override}")
        print("This may take a while depending on the video length...")
        
        # Download the video
        download_result = None
        last_download_error = None
        
        for cmd in download_commands_to_try:
            try:
                download_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                break  # Success, exit loop
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                last_download_error = e
                continue  # Try next command
        
        if download_result is None:
            raise last_download_error
        
        # Find the downloaded video file
        print("Locating downloaded file...")
        video_file = None
        
        # Look for common video/audio formats in output directory
        video_extensions = ['*.mp4', '*.webm', '*.m4a', '*.mp3', '*.opus', '*.aac', '*.flv', '*.mkv']
        downloaded_files = []
        
        for ext in video_extensions:
            downloaded_files.extend(list(Path(output_dir).glob(ext)))
        
        if downloaded_files:
            # Get the most recently created file (should be our download)
            video_file = max(downloaded_files, key=os.path.getctime)
            print(f"Found downloaded file: {video_file.name}")
        else:
            print("Error: Could not locate downloaded video file")
            return None
        
        # Step 2: Check if the downloaded file is already MP3
        if video_file.suffix.lower() == '.mp3':
            print(f"✓ File is already in MP3 format: {video_file}")
            return str(video_file)
        
        # Step 3: Convert to MP3 using ffmpeg
        print("Converting to MP3 format...")
        
        # Determine the output MP3 filename
        if title_override:
            safe_title = "".join(c for c in title_override if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            safe_title = safe_title[:100]  # Limit length
            mp3_file = Path(output_dir) / f'{safe_title}.mp3'
        else:
            mp3_file = video_file.with_suffix('.mp3')
        
        # Use ffmpeg to convert
        try:
            ffmpeg_result = subprocess.run([
                'ffmpeg', '-i', str(video_file), 
                '-codec:a', 'libmp3lame', 
                '-b:a', '192k',
                '-y',  # Overwrite output file
                str(mp3_file)
            ], capture_output=True, text=True, check=True)
            
            # Conversion successful - remove original video file
            try:
                video_file.unlink()
                print(f"✓ Successfully converted and cleaned up: {mp3_file.name}")
            except Exception as cleanup_error:
                print(f"✓ Successfully converted: {mp3_file.name}")
                print(f"Warning: Could not remove original video file: {cleanup_error}")
            
            return str(mp3_file)
            
        except subprocess.CalledProcessError as ffmpeg_error:
            # Conversion failed - keep the original video file
            print(f"✗ FFmpeg conversion failed: {ffmpeg_error.stderr}")
            print(f"📁 Original video file preserved: {video_file.name}")
            print("You can try converting it manually or use a different tool.")
            return None
        
        except FileNotFoundError:
            print("✗ FFmpeg not found. Please install FFmpeg to convert video files.")
            print(f"📁 Original video file preserved: {video_file.name}")
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
    Extract playlist information using yt-dlp without downloading.
    
    Args:
        playlist_url (str): YouTube playlist URL
    
    Returns:
        list: List of video dictionaries with title and URL, or None if failed
    """
    try:
        print(f"🔍 Extracting playlist metadata from: {playlist_url}")
        print("📋 Getting video list without downloading (avoids rate limits)...")
        
        # Try different ways to call yt-dlp for playlist extraction
        # Use a unique separator that won't appear in video titles
        separator = "|||SEPARATOR|||"
        commands_to_try = [
            ['yt-dlp', '--flat-playlist', '--print', f'%(title)s{separator}%(webpage_url)s{separator}%(id)s', '--no-download', playlist_url],
            ['python', '-m', 'yt_dlp', '--flat-playlist', '--print', f'%(title)s{separator}%(webpage_url)s{separator}%(id)s', '--no-download', playlist_url]
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
        
        # Parse the output using our unique separator
        playlist_data = []
        lines = result.stdout.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            if separator in line:
                parts = line.split(separator)
                if len(parts) >= 3:
                    title = parts[0].strip()
                    url = parts[1].strip()
                    video_id = parts[2].strip()
                    
                    # Validate that we got a proper YouTube URL
                    if not url.startswith('https://www.youtube.com/watch?v='):
                        print(f"Warning: Unexpected URL format in line {i}: {url}")
                        continue
                    
                    video_info = {
                        'title': title,
                        'videoUrl': url,
                        'videoId': video_id,
                        'author': 'Unknown',
                        'length': 'Unknown',
                        'viewCount': 'Unknown',
                        'publishedDate': 'Unknown',
                        'thumbnailUrl': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                    }
                    playlist_data.append(video_info)
                else:
                    print(f"Warning: Could not parse line {i}: {line}")
            elif line.strip():  # Skip empty lines
                print(f"Warning: Line {i} doesn't contain separator: {line[:50]}...")
        
        if playlist_data:
            print(f"✅ Found {len(playlist_data)} videos in playlist metadata")
            
            # Show first few entries for verification
            print("📋 Sample entries:")
            for i, video in enumerate(playlist_data[:3], 1):
                title_preview = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
                print(f"   {i}. {title_preview}")
                print(f"      URL: {video['videoUrl']}")
            
            if len(playlist_data) > 3:
                print(f"   ... and {len(playlist_data) - 3} more videos")
            
            return playlist_data
        else:
            print("❌ No videos found in playlist")
            print("This could be due to:")
            print("  • Private or restricted playlist") 
            print("  • Invalid playlist URL")
            print("  • Network connectivity issues")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error extracting playlist: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
            if "Sign in to confirm you're not a bot" in e.stderr:
                print("💡 This looks like a rate limiting issue.")
                print("   Try again later or use a VPN to change your IP address.")
        return None
    except Exception as e:
        print(f"Unexpected error extracting playlist: {e}")
        return None


def filter_missing_videos(playlist_data, output_dir='.'):
    """
    Filter playlist to only include videos that don't already exist as MP3s.
    This prevents unnecessary downloads and rate limiting.
    
    Args:
        playlist_data (list): List of video dictionaries from playlist
        output_dir (str): Directory to check for existing MP3 files
    
    Returns:
        tuple: (missing_videos, existing_videos) - both are lists of video info
    """
    if not playlist_data:
        return [], []
    
    print(f"\n🔍 Checking existing files in: {output_dir}")
    
    output_path = Path(output_dir)
    existing_mp3s = set()
    
    # Get all existing MP3 files
    if output_path.exists():
        for mp3_file in output_path.glob('*.mp3'):
            existing_mp3s.add(mp3_file.stem)  # filename without extension
    
    print(f"📁 Found {len(existing_mp3s)} existing MP3 files")
    
    missing_videos = []
    existing_videos = []
    
    # Check each video in the playlist
    for video in playlist_data:
        title = video.get('title', 'Unknown')
        
        # Sanitize title for filename matching
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        safe_title = safe_title[:100]  # Limit length
        
        # Check if MP3 already exists
        if safe_title in existing_mp3s:
            existing_videos.append(video)
        else:
            missing_videos.append(video)
    
    print(f"\n📊 Playlist Analysis:")
    print(f"   Total videos in playlist: {len(playlist_data)}")
    print(f"   Already downloaded (MP3): {len(existing_videos)}")
    print(f"   Missing (need download): {len(missing_videos)}")
    
    if existing_videos:
        print(f"\n⏭️  Skipping {len(existing_videos)} existing files:")
        for video in existing_videos[:5]:  # Show first 5
            title = video.get('title', 'Unknown')[:50]
            print(f"     ✓ {title}")
        if len(existing_videos) > 5:
            print(f"     ... and {len(existing_videos) - 5} more")
    
    if missing_videos:
        print(f"\n⬇️  Will download {len(missing_videos)} missing files:")
        for video in missing_videos[:5]:  # Show first 5
            title = video.get('title', 'Unknown')[:50]
            print(f"     📥 {title}")
        if len(missing_videos) > 5:
            print(f"     ... and {len(missing_videos) - 5} more")
    
    return missing_videos, existing_videos


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
        # Process JSON playlist file with smart filtering
        print("📁 Processing JSON playlist file...")
        playlist_data = load_playlist_from_json(args.input)
        if not playlist_data:
            sys.exit(1)
        
        # Filter out videos that already exist as MP3s
        missing_videos, existing_videos = filter_missing_videos(playlist_data, args.output)
        
        if not missing_videos:
            print(f"\n🎉 All {len(playlist_data)} videos are already downloaded!")
            print("✅ Nothing to do - all MP3 files exist.")
            sys.exit(0)
        
        # Only process missing videos
        print(f"\n🚀 Processing {len(missing_videos)} missing videos...")
        successful, failed = process_playlist(missing_videos, args.output)
        
        # Include existing videos in success count for reporting
        total_successful = successful + [v['title'] for v in existing_videos]
        print_playlist_summary(total_successful, failed)
        
        if failed:
            print(f"\n⚠️  {len(total_successful)} videos successful, {len(failed)} failed")
            sys.exit(1)
        else:
            print(f"\n🎉 All {len(total_successful)} videos are now available!")
            sys.exit(0)
    
    elif is_youtube_playlist_url(args.input):
        # Process YouTube playlist URL with smart filtering
        print("🎵 Processing YouTube playlist URL...")
        
        # Step 1: Extract playlist metadata (no downloads, avoids rate limits)
        playlist_data = extract_playlist_info(args.input)
        if not playlist_data:
            sys.exit(1)
        
        # Step 2: Filter out videos that already exist as MP3s
        missing_videos, existing_videos = filter_missing_videos(playlist_data, args.output)
        
        if not missing_videos:
            print(f"\n🎉 All {len(playlist_data)} videos are already downloaded!")
            print("✅ Nothing to do - all MP3 files exist.")
            sys.exit(0)
        
        # Step 3: Only process missing videos (avoids rate limiting)
        print(f"\n🚀 Processing {len(missing_videos)} missing videos...")
        successful, failed = process_playlist(missing_videos, args.output)
        
        # Step 4: Include existing videos in success count for reporting
        total_successful = successful + [v['title'] for v in existing_videos]
        print_playlist_summary(total_successful, failed)
        
        if failed:
            print(f"\n⚠️  {len(total_successful)} videos successful, {len(failed)} failed")
            sys.exit(1)
        else:
            print(f"\n🎉 All {len(total_successful)} videos are now available!")
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
