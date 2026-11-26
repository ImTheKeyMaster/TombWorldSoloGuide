"""Actual application startup and Recon launch from a deployed solo roster.
Only the test server exposes a fixture hook; production app contains no test API."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"app.js").read_text()
hook=r"""
  window.__reconFixture={
    ready:()=>Boolean(playerManifest?.teams?.length&&missions?.length),
    prepare:async()=>{
      state=initialState();
      Object.assign(state,{gameMode:'solo',screen:'game',tab:'play',phase:'between',turningPoint:0,missionId:'shifting-labyrinth',playerTeamId:'deathwatch',playerTeamFile:'DeathWatch.json'});
      await loadPlayerTeamData('deathwatch');
      state.playerRoster=playerTeamData.operatives.slice(0,5).map(o=>o.id);
      state.playerCount=state.playerReady=state.playerRoster.length;
      initializePlayerWounds();
      state.roster.push(createNpo('Canoptek Macrocyte Warrior',undefined,{ready:false}));
      state.roster.push(createNpo('Canoptek Scarab Swarm',undefined,{ready:false}));
      state.roster.push(createNpo('Geomancer',undefined,{ready:false}));
      setExperimentalFeatures(true);
      render();
    },
    // Strategy fixture avoids dice and narration, exercising retry without advancing game state.
    strategy:()=>{Object.assign(state,{turningPoint:1,phase:'strategy',strategyStage:'summary',strategyData:{viewStep:'actions',reinforcements:[],grade:0},strategyPipeline:{current:'complete',completed:['ready','initiative','event','reinforcement']}});render();},
    state:()=>({phase:state.phase,turn:state.turningPoint,players:state.playerRoster.length,npos:state.roster.length}),
    launch:()=>showReconTracking(null,true),
    prepareMovement:()=>{
      closeModal();
      state.phase='firefight';state.nextSide='npo';state.turningPoint=1;
      const n=createNpo('Necron Warrior',undefined,{ready:true});
      n.ready=true;n.deployed=true;n.battlefieldState='deployed';n.dormant=false;
      state.roster=[n];state.activeNpoId=null;state.lastActivation=null;
      render();
      const original=window.TombWorldReconTracking.open;
      window.TombWorldReconTracking.open=(host,config)=>{window.__reconConfig=config;original(host,config);};
      showReconTracking();
      return n.id;
    },
    confirmMove:(kind='dash',followKind=null)=>{
      const c=window.__reconConfig,m=c.models.find(m=>m.side==='npo');
      const action=c.actionOrder(m,false).find(x=>npoActionId(x)===kind);
      if(!action)throw Error('No action '+kind);
      const next=followKind?c.actionOrder({...m,ap:m.ap-1},false,[kind]).find(x=>npoActionId(x)===followKind):null;
      if(followKind&&!next)throw Error('Missing follow-up '+followKind);
      c.accept({actor:m.key,action,id:kind,inControl:false,shootable:false,fightable:false,movementConfirmed:true,confirmedFollowUp:next?{actor:m.key,id:followKind,action:next,inControl:false,shootable:false,fightable:false}:null});
    },
    ap:()=>({id:state.activeNpoId,remaining:state.lastActivation?.remainingAp,completed:state.lastActivation?.completedActionIds,committed:state.lastActivation?.committed})
  };
"""
assert source.rstrip().endswith("})();")
patched=source.rstrip()[:-5]+hook+"})();\n"
server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={"width":390,"height":844},has_touch=True,service_workers="block")
        page.route("**/app.js?*",lambda route:route.fulfill(status=200,content_type="application/javascript",body=patched))
        page.route("**/analytics.js?*",lambda route:route.fulfill(status=200,content_type="application/javascript",body=""))
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto(f"http://127.0.0.1:{server.server_port}/index.html",wait_until="domcontentloaded")
        page.wait_for_function("window.__reconFixture?.ready()")
        page.evaluate("__reconFixture.prepare()")
        # Exercise the real launch, not a mocked showReconTracking.
        page.locator("#startTp").click()
        page.locator(".recon-tracking").wait_for(state="visible",timeout=8000)
        assert page.locator("#modalTitle").inner_text()=="Capture Battlefield"
        assert page.evaluate("__reconFixture.state()")=={"phase":"between","turn":0,"players":5,"npos":3}
        page.keyboard.press("Escape")
        page.evaluate("__reconFixture.strategy()")
        before=page.evaluate("__reconFixture.state()")
        page.locator("#retryReconSetup").click()
        page.locator(".recon-tracking").wait_for(state="visible")
        page.get_by_text("Skip Recon Setup",exact=True).click()
        assert page.evaluate("__reconFixture.state()")==before
        actor=page.evaluate("__reconFixture.prepareMovement()")
        page.evaluate("__reconFixture.confirmMove('dash')")
        page.wait_for_function("window.__reconConfig.actorKey!==null")
        assert page.evaluate("__reconFixture.ap()")=={"id":actor,"remaining":1,"completed":["dash"],"committed":False}
        assert page.locator('#confirmNpoMovement').count()==0
        assert '1 AP remaining' in page.locator('.rt-ap-progress').inner_text()
        assert page.evaluate("window.__reconConfig.reusePrevious===true")
        assert page.evaluate("window.__reconConfig.completedActionIds")==["dash"]
        page.evaluate("__reconFixture.confirmMove('reposition')")
        page.wait_for_function("__reconFixture.ap().committed===true")
        assert page.evaluate("__reconFixture.ap().remaining")==0
        assert page.evaluate("__reconFixture.ap().completed")==["dash","reposition"]
        # One confirmation commits both movements through two guarded AP transactions.
        actor=page.evaluate("__reconFixture.prepareMovement()")
        page.evaluate("__reconFixture.confirmMove('dash','reposition')")
        page.wait_for_function("__reconFixture.ap().committed===true")
        assert page.evaluate("__reconFixture.ap().remaining")==0
        assert page.evaluate("__reconFixture.ap().completed")==["dash","reposition"]
        assert page.locator('#confirmNpoMovement').count()==0
        assert not errors,errors
        browser.close()
finally:
    server.shutdown()
print("Actual app Recon setup and Strategy retry passed.")
