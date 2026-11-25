"""Synthetic-photo workflow through calibration, identity, terrain, decision and tracking."""
from pathlib import Path
import struct
import zlib
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def image():
    w=h=300
    rows=bytearray()
    for y in range(h):
        rows.append(0)
        for x in range(w):
            cx,cy=(100,100) if (x-100)**2+(y-100)**2<8**2 else ((150,100) if (x-150)**2+(y-100)**2<8**2 else (0,0))
            rows.extend((100+(x-cx)*8,100+(y-cy)*8,190) if cx else (30,30,30))
    def chunk(k,d):return struct.pack(">I",len(d))+k+d+struct.pack(">I",zlib.crc32(k+d))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(rows))+chunk(b"IEND",b"")

with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={"width":390,"height":844})
    errors=[]
    page.on("pageerror",lambda e: errors.append(str(e)))
    page.set_content('<html data-experimental="on"><body><div id="host"></div></body></html>')
    for f in ["styles.css","battlefield-recon.css","battlefield-tracking.css"]:page.add_style_tag(path=str(ROOT/f))
    page.add_script_tag(path=str(ROOT/"battlefield-tracking.js"))
    page.evaluate("""window.reconConfig={token:{},turn:1,scanKey:'1',activated:[],ready:['n:a'],models:[{key:'n:a',side:'npo',name:'Warrior',base:32,ready:true,move:6,ap:2,canShoot:true,range:12,focus:'shoot',wounds:9},{key:'p:b',side:'player',name:'Gunner',base:32,order:'Engage',wounds:5}],valid:()=>true,actionOrder:()=>['Shoot','Reposition'],manual:()=>{window.manual=true},accept:p=>{window.accepted=p}};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)""")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text('Confirm Board Area',exact=True).wait_for()
    canvas=page.locator("canvas")
    def tap(x,y):
        b=canvas.bounding_box()
        canvas.click(position={"x":b["width"]*x/300,"y":b["height"]*y/300})
    assert page.get_by_text("Width (in)",exact=True).count()==0
    assert page.get_by_text("Height (in)",exact=True).count()==0
    # Drag a corner inward, move the frame, then rotate twice to restore orientation.
    b=canvas.bounding_box()
    page.mouse.move(b["x"]+b["width"]*.06,b["y"]+b["height"]*.18)
    page.mouse.down()
    page.mouse.move(b["x"]+b["width"]*.08,b["y"]+b["height"]*.20,steps=5)
    page.mouse.up()
    # Reload the same fixture to restore the initial crop after exercising drag.
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text('Confirm Board Area',exact=True).wait_for()
    page.get_by_text("Confirm Board Area",exact=True).click()
    assert page.evaluate("document.querySelector('canvas').width===600&&document.querySelector('canvas').height===440")
    # Blank floor must not assign the first operative.
    tap(35,35)
    assert 'No distinct miniature' in page.locator('.rt-status').inner_text()
    assert page.locator('select[aria-label="Operative to identify"]').input_value()=='n:a'
    tap(93,73);tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Assess Battlefield",exact=True).click()
    page.get_by_text("Accept Tactical Recommendation",exact=True).click()
    assert page.evaluate("window.accepted.id")=="shoot"
    assert page.evaluate("window.accepted.target")=="p:b"
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.evaluate("TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text('Confirm Board Area',exact=True).click()
    page.wait_for_function("document.querySelector('.rt-status').textContent.includes('Positions tracked')||document.querySelector('.rt-status').textContent.includes('could not be tracked')")
    assert page.get_by_text("Review / Correct Models",exact=True).count() or page.get_by_text("Identify Missing Models",exact=True).count()
    page.get_by_text("Use Manual Guide",exact=True).click()
    assert page.evaluate("window.manual")
    page.evaluate("reconConfig={...reconConfig,token:{},turn:0,setup:true,complete:()=>{window.setupDone=true}};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text("Confirm Board Area",exact=True).click()
    tap(93,73);tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.get_by_text("Finish Recon Setup",exact=True).click()
    assert page.evaluate("window.setupDone===true")
    # A real mission ID loads a geometry overlay rather than manual marking controls.
    page.evaluate("reconConfig={...reconConfig,token:{},missionNumber:'01'};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text('Confirm Board Area',exact=True).click()
    page.get_by_text('Confirm Mission Layout',exact=True).wait_for()
    assert page.get_by_text('Mark Wall',exact=True).count()==0
    assert page.get_by_text('Mark Objective',exact=True).count()==0
    page.get_by_text('Confirm Mission Layout',exact=True).click()
    assert 'Confirm the overlay' in page.locator('.rt-status').inner_text()
    page.locator('.rt-check input').check()
    page.get_by_text('Confirm Mission Layout',exact=True).click()
    assert page.locator('select[aria-label="Operative to identify"]').count()==1
    assert not errors,errors
    browser.close()
print("Tactical scan browser workflow passed.")
