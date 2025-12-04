#!/usr/bin/env python3
"""
Download YouTube video transcripts as plain text.
Usage: 
  python download_transcript.py <video_url_or_id>           # outputs to stdout (pipe-friendly)
  python download_transcript.py <video_url_or_id> <file>    # saves to file
  python download_transcript.py -l de <video_url_or_id>     # prefer German, fallback to English
"""

import argparse
import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return as-is if already an ID."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def download_transcript(video_id, output_file=None, languages=None):
    """Download transcript for a YouTube video."""
    if languages is None:
        languages = ['en']
    
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=languages)
        
        # Collect transcript text
        text_lines = [entry.text for entry in transcript]
        
        # Output to stdout or file
        if output_file:
            # Write to file with status messages to stderr
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(text_lines) + '\n')
            
            print(f'✓ Transcript downloaded successfully', file=sys.stderr)
            print(f'  Video ID: {video_id}', file=sys.stderr)
            print(f'  Output: {output_file}', file=sys.stderr)
            print(f'  Lines: {len(text_lines)}', file=sys.stderr)
        else:
            # Output to stdout (pipe-friendly)
            print('\n'.join(text_lines))
        
        return True
        
    except Exception as e:
        print(f'✗ Error downloading transcript: {e}', file=sys.stderr)
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
        print(f'✗ Error: Could not extract video ID from: {args.video}', file=sys.stderr)
        sys.exit(1)
    
    # Build language list with English fallback
    if args.lang:
        languages = [lang.strip() for lang in args.lang.split(',')]
        if 'en' not in languages:
            languages.append('en')
    else:
        languages = ['en']
    
    success = download_transcript(video_id, args.output, languages)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
