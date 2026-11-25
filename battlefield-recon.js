'use strict';
function reconCore(){
  const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  function nearest(point,candidates,limit){
    return candidates.reduce((best,c)=>distance(point,c)<=limit&&(!best||distance(point,c)<distance(point,best))?c:best,null);
  }
  // Circular edge proposals, never an assertion of miniature identity or legal targeting.
  function detect(data,w,h){
    const gray=new Float32Array(w*h);
    for(let i=0;i<gray.length;i++)gray[i]=.299*data[4*i]+.587*data[4*i+1]+.114*data[4*i+2];
    const scale=Math.min(w,h), radii=[.017,.023,.029,.036].map(x=>Math.max(4,Math.round(scale*x)));
    const angles=Array.from({length:16},(_,i)=>[Math.cos(i*Math.PI/8),Math.sin(i*Math.PI/8)]);
    const hits=[],step=Math.max(2,Math.round(scale/160)),margin=Math.max(...radii)+3;
    for(let y=margin;y<h-margin;y+=step)for(let x=margin;x<w-margin;x+=step)for(const r of radii){
      let strong=0,score=0,quadrants=[0,0,0,0];
      for(let i=0;i<angles.length;i++){
        const [dx,dy]=angles[i];
        const get=d=>gray[Math.round(y+dy*d)*w+Math.round(x+dx*d)];
        const edge=Math.abs(get(r-2)-get(r+2));
        if(edge>=18){strong++;quadrants[Math.floor(i/4)]++;}
        score+=Math.min(75,edge);
      }
      if(strong>=11&&quadrants.every(q=>q>=2)&&score/16>=25)hits.push({x,y,r,score:score/16});
    }
    hits.sort((a,b)=>b.score-a.score);
    const found=[];
    for(const hit of hits){if(found.every(p=>distance(p,hit)>Math.max(p.r,hit.r)*1.6))found.push(hit);if(found.length>=28)break;}
    return found;
  }
  function pointFromRect(x,y,rect,w,h){
    if(rect.width<=0||rect.height<=0)return null;
    const px=(x-rect.left)*w/rect.width,py=(y-rect.top)*h/rect.height;
    return px>=0&&py>=0&&px<=w&&py<=h?{x:px,y:py}:null;
  }
  return {distance,nearest,detect,pointFromRect};
}
function reconUI(){
  const core=reconCore();
  const enabled=()=>document.documentElement.dataset.experimental==='on';
  const mount=(host)=>{
    if(!enabled()||host.dataset.reconMounted)return;
    host.dataset.reconMounted='yes';
    const kind=host.dataset.reconKind;
    const second=kind==='move'?'destination':'target';
    const details=document.createElement('details');
    details.className='recon-panel';
    details.innerHTML='<summary><span class="recon-emblem" aria-hidden="true">◎</span><span>Battlefield Recon<small>Optional photo assist · Experimental</small></span></summary><div class="recon-body"><p class="recon-context"></p><div class="recon-upload"><label class="btn secondary">Take Photo<input type="file" accept="image/*" capture="environment" aria-label="Take battlefield photo"></label><label class="btn ghost">Choose Photo<input type="file" accept="image/*" aria-label="Choose battlefield photo"></label></div><p class="recon-status" role="status" aria-live="polite">Capture the current board from above.</p><div class="recon-workspace" hidden><div class="recon-frame"><canvas aria-label="Battlefield photograph with optional model candidates and marked action"></canvas></div><div class="recon-tools"><button type="button" class="btn secondary" data-recon="scan">Find possible bases</button><button type="button" class="btn ghost" data-recon="reset">Clear marks</button></div><p class="recon-legend"><span>● Acting NPO</span><span class="recon-other"></span></p><p class="recon-note">Photo only. Verify movement, visibility, cover and target eligibility on the table. No game state is changed.</p></div></div>';
    host.append(details);
    const get=s=>details.querySelector(s),canvas=get('canvas'),ctx=canvas.getContext('2d'),status=get('.recon-status'),workspace=get('.recon-workspace'),scan=get('[data-recon="scan"]');
    get('.recon-context').textContent=host.dataset.reconActor+' · '+host.dataset.reconAction;
    get('.recon-other').textContent=kind==='move'?'◌ Destination':'● Target';
    get('.recon-other').classList.toggle('recon-target',kind!=='move');
    if(!ctx){status.textContent='Photo preview unavailable on this device.';return;}
    let photo=null,candidates=[],actor=null,other=null,sequence=0,busy=false;
    function draw(){
      if(!photo)return;
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(photo,0,0,canvas.width,canvas.height);
      const radius=Math.max(12,Math.min(canvas.width,canvas.height)*.033);
      function circle(p,r,color,dash=false){
        ctx.save();ctx.setLineDash(dash?[r*.36,r*.22]:[]);ctx.strokeStyle='#08130c';ctx.lineWidth=7;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=3.5;ctx.stroke();ctx.restore();
      }
      candidates.forEach(p=>circle(p,Math.max(8,p.r),'#f0c66a',true));
      if(actor&&other){
        const angle=Math.atan2(other.y-actor.y,other.x-actor.x),len=core.distance(actor,other),color=kind==='move'?'#76f5a8':'#ff7f83';
        if(len>radius*2.3){
          const end={x:other.x-Math.cos(angle)*radius,y:other.y-Math.sin(angle)*radius},start={x:actor.x+Math.cos(angle)*radius,y:actor.y+Math.sin(angle)*radius};
          ctx.save();ctx.strokeStyle='#08130c';ctx.lineWidth=8;ctx.beginPath();ctx.moveTo(start.x,start.y);ctx.lineTo(end.x,end.y);ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=4;if(kind!=='move')ctx.setLineDash([12,8]);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(end.x,end.y);ctx.lineTo(end.x-17*Math.cos(angle-.45),end.y-17*Math.sin(angle-.45));ctx.lineTo(end.x-17*Math.cos(angle+.45),end.y-17*Math.sin(angle+.45));ctx.fill();ctx.restore();
        }
      }
      if(actor)circle(actor,radius,'#76f5a8');
      if(other)circle(other,radius,kind==='move'?'#76f5a8':'#ff7f83',kind==='move');
    }
    function reset(){actor=null;other=null;candidates=[];draw();status.textContent='Tap the acting NPO, then its '+second+'.';}
    async function load(file){
      const token=++sequence;
      if(!file)return;
      status.textContent='Reading photo…';
      busy=true;scan.disabled=true;
      let url;
      try{
        url=URL.createObjectURL(file);
        const image=new Image();
        await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});
        if(token!==sequence||!host.isConnected||!enabled())return;
        const factor=Math.min(1,1200/Math.max(image.naturalWidth,image.naturalHeight));
        canvas.width=Math.max(1,Math.round(image.naturalWidth*factor));canvas.height=Math.max(1,Math.round(image.naturalHeight*factor));
        photo=image;workspace.hidden=false;reset();
      }catch(error){if(token===sequence)status.textContent='Could not read that photo. Try a JPEG or another image.';}
      finally{if(url)URL.revokeObjectURL(url);if(token===sequence){busy=false;scan.disabled=false;}}
    }
    details.querySelectorAll('input').forEach(input=>input.addEventListener('change',()=>{const file=input.files?.[0];input.value='';if(file)void load(file);}));
    scan.addEventListener('click',()=>{
      if(!photo||busy)return;
      try{
        const small=document.createElement('canvas'),scale=Math.min(1,384/Math.max(canvas.width,canvas.height));
        small.width=Math.max(1,Math.round(canvas.width*scale));small.height=Math.max(1,Math.round(canvas.height*scale));
        const context=small.getContext('2d');context.drawImage(photo,0,0,small.width,small.height);
        candidates=core.detect(context.getImageData(0,0,small.width,small.height).data,small.width,small.height).map(p=>({x:p.x*canvas.width/small.width,y:p.y*canvas.height/small.height,r:p.r/scale}));
        draw();status.textContent=candidates.length?'Amber rings are unverified base candidates. Tap '+(!actor?'the acting NPO':!other?'its '+second:'Clear marks to start again')+'.':'No reliable base candidates. Tap the acting NPO and its '+second+' manually.';
      }catch(error){status.textContent='Base scan unavailable. Mark positions manually.';}
    });
    get('[data-recon="reset"]').addEventListener('click',reset);
    canvas.addEventListener('click',event=>{
      if(!photo||busy||!enabled())return;
      let p=core.pointFromRect(event.clientX,event.clientY,canvas.getBoundingClientRect(),canvas.width,canvas.height);
      if(!p)return;
      if(!actor||kind!=='move')p=core.nearest(p,candidates,Math.min(canvas.width,canvas.height)*.035)||p;
      if(!actor){actor=p;status.textContent='Tap the '+second+'.';}
      else if(!other){if(core.distance(actor,p)<Math.min(canvas.width,canvas.height)*.025){status.textContent='Choose a different position.';return;}other=p;status.textContent='Marked. Verify on the tabletop, then use the normal action controls.';}
      else{other=null;actor=p;status.textContent='Tap the '+second+'.';}
      draw();
    });
    details.addEventListener('toggle',()=>{if(!details.open){sequence++;busy=false;scan.disabled=false;photo=null;actor=null;other=null;candidates=[];canvas.width=1;canvas.height=1;workspace.hidden=true;status.textContent='Capture the current board from above.';}});
  };
  function refresh(){
    if(!enabled()){
      document.querySelectorAll('[data-recon-kind]').forEach(host=>{host.replaceChildren();delete host.dataset.reconMounted;});
      return;
    }
    document.querySelectorAll('[data-recon-kind]').forEach(mount);
  }
  const observer=new MutationObserver(refresh);
  observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['data-experimental']});
  refresh();
}
if(typeof document!=='undefined')reconUI();
if(typeof module!=='undefined')module.exports=reconCore();
