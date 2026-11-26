'use strict';
const c=require('../battlefield-tracking.js'),a=require('node:assert/strict');
const board={x0:0,y0:0,x1:300,y1:300,width:30,height:30},models=[{key:'n:a',side:'npo',ready:true,base:32,move:6,ap:2,canShoot:true,range:12,focus:'shoot',wounds:9},{key:'p:b',side:'player',ready:true,base:32,order:'Engage',wounds:5}];
const positions={'n:a':{x:100,y:100},'p:b':{x:150,y:100}};
const args={board,positions,models,mapped:true,actionOrder:()=>['Shoot','Reposition']};
a.equal(c.segmentDistance({x:1,y:1},{x:0,y:0},{x:2,y:0}),1);
a.equal(c.plan(args).id,'shoot');
a.equal(c.plan({...args,positions:{...positions,'p:b':{x:119,y:100}},actionOrder:()=>['Fight','Shoot']}).id,'fight');
a.equal(c.plan({...args,mapped:false}),null);
a.equal(c.plan({...args,walls:[[{x:125,y:0},{x:125,y:300}]],actionOrder:()=>['Shoot']}),null);
a.equal(c.plan({...args,models:[models[0],{...models[1],order:'Conceal'}]}),null);
a.equal(c.plan({...args,actionOrder:()=>['Overcharge','Shoot']}),null);
a.equal(c.plan({...args,positions:{'n:a':positions['n:a']}}),null);
a.equal(c.plan({...args,models:[{...models[0],base:null},models[1]]}),null);
const w=100,h=100,old=new Uint8ClampedArray(w*h*4),next=new Uint8ClampedArray(w*h*4);
function paint(data,cx,cy){for(let y=-7;y<=7;y++)for(let x=-7;x<=7;x++){const i=((cy+y)*w+cx+x)*4;data[i]=100+x*9;data[i+1]=100+y*8;data[i+2]=190;data[i+3]=255;}}
paint(old,25,25);paint(next,51,40);
const prior={x:25,y:25,r:7,template:c.patch(old,w,h,{x:25,y:25},7)};
const res=c.track({'n:a':prior},next,w,h,{x0:0,y0:0,x1:99,y1:99},[models[0]],new Set(['n:a']));
a(res['n:a']&&c.dist(res['n:a'],{x:51,y:40})<4);
a.equal(c.track({'n:a':prior},new Uint8ClampedArray(w*h*4),w,h,{x0:0,y0:0,x1:99,y1:99},[models[0]],new Set(['n:a']))['n:a'],null);
a.equal(c.plan({...args,positions:{...positions,'p:b':{x:123,y:100}},actionOrder:()=>['Fight','Shoot']}),null);
console.log('Tracking and tactical geometry checks passed.');

const cal=c.calibration,rect=cal.fit(400,600);
a(Math.abs(rect.w/rect.h-22/30)<1e-10);
const resized=cal.drag(rect,'se',-50,-80,400,600);
a(resized.w<rect.w&&Math.abs(resized.w/resized.h-22/30)<1e-10);
const moved=cal.drag(resized,'move',-1000,1000,400,600);
a.equal(moved.x,0);a(Math.abs(moved.y+moved.h-600)<1e-8);
for(const handle of ['nw','ne','sw','se']){const r=cal.drag(rect,handle,10000,-10000,400,600);a(r.x>=-1e-8&&r.y>=-1e-8&&r.x+r.w<=400+1e-8&&r.y+r.h<=600+1e-8);a(Math.abs(r.w/r.h-22/30)<1e-10);}
const W=240,H=320,d=new Uint8ClampedArray(W*H*4);
for(let y=0;y<H;y++)for(let x=0;x<W;x++){const val=x>25+y*.025&&x<216-y*.018&&y>30+x*.025&&y<294-x*.025?40:190,i=(y*W+x)*4;d[i]=d[i+1]=d[i+2]=val;d[i+3]=255;}
const q=cal.detect(d,W,H);a(q&&Math.abs(q[0].x-26)<8);a(Math.abs(cal.project(q,1,1).x-q[2].x)<1e-8);
a.equal(cal.detect(new Uint8ClampedArray(W*H*4),W,H),null);
const warped=cal.warp(d,W,H,q,120,160,10);a.equal(warped.length,120*160*4);a(warped[(80*120+60)*4]<60);
console.log('Board calibration checks passed.');

const mb={x0:0,y0:0,x1:440,y1:600,width:22,height:30};
for(let i=1;i<=6;i++){const g=c.maps.geometry(i,mb);a(g.walls.length&&g.doors.length&&g.terrain.length);}
const closed=c.maps.geometry(1,mb),opened=c.maps.geometry(1,mb,0,[0]);a(opened.walls.length>closed.walls.length);a(opened.doors[0].open);a.notDeepEqual(c.maps.geometry(1,mb,1).walls,closed.walls);
a.equal(c.maps.geometry(99,mb),null);
const img=new Uint8ClampedArray(100*100*4);for(let y=0;y<100;y++)for(let x=0;x<100;x++){const v=Math.hypot(x-50,y-50)<=9?180:40;img.fill(v,(y*100+x)*4,(y*100+x)*4+3);}
a(Math.abs(c.snapping.snap(img,100,100,{x:55,y:52},9).x-50)<=2);a.equal(c.snapping.snap(img,100,100,{x:15,y:15},9),null);a.equal(c.snapping.snap(img,100,100,{x:55,y:52},9,()=>true),null);
console.log('Mission layouts and miniature snapping checks passed.');

// A dim base, protruding weapon, gradient floor and nearby wall must not displace the selected base.
const ww=120,hh=120,photo=new Uint8ClampedArray(ww*hh*4);
for(let y=0;y<hh;y++)for(let x=0;x<ww;x++){let v=70+Math.round(x/10);const rr=Math.hypot(x-55,y-60);if(rr<=12)v=rr>9?112:48;if(x>=55&&x<=77&&Math.abs(y-57)<=2)v=175;if(x>=90&&x<=97)v=180;photo.fill(v,(y*ww+x)*4,(y*ww+x)*4+3);}
const picked=c.snapping.snap(photo,ww,hh,{x:60,y:62},12);a(picked&&Math.hypot(picked.x-55,picked.y-60)<=4);a.equal(c.snapping.snap(photo,ww,hh,{x:25,y:85},12),null);a.equal(c.snapping.snap(photo,ww,hh,{x:93,y:60},12),null);a.equal(c.snapping.snap(photo,ww,hh,{x:55,y:60},12,()=>true),null);
console.log('Partial rim, wall, weapon and empty floor selection regressions passed.');

const reasons=[];
a.equal(c.plan({...args,models:[{...models[0],base:null},models[1]],diagnostics:reasons}),null);
a.equal(reasons[0].code,'base');
const second={...models[0],key:'n:c',name:'Warrior 2',wounds:9};
const all={...args,models:[{...models[0],name:'Support'},second,models[1]],positions:{...positions,'n:c':{x:100,y:140}},actionOrder:m=>m.key==='n:a'?['Overcharge','Shoot']:['Shoot','Reposition']};
a.equal(c.plan(all).actor,'n:c');
const route=c.plan({...args,models:[{...models[0],move:3,canShoot:false,focus:'fight'},models[1]],positions:{...positions,'p:b':{x:220,y:100}},actionOrder:()=>['Fight','Charge','Reposition','Dash']});
a(route&&route.id==='reposition');a.equal(route.skipped[0].action,'Charge');
const blockedReasons=[];a.equal(c.plan({...args,actionOrder:()=>['Overcharge'],diagnostics:blockedReasons}),null);a.equal(blockedReasons[0].code,'special');
console.log('Multi-candidate and diagnostic regressions passed.');

// A localized hatchway change must invalidate terrain even if the overall board matches.
const bw=120,bh=120,priorBoard=new Uint8ClampedArray(bw*bh*4).fill(40),nextBoard=priorBoard.slice();
a.deepEqual(c.compareBoard(priorBoard,nextBoard,bw,bh,{},[{x:60,y:60}]),{aligned:true,terrainStable:true});
for(let y=50;y<=70;y++)for(let x=50;x<=70;x++)nextBoard.fill(200,(y*bw+x)*4,(y*bw+x)*4+3);
a.deepEqual(c.compareBoard(priorBoard,nextBoard,bw,bh,{},[{x:60,y:60}]),{aligned:true,terrainStable:false});
a.equal(c.compareBoard(priorBoard,new Uint8ClampedArray(bw*bh*4).fill(200),bw,bh).aligned,false);
console.log('Repeat scan and hatchway change checks passed.');

// A Marksman must not blindly move toward an enemy behind a solid wall.
const marksman={...models[0],move:5,focus:'shoot',operatesHatches:true,name:'Warrior'},enemy={...models[1],name:'Gunner'};
const tactical={...args,models:[marksman,enemy],positions:{'n:a':{x:200,y:100},'p:b':{x:100,y:100}},actionOrder:()=>['Shoot','Reposition']};
const solid=[[{x:150,y:0},{x:150,y:300}]];
a.equal(c.plan({...tactical,walls:solid}),null);
const detour=c.plan({...tactical,walls:[[{x:150,y:0},{x:150,y:225}]]});
a(detour&&detour.id==='reposition'&&detour.destination.y>120&&detour.distance<=5&&detour.intent.includes('firing position'));
const around=c.plan({...tactical,models:[{...marksman,move:9,range:20},enemy],positions:{'n:a':{x:180,y:120},'p:b':{x:100,y:120}},walls:[[{x:150,y:0},{x:150,y:145}]]});
a(around&&around.path.length>=2&&around.distance<=9);
const door={x:150,y:160,id:1,open:false};
const hatch=c.plan({...tactical,walls:solid,doors:[door],futureWalls:[[{x:150,y:0},{x:150,y:149.5}],[{x:150,y:170.5},{x:150,y:300}]]});
a(hatch&&hatch.hatchway&&hatch.destination.x>150&&hatch.distance<=5);
for(let i=1;i<hatch.path.length;i++)a(c.segmentGap(hatch.path[i-1],hatch.path[i],...solid[0])>6);
console.log('Tactical intent, obstacle detour and closed hatchway regressions passed.');

// Mission alignment drag changes only the fitted terrain; opposite corner stays anchored.
for(let rotation=0;rotation<4;rotation++)for(let mission=1;mission<=6;mission++){
  const bounds=c.maps.fitBounds(mission,mb,rotation),initial={sx:1,sy:1,dx:0,dy:0},rect=c.maps.fitRect(mb,bounds,initial);
  const moved=c.maps.dragFit(mb,bounds,initial,'move',22,-30);
  a(Math.abs(moved.dx-.05)<1e-9&&Math.abs(moved.dy+.05)<1e-9);a.equal(moved.sx,1);a.equal(moved.sy,1);
  for(const corner of ['nw','ne','se','sw']){
    const fit=c.maps.dragFit(mb,bounds,initial,corner,12,20),after=c.maps.fitRect(mb,bounds,fit);
    a(Math.abs((corner.includes('w')?after.x+after.w-rect.x-rect.w:after.x-rect.x))<1e-8);
    a(Math.abs((corner.includes('n')?after.y+after.h-rect.y-rect.h:after.y-rect.y))<1e-8);
    const limited=c.maps.dragFit(mb,bounds,initial,corner,10000,-10000);
    a(limited.sx>=.65&&limited.sx<=1.35&&limited.sy>=.65&&limited.sy<=1.35&&Math.abs(limited.dx)<=.25&&Math.abs(limited.dy)<=.25);
  }
  const before=c.maps.geometry(mission,mb,rotation,[0]),after=c.maps.geometry(mission,mb,rotation,[0],moved);
  a(after.doors[0].open);a(Math.abs(after.doors[0].x-before.doors[0].x-22)<1e-8);
}
console.log('Mission overlay handle movement, independent scaling and hatchway preservation passed.');

// Experimental Recon ignores orders, but does not ignore walls or range.
for(const order of ['Unknown','Conceal','Engage']){
  const input={...args,ignoreOrders:true,models:[models[0],{...models[1],order}]};
  a.equal(c.plan(input).id,'shoot');
  a.equal(c.plan({...input,walls:[[{x:125,y:0},{x:125,y:300}]],actionOrder:()=>['Shoot']}),null);
}
console.log('Order-independent Recon target selection passed.');

// Off-base taps, square terrain, wall junctions and fitted outer rims.
const sn=c.snapping;
for(const tap of [{x:60,y:50},{x:61,y:52},{x:50,y:61}])a.equal(sn.snap(img,100,100,tap,9),null);
for(const tap of [{x:46,y:50},{x:54,y:53},{x:50,y:45}]){
 const fit=sn.snap(img,100,100,tap,9);a(fit&&Math.hypot(fit.x-50,fit.y-50)<=1.5&&Math.abs(fit.r-9)<=1.5);
}
a(Math.abs(picked.r-12)<=2);
const cap=new Uint8ClampedArray(100*100*4),square=cap.slice();
for(let y=0;y<100;y++)for(let x=0;x<100;x++){
 const i=(y*100+x)*4,block=Math.abs(x-50)<=9&&Math.abs(y-50)<=9;
 square.fill(block?180:45,i,i+3);
 cap.fill(block||(Math.abs(x-50)<4&&y>20)?180:45,i,i+3);
}
a.equal(sn.snap(square,100,100,{x:50,y:50},10),null);
const wall=[[{x:50,y:20},{x:50,y:99}]];
for(const tap of [{x:50,y:50},{x:54,y:50},{x:47,y:47}])a.equal(sn.snap(cap,100,100,tap,10,p=>sn.terrainBlocked(p,10,wall)),null);
a(sn.terrainBlocked({x:52,y:50},10,wall));a(!sn.terrainBlocked({x:65,y:50},10,wall));
console.log('Strict base hit testing, concentric rim fit and wall cap rejection passed.');
