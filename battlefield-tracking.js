'use strict';
function trackingCore(){
  const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const bounded=(v,a,b)=>Math.max(a,Math.min(b,v));
  const inside=(p,b)=>p.x>=b.x0&&p.x<=b.x1&&p.y>=b.y0&&p.y<=b.y1;
  function physical(p,b){return {x:(p.x-b.x0)/(b.x1-b.x0)*b.width,y:(p.y-b.y0)/(b.y1-b.y0)*b.height};}
  function imagePoint(p,b){return {x:b.x0+p.x/b.width*(b.x1-b.x0),y:b.y0+p.y/b.height*(b.y1-b.y0)};}
  function segmentDistance(p,a,b){
    const dx=b.x-a.x,dy=b.y-a.y,d=dx*dx+dy*dy;
    const t=d?bounded(((p.x-a.x)*dx+(p.y-a.y)*dy)/d,0,1):0;
    return dist(p,{x:a.x+t*dx,y:a.y+t*dy});
  }
  function patch(data,w,h,p,r){
    const out=[];
    for(let y=-3;y<=3;y++)for(let x=-3;x<=3;x++){
      const xx=Math.round(p.x+x*r/3),yy=Math.round(p.y+y*r/3);
      if(xx<0||yy<0||xx>=w||yy>=h)return null;
      const i=(yy*w+xx)*4;
      out.push((data[i]+data[i+1]+data[i+2])/3,data[i]-data[i+1],data[i+2]-data[i+1]);
    }
    let mean=0;for(let i=0;i<out.length;i+=3)mean+=out[i]/49;
    for(let i=0;i<out.length;i+=3)out[i]-=mean;
    return out;
  }
  function matchScore(a,b){
    if(!a||!b)return Infinity;
    let s=0;for(let i=0;i<a.length;i++)s+=Math.abs(a[i]-b[i])*(i%3===0?1:.45);
    return s/a.length;
  }
  function track(old,data,w,h,board,roster,changed){
    const results={},claimed=[];
    const live=roster.filter(m=>old[m.key]);
    // Stationary models are evaluated first. If the activation history is incomplete,
    // the matcher searches locally and returns uncertain results instead of swapping identities.
    const ordered=[...live].sort((a,b)=>Number(changed.has(a.key))-Number(changed.has(b.key)));
    for(const m of ordered){
      const prior=old[m.key],radius=Math.max(4,Math.round(prior.r||7));
      const max=changed.has(m.key)?Math.max(w,h)*.42:Math.max(8,radius*1.5);
      const step=changed.has(m.key)?3:1;
      let best=null,second=null;
      const candidates=[];
      for(let y=Math.max(board.y0+radius,prior.y-max);y<=Math.min(board.y1-radius,prior.y+max);y+=step)
        for(let x=Math.max(board.x0+radius,prior.x-max);x<=Math.min(board.x1-radius,prior.x+max);x+=step){
          const p={x,y};
          if(claimed.some(c=>dist(c,p)<Math.max(c.r,radius)))continue;
          const score=matchScore(prior.template,patch(data,w,h,p,radius))+(changed.has(m.key)?0:dist(p,prior)*.28);
          if(Number.isFinite(score))candidates.push({x,y,score});
        }
      candidates.sort((a,b)=>a.score-b.score);
      // Refine the strongest separated coarse matches at one-pixel resolution.
      if(step>1){
        const seeds=[];
        for(const c of candidates){if(seeds.every(p=>dist(p,c)>radius*.8))seeds.push(c);if(seeds.length>=12)break;}
        for(const c of seeds)for(let dy=-step;dy<=step;dy++)for(let dx=-step;dx<=step;dx++){
          const p={x:c.x+dx,y:c.y+dy};
          if(p.x<board.x0+radius||p.x>board.x1-radius||p.y<board.y0+radius||p.y>board.y1-radius||claimed.some(q=>dist(p,q)<Math.max(q.r,radius)))continue;
          const score=matchScore(prior.template,patch(data,w,h,p,radius));
          if(Number.isFinite(score))candidates.push({...p,score});
        }
        candidates.sort((a,b)=>a.score-b.score);
      }
      best=candidates[0];second=best&&candidates.find(c=>dist(c,best)>radius*1.65);
      const confident=Boolean(best&&best.score<=9&&(!second||second.score-best.score>=1.1));
      if(confident){results[m.key]={x:best.x,y:best.y,r:radius,template:patch(data,w,h,best,radius)};claimed.push(results[m.key]);}
      else results[m.key]=null;
    }
    return results;
  }
  function plan({board,positions,models,walls=[],objectives=[],mapped=false,actorKey=null,actionOrder}){
    if(!board||!mapped||!models.length||models.some(m=>!positions[m.key]||!Number.isFinite(m.base)||m.base<=0))return null;
    const units=models.map(m=>({...m,p:physical(positions[m.key],board),r:m.base/50.8}));
    const players=units.filter(m=>m.side==='player'),npos=units.filter(m=>m.side==='npo'),ready=npos.filter(m=>m.ready&&(!actorKey||m.key===actorKey));
    if(!players.length||!ready.length)return null;
    const barriers=walls.map(w=>w.map(p=>physical(p,board)));
    const obj=objectives.map(p=>physical(p,board));
    const edge=(a,b)=>Math.max(0,dist(a.p,b.p)-a.r-b.r);
    function clear(a,b,r=0){
      const steps=Math.max(1,Math.ceil(dist(a,b)/.12));
      for(let i=0;i<=steps;i++){
        const p={x:a.x+(b.x-a.x)*i/steps,y:a.y+(b.y-a.y)*i/steps};
        if(barriers.some(([s,t])=>segmentDistance(p,s,t)<r+.12))return false;
      }
      return true;
    }
    const visible=(a,b)=>clear(a.p,b.p,0);
    const control=(a,b)=>edge(a,b)<=.93&&visible(a,b);
    const shooting=(a,b,from=a.p)=>a.canShoot&&b.order==='Engage'&&clear(from,b.p,0)&&(!Number.isFinite(a.range)||Math.max(0,dist(from,b.p)-a.r-b.r)<=a.range-.12);
    function targets(a,kind,from=a.p){
      return players.filter(b=>kind==='fight'?control(a,b):shooting(a,b,from)).sort((b,c)=>b.wounds-c.wounds||dist(from,b.p)-dist(from,c.p)||Number(c.ready)-Number(b.ready));
    }
    const ranking=ready.map(a=>({a,threat:Number(targets(a,'fight').length>0||targets(a,'shoot').length>0),distance:Math.min(...players.map(b=>edge(a,b))),objective:obj.length?Math.min(...obj.map(p=>dist(a.p,p))):Infinity})).sort((b,c)=>c.threat-b.threat||b.distance-c.distance||b.objective-c.objective);
    const a=ranking[0].a;
    const inControl=players.some(b=>control(a,b));
    // Borderline base-to-base estimates cannot establish control range reliably.
    if(players.some(b=>Math.abs(edge(a,b)-1)<.15&&visible(a,b)))return null;
    // A straight unobstructed movement is conservative; no invented routes through walls.
    const validMove=(p,chargeTarget=null)=>{
      if(p.x<a.r+.1||p.y<a.r+.1||p.x>board.width-a.r-.1||p.y>board.height-a.r-.1||!clear(a.p,p,a.r))return false;
      for(const b of units.filter(b=>b.key!==a.key)){
        if(segmentDistance(b.p,a.p,p)<a.r+b.r+.08)return false;
        if(b.side==='player'&&b.key!==chargeTarget?.key&&segmentDistance(b.p,a.p,p)<a.r+b.r+1.04)return false;
      }
      return true;
    };
    function movement(kind){
      if(inControl||!Number.isFinite(a.move))return null;
      const max=kind==='dash'?3:kind==='charge'?a.move+2:a.move;
      const focus=a.focus;
      const goal=focus==='mission'&&obj.length?obj.reduce((b,c)=>dist(a.p,b)<dist(a.p,c)?b:c):players.reduce((b,c)=>dist(a.p,b.p)<dist(a.p,c.p)?b:c).p;
      let best=null;
      for(let d=.5;d<=max-.12;d+=.5)for(let i=0;i<32;i++){
        const t=i*Math.PI/16,p={x:a.p.x+d*Math.cos(t),y:a.p.y+d*Math.sin(t)};
        if(kind==='charge'){
          const target=players.find(b=>dist(p,b.p)-a.r-b.r>=.1&&dist(p,b.p)-a.r-b.r<=.85&&clear(p,b.p)&&validMove(p,b));
          if(target){const score=target.wounds+d*.1;if(!best||score<best.score)best={p,target,score};}
        }else if(validMove(p)){
          const next=targets(a,'shoot',p)[0],improvement=dist(a.p,goal)-dist(p,goal);
          const score=improvement+(focus==='shoot'&&next?100:0);
          if(score>.2&&(!best||score>best.score))best={p,target:focus==='shoot'?next:null,score};
        }
      }
      if(!best)return null;
      return {destination:imagePoint(best.p,board),target:best.target?.key||null,distance:dist(a.p,best.p),followUp:kind==='charge'&&a.ap>=2?'fight':best.target&&a.ap>=2?'shoot':null};
    }
    const order=actionOrder(a,inControl);
    if(!Array.isArray(order))return null;
    for(const name of order){
      const id=String(name).toLowerCase().split(' ')[0];
      if(id==='fight'){
        const target=targets(a,'fight')[0];if(target)return {actor:a.key,action:name,id,target:target.key,inControl,shootable:targets(a,'shoot').length>0,fightable:true};
      }else if(id==='shoot'){
        if(inControl)return null;
        const target=targets(a,'shoot')[0];if(target)return {actor:a.key,action:name,id,target:target.key,inControl,shootable:true,fightable:false};
        // Conceal/cover and unknown orders cannot be treated as proof no target exists.
        if(players.some(b=>b.order!=='Engage'&&visible(a,b)))return null;
      }else if(['charge','reposition','dash'].includes(id)){
        if(inControl)return null;
        const move=movement(id);
        if(move)return {actor:a.key,action:name,id,...move,inControl,shootable:targets(a,'shoot').length>0,fightable:false};
        // No straight route found is not proof that no legal path exists.
        return null;
      }else if(id==='fall'){
        if(inControl)return null;
      }else return null; // Special actions and hatch operation remain with the rules engine.
    }
    return null;
  }
  return {dist,inside,physical,imagePoint,segmentDistance,patch,matchScore,track,plan};
}
function trackingUI(){
  const core=trackingCore();
  let session=null,preview=null;
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function draw(canvas,frame,positions,models,board,walls,objectives,plan,showLabels){
    const ctx=canvas.getContext('2d');
    canvas.width=frame.width;canvas.height=frame.height;ctx.drawImage(frame,0,0);
    const ring=(p,color,r=11,dash=false)=>{ctx.save();ctx.setLineDash(dash?[5,4]:[]);ctx.strokeStyle='#06100c';ctx.lineWidth=5;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=2.5;ctx.stroke();ctx.restore();};
    const line=(a,b,c,dash=false,arrow=false)=>{ctx.save();ctx.setLineDash(dash?[7,5]:[]);ctx.strokeStyle='#06100c';ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.strokeStyle=c;ctx.lineWidth=3;ctx.stroke();ctx.setLineDash([]);if(arrow){const t=Math.atan2(b.y-a.y,b.x-a.x);ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(b.x,b.y);ctx.lineTo(b.x-12*Math.cos(t-.5),b.y-12*Math.sin(t-.5));ctx.lineTo(b.x-12*Math.cos(t+.5),b.y-12*Math.sin(t+.5));ctx.fill();}ctx.restore();};
    if(board&&showLabels){ctx.strokeStyle='#81b8ae';ctx.lineWidth=2;ctx.strokeRect(board.x0,board.y0,board.x1-board.x0,board.y1-board.y0);}
    if(showLabels){walls.forEach(([a,b])=>line(a,b,'#f0c66a'));objectives.forEach(p=>ring(p,'#f0c66a',8,true));}
    if(showLabels)models.forEach((m,i)=>{const p=positions[m.key];if(!p)return;const c=m.side==='npo'?'#76f5a8':'#91caff';ring(p,c,Math.max(8,p.r||10));ctx.font='bold 11px system-ui';ctx.fillStyle='#06100c';ctx.fillRect(p.x-9,p.y-19,19,13);ctx.fillStyle=c;ctx.textAlign='center';ctx.fillText(String(i+1),p.x,p.y-9);});
    if(plan){
      const a=positions[plan.actor],t=positions[plan.target],d=plan.destination;
      if(a){if(d)line(a,d,'#76f5a8',false,true);if(t)line(d||a,t,'#ff7f83',true,true);ring(a,'#76f5a8',Math.max(12,a.r||10));if(d)ring(d,'#76f5a8',12,true);if(t)ring(t,'#ff7f83',Math.max(12,t.r||10));}
    }
  }
  function open(host,config){
    if(!host||!config||document.documentElement.dataset.experimental!=='on')return;
    if(!session||session.token!==config.token)session={token:config.token,board:null,positions:{},walls:[],objectives:[],mapped:false,frame:null,turn:null,activated:new Set(),ready:new Set(),meta:{}};
    preview=null;
    const s=session,models=config.models.map(m=>({...m,...(s.meta[m.key]?.base&&!m.base?{base:s.meta[m.key].base}:{}),...(m.side==='player'&&m.order==='Unknown'&&s.meta[m.key]?.order?{order:s.meta[m.key].order}:{})}));
    // A player may change order during their activation. Unknown must remain unknown until confirmed.
    if(s.frame)for(const m of models.filter(m=>m.side==='player'&&(s.turn!==config.turn||!s.activated.has(m.key)&&config.activated.includes(m.key))))if(config.models.find(x=>x.key===m.key)?.order==='Unknown')m.order='Unknown';
    let frame=null,positions={},board=null,walls=[],objectives=[],mapped=false,stage='photo',corner=null,wallStart=null,selected='',plan=null,seq=0;
    host.innerHTML='<section class="recon-tracking"><p class="eyebrow">TACTICAL SCAN · EXPERIMENTAL</p><p class="rt-status" role="status" aria-live="polite"></p><div class="recon-upload"><label class="btn secondary">Take Photo<input type="file" accept="image/*" capture="environment" aria-label="Take tactical photo"></label><label class="btn ghost">Choose Photo<input type="file" accept="image/*" aria-label="Choose tactical photo"></label></div><div class="rt-work" hidden><div class="recon-frame"><canvas aria-label="Battlefield photograph and tactical overlays"></canvas></div><div class="rt-controls"></div></div><div class="wizard-actions"><button type="button" class="btn ghost rt-manual">Use Manual Guide</button></div></section>';
    const get=q=>host.querySelector(q),status=get('.rt-status'),canvas=get('canvas'),controls=get('.rt-controls'),work=get('.rt-work');
    const tell=t=>status.textContent=t;
    const button=(label,fn,kind='secondary')=>{const b=document.createElement('button');b.type='button';b.className='btn '+kind;b.textContent=label;b.onclick=fn;return b;};
    const live=()=>host.isConnected&&document.documentElement.dataset.experimental==='on'&&config.valid();
    const repaint=()=>{if(frame)draw(canvas,frame,positions,models,board,walls,objectives,plan,stage!=='plan');};
    function update(){
      controls.replaceChildren();
      if(stage==='corners'){
        tell(corner?'Tap the bottom-right playable corner.':'Tap the top-left playable corner. Use a square-on photo.');
      }else if(stage==='dimensions'){
        tell('Enter the actual playable board width and height in inches.');
        const group=document.createElement('div');group.className='rt-dimensions';
        group.innerHTML='<label>Width (in)<input type="number" min="1" max="100" step=".01" value="23.86"></label><label>Height (in)<input type="number" min="1" max="100" step=".01" value="27.68"></label>';
        if(config.boardWidth&&config.boardHeight){group.children[0].lastChild.value=config.boardWidth;group.children[1].lastChild.value=config.boardHeight;}
        if(board.x1-board.x0>board.y1-board.y0){group.children[0].lastChild.value='27.68';group.children[1].lastChild.value='23.86';}
        controls.append(group,button('Use Board Dimensions',()=>{const [w,h]=Array.from(group.querySelectorAll('input'),i=>Number(i.value));if(!(w>0&&w<=100&&h>0&&h<=100)){tell('Enter valid positive dimensions.');return;}board.width=w;board.height=h;stage='identify';update();},'primary'));
      }else if(stage==='identify'){
        const missing=models.filter(m=>!positions[m.key]);
        if(!selected||!models.some(m=>m.key===selected))selected=missing[0]?.key||models[0]?.key||'';
        const current=models.find(m=>m.key===selected);
        tell(missing.length?`${models.length-missing.length} of ${models.length} identified. Tap ${current?.name||'the selected operative'} on the photo.`:'All operatives located. Verify the markers, then continue.');
        const select=document.createElement('select');select.setAttribute('aria-label','Operative to identify');
        models.forEach((m,i)=>{const o=document.createElement('option');o.value=m.key;o.textContent=`${i+1}. ${m.name}${positions[m.key]?' ✓':' •'}`;select.append(o);});select.value=selected;
        select.onchange=()=>{selected=select.value;update();};controls.append(select);
        if(current&&!current.base){const label=document.createElement('label');label.className='rt-metadata';label.textContent='Base diameter (mm)';const input=document.createElement('input');input.type='number';input.min='10';input.max='100';input.placeholder='e.g. 32';input.onchange=()=>{const v=Number(input.value);if(v>=10&&v<=100){current.base=v;update();}};label.append(input);controls.append(label);}
        if(current?.side==='player'){const label=document.createElement('label');label.className='rt-metadata';label.textContent='Current tabletop order';const order=document.createElement('select');for(const value of ['Unknown','Engage','Conceal']){const option=document.createElement('option');option.value=value;option.textContent=value;order.append(option);}order.value=current.order;order.onchange=()=>{current.order=order.value;};label.append(order);controls.append(label);}
        if(!missing.length)controls.append(button('Confirm Operative Positions',()=>{stage='terrain';update();},'primary'));
        controls.append(button('Clear Selected Marker',()=>{delete positions[selected];update();},'ghost'));
      }else if(stage==='terrain'){
        tell('Mark wall sections once, leaving open hatchways unmarked. Tap two endpoints per wall. Add objectives if useful.');
        const group=document.createElement('div');group.className='rt-actions';
        group.append(button('Mark Wall',()=>{stage='wall';wallStart=null;update();}),button('Mark Objective',()=>{stage='objective';update();}),button('Undo Wall',()=>{walls.pop();repaint();update();},'ghost'),button('Undo Objective',()=>{objectives.pop();repaint();update();},'ghost'));
        controls.append(group);
        const unresolved=models.filter(m=>!m.base);if(unresolved.length){const note=document.createElement('p');note.className='rt-metadata';note.textContent='Base size required for '+unresolved.map(m=>m.name).join(', ')+'.';controls.append(note,button('Set Missing Base Sizes',()=>{selected=unresolved[0].key;stage='identify';update();}));}
        const unknown=models.filter(m=>m.side==='player'&&m.order==='Unknown');if(unknown.length){const note=document.createElement('p');note.className='rt-metadata';note.textContent='Unknown orders may prevent shooting recommendations. Update them if needed.';controls.append(note,button('Review Player Orders',()=>{selected=unknown[0].key;stage='identify';update();},'ghost'));}
        const check=document.createElement('label');check.className='rt-check';const input=document.createElement('input');input.type='checkbox';input.checked=mapped;input.onchange=()=>{mapped=input.checked;};check.append(input,document.createTextNode(' All blocking terrain is marked; verify physical board and open hatchways.'));controls.append(check);
        controls.append(button('Assess Battlefield',assess,'primary'));
      }else if(stage==='wall'){tell(wallStart?'Tap the other end of this wall.':'Tap the first end of the wall.');controls.append(button('Cancel Wall',()=>{wallStart=null;stage='terrain';update();},'ghost'));}
      else if(stage==='objective'){tell('Tap the centre of an objective.');controls.append(button('Cancel Objective',()=>{stage='terrain';update();},'ghost'));}
      else if(stage==='review'){
        const missing=models.filter(m=>!positions[m.key]);
        tell(missing.length?`${missing.length} operative(s) could not be tracked reliably. Correct only these positions.`:'Positions tracked. Verify the photo matches the physical board.');
        controls.append(button(missing.length?'Identify Missing Models':'Review / Correct Models',()=>{selected=missing[0]?.key||'';stage='identify';update();}));
        if(!missing.length)controls.append(button('Review Terrain & Assess',()=>{stage='terrain';update();},'primary'));
        controls.append(button('Recalibrate Photo',()=>{resetCalibration();},'ghost'));
      }else if(stage==='plan'){
        if(!plan){tell('No reliable tactical recommendation from this photo. The normal guide remains available.');controls.append(button('Review Positions / Terrain',()=>{stage='terrain';update();}));}
        else{
          const a=models.find(m=>m.key===plan.actor),target=models.find(m=>m.key===plan.target);
          tell('Tactical recommendation · confirm on the physical table');
          const info=document.createElement('div');info.className='rt-plan';
          info.innerHTML='<strong>'+esc(a?.name)+' · '+esc(plan.id==='fall-back'?'Fall Back':plan.id[0].toUpperCase()+plan.id.slice(1))+'</strong><p>'+esc(plan.destination?`${plan.distance.toFixed(1)}″ proposed straight movement${target?` toward ${target.name}`:''}.`:target?`Target ${target.name}.`:'')+'</p>'+(plan.followUp?'<p>Potential follow-up: '+esc(plan.followUp)+'</p>':'')+'<small>Green: acting NPO / destination. Red: target. Check visibility, cover, base fit and special rules before accepting.</small>';
          controls.append(info,button('Accept Tactical Recommendation',()=>{if(!live())return;preview={frame,positions,models,board,walls,objectives,plan};config.accept(plan);},'primary'),button('Review Positions / Terrain',()=>{stage='terrain';plan=null;update();},'ghost'));
        }
      }
      repaint();
    }
    function resetCalibration(){positions={};board=null;walls=[];objectives=[];mapped=false;corner=null;plan=null;stage='corners';update();}
    function assess(){
      if(!live()||!board||models.some(m=>!positions[m.key]))return;
      s.meta=Object.fromEntries(models.map(m=>[m.key,{base:m.base,order:m.order}]));s.frame=frame;s.board={...board};s.positions={...positions};s.walls=walls.map(w=>w.map(p=>({...p})));s.objectives=objectives.map(p=>({...p}));s.mapped=mapped;s.turn=config.turn;s.activated=new Set(config.activated);s.ready=new Set(config.ready);s.scanKey=config.scanKey;
      plan=core.plan({board,positions,models,walls,objectives,mapped,actorKey:config.actorKey,actionOrder:config.actionOrder});
      stage='plan';update();
    }
    async function load(file){
      const ticket=++seq;if(!file)return;
      tell('Reading battlefield photograph…');let url;
      try{
        url=URL.createObjectURL(file);const im=new Image();await new Promise((res,rej)=>{im.onload=res;im.onerror=rej;im.src=url;});
        if(ticket!==seq||!live())return;
        const factor=Math.min(1,600/Math.max(im.naturalWidth,im.naturalHeight));
        const next=document.createElement('canvas');next.width=Math.max(1,Math.round(im.naturalWidth*factor));next.height=Math.max(1,Math.round(im.naturalHeight*factor));
        next.getContext('2d').drawImage(im,0,0,next.width,next.height);frame=next;work.hidden=false;plan=null;
        if(s.frame&&s.board&&s.frame.width===next.width&&s.frame.height===next.height){
          // Fixed overhead camera: detect broad framing/lighting changes by comparing a sparse grid.
          const data=next.getContext('2d').getImageData(0,0,next.width,next.height).data;
          const before=s.frame.getContext('2d').getImageData(0,0,next.width,next.height).data;
          let delta=0,count=0;
          for(let y=12;y<next.height-12;y+=13)for(let x=12;x<next.width-12;x+=13){if(!core.inside({x,y},s.board)||Object.values(s.positions).some(p=>core.dist(p,{x,y})<(p.r||8)*2))continue;const i=(y*next.width+x)*4;delta+=(Math.abs(data[i]-before[i])+Math.abs(data[i+1]-before[i+1])+Math.abs(data[i+2]-before[i+2]))/3;count++;}
          if(count&&delta/count<16){
            board={...s.board};walls=s.walls.map(w=>w.map(p=>({...p})));objectives=s.objectives.map(p=>({...p}));mapped=false;
            const changed=new Set(models.filter(m=>m.side==='player'&&(!s.activated.has(m.key)&&config.activated.includes(m.key)||s.turn!==config.turn)||m.side==='npo'&&(s.ready.has(m.key)&&!config.ready.includes(m.key)||m.key===config.actorKey||s.turn!==config.turn)).map(m=>m.key));
            const matches=core.track(s.positions,data,next.width,next.height,board,models,changed);
            positions=Object.fromEntries(Object.entries(matches).filter(([,p])=>p));stage='review';update();return;
          }
        }
        resetCalibration();
      }catch(e){if(ticket===seq&&live())tell('Could not read photo. Try a JPEG or another image.');}
      finally{if(url)URL.revokeObjectURL(url);}
    }
    host.querySelectorAll('input[type=file]').forEach(i=>i.onchange=()=>{const f=i.files?.[0];i.value='';if(f)void load(f);});
    get('.rt-manual').onclick=()=>{seq++;preview=null;config.manual();};
    canvas.onclick=e=>{
      if(!frame||!live())return;
      const rect=canvas.getBoundingClientRect(),p={x:(e.clientX-rect.left)*canvas.width/rect.width,y:(e.clientY-rect.top)*canvas.height/rect.height};
      if(stage==='corners'){
        if(!corner){corner=p;update();return;}
        if(p.x-corner.x<canvas.width*.25||p.y-corner.y<canvas.height*.25){tell('Choose a bottom-right corner well below and to the right.');return;}
        board={x0:corner.x,y0:corner.y,x1:p.x,y1:p.y,width:0,height:0};stage='dimensions';update();return;
      }
      if(!board||!core.inside(p,board))return;
      if(stage==='identify'){
        const m=models.find(m=>m.key===selected);if(!m)return;
        if(Object.entries(positions).some(([k,v])=>k!==selected&&core.dist(p,v)<5)){tell('That location is already assigned. Select a different miniature.');return;}
        const r=Math.max(5,Math.round((m.base||32)/50.8*(board.x1-board.x0)/board.width));
        const data=frame.getContext('2d').getImageData(0,0,frame.width,frame.height).data;
        positions[selected]={...p,r,template:core.patch(data,frame.width,frame.height,p,r)};
        selected=models.find(m=>!positions[m.key])?.key||selected;update();
      }else if(stage==='wall'){if(!wallStart){wallStart=p;update();}else{if(core.dist(wallStart,p)<4)return;walls.push([wallStart,p]);mapped=false;wallStart=null;stage='terrain';update();}}
      else if(stage==='objective'){objectives.push(p);stage='terrain';update();}
    };
    if(s.frame)tell('Capture a fresh photograph from the same overhead position. Previously identified models will be tracked.');
    else tell('Photograph the deployed board from directly overhead. Identify each miniature once.');
  }
  function renderPreview(host){
    if(!preview||!host||host.dataset.rtMounted)return;
    host.dataset.rtMounted='1';const canvas=document.createElement('canvas');canvas.setAttribute('aria-label','Approved tactical movement or attack overlay');host.append(canvas);
    const {frame,positions,models,board,walls,objectives,plan}=preview;draw(canvas,frame,positions,models,board,walls,objectives,plan,false);
  }
  function clearPreview(){preview=null;}
  new MutationObserver(()=>{if(document.documentElement.dataset.experimental==='on')document.querySelectorAll('[data-recon-plan]').forEach(renderPreview);}).observe(document.documentElement,{subtree:true,childList:true});
  return {open,clearPreview};
}
if(typeof document!=='undefined')window.TombWorldReconTracking=trackingUI();
if(typeof module!=='undefined')module.exports=trackingCore();
