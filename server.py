#!/usr/bin/env python3
"""HTTP layer over the capability manifests.

Both surfaces, one source. The browsable pages and the JSON API read the same
files in capabilities/, and the query logic is imported from tools/catalogue.py
rather than reimplemented here, so there is only one answer to "what does this
capability do".

Local:   python3 server.py          → http://localhost:8000
Railway: Procfile runs the same command; PORT comes from the environment.
"""
import importlib.util
import os
import pathlib

import markdown as md
import yaml
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route

ROOT = pathlib.Path(__file__).resolve().parent

# Import tools/catalogue.py by path — it is a script, not a package.
_spec = importlib.util.spec_from_file_location("catalogue", ROOT / "tools" / "catalogue.py")
catalogue = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(catalogue)

ORCHARDS = ["self-serve", "assisted", "business"]
MARKETS = ["DE", "UK", "ES"]

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f7f8f6;--card:#fff;--fg:#14201c;--soft:#3f504a;--faint:#6d7d77;
--rule:#d6dedа;--rule2:#c3ccc8;--accent:#0f6b52;--accentbg:#dcede6;--warn:#8a5612;--warnbg:#fbf0dd;
--mono:ui-monospace,SFMono-Regular,Menlo,monospace;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121715;--card:#1a211e;--fg:#e8eeea;--soft:#a3b0aa;
--faint:#7b8782;--rule:#2c3531;--rule2:#3d4844;--accent:#4fc39b;--accentbg:#17312a;
--warn:#d79a3c;--warnbg:#2e2718;color-scheme:dark}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif}}
.wrap{{max-width:900px;margin:0 auto;padding:32px 20px 72px}}
header{{border-bottom:1px solid var(--rule2);padding-bottom:18px;margin-bottom:28px}}
.eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;
color:var(--accent);margin:0 0 8px}}
h1{{font-size:30px;letter-spacing:-.02em;margin:0 0 6px;line-height:1.15}}
h2{{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);
margin:32px 0 10px;border-bottom:1px solid var(--rule);padding-bottom:6px}}
h3{{font-size:18px;margin:22px 0 8px}}
p,li{{color:var(--fg)}}
.lede{{color:var(--soft);margin:0;max-width:66ch}}
a{{color:var(--accent)}}
code,pre{{font-family:var(--mono);font-size:13px}}
pre{{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:14px;
overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0}}
th{{text-align:left;font-family:var(--mono);font-size:11px;letter-spacing:.07em;
text-transform:uppercase;color:var(--faint);font-weight:500;
border-bottom:1px solid var(--rule2);padding:7px 10px 7px 0}}
td{{padding:8px 10px 8px 0;border-bottom:1px solid var(--rule);vertical-align:top}}
.badge{{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:4px;
border:1px solid var(--rule2);color:var(--soft);background:var(--bg);white-space:nowrap}}
.badge.ok{{background:var(--accentbg);border-color:var(--accent);color:var(--accent)}}
.badge.warn{{background:var(--warnbg);border-color:var(--warn);color:var(--warn)}}
.card{{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:18px;
margin:14px 0}}
.note{{border-left:3px solid var(--warn);background:var(--warnbg);padding:12px 14px;
border-radius:0 8px 8px 0;margin:14px 0;font-size:14px}}
blockquote{{border-left:3px solid var(--accent);background:var(--accentbg);margin:14px 0;
padding:12px 14px;border-radius:0 8px 8px 0}}
blockquote p{{margin:0}}
.gen{{font-family:var(--mono);font-size:12px;color:var(--faint);margin-top:36px;
padding-top:14px;border-top:1px dashed var(--rule2)}}
.try{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.try a{{font-family:var(--mono);font-size:12.5px;background:var(--card);
border:1px solid var(--rule);border-radius:6px;padding:7px 11px;text-decoration:none}}
.try a:hover{{border-color:var(--accent)}}
</style></head><body><div class="wrap">{body}</div></body></html>"""


def load():
    return catalogue.load_all(ROOT / "capabilities")


def page(title, body):
    return HTMLResponse(PAGE.format(title=title, body=body))


async def index(request):
    docs = load()
    rows = []
    for d in docs:
        m, s = d["metadata"], d["spec"]
        cls = {"stable": "ok", "beta": "warn", "experimental": ""}[m["lifecycle"]]
        n = len({c["orchard"] for c in s["consumers"]})
        rows.append(
            f'<tr><td><a href="/c/{m["name"]}">{m.get("title", m["name"])}</a></td>'
            f'<td><code>{m["trunk"]}</code></td>'
            f'<td><span class="badge {cls}">{m["lifecycle"]}</span></td>'
            f'<td>{n}</td><td>{m["summary"].strip()}</td></tr>'
        )
    body = f"""<header>
<p class="eyebrow">Capability playbook</p>
<h1>What the platform already does</h1>
<p class="lede">One manifest per capability, living beside the code. This page and
the JSON API below are both generated from those files.</p>
</header>
<h2>Capabilities</h2>
<table><tr><th>Capability</th><th>Team</th><th>Status</th><th>Teams using it</th>
<th>Summary</th></tr>{''.join(rows)}</table>
<h2>The same data, for agents</h2>
<p class="lede">Every page here has a JSON equivalent. An agent asks the question a
builder would ask, and gets back what the manifest declares plus an honest label on
what the matcher guessed.</p>
<div class="try">
<a href="/api">/api</a>
<a href="/api/capabilities">/api/capabilities</a>
<a href="/api/search?q=extract+fields+from+an+invoice">/api/search?q=…</a>
<a href="/api/can-i?need=file+an+income+tax+return&amp;orchard=business&amp;market=DE">/api/can-i?…</a>
<a href="/api/can-i?need=file+a+VAT+advance+return&amp;orchard=business&amp;market=DE">/api/can-i (nothing matches)</a>
</div>
<div class="note"><strong>Prototype.</strong> Every accuracy, cost and throughput
figure in these manifests is invented and marked <code>ASSUMPTION</code>. The
structure is the point, not the numbers.</div>
<p class="gen">Generated from capabilities/*.yaml — edit the manifest, not the page.</p>"""
    return page("Capability playbook", body)


async def capability_page(request):
    name = request.path_params["name"]
    docs = load()
    hit = next((d for d in docs if d["metadata"]["name"] == name), None)
    if hit is None:
        return page("Not found", "<header><h1>No such capability</h1></header>"
                                 '<p><a href="/">Back to the catalogue</a></p>')
    source = ROOT / "docs" / f"{name}.md"
    if source.exists():
        inner = md.markdown(source.read_text(), extensions=["tables", "fenced_code"])
    else:
        inner = "<p>No rendered page yet. Run <code>python3 tools/render.py</code>.</p>"
    body = (f'<header><p class="eyebrow"><a href="/">&larr; Catalogue</a></p></header>'
            f'{inner}'
            f'<h2>The same capability, as JSON</h2><div class="try">'
            f'<a href="/api/capabilities/{name}">/api/capabilities/{name}</a>'
            f'<a href="/api/consumers-of/{name}">/api/consumers-of/{name}</a></div>')
    return page(hit["metadata"].get("title", name), body)


async def api_index(request):
    return JSONResponse({
        "service": "capability-playbook",
        "source": "capabilities/*.yaml — the manifests are the single source of truth",
        "human_surface": "/",
        "endpoints": {
            "GET /api/capabilities": "every capability, summarised",
            "GET /api/capabilities/{name}": "one full manifest",
            "GET /api/consumers-of/{name}": "which teams depend on it, and how critically",
            "GET /api/search?q=": "rank capabilities against a need (lexical, not semantic)",
            "GET /api/can-i?need=&orchard=&market=": (
                "the question a builder asks. Returns what the matcher GUESSED "
                "separately from what the manifest DECLARES."
            ),
        },
        "orchards": ORCHARDS,
        "markets": MARKETS,
    })


async def api_list(request):
    return JSONResponse([
        {
            "name": d["metadata"]["name"],
            "title": d["metadata"].get("title"),
            "trunk": d["metadata"]["trunk"],
            "lifecycle": d["metadata"]["lifecycle"],
            "summary": d["metadata"]["summary"].strip(),
            "orchards": sorted({c["orchard"] for c in d["spec"]["consumers"]}),
            "href": f"/api/capabilities/{d['metadata']['name']}",
        }
        for d in load()
    ])


async def api_one(request):
    out = catalogue.tool_describe(request.path_params["name"], load())
    return JSONResponse(out, status_code=404 if "error" in out else 200)


async def api_consumers(request):
    out = catalogue.tool_consumers_of(request.path_params["name"], load())
    return JSONResponse(out, status_code=404 if "error" in out else 200)


async def api_search(request):
    q = request.query_params.get("q", "").strip()
    if not q:
        return JSONResponse({"error": "pass ?q=<what you need>"}, status_code=400)
    return JSONResponse(catalogue.tool_search(q, load()))


async def api_can_i(request):
    p = request.query_params
    need, orchard, market = p.get("need", "").strip(), p.get("orchard"), p.get("market")
    if not need:
        return JSONResponse({"error": "pass ?need=<what you are trying to do>"},
                            status_code=400)
    if orchard not in ORCHARDS:
        return JSONResponse({"error": f"orchard must be one of {ORCHARDS}"},
                            status_code=400)
    if market not in MARKETS:
        return JSONResponse({"error": f"market must be one of {MARKETS}"},
                            status_code=400)
    return JSONResponse(catalogue.tool_can_i(need, orchard, market, load()))


async def healthz(request):
    try:
        n = len(load())
    except Exception as e:                                  # a broken manifest
        return JSONResponse({"ok": False, "error": str(e)}, status_code=503)
    return JSONResponse({"ok": True, "capabilities": n})


app = Starlette(routes=[
    Route("/", index),
    Route("/c/{name}", capability_page),
    Route("/api", api_index),
    Route("/api/capabilities", api_list),
    Route("/api/capabilities/{name}", api_one),
    Route("/api/consumers-of/{name}", api_consumers),
    Route("/api/search", api_search),
    Route("/api/can-i", api_can_i),
    Route("/healthz", healthz),
    Route("/favicon.ico", lambda r: RedirectResponse("/", status_code=302)),
])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
