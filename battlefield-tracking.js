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
function calibrationCore(){
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const ratio=(w,h)=>w>=h?30/22:22/30;
  function fit(w,h,margin=.06){
    const r=ratio(w,h),width=Math.min(w*(1-2*margin),h*(1-2*margin)*r),height=width/r;
    return {x:(w-width)/2,y:(h-height)/2,w:width,h:height};
  }
  function drag(rect,handle,dx,dy,w,h){
    if(handle==='move')return {...rect,x:clamp(rect.x+dx,0,w-rect.w),y:clamp(rect.y+dy,0,h-rect.h)};
    const r=rect.w/rect.h,sx=handle.includes('e')?1:-1,sy=handle.includes('s')?1:-1;
    const ax=sx===1?rect.x:rect.x+rect.w,ay=sy===1?rect.y:rect.y+rect.h;
    const wanted=rect.w+(sx*dx+sy*dy/r)/(1+1/(r*r));
    const max=Math.min(sx===1?w-ax:ax,(sy===1?h-ay:ay)*r);
    const width=clamp(wanted,Math.min(max,Math.min(w,h)*.22),max),height=width/r;
    return {x:sx===1?ax:ax-width,y:sy===1?ay:ay-height,w:width,h:height};
  }
  const median=a=>{const b=[...a].sort((x,y)=>x-y);return b[Math.floor(b.length/2)];};
  // Find a long, consistent luminance transition on each side of a darker
  // central playing surface. A suggestion only: no automatic acceptance.
  function detect(data,w,h){
    if(w<80||h<80||data.length!==w*h*4)return null;
    const gray=new Float32Array(w*h);
    // Warm wooden surrounds remain distinguishable even under uneven lighting.
    for(let i=0;i<gray.length;i++)gray[i]=.299*data[4*i]+.587*data[4*i+1]+.114*data[4*i+2]+1.6*(data[4*i]-data[4*i+2]);
    function line(vertical,far){
      const across=vertical?w:h,along=vertical?h:w,window=Math.max(3,Math.round(across*.012)),rows=[];
      const pixel=(a,b)=>vertical?gray[b*w+a]:gray[a*w+b];
      const start=Math.max(window,Math.round(across*(far?.60:.025))),end=Math.min(across-window,Math.round(across*(far?.975:.40)));
      for(let b=Math.round(along*.23);b<along*.78;b+=Math.max(2,Math.round(along*.018))){
        const scores=new Float32Array(across);
        for(let a=start;a<end;a++){
          let outside=0,inside=0;
          for(let k=1;k<=window;k++){outside+=pixel(a+(far?k:-k),b);inside+=pixel(a+(far?-k:k),b);}
          scores[a]=(outside-inside)/window;
        }
        rows.push({b,scores});
      }
      if(rows.length<12)return null;
      // Score continuous edge hypotheses across all sampled rows instead of
      // choosing the strongest individual reflection or terrain feature.
      let best=null;
      for(let step=-25;step<=25;step++){
        const m=step/100;
        for(let mid=start;mid<end;mid++){
          let support=0,total=0;
          for(const {b,scores} of rows){
            const a=Math.round(mid+m*(b-along/2));
            if(a<start+2||a>=end-2)continue;
            const score=Math.max(scores[a-2],scores[a-1],scores[a],scores[a+1],scores[a+2]);
            if(score>22)support++;
            total+=clamp(score,0,55);
          }
          if(support/rows.length<.78)continue;
          const rank=total/rows.length+180*(far?1-mid/across:mid/across);
          if(!best||rank>best.rank)best={m,mid,rank};
        }
      }
      if(!best)return null;
      // Refine the actual edge within the tolerance band, avoiding a systematic
      // inward bias from the hypothesis scoring.
      const hits=[];
      for(const {b,scores} of rows){
        const center=Math.round(best.mid+best.m*(b-along/2));
        let a=center,score=-Infinity;
        for(let x=Math.max(start,center-3);x<Math.min(end,center+4);x++)if(scores[x]>score){a=x;score=scores[x];}
        if(score>22)hits.push({a,b});
      }
      if(hits.length<10)return null;
      const mb=hits.reduce((v,p)=>v+p.b,0)/hits.length,ma=hits.reduce((v,p)=>v+p.a,0)/hits.length;
      const m=hits.reduce((v,p)=>v+(p.b-mb)*(p.a-ma),0)/hits.reduce((v,p)=>v+(p.b-mb)**2,0);
      return {m,c:ma-m*mb};
    }
    const l=line(true,false),r=line(true,true),t=line(false,false),b=line(false,true);
    if(!l||!r||!t||!b)return null;
    function intersection(v,horizontal){const y=(horizontal.m*v.c+horizontal.c)/(1-horizontal.m*v.m);return {x:v.m*y+v.c,y};}
    const q=[intersection(l,t),intersection(r,t),intersection(r,b),intersection(l,b)];
    if(q.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)||p.x<0||p.y<0||p.x>=w||p.y>=h))return null;
    const len=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),width=(len(q[0],q[1])+len(q[2],q[3]))/2,height=(len(q[0],q[3])+len(q[1],q[2]))/2;
    if(width<w*.58||height<h*.58||width/height<.48||width/height>2.1)return null;
    if((w/h<.87&&width>height)||(w/h>1.15&&height>width))return null;
    return q;
  }
  function project(q,u,v){
    const [a,b,c,d]=q,dx1=b.x-c.x,dx2=d.x-c.x,dx3=a.x-b.x+c.x-d.x,dy1=b.y-c.y,dy2=d.y-c.y,dy3=a.y-b.y+c.y-d.y,det=dx1*dy2-dx2*dy1;
    if(Math.abs(det)<1e-6)return null;
    const g=(dx3*dy2-dx2*dy3)/det,h=(dx1*dy3-dx3*dy1)/det,z=g*u+h*v+1;
    if(Math.abs(z)<1e-8)return null;
    return {x:((b.x-a.x+g*b.x)*u+(d.x-a.x+h*d.x)*v+a.x)/z,y:((b.y-a.y+g*b.y)*u+(d.y-a.y+h*d.y)*v+a.y)/z};
  }
  function warp(data,w,h,q,outW,outH,pad){
    const out=new Uint8ClampedArray(outW*outH*4),bw=outW-2*pad,bh=outH-2*pad;
    for(let y=0;y<outH;y++)for(let x=0;x<outW;x++){
      const p=project(q,(x-pad)/bw,(y-pad)/bh),i=(y*outW+x)*4;
      if(!p||p.x<0||p.y<0||p.x>w-1||p.y>h-1){out[i]=8;out[i+1]=20;out[i+2]=15;out[i+3]=255;continue;}
      const x0=Math.floor(p.x),y0=Math.floor(p.y),x1=Math.min(w-1,x0+1),y1=Math.min(h-1,y0+1),fx=p.x-x0,fy=p.y-y0;
      for(let k=0;k<3;k++)out[i+k]=(data[(y0*w+x0)*4+k]*(1-fx)+data[(y0*w+x1)*4+k]*fx)*(1-fy)+(data[(y1*w+x0)*4+k]*(1-fx)+data[(y1*w+x1)*4+k]*fx)*fy;
      out[i+3]=255;
    }
    return out;
  }
  return {fit,drag,detect,project,warp};
}
function mapCore(){
  // Digitized from Assets/Maps/mission-01..06.png, not the legacy schematic JSON.
  // Coordinates are in the map image's playable area (45,45)-(1035,885).
  const layouts={
    '01':{walls:[[178,62,178,331],[178,331,716,331],[312,331,312,870],[444,196,444,331],[580,196,580,331],[716,62,716,601],[312,601,851,601],[851,601,851,870],[447,736,716,736]],doors:[[178,130],[242,331],[380,331],[648,331],[716,130],[716,533],[380,601],[650,601],[312,805],[851,805]],terrain:[[282,162,27],[511,89,27],[853,200,27],[408,469,27],[599,460,51],[511,263,40],[578,811,40]],objectives:[[1035,465,'Escape']]},
    '02':{walls:[[446,62,446,331],[850,62,850,601],[178,331,850,331],[178,331,178,601],[178,601,850,601],[312,601,312,870],[578,331,578,870]],doors:[[446,130],[850,265],[381,331],[514,331],[178,537],[578,403],[850,536],[650,601],[312,668],[578,806]],terrain:[[607,79,27],[756,233,27],[311,467,27],[659,466,51],[448,737,27],[510,535,40],[510,668,40]],objectives:[]},
    '03':{walls:[[66,185,1011,185],[336,185,336,726],[738,185,738,726],[738,455,1011,455],[67,591,336,591],[336,726,1011,726]],doors:[[533,185],[945,185],[336,257],[336,525],[267,591],[738,523],[945,455],[679,726],[945,726]],terrain:[[211,461,27],[462,322,27],[535,454,51],[613,592,27],[942,322,27],[810,247,40],[810,665,40]],objectives:[[134,525,'Search site'],[467,455,'Search site'],[807,391,'Search site']]},
    '04':{walls:[[607,51,607,185],[470,185,1011,185],[470,185,470,455],[740,185,740,726],[67,455,1011,455],[202,455,202,727],[202,727,740,727]],doors:[[607,118],[675,185],[945,185],[470,385],[135,455],[675,455],[945,455],[202,525],[740,525],[406,727]],terrain:[[272,266,27],[401,271,40],[655,323,51],[882,289,27],[809,392,40],[406,589,27],[598,588,27]],objectives:[[655,323,'Sarcophagus']]},
    '05':{walls:[[66,185,470,185],[470,185,470,725],[740,78,740,322],[470,322,877,322],[877,322,877,592],[877,458,1011,458],[470,592,877,592],[202,318,202,585],[202,585,338,585],[67,725,470,725]],doors:[[268,185],[470,254],[740,148],[673,322],[812,322],[877,391],[945,458],[810,592],[470,391],[272,725]],terrain:[[605,201,27],[607,450,27],[742,454,27],[718,710,27],[285,385,51],[134,385,40],[943,532,40]],objectives:[]},
    '06':{walls:[[312,62,312,466],[588,62,588,604],[312,332,998,332],[178,466,178,870],[178,604,998,604],[451,466,451,870]],doors:[[312,264],[588,128],[648,332],[588,401],[451,533],[524,604],[657,604],[928,604],[178,804],[451,806]],terrain:[[454,131,27],[727,196,27],[510,261,40],[649,539,40],[727,472,27],[312,730,27],[671,740,51]],objectives:[[105,465,'Regroup zone']]}
  };
  function geometry(number,board,rotation=0,open=[],fit={sx:1,sy:1,dx:0,dy:0}){
    const l=layouts[String(number).padStart(2,'0')];if(!l||!board)return null;
    const W=board.x1-board.x0,H=board.y1-board.y0;
    const point=(x,y)=>{
      let u=(x-45)/990,v=(y-45)/840;
      for(let k=0;k<(rotation%4+4)%4;k++)[u,v]=[1-v,u];
      return {x:board.x0+W*(.5+(u-.5)*fit.sx+fit.dx),y:board.y0+H*(.5+(v-.5)*fit.sy+fit.dy)};
    };
    const doors=l.doors.map(([x,y],id)=>({...point(x,y),id,open:open.includes(id)}));
    const walls=[];
    for(const [x,y,xx,yy] of l.walls){
      const a=point(x,y),b=point(xx,yy),dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy);
      const gaps=doors.filter(d=>d.open&&Math.abs((d.x-a.x)*dy-(d.y-a.y)*dx)/len<2).map(d=>((d.x-a.x)*dx+(d.y-a.y)*dy)/len).filter(t=>t>0&&t<len).sort((a,b)=>a-b);
      let start=0;const half=1.05*W/board.width;
      for(const t of [...gaps,len+half]){const end=Math.min(len,t-half);if(end>start)walls.push([{x:a.x+dx*start/len,y:a.y+dy*start/len},{x:a.x+dx*end/len,y:a.y+dy*end/len}]);start=Math.max(start,t+half);}
    }
    const terrain=l.terrain.map(([x,y,r])=>({...point(x,y),r:r/990*W}));
    const objectives=l.objectives.map(([x,y,label])=>({...point(x,y),label}));
    return {walls,doors,terrain,objectives,rotation,fit};
  }
  function alignment(number,board,data,w,h){
    if(!layouts[String(number).padStart(2,'0')])return null;
    const gray=new Float32Array(w*h);for(let i=0;i<gray.length;i++)gray[i]=(data[i*4]+data[i*4+1]+data[i*4+2])/3;
    const sample=(x,y)=>gray[Math.max(0,Math.min(h-1,Math.round(y)))*w+Math.max(0,Math.min(w-1,Math.round(x)))];
    const edge=(p,n,offset)=>Math.abs(sample(p.x+n.x*offset,p.y+n.y*offset)-sample(p.x+n.x*(offset+2),p.y+n.y*(offset+2)));
    let best=null;
    for(let rotation=0;rotation<4;rotation++)for(const sx of [.9,1,1.1])for(const sy of [.9,1,1.1])for(const dx of [-.04,0,.04])for(const dy of [-.04,0,.04]){
      const fit={sx,sy,dx,dy},g=geometry(number,board,rotation,[],fit);let sum=0,count=0;
      for(const [a,b] of g.walls){const len=Math.hypot(b.x-a.x,b.y-a.y),n={x:-(b.y-a.y)/len,y:(b.x-a.x)/len};for(let t=10;t<len-10;t+=12){const p={x:a.x+(b.x-a.x)*t/len,y:a.y+(b.y-a.y)*t/len};if(p.x<15||p.x>w-15||p.y<15||p.y>h-15)continue;let e=0;for(const k of [-6,-4,-2,0,2,4,6])e=Math.max(e,edge(p,n,k));sum+=e-.5*(edge(p,n,12)+edge(p,n,-12));count++;}}
      const score=count?sum/count-2*(Math.abs(sx-1)+Math.abs(sy-1)):0;
      if(!best||score>best.score)best={rotation,fit,score};
    }
    return best;
  }
  return {geometry,alignment};
}
function snapCore(){
  const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  // Fit the circular base directly. Weapons, shadows and disconnected highlights
  // must not pull the selected center away from the physical miniature.
  const rays=Array.from({length:24},(_,k)=>[Math.cos(k*Math.PI/12),Math.sin(k*Math.PI/12)]);
  function snap(data,w,h,tap,r,blocked=()=>false){
    if(data.length!==w*h*4||!Number.isFinite(tap.x)||!Number.isFinite(tap.y)||!Number.isFinite(r))return null;
    r=Math.max(5,r);
    const search=r*.85,step=r>22?2:1,radiusStep=Math.max(1,Math.round(r/6));
    let best=null;
    for(let y=Math.max(0,Math.round(tap.y-search));y<=Math.min(h-1,tap.y+search);y+=step)
      for(let x=Math.max(0,Math.round(tap.x-search));x<=Math.min(w-1,tap.x+search);x+=step){
        const offset=dist({x,y},tap);if(offset>search)continue;
        for(let rad=r*.65;rad<=r*1.7;rad+=radiusStep){
          if(offset>rad*.9)continue; // A nearby empty floor tap is not a selection.
          let total=0,hits=0,quadrants=[0,0,0,0],valid=0;
          for(let k=0;k<rays.length;k++){
            const [dx,dy]=rays[k],ax=Math.round(x+dx*(rad-2)),ay=Math.round(y+dy*(rad-2)),bx=Math.round(x+dx*(rad+2)),by=Math.round(y+dy*(rad+2));
            if(ax<0||ay<0||bx<0||by<0||ax>=w||bx>=w||ay>=h||by>=h)continue;
            const i=(ay*w+ax)*4,j=(by*w+bx)*4;
            const edge=Math.max(Math.abs(data[i]-data[j]),Math.abs(data[i+1]-data[j+1]),Math.abs(data[i+2]-data[j+2]));
            valid++;total+=Math.min(edge,65);
            if(edge>=15){hits++;quadrants[Math.floor(k/6)]++;}
          }
          if(valid<22||hits<12||quadrants.slice(0,4).some(v=>v<2))continue;
          const score=total/24+hits*.65-offset*.6-Math.abs(rad-r)*.35;
          if(score>=26&&(!best||score>best.score))best={x,y,r,detectedRadius:rad,score};
        }
      }
    // Reject the winning fit when it is a known fixed terrain feature; do not
    // move the selection to a weaker, off-base match merely to avoid the mask.
    return best&&!blocked(best)?best:null;
  }
  return {snap};
}
function trackingUI(){
  const core=trackingCore(),calibration=calibrationCore(),maps=mapCore(),snapping=snapCore();
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
    if(!session||session.token!==config.token)session={token:config.token,board:null,positions:{},walls:[],objectives:[],mapped:false,frame:null,turn:null,activated:new Set(),ready:new Set(),meta:{},mapRotation:0,mapFit:null,openDoors:[]};
    preview=null;
    const s=session,models=config.models.map(m=>({...m,...(s.meta[m.key]?.base&&!m.base?{base:s.meta[m.key].base}:{}),...(m.side==='player'&&m.order==='Unknown'&&s.meta[m.key]?.order?{order:s.meta[m.key].order}:{})}));
    // A player may change order during their activation. Unknown must remain unknown until confirmed.
    if(s.frame)for(const m of models.filter(m=>m.side==='player'&&(s.turn!==config.turn||!s.activated.has(m.key)&&config.activated.includes(m.key))))if(config.models.find(x=>x.key===m.key)?.order==='Unknown')m.order='Unknown';
    let frame=null,positions={},board=null,walls=[],objectives=[],mapped=false,stage='photo',wallStart=null,selected='',plan=null,seq=0,raw=null,crop=null,dragging=null,autoRectified=false,mapLayout=null,rotation=0,mapFit=null,openDoors=[];
    host.innerHTML='<section class="recon-tracking"><p class="eyebrow">TACTICAL SCAN · EXPERIMENTAL</p><p class="rt-status" role="status" aria-live="polite"></p><div class="recon-upload"><label class="btn secondary">Take Photo<input type="file" accept="image/*" capture="environment" aria-label="Take tactical photo"></label><label class="btn ghost">Choose Photo<input type="file" accept="image/*" aria-label="Choose tactical photo"></label></div><div class="rt-work" hidden><div class="recon-frame"><canvas aria-label="Battlefield photograph and tactical overlays"></canvas></div><div class="rt-controls"></div></div><div class="wizard-actions"><button type="button" class="btn ghost rt-manual">Use Manual Guide</button></div></section>';
    const get=q=>host.querySelector(q),status=get('.rt-status'),canvas=get('canvas'),controls=get('.rt-controls'),work=get('.rt-work');
    const tell=t=>status.textContent=t;
    const button=(label,fn,kind='secondary')=>{const b=document.createElement('button');b.type='button';b.className='btn '+kind;b.textContent=label;b.onclick=fn;return b;};
    const live=()=>host.isConnected&&document.documentElement.dataset.experimental==='on'&&config.valid();
    const repaint=()=>{
      canvas.classList.toggle('rt-crop-mode',stage==='crop');
      if(!frame)return;
      draw(canvas,frame,positions,models,board,stage==='identify'&&mapLayout?[]:walls,stage==='identify'&&mapLayout?[]:objectives,plan,stage!=='plan');
      if(mapLayout&&stage==='terrain'){
        const c=canvas.getContext('2d');c.font='bold 11px system-ui';c.textAlign='center';
        for(const p of mapLayout.terrain){c.strokeStyle='#eacb83';c.lineWidth=1.3;c.setLineDash([3,3]);c.beginPath();c.arc(p.x,p.y,Math.max(5,p.r*.65),0,Math.PI*2);c.stroke();}c.setLineDash([]);
        for(const p of mapLayout.doors){c.fillStyle=p.open?'#76f5a8':'#f0c66a';c.fillRect(p.x-4,p.y-4,8,8);}
      }
      if(stage!=='crop'||!crop)return;
      const ctx=canvas.getContext('2d'),{x,y,w,h}=crop;
      ctx.fillStyle='rgba(3,12,8,.45)';ctx.beginPath();ctx.rect(0,0,canvas.width,canvas.height);ctx.rect(x,y,w,h);ctx.fill('evenodd');
      ctx.strokeStyle='#8ff5ca';ctx.lineWidth=2.5;ctx.strokeRect(x,y,w,h);
      const radius=Math.max(7,canvas.width/48);
      for(const [px,py] of [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]){
        ctx.beginPath();ctx.arc(px,py,radius+2,0,Math.PI*2);ctx.fillStyle='#07140f';ctx.fill();
        ctx.beginPath();ctx.arc(px,py,radius,0,Math.PI*2);ctx.fillStyle='#8ff5ca';ctx.fill();
      }
    };
    function refreshMap(realign=false){
      if(!config.missionNumber||!frame||!board)return;
      if(realign||!mapFit){const data=frame.getContext('2d').getImageData(0,0,frame.width,frame.height).data;const found=maps.alignment(config.missionNumber,board,data,frame.width,frame.height);if(!found)return;rotation=found.rotation;mapFit=found.fit;}
      mapLayout=maps.geometry(config.missionNumber,board,rotation,openDoors,mapFit);
      if(mapLayout){walls=mapLayout.walls;objectives=mapLayout.objectives;mapped=false;}
    }
    function update(){
      controls.replaceChildren();
      if(stage==='crop'){
        tell(autoRectified?'Board detected and straightened. Drag the frame or corner handles to fit the playable area.':'Align the frame with the playable board. Drag the frame or corner handles to adjust.');
        controls.append(button('Confirm Board Area',confirmCrop,'primary'),button('Rotate Photo 90°',rotatePhoto,'ghost'));
        if(autoRectified)controls.append(button('Use Original Photo',()=>{frame=raw;autoRectified=false;crop=calibration.fit(frame.width,frame.height);update();},'ghost'));
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
        if(!missing.length)controls.append(button('Confirm Operative Positions',()=>{if(mapLayout&&mapped)assess();else{stage='terrain';update();}},'primary'));
        if(mapLayout)controls.append(button('Review Mission Layout',()=>{stage='terrain';update();},'ghost'));
        controls.append(button('Adjust Board Crop',resetCalibration,'ghost'));
        controls.append(button('Clear Selected Marker',()=>{delete positions[selected];update();},'ghost'));
      }else if(stage==='terrain'){
        if(mapLayout){
          tell('Mission layout loaded automatically. Check the overlay against the board. Tap a hatchway square to mark it open or closed.');
          const note=document.createElement('p');note.className='rt-metadata';note.textContent='Amber: walls, terrain and closed hatchways. Green squares: open hatchways.';controls.append(note);
          const adjustments=document.createElement('details');adjustments.className='rt-map-adjust';
          const summary=document.createElement('summary');summary.textContent='Adjust mission alignment';adjustments.append(summary);
          const grid=document.createElement('div');grid.className='rt-actions';
          const change=(key,delta)=>{mapFit={...mapFit,[key]:Math.max(key.startsWith('s')?.65:-.25,Math.min(key.startsWith('s')?1.35:.25,mapFit[key]+delta))};refreshMap();repaint();const check=get('.rt-check input');if(check)check.checked=false;};
          for(const [label,key,delta] of [['← Left','dx',-.015],['Right →','dx',.015],['↑ Up','dy',-.015],['Down ↓','dy',.015],['Narrower','sx',-.025],['Wider','sx',.025],['Shorter','sy',-.025],['Taller','sy',.025]])grid.append(button(label,()=>change(key,delta),'ghost'));
          adjustments.append(grid);controls.append(adjustments,button('Rotate Mission Layout 90°',()=>{rotation=(rotation+1)%4;mapFit={sx:1,sy:1,dx:0,dy:0};openDoors=[];refreshMap();update();},'ghost'),button('Auto-align Mission Layout',()=>{openDoors=[];refreshMap(true);update();},'ghost'),button('Recalibrate Photo',resetCalibration,'ghost'));
        }else{
          tell('No verified mission layout is available. Use the manual guide or mark blocking terrain.');
          const group=document.createElement('div');group.className='rt-actions';
          group.append(button('Mark Wall',()=>{stage='wall';wallStart=null;update();}),button('Mark Objective',()=>{stage='objective';update();}),button('Undo Wall',()=>{walls.pop();repaint();update();},'ghost'),button('Undo Objective',()=>{objectives.pop();repaint();update();},'ghost'));
          controls.append(group);
        }
        const unresolved=models.filter(m=>!m.base);if(unresolved.length){const note=document.createElement('p');note.className='rt-metadata';note.textContent='Base size required for '+unresolved.map(m=>m.name).join(', ')+'.';controls.append(note,button('Set Missing Base Sizes',()=>{selected=unresolved[0].key;stage='identify';update();}));}
        const unknown=models.filter(m=>m.side==='player'&&m.order==='Unknown');if(unknown.length){const note=document.createElement('p');note.className='rt-metadata';note.textContent='Unknown orders may prevent shooting recommendations. Update them if needed.';controls.append(note,button('Review Player Orders',()=>{selected=unknown[0].key;stage='identify';update();},'ghost'));}
        const check=document.createElement('label');check.className='rt-check';const input=document.createElement('input');input.type='checkbox';input.checked=mapped;input.onchange=()=>{mapped=input.checked;};check.append(input,document.createTextNode(mapLayout?' Mission overlay matches the physical board, including hatchway states.':' All blocking terrain is marked; verify physical board and open hatchways.'));controls.append(check);
                const missing=models.some(m=>!positions[m.key]);
        controls.append(button(mapLayout&&missing?'Confirm Mission Layout':config.setup?'Finish Recon Setup':'Assess Battlefield',()=>{if(mapLayout&&!mapped){tell('Confirm the overlay and hatchway states first.');return;}if(mapLayout&&missing){stage='identify';update();return;}assess();},'primary'));
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
    function resetCalibration(){
      if(!raw)return;
      positions={};board=null;walls=[];objectives=[];mapped=false;mapLayout=null;mapFit=null;plan=null;dragging=null;frame=raw;autoRectified=false;
      const ctx=raw.getContext('2d'),data=ctx.getImageData(0,0,raw.width,raw.height).data,q=calibration.detect(data,raw.width,raw.height);
      if(q){
        const horizontal=Math.hypot(q[1].x-q[0].x,q[1].y-q[0].y)>=Math.hypot(q[3].x-q[0].x,q[3].y-q[0].y);
        const w=horizontal?600:440,h=horizontal?440:600,pad=24;
        const corrected=document.createElement('canvas');corrected.width=w+2*pad;corrected.height=h+2*pad;
        const c=corrected.getContext('2d'),im=c.createImageData(corrected.width,corrected.height);
        im.data.set(calibration.warp(data,raw.width,raw.height,q,corrected.width,corrected.height,pad));c.putImageData(im,0,0);
        frame=corrected;crop={x:pad,y:pad,w,h};autoRectified=true;
      }else crop=calibration.fit(frame.width,frame.height);
      stage='crop';update();
    }
    function rotatePhoto(){
      if(!frame)return;
      const rotated=document.createElement('canvas');rotated.width=frame.height;rotated.height=frame.width;
      const c=rotated.getContext('2d');c.translate(rotated.width,0);c.rotate(Math.PI/2);c.drawImage(frame,0,0);
      crop={x:frame.height-crop.y-crop.h,y:crop.x,w:crop.h,h:crop.w};frame=rotated;update();
    }
    function confirmCrop(){
      if(!live()||!crop)return;
      const out=document.createElement('canvas'),landscape=crop.w>crop.h;
      out.width=landscape?600:440;out.height=landscape?440:600;
      out.getContext('2d').drawImage(frame,crop.x,crop.y,crop.w,crop.h,0,0,out.width,out.height);
      frame=out;crop=null;board={x0:0,y0:0,x1:out.width,y1:out.height,width:landscape?30:22,height:landscape?22:30};
      if(s.frame&&s.board&&s.frame.width===out.width&&s.frame.height===out.height){
        const data=out.getContext('2d').getImageData(0,0,out.width,out.height).data,before=s.frame.getContext('2d').getImageData(0,0,out.width,out.height).data;
        let delta=0,count=0;
        for(let y=12;y<out.height-12;y+=13)for(let x=12;x<out.width-12;x+=13){if(Object.values(s.positions).some(p=>core.dist(p,{x,y})<(p.r||8)*2))continue;const i=(y*out.width+x)*4;delta+=(Math.abs(data[i]-before[i])+Math.abs(data[i+1]-before[i+1])+Math.abs(data[i+2]-before[i+2]))/3;count++;}
        if(count&&delta/count<16){
          walls=s.walls.map(w=>w.map(p=>({...p})));objectives=s.objectives.map(p=>({...p}));mapped=false;
          if(config.missionNumber){rotation=s.mapRotation;mapFit=s.mapFit;openDoors=[...s.openDoors];refreshMap();}
          const changed=new Set(models.filter(m=>m.side==='player'&&(!s.activated.has(m.key)&&config.activated.includes(m.key)||s.turn!==config.turn)||m.side==='npo'&&(s.ready.has(m.key)&&!config.ready.includes(m.key)||m.key===config.actorKey||s.turn!==config.turn)).map(m=>m.key));
          const matches=core.track(s.positions,data,out.width,out.height,board,models,changed);
          positions=Object.fromEntries(Object.entries(matches).filter(([,p])=>p));stage='review';update();return;
        }
      }
      positions={};walls=[];objectives=[];mapped=false;selected='';openDoors=[];refreshMap(true);stage=mapLayout?'terrain':'identify';update();
    }
    function assess(){
      if(!live()||!board||models.some(m=>!positions[m.key]))return;
      if(mapLayout&&!mapped){tell('Confirm that the mission overlay matches the physical board before proceeding.');return;}
      s.meta=Object.fromEntries(models.map(m=>[m.key,{base:m.base,order:m.order}]));s.frame=frame;s.board={...board};s.positions={...positions};s.walls=walls.map(w=>w.map(p=>({...p})));s.objectives=objectives.map(p=>({...p}));s.mapped=mapped;s.turn=config.turn;s.activated=new Set(config.activated);s.ready=new Set(config.ready);s.scanKey=config.scanKey;s.mapRotation=rotation;s.mapFit=mapFit;s.openDoors=[...openDoors];
      if(config.setup){config.complete();return;}
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
        next.getContext('2d').drawImage(im,0,0,next.width,next.height);raw=next;work.hidden=false;
        resetCalibration();
      }catch(e){if(ticket===seq&&live())tell('Could not read photo. Try a JPEG or another image.');}
      finally{if(url)URL.revokeObjectURL(url);}
    }
    host.querySelectorAll('input[type=file]').forEach(i=>i.onchange=()=>{const f=i.files?.[0];i.value='';if(f)void load(f);});
    get('.rt-manual').textContent=config.setup?'Skip Recon Setup':'Use Manual Guide';
    get('.rt-manual').onclick=()=>{seq++;preview=null;config.manual();};
    function canvasPoint(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*canvas.width/r.width,y:(e.clientY-r.top)*canvas.height/r.height};}
    canvas.addEventListener('pointerdown',e=>{
      if(stage!=='crop'||!crop||!live())return;
      const p=canvasPoint(e),radius=Math.max(15,canvas.width/23),corners=[['nw',crop.x,crop.y],['ne',crop.x+crop.w,crop.y],['se',crop.x+crop.w,crop.y+crop.h],['sw',crop.x,crop.y+crop.h]];
      const handle=corners.find(([,x,y])=>Math.hypot(p.x-x,p.y-y)<=radius)?.[0]||(p.x>=crop.x&&p.x<=crop.x+crop.w&&p.y>=crop.y&&p.y<=crop.y+crop.h?'move':null);
      if(!handle)return;
      e.preventDefault();dragging={handle,p,rect:{...crop},id:e.pointerId};canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove',e=>{
      if(stage!=='crop'||dragging?.id!==e.pointerId)return;
      const p=canvasPoint(e);crop=calibration.drag(dragging.rect,dragging.handle,p.x-dragging.p.x,p.y-dragging.p.y,canvas.width,canvas.height);repaint();
    });
    const endDrag=e=>{if(dragging?.id===e.pointerId)dragging=null;};
    canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);canvas.addEventListener('lostpointercapture',endDrag);
    canvas.onclick=e=>{
      if(!frame||!live())return;
      const rect=canvas.getBoundingClientRect(),p={x:(e.clientX-rect.left)*canvas.width/rect.width,y:(e.clientY-rect.top)*canvas.height/rect.height};
      if(stage==='crop')return;
      if(!board||!core.inside(p,board))return;
      if(stage==='identify'){
        const m=models.find(m=>m.key===selected);if(!m)return;
        const r=Math.max(5,Math.round((m.base||32)/50.8*(board.x1-board.x0)/board.width));
        const data=frame.getContext('2d').getImageData(0,0,frame.width,frame.height).data;
        const blocked=q=>Boolean(mapLayout&&mapped&&(mapLayout.walls.some(([a,b])=>core.segmentDistance(q,a,b)<r*.22)||mapLayout.terrain.some(t=>core.dist(q,t)<Math.min(t.r*.45,r*.65))));
        const hit=snapping.snap(data,frame.width,frame.height,p,r,blocked);
        if(!hit){tell('No miniature base detected at that spot. Tap the centre of its base and try again.');return;}
        if(Object.entries(positions).some(([k,v])=>k!==selected&&core.dist(hit,v)<Math.max(5,r*.85))){tell('That miniature is already assigned. Select a different model.');return;}
        positions[selected]={x:hit.x,y:hit.y,r,template:core.patch(data,frame.width,frame.height,hit,r)};
        selected=models.find(m=>!positions[m.key])?.key||selected;update();
      }else if(stage==='terrain'&&mapLayout){const door=mapLayout.doors.reduce((best,d)=>core.dist(d,p)<12&&(!best||core.dist(d,p)<core.dist(best,p))?d:best,null);if(door){openDoors=door.open?openDoors.filter(id=>id!==door.id):[...openDoors,door.id];refreshMap();update();}}
      else if(stage==='wall'){if(!wallStart){wallStart=p;update();}else{if(core.dist(wallStart,p)<4)return;walls.push([wallStart,p]);mapped=false;wallStart=null;stage='terrain';update();}}
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
if(typeof module!=='undefined')module.exports={...trackingCore(),calibration:calibrationCore(),maps:mapCore(),snapping:snapCore()};
