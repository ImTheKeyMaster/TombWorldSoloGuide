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
  // Compare the confirmed board to a newly normalized photo. Local hatchway
  // changes invalidate terrain even if the overall board still matches.
  function compareBoard(before,after,w,h,positions={},doors=[]){
    const pixelDelta=(x,y)=>{const i=(y*w+x)*4;return (Math.abs(before[i]-after[i])+Math.abs(before[i+1]-after[i+1])+Math.abs(before[i+2]-after[i+2]))/3;};
    let delta=0,count=0;
    for(let y=12;y<h-12;y+=13)for(let x=12;x<w-12;x+=13){
      if(Object.values(positions).some(p=>dist(p,{x,y})<(p.r||8)*2))continue;
      delta+=pixelDelta(x,y);count++;
    }
    const aligned=count>0&&delta/count<16;
    const changedDoors=doors.filter(d=>{
      let sum=0,n=0,changed=0;
      for(let y=Math.max(0,Math.round(d.y)-12);y<=Math.min(h-1,Math.round(d.y)+12);y+=2)
        for(let x=Math.max(0,Math.round(d.x)-12);x<=Math.min(w-1,Math.round(d.x)+12);x+=2){
          const diff=pixelDelta(x,y);sum+=diff;n++;if(diff>35)changed++;
        }
      return !n||sum/n>18||changed/n>.2;
    });
    return {aligned,terrainStable:aligned&&!changedDoors.length};
  }
  // Segment clearance checks keep both the grid edges and the simplified
  // movement overlay outside walls and the other models' bases.
  function segmentGap(a,b,c,d){
    const cross=(p,q,r)=>(q.x-p.x)*(r.y-p.y)-(q.y-p.y)*(r.x-p.x);
    if(cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0)return 0;
    return Math.min(segmentDistance(a,c,d),segmentDistance(b,c,d),segmentDistance(c,a,b),segmentDistance(d,a,b));
  }
  function routeGrid(board,start,legal,strategic,max){
    const step=.5,cols=Math.ceil(board.width/step),rows=Math.ceil(board.height/step),nodes=[];
    for(let y=0;y<rows;y++)for(let x=0;x<cols;x++)nodes.push({x:(x+.5)*step,y:(y+.5)*step});
    const edges=nodes.map(()=>[]),seeds=[];
    for(let i=0;i<nodes.length;i++){
      const p=nodes[i],x=i%cols,y=Math.floor(i/cols);
      if(dist(start,p)<=.9&&legal(start,p))seeds.push([i,dist(start,p)]);
      if(!strategic(p,p))continue;
      for(const [dx,dy] of [[1,0],[0,1],[1,1],[-1,1]]){
        const nx=x+dx,ny=y+dy;if(nx<0||nx>=cols||ny>=rows)continue;
        const j=ny*cols+nx,q=nodes[j];if(!strategic(p,q))continue;
        const cost=dist(p,q),open=legal(p,q);
        // Closed hatchways may be future routes, never part of the current move.
        const edge={to:j,cost,open},back={...edge,to:i};edges[i].push(edge);edges[j].push(back);
      }
    }
    function search(initial,future,limit=Infinity){
      const distance=new Float64Array(nodes.length).fill(Infinity),prev=new Int32Array(nodes.length).fill(-1),heap=[];
      function push(item){let i=heap.length;heap.push(item);while(i){const j=(i-1)>>1;if(heap[j][1]<=item[1])break;heap[i]=heap[j];i=j;}heap[i]=item;}
      function pop(){const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(2*i+1<heap.length){let j=2*i+1;if(j+1<heap.length&&heap[j+1][1]<heap[j][1])j++;if(heap[j][1]>=last[1])break;heap[i]=heap[j];i=j;}heap[i]=last;}return first;}
      for(const [i,d] of initial)if(d<distance[i]){distance[i]=d;push([i,d]);}
      while(heap.length){const [i,d]=pop();if(d!==distance[i]||d>limit)continue;
        for(const e of edges[i]){
          if(!e.open&&!future)continue;
          const v=d+e.cost+(e.open?0:1.5);
          if(v<=limit&&v<distance[e.to]-1e-8){distance[e.to]=v;prev[e.to]=i;push([e.to,v]);}
        }
      }
      return {distance,prev};
    }
    const reach=search(seeds,false,max);
    function path(i){
      const raw=[];for(let j=i;j>=0;j=reach.prev[j])raw.push(nodes[j]);raw.reverse();raw.unshift(start);
      const out=[start];let k=0;while(k<raw.length-1){let j=raw.length-1;while(j>k+1&&!legal(raw[k],raw[j]))j--;out.push(raw[j]);k=j;}return out;
    }
    return {nodes,seeds,reach,path,field:goals=>search(goals.map(i=>[i,0]),true)};
  }
  function plan({board,positions,models,walls=[],objectives=[],doors=[],futureWalls=null,terrain=[],mapped=false,actorKey=null,actionOrder,diagnostics=[]}){
    const report=(code,message,actor=null)=>{diagnostics.push({code,message,actor:actor?.key||null});return null;};
    if(!board)return report('board','The playable board has not been calibrated.');
    if(!mapped)return report('terrain','Confirm the mission layout and hatchway states.');
    if(!models.length)return report('roster','No deployed operatives were supplied.');
    const missing=models.filter(m=>!positions[m.key]);
    if(missing.length)return report('positions','Missing positions: '+missing.map(m=>m.name||m.key).join(', ')+'.');
    const sizes=models.filter(m=>!Number.isFinite(m.base)||m.base<=0);
    if(sizes.length)return report('base','Base diameter needed: '+sizes.map(m=>m.name||m.key).join(', ')+'.');
    const units=models.map(m=>({...m,p:physical(positions[m.key],board),r:m.base/50.8}));
    const players=units.filter(m=>m.side==='player'),npos=units.filter(m=>m.side==='npo'),ready=npos.filter(m=>m.ready&&(!actorKey||m.key===actorKey));
    if(!players.length)return report('enemies','No living player operatives on the board.');
    if(!ready.length)return report('ready','No ready NPO is available for this activation.');
    const barriers=walls.map(w=>w.map(p=>physical(p,board)));
    const obj=objectives.map(p=>({...physical(p,board),label:p.label||'mission objective'}));
    const futureBarriers=(futureWalls||walls).map(w=>w.map(p=>physical(p,board)));
    const obstacles=terrain.map(t=>({...physical(t,board),r:t.r/(board.x1-board.x0)*board.width*.65}));
    const closedDoors=doors.filter(d=>!d.open).map(d=>({...physical(d,board),id:d.id}));
    const edge=(a,b)=>Math.max(0,dist(a.p,b.p)-a.r-b.r);
    function clear(a,b,r=0,segments=barriers){
      return !segments.some(([s,t])=>segmentGap(a,b,s,t)<r+.12);
    }
    const visible=(a,b)=>clear(a.p,b.p,0);
    const control=(a,b)=>edge(a,b)<=.93&&visible(a,b);
    const shooting=(a,b,from=a.p)=>a.canShoot&&b.order==='Engage'&&clear(from,b.p,0)&&(!Number.isFinite(a.range)||Math.max(0,dist(from,b.p)-a.r-b.r)<=a.range-.12);
    function targets(a,kind,from=a.p){
      return players.filter(b=>kind==='fight'?control(a,b):shooting(a,b,from)).sort((b,c)=>b.wounds-c.wounds||dist(from,b.p)-dist(from,c.p)||Number(c.ready)-Number(b.ready));
    }
    const ranking=ready.map(a=>({a,threat:Number(targets(a,'fight').length>0||targets(a,'shoot').length>0),distance:Math.min(...players.map(b=>edge(a,b))),objective:obj.length?Math.min(...obj.map(p=>dist(a.p,p))):Infinity})).sort((b,c)=>c.threat-b.threat||b.distance-c.distance||b.objective-c.objective);
    // A candidate that requires a tabletop ruling must not prevent another ready NPO from acting.
    function evaluate(a){
    const skipped=[];
    const inControl=players.some(b=>control(a,b));
    // Borderline base-to-base estimates cannot establish control range reliably.
    if(players.some(b=>Math.abs(edge(a,b)-1)<.15&&visible(a,b)))return report('control','Control range is too close to the 1-inch boundary to estimate reliably.',a);
    const order=actionOrder(a,inControl);
    const canFollow=id=>a.ap>=2&&Array.isArray(order)&&order.some(name=>String(name).toLowerCase().split(' ')[0]===id);
    function legalSegment(from,to,chargeTarget=null,segments=barriers){
      if(to.x<a.r+.1||to.y<a.r+.1||to.x>board.width-a.r-.1||to.y>board.height-a.r-.1||!clear(from,to,a.r,segments))return false;
      if(obstacles.some(t=>segmentDistance(t,from,to)<a.r+t.r+.08))return false;
      for(const b of units.filter(b=>b.key!==a.key)){
        if(segmentDistance(b.p,from,to)<a.r+b.r+.08)return false;
        if(b.side==='player'&&b.key!==chargeTarget?.key&&segmentDistance(b.p,from,to)<a.r+b.r+1.04)return false;
      }
      return true;
    }
    function result(grid,i,extra){
      const path=grid.path(i),distance=path.slice(1).reduce((v,p,j)=>v+dist(path[j],p),0);
      return {destination:imagePoint(path.at(-1),board),path:path.map(p=>imagePoint(p,board)),distance,...extra};
    }
    function movement(kind){
      if(inControl||!Number.isFinite(a.move))return null;
      const max=(kind==='dash'?3:kind==='charge'?a.move+2:a.move)-.12;
      if(kind==='charge'){
        let best=null;
        for(const target of players){
          const legal=(p,q)=>legalSegment(p,q,target),grid=routeGrid(board,a.p,legal,legal,max);
          grid.nodes.forEach((p,i)=>{
            const d=grid.reach.distance[i],gap=dist(p,target.p)-a.r-target.r;
            if(!Number.isFinite(d)||gap<.1||gap>.85||!clear(p,target.p))return;
            const score=target.wounds*100+d;
            if(!best||score<best.score)best={score,move:result(grid,i,{target:target.key,intent:'Reach '+(target.name||'the enemy')+' in control range.',followUp:canFollow('fight')?'fight':null})};
          });
        }
        return best?.move||null;
      }
      const legal=(p,q)=>legalSegment(p,q),strategic=(p,q)=>legalSegment(p,q,null,a.operatesHatches?futureBarriers:barriers);
      const grid=routeGrid(board,a.p,legal,strategic,max);
      const focus=a.focus,shootFocus=focus==='shoot'&&a.canShoot;
      const firing=(p,b)=>clear(p,b.p)&&(!Number.isFinite(a.range)||Math.max(0,dist(p,b.p)-a.r-b.r)<=a.range-.12);
      // Use actual firing positions as goals, rather than the enemy's centre.
      // Future routes may use an opened hatch, but the movement itself cannot.
      const known=players.filter(b=>b.order==='Engage'),potential=players.filter(b=>b.order!=='Engage');
      const shootingGoals=list=>grid.nodes.flatMap((p,i)=>strategic(p,p)&&list.some(b=>firing(p,b))?[i]:[]);
      const groups=[];
      if(shootFocus){
        const goals=shootingGoals(known);if(goals.length)groups.push({goals,type:'shoot',targets:known});
      }
      if(focus==='fight'){
        const nearest=[...players].sort((b,c)=>edge(a,b)-edge(a,c))[0];
        const goals=grid.nodes.flatMap((p,i)=>strategic(p,p)&&dist(p,nearest.p)-a.r-nearest.r<=1.85&&clear(p,nearest.p)?[i]:[]);
        if(goals.length)groups.push({goals,type:'fight',targets:[nearest]});
      }
      if(focus==='warden'){
        const leader=npos.find(n=>n.type==='Royal Warden');
        if(leader){const goals=grid.nodes.flatMap((p,i)=>strategic(p,p)&&dist(p,leader.p)-a.r-leader.r<=2?[i]:[]);if(goals.length)groups.push({goals,type:'warden',targets:[leader]});}
      }
      if(obj.length){
        const goals=grid.nodes.flatMap((p,i)=>strategic(p,p)&&obj.some(o=>dist(p,o)<=2)?[i]:[]);
        if(goals.length)groups.push({goals,type:'mission'});
      }
      if(shootFocus&&potential.length){const goals=shootingGoals(potential);if(goals.length)groups.push({goals,type:'potential',targets:potential});}
      // An immediately attainable shot outranks longer-term positioning.
      if(shootFocus&&canFollow('shoot')){
        let best=null;
        grid.nodes.forEach((p,i)=>{const d=grid.reach.distance[i];if(!Number.isFinite(d)||d<.25)return;const t=targets(a,'shoot',p)[0];if(!t)return;const score=t.wounds*100+d;if(!best||score<best.score)best={i,t,score};});
        if(best)return result(grid,best.i,{target:best.t.key,intent:'Establish a firing position against '+(best.t.name||'the enemy')+'.',followUp:'shoot'});
      }
      for(const group of groups){
        const field=grid.field(group.goals),baseline=Math.min(...grid.seeds.map(([i,d])=>field.distance[i]+d));
        if(!Number.isFinite(baseline)||baseline<.4)continue;
        let best=null;
        grid.nodes.forEach((p,i)=>{
          const d=grid.reach.distance[i],remaining=field.distance[i];
          if(!Number.isFinite(d)||!Number.isFinite(remaining)||d<.25||baseline-remaining<.45)return;
          const score=remaining+d*.03;
          if(!best||score<best.score)best={i,score};
        });
        if(!best)continue;
        let end=best.i,hatch=null,prior=end;
        while(field.prev[end]>=0){
          const next=field.prev[end],p=grid.nodes[end],q=grid.nodes[next];
          if(!legal(p,q)&&closedDoors.length&&!hatch)hatch=[...closedDoors].sort((b,c)=>segmentDistance(b,p,q)-segmentDistance(c,p,q))[0];
          prior=end;end=next;
        }
        const goal=grid.nodes[end],target=group.targets?.filter(b=>group.type!=='shoot'&&group.type!=='potential'||firing(goal,b)).sort((b,c)=>dist(goal,b.p)-dist(goal,c.p))[0];
        const objective=group.type==='mission'?[...obj].sort((b,c)=>dist(goal,b)-dist(goal,c))[0]:null;
        const intent=group.type==='shoot'?'Advance along a reachable route toward a firing position against '+(target?.name||'the enemy')+'.':
          group.type==='potential'?'Advance toward a potential firing position; verify the enemy order and cover before shooting.':
          group.type==='fight'?'Close the distance along a reachable route to '+(target?.name||'the enemy')+'.':
          group.type==='warden'?'Move toward the Royal Warden.':'Move to help contest or defend '+(objective?.label||'the mission objective')+'.';
        return result(grid,best.i,{goalTarget:target?.key||null,goal:imagePoint(goal,board),intent,hatchway:hatch?imagePoint(hatch,board):null,followUp:null});
      }
      return null;
    }
    if(!Array.isArray(order)||!order.length)return report('actions','No legal actions are available in the current activation.',a);
    for(const name of order){
      const id=String(name).toLowerCase().split(' ')[0];
      if(id==='fight'){
        const target=targets(a,'fight')[0];if(target)return {actor:a.key,action:name,id,target:target.key,inControl,shootable:targets(a,'shoot').length>0,fightable:true,skipped};
      }else if(id==='shoot'){
        if(inControl)continue;
        const target=targets(a,'shoot')[0];if(target)return {actor:a.key,action:name,id,target:target.key,inControl,shootable:true,fightable:false,skipped};
        // Conceal/cover and unknown orders cannot be treated as proof no target exists.
        if(a.canShoot&&players.some(b=>b.order!=='Engage'&&visible(a,b)&&(!Number.isFinite(a.range)||edge(a,b)<=a.range)))return report('orders','A visible enemy has an unknown or Conceal order; shooting eligibility needs a tabletop check.',a);
      }else if(['charge','reposition','dash'].includes(id)){
        if(inControl)continue;
        if(!Number.isFinite(a.move))return report('move-stat','Movement allowance is missing.',a);
        const move=movement(id);
        if(move)return {actor:a.key,action:name,id,...move,inControl,shootable:targets(a,'shoot').length>0,fightable:false,skipped};
        // Search lower-priority movement options, but explicitly flag that curved
        // routes for the higher-priority action have not been ruled out.
        skipped.push({action:name,reason:'No supported route within the movement allowance found.'});
      }else if(id==='fall'){
        if(inControl)return report('fall-back','Fall Back requires a tabletop route check.',a);
      }else return report('special',name+' requires a tabletop rules check.',a);
    }
    return report('route',skipped.length?'No reachable tactical position or eligible attack found. Check hatchway access, terrain and special rules.':'No eligible attack or movement that improves a tactical goal was found.',a);
    }
    for(const {a} of ranking){const result=evaluate(a);if(result)return result;}
    return null;
  }
  return {dist,inside,physical,imagePoint,segmentDistance,segmentGap,routeGrid,patch,matchScore,track,compareBoard,plan};
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
  // Use fixed reference bounds from the unscaled terrain, independent of
  // hatchway state. The mission overlay can stretch independently in X/Y;
  // this never changes the calibrated physical killzone or model positions.
  function fitBounds(number,board,rotation){
    const g=geometry(number,board,rotation);
    if(!g)return null;
    const pts=[...g.walls.flat(),...g.terrain,...g.doors];
    const W=board.x1-board.x0,H=board.y1-board.y0;
    return {l:Math.min(...pts.map(p=>(p.x-board.x0)/W)),r:Math.max(...pts.map(p=>(p.x-board.x0)/W)),
      t:Math.min(...pts.map(p=>(p.y-board.y0)/H)),b:Math.max(...pts.map(p=>(p.y-board.y0)/H))};
  }
  function fitRect(board,bounds,fit){
    const W=board.x1-board.x0,H=board.y1-board.y0;
    return {x:board.x0+W*(.5+(bounds.l-.5)*fit.sx+fit.dx),y:board.y0+H*(.5+(bounds.t-.5)*fit.sy+fit.dy),
      w:W*(bounds.r-bounds.l)*fit.sx,h:H*(bounds.b-bounds.t)*fit.sy};
  }
  function dragFit(board,bounds,fit,handle,dx,dy){
    const clamp=(v,l,h)=>Math.max(l,Math.min(h,v)),W=board.x1-board.x0,H=board.y1-board.y0;
    if(handle==='move')return {...fit,dx:clamp(fit.dx+dx/W,-.25,.25),dy:clamp(fit.dy+dy/H,-.25,.25)};
    function axis(lo,hi,s,d,delta,lower){
      const anchor=(lower?hi:lo)-.5;
      let min=.65,max=1.35;
      if(Math.abs(anchor)>1e-9){
        const a=s+(d-.25)/anchor,b=s+(d+.25)/anchor;
        min=Math.max(min,Math.min(a,b));max=Math.min(max,Math.max(a,b));
      }
      const scale=clamp(s+(lower?-1:1)*delta/(hi-lo),min,max);
      return [scale,clamp(d-anchor*(scale-s),-.25,.25)];
    }
    const [sx,x]=axis(bounds.l,bounds.r,fit.sx,fit.dx,dx/W,handle.includes('w'));
    const [sy,y]=axis(bounds.t,bounds.b,fit.sy,fit.dy,dy/H,handle.includes('n'));
    return {sx,sy,dx:x,dy:y};
  }
  return {geometry,alignment,fitBounds,fitRect,dragFit};
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
  let session=null,preview=null,continuation=null;
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function draw(canvas,frame,positions,models,board,walls,objectives,plan,showLabels,nextPlan=null,projected=false){
    const ctx=canvas.getContext('2d');
    canvas.width=frame.width;canvas.height=frame.height;ctx.drawImage(frame,0,0);
    const ring=(p,color,r=11,dash=false)=>{ctx.save();ctx.setLineDash(dash?[5,4]:[]);ctx.strokeStyle='#06100c';ctx.lineWidth=5;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.stroke();ctx.strokeStyle=color;ctx.lineWidth=2.5;ctx.stroke();ctx.restore();};
    const line=(a,b,c,dash=false,arrow=false)=>{ctx.save();ctx.setLineDash(dash?[7,5]:[]);ctx.strokeStyle='#06100c';ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.strokeStyle=c;ctx.lineWidth=3;ctx.stroke();ctx.setLineDash([]);if(arrow){const t=Math.atan2(b.y-a.y,b.x-a.x);ctx.fillStyle=c;ctx.beginPath();ctx.moveTo(b.x,b.y);ctx.lineTo(b.x-12*Math.cos(t-.5),b.y-12*Math.sin(t-.5));ctx.lineTo(b.x-12*Math.cos(t+.5),b.y-12*Math.sin(t+.5));ctx.fill();}ctx.restore();};
    if(board&&showLabels){ctx.strokeStyle='#81b8ae';ctx.lineWidth=2;ctx.strokeRect(board.x0,board.y0,board.x1-board.x0,board.y1-board.y0);}
    if(showLabels){walls.forEach(([a,b])=>line(a,b,'#f0c66a'));objectives.forEach(p=>ring(p,'#f0c66a',8,true));}
    if(showLabels)models.forEach((m,i)=>{const p=positions[m.key];if(!p)return;const c=m.side==='npo'?'#76f5a8':'#91caff';ring(p,c,Math.max(8,p.r||10));ctx.font='bold 11px system-ui';ctx.fillStyle='#06100c';ctx.fillRect(p.x-9,p.y-19,19,13);ctx.fillStyle=c;ctx.textAlign='center';ctx.fillText(String(i+1),p.x,p.y-9);});
    if(plan){
      const origin=positions[plan.actor];
      if(origin){
        const green='#76f5a8',red='#ff7f83',amber='#f0c66a',labels=[];
        let marker=1;
        const tag=(p,text,color,radius=13)=>{
          ctx.save();ctx.font='bold 12px system-ui';ctx.textAlign='left';ctx.textBaseline='middle';
          const w=ctx.measureText(text).width+12,h=19;
          const candidates=[[p.x-w/2,p.y-radius-h-4],[p.x-w/2,p.y+radius+4],[p.x+radius+5,p.y-h/2],[p.x-radius-w-5,p.y-h/2]].map(([x,y])=>({x:Math.max(2,Math.min(canvas.width-w-2,x)),y:Math.max(2,Math.min(canvas.height-h-2,y)),w,h}));
          const overlaps=(a,b)=>a.x<b.x+b.w+3&&a.x+a.w+3>b.x&&a.y<b.y+b.h+3&&a.y+a.h+3>b.y;
          const rect=candidates.find(c=>labels.every(l=>!overlaps(c,l)))||candidates[0];labels.push(rect);
          ctx.fillStyle='#06100c';ctx.fillRect(rect.x,rect.y,w,h);ctx.strokeStyle=color;ctx.lineWidth=1;ctx.strokeRect(rect.x,rect.y,w,h);ctx.fillStyle=color;ctx.fillText(text,rect.x+6,rect.y+h/2);ctx.restore();
        };
        const marks=[];
        function action(p,start,future){
          const d=p.destination,t=positions[p.target];
          if(d){
            const route=p.path||[start,d];
            for(let i=1;i<route.length;i++)line(route[i-1],route[i],green,future,i===route.length-1);
            ring(d,green,Math.max(12,origin.r||10),true);
            marks.push([d,(marker++)+' '+(p.id==='dash'?'DASH HERE':'MOVE HERE'),green]);
          }
          if(t){
            // A movement's prospective target is not another AP unless the
            // second planned action is an actual attack.
            const attack=p.id==='shoot'||p.id==='fight',charge=p.id==='charge';
            if(attack||charge||(!nextPlan&&p.followUp)){
              line(d||start,t,red,true,true);ring(t,red,Math.max(12,t.r||10));
              marks.push([t,(marker++)+' '+(charge?'CHARGE TARGET':future?'POTENTIAL TARGET':attack?'ATTACK TARGET':'POTENTIAL TARGET'),red]);
            }
          }
          if(p.hatchway)ring(p.hatchway,amber,9,true);
          if(!t&&!nextPlan){const goal=positions[p.goalTarget]||p.goal;if(goal)ring(goal,amber,Math.max(12,goal.r||10),true);}
          return d||start;
        }
        ring(origin,green,Math.max(12,origin.r||10),projected);
        const end=action(plan,origin,false);
        if(nextPlan&&nextPlan.actor===plan.actor)action(nextPlan,end,true);
        // Draw labels last so routes cannot obscure the numbered instructions.
        tag(origin,'1 '+(projected?'CONFIRMED NPO':'ACTING NPO'),green,Math.max(12,origin.r||10));
        // Number 1 is reserved for the actor; destination and target follow.
        for(const [point,label,color] of marks)tag(point,label.replace(/^\d+/,n=>String(Number(n)+1)),color);
      }
    }
  }
  function open(host,config){
    if(!host||!config||document.documentElement.dataset.experimental!=='on')return;
    if(!session||session.token!==config.token){continuation=null;session={token:config.token,board:null,positions:{},walls:[],objectives:[],mapped:false,frame:null,turn:null,activated:new Set(),ready:new Set(),meta:{},mapRotation:0,mapFit:null,openDoors:[],capture:null};}
    preview=null;
    const s=session,models=config.models.map(m=>({...m,...(s.meta[m.key]?.base&&!m.base?{base:s.meta[m.key].base}:{}),...(m.side==='player'&&m.order==='Unknown'&&s.meta[m.key]?.order?{order:s.meta[m.key].order}:{})}));
    // A player may change order during their activation. Unknown must remain unknown until confirmed.
    if(s.frame)for(const m of models.filter(m=>m.side==='player'&&(s.turn!==config.turn||!s.activated.has(m.key)&&config.activated.includes(m.key))))if(config.models.find(x=>x.key===m.key)?.order==='Unknown')m.order='Unknown';
    let frame=null,positions={},board=null,walls=[],objectives=[],mapped=false,stage='photo',wallStart=null,selected='',plan=null,seq=0,raw=null,crop=null,dragging=null,autoRectified=false,mapLayout=null,rotation=0,mapFit=null,openDoors=[],diagnostics=[],capture=null,nextPlan=null,reused=false,suppressMapClick=false;
    host.innerHTML='<section class="recon-tracking"><p class="eyebrow">TACTICAL SCAN · EXPERIMENTAL</p><p class="rt-status" role="status" aria-live="polite"></p><p class="rt-metadata rt-ap-progress" hidden></p><div class="recon-upload"><label class="btn secondary">Take Photo<input type="file" accept="image/*" capture="environment" aria-label="Take tactical photo"></label><label class="btn ghost">Choose Photo<input type="file" accept="image/*" aria-label="Choose tactical photo"></label></div><div class="rt-work" hidden><div class="rt-recommendation" hidden></div><div class="recon-frame"><canvas aria-label="Battlefield photograph and tactical overlays"></canvas></div><div class="rt-controls"></div></div><div class="wizard-actions"><button type="button" class="btn ghost rt-manual">Use Manual Guide</button></div></section>';
    const get=q=>host.querySelector(q),status=get('.rt-status'),canvas=get('canvas'),controls=get('.rt-controls'),work=get('.rt-work'),recommendation=get('.rt-recommendation');
    const tell=t=>status.textContent=t;
    const progress=get('.rt-ap-progress'),active=models.find(m=>m.key===config.actorKey);
    if(active&&!config.setup){
      progress.hidden=false;
      progress.textContent=active.name+' · '+active.ap+' AP remaining'+(config.completedActions?.length?' · Completed: '+config.completedActions.join(', '):'');
    }
    const actionLabel=id=>id==='fall-back'?'Fall Back':id[0].toUpperCase()+id.slice(1);
    const isMove=p=>['reposition','dash','charge','fall-back'].includes(p.id);
    const cost=p=>p.id==='fall-back'?2:1;
    function confirmPlan(button,check=null){
      if(!live()||button.disabled||(check&&!check.checked))return;
      button.disabled=true;
      preview={frame,positions,models,board,walls,objectives,plan};
      // Keep projected positions separate from the photographic templates:
      // pixels still show the original board until the next real capture.
      const confirmed={...positions};
      if(isMove(plan)&&plan.destination)confirmed[plan.actor]={...positions[plan.actor],...plan.destination};
      continuation={token:config.token,turn:config.turn,actor:plan.actor,action:plan.id,frame,board:{...board},positions:confirmed,walls,objectives,mapped,rotation,mapFit,openDoors:[...openDoors]};
      config.accept({...plan,movementConfirmed:isMove(plan)});
    }
    const button=(label,fn,kind='secondary')=>{const b=document.createElement('button');b.type='button';b.className='btn '+kind;b.textContent=label;b.onclick=fn;return b;};
    const live=()=>host.isConnected&&document.documentElement.dataset.experimental==='on'&&config.valid();
    // Clamp handles to the visible photo so even a misaligned overlay can
    // be grabbed and brought back into view.
    function alignmentHandles(){
      if(stage!=='terrain'||!mapLayout||!mapFit||!board)return null;
      const bounds=maps.fitBounds(config.missionNumber,board,rotation);
      if(!bounds)return null;
      const rect=maps.fitRect(board,bounds,mapFit),pad=Math.max(12,canvas.width/45);
      const x=v=>Math.max(pad,Math.min(canvas.width-pad,v)),y=v=>Math.max(pad,Math.min(canvas.height-pad,v));
      const left=x(rect.x),right=x(rect.x+rect.w),top=y(rect.y),bottom=y(rect.y+rect.h);
      return {bounds,left,right,top,bottom,corners:[['nw',left,top],['ne',right,top],['se',right,bottom],['sw',left,bottom]]};
    }
    function invalidateAlignment(){
      refreshMap();
    }
    const repaint=()=>{
      canvas.classList.toggle('rt-crop-mode',stage==='crop');
      canvas.classList.toggle('rt-map-mode',stage==='terrain'&&Boolean(mapLayout));
      if(!frame)return;
      draw(canvas,frame,positions,models,board,stage==='identify'&&mapLayout?[]:walls,stage==='identify'&&mapLayout?[]:objectives,plan,stage!=='plan'||!plan,stage==='plan'?nextPlan:null,reused);
      if(mapLayout&&stage==='terrain'){
        const c=canvas.getContext('2d');c.font='bold 11px system-ui';c.textAlign='center';
        for(const p of mapLayout.terrain){c.strokeStyle='#eacb83';c.lineWidth=1.3;c.setLineDash([3,3]);c.beginPath();c.arc(p.x,p.y,Math.max(5,p.r*.65),0,Math.PI*2);c.stroke();}c.setLineDash([]);
        for(const p of mapLayout.doors){c.fillStyle=p.open?'#76f5a8':'#f0c66a';c.fillRect(p.x-4,p.y-4,8,8);}
        const h=alignmentHandles();
        if(h){
          c.save();c.strokeStyle='#8ff5ca';c.lineWidth=1.5;c.setLineDash([6,5]);c.strokeRect(h.left,h.top,h.right-h.left,h.bottom-h.top);c.setLineDash([]);
          const radius=Math.max(7,canvas.width/48);
          for(const [,x,y] of h.corners){
            c.beginPath();c.arc(x,y,radius+2,0,Math.PI*2);c.fillStyle='#07140f';c.fill();
            c.beginPath();c.arc(x,y,radius,0,Math.PI*2);c.fillStyle='#8ff5ca';c.fill();
          }
          c.restore();
          canvas.dataset.alignmentHandles=JSON.stringify(h.corners);
        }
      }else delete canvas.dataset.alignmentHandles;
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
      controls.replaceChildren();recommendation.replaceChildren();recommendation.hidden=true;
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
        if(!missing.length)controls.append(button('Confirm Operative Positions',()=>{if(mapped)assess();else{stage='terrain';update();}},'primary'));
        controls.append(button('Review Mission Layout',()=>{stage='terrain';update();},'ghost'));
        controls.append(button('Adjust Board Crop',resetCalibration,'ghost'));
        controls.append(button('Clear Selected Marker',()=>{delete positions[selected];update();},'ghost'));
      }else if(stage==='terrain'){
        if(mapLayout){
          tell('Drag inside the frame to move the layout. Drag a corner to resize it. Tap hatchways to toggle open or closed, then confirm the layout.');
          const note=document.createElement('p');note.className='rt-metadata';note.textContent='Amber: walls, terrain and closed hatchways. Green squares: open hatchways.';controls.append(note);
          controls.append(button('Rotate Mission Layout 90°',()=>{rotation=(rotation+1)%4;mapFit={sx:1,sy:1,dx:0,dy:0};openDoors=[];refreshMap();update();},'ghost'),button('Auto-align Mission Layout',()=>{openDoors=[];refreshMap(true);update();},'ghost'),button(reused?'Take New Photo':'Recalibrate Photo',reused?()=>get('input[aria-label="Take tactical photo"]').click():resetCalibration,'ghost'));
        }else{
          tell('No verified mission layout is available. Use the manual guide or mark blocking terrain.');
          const group=document.createElement('div');group.className='rt-actions';
          group.append(button('Mark Wall',()=>{stage='wall';wallStart=null;update();}),button('Mark Objective',()=>{stage='objective';update();}),button('Undo Wall',()=>{walls.pop();repaint();update();},'ghost'),button('Undo Objective',()=>{objectives.pop();repaint();update();},'ghost'));
          controls.append(group);
        }
        const unresolved=models.filter(m=>!m.base);if(unresolved.length){const note=document.createElement('p');note.className='rt-metadata';note.textContent='Base size required for '+unresolved.map(m=>m.name).join(', ')+'.';controls.append(note,button('Set Missing Base Sizes',()=>{selected=unresolved[0].key;stage='identify';update();}));}
        // A verified mission's primary button is the confirmation itself.
        // Manual terrain marking still requires explicit completeness review.
        if(!mapLayout){
          const check=document.createElement('label');check.className='rt-check';const input=document.createElement('input');input.type='checkbox';input.checked=mapped;input.onchange=()=>{mapped=input.checked;};check.append(input,document.createTextNode(' All blocking terrain is marked; verify physical board and open hatchways.'));controls.append(check);
        }
        const missing=models.some(m=>!positions[m.key]);
        controls.append(button(missing?'Confirm Mission Layout':config.setup?'Finish Recon Setup':'Assess Battlefield',()=>{if(!live())return;if(mapLayout)mapped=true;if(!mapped){tell('Confirm the marked terrain first.');return;}if(missing){stage='identify';update();return;}assess();},'primary'));
      }else if(stage==='wall'){tell(wallStart?'Tap the other end of this wall.':'Tap the first end of the wall.');controls.append(button('Cancel Wall',()=>{wallStart=null;stage='terrain';update();},'ghost'));}
      else if(stage==='objective'){tell('Tap the centre of an objective.');controls.append(button('Cancel Objective',()=>{stage='terrain';update();},'ghost'));}
      else if(stage==='plan'){
        if(!plan){
          tell('Recon could not confirm a tactical action. This does not mean there are no legal moves.');
          const reasons=document.createElement('div');reasons.className='rt-plan';
          const heading=document.createElement('strong');heading.textContent='Assessment results';reasons.append(heading);
          for(const reason of diagnostics){const p=document.createElement('p');const model=models.find(m=>m.key===reason.actor);p.textContent=(model?model.name+': ':'')+reason.message;reasons.append(p);}
          controls.append(reasons);
          if(!reused)controls.append(button('Review Operative Positions / Orders',()=>{selected='';stage='identify';update();}));
          else controls.append(button('Position differs? Take New Photo',()=>get('input[aria-label="Take tactical photo"]').click(),'ghost'));
          controls.append(button('Review Mission Layout',()=>{stage='terrain';update();},'ghost'));
        }
        else{
          const a=models.find(m=>m.key===plan.actor),target=models.find(m=>m.key===plan.target);
          tell((reused?'Using the same photograph; marked positions reflect confirmed actions. ':'')+(isMove(plan)?'Move the indicated operative, then confirm completion.':'Resolve the indicated action.'));
          const remaining=Math.max(0,a.ap-cost(plan)),starting=config.startingAp??a.ap;
          const apSummary=starting-a.ap>0?'AP spent: '+(starting-a.ap)+' of '+starting+' · ':'';
          const next=nextPlan?('Next planned action: '+actionLabel(nextPlan.id)+(nextPlan.distance!=null?' · '+nextPlan.distance.toFixed(1)+'″':'')+(nextPlan.target?' · '+(models.find(m=>m.key===nextPlan.target)?.name||'target'):'' )+'. Shown on the same photograph; confirmed separately.'):'Remaining AP will be assessed after this action is resolved.';
          const apHtml='<p class="rt-ap-summary"><b>'+esc(apSummary+a.ap+' AP available · '+cost(plan)+' AP for '+actionLabel(plan.id)+' · '+remaining+' AP remaining after')+'</b></p>'+(remaining?'<p>'+esc(next)+'</p>':'<p>Final AP of this activation.</p>');
          const buttonLabel=isMove(plan)?'Move Complete':plan.id==='shoot'?'Resolve Shoot':plan.id==='fight'?'Resolve Fight':'Resolve '+actionLabel(plan.id);
          const info=document.createElement('div');info.className='rt-plan';
          const intent=plan.intent||(plan.id==='shoot'?'Shoot a priority eligible enemy.':plan.id==='fight'?'Fight a priority enemy in control range.':'Improve the tactical position.');
          info.innerHTML='<strong>'+esc(a?.name)+' · '+esc(plan.id==='fall-back'?'Fall Back':plan.id[0].toUpperCase()+plan.id.slice(1))+'</strong><p><b>Tactical Intent:</b> '+esc(intent)+'</p><p>'+esc(plan.destination?`${plan.distance.toFixed(1)}″ along the marked route${target?` toward ${target.name}`:''}.`:target?`Target ${target.name}.`:'')+'</p>'+(plan.followUp&&!nextPlan?'<p>Potential follow-up: '+esc(plan.followUp)+'</p>':'')+(plan.hatchway?'<p>Later route requires an open hatchway. Verify and resolve opening on the tabletop before crossing.</p>':'') +apHtml+'<small>Green: movement (dashed for next action). Red: attack target. Amber: future goal or hatchway. Follow the numbered markers in order.</small>';
          recommendation.hidden=false;recommendation.append(info);
          if(plan.skipped?.length){
            const note=document.createElement('p');note.textContent='Check higher-priority actions first: '+plan.skipped.map(s=>s.action+' ('+s.reason+')').join('; ');info.append(note);
            const label=document.createElement('label');label.className='rt-check';const check=document.createElement('input');check.type='checkbox';label.append(check,document.createTextNode(' No legal higher-priority route exists on the tabletop.'));controls.append(label);
            const accept=button(buttonLabel,()=>confirmPlan(accept,check),'primary');accept.disabled=true;check.onchange=()=>accept.disabled=!check.checked;controls.append(accept);
          }else{const confirm=button(buttonLabel,()=>confirmPlan(confirm),'primary');controls.append(confirm);}
          if(!reused)controls.append(button('Review / Correct Models',()=>{stage='identify';plan=null;selected='';update();},'ghost'));
          controls.append(button('Review Mission Layout',()=>{stage='terrain';plan=null;update();},'ghost'));
          if(!reused)controls.append(button('Recalibrate Photo',resetCalibration,'ghost'));
          else controls.append(button('Position differs? Take New Photo',()=>get('input[aria-label="Take tactical photo"]').click(),'ghost'));
        }
      }
      repaint();
    }
    function resetCalibration(attemptAutomatic=false){
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
      stage='crop';
      // Reuse the last confirmed crop only when framing mode and orientation match.
      if(attemptAutomatic===true&&!config.setup&&s.mapped&&s.capture&&s.capture.rectified===autoRectified&&Math.abs(frame.width/frame.height-s.capture.aspect)<.015){
        const c=s.capture.rect;crop={x:c.x*frame.width,y:c.y*frame.height,w:c.w*frame.width,h:c.h*frame.height};
        if(confirmCrop(true))return;
      }
      update();
    }
    function rotatePhoto(){
      if(!frame)return;
      const rotated=document.createElement('canvas');rotated.width=frame.height;rotated.height=frame.width;
      const c=rotated.getContext('2d');c.translate(rotated.width,0);c.rotate(Math.PI/2);c.drawImage(frame,0,0);
      crop={x:frame.height-crop.y-crop.h,y:crop.x,w:crop.h,h:crop.w};frame=rotated;update();
    }
    function confirmCrop(automatic=false){
      if(!live()||!crop)return false;
      automatic=automatic===true;
      const previousFrame=frame,previousCrop={...crop};
      capture={rectified:autoRectified,aspect:frame.width/frame.height,rect:{x:crop.x/frame.width,y:crop.y/frame.height,w:crop.w/frame.width,h:crop.h/frame.height}};
      const out=document.createElement('canvas'),landscape=crop.w>crop.h;
      out.width=landscape?600:440;out.height=landscape?440:600;
      out.getContext('2d').drawImage(frame,crop.x,crop.y,crop.w,crop.h,0,0,out.width,out.height);
      frame=out;crop=null;board={x0:0,y0:0,x1:out.width,y1:out.height,width:landscape?30:22,height:landscape?22:30};
      if(s.frame&&s.board&&s.frame.width===out.width&&s.frame.height===out.height){
        const data=out.getContext('2d').getImageData(0,0,out.width,out.height).data,before=s.frame.getContext('2d').getImageData(0,0,out.width,out.height).data;
        const priorLayout=config.missionNumber&&s.mapFit?maps.geometry(config.missionNumber,board,s.mapRotation,s.openDoors,s.mapFit):null;
        const comparison=core.compareBoard(before,data,out.width,out.height,s.positions,priorLayout?.doors||[]);
        if(comparison.aligned){
          walls=s.walls.map(w=>w.map(p=>({...p})));objectives=s.objectives.map(p=>({...p}));
          if(config.missionNumber){rotation=s.mapRotation;mapFit=s.mapFit;openDoors=[...s.openDoors];refreshMap();}
          mapped=Boolean(s.mapped&&comparison.terrainStable&&(!config.missionNumber||priorLayout&&mapLayout));
          const changed=new Set(models.filter(m=>m.side==='player'&&(!s.activated.has(m.key)&&config.activated.includes(m.key)||s.turn!==config.turn)||m.side==='npo'&&(s.ready.has(m.key)&&!config.ready.includes(m.key)||m.key===config.actorKey||s.turn!==config.turn)).map(m=>m.key));
          const matches=core.track(s.positions,data,out.width,out.height,board,models,changed);
          positions=Object.fromEntries(Object.entries(matches).filter(([,p])=>p));
          const missing=models.filter(m=>!positions[m.key]);
          if(!missing.length&&mapped&&!config.setup){assess();return true;}
          selected=missing[0]?.key||'';
          stage=!mapped?'terrain':missing.length?'identify':'terrain';update();
          if(!mapped&&priorLayout&&!comparison.terrainStable)tell('The photo changed near a hatchway. Confirm the current hatchway states before continuing.');
          return true;
        }
      }
      if(automatic){frame=previousFrame;crop=previousCrop;board=null;capture=null;stage='crop';return false;}
      positions={};walls=[];objectives=[];mapped=false;selected='';openDoors=[];refreshMap(true);stage=mapLayout?'terrain':'identify';update();return true;
    }
    function assess(){
      if(!live()||!board||models.some(m=>!positions[m.key]))return;
      if(!mapped){tell('Confirm that the terrain matches the physical board before proceeding.');return;}
      if(!reused){s.meta=Object.fromEntries(models.map(m=>[m.key,{base:m.base,order:m.order}]));s.frame=frame;s.board={...board};s.positions={...positions};s.walls=walls.map(w=>w.map(p=>({...p})));s.objectives=objectives.map(p=>({...p}));s.mapped=mapped;s.turn=config.turn;s.activated=new Set(config.activated);s.ready=new Set(config.ready);s.scanKey=config.scanKey;s.mapRotation=rotation;s.mapFit=mapFit;s.openDoors=[...openDoors];s.capture=capture;}
      if(config.setup){config.complete();return;}
      const future=mapLayout&&maps.geometry(config.missionNumber,board,rotation,mapLayout.doors.map(d=>d.id),mapFit);
      const input={board,positions,models,walls,objectives,doors:mapLayout?.doors||[],terrain:mapLayout?.terrain||[],futureWalls:future?.walls||null,mapped,actorKey:config.actorKey,actionOrder:config.actionOrder};
      diagnostics=[];plan=core.plan({...input,diagnostics});nextPlan=null;
      if(plan){
        const actor=models.find(m=>m.key===plan.actor),remaining=actor.ap-cost(plan);
        // Preview the second AP from the expected post-action board. After
        // combat, rebuild the plan from the actual surviving roster.
        if(remaining>0){
          const projected={...positions};
          if(isMove(plan)&&plan.destination)projected[actor.key]={...positions[actor.key],...plan.destination};
          nextPlan=core.plan({...input,actorKey:actor.key,positions:projected,models:models.map(m=>m.key===actor.key?{...m,ap:remaining}:m),
            actionOrder:(m,inControl)=>config.actionOrder(m,inControl,[plan.id]).filter(name=>String(name).toLowerCase().split(' ')[0]!==plan.id)});
        }
      }
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
        next.getContext('2d').drawImage(im,0,0,next.width,next.height);raw=next;work.hidden=false;reused=false;continuation=null;
        resetCalibration(true);
      }catch(e){if(ticket===seq&&live())tell('Could not read photo. Try a JPEG or another image.');}
      finally{if(url)URL.revokeObjectURL(url);}
    }
    host.querySelectorAll('input[type=file]').forEach(i=>i.onchange=()=>{const f=i.files?.[0];i.value='';if(f)void load(f);});
    get('.rt-manual').textContent=config.setup?'Skip Recon Setup':'Use Manual Guide';
    get('.rt-manual').onclick=()=>{seq++;preview=null;continuation=null;config.manual();};
    function canvasPoint(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*canvas.width/r.width,y:(e.clientY-r.top)*canvas.height/r.height};}
    canvas.addEventListener('pointerdown',e=>{
      suppressMapClick=false;
      if(!live()||dragging||e.button!==0)return;
      const p=canvasPoint(e),radius=Math.max(15,canvas.width/23);
      if(stage==='crop'&&crop){
        const corners=[['nw',crop.x,crop.y],['ne',crop.x+crop.w,crop.y],['se',crop.x+crop.w,crop.y+crop.h],['sw',crop.x,crop.y+crop.h]];
        const handle=corners.find(([,x,y])=>Math.hypot(p.x-x,p.y-y)<=radius)?.[0]||(p.x>=crop.x&&p.x<=crop.x+crop.w&&p.y>=crop.y&&p.y<=crop.y+crop.h?'move':null);
        if(!handle)return;
        e.preventDefault();dragging={kind:'crop',handle,p,rect:{...crop},id:e.pointerId};
      }else if(stage==='terrain'&&mapLayout){
        const h=alignmentHandles();if(!h)return;
        const handle=h.corners.find(([,x,y])=>Math.hypot(p.x-x,p.y-y)<=radius)?.[0]||(p.x>=h.left&&p.x<=h.right&&p.y>=h.top&&p.y<=h.bottom?'move':null);
        if(!handle)return;
        dragging={kind:'map',handle,p,bounds:h.bounds,fit:{...mapFit},id:e.pointerId,moved:false};
      }else return;
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove',e=>{
      if(dragging?.id!==e.pointerId||!live())return;
      const p=canvasPoint(e),dx=p.x-dragging.p.x,dy=p.y-dragging.p.y;
      if(dragging.kind==='crop'&&stage==='crop'){
        crop=calibration.drag(dragging.rect,dragging.handle,dx,dy,canvas.width,canvas.height);repaint();
      }else if(dragging.kind==='map'&&stage==='terrain'){
        // Keep a tap distinct from dragging, including taps directly on doors.
        if(!dragging.moved&&Math.hypot(dx,dy)<5*canvas.width/canvas.getBoundingClientRect().width)return;
        dragging.moved=true;suppressMapClick=true;
        mapFit=maps.dragFit(board,dragging.bounds,dragging.fit,dragging.handle,dx,dy);
        invalidateAlignment();repaint();
      }
    });
    const endDrag=e=>{if(dragging?.id===e.pointerId){if(dragging.kind==='map'&&dragging.moved)suppressMapClick=true;dragging=null;}};
    canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);canvas.addEventListener('lostpointercapture',endDrag);
    canvas.onclick=e=>{
      if(!frame||!live())return;
      if(suppressMapClick){suppressMapClick=false;return;}
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
    const saved=continuation;
    // Only reuse within the same activation, after the app confirms that
    // the previous action actually committed. Never reuse for a new NPO.
    if(config.reusePrevious&&active&&saved&&saved.token===config.token&&saved.turn===config.turn&&saved.actor===active.key&&config.completedActionIds?.at(-1)===saved.action&&saved.mapped&&models.every(m=>saved.positions[m.key])){
      reused=true;frame=saved.frame;board={...saved.board};positions=Object.fromEntries(models.map(m=>[m.key,{...saved.positions[m.key]}]));
      walls=saved.walls.map(w=>w.map(p=>({...p})));objectives=saved.objectives.map(p=>({...p}));
      rotation=saved.rotation;mapFit=saved.mapFit;openDoors=[...saved.openDoors];refreshMap();mapped=true;
      work.hidden=false;assess();return;
    }
    if(s.frame)tell(active?'Capture a photograph or use the manual guide to assess this operative’s remaining AP.':'Capture a fresh photograph from the same overhead position for a tactical recommendation.');
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
