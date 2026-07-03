#!/usr/bin/env python3
"""render_interactive.py — flows.json -> self-contained living-doc HTML.

Each flow becomes one animated, narrated sequence diagram: participant lanes
(the graph communities the flow crosses), messages that light up one at a time
as a viewer presses Play or steps through, a plain-language narration panel,
and a "release" toggle that highlights the steps a merge added or changed.

Every page is fully self-contained (inline CSS + JS, no network, no build) so
it can be dropped straight onto GitHub Pages. An index.html links them by module.

Usage:
    python code2docs/render_interactive.py                 # render every flow
    python code2docs/render_interactive.py --only impacted.json   # only impacted flows + index
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import c2d_common as c2d


# ---------------------------------------------------------------------------
# Shared CSS + JS. Kept as plain strings (no .format) so the many CSS/JS braces
# need no escaping. Per-page data is injected via marker replacement.
# ---------------------------------------------------------------------------

PAGE_CSS = """
:root{
  --bg:#0f1420; --panel:#161d2e; --panel2:#1d2740; --line:#2c3550; --ink:#e8edf7;
  --muted:#93a1c4; --accent:#4f8cff; --accent2:#7c5cff; --new:#25c26e; --changed:#ffb020;
  --lane:#2a3350;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 70% -10%,#1a2440 0%,var(--bg) 55%);
  color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:1040px;margin:0 auto;padding:28px 20px 80px}
.top{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:4px}
.crumb{color:var(--muted);font-size:13px}
h1{font-size:26px;margin:6px 0 2px;letter-spacing:.2px}
.sub{color:var(--muted);margin:0 0 18px;font-size:14px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;
  background:var(--panel2);color:var(--muted);border:1px solid var(--line)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  box-shadow:0 10px 30px rgba(0,0,0,.25)}
.stage{padding:10px 8px 4px;overflow-x:auto}
svg{display:block;margin:0 auto;max-width:100%;height:auto}
.diagram text{fill:var(--ink);font:13px system-ui,Segoe UI,sans-serif}
.diagram .laneName{font-weight:600;font-size:13px}
.diagram .laneEmoji{font-size:18px}
.diagram .lifeline{stroke:var(--lane);stroke-width:2;stroke-dasharray:4 6}
.diagram .msg{stroke:var(--muted);stroke-width:2;opacity:.28;transition:.25s}
.diagram .msghead{fill:var(--muted);opacity:.28;transition:.25s}
.diagram .cap{fill:var(--muted);opacity:.30;font-size:12px;transition:.25s}
.diagram .laneBox{fill:var(--panel2);stroke:var(--line)}
.diagram .step.done .msg{opacity:.85;stroke:var(--ink)}
.diagram .step.done .msghead{opacity:.85;fill:var(--ink)}
.diagram .step.done .cap{opacity:.9;fill:var(--ink)}
.diagram .step.active .msg{opacity:1;stroke:var(--accent);stroke-width:3}
.diagram .step.active .msghead{opacity:1;fill:var(--accent)}
.diagram .step.active .cap{opacity:1;fill:var(--accent);font-weight:700}
.diagram .step.changed.show .msg{stroke:var(--changed)!important;opacity:1}
.diagram .step.changed.show .msghead{fill:var(--changed)!important;opacity:1}
.diagram .step.added.show .msg{stroke:var(--new)!important;opacity:1}
.diagram .step.added.show .msghead{fill:var(--new)!important;opacity:1}
.diagram .tag{font-size:10px;font-weight:700}
.diagram .tag.changed{fill:var(--changed)}
.diagram .tag.added{fill:var(--new)}
.narr{padding:16px 20px;border-top:1px solid var(--line);min-height:96px}
.narr .say{font-size:19px;margin:0 0 8px}
.narr .tech{font:12.5px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted);
  word-break:break-word}
.pills{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
.pill{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.pill.changed{color:var(--changed);border-color:var(--changed)}
.pill.added{color:var(--new);border-color:var(--new)}
.ctl{display:flex;align-items:center;gap:10px;padding:14px 20px;border-top:1px solid var(--line);
  flex-wrap:wrap}
button{background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:10px;
  padding:8px 14px;font-size:14px;cursor:pointer;transition:.15s}
button:hover{border-color:var(--accent);color:#fff}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
button:disabled{opacity:.4;cursor:default}
.counter{color:var(--muted);font-variant-numeric:tabular-nums;margin-left:auto}
.toggle{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:13px;cursor:pointer;user-select:none}
.toggle input{accent-color:var(--changed);width:16px;height:16px}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:14px 2px 0;color:var(--muted);font-size:12px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:middle}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-top:18px}
.flowcard{padding:18px;text-decoration:none;color:inherit;display:block}
.flowcard:hover{border-color:var(--accent)}
.flowcard h3{margin:0 0 6px;font-size:17px}
.flowcard p{margin:0 0 12px;color:var(--muted);font-size:13.5px;min-height:38px}
.flowcard .meta{color:var(--muted);font-size:12px}
.lanes-mini{margin-top:10px;font-size:16px;letter-spacing:2px}
.foot{margin-top:34px;color:var(--muted);font-size:12px;text-align:center}
"""


PLAYER_JS = r"""
(function(){
  var FLOW = window.__FLOW__, REL = window.__RELEASE__ || {};
  var steps = FLOW.steps, lanes = FLOW.actors;
  var svg = document.getElementById('diagram');
  var NS = 'http://www.w3.org/2000/svg';
  var laneGap = Math.max(150, Math.min(230, 820/Math.max(1,lanes.length-1)));
  var marginX = 90, topY = 30, headH = 46, firstY = headH + 46, stepGap = 46;
  var width = marginX*2 + (lanes.length-1)*laneGap;
  var height = firstY + steps.length*stepGap + 30;
  svg.setAttribute('viewBox','0 0 '+width+' '+height);
  svg.setAttribute('width', width); svg.setAttribute('height', height);
  function laneX(i){ return marginX + i*laneGap; }
  function el(tag, attrs, txt){ var e=document.createElementNS(NS,tag);
    for(var k in attrs) e.setAttribute(k, attrs[k]); if(txt!=null) e.textContent=txt; return e; }

  // arrowhead marker
  var defs = el('defs',{});
  ['muted','#4f8cff','#25c26e','#ffb020','#e8edf7'].forEach(function(c,i){
    var m = el('marker',{id:'ah'+i,markerWidth:9,markerHeight:9,refX:7,refY:3,orient:'auto',markerUnits:'userSpaceOnUse'});
    m.appendChild(el('path',{d:'M0,0 L7,3 L0,6 Z', fill: c==='muted'?'#93a1c4':c}));
    defs.appendChild(m);
  });
  svg.appendChild(defs);

  // lane headers + lifelines
  lanes.forEach(function(a,i){
    var x = laneX(i);
    var g = el('g',{class:'lane'});
    g.appendChild(el('rect',{class:'laneBox', x:x-64, y:topY, width:128, height:headH, rx:9}));
    g.appendChild(el('text',{class:'laneEmoji','text-anchor':'middle', x:x, y:topY+20}, a.emoji||''));
    var nm = el('text',{class:'laneName','text-anchor':'middle', x:x, y:topY+38}, a.name);
    g.appendChild(nm);
    g.appendChild(el('line',{class:'lifeline', x1:x, y1:topY+headH, x2:x, y2:height-16}));
    svg.appendChild(g);
  });

  // steps
  var stepEls = [];
  steps.forEach(function(s,i){
    var y = firstY + i*stepGap;
    var x1 = laneX(s.from), x2 = laneX(s.to);
    var g = el('g',{class:'step', 'data-i':i});
    var cls = classFor(i);
    if(cls) g.setAttribute('class','step '+cls);
    if(x1===x2){ // self message: little loop to the right
      var lx = x1, w=34;
      var p = el('path',{class:'msg', d:'M'+lx+','+y+' h'+w+' v14 h-'+w, fill:'none','marker-end':'url(#ah0)'});
      g.appendChild(p);
      g.appendChild(el('text',{class:'cap','text-anchor':'start', x:lx+w+8, y:y+10}, s.cap));
    } else {
      var dir = x2>x1?1:-1;
      g.appendChild(el('line',{class:'msg', x1:x1, y1:y, x2:x2-dir*7, y2:y, 'marker-end':'url(#ah0)'}));
      g.appendChild(el('text',{class:'cap','text-anchor':'middle', x:(x1+x2)/2, y:y-7}, s.cap));
    }
    if((REL.changedSteps||[]).indexOf(i)>=0) g.appendChild(el('text',{class:'tag changed', x:x2+10, y:y+4},'~ changed'));
    if((REL.addedSteps||[]).indexOf(i)>=0)   g.appendChild(el('text',{class:'tag added',   x:x2+10, y:y+4},'+ new in '+(REL.version||'')));
    svg.appendChild(g); stepEls.push(g);
  });

  function classFor(i){
    var c=[];
    if((REL.changedSteps||[]).indexOf(i)>=0) c.push('changed');
    if((REL.addedSteps||[]).indexOf(i)>=0) c.push('added');
    return c.join(' ');
  }

  // narration + controls
  var say=document.getElementById('say'), tech=document.getElementById('tech'),
      pills=document.getElementById('pills'), counter=document.getElementById('counter'),
      btnPrev=document.getElementById('prev'), btnNext=document.getElementById('next'),
      btnPlay=document.getElementById('play'), btnReset=document.getElementById('reset'),
      relToggle=document.getElementById('relToggle');
  var cur=-1, timer=null;

  function render(){
    stepEls.forEach(function(g,i){
      g.classList.remove('active');
      var base='step '+classFor(i);
      g.setAttribute('class', base + (i<cur?' done':'') + (i===cur?' active':''));
      if(relToggle.checked) g.classList.add('show');
    });
    var s = steps[cur];
    if(s){ say.textContent = s.say || s.cap; tech.textContent = s.tech || ''; }
    else { say.textContent = FLOW.description || ('Press Play to walk through "'+FLOW.title+'".'); tech.textContent=''; }
    pills.innerHTML='';
    if((REL.addedSteps||[]).indexOf(cur)>=0)   addPill('added','+ new in '+(REL.version||''));
    if((REL.changedSteps||[]).indexOf(cur)>=0) addPill('changed','~ changed in '+(REL.version||''));
    counter.textContent = (cur<0?0:cur+1)+' / '+steps.length;
    btnPrev.disabled = cur<0; btnNext.disabled = cur>=steps.length-1;
  }
  function addPill(kind,txt){ var p=document.createElement('span'); p.className='pill '+kind; p.textContent=txt; pills.appendChild(p); }
  function go(i){ cur=Math.max(-1,Math.min(steps.length-1,i)); render(); }
  function next(){ if(cur<steps.length-1) go(cur+1); else stop(); }
  function play(){ if(timer){stop();return;} if(cur>=steps.length-1) cur=-1;
    btnPlay.textContent='⏸ Pause'; btnPlay.classList.add('primary');
    timer=setInterval(function(){ if(cur>=steps.length-1){stop();return;} go(cur+1); },1100); next(); }
  function stop(){ if(timer)clearInterval(timer); timer=null; btnPlay.textContent='▶ Play'; btnPlay.classList.remove('primary'); }

  btnPrev.onclick=function(){stop();go(cur-1);};
  btnNext.onclick=function(){stop();next();};
  btnPlay.onclick=play;
  btnReset.onclick=function(){stop();go(-1);};
  relToggle.onchange=render;
  document.addEventListener('keydown',function(e){
    if(e.key==='ArrowRight'){stop();next();} else if(e.key==='ArrowLeft'){stop();go(cur-1);}
    else if(e.key===' '){e.preventDefault();play();}
  });
  render();
})();
"""


def _release_for(flow: dict, version: str) -> dict:
    """Extract the release-highlight descriptor from a flow (set by the update
    path), SCOPED to `version`. changedSteps / addedSteps are the indices of the
    steps that arrived or changed in the current release only, so a highlight
    from an earlier release no longer lights up. version is the tag."""
    changed, added = [], []
    for i, s in enumerate(flow.get("steps", [])):
        if c2d.step_changed_in(s, version):
            changed.append(i)
        if c2d.step_new_in(s, version):
            added.append(i)
    rel = dict(flow.get("release", {}))
    rel["changedSteps"] = changed
    rel["addedSteps"] = added
    rel.setdefault("version", version)
    return rel


def render_flow_page(flow: dict, doc: dict) -> str:
    sv = c2d.short_version(doc.get("version", ""))
    rel_desc = _release_for(flow, sv)
    data = json.dumps(flow, ensure_ascii=False)
    rel = json.dumps(rel_desc, ensure_ascii=False)
    title = html.escape(flow.get("title", flow["id"]))
    module = html.escape(flow.get("module", doc.get("module", "")))
    version = html.escape(doc.get("version", ""))
    desc = html.escape(flow.get("description", ""))
    changed_count = len(rel_desc.get("changedSteps", [])) + len(rel_desc.get("addedSteps", []))
    rel_label = (f"Highlight what changed in v{version}"
                 if changed_count else "No release changes recorded")
    rel_disabled = "" if changed_count else "disabled"

    tpl = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · Living Doc</title><style>__CSS__</style></head>
<body><div class="wrap">
  <div class="crumb"><a href="index.html">&larr; All flows</a></div>
  <div class="top"><h1>__TITLE__</h1><span class="badge">__MODULE__</span><span class="badge">v__VERSION__</span></div>
  <p class="sub">__DESC__</p>
  <div class="card">
    <div class="stage"><svg id="diagram" class="diagram" role="img" aria-label="__TITLE__ sequence"></svg></div>
    <div class="narr"><p class="say" id="say"></p><div class="tech" id="tech"></div><div class="pills" id="pills"></div></div>
    <div class="ctl">
      <button id="reset" title="Restart">⟲</button>
      <button id="prev">‹ Prev</button>
      <button id="play" class="primary">▶ Play</button>
      <button id="next">Next ›</button>
      <label class="toggle"><input type="checkbox" id="relToggle" __RELDIS__>__RELLABEL__</label>
      <span class="counter" id="counter"></span>
    </div>
  </div>
  <div class="legend">
    <span><span class="dot" style="background:#4f8cff"></span>current step</span>
    <span><span class="dot" style="background:#25c26e"></span>new this release</span>
    <span><span class="dot" style="background:#ffb020"></span>changed this release</span>
    <span>← / → step · space to play</span>
  </div>
  <p class="foot">Generated by Code2Docs from the code graph · nothing here was hand-written.</p>
</div>
<script>window.__FLOW__=__DATA__;window.__RELEASE__=__REL__;</script>
<script>__JS__</script>
</body></html>"""
    return (tpl
            .replace("__CSS__", PAGE_CSS)
            .replace("__JS__", PLAYER_JS)
            .replace("__DATA__", data)
            .replace("__REL__", rel)
            .replace("__TITLE__", title)
            .replace("__MODULE__", module)
            .replace("__VERSION__", version)
            .replace("__DESC__", desc or f"An automatically narrated walkthrough of “{title}”.")
            .replace("__RELDIS__", rel_disabled)
            .replace("__RELLABEL__", html.escape(rel_label)))


def render_index(doc: dict, flows: list[dict]) -> str:
    module = html.escape(doc.get("module", "Module"))
    version = html.escape(doc.get("version", ""))
    sv = c2d.short_version(doc.get("version", ""))
    cards = []
    for f in flows:
        title = html.escape(f.get("title", f["id"]))
        desc = html.escape(f.get("description", "")) or \
            f"{len(f['steps'])} steps across {len(f['actors'])-1} components."
        lanes = "".join(a.get("emoji", "") for a in f.get("actors", []))
        rel_desc = _release_for(f, sv)
        n_changed = len(rel_desc.get("changedSteps", [])) + len(rel_desc.get("addedSteps", []))
        chg = f'<span class="badge" style="border-color:#ffb020;color:#ffb020">{n_changed} changed</span>' if n_changed else ""
        cards.append(f"""<a class="card flowcard" href="{f['id']}.html">
          <h3>{title}</h3><p>{desc}</p>
          <div class="lanes-mini">{lanes}</div>
          <div class="meta">{len(f['steps'])} steps · {len(f['actors'])-1} components {chg}</div></a>""")
    tpl = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__MODULE__ · Living Docs</title><style>__CSS__</style></head>
<body><div class="wrap">
  <div class="crumb">Code2Docs · Interactive Living Docs</div>
  <div class="top"><h1>__MODULE__</h1><span class="badge">v__VERSION__</span></div>
  <p class="sub">Playable, narrated walkthroughs generated from the code graph. Pick a flow to watch it step through in plain language.</p>
  <div class="grid">__CARDS__</div>
  <p class="foot">__COUNT__ flows · generated by Code2Docs · source of truth is graphify-out/graph.json</p>
</div></body></html>"""
    return (tpl
            .replace("__CSS__", PAGE_CSS)
            .replace("__MODULE__", module)
            .replace("__VERSION__", version)
            .replace("__CARDS__", "\n".join(cards))
            .replace("__COUNT__", str(len(flows))))


def main():
    ap = argparse.ArgumentParser(description="Render flows.json to interactive living docs.")
    ap.add_argument("--config", default=None)
    ap.add_argument("--flows", default=None, help="override flows.json path")
    ap.add_argument("--only", default=None, help="impacted.json: render only these flow ids (+ index)")
    ap.add_argument("--out", default=None, help="override output dir")
    args = ap.parse_args()

    c2d.init_io()
    cfg = c2d.load_config(args.config)
    flows_path = Path(args.flows) if args.flows else c2d._abs(cfg["flows_path"])
    doc = json.loads(flows_path.read_text(encoding="utf-8"))
    all_flows = doc.get("flows", [])

    only_ids = None
    if args.only:
        impacted = json.loads(Path(args.only).read_text(encoding="utf-8"))
        only_ids = set(impacted.get("flows", []))

    out_dir = Path(args.out) if args.out else c2d._abs(cfg["interactive_out"])
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered = []
    for f in all_flows:
        if only_ids is not None and f["id"] not in only_ids:
            continue
        (out_dir / f"{f['id']}.html").write_text(render_flow_page(f, doc), encoding="utf-8")
        rendered.append(f["id"])

    # Index always lists the full flow set so navigation stays complete.
    (out_dir / "index.html").write_text(render_index(doc, all_flows), encoding="utf-8")

    scope = "all" if only_ids is None else f"{len(rendered)} impacted"
    print(f"Rendered {scope} flow page(s) -> {out_dir}")
    for fid in rendered:
        print(f"  - {fid}.html")
    print(f"  - index.html ({len(all_flows)} flows)")


if __name__ == "__main__":
    main()
