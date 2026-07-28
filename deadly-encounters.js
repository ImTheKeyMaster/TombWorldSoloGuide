(function(root){
  'use strict';

  const SOURCE='White Dwarf 521, February 2026';
  const D33_RESULTS=Object.freeze(['11','12','13','21','22','23','31','32','33']);
  const UNUSUAL_ID='unusual';
  const feature=(id,table,result,name,summary,duration,timing,automation,handler,cleanupTiming='none',requiredInput='tabletop confirmation')=>Object.freeze({
    id,table,result,name,summary,duration,timing,affectedSides:'player-and-npo',requiredInput,automation,handler,cleanupTiming,source:SOURCE
  });
  const roomFeatures=Object.freeze([
    feature('room-collapsed-ceiling','room','11','Collapsed Ceiling','Within this room: Move −1 inch; prompt for Light cover subject to normal restrictions.','while-within-room','movement and defence','automatic-guided','applyRoomModifiers'),
    feature('room-darkness','room','12','Darkness','During visibility checks, confirm whether more than 6 inches of the line passes through this room.','battle','visibility check','guided','checkDarkness'),
    feature('room-corrosive-fluid-leak','room','13','Corrosive Fluid Leak','At activation start in this room, confirm Wall control range; if absent, inflict D3 damage.','activation-start','operative activation','guided-automatic','resolveCorrosiveDamage'),
    feature('room-energy-rupture','room','21','Energy Rupture','Once per operative activation in this room when Wall terrain is in control range, inflict D3 damage.','once-per-activation','activation or room entry','guided-automatic','resolveEnergyRupture','activation-end'),
    feature('room-airborne-virus','room','22','Airborne Virus','Before a non-exempt action, roll D6; above APL blocks that action without spending AP.','activation-or-counteraction','before action','guided-automatic','checkAirborneVirus','activation-or-counteraction-end'),
    feature('room-accelerated-decelerated-time','room','23','Accelerated/Decelerated Time','Roll D6 once to persist Accelerated or Decelerated activation restrictions for each side.','battle','feature determined and activation choice','guided-automatic','resolveTimeMode'),
    feature('room-crumbling-floor','room','31','Crumbling Floor','Within this room, Dash is unavailable and Charge gains no additional 2 inches.','while-within-room','movement action','automatic','applyRoomModifiers'),
    feature('room-gravitic-anomaly','room','32','Gravitic Anomaly','Within this room: Move +1 inch and both melee Damage values −1.','while-within-room','movement and melee profile','automatic','applyRoomModifiers'),
    feature(UNUSUAL_ID,'room','33','Unusual','Determine two different unused features from this same table; secondary 33 results are rerolled.','battle','feature determined','automatic','resolveUnusual')
  ]);
  const objectiveFeatures=Object.freeze([
    feature('objective-quantum-shield','objective','11','Quantum Shield','If a shooting target is within 3 inches, offer one defence-die reroll.','shooting-attack','shoot defence','guided','offerQuantumShield','attack-end'),
    feature('objective-tesla-device','objective','12','Tesla Device','After Charge, Dash, Fall Back, or Reposition ends contesting this marker, inflict D3 damage.','battle','movement action end','guided-automatic','resolveTeslaDamage'),
    feature('objective-teleportation-device','objective','13','Teleportation Device','Guide a legal teleport-pad move or swap; cancel before AP or movement commits if setup is illegal.','battle','eligible movement action','guided','guideTeleportation'),
    feature('objective-control-node','objective','21','Control Node','In each Ready Step, confirm Player control to gain one additional CP once that Turning Point.','once-per-turning-point','strategy ready step','guided','resolveControlNode','next-turning-point'),
    feature('objective-temporal-sphere','objective','22','Temporal Sphere','Adjust Time (1AP), once per Turning Point; if control remains, the operative stays Ready.','once-per-turning-point','player activation','guided','resolveAdjustTime','next-turning-point'),
    feature('objective-hyperphase-aura','objective','23','Hyperphase Aura','Within 3 inches, melee gains Lethal 5+ or improves an existing Lethal threshold by 1.','while-within-range','melee profile','guided-automatic','applyHyperphaseAura'),
    feature('objective-regeneration-sphere','objective','31','Regeneration Sphere','Once per operative per battle, roll D6 before incapacitation; on 4+, remain at 1 wound and end remaining attack dice.','once-per-operative-battle','before incapacitation','guided-automatic','resolveRegeneration'),
    feature('objective-amplification-matrix','objective','32','Amplification Matrix','Amplify Weaponry (0AP) gives one selected weapon Lethal 4+ and Hot until activation/counteraction ends.','activation-or-counteraction','operative action','guided-automatic','resolveAmplification','activation-or-counteraction-end'),
    feature(UNUSUAL_ID,'objective','33','Unusual','Determine two different unused features from this same table; secondary 33 results are rerolled.','battle','feature determined','automatic','resolveUnusual')
  ]);
  const tables=Object.freeze({room:roomFeatures,objective:objectiveFeatures});
  const featureById=new Map([...roomFeatures,...objectiveFeatures].map(item=>[item.id,item]));
  const isRecord=value=>Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  const clone=value=>JSON.parse(JSON.stringify(value));
  const uniqueStrings=value=>Array.isArray(value)?[...new Set(value.filter(item=>typeof item==='string'&&featureById.has(item)))]:[];
  const emptyState=()=>({version:1,rooms:{},objectives:{},operativeLocations:{},usedFeatureIds:[],pendingChecks:[],pendingResolution:null,rollHistory:[],resolutionHistory:[],turningPointState:{},completedTransactionIds:[],temporaryEffects:[],regenerationUsedBy:[]});
  const roomEligible=dropZone=>['none','npo','both'].includes(dropZone);

  function normalizeEntity(raw,type){
    if(!isRecord(raw)||typeof raw.id!=='string'||!raw.id.trim()||typeof raw.label!=='string'||!raw.label.trim())return null;
    const featureIds=uniqueStrings(raw.featureIds).filter(id=>featureById.get(id)?.table===type||id===UNUSUAL_ID);
    if(type==='room'){
      const dropZone=['none','player','npo','both'].includes(raw.dropZone)?raw.dropZone:'none';
      return {...clone(raw),id:raw.id,label:raw.label,dropZone,eligible:roomEligible(dropZone),featureIds,corrections:Array.isArray(raw.corrections)?raw.corrections:[]};
    }
    return {...clone(raw),id:raw.id,label:raw.label,eligible:raw.eligible===true,carrierId:typeof raw.carrierId==='string'?raw.carrierId:null,featureIds,corrections:Array.isArray(raw.corrections)?raw.corrections:[]};
  }
  function normalizeState(raw){
    if(!isRecord(raw)||raw.version!==1)return emptyState();
    const normalized=emptyState();
    ['rooms','objectives'].forEach(key=>Object.values(isRecord(raw[key])?raw[key]:{}).forEach(value=>{const entity=normalizeEntity(value,key==='rooms'?'room':'objective');if(entity)normalized[key][entity.id]=entity;}));
    normalized.usedFeatureIds=uniqueStrings(raw.usedFeatureIds);
    normalized.operativeLocations=isRecord(raw.operativeLocations)?Object.fromEntries(Object.entries(raw.operativeLocations).filter(([id,roomId])=>typeof id==='string'&&(roomId===null||normalized.rooms[roomId])).map(([id,roomId])=>[id,roomId])):{};
    normalized.pendingChecks=Array.isArray(raw.pendingChecks)?clone(raw.pendingChecks.filter(isRecord)):[];
    normalized.pendingResolution=isRecord(raw.pendingResolution)?clone(raw.pendingResolution):null;
    normalized.rollHistory=Array.isArray(raw.rollHistory)?clone(raw.rollHistory.filter(isRecord)):[];
    normalized.resolutionHistory=Array.isArray(raw.resolutionHistory)?clone(raw.resolutionHistory.filter(isRecord)):[];
    normalized.turningPointState=isRecord(raw.turningPointState)?clone(raw.turningPointState):{};
    normalized.completedTransactionIds=Array.isArray(raw.completedTransactionIds)?[...new Set(raw.completedTransactionIds.filter(id=>typeof id==='string'))]:[];
    normalized.temporaryEffects=Array.isArray(raw.temporaryEffects)?clone(raw.temporaryEffects.filter(isRecord)):[];
    normalized.regenerationUsedBy=Array.isArray(raw.regenerationUsedBy)?[...new Set(raw.regenerationUsedBy.filter(id=>typeof id==='string'))]:[];
    return normalized;
  }
  function d33(tens,units){
    if(![1,2,3].includes(tens)||![1,2,3].includes(units))throw new RangeError('D33 dice must each be a D3 result from 1 to 3.');
    return `${tens}${units}`;
  }
  function findFeature(table,result){return tables[table]?.find(item=>item.result===String(result))||null;}
  function transactionId(context){return [context.missionId,context.entityType,context.entityId,context.turningPoint,context.activationId,context.actionId,context.triggerType].map(value=>String(value??'')).join('|');}
  function triggerPipeline(enabled,current,context){
    if(!enabled||!isRecord(context)||context.actingSide!=='player')return {checks:[],transactionId:null};
    const id=transactionId(context);
    if(current.completedTransactionIds.includes(id)||current.pendingChecks.some(check=>check.transactionId===id))return {checks:[],transactionId:id,duplicate:true};
    const checks=[];
    if(['opened','entered'].includes(context.triggerType)&&context.roomId&&current.rooms[context.roomId]?.eligible&&!current.rooms[context.roomId].featureIds.length)checks.push({type:'room',entityId:context.roomId,triggerType:context.triggerType});
    if(['contested','controlled'].includes(context.triggerType)&&context.objectiveId&&current.objectives[context.objectiveId]?.eligible&&!current.objectives[context.objectiveId].featureIds.length)checks.push({type:'objective',entityId:context.objectiveId,triggerType:context.triggerType});
    return {checks,transactionId:id};
  }
  function rollFeature(current,table,rollD3=MathD3,options={}){
    const state=normalizeState(current),secondary=options.secondary===true,attempts=[],legal=tables[table].filter(item=>!state.usedFeatureIds.includes(item.id)&&(!secondary||item.id!==UNUSUAL_ID));
    if(!legal.length)return {state,featureIds:[],attempts,exhausted:true,message:`No unused official ${table} feature remains.`};
    const maxAttempts=D33_RESULTS.length*4;
    for(let count=0;count<maxAttempts;count++){
      const tens=rollD3(),units=rollD3(),result=d33(tens,units),candidate=findFeature(table,result);
      const rejected=!candidate||(secondary&&candidate.id===UNUSUAL_ID)||state.usedFeatureIds.includes(candidate.id);
      const attempt={table,tens,units,result,featureId:candidate?.id||null,status:rejected?'discarded':'determined',reason:rejected?(candidate?.id===UNUSUAL_ID&&secondary?'Unusual cannot be a secondary result.':'Feature already used in this battle.'):null,secondary};
      attempts.push(attempt);state.rollHistory.push(attempt);
      if(rejected)continue;
      state.usedFeatureIds.push(candidate.id);
      if(candidate.id!==UNUSUAL_ID)return {state,featureIds:[candidate.id],attempts,exhausted:false};
      const first=rollFeature(state,table,rollD3,{secondary:true});
      const second=rollFeature(first.state,table,rollD3,{secondary:true});
      return {state:second.state,featureIds:[...first.featureIds,...second.featureIds],attempts:[...attempts,...first.attempts,...second.attempts],exhausted:first.exhausted||second.exhausted,message:first.message||second.message||null,unusual:true};
    }
    return {state,featureIds:[],attempts,exhausted:true,message:`No unused official ${table} feature could be generated safely.`};
  }
  function MathD3(){return Math.floor(Math.random()*3)+1;}
  function discover(current,enabled,context,rollD3=MathD3){
    let state=normalizeState(current);const pipeline=triggerPipeline(enabled,state,context);
    if(!pipeline.checks.length)return {state,checks:pipeline.checks,duplicate:Boolean(pipeline.duplicate),featureIds:[]};
    const check=pipeline.checks[0],key=check.type==='room'?'rooms':'objectives';
    const rolled=rollFeature(state,check.type,rollD3);state=rolled.state;
    const entity=state[key][check.entityId];
    Object.assign(entity,{discoveryMethod:check.triggerType,triggeringOperativeId:context.operativeId||null,missionId:context.missionId||null,turningPoint:context.turningPoint||0,activationId:context.activationId||null,actionId:context.actionId||null,d33Attempts:rolled.attempts,featureIds:rolled.featureIds,resolutionState:rolled.exhausted?'exhausted':'determined',activeEffectState:{}});
    state.completedTransactionIds.push(pipeline.transactionId);
    state.resolutionHistory.push({transactionId:pipeline.transactionId,type:'discovery',entityType:check.type,entityId:entity.id,featureIds:rolled.featureIds,turningPoint:context.turningPoint||0,status:entity.resolutionState});
    return {...rolled,state,checks:pipeline.checks,entity};
  }
  function registerRoom(current,{id,label,missionId,dropZone}){const state=normalizeState(current);if(!id||state.rooms[id])return state;state.rooms[id]=normalizeEntity({id,label,missionId,dropZone,featureIds:[],activeEffectState:{},resolutionState:'registered',corrections:[]},'room');return state;}
  function registerObjective(current,{id,label,missionId,eligible=true}){const state=normalizeState(current);if(!id||state.objectives[id])return state;state.objectives[id]=normalizeEntity({id,label,missionId,eligible,carrierId:null,featureIds:[],activeEffectState:{},resolutionState:'registered',corrections:[]},'objective');return state;}
  function roomFeatureIdsForOperative(current,operativeId){const state=normalizeState(current),room=state.rooms[state.operativeLocations[operativeId]];return room?.featureIds||[];}
  function effectiveMove(base,current,operativeId){const ids=roomFeatureIdsForOperative(current,operativeId);return Math.max(0,Number(base)+(ids.includes('room-collapsed-ceiling')?-1:0)+(ids.includes('room-gravitic-anomaly')?1:0));}
  function meleeDamage(damage,current,operativeId){return roomFeatureIdsForOperative(current,operativeId).includes('room-gravitic-anomaly')?Math.max(0,Number(damage)-1):Number(damage);}
  function actionRestrictions(current,operativeId){const ids=roomFeatureIdsForOperative(current,operativeId);return {dashBlocked:ids.includes('room-crumbling-floor'),chargeBonus:ids.includes('room-crumbling-floor')?0:2,pauseGuidance:'Pause if this operative first enters an unexplored room.',airborneVirus:ids.includes('room-airborne-virus')};}
  function improveLethal(existing){if(existing==null)return 5;return Math.max(2,Number(existing)-1);}
  function validateDefinitions(){const ids=new Set();for(const [table,items] of Object.entries(tables)){if(items.length!==9||new Set(items.map(item=>item.result)).size!==9||D33_RESULTS.some(result=>!items.some(item=>item.result===result)))throw new Error(`${table} D33 table is incomplete.`);for(const item of items){if(ids.has(item.id)&&item.id!==UNUSUAL_ID)throw new Error(`Duplicate feature ID: ${item.id}`);ids.add(item.id);if(!item.automation||!item.handler||!item.source)throw new Error(`Incomplete feature: ${item.id}`);}}return true;}
  validateDefinitions();
  const api={SOURCE,D33_RESULTS,UNUSUAL_ID,tables,features:[...roomFeatures,...objectiveFeatures],emptyState,normalizeState,roomEligible,d33,findFeature,transactionId,triggerPipeline,rollFeature,discover,registerRoom,registerObjective,roomFeatureIdsForOperative,effectiveMove,meleeDamage,actionRestrictions,improveLethal,validateDefinitions};
  root.TombWorldDeadlyEncounters=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
