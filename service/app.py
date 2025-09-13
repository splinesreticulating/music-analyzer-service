from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from pathlib import Path
import essentia.standard as es
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Load required configuration from environment variable
SAFE_ROOT = os.environ.get("MUSIC_ANALYZER_SAFE_ROOT")
if not SAFE_ROOT:
    raise ValueError(
        "MUSIC_ANALYZER_SAFE_ROOT environment variable must be set. "
        "Please create a .env file in the project root with this variable."
    )

app = FastAPI(title="Essentia Audio Analyzer")


CAMELOT = {
    # Major keys (B suffix)
    "C major": "8B", "G major": "9B", "D major": "10B", "A major": "11B", 
    "E major": "12B", "B major": "1B", "F# major": "2B", "Gb major": "2B",
    "C# major": "3B", "Db major": "3B", "G# major": "4B", "Ab major": "4B",
    "D# major": "5B", "Eb major": "5B", "A# major": "6B", "Bb major": "6B",
    "F major": "7B",
    
    # Minor keys (A suffix) 
    "A minor": "8A", "E minor": "9A", "B minor": "10A", "F# minor": "11A",
    "Gb minor": "11A", "C# minor": "12A", "Db minor": "12A", "G# minor": "1A",
    "Ab minor": "1A", "D# minor": "2A", "Eb minor": "2A", "A# minor": "3A",
    "Bb minor": "3A", "F minor": "4A", "C minor": "5A", "G minor": "6A",
    "D minor": "7A"
}

class PathReq(BaseModel):
    path: str
    seconds: int = 180

def _to_float_or_none(x):
    # Safely coerce Essentia/NumPy outputs to a scalar float or None
    try:
        # numpy scalar?
        import numpy as np  # type: ignore
        if isinstance(x, np.generic):
            return float(x)
    except Exception:
        pass
    # sequence-like?
    try:
        if hasattr(x, "__len__"):
            return float(x[0]) if len(x) else None
    except Exception:
        pass
    # plain number?
    try:
        return float(x)
    except Exception:
        return None

def analyze(filepath: str, seconds: int):
    audio = es.MonoLoader(filename=filepath, sampleRate=44100)()
    if seconds and seconds > 0:
        max_samples = 44100 * seconds
        if len(audio) > max_samples:
            audio = audio[:max_samples]

    # BPM (robust → fallback)
    try:
        bpm_tuple = es.RhythmExtractor2013()(audio)
        bpm = float(bpm_tuple[0])
        bpm_conf = _to_float_or_none(bpm_tuple[2])  # don't boolean-test it!
    except Exception:
        bpm = float(es.PercivalBpmEstimator()(audio))
        bpm_conf = None

    # Key
    key, scale, strength = es.KeyExtractor()(audio)
    camelot = CAMELOT.get(f"{key} {scale}", "Unknown")

    return {
        "file": os.path.basename(filepath),
        "bpm": round(bpm, 1),
        "bpm_confidence": (round(bpm_conf, 2) if isinstance(bpm_conf, float) else None),
        "key": key,
        "scale": scale,
        "camelot": camelot,
        "key_confidence": round(float(strength), 2),
    }

@app.post("/analyze/path")
def analyze_path(req: PathReq):
    abs_path = os.path.abspath(req.path)
    if not abs_path.startswith(os.path.abspath(SAFE_ROOT) + os.sep):
        raise HTTPException(status_code=400, detail="Path outside SAFE_ROOT")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        return analyze(abs_path, req.seconds)
    except HTTPException:
        raise
    except Exception as e:
        # Return a clean 500 with message instead of a stack trace
        raise HTTPException(status_code=500, detail=f"Analyzer error: {e}")
