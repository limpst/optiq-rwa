"""Static export of the dashboard: inline the /api/all bundle into static/index.html -> docs/index.html.

    PYTHONPATH=src python scripts/export_dashboard.py [--out docs/index.html]
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from optiq_rwa.dashboard.app import STATIC, build_bundle, full_document  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="docs/index.html")
a = ap.parse_args()
html = (STATIC / "index.html").read_text()
data = json.dumps(build_bundle(), default=str).replace("</", "<\\/")
marker = '<script id="data" type="application/json">'
if marker in html:
    pre, rest = html.split(marker, 1)
    _, post = rest.split("</script>", 1)
    html = pre + marker + data + "</script>" + post
else:
    html = html.replace("</head>", marker + data + "</script>\n</head>", 1)
out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(full_document(html))                      # browsable copy (docs/index.html, GitHub Pages)
# artifact: page without inline data + data.json beside it (published through the Artifact tool's `files`)
slim = pre + marker + "null" + "</script>" + post if marker in html else html
frag = out.with_name("artifact.html"); frag.write_text(slim)
(out.parent / "data.json").write_text(data.replace("<\\/", "</"))
print("wrote", out, f"{out.stat().st_size/1e6:.2f} MB;", frag, f"{frag.stat().st_size/1e6:.2f} MB; data.json {(out.parent / 'data.json').stat().st_size/1e6:.2f} MB")
