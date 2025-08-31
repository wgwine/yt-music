#!/usr/bin/env python3
"""
Windows Diagnostic Script for YouTube to MP3 Converter

This script helps diagnose common Windows installation and PATH issues
that can prevent the YouTube to MP3 converter from working properly.
"""

import sys
import os
import subprocess
import importlib.util

def check_python_info():
    """Display Python installation information."""
    print("Python Installation Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Python executable: {sys.executable}")
    print(f"  Python path: {sys.path[:3]}...")  # Show first 3 paths
    
    # Check if user site-packages is in path
    import site
    try:
        user_site = site.getusersitepackages()
        print(f"  User site-packages: {user_site}")
        print(f"  User site-packages exists: {os.path.exists(user_site)}")
    except:
        print("  User site-packages: Not available")

def check_yt_dlp_installation():
    """Check yt-dlp installation in detail."""
    print("\nyt-dlp Installation Check:")
    
    # Method 1: Try importing
    try:
        import yt_dlp
        print("  ✓ yt-dlp module can be imported")
        print(f"    Version: {yt_dlp.version.__version__}")
        print(f"    Location: {yt_dlp.__file__}")
    except ImportError as e:
        print(f"  ✗ Cannot import yt-dlp module: {e}")
    
    # Method 2: Check if installed via pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'yt-dlp'], 
                               capture_output=True, text=True, check=True)
        print("  ✓ yt-dlp found via pip:")
        for line in result.stdout.split('\n'):
            if line.startswith(('Version:', 'Location:')):
                print(f"    {line}")
    except subprocess.CalledProcessError:
        print("  ✗ yt-dlp not found via pip")
    
    # Method 3: Try calling as module
    try:
        result = subprocess.run([sys.executable, '-m', 'yt_dlp', '--version'], 
                               capture_output=True, text=True, check=True)
        print("  ✓ yt-dlp can be called as module")
        print(f"    Output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Cannot call yt-dlp as module: {e}")
    
    # Method 4: Try calling as command
    try:
        result = subprocess.run(['yt-dlp', '--version'], 
                               capture_output=True, text=True, check=True)
        print("  ✓ yt-dlp can be called as command")
        print(f"    Output: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ✗ Cannot call yt-dlp as command: {e}")

def check_ffmpeg_installation():
    """Check ffmpeg installation."""
    print("\nffmpeg Installation Check:")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, text=True, check=True)
        print("  ✓ ffmpeg is available")
        # Extract version from first line
        first_line = result.stdout.split('\n')[0]
        print(f"    {first_line}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  ✗ ffmpeg not available: {e}")
        print("    Install ffmpeg from: https://ffmpeg.org/download.html")

def check_path_environment():
    """Check PATH environment variable."""
    print("\nPATH Environment Check:")
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    
    print(f"  PATH contains {len(path_dirs)} directories")
    
    # Look for Python Scripts directory (where pip installs executables on Windows)
    python_scripts_dirs = [d for d in path_dirs if 'Scripts' in d and 'Python' in d]
    if python_scripts_dirs:
        print("  Python Scripts directories in PATH:")
        for d in python_scripts_dirs:
            print(f"    {d}")
            # Check if yt-dlp.exe exists there
            yt_dlp_exe = os.path.join(d, 'yt-dlp.exe')
            if os.path.exists(yt_dlp_exe):
                print(f"      ✓ yt-dlp.exe found here")
    else:
        print("  ✗ No Python Scripts directories found in PATH")
        print("    This might explain why yt-dlp command is not found")

def provide_solutions():
    """Provide potential solutions."""
    print("\nPotential Solutions:")
    print("1. If yt-dlp module can be imported but command fails:")
    print("   - Use: python -m yt_dlp instead of yt-dlp")
    print("   - Or add Python Scripts directory to PATH")
    
    print("\n2. If yt-dlp is not found at all:")
    print("   - Try: python -m pip install --user yt-dlp")
    print("   - Or: pip install --user yt-dlp")
    
    print("\n3. If ffmpeg is not found:")
    print("   - Download from: https://ffmpeg.org/download.html")
    print("   - Add ffmpeg.exe location to PATH")
    
    print("\n4. If PATH issues persist:")
    print("   - Restart command prompt/terminal after installation")
    print("   - Use full Python path: C:\\...\\python.exe -m yt_dlp")

def main():
    """Main diagnostic function."""
    print("Windows Diagnostic Tool for YouTube to MP3 Converter")
    print("=" * 60)
    
    check_python_info()
    check_yt_dlp_installation()
    check_ffmpeg_installation()
    check_path_environment()
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("Diagnostic complete. Use the information above to troubleshoot issues.")

if __name__ == '__main__':
    main()
