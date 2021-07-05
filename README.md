# transcribe

A simple script transcribing mp3 files in a given folder using GCP Speech2Text (free tier)

## Requirements
- python3.6
- ffmpeg, for MacOS `brew install ffmpeg`
- GCP Speech2Text credentials  (free tier is OK). See `sample_credentials.json`

## Setup (MacOS)

```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

try `python gcp_transcribe.py -h` to see usages
