'use strict';
function reconCore(){
  const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  function nearest(point,candidates,limit){
    return candidates.reduce((best,c)=>distance(point,c)<=limit&&(!best||distance(point,c)<distance(point,best))?c:best,null);
  }
  // Compact foreground proposals; terrain and operatives may look alike.
  function detect(data,w,h){
    if(w<32||h<32||data.length!==w*h*4)return [];
    const scale=Math.min(w,h),gray=new Uint8Array(w*h),contrast=new Uint8Array(w*h),radius=Math.max(5,Math.round(scale*.039));
    for(let i=0;i<gray.length;i++)gray[i]=Math.round(.299*data[4*i]+.587*data[4*i+1]+.114*data[4*i+2]);
    // Local median removes uneven lighting on plain tabletops.
    for(let y=0;y<h;y++){
      const top=Math.max(0,y-radius),bottom=Math.min(h-1,y+radius),hist=new Uint32Array(256);
      let count=0;
      for(let yy=top;yy<=bottom;yy++)for(let xx=0;xx<=Math.min(w-1,radius);xx++){hist[gray[yy*w+xx]]++;count++;}
      for(let x=0;x<w;x++){
        let acc=0,median=0;while(median<255&&(acc+=hist[median])<=count/2)median++;
        contrast[y*w+x]=Math.abs(gray[y*w+x]-median);
        const remove=x-radius,add=x+radius+1;
        if(remove>=0)for(let yy=top;yy<=bottom;yy++){hist[gray[yy*w+remove]]--;count--;}
        if(add<w)for(let yy=top;yy<=bottom;yy++){hist[gray[yy*w+add]]++;count++;}
      }
    }
    const closeRadius=Math.max(1,Math.round(scale*.004));
    function morph(input,dilate,vertical){
      const out=new Uint8Array(input.length),length=vertical?h:w,lines=vertical?w:h;
      for(let line=0;line<lines;line++){
        const index=p=>vertical?p*w+line:line*w+p;
        let sum=0;
        for(let p=0;p<=Math.min(length-1,closeRadius);p++)sum+=input[index(p)];
        for(let p=0;p<length;p++){
          const count=Math.min(length-1,p+closeRadius)-Math.max(0,p-closeRadius)+1;
          out[index(p)]=dilate?+(sum>0):+(sum===count);
          if(p-closeRadius>=0)sum-=input[index(p-closeRadius)];
          if(p+closeRadius+1<length)sum+=input[index(p+closeRadius+1)];
        }
      }
      return out;
    }
    const found=[];
    for(const threshold of [15,20,25]){
      let mask=Uint8Array.from(contrast,v=>+(v>=threshold));
      mask=morph(morph(morph(morph(mask,true,false),true,true),false,false),false,true);
      const queue=new Int32Array(mask.length);
      for(let i=0;i<mask.length;i++){
        if(!mask[i])continue;
        let head=0,tail=1,sx=0,sy=0,x0=w,x1=0,y0=h,y1=0;
        queue[0]=i;mask[i]=0;
        while(head<tail){
          const p=queue[head++],x=p%w,y=Math.floor(p/w);sx+=x;sy+=y;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
          if(x>0&&mask[p-1]){mask[p-1]=0;queue[tail++]=p-1;}
          if(x<w-1&&mask[p+1]){mask[p+1]=0;queue[tail++]=p+1;}
          if(y>0&&mask[p-w]){mask[p-w]=0;queue[tail++]=p-w;}
          if(y<h-1&&mask[p+w]){mask[p+w]=0;queue[tail++]=p+w;}
        }
        const bw=x1-x0+1,bh=y1-y0+1,ratio=bw/bh,fill=tail/(bw*bh);
        if(x0===0||y0===0||x1===w-1||y1===h-1||Math.min(bw,bh)<scale*.019||Math.max(bw,bh)>scale*.086||ratio<.42||ratio>2.4||fill<.18||tail<scale*scale*.00014)continue;
        const hit={x:sx/tail,y:sy/tail,r:Math.max(bw,bh)/2,score:Math.min(ratio,1/ratio)*fill,votes:1};
        const prior=found.find(p=>Math.hypot(p.x-hit.x,p.y-hit.y)<Math.max(p.r,hit.r)*.85);
        if(prior){prior.votes++;if(hit.score>prior.score){prior.x=hit.x;prior.y=hit.y;prior.r=hit.r;prior.score=hit.score;}}
        else found.push(hit);
      }
    }
    return found.sort((a,b)=>b.votes-a.votes||b.score-a.score).slice(0,32);
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
    details.innerHTML='<summary><span class="recon-emblem" aria-hidden="true">◎</span><span>Battlefield Recon<small>Optional photo assist · Experimental</small></span></summary><div class="recon-body"><p class="recon-context"></p><div class="recon-upload"><label class="btn secondary">Take Photo<input type="file" accept="image/*" capture="environment" aria-label="Take battlefield photo"></label><label class="btn ghost">Choose Photo<input type="file" accept="image/*" aria-label="Choose battlefield photo"></label></div><p class="recon-status" role="status" aria-live="polite">Capture the current board from above, filling the frame.</p><div class="recon-workspace" hidden><div class="recon-frame"><canvas aria-label="Battlefield photograph with optional model candidates and marked action"></canvas></div><div class="recon-tools"><button type="button" class="btn secondary" data-recon="scan">Find possible bases</button><button type="button" class="btn ghost" data-recon="reset">Clear marks</button></div><p class="recon-legend"><span>● Acting NPO</span><span class="recon-other"></span></p><p class="recon-note">Photo only. Verify movement, visibility, cover and target eligibility on the table. No game state is changed.</p></div></div>';
    host.append(details);
    const get=s=>details.querySelector(s),canvas=get('canvas'),ctx=canvas.getContext('2d'),status=get('.recon-status'),workspace=get('.recon-workspace'),scan=get('[data-recon="scan"]');
    get('.recon-context').textContent=host.dataset.reconActor+' · '+host.dataset.reconAction;
    get('.recon-other').textContent=kind==='move'?'◌ Destination':'● Target';
    get('.recon-other').classList.toggle('recon-target',kind!=='move');
    if(!ctx){status.textContent='Photo preview unavailable on this device.';return;}
    let photo=null,candidates=[],actor=null,other=null,sequence=0,busy=false,showCandidates=true;
    function draw(){
      if(!photo)return;
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(photo,0,0,canvas.width,canvas.height);
      const radius=Math.max(12,Math.min(canvas.width,canvas.height)*.033);
      function circle(p,r,color,dash=false){
        ctx.save();ctx.setLineDash(dash?[r*.36,r*.22]:[]);ctx.strokeStyle='#08130c';ctx.lineWidth=7;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=3.5;ctx.stroke();ctx.restore();
      }
      if(showCandidates)candidates.forEach(p=>circle(p,Math.max(8,p.r),'#f0c66a',true));
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
    function reset(){actor=null;other=null;draw();status.textContent='Tap the acting NPO, then its '+second+'.';}
    async function load(file){
      const token=++sequence;
      if(!file)return;
      status.textContent='Reading photo…';
      busy=true;scan.disabled=true;
      let url,loaded=false;
      try{
        url=URL.createObjectURL(file);
        const image=new Image();
        await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});
        if(token!==sequence||!host.isConnected||!enabled())return;
        const factor=Math.min(1,1200/Math.max(image.naturalWidth,image.naturalHeight));
        canvas.width=Math.max(1,Math.round(image.naturalWidth*factor));canvas.height=Math.max(1,Math.round(image.naturalHeight*factor));
        photo=image;loaded=true;candidates=[];showCandidates=true;workspace.hidden=false;reset();
      }catch(error){if(token===sequence)status.textContent='Could not read that photo. Try a JPEG or another image.';}
      finally{if(url)URL.revokeObjectURL(url);if(token===sequence){busy=false;scan.disabled=false;if(loaded&&host.isConnected&&details.open&&enabled())scanPhoto();}}
    }
    details.querySelectorAll('input').forEach(input=>input.addEventListener('change',()=>{const file=input.files?.[0];input.value='';if(file)void load(file);}));
    function scanPhoto(){
      if(!photo||busy)return;
      try{
        const small=document.createElement('canvas'),scale=Math.min(1,704/Math.max(canvas.width,canvas.height));
        small.width=Math.max(1,Math.round(canvas.width*scale));small.height=Math.max(1,Math.round(canvas.height*scale));
        const context=small.getContext('2d');context.drawImage(photo,0,0,small.width,small.height);
        candidates=core.detect(context.getImageData(0,0,small.width,small.height).data,small.width,small.height).map(p=>({x:p.x*canvas.width/small.width,y:p.y*canvas.height/small.height,r:p.r/scale}));
        showCandidates=true;scan.textContent=candidates.length?'Hide suggestions':'Find possible models';draw();status.textContent=candidates.length?'Amber rings are possible models or terrain. Tap the actual acting NPO, then its '+second+'.':'No candidate positions found. Tap the acting NPO and its '+second+' manually.';
      }catch(error){status.textContent='Base scan unavailable. Mark positions manually.';}
    }
    scan.addEventListener('click',()=>{
      if(!photo||busy)return;
      if(candidates.length){showCandidates=!showCandidates;scan.textContent=showCandidates?'Hide suggestions':'Show suggestions';draw();}
      else scanPhoto();
    });
    get('[data-recon="reset"]').addEventListener('click',reset);
    canvas.addEventListener('click',event=>{
      if(!photo||busy||!enabled())return;
      let p=core.pointFromRect(event.clientX,event.clientY,canvas.getBoundingClientRect(),canvas.width,canvas.height);
      if(!p)return;
      // Use the user's exact touch. Unverified detections must not override it.
      if(!actor){actor=p;status.textContent='Tap the '+second+'.';}
      else if(!other){if(core.distance(actor,p)<Math.min(canvas.width,canvas.height)*.025){status.textContent='Choose a different position.';return;}other=p;status.textContent='Marked. Verify on the tabletop, then use the normal action controls.';}
      else{other=null;actor=p;status.textContent='Tap the '+second+'.';}
      draw();
    });
    details.addEventListener('toggle',()=>{if(!details.open){sequence++;busy=false;scan.disabled=false;photo=null;actor=null;other=null;candidates=[];canvas.width=1;canvas.height=1;workspace.hidden=true;status.textContent='Capture the current board from above, filling the frame.';}});
  };
  function refresh(){
    if(!enabled()){
      document.querySelectorAll('[data-recon-kind]').forEach(host=>{if(host.dataset.reconMounted){host.replaceChildren();delete host.dataset.reconMounted;}});
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
