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
    page.evaluate("() => {window.overlayLabels=[];const original=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(text,...args){overlayLabels.push(String(text));return original.call(this,text,...args)};}")
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
    # Blank floor and a near-base miss must leave the selection unchanged.
    for x,y in [(35,35),(105,73)]:
        tap(x,y)
        assert 'No miniature base' in page.locator('.rt-status').inner_text()
        assert page.locator('select[aria-label="Operative to identify"]').input_value()=='n:a'
        assert page.get_by_text('Confirm Operative Positions',exact=True).count()==0
    # Tap off-centre but within the actual base; rendered ring must fit the base.
    page.evaluate("() => {window.rings=[];const arc=CanvasRenderingContext2D.prototype.arc;CanvasRenderingContext2D.prototype.arc=function(x,y,r,...args){rings.push([x,y,r]);return arc.call(this,x,y,r,...args)};}")
    tap(97,75)
    assert page.locator('select[aria-label="Operative to identify"]').input_value()=='p:b'
    assert page.evaluate("rings.some(([x,y,r])=>Math.abs(x-186)<3&&Math.abs(y-107)<3&&r>=15&&r<=21)")
    tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Assess Battlefield",exact=True).click()
    page.get_by_text("Resolve Shoot",exact=True).click()
    assert page.evaluate("window.accepted.id")=="shoot"
    assert page.evaluate("window.accepted.target")=="p:b"
    assert page.evaluate("window.accepted.movementConfirmed") is False
    assert '2 AP available' in page.locator('.rt-recommendation').inner_text()
    assert '1 AP remaining after' in page.locator('.rt-recommendation').inner_text()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.evaluate("TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    # Repeat photo: skip crop and review, show the action and target.
    page.get_by_text("Resolve Shoot",exact=True).wait_for()
    assert page.get_by_text("Confirm Board Area",exact=True).count()==0
    assert page.get_by_text("Review Terrain & Assess",exact=True).count()==0
    assert page.locator('.rt-recommendation').is_visible()
    for value in ['Warrior','Shoot','Gunner','Tactical Intent']:
        assert value in page.locator('.rt-recommendation').inner_text()
    page.get_by_text("Review / Correct Models",exact=True).click()
    assert page.locator('select[aria-label="Operative to identify"]').count()==1
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.get_by_text("Resolve Shoot",exact=True).wait_for()
    page.get_by_text("Review Mission Layout",exact=True).click()
    assert page.locator(".rt-check input").is_checked()
    page.get_by_text("Assess Battlefield",exact=True).click()
    page.get_by_text("Resolve Shoot",exact=True).wait_for()
    page.get_by_text("Use Manual Guide",exact=True).click()
    assert page.evaluate("window.manual")
    page.evaluate("reconConfig={...reconConfig,token:{},turn:0,setup:true,complete:()=>{window.setupDone=true}};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text("Confirm Board Area",exact=True).click()
    tap(93,73);tap(150,73)
    assert page.get_by_text('Current tabletop order',exact=True).count()==0
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Finish Recon Setup",exact=True).click()
    assert page.evaluate("window.setupDone===true")
    # A real mission ID loads a geometry overlay rather than manual marking controls.
    page.evaluate("reconConfig={...reconConfig,token:{},missionNumber:'01'};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text('Confirm Board Area',exact=True).click()
    page.get_by_text('Confirm Mission Layout',exact=True).wait_for()
    assert page.get_by_text('Mark Wall',exact=True).count()==0
    assert page.get_by_text('Mark Objective',exact=True).count()==0
    assert page.get_by_text('Review Player Orders',exact=True).count()==0
    assert page.locator('.rt-check input').count()==0
    assert page.get_by_text('Adjust mission alignment',exact=True).count()==0
    assert page.get_by_text('Rotate Mission Layout 90°',exact=True).count()==1
    assert page.get_by_text('Auto-align Mission Layout',exact=True).count()==1
    # Drag a mission corner and then translate the whole overlay on the photo.
    import json
    # Reset the synthetic image's auto-alignment to a deterministic, in-frame fit.
    page.get_by_text('Rotate Mission Layout 90°',exact=True).click()
    canvas.scroll_into_view_if_needed()
    def handles():
        return json.loads(canvas.get_attribute("data-alignment-handles"))
    def drag_map(x,y,dx,dy):
        box=canvas.bounding_box()
        size=canvas.evaluate("(el)=>[el.width,el.height]")
        px=box["x"]+box["width"]*x/size[0]
        py=box["y"]+box["height"]*y/size[1]
        page.mouse.move(px,py);page.mouse.down()
        page.mouse.move(px+box["width"]*dx/size[0],py+box["height"]*dy/size[1],steps=6);page.mouse.up()
    before=handles()
    assert len(before)==4 and canvas.evaluate("(el)=>getComputedStyle(el).touchAction")=="none"
    canvas.scroll_into_view_if_needed()
    drag_map(before[0][1],before[0][2],35,25)
    resized=handles()
    assert resized[0][1]>before[0][1] and resized[0][2]>before[0][2], (before,resized,canvas.bounding_box())
    assert abs(resized[2][1]-before[2][1])<1 and abs(resized[2][2]-before[2][2])<1
    assert page.locator('.rt-check input').count()==0
    cx=(resized[0][1]+resized[2][1])/2;cy=(resized[0][2]+resized[2][2])/2
    drag_map(cx,cy,20,10)
    translated=handles()
    assert translated[0][1]>resized[0][1] and translated[0][2]>resized[0][2]
    assert page.locator('.rt-check input').count()==0
    # Confirmation is one click after adjustment, with no redundant checkbox.
    assert page.get_by_text("Adjust mission alignment",exact=True).count()==0
    assert page.get_by_text("← Left",exact=True).count()==0
    page.get_by_text('Confirm Mission Layout',exact=True).click()
    assert page.locator('select[aria-label="Operative to identify"]').count()==1
    # A blocked assessment must explain its cause and allow direct roster correction.
    page.evaluate("reconConfig={...reconConfig,token:{},setup:false,turn:1,missionNumber:null,actionOrder:()=>['Overcharge']};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text("Confirm Board Area",exact=True).click()
    tap(93,73);tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Assess Battlefield",exact=True).click()
    assert "Overcharge requires a tabletop rules check" in page.locator(".rt-plan").inner_text()
    assert page.get_by_text("Resolve Shoot",exact=True).count()==0
    page.get_by_text("Review Operative Positions",exact=True).click()
    assert page.locator('select[aria-label="Operative to identify"]').count()==1
    # Both planned moves are displayed and submitted by one confirmation.
    page.evaluate("reconConfig={...reconConfig,token:{},setup:false,turn:1,missionNumber:null,actorKey:null,actionOrder:(m,c,planned=[])=>['Reposition','Dash'].filter(x=>!planned.includes(x.toLowerCase())),models:reconConfig.models.map(m=>m.side==='npo'?{...m,canShoot:false,focus:'fight',move:2,ap:2}:m)};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text("Confirm Board Area",exact=True).click()
    tap(93,73);tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Assess Battlefield",exact=True).click()
    page.get_by_text("Confirm Activation",exact=True).wait_for()
    assert '1 AP remaining after' in page.locator('.rt-recommendation').inner_text()
    assert 'Next planned action: Dash' in page.locator('.rt-recommendation').inner_text()
    assert page.evaluate("['1 ACTING NPO','2 MOVE HERE','3 DASH HERE'].every(label=>overlayLabels.includes(label))")
    page.get_by_text("Confirm Activation",exact=True).click()
    assert page.evaluate("window.accepted.movementConfirmed") is True
    assert page.evaluate("window.accepted.id")=="reposition"
    assert page.evaluate("window.accepted.confirmedFollowUp.id")=="dash"
    # Same photograph, confirmed position, only the remaining action.
    page.evaluate("reconConfig={...reconConfig,actorKey:'n:a',reusePrevious:true,completedActionIds:['reposition'],completedActions:['Reposition'],startingAp:2,models:reconConfig.models.map(m=>m.side==='npo'?{...m,ap:1}:m),actionOrder:()=>['Dash']};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.get_by_text("Move Complete",exact=True).wait_for()
    assert 'same photograph' in page.locator('.rt-status').inner_text()
    assert '1 AP available' in page.locator('.rt-recommendation').inner_text()
    assert 'Final AP' in page.locator('.rt-recommendation').inner_text()
    assert page.get_by_text("Confirm Board Area",exact=True).count()==0
    assert page.evaluate("overlayLabels.includes('1 CONFIRMED NPO')")
    page.get_by_text("Move Complete",exact=True).click()
    assert page.evaluate("window.accepted.id")=="dash"
    # Move then Shoot: both routes/target appear in the original photo.
    page.evaluate("overlayLabels=[];reconConfig={...reconConfig,token:{},actorKey:null,reusePrevious:false,startingAp:null,completedActionIds:[],completedActions:[],models:reconConfig.models.map(m=>m.side==='npo'?{...m,ap:2,move:4,canShoot:true,range:4,focus:'shoot'}:m),actionOrder:(m,c,done=[])=>['Shoot','Reposition'].filter(x=>!done.includes(x.toLowerCase()))};TombWorldReconTracking.open(document.querySelector('#host'),reconConfig)")
    page.locator("input[aria-label='Choose tactical photo']").set_input_files({"name":"board.png","mimeType":"image/png","buffer":image()})
    page.get_by_text("Confirm Board Area",exact=True).click()
    tap(93,73);tap(150,73)
    page.get_by_text("Confirm Operative Positions",exact=True).click()
    page.locator(".rt-check input").check()
    page.get_by_text("Assess Battlefield",exact=True).click()
    page.get_by_text("Confirm Activation",exact=True).wait_for()
    assert 'Next planned action: Shoot' in page.locator('.rt-recommendation').inner_text()
    assert page.evaluate("['1 ACTING NPO','2 MOVE HERE','3 POTENTIAL TARGET'].every(label=>overlayLabels.includes(label))")
    page.get_by_text("Confirm Activation",exact=True).click()
    assert page.evaluate("window.accepted.confirmedFollowUp.id")=="shoot"
    assert page.get_by_text("Current tabletop order",exact=True).count()==0
    assert not errors,errors
    browser.close()
print("Tactical scan browser workflow passed.")
