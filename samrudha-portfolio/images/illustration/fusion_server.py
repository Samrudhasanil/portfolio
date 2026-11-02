"""
AVAL fusion server — runs entirely on your own machine.

PUT THIS FILE IN YOUR FUSION PROJECT FOLDER, next to your existing app.py and the
services/ folder (C:\\...\\domestic_violence_fusion), then run:

    python fusion_server.py

It reuses your services exactly as they are:
    services.text_service.predict_text(text)
    services.image_service.predict_image(path)
    services.video_service.predict_video(path)
    services.audio_service.predict_audio(path)     (optional)
each returning {"prediction": 0|1, "confidence": float, ...}   (1 = threat)

Any subset of inputs works. Privacy: nothing is sent anywhere; uploaded files are written to a
temporary folder and deleted as soon as the analysis finishes; message text is never logged.
"""
import importlib
import json
import os
import re
import sys
import tempfile
import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Behave exactly like running your app.py from this folder (relative model paths keep working).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ALERT_LOG = os.path.join(BASE_DIR, "alerts.log")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB per request (videos)

# CORS: any port on localhost or a private LAN address by default.
# Override with AVAL_CORS_ORIGINS="*" or a comma-separated list of exact origins.
_origins = os.environ.get("AVAL_CORS_ORIGINS", "").strip()
if _origins == "*":
    _cors_origins = "*"
elif _origins:
    _cors_origins = [o.strip() for o in _origins.split(",")]
else:
    _cors_origins = [re.compile(
        r"^http://(localhost|127\.0\.0\.1|10(\.\d{1,3}){3}|192\.168(\.\d{1,3}){2}|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2})(:\d+)?$"
    )]
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})

# ---------------------------------------------------------------- load your services
SERVICE_SPECS = {
    "text": ("services.text_service", "predict_text"),
    "image": ("services.image_service", "predict_image"),
    "video": ("services.video_service", "predict_video"),
    "audio": ("services.audio_service", "predict_audio"),
}
PREDICTORS = {}
LOAD_ERRORS = {}

print("\n[AVAL Fusion] Loading services (this can take a while for TensorFlow/PyTorch)...")
for _name, (_mod, _fn) in SERVICE_SPECS.items():
    try:
        PREDICTORS[_name] = getattr(importlib.import_module(_mod), _fn)
        print(f"[AVAL Fusion]   {_name:5} OK")
    except Exception as e:  # keep the server up with whatever loads
        LOAD_ERRORS[_name] = f"{type(e).__name__}: {e}"
        print(f"[AVAL Fusion]   {_name:5} NOT LOADED -> {LOAD_ERRORS[_name]}")
print("[AVAL Fusion] Ready.\n")

_predict_lock = threading.Lock()  # keras/torch models are not safe to call concurrently

# ---------------------------------------------------------------- text safety rules
# Escalate-only: these can raise a text result to "threat" but never lower a model's verdict.
THREAT_PHRASES = [
    "kollum", "kolla", "chavum", "vettum", "kill", "die", "murder", "stab", "slaughter",
    "jeevan edukkum", "adikkunnu", "adichu kollum", "kollaam ninne", "kill you",
]
THREAT_RE = re.compile(r"\b(?:" + "|".join(re.escape(p) for p in THREAT_PHRASES) + r")\b", re.IGNORECASE)

ALLOWED_EXT = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"},
    "video": {".mp4", ".avi", ".mov", ".mkv", ".webm", ".3gp", ".m4v"},
    "audio": {".wav", ".mp3", ".m4a", ".ogg", ".aac", ".flac", ".opus", ".3gp"},
}
RESPONSE_LIST_KEY = {
    "text": "text_predictions",
    "image": "image_predictions",
    "video": "video_predictions",
    "audio": "voice_predictions",  # the Android app calls audio "voice"
}
NICE = {"text": "Text", "image": "Image", "video": "Video", "audio": "Audio"}


# ---------------------------------------------------------------- helpers
def _clean(o):
    """Make numpy/torch scalars JSON-safe."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item") and callable(o.item):
        try:
            return o.item()
        except Exception:
            return str(o)
    return o


def _is_threat(pred):
    return pred == 1 or pred == "1" or pred is True


def _threat_probability(raw):
    """Probability of 'threat', assuming `confidence` is confidence in the predicted class."""
    conf = raw.get("confidence")
    if conf is None:
        return 1.0 if _is_threat(raw.get("prediction")) else 0.0
    conf = max(0.0, min(1.0, float(conf)))
    return conf if _is_threat(raw.get("prediction")) else 1.0 - conf


def _run(modality, arg):
    fn = PREDICTORS.get(modality)
    if fn is None:
        raise RuntimeError(f"{modality} service not loaded ({LOAD_ERRORS.get(modality, 'not found')})")
    with _predict_lock:
        res = fn(arg)
    if not isinstance(res, dict) or "prediction" not in res:
        raise ValueError("unexpected output from service (needs a dict with 'prediction')")
    return _clean(res)


def _analyze_text(text):
    """Returns (raw_result_or_None, error_or_None) with the escalate-only keyword rules applied."""
    raw, err = None, None
    try:
        raw = _run("text", text)
    except Exception as e:
        err = f"text analysis failed ({type(e).__name__})"
        print(f"[AVAL Fusion] text error: {type(e).__name__}: {e}")
    if THREAT_RE.search(text) and (raw is None or not _is_threat(raw.get("prediction"))):
        raw = {"prediction": 1, "confidence": 0.95, "raw_label": "Severe Threat (keyword rule)"}
        err = None
    return raw, err


def _item(modality, raw):
    flagged = _is_threat(raw.get("prediction"))
    risk = _threat_probability(raw)
    conf = raw.get("confidence")
    detail = "Threat indicators detected." if flagged else "No threat indicators detected."
    if conf is not None:
        detail += f" Model confidence {float(conf) * 100:.1f}%."
    if raw.get("raw_label"):
        detail += f" Label: {raw['raw_label']}."
    return {
        "label": f"{NICE[modality]}: " + ("threat indicators" if flagged else "no threat indicators"),
        "confidence": float(conf) if conf is not None else None,
        "riskScore": round(risk, 4),
        "flagged": flagged,
        "severity": "low" if not flagged else ("high" if risk >= 0.8 else "medium"),
        "detail": detail,
    }


def _overall(raw_results):
    """Your original fusion rule, unchanged. Returns your label."""
    threat_scores, confidences = [], []
    for res in raw_results.values():
        threat_scores.append(1 if _is_threat(res.get("prediction")) else 0)
        if res.get("confidence") is not None:
            confidences.append(float(res["confidence"]))
    label = "LOW RISK"
    if threat_scores:
        ratio = sum(threat_scores) / len(threat_scores)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        if ratio >= 0.5 and avg_conf > 0.6:
            label = "HIGH EMERGENCY"
        elif ratio > 0:
            label = "MODERATE WARNING"
    return label


def _level(label, flagged_count):
    if label == "HIGH EMERGENCY":
        return "CRITICAL" if flagged_count >= 3 else "HIGH"
    if label == "MODERATE WARNING":
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------- routes
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "modelLoaded": "text" in PREDICTORS,
        "services": {m: (m in PREDICTORS) for m in SERVICE_SPECS},
        "loadErrors": LOAD_ERRORS,
    })


@app.post("/api/fusion")
def fusion():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        text = str(data.get("text") or data.get("message") or "").strip()
        uploads = {}
    else:
        text = (request.form.get("text") or request.form.get("message") or "").strip()
        uploads = {
            "image": request.files.get("image"),
            "video": request.files.get("video"),
            "audio": request.files.get("audio") or request.files.get("voice"),
        }
        uploads = {k: f for k, f in uploads.items() if f is not None and f.filename}

    if not text and not uploads:
        return jsonify({"status": "error", "error": "Send 'text' and/or an image, video or audio file."}), 400

    raw_results, errors = {}, {}

    if text:
        raw, err = _analyze_text(text)
        if raw is not None:
            raw_results["text"] = raw
        if err:
            errors["text"] = err

    # Files live only inside this temp folder and are deleted when the block exits.
    with tempfile.TemporaryDirectory(prefix="aval_") as tmp:
        for modality, f in uploads.items():
            ext = os.path.splitext(secure_filename(f.filename))[1].lower()
            if ext not in ALLOWED_EXT[modality]:
                errors[modality] = f"unsupported {modality} file type '{ext or 'none'}'"
                continue
            path = os.path.join(tmp, f"{modality}{ext}")
            try:
                f.save(path)
                raw_results[modality] = _run(modality, path)
            except Exception as e:
                errors[modality] = f"{modality} analysis failed ({type(e).__name__})"
                print(f"[AVAL Fusion] {modality} error: {type(e).__name__}: {e}")

    if not raw_results:
        return jsonify({"status": "error", "error": "No modality could be analyzed.", "errors": errors}), 500

    label = _overall(raw_results)
    flagged_count = sum(1 for r in raw_results.values() if _is_threat(r.get("prediction")))
    analyzed = len(raw_results)
    level = _level(label, flagged_count)

    body = {
        "status": "success",
        "overall_risk_level": level,
        "overall_risk_label": label,
        "triggers_alert_suggestion": label == "HIGH EMERGENCY",
        "flagged_modalities_count": flagged_count,
        "modalities_analyzed": analyzed,
        "summary": f"{flagged_count} of {analyzed} analyzed modalit{'y' if analyzed == 1 else 'ies'} flagged. Overall risk: {level}.",
        "fusion_results": raw_results,
        "errors": errors,
    }
    for modality, key in RESPONSE_LIST_KEY.items():
        body[key] = [_item(modality, raw_results[modality])] if modality in raw_results else []
    return jsonify(body)


@app.post("/api/predict")
def predict_text_only():
    """Backwards-compatible text-only endpoint (the earlier AVAL app used this one)."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("message", "")).strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400
    raw, err = _analyze_text(text)
    if raw is None:
        return jsonify({"error": err or "text model unavailable"}), 500
    item = _item("text", raw)
    risk = item["riskScore"]
    return jsonify({
        "message": text,
        "category": raw.get("raw_label") or ("Threat" if item["flagged"] else "Safe / Non-Threat"),
        "riskScore": risk,
        "riskPercentage": int(risk * 100),
        "isAlert": item["flagged"],
        "modelLoaded": True,
    })


@app.post("/api/alert")
def alert():
    """Logs SOS / suggested alerts locally. Plug an SMS/WhatsApp provider in at the marked spot."""
    data = request.get_json(silent=True) or {}
    record = {
        "receivedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "payload": data.get("payload"),
        "mode": data.get("mode"),
        "location": data.get("location"),
        "contacts": data.get("contacts", []),
    }
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    # >>> send SMS/WhatsApp to record["contacts"] with your provider here <<<
    return jsonify({"status": "received", "delivered": False, "note": "Logged locally; no SMS provider configured."})


if __name__ == "__main__":
    # Local-only by default (privacy). For a real phone on your Wi-Fi: set AVAL_HOST=0.0.0.0
    host = os.environ.get("AVAL_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"  # never on 0.0.0.0: exposes the Werkzeug debugger
    app.run(host=host, port=5000, debug=debug, threaded=True, use_reloader=False)
