# ytt - YouTube Transcript Tool

Download YouTube video transcripts as plain text from the command line.

## Installation

```bash
# Using pipx (recommended)
pipx install git+https://github.com/cloonix/yt-transcript.git

# Using pip
pip install git+https://github.com/cloonix/yt-transcript.git
```

## Usage

```bash
# Output to stdout (pipe-friendly)
ytt https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Save to file
ytt https://www.youtube.com/watch?v=dQw4w9WgXcQ -o transcript.txt

# Using just the video ID
ytt dQw4w9WgXcQ

# Pipe to other tools
ytt dQw4w9WgXcQ | grep "keyword"
ytt dQw4w9WgXcQ | wc -w

# Specify preferred language (falls back to English)
ytt -l de dQw4w9WgXcQ           # German preferred
ytt -l de,fr dQw4w9WgXcQ        # German, then French, then English
```

## Options

```
positional arguments:
  video                 YouTube video URL or ID

options:
  -h, --help            show this help message and exit
  -o, --output FILE     Output file (default: stdout)
  -l, --lang LANG       Preferred language(s), comma-separated (default: en)
```

## License

MIT
