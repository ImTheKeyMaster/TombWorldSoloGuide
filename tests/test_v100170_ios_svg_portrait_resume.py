"""Verify iOS foreground repaints external SVG portraits without resetting UI."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_foreground_repaints_images_then_rebuilds_svg_roots_after_resume():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  // iOS standalone PWAs can restore the DOM');
const end=source.indexOf('  function normalizeSarcophagusControllers(',start);
assert(start>0&&end>start,'resume hook is correctly scoped');
const listeners={},windowListeners={},replaced=[],rootsReplaced=[];
const timers=new Map();
let nextTimer=0,queries=0;
const root=id=>({
  id,
  cloneNode(deep){assert.equal(deep,true);return {id,clone:true};},
  replaceWith(next){rootsReplaced.push({old:this,next});}
});
const sharedRoot=root('shared'),otherRoot=root('other');
const image=(id,svg)=>({
  id,
  href:'Assets/Images/TombUI/'+id+'.png',
  closest(selector){assert.equal(selector,'svg');return svg;},
  cloneNode(deep){assert.equal(deep,true);return {id,href:this.href,clone:true};},
  replaceWith(next){replaced.push({old:this,next});}
});
const images=[image('confidant',sharedRoot),image('plasma-gunner',sharedRoot),
  image('necron',otherRoot)];
const document={
  visibilityState:'hidden',
  addEventListener(type,cb){listeners[type]=cb;},
  querySelectorAll(selector){
    assert.equal(selector,'svg image[href]');
    queries++;
    return images;
  }
};
const window={addEventListener(type,cb){windowListeners[type]=cb;}};
const setTimeout=(cb,ms)=>{
  assert([100,1500].includes(ms));
  const id=++nextTimer;timers.set(id,{cb,ms});
  return id;
};
const clearTimeout=id=>{timers.delete(id);};
const runTimer=ms=>{
  const selected=[...timers.entries()].filter(([id,t])=>t.ms===ms);
  selected.forEach(([id])=>timers.delete(id));
  selected.forEach(([id,t])=>t.cb());
};
new Function('document','window','setTimeout','clearTimeout',
  source.slice(start,end)
)(document,window,setTimeout,clearTimeout);
assert.equal(typeof listeners.visibilitychange,'function');
assert.equal(typeof windowListeners.pageshow,'function');
assert.equal(typeof windowListeners.focus,'function');
assert.equal(typeof windowListeners.pagehide,'function');
listeners.visibilitychange();
windowListeners.focus();
assert.equal(timers.size,0,'nothing should repaint while hidden');
document.visibilityState='visible';
listeners.visibilitychange();
windowListeners.focus();
assert.equal(timers.size,2,'visibility and focus events must debounce both phases');
runTimer(100);
assert.equal(queries,1);
assert.equal(replaced.length,3,'first phase recreates SVG image resources');
assert(replaced.every(x=>x.next.clone&&x.next.href===x.old.href),
  'first phase preserves image URLs and attributes');
runTimer(1500);
assert.equal(queries,2);
assert.equal(rootsReplaced.length,2,'second phase rebuilds each unique SVG root once');
assert(rootsReplaced.every(x=>x.next.clone));
windowListeners.pageshow({persisted:false});
assert.equal(timers.size,0,'normal page loads do not reschedule');
windowListeners.pageshow({persisted:true});
assert.equal(timers.size,2,'BFCache restore retries both phases');
windowListeners.pagehide();
assert.equal(timers.size,0,'pagehide cancels pending repaint');
document.visibilityState='visible';
windowListeners.focus();
assert.equal(timers.size,2);
document.visibilityState='hidden';
listeners.visibilitychange();
assert.equal(timers.size,0,'backgrounding cancels both timers');
runTimer(100);runTimer(1500);
assert.equal(queries,2,'backgrounded pages do not repaint');
"""
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr or result.stdout

def test_restore_only_svg_image_nodes_and_preserve_gameplay():
    start = APP.index("  // iOS PWA resume can leave external SVG")
    end = APP.index("  function normalizeSarcophagusControllers(", start)
    code = APP[start:end]
    assert "querySelectorAll('svg image[href]')" in code
    assert "image.replaceWith(image.cloneNode(true))" in code
    assert "root.replaceWith(root.cloneNode(true))" in code
    assert "window.addEventListener('pagehide',cancelSvgPortraitRefresh)" in code
    assert "1500" in code
    assert "showModal(" not in code
    assert "save()" not in code
    assert "renderHumanPlayerActionPicker(" not in code
    assert "setAttribute('href'" not in code
    assert "window.addEventListener('orientationchange'" in APP


def test_release_and_pwa_cache_updated():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
