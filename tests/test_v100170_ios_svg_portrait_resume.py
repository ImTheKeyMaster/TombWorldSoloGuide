"""Verify iOS foreground repaints external SVG portraits without resetting UI."""

from pathlib import Path
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def test_foreground_replaces_svg_images_once_and_skips_background():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const start=source.indexOf('  // iOS PWA resume can leave external SVG');
const end=source.indexOf('  function normalizeSarcophagusControllers(',start);
assert(start>0&&end>start,'resume hook is correctly scoped');
const listeners={}, windowListeners={}, replaced=[];
const timers=new Map();
let nextTimer=0, queries=0;
const createImage=id=>({
  id,
  href:'Assets/Images/TombUI/'+id+'.png',
  cloneNode(deep){assert.equal(deep,true);return {id:this.id,href:this.href,isClone:true};},
  replaceWith(next){replaced.push({old:this,next});}
});
const images=[createImage('confidant'),createImage('geomancer')];
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
  assert.equal(ms,100);
  const id=++nextTimer;
  timers.set(id,cb);
  return id;
};
const clearTimeout=id=>{timers.delete(id);};
const runTimer=()=>{
  const callbacks=[...timers.values()];
  timers.clear();
  callbacks.forEach(cb=>cb());
};
new Function('document','window','setTimeout','clearTimeout',
  source.slice(start,end)
)(document,window,setTimeout,clearTimeout);
assert.equal(typeof listeners.visibilitychange,'function');
assert.equal(typeof windowListeners.pageshow,'function');
assert.equal(typeof windowListeners.focus,'function');
listeners.visibilitychange();
windowListeners.focus();
assert.equal(timers.size,0,'nothing to repaint while app is hidden');
document.visibilityState='visible';
listeners.visibilitychange();
windowListeners.focus();
assert.equal(timers.size,1,'visibility and focus are coalesced');
runTimer();
assert.equal(queries,1);
assert.equal(replaced.length,2);
assert(replaced.every(x=>x.next.isClone&&x.next.href===x.old.href),
  'only original image data is re-instantiated');
windowListeners.pageshow({persisted:false});
assert.equal(timers.size,0,'normal page loads do not trigger extra work');
windowListeners.pageshow({persisted:true});
assert.equal(timers.size,1,'bfcache restores repaint image resources');
runTimer();
assert.equal(replaced.length,4);
windowListeners.focus();
document.visibilityState='hidden';
runTimer();
assert.equal(replaced.length,4,'if backgrounded before timeout no repaint');
assert.equal(queries,2);
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
