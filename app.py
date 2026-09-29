"""Greywater Testing Kit web app — stdlib only (+sklearn for model). Run: python3 app.py → http://localhost:8000"""
import json, pickle, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import pandas as pd

model = pickle.load(open("greywater_model.pkl", "rb"))
COLS = ["pH", "turbidity_NTU", "TDS_mgL", "microbial_present"]
LABELS = {0: ("SAFE — Garden/Irrigation", "green", "Water is suitable for gardening, irrigation and flushing."),
          1: ("CAUTION — Flushing Only", "orange", "Use only for toilet flushing. Not for plants/edibles."),
          2: ("UNSAFE — Do Not Reuse", "red", "Do not reuse. Discard safely or treat further.")}

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Greywater Testing Kit + AI</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem;background:#f4f7f5}h1{color:#1b5e20}.card{background:#fff;padding:1.5rem;border-radius:12px;box-shadow:0 2px 8px #0002}label{display:block;margin:.6rem 0 .2rem}input,select{width:100%;padding:.5rem;font-size:1rem}button{background:#1b5e20;color:#fff;border:0;padding:.7rem 1.2rem;font-size:1rem;border-radius:8px;margin-top:1rem;cursor:pointer}#res{margin-top:1rem;padding:1rem;border-radius:8px;font-weight:bold}.green{background:#e8f5e9;color:#1b5e20}.orange{background:#fff3e0;color:#e65100}.red{background:#ffebee;color:#b71c1c}.small{color:#666;font-size:.85rem}</style></head>
<body><h1>💧 Greywater Testing Kit + AI</h1>
<div class="card">
<p class="small">Decision-Tree model (90.7% test accuracy, 1500-sample dataset). Enter sensor/strip readings:</p>
<label>pH (4.5 – 9.5)</label><input id="ph" type="number" step="0.1" value="7.2">
<label>Turbidity (NTU)</label><input id="turb" type="number" step="0.1" value="5">
<label>TDS (mg/L)</label><input id="tds" type="number" step="1" value="320">
<label>Microbial present?</label><select id="mic"><option value="0">Absent / Negative</option><option value="1">Present / Positive</option></select>
<button onclick="go()">Analyze Water</button>
<div id="res"></div>
<p class="small">Thresholds: pH 6.0–8.5 · Turbidity &lt;10 garden, &lt;20 flushing · TDS &lt;500 garden, &lt;1000 flushing</p>
</div>
<script>async function go(){const b={pH:+ph.value,turbidity_NTU:+turb.value,TDS_mgL:+tds.value,microbial_present:+mic.value};
const r=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json());
const d=document.getElementById('res');d.className=r.color;d.innerHTML=r.label+'<br><span style="font-weight:normal">'+r.advice+'</span>';}</script>
</body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, body, ctype="text/html"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(200); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path in ("/", "/index.html"): self._send(HTML)
        elif self.path == "/api/stats":
            df = pd.read_csv("greywater_dataset.csv")
            self._send(json.dumps({"rows": len(df), "accuracy": 0.907, "dist": df["label_name"].value_counts().to_dict()}), "application/json")
        else: self.send_error(404)
    def do_POST(self):
        if self.path == "/api/predict":
            n = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(n) or b"{}")
            v = [[float(d.get("pH", 7)), float(d.get("turbidity_NTU", 5)), float(d.get("TDS_mgL", 300)), int(d.get("microbial_present", 0))]]
            p = int(model.predict(pd.DataFrame(v, columns=COLS))[0])
            label, color, advice = LABELS[p]
            self._send(json.dumps({"class": p, "label": label, "color": color, "advice": advice}), "application/json")
        else: self.send_error(404)

if __name__ == "__main__":
    print("Serving on http://localhost:8000"); HTTPServer(("0.0.0.0", 8000), H).serve_forever()
