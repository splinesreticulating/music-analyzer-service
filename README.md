# Essentia Music Analyzer (FastAPI)

A simple FastAPI service that uses [Essentia](https://essentia.upf.edu/) to extract BPM and musical key from audio files, and maps keys to [Camelot notation](https://mixedinkey.com/camelot-wheel/).

## Features

- Analyze an audio file by **path** (within a configured safe root)
- Returns:
  - BPM (with confidence, if available)
  - Musical key (major/minor)
  - Camelot key
  - Key confidence
- JSON API, easy to call from Node.js or Next.js

## Requirements

- Python 3.9+
- [Essentia](https://essentia.upf.edu/) (via `pip install essentia`)
- FastAPI + Uvicorn
- python-dotenv (for local development)

## Setup

```bash
# Clone the repo
git clone git@github.com:splinesreticulating/music-analyzer-service.git

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the service
cd service
uvicorn app:app --host 0.0.0.0 --port 8000
```

Analyze a track by file path (must be inside the `SAFE_ROOT` defined in `app.py`):

```bash
curl -X POST http://localhost:8000/analyze/path \
  -H "Content-Type: application/json" \
  -d '{"path":"/path/to/file.mp3","seconds":120}'
```

Example response:
```json
{
  "file": "file.mp3",
  "bpm": 104.4,
  "bpm_confidence": 2.65,
  "key": "Bb",
  "scale": "major",
  "camelot": "6B",
  "key_confidence": 0.89
}
```

## API

- `POST /analyze/path`

  Analyze a file by its absolute path (must be under `SAFE_ROOT`).

  - Request body: `{"path": "<file path>", "seconds": 120}`

## Notes

- For now, only path-based analysis is enabled. You can add an /upload endpoint if you want to accept uploaded files.

- Key detection is accurate for most popular music, but ambiguous tracks may vary.

- BPM confidence values may be >1.0 — they’re a relative measure from Essentia.

## License

This project is licensed under the MIT License.
