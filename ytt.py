#!/usr/bin/env python3
"""
Download YouTube video transcripts as plain text.
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

# Forbidden system directories for output files (includes macOS paths)
FORBIDDEN_PATHS = [
    '/etc', '/sys', '/proc', '/boot', '/root', '/var',
    '/private/etc', '/private/var', '/System', '/Library', '/Applications',
    '/tmp', '/dev',
]


def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return as-is if already an ID."""
    if len(url_or_id) > 500:
        return None
    
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match and re.match(r'^[0-9A-Za-z_-]{11}$', match.group(1)):
            return match.group(1)
    
    return None


def validate_output_path(output_file):
    """Validate output file path to prevent path traversal attacks."""
    if not output_file or not output_file.strip():
        return False
    
    try:
        resolved = str(Path(output_file).resolve())
        for forbidden in FORBIDDEN_PATHS:
            forbidden_resolved = str(Path(forbidden).resolve()) if Path(forbidden).exists() else forbidden
            if resolved.startswith(forbidden_resolved) or resolved.startswith(forbidden):
                return False
        return True
    except (ValueError, OSError):
        return False


def create_api_client():
    """Create YouTubeTranscriptApi client with optional env configuration."""
    kwargs = {}
    
    cookies_path = os.environ.get('YOUTUBE_COOKIES')
    if cookies_path:
        expanded = Path(cookies_path).expanduser()
        if expanded.exists():
            kwargs['cookies'] = str(expanded)
    
    proxy_http = os.environ.get('YOUTUBE_PROXY_HTTP')
    proxy_https = os.environ.get('YOUTUBE_PROXY_HTTPS')
    if proxy_http or proxy_https:
        from youtube_transcript_api.proxies import GenericProxyConfig
        kwargs['proxy_config'] = GenericProxyConfig(
            http_url=proxy_http,
            https_url=proxy_https or proxy_http
        )
    
    return YouTubeTranscriptApi(**kwargs)


def download_transcript(video_id, output_file=None, languages=None):
    """Download transcript for a YouTube video."""
    languages = languages or ['en']
    
    if output_file and not validate_output_path(output_file):
        print('Error: Invalid output path', file=sys.stderr)
        return False
    
    try:
        transcript = create_api_client().fetch(video_id, languages=languages)
        text = '\n'.join(entry.text for entry in transcript)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text + '\n')
        else:
            print(text)
        
        return True
    
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, InvalidVideoId) as e:
        print(f'Error: {type(e).__name__}', file=sys.stderr)
        return False
    except Exception as e:
        print(f'Error: {type(e).__name__}', file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube video transcripts as plain text.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  ytt https://www.youtube.com/watch?v=dQw4w9WgXcQ
  ytt dQw4w9WgXcQ -o transcript.txt
  ytt -l de,fr dQw4w9WgXcQ

Environment Variables:
  YOUTUBE_COOKIES       Path to cookies file for age-restricted videos
  YOUTUBE_PROXY_HTTP    HTTP proxy URL
  YOUTUBE_PROXY_HTTPS   HTTPS proxy URL
'''
    )
    parser.add_argument('video', help='YouTube video URL or ID')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-l', '--lang', help='Preferred language(s), comma-separated (default: en)')
    
    args = parser.parse_args()
    
    video_id = extract_video_id(args.video)
    if not video_id:
        print('Error: Invalid video URL or ID', file=sys.stderr)
        sys.exit(1)
    
    languages = [l.strip() for l in args.lang.split(',')] if args.lang else []
    if 'en' not in languages:
        languages.append('en')
    
    success = download_transcript(video_id, args.output, languages)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
