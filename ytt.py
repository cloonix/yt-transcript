#!/usr/bin/env python3
"""
Download YouTube video transcripts as plain text.
Usage: 
  python download_transcript.py <video_url_or_id>           # outputs to stdout (pipe-friendly)
  python download_transcript.py <video_url_or_id> <file>    # saves to file
  python download_transcript.py -l de <video_url_or_id>     # prefer German, fallback to English
"""

import argparse
import os
import sys
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    InvalidVideoId,
)

# Maximum number of languages to accept
MAX_LANGUAGES = 10

# Forbidden system directories for output files (includes macOS paths)
FORBIDDEN_PATHS = [
    # Linux system directories
    '/etc', '/sys', '/proc', '/boot', '/root', '/var',
    # macOS system directories (macOS symlinks /etc -> /private/etc, etc.)
    '/private/etc', '/private/var', '/System', '/Library', '/Applications',
    # Common sensitive directories
    '/tmp', '/dev',
]

# Forbidden filenames that should not be overwritten
FORBIDDEN_FILENAMES = ['.env', '.git', 'id_rsa', 'authorized_keys', '.ssh']


def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return as-is if already an ID."""
    # Limit input length to prevent ReDoS
    if len(url_or_id) > 500:
        return None
    
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            video_id = match.group(1)
            # Additional validation: ensure it only contains valid characters
            if re.match(r'^[0-9A-Za-z_-]{11}$', video_id):
                return video_id
    
    return None


def sanitize_for_display(text, max_length=50):
    """Sanitize text for safe terminal display."""
    if not text:
        return ''
    # Remove control characters and limit length
    sanitized = ''.join(c for c in text[:max_length] if c.isprintable())
    return sanitized


def validate_output_path(output_file):
    """
    Validate output file path to prevent path traversal attacks.
    Returns (is_valid, error_message).
    """
    # Check for empty path
    if not output_file or not output_file.strip():
        return False, 'Output path cannot be empty'
    
    try:
        output_path = Path(output_file).resolve()
        output_path_str = str(output_path)
        
        # Check against forbidden system directories
        # Resolve forbidden paths too to handle symlinks (e.g., macOS /etc -> /private/etc)
        for forbidden in FORBIDDEN_PATHS:
            forbidden_resolved = str(Path(forbidden).resolve()) if Path(forbidden).exists() else forbidden
            if output_path_str.startswith(forbidden_resolved) or output_path_str.startswith(forbidden):
                return False, f'Cannot write to system directory: {forbidden}'
        
        # Check against forbidden filenames
        if output_path.name in FORBIDDEN_FILENAMES:
            return False, f'Cannot overwrite protected file: {output_path.name}'
        
        # Check if parent directory exists
        if not output_path.parent.exists():
            return False, f'Parent directory does not exist: {output_path.parent}'
        
        return True, None
        
    except (ValueError, OSError) as e:
        return False, f'Invalid output path: {e}'


def create_api_client():
    """
    Create YouTubeTranscriptApi client with optional configuration from environment.
    Supports YOUTUBE_COOKIES and YOUTUBE_PROXY_* environment variables.
    """
    from youtube_transcript_api.proxies import GenericProxyConfig
    
    cookies_path = os.environ.get('YOUTUBE_COOKIES')
    proxy_http = os.environ.get('YOUTUBE_PROXY_HTTP')
    proxy_https = os.environ.get('YOUTUBE_PROXY_HTTPS')
    
    kwargs = {}
    
    # Configure cookies if provided
    if cookies_path:
        cookies_path = Path(cookies_path).expanduser()
        if cookies_path.exists():
            kwargs['cookies'] = str(cookies_path)
        else:
            print(f'Warning: Cookies file not found: {cookies_path}', file=sys.stderr)
    
    # Configure proxy if provided
    if proxy_http or proxy_https:
        kwargs['proxy_config'] = GenericProxyConfig(
            http_url=proxy_http,
            https_url=proxy_https or proxy_http
        )
    
    return YouTubeTranscriptApi(**kwargs)


def download_transcript(video_id, output_file=None, languages=None):
    """Download transcript for a YouTube video."""
    if languages is None:
        languages = ['en']
    
    # Validate output path if provided
    if output_file:
        is_valid, error_msg = validate_output_path(output_file)
        if not is_valid:
            print(f'Error: {error_msg}', file=sys.stderr)
            return False
    
    try:
        api = create_api_client()
        transcript = api.fetch(video_id, languages=languages)
        
        # Collect transcript text
        text_lines = [entry.text for entry in transcript]
        
        # Output to stdout or file
        if output_file:
            # Write to file with status messages to stderr
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_lines) + '\n')
            
            print(f'Transcript downloaded successfully', file=sys.stderr)
            print(f'  Video ID: {video_id}', file=sys.stderr)
            print(f'  Output: {output_file}', file=sys.stderr)
            print(f'  Lines: {len(text_lines)}', file=sys.stderr)
        else:
            # Output to stdout (pipe-friendly)
            print('\n'.join(text_lines))
        
        return True
    
    except TranscriptsDisabled:
        print('Error: Transcripts are disabled for this video', file=sys.stderr)
        return False
    
    except NoTranscriptFound:
        lang_str = ', '.join(languages)
        print(f'Error: No transcript found for languages: {lang_str}', file=sys.stderr)
        return False
    
    except VideoUnavailable:
        print('Error: Video is unavailable or does not exist', file=sys.stderr)
        return False
    
    except InvalidVideoId:
        print('Error: Invalid video ID', file=sys.stderr)
        return False
    
    except Exception as e:
        # Log only the exception type, not the full message (may contain sensitive info)
        error_type = type(e).__name__
        print(f'Error downloading transcript: {error_type}', file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube video transcripts as plain text.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python download_transcript.py https://www.youtube.com/watch?v=d1CdyCDZ2x8
  python download_transcript.py d1CdyCDZ2x8 | grep "keyword"
  python download_transcript.py d1CdyCDZ2x8 -o output.txt
  python download_transcript.py -l de d1CdyCDZ2x8     # prefer German, fallback to English
  python download_transcript.py -l de,fr d1CdyCDZ2x8  # prefer German, then French, then English

Environment Variables:
  YOUTUBE_COOKIES      Path to Netscape-format cookies file for age-restricted videos
  YOUTUBE_PROXY_HTTP   HTTP proxy URL (e.g., http://user:pass@proxy:8080)
  YOUTUBE_PROXY_HTTPS  HTTPS proxy URL (defaults to HTTP proxy if not set)
'''
    )
    parser.add_argument('video', help='YouTube video URL or ID')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-l', '--lang', 
                        help='Preferred language(s), comma-separated (default: en). '
                             'English is always used as final fallback.')
    
    args = parser.parse_args()
    
    video_id = extract_video_id(args.video)
    if not video_id:
        # Sanitize user input for display
        safe_input = sanitize_for_display(args.video)
        print(f'Error: Could not extract video ID from: {safe_input}', file=sys.stderr)
        sys.exit(1)
    
    # Build language list with English fallback (limit to MAX_LANGUAGES)
    if args.lang:
        languages = [lang.strip() for lang in args.lang.split(',')][:MAX_LANGUAGES]
        if 'en' not in languages:
            languages.append('en')
    else:
        languages = ['en']
    
    success = download_transcript(video_id, args.output, languages)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
