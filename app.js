(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
  const APP_VERSION = '5.7.9';

let lastTouchEnd=0;
document.addEventListener('touchend',function(e){const now=Date.now();if(now-lastTouchEnd<=300){e.preventDefault();}lastTouchEnd=now;},{passive:false});
  const MAX_NPOS = 10;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const app = $('#app');
  const gameMenuBtn = $('#gameMenuBtn');
  const modal = $('#modal');
  const modalBody = $('#modalBody');
  const toast = $('#toast');
  const importInput = $('#importInput');
  const updateNotice = $('#updateNotice');
  const updateAppBtn = $('#updateAppBtn');

  function registerServiceWorker(){
    if(!('serviceWorker' in navigator))return;
    let waitingWorker=null;
    let updateRequested=false;
    const showUpdate=worker=>{
      waitingWorker=worker;
      if(navigator.onLine)updateNotice.hidden=false;
    };
    window.addEventListener('online',()=>{
      if(waitingWorker)updateNotice.hidden=false;
    });
    updateAppBtn.addEventListener('click',()=>{
      if(!waitingWorker)return;
      updateRequested=true;
      updateAppBtn.disabled=true;
      waitingWorker.postMessage({type:'SKIP_WAITING'});
    });
    navigator.serviceWorker.addEventListener('controllerchange',()=>{
      if(updateRequested)window.location.reload();
    });
    window.addEventListener('load',()=>{
      navigator.serviceWorker.register('./service-worker.js',{scope:'./'})
        .then(registration=>{
          if(registration.waiting)showUpdate(registration.waiting);
          registration.addEventListener('updatefound',()=>{
            const installingWorker=registration.installing;
            if(!installingWorker)return;
            installingWorker.addEventListener('statechange',()=>{
              if(installingWorker.state==='installed'&&navigator.serviceWorker.controller){
                showUpdate(installingWorker);
              }
            });
          });
        })
        .catch(()=>{});
    });
  }

  registerServiceWorker();

  let missionManifest=null;
  let objectiveEngine=null;
  let objectiveDefinition=null;
  let missionOperationResolving=false;
  let missionDialogLocked=false;
  const missionActivationStarts=new Set();
  async function loadMissionPack(){
    const manifestResponse=await fetch('Missions/manifest.json',{cache:'no-store'});
    if(!manifestResponse.ok)throw new Error(`Unable to load Missions/manifest.json (${manifestResponse.status})`);
    missionManifest=await manifestResponse.json();
    if(!Array.isArray(missionManifest.missions)||!missionManifest.missions.length)throw new Error('Mission manifest has no missions.');
    const loaded=await Promise.all(missionManifest.missions.map(async entry=>{
      const response=await fetch(`Missions/${entry.file}`,{cache:'no-store'});
      if(!response.ok)throw new Error(`Unable to load ${entry.file} (${response.status})`);
      return response.json();
    }));
    missions=loaded.sort((a,b)=>String(a.number).localeCompare(String(b.number)));
    maps=Object.fromEntries(missions.map(m=>[m.id,m.map||{walls:[],hatches:[],markers:[]}]));
  }

  async function loadObjectiveMission(){
    objectiveEngine=null;objectiveDefinition=null;
    const selectedMission=missionDefinition(state.missionId);
    const registered=missionManifest?.definitions?.some(entry=>entry.id===selectedMission?.number);
    if(!registered)return;
    try{
      const restoringRuntime=state.missionRuntime?.missionId===selectedMission.number;
      objectiveDefinition=await TombWorldMissionEngine.loadMissionDefinition(selectedMission.number);
      objectiveEngine=TombWorldMissionEngine.createMissionEngine({requestDiceRoll:animateMissionDice,requestNumericInput:requestMissionNumber});
      state.missionRuntime=objectiveEngine.restoreMissionRuntime(objectiveDefinition,state.missionRuntime);
      if(!restoringRuntime)await executeMissionLifecycleHook('onMissionInitialized');
    }catch(error){
      console.error('[MissionEngine]',error);
      showToast('Mission automation could not be loaded. Track this mission manually.');
    }
  }

  let playerManifest=null;
  let playerTeamData=null;
  async function loadPlayerManifest(){
    const response=await fetch('Player_Operatives/manifest.json',{cache:'no-store'});
    if(!response.ok)throw new Error(`Unable to load manifest.json (${response.status})`);
    const data=await response.json();
    if(!Array.isArray(data.teams)||!data.teams.length)throw new Error('manifest.json has no Kill Teams.');
    playerManifest=data;
    return data;
  }
  function playerTeamEntry(teamId=state.playerTeamId){
    return playerManifest?.teams?.find(team=>team.id===teamId)||null;
  }
  async function loadPlayerTeamData(teamId=state.playerTeamId){
    const entry=playerTeamEntry(teamId);
    if(!entry)throw new Error(`Kill Team "${teamId||'unknown'}" is not listed in manifest.json.`);
    const response=await fetch(`Player_Operatives/${entry.file}`,{cache:'no-store'});
    if(!response.ok)throw new Error(`Unable to load ${entry.file} (${response.status})`);
    const data=await response.json();
    if(!Array.isArray(data.operatives)||!data.operatives.length)throw new Error(`${entry.file} has no operatives.`);
    playerTeamData=data;
    state.playerTeamId=entry.id;
    state.playerTeamFile=entry.file;
    return data;
  }
  function playerDefinition(id){return playerTeamData?.operatives?.find(o=>o.id===id)||null;}
  function playerCurrentWounds(id){
    const definition=playerDefinition(id);
    const stored=Number(state.playerWounds?.[id]);
    return Number.isFinite(stored)?stored:Number(definition?.wounds||0);
  }
  function livePlayerOperative(id){
    const definition=playerDefinition(id);
    return definition?{...definition,wounds:playerCurrentWounds(id)}:null;
  }
  function initializePlayerWounds(){
    state.playerWounds={};
    (state.playerRoster||[]).forEach(id=>{
      const definition=playerDefinition(id);
      if(definition)state.playerWounds[id]=Number(definition.wounds||0);
    });
  }
  function selectedPlayerOperatives(){return (state.playerRoster||[]).map(livePlayerOperative).filter(Boolean);}
  function playerRosterLimits(){
    const maxRoster=Number(playerTeamData?.maxRoster??playerTeamData?.rosterSize??5);
    const minRoster=Number(playerTeamData?.minRoster??maxRoster);
    return {minRoster,maxRoster};
  }
  function playerName(id){
    const definition=playerDefinition(id);
    if(!definition)return String(id);
    const baseName=definition.name||String(id);
    const matchingSelected=(state.playerRoster||[]).filter(selectedId=>playerDefinition(selectedId)?.name===baseName);
    if(matchingSelected.length<=1)return baseName;
    const index=matchingSelected.indexOf(id);
    return `${baseName} ${index>=0?index+1:1}`;
  }

  let missions=[];
  let maps={};

  // Official NPO datacards, Tomb World Mission Pack pp. 6-7. Combat consumers use
  // these canonical profiles and delegate externally defined Core mechanics to tabletop play.
  const npoDefinitions = {
    'Canoptek Scarab Swarm': {
      name:'Canoptek Scarab Swarm',type:'Canoptek Scarab Swarm',move:6,apl:2,save:5,wounds:10,baseSize:40,
      compatibilityBehavior:'Brawler',compatibilityAttack:{dice:5,hit:4,normal:2,crit:3},defaultWeaponId:'feeder-mandibles',
      rangedWeapons:[],
      meleeWeapons:[{id:'feeder-mandibles',name:'Feeder mandibles',type:'melee',attacks:5,hit:4,damage:{normal:1,critical:2},rules:[]}],
      abilities:[],
      behavior:{summary:'Move towards the enemy to fight them, seeking cover on the way.',actions:['Fight','Charge the closest player operative via the shortest possible route','Reposition towards the closest player operative, to cover if possible','Dash towards the closest player operative, to cover if possible'],operatesHatches:true}
    },
    'Necron Warrior': {
      name:'Necron Warrior',type:'Necron Warrior',move:5,apl:2,save:4,wounds:9,baseSize:32,
      compatibilityBehavior:'Marksman',compatibilityAttack:{dice:4,hit:4,normal:3,crit:4},defaultWeaponId:'gauss-flayer',
      rangedWeapons:[
        {id:'gauss-flayer',name:'Gauss flayer',type:'ranged',attacks:4,hit:4,damage:{normal:3,critical:4},rules:['Piercing 1']},
        {id:'gauss-reaper',name:'Gauss reaper',type:'ranged',attacks:4,hit:3,damage:{normal:3,critical:4},rules:['Range 8"','Piercing 1']}
      ],
      meleeWeapons:[{id:'combat-attachment',name:'Combat attachment',type:'melee',attacks:3,hit:4,damage:{normal:3,critical:4},rules:[]}],
      abilities:[],
      behavior:{summary:'Move to an ideal position to shoot the enemy, but fight if unable to do anything else.',actions:['Fall Back','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission','Fight'],operatesHatches:true}
    },
    'Canoptek Tomb Crawler': {
      name:'Canoptek Tomb Crawler',type:'Canoptek Tomb Crawler',move:5,apl:2,save:3,wounds:21,baseSize:50,
      compatibilityBehavior:'Guardian',compatibilityAttack:{dice:4,hit:3,normal:4,crit:5},defaultWeaponId:'twin-gauss-reapers',
      rangedWeapons:[
        {id:'twin-gauss-reapers',name:'Twin gauss reapers',type:'ranged',profiles:[
          {id:'focused',name:'Focused',attacks:5,hit:4,damage:{normal:4,critical:5},rules:['Piercing 1','Punishing']},
          {id:'sweeping',name:'Sweeping',attacks:4,hit:4,damage:{normal:4,critical:5},rules:['Piercing 1','Punishing','Torrent 1"']}
        ]},
        {id:'transdimensional-isolator',name:'Transdimensional isolator',type:'ranged',attacks:5,hit:4,damage:{normal:5,critical:6},rules:['Dimensional Banishment']}
      ],
      meleeWeapons:[{id:'claws',name:'Claws',type:'melee',attacks:4,hit:4,damage:{normal:4,critical:4},rules:['Brutal']}],
      abilities:[
        {id:'weapon-sentinel',name:'Weapon Sentinel',text:'When selecting a valid target, if this operative has a Conceal order, it cannot use Light terrain for cover. This can allow it to be targeted but does not remove its cover save.'},
        {id:'steadfast',name:'Steadfast',text:'When determining control of a marker, this operative can be treated as having APL 3. This takes precedence over all other APL changes.'},
        {id:'dimensional-banishment',name:'Dimensional Banishment',text:'After using this weapon, if damage was inflicted or any critical successes were retained and the target was not incapacitated, roll 2D6. If the result is higher than the target remaining wounds, it is incapacitated.'}
      ],
      behavior:{summary:'Fight if necessary; otherwise move to an ideal position to shoot when outside player control range.',actions:['Fight','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission'],operatesHatches:true,weaponGuidance:'Use the sweeping twin gauss reapers profile when it would target more than one player operative.'}
    },
    'Canoptek Macrocyte': {
      name:'Canoptek Macrocyte',type:'Canoptek Macrocyte',move:7,apl:2,save:4,wounds:7,baseSize:28,
      compatibilityBehavior:'Sentinel',compatibilityAttack:{dice:4,hit:3,normal:3,crit:4},defaultWeaponId:'gauss-scalpel',
      rangedWeapons:[
        {id:'gauss-scalpel',name:'Gauss scalpel',type:'ranged',attacks:4,hit:4,damage:{normal:3,critical:4},rules:['Piercing 1']},
        {id:'tesla-caster',name:'Tesla caster',type:'ranged',profiles:[
          {id:'focused',name:'Focused',attacks:5,hit:4,damage:{normal:2,critical:3},rules:[]},
          {id:'living-lightning',name:'Living lightning',attacks:5,hit:4,damage:{normal:2,critical:3},rules:['Blast 2"']}
        ]}
      ],
      meleeWeapons:[{id:'claws-and-tail',name:'Claws & tail',type:'melee',attacks:4,hit:4,damage:{normal:3,critical:4},rules:[]}],
      abilities:[{id:'aggressive-defence-construct',name:'Aggressive Defense Construct',text:'If incapacitated by a player operative within 2", roll one D3. On a 2+, inflict damage on that player operative equal to the result.'}],
      behavior:{summary:'Fight if necessary; otherwise move to an ideal position to shoot when outside player control range.',actions:['Fight','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission'],operatesHatches:true,weaponGuidance:'Use the living lightning tesla caster profile when it would target more than one player operative and no NPOs.'}
    }
  };

  // Official 2D6 table, Tomb World Mission Pack p. 5. The unavailable-model
  // instruction to use the next row is a tabletop contingency, not a fallback.
  const npoGenerationTable = [
    {min:2,max:3,type:'Canoptek Scarab Swarm',weaponIds:['feeder-mandibles']},
    {min:4,max:6,type:'Canoptek Macrocyte',weaponIds:['gauss-scalpel','tesla-caster']},
    {min:7,max:10,type:'Necron Warrior',weaponIds:['gauss-flayer','gauss-reaper']},
    {min:11,max:11,type:'Canoptek Tomb Crawler',weaponIds:['twin-gauss-reapers']},
    {min:12,max:12,type:'Canoptek Tomb Crawler',weaponIds:['transdimensional-isolator']}
  ];

  // Physical Tomb World Event deck, Tomb World Mission Pack pp. 20-22.
  // Card-instance IDs preserve the printed duplicate weighting.
  const eventDefinitions = {
    'subjugation-glyphs':{title:'Subjugation Glyphs',text:'Until the end of the turning point, subtract 1 from the APL stat of player operatives while they are within 2" of an objective marker.',execution:{type:'activate'},duration:'turning-point'},
    'transdimensional-relocation':{title:'Transdimensional Relocation',text:'Relocate the player operative that is closest to an NPO. Follow the placement restrictions on the event card.',execution:{type:'tabletop-confirm'},duration:'immediate'},
    'my-will-be-done':{title:'My Will Be Done',text:'Until the end of the turning point, improve the Hit stat of NPO weapons by 1.',execution:{type:'activate'},duration:'turning-point'},
    'reanimation-protocols':{title:'Reanimation Protocols',text:'Until the end of the turning point, resolve Reanimation Protocols whenever an NPO is incapacitated, as described on the event card.',execution:{type:'activate'},duration:'turning-point'},
    'dark-of-the-tomb':{title:'Dark of the Tomb',text:'Until the end of the turning point, apply the Dark of the Tomb effect and its required re-rolls as described on the event card.',execution:{type:'activate'},duration:'turning-point'},
    'countertemporal-shifting':{title:'Countertemporal Shifting',text:'Until the end of the turning point, when an NPO would lose wounds, roll one D6 for each point of damage inflicted: for each 5+, that point of damage is ignored.',execution:{type:'activate'},duration:'turning-point'},
    'living-metal-flux':{title:'Living Metal Flux',text:'Each NPO that has lost any wounds regains D3+2 wounds.',execution:{type:'living-metal-flux'},duration:'immediate'},
    'maze-reforms':{title:'The Maze Reforms',text:'Close one breach and up to D3 open hatchways. If this cannot be resolved, draw another event card.',execution:{type:'maze-reforms'},duration:'immediate',redrawIfImpossible:true},
    'stirrings-of-horror':{title:'Stirrings of Horror',text:'Increase the Threat level by 1. If the Threat level is already 15, draw another event card instead.',execution:{type:'stirrings'},duration:'immediate',redrawIfImpossible:true},
    'chittering-drone':{title:'A Chittering Drone',text:'If a Canoptek Scarab Swarm has lost any wounds, it regains all lost wounds. Otherwise, set up one ready Canoptek Scarab Swarm with a Conceal order as described on the event card. If neither effect is possible, draw another event card.',execution:{type:'chittering-drone'},duration:'immediate',redrawIfImpossible:true},
    'awakened-warrior':{title:'Awakened Warrior',text:'Set up one ready Necron Warrior with a Conceal order as described on the event card. If this is not possible, draw another event card.',execution:{type:'awakened-warrior'},duration:'immediate',redrawIfImpossible:true}
  };
  const eventDeck = [
    {instanceId:'subjugation-glyphs-1',definitionId:'subjugation-glyphs'},
    {instanceId:'transdimensional-relocation-1',definitionId:'transdimensional-relocation'},
    {instanceId:'my-will-be-done-1',definitionId:'my-will-be-done'},
    {instanceId:'reanimation-protocols-1',definitionId:'reanimation-protocols'},
    {instanceId:'dark-of-the-tomb-1',definitionId:'dark-of-the-tomb'},
    {instanceId:'countertemporal-shifting-1',definitionId:'countertemporal-shifting'},
    {instanceId:'living-metal-flux-1',definitionId:'living-metal-flux'},
    {instanceId:'maze-reforms-1',definitionId:'maze-reforms'},
    {instanceId:'stirrings-of-horror-1',definitionId:'stirrings-of-horror'},
    {instanceId:'chittering-drone-1',definitionId:'chittering-drone'},
    {instanceId:'awakened-warrior-1',definitionId:'awakened-warrior'},
    {instanceId:'awakened-warrior-2',definitionId:'awakened-warrior'}
  ];

  const missionStateFactories = {
    escape:()=>({escapedIds:[],auspexCalibrations:{}}),
    sabotage:()=>({completedFeatureIds:[]}),
    transponder:()=>({sites:{},carrierId:null,escaped:false,lastRoll:null}),
    destruction:()=>({destruction:0}),
    scout:()=>({awakenedRooms:{},scoutedRoomIds:[]}),
    regroup:()=>({operativeChecks:{},lastCheckedTurningPoint:0})
  };

  const isRecord = value => Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  const boundedInteger = (value,min,max,fallback=min) => {
    const number=Number(value);
    return Number.isFinite(number)?Math.max(min,Math.min(max,Math.round(number))):fallback;
  };
  const normalizeIdList = (value,allowedIds=null) => {
    if(!Array.isArray(value))return [];
    const allowed=allowedIds?new Set(allowedIds):null;
    return [...new Set(value.filter(id=>typeof id==='string'&&id&&(allowed?.has(id)??true)))];
  };

  function missionDefinition(missionId=state?.missionId){return missions.find(item=>item.id===missionId)||null;}
  function missionEngine(m=mission()){return m?.missionEngine||null;}
  function freshMissionState(m=mission()){
    const factory=missionStateFactories[missionEngine(m)?.type];
    return factory?factory():{};
  }
  function normalizeMissionState(rawMissionState,m,legacyTracker=0){
    // Mission JSON loads after localStorage. Preserve saved progress until its
    // mission definition is available, then normalize it against that schema.
    if(!m)return isRecord(rawMissionState)?{...rawMissionState}:null;
    const engine=missionEngine(m), base=freshMissionState(m);
    if(!engine)return base;
    const raw=isRecord(rawMissionState)?rawMissionState:{};
    const normalized={...base,...raw};
    if(engine.type==='escape'){
      normalized.escapedIds=normalizeIdList(raw.escapedIds);
      normalized.auspexCalibrations=isRecord(raw.auspexCalibrations)?{...raw.auspexCalibrations}:{};
    }else if(engine.type==='sabotage'){
      normalized.completedFeatureIds=Array.isArray(raw.completedFeatureIds)
        ? normalizeIdList(raw.completedFeatureIds,engine.features.map(feature=>feature.id))
        : engine.features.slice(0,boundedInteger(legacyTracker,0,engine.features.length)).map(feature=>feature.id);
    }else if(engine.type==='transponder'){
      normalized.sites=isRecord(raw.sites)?Object.fromEntries(Object.entries(raw.sites).filter(([,value])=>['found','empty'].includes(value))):{};
      normalized.carrierId=typeof raw.carrierId==='string'&&raw.carrierId?raw.carrierId:null;
      normalized.escaped=Boolean(raw.escaped);
      normalized.lastRoll=isRecord(raw.lastRoll)?{...raw.lastRoll}:null;
    }else if(engine.type==='destruction'){
      normalized.destruction=Math.max(0,Number.isFinite(Number(raw.destruction))?Number(raw.destruction):Number(legacyTracker)||0);
    }else if(engine.type==='scout'){
      normalized.awakenedRooms=isRecord(raw.awakenedRooms)?{...raw.awakenedRooms}:{};
      normalized.scoutedRoomIds=Array.isArray(raw.scoutedRoomIds)
        ? normalizeIdList(raw.scoutedRoomIds,engine.rooms.map(room=>room.id))
        : engine.rooms.slice(0,boundedInteger(legacyTracker,0,engine.rooms.length)).map(room=>room.id);
    }else if(engine.type==='regroup'){
      normalized.operativeChecks=isRecord(raw.operativeChecks)?{...raw.operativeChecks}:{};
      normalized.lastCheckedTurningPoint=boundedInteger(raw.lastCheckedTurningPoint,0,999);
    }
    return normalized;
  }

  const initialState = () => ({
    version:APP_VERSION, screen:'home', tab:'play', setupStep:0, missionId:null,
    setupChecks:{}, roster:[], playerTeamId:'', playerTeamFile:'', playerRoster:[], playerRosterInitializedForTeamId:'', playerCount:0, playerReady:0, playerDeployed:false, turningPoint:0,
    threat:0, initiative:'player', phase:'setup', nextSide:'player', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, strategyPipeline:null, missionReadyContext:{sarcophagusControllers:0}, activationNumber:0,totalActivationsThisTP:0, playerActivated:0, npoActivated:0,
    activationHistory:[], playerActivatedIds:[], playerCasualtyIds:[], playerWounds:{}, reinforcementState:{turningPoint:0,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0},
    gradeMilestone:null, tpStartThreat:0, tpStartGrade:0, tpStartDestroyedNpos:0, tpStartPlayerCasualties:0,
    npoAttackTargetId:null,
    npoAttackSummary:null, combatState:null, missionState:null, missionRuntime:null, startingNpoGeneration:null, eventState:{available:eventDeck.map(card=>card.instanceId),used:[],active:[]}, gameEnd:null
  });

  const loadedState = load();
  let state = normalizeState(loadedState || initialState());
  if(loadedState?.version==='5.6.0'&&state.version===APP_VERSION)save();
  let lastRenderedStepKey = null;
  let startingNpoTimer = null;
  let threatAdjustOpen = false;
  let expandedRosterCategories = null;
  function autoSelectRequiredPlayerOperatives(){
    if(!playerTeamData||state.playerRosterInitializedForTeamId===playerTeamData.teamId)return;
    state.playerRosterInitializedForTeamId=playerTeamData.teamId;
    const operatives=playerTeamData.operatives||[];
    const requiredCategories=(playerTeamData.rosterCategories||[])
      .map(category=>({count:Number(category.requiredCount||0),eligible:operatives.filter(operative=>operative.category===category.id)}))
      .filter(category=>category.count>0);
    const selected=new Set(state.playerRoster||[]);
    requiredCategories.forEach(category=>{
      if(category.eligible.length===category.count)category.eligible.forEach(operative=>selected.add(operative.id));
    });
    state.playerRoster=[...selected];
    state.playerCount=state.playerRoster.length;
    state.playerReady=state.playerCount;
    initializePlayerWounds();
  }

  function applyPlayerRoster(operativeIds){
    state.playerRoster=[...operativeIds];
    state.playerCount=state.playerRoster.length;
    state.playerReady=state.playerCount;
    state.playerCasualtyIds=[];
    initializePlayerWounds();
    state.playerActivatedIds=[];
    state.playerDeployed=false;
  }

  function randomPlayerRoster(){
    const operatives=playerTeamData?.operatives||[];
    const rules=playerTeamData?.selectionRules||{};
    const {maxRoster}=playerRosterLimits();
    const selected=new Set();
    const shuffled=items=>{
      const result=[...items];
      for(let index=result.length-1;index>0;index--){
        const swapIndex=Math.floor(Math.random()*(index+1));
        [result[index],result[swapIndex]]=[result[swapIndex],result[index]];
      }
      return result;
    };
    const addRandom=(items,count)=>shuffled(items.filter(operative=>!selected.has(operative.id))).slice(0,count).forEach(operative=>selected.add(operative.id));

    if(rules.leader?.operativeId)selected.add(rules.leader.operativeId);
    (playerTeamData?.rosterCategories||[]).forEach(category=>{
      const required=Number(category.requiredCount||0);
      const current=operatives.filter(operative=>operative.category===category.id&&selected.has(operative.id)).length;
      addRandom(operatives.filter(operative=>operative.category===category.id),Math.max(0,required-current));
    });
    const troopersRequired=Number(rules.mandatoryTroopers||0);
    const troopersSelected=operatives.filter(operative=>operative.role==='Trooper'&&selected.has(operative.id)).length;
    addRandom(operatives.filter(operative=>operative.role==='Trooper'),Math.max(0,troopersRequired-troopersSelected));

    for(const operative of shuffled(operatives)){
      if(selected.size>=maxRoster)break;
      if(selected.has(operative.id))continue;
      const maxGunners=Number(rules.maxGunners||Infinity);
      if(operative.role==='Gunner'&&operatives.filter(candidate=>candidate.role==='Gunner'&&selected.has(candidate.id)).length>=maxGunners)continue;
      const maxGravis=Number(rules.maxGravis||1);
      if(operative.gravis&&operatives.filter(candidate=>candidate.gravis&&selected.has(candidate.id)).length>=maxGravis)continue;
      selected.add(operative.id);
    }
    applyPlayerRoster(selected);
  }

  function save(){
    if(objectiveEngine)state.missionRuntime=objectiveEngine.getMissionRuntime();
    state.version=APP_VERSION;
    try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));return true;}
    catch{showToast('The game could not be saved. Check available browser storage.');return false;}
  }
  function load(){
    try{
      const saved=localStorage.getItem(STORAGE_KEY);
      if(!saved)return null;
      const parsed=JSON.parse(saved);
      return isRecord(parsed)?parsed:null;
    }catch{return null;}
  }
  function recoverInvalidMission(){
    if(!state.missionId||missionDefinition(state.missionId))return false;
    state.missionId=null;
    state.missionState=null;
    state.screen='setup';
    showToast('The saved mission is unavailable. Select a mission to continue.');
    return true;
  }
  function normalizeState(raw){
    raw=isRecord(raw)?raw:{};
    const base=initialState(), merged={...base,...raw};
    if(!['home','help','setup','game'].includes(merged.screen))merged.screen='home';
    if(!['play','mission','roster','player-roster','journal','help'].includes(merged.tab))merged.tab='play';
    merged.turningPoint=boundedInteger(raw.turningPoint,0,999);
    merged.threat=boundedInteger(raw.threat,0,15);
    merged.roster=Array.isArray(raw.roster)?raw.roster.map(normalizeNpo).filter(Boolean):[];
    if(Number(raw.turningPoint)>0){
      const importedRoster=Array.isArray(raw.roster)?raw.roster:[];
      const explicitStates=new Set(importedRoster.filter(isRecord).filter(npo=>['reserve','deployed','out-of-action'].includes(npo.battlefieldState)).map(npo=>npo.id));
      merged.roster.filter(npo=>npo.wounds>0&&!explicitStates.has(npo.id)).forEach(npo=>{npo.battlefieldState='deployed';npo.deployed=true;});
    }
    const importedDormancy=new Map((Array.isArray(raw.roster)?raw.roster:[])
      .filter(npo=>isRecord(npo)&&typeof npo.id==='string'&&typeof npo.dormant==='boolean')
      .map(npo=>[npo.id,npo.dormant]));
    merged.roster.forEach(npo=>{
      if(!npo)return;
      if(npo.battlefieldState==='out-of-action'||npo.wounds<=0){
        npo.dormant=false;
        npo.ready=false;
        return;
      }
      if(npo.battlefieldState==='reserve'){
        npo.dormant=false;
        return;
      }
      npo.dormant=importedDormancy.has(npo.id)?importedDormancy.get(npo.id):merged.threat===0;
      if(npo.dormant)npo.ready=false;
    });
    merged.journal=Array.isArray(raw.journal)?raw.journal.filter(isRecord):[];
    merged.newIds=normalizeIdList(raw.newIds,merged.roster.map(npo=>npo.id));
    const importedReinforcements=isRecord(raw.reinforcementState)?raw.reinforcementState:{};
    const reinforcementIds=normalizeIdList(importedReinforcements.operativeIds,merged.roster.map(npo=>npo.id));
    const blockedReinforcementIds=normalizeIdList(importedReinforcements.blockedOperativeIds,merged.roster.map(npo=>npo.id))
      .filter(id=>!reinforcementIds.includes(id)&&merged.roster.some(npo=>npo.id===id&&npo.battlefieldState==='reserve'));
    const reinforcementStatus=['idle','placement','complete','blocked'].includes(importedReinforcements.status)?importedReinforcements.status:'idle';
    merged.reinforcementState={
      turningPoint:boundedInteger(importedReinforcements.turningPoint,0,merged.turningPoint),
      status:reinforcementStatus==='placement'&&!reinforcementIds.length?'idle':reinforcementStatus,
      operativeIds:reinforcementIds,
      blockedOperativeIds:blockedReinforcementIds,
      blocked:boundedInteger(importedReinforcements.blocked,0,MAX_NPOS)
    };
    merged.activationHistory=Array.isArray(raw?.activationHistory)?raw.activationHistory:[];
    merged.playerActivatedIds=Array.isArray(raw?.playerActivatedIds)?raw.playerActivatedIds:[];
    merged.playerCasualtyIds=Array.isArray(raw?.playerCasualtyIds)?raw.playerCasualtyIds:[];
    merged.playerWounds=raw?.playerWounds&&typeof raw.playerWounds==='object'?{...raw.playerWounds}:{};
    merged.combatState=isRecord(raw.combatState)&&raw.combatState.side==='player'&&isRecord(raw.combatState.stage)
      ? {side:'player',stage:{...raw.combatState.stage}}
      : null;
    merged.playerRoster=Array.isArray(raw?.playerRoster)?raw.playerRoster:[];
    merged.setupChecks=raw?.setupChecks&&!Array.isArray(raw.setupChecks)&&typeof raw.setupChecks==='object'?{...raw.setupChecks}:{};
    merged.startingNpoGeneration=isRecord(raw?.startingNpoGeneration)
      ? {...raw.startingNpoGeneration,dice:Array.isArray(raw.startingNpoGeneration.dice)?raw.startingNpoGeneration.dice.map(value=>boundedInteger(value,1,3,1)):[]}
      : null;
    if(merged.startingNpoGeneration){
      const rosterIds=merged.roster.map(npo=>npo.id);
      merged.startingNpoGeneration.deployedNpoIds=normalizeIdList(merged.startingNpoGeneration.deployedNpoIds,rosterIds);
      const deployedIds=new Set(merged.startingNpoGeneration.deployedNpoIds);
      merged.startingNpoGeneration.reserveNpoIds=normalizeIdList(merged.startingNpoGeneration.reserveNpoIds,rosterIds).filter(id=>!deployedIds.has(id));
      if(!merged.startingNpoGeneration.deployedNpoIds.length&&!merged.startingNpoGeneration.reserveNpoIds.length){
        // Legacy starting rosters contained only the mission-roll quantity, so
        // preserving prior gameplay means treating every surviving entry as deployed.
        merged.roster.filter(npo=>npo.battlefieldState!=='out-of-action').forEach(npo=>{npo.battlefieldState='deployed';npo.deployed=true;});
        merged.startingNpoGeneration.deployedNpoIds=merged.roster.filter(npo=>npo.battlefieldState==='deployed').map(npo=>npo.id);
        merged.startingNpoGeneration.reserveNpoIds=[];
        merged.startingNpoGeneration.availableNpos=merged.startingNpoGeneration.deployedNpoIds.length;
        merged.startingNpoGeneration.deploymentCount=Math.min(merged.startingNpoGeneration.missionRoll,merged.startingNpoGeneration.availableNpos);
      }
    }
    if(raw.version==='5.6.0'&&merged.screen==='setup'&&merged.startingNpoGeneration?.navigationComplete){
      merged.setupStep=Math.max(0,Number(merged.setupStep||0)-1);
      merged.version=APP_VERSION;
    }
    merged.playerTeamId=raw?.playerTeamId||'';
    if(isRecord(raw.strategyData)){
      const legacyEvent=raw.strategyData.event;
      const legacyTitle=Array.isArray(legacyEvent)?legacyEvent[0]:legacyEvent?.title;
      const legacyDefinitionId=Object.keys(eventDefinitions).find(id=>eventDefinitions[id].title===legacyTitle);
      const event=legacyDefinitionId?eventRecord({instanceId:`legacy-${legacyDefinitionId}`,definitionId:legacyDefinitionId}):legacyEvent;
      const hasRolledInitiative=Number.isFinite(raw.strategyData.playerRoll)&&Number.isFinite(raw.strategyData.npoRoll);
      merged.strategyData={
        ...raw.strategyData,
        event,
        events:Array.isArray(raw.strategyData.events)?raw.strategyData.events:(event?[{...event,status:raw.strategyData.eventPending?'drawn':'resolved'}]:[]),
        eventIndex:Number.isInteger(raw.strategyData.eventIndex)?raw.strategyData.eventIndex:0,
        initiativeMode:raw.strategyData.initiativeMode==='rolled'||raw.strategyData.initiativeMode==='automatic'
          ? raw.strategyData.initiativeMode
          : hasRolledInitiative?'rolled':'automatic',
        initiativeReason:raw.strategyData.initiativeReason||(raw?.turningPoint===1?'Turning Point 1':'Threat was 0 when initiative was determined')
      };
    }else merged.strategyData=null;
    const importedEvents=isRecord(raw.eventState)?raw.eventState:{};
    const validInstances=new Set(eventDeck.map(card=>card.instanceId));
    const available=Array.isArray(importedEvents.available)?normalizeIdList(importedEvents.available,validInstances):eventDeck.map(card=>card.instanceId);
    const used=normalizeIdList(importedEvents.used,validInstances).filter(id=>!available.includes(id));
    merged.eventState={
      available,
      used,
      active:Array.isArray(importedEvents.active)?importedEvents.active.filter(event=>isRecord(event)&&eventDefinitions[event.definitionId]).map(event=>({...event})):[]
    };
    const livingImportedPlayers=merged.playerRoster.filter(id=>!merged.playerCasualtyIds.includes(id)).length;
    merged.missionReadyContext=raw?.missionReadyContext&&typeof raw.missionReadyContext==='object'
      ? {sarcophagusControllers:normalizeSarcophagusControllers(raw.missionReadyContext.sarcophagusControllers,livingImportedPlayers)}
      : {sarcophagusControllers:0};
    merged.strategyPipeline=isRecord(raw.strategyPipeline)
      ? {...raw.strategyPipeline,completed:Array.isArray(raw.strategyPipeline.completed)?raw.strategyPipeline.completed:[]}
      : null;
    merged.gameEnd=['victory','defeat'].includes(raw?.gameEnd)?raw.gameEnd:null;
    const savedMission=missionDefinition(merged.missionId);
    merged.missionState=normalizeMissionState(raw?.missionState,savedMission,raw?.tracker);
    merged.completed=Boolean(merged.gameEnd);
    merged.playerCount=merged.playerRoster.length;
    if(merged.phase==='strategy'&&merged.strategyStage==='initiative'){
      const resolvedSide=merged.strategyData?.suggestedInitiative==='npo'?'npo':'player';
      merged.initiative=resolvedSide;
      merged.phase='firefight';
      merged.strategyStage=null;
      merged.nextSide=resolvedSide;
    }
    return merged;
  }
  function npoDefinition(type){return npoDefinitions[type]||null;}
  function npoWeapon(definition,weaponId){
    return [...(definition?.rangedWeapons||[]),...(definition?.meleeWeapons||[])].find(weapon=>weapon.id===weaponId)||null;
  }
  function weaponProfiles(weapon){
    if(!weapon)return [];
    return (weapon.profiles||[weapon]).map(profile=>({...profile,weaponId:weapon.id,weaponName:weapon.name}));
  }
  function npoAttackProfiles(npo,attackType){
    const definition=npoDefinition(npo?.type);
    if(!definition)return [];
    const weapons=attackType==='shoot'
      ? (definition.rangedWeapons||[]).filter(weapon=>weapon.id===npo.weaponId)
      : definition.meleeWeapons||[];
    return weapons.flatMap(weaponProfiles);
  }
  function canonicalAttackProfile(profile){
    const piercing=(profile?.rules||[]).map(String).map(rule=>rule.match(/(?:Piercing|AP)\s*(\d+)/i)).find(Boolean);
    return {
      dice:Number(profile?.attacks||0),hit:Number(profile?.hit||0),
      normal:Number(profile?.damage?.normal||0),crit:Number(profile?.damage?.critical||0),
      ap:Number(piercing?.[1]||0),
      rules:[...(profile?.rules||[])],weaponId:profile?.weaponId||'',profileId:profile?.id||'',
      name:profile?.weaponName===profile?.name?profile?.name:`${profile?.weaponName}: ${profile?.name}`
    };
  }
  function legacyNpoType(npo){
    if(npoDefinitions[npo?.type])return npo.type;
    return Object.keys(npoDefinitions).find(type=>String(npo?.name||'').startsWith(type))||npo?.type;
  }
  function normalizeNpo(npo){
    if(!isRecord(npo))return null;
    const type=legacyNpoType(npo),definition=npoDefinition(type);
    if(!definition)return null;
    const weaponId=npoWeapon(definition,npo.weaponId)?.id||definition.defaultWeaponId;
    const battlefieldState=Number(npo.wounds)<=0
      ? 'out-of-action'
      : ['reserve','deployed','out-of-action'].includes(npo.battlefieldState)
        ? npo.battlefieldState
        : npo.deployed||npo.ready?'deployed':'reserve';
    return {
      ...npo,
      type,
      name:npo.name||definition.name,
      move:Number.isFinite(Number(npo.move))?Number(npo.move):definition.move,
      apl:Number.isFinite(Number(npo.apl))?Number(npo.apl):definition.apl,
      save:Number.isFinite(Number(npo.save))?Number(npo.save):definition.save,
      maxWounds:Number.isFinite(Number(npo.maxWounds))?Number(npo.maxWounds):definition.wounds,
      wounds:Number.isFinite(Number(npo.wounds))?Number(npo.wounds):definition.wounds,
      baseSize:Number.isFinite(Number(npo.baseSize))?Number(npo.baseSize):definition.baseSize,
      behavior:npo.behavior||definition.compatibilityBehavior,
      attack:canonicalAttackProfile(npoAttackProfiles({...npo,type,weaponId},'shoot')[0]||npoAttackProfiles({...npo,type,weaponId},'melee')[0]) || {...definition.compatibilityAttack},
      weaponId,
      order:npo.order||'Conceal',
      battlefieldState,
      deployed:battlefieldState==='deployed',
      dormant:Boolean(npo.dormant),
      reinforcement:npo.reinforcement&&typeof npo.reinforcement==='object'
        ? {...npo.reinforcement,hatchway:String(npo.reinforcement.hatchway||''),placementConfirmed:Boolean(npo.reinforcement.placementConfirmed)}
        : null
    };
  }
  function mission(){ return missions.find(m => m.id === state.missionId) || missions[0]; }
  function missionSetup(m=mission()){return m?.startingNpos?.formula||'0';}
  function missionTracker(m=mission()){return m?.tracker?.label||'Mission progress';}
  function missionTrackerMax(m=mission()){return Number(m?.tracker?.max||0);}
  function missionSpecial(m=mission()){return (m?.rules||[]).map(rule=>`${rule.name}: ${rule.summary}`).join(' ');}
  function missionFirstInitiative(m=mission()){return m?.firstTurningPointInitiative||'player';}

  function roll(sides=6){ return Math.floor(Math.random()*sides)+1; }
  function rollD3(){ return roll(3); }
  function uid(){ return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,7)}`; }
  function generationResult(total){return npoGenerationTable.find(row=>total>=row.min&&total<=row.max)||null;}
  function generatedWeaponId(result){return result.weaponIds[roll(result.weaponIds.length)-1];}
  function createNpo(type,name=`${type} ${state.roster.length+1}`,options={}){
    const definition=npoDefinition(type);
    if(!definition)throw new Error(`Unknown NPO type: ${type}`);
    const weaponId=npoWeapon(definition,options.weaponId)?.id||definition.defaultWeaponId;
    const battlefieldState=options.battlefieldState||(options.deployed===false?'reserve':'deployed');
    const dormant=battlefieldState==='deployed'&&(options.dormant??state.threat===0);
    return {
      id:uid(),name,type,move:definition.move,apl:definition.apl,save:definition.save,
      maxWounds:definition.wounds,wounds:definition.wounds,baseSize:definition.baseSize,
      behavior:definition.compatibilityBehavior,attack:canonicalAttackProfile(npoAttackProfiles({type,weaponId},'shoot')[0]||npoAttackProfiles({type,weaponId},'melee')[0]),weaponId,order:'Conceal',
      ready:options.ready??(battlefieldState==='deployed'&&!dormant),dormant,
      battlefieldState,deployed:battlefieldState==='deployed',
      reinforcement:options.reinforcement||null
    };
  }
  function rollNpo(){
    const rolls=[roll(6),roll(6)],total=rolls[0]+rolls[1],result=generationResult(total);
    return {...result,rolls,total,weaponId:generatedWeaponId(result)};
  }
  function activeNpos(){ return state.roster.filter(n => n.battlefieldState==='deployed'&&n.wounds > 0); }
  function reserveNpos(){ return state.roster.filter(n => n.battlefieldState==='reserve'&&n.wounds > 0); }
  function readyNpos(){ return activeNpos().filter(n => n.ready&&!n.dormant); }
  function livingPlayerOperativeCount(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id)).length;
  }

  function normalizeSarcophagusControllers(value,max=livingPlayerOperativeCount()){
    const limit=Math.max(0,Math.round(Number(max)||0));
    return Math.max(0,Math.min(limit,Math.round(Number(value)||0)));
  }

  const missionOutcomeEvaluators = {
    escape:(engine,progress)=>{
      const total=state.playerRoster.length, departed=new Set([...progress.escapedIds,...state.playerCasualtyIds]);
      if(!total||departed.size<total)return null;
      return progress.escapedIds.length>=Math.ceil(total/2)?'victory':'defeat';
    },
    sabotage:(engine,progress)=>progress.completedFeatureIds.length>=engine.required?'victory':null,
    transponder:(engine,progress)=>progress.escaped?'victory':null,
    destruction:()=>null,
    scout:(engine,progress)=>progress.scoutedRoomIds.length>=engine.required?'victory':null,
    regroup:(engine,progress,timing)=>{
      if(timing!=='end-turning-point')return null;
      const survivors=(state.playerRoster||[]).filter(id=>!state.playerCasualtyIds.includes(id));
      if(!survivors.length)return null;
      return survivors.every(id=>{
        const check=progress.operativeChecks[id]||{};
        return check.inDropZone&&check.outsideNpoControl&&check.nearPlayer;
      })?'victory':null;
    }
  };

  function missionOutcome(timing='immediate'){
    const engine=missionEngine(), progress=state.missionState||freshMissionState();
    const defeat=(state.playerRoster||[]).length>0&&livingPlayerOperativeCount()===0;
    if(defeat&&engine?.type!=='escape')return 'defeat';
    const evaluator=missionOutcomeEvaluators[engine?.type];
    return evaluator?evaluator(engine,progress,timing):null;
  }

  function completeMission(outcome){
    if(!['victory','defeat'].includes(outcome)||state.gameEnd)return false;
    state.gameEnd=outcome;
    state.completed=true;
    state.phase='end';
    executeMissionLifecycleHook('onBattleEnded',{outcome});
    const engine=missionEngine();
    log(`${mission().name}: ${outcome}. ${outcome==='victory'?engine?.success:engine?.failure}`);
    closeModal();
    save();
    render();
    return true;
  }

  function checkGameEnd(timing='immediate'){
    const outcome=missionOutcome(timing);
    return outcome?completeMission(outcome):false;
  }

  function totalLivingOperatives(){
    return livingPlayerOperativeCount()+activeNpos().length;
  }

  function activationProgressLabel(){
    const current=Math.max(1,state.activationNumber+1);
    return `ACTIVATION ${current} OF ${totalLivingOperatives()}`;
  }

  function playerOperativesRemaining(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id)&&!activated.has(id)).length;
  }
  function destroyedNpoCount(){ return state.roster.filter(n=>n.wounds<=0).length; }
  function eligibleNpoAttackTargets(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id));
  }
  function selectedNpoAttackTarget(){
    return livePlayerOperative(state.npoAttackTargetId);
  }

  function setNextActivation(preferredSide){
    const playerRemaining=playerOperativesRemaining();
    const npoRemaining=readyNpos().length;

    if(playerRemaining<=0 && npoRemaining<=0){
      state.nextSide=null;
      state.phase='end';
      return null;
    }
    if(playerRemaining<=0){
      state.nextSide='npo';
      return 'npo';
    }
    if(npoRemaining<=0){
      state.nextSide='player';
      return 'player';
    }

    state.nextSide=preferredSide==='npo'?'npo':'player';
    return state.nextSide;
  }

  function advanceAfterActivation(completedSide){
    return setNextActivation(completedSide==='player'?'npo':'player');
  }

  function threatGrade(){ return state.threat === 0 ? 0 : state.threat <= 5 ? 1 : state.threat <= 10 ? 2 : 3; }
  function threatLabel(){ return ['Dormant','Stirring','Awakened','Overrun'][threatGrade()]; }
  function threatToNext(){ const g=threatGrade(); if(g===3)return 0; return [1,6,11][g]-state.threat; }
  function log(text){ state.journal.unshift({time:new Date().toISOString(),text}); state.journal=state.journal.slice(0,150); }
  function setThreat(amount,reason){
    const before=state.threat;
    const beforeGrade=threatGrade();
    state.threat=boundedInteger(state.threat+amount,0,15,state.threat);
    if(before===0&&state.threat>0){
      activeNpos().filter(npo=>npo.dormant).forEach(npo=>{npo.dormant=false;npo.ready=true;});
    }else if(state.threat===0){
      activeNpos().forEach(npo=>{npo.dormant=true;npo.ready=false;});
    }
    const afterGrade=threatGrade();
    if(state.threat!==before) log(`Threat ${before} → ${state.threat}: ${reason}`);
    if(afterGrade>beforeGrade){
      state.gradeMilestone={grade:afterGrade,threat:state.threat,label:threatLabel()};
      log(`Threat reached Grade ${afterGrade}: ${threatLabel()}.`);
    }
  }
  function escapeHtml(s){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

  function startingNpoRoll(){
    const formula=missionSetup(), dice=formula==='2D3+3'?[rollD3(),rollD3()]:formula==='D3+6'?[rollD3()]:[];
    const missionRoll=formula==='2D3+3'?dice[0]+dice[1]+3:formula==='D3+6'?dice[0]+6:0;
    const calculation=formula==='2D3+3'?`${dice[0]} + ${dice[1]} + 3 = ${missionRoll}`:formula==='D3+6'?`${dice[0]} + 6 = ${missionRoll}`:'0';
    return {dice,missionRoll,deploymentCount:Math.min(missionRoll,MAX_NPOS),availableNpos:MAX_NPOS,calculation,deployedNpoIds:[],reserveNpoIds:[],animationShown:false,navigationComplete:false};
  }

  function restoredStartingNpoGeneration(){
    const missionRoll=state.roster.length, formula=missionSetup();
    const d3Total=missionRoll-3;
    const dice=formula==='2D3+3'?[Math.max(1,d3Total-3),Math.min(3,d3Total-1)]:formula==='D3+6'?[Math.max(1,Math.min(3,missionRoll-6))]:[];
    const calculation=formula==='2D3+3'?`${dice[0]} + ${dice[1]} + 3 = ${missionRoll}`:formula==='D3+6'?`${dice[0]} + 6 = ${missionRoll}`:'0';
    return {dice,missionRoll,deploymentCount:Math.min(missionRoll,state.roster.length),availableNpos:state.roster.length,calculation,deployedNpoIds:[],reserveNpoIds:[],animationShown:true,navigationComplete:false};
  }

  function selectStartingNpos(generation){
    const available=state.roster.filter(npo=>npo.wounds>0),shuffled=[...available];
    const assignedIds=new Set([...(generation.deployedNpoIds||[]),...(generation.reserveNpoIds||[])]);
    if(assignedIds.size===available.length&&available.every(npo=>assignedIds.has(npo.id)))return false;
    generation.availableNpos=available.length;
    generation.deploymentCount=Math.min(generation.missionRoll,available.length);
    for(let index=shuffled.length-1;index>0;index--){
      const swapIndex=Math.floor(Math.random()*(index+1));
      [shuffled[index],shuffled[swapIndex]]=[shuffled[swapIndex],shuffled[index]];
    }
    generation.deployedNpoIds=shuffled.slice(0,generation.deploymentCount).map(npo=>npo.id);
    generation.reserveNpoIds=shuffled.slice(generation.deploymentCount).map(npo=>npo.id);
    const deployedIds=new Set(generation.deployedNpoIds);
    available.forEach(npo=>{
      npo.battlefieldState=deployedIds.has(npo.id)?'deployed':'reserve';
      npo.deployed=npo.battlefieldState==='deployed';
      npo.dormant=npo.deployed&&state.threat===0;
      npo.ready=false;
    });
    return true;
  }

  function generateRoster(generation){
    const m=mission(),count=MAX_NPOS,formula=generation.calculation;
    state.roster=[];
    for(let i=0;i<count;i++){
      const result=rollNpo();
      state.roster.push(createNpo(result.type,`${result.type} ${i+1}`,{weaponId:result.weaponId,ready:false,deployed:false}));
    }
    selectStartingNpos(generation);
    state.newIds=[]; log(`${m.name}: selected ${generation.deploymentCount} of ${count} starting NPOs (${formula}).`); return {count,formula};
  }

  function ensureStartingNpoGeneration(){
    if(state.startingNpoGeneration)return false;
    if(state.roster.length){
      state.startingNpoGeneration=restoredStartingNpoGeneration();
      selectStartingNpos(state.startingNpoGeneration);
      save();
      return false;
    }
    state.startingNpoGeneration=startingNpoRoll();
    generateRoster(state.startingNpoGeneration);
    save();
    return true;
  }

  function render(){
    sortOperativesGlobally();
    const currentStepKey = [
      state.screen,
      state.setupStep ?? '',
      state.tab ?? '',
      state.phase ?? '',
      state.turningPoint ?? '',
      state.nextSide ?? '',
      state.activationNumber ?? ''
    ].join(':');
    const movedToNewStep = lastRenderedStepKey !== null && currentStepKey !== lastRenderedStepKey;
    lastRenderedStepKey = currentStepKey;

    gameMenuBtn.hidden = state.screen !== 'game' || Boolean(state.gameEnd);
    if(state.screen==='home') renderHome();
    else if(state.screen==='help') renderHowItWorks();
    else if(state.screen==='setup') renderSetup();
    else renderGame();
    bindCommon();

    if(movedToNewStep){
      requestAnimationFrame(()=>{
        window.scrollTo({top:0,left:0,behavior:'auto'});
        document.documentElement.scrollTop=0;
        document.body.scrollTop=0;
      });
    }
  }

  function guideInstructionsHtml(full=false){
    const overview=`<section class="help-section">
      <h3>What the Guide does</h3>
      <p>Tomb World Solo Guide walks you through setup, Turning Points, alternating Player and NPO activations, Threat, reinforcements, combat, and the battle record. You still move models, measure distances, determine line of sight, and apply any operative-specific rules on the tabletop.</p>
    </section>`;

    const flow=`<section class="help-section">
      <h3>Game flow</h3>
      <ol class="guide-flow-list">
        <li><strong>Set up the mission</strong><span>Choose a mission, build the killzone, generate the starting NPO roster, and deploy both sides.</span></li>
        <li><strong>Prepare the Turning Point</strong><span>The Guide readies operatives, applies mission Ready rules, determines initiative, then processes events and reinforcements.</span></li>
        <li><strong>Alternate activations</strong><span>The side with initiative activates first. Player and NPO activations then alternate until one side runs out of ready operatives.</span></li>
        <li><strong>End the Turning Point</strong><span>Score mission progress, resolve end-of-turn effects, and begin the next Turning Point.</span></li>
      </ol>
    </section>`;

    const ai=`<section class="help-section ai-help-section">
      <h3>How the NPO AI decides</h3>
      <div class="ai-step-grid">
        <article><span>1</span><div><strong>Queue the NPO</strong><p>The Guide identifies the next ready NPO. Every battlefield question applies only to that operative.</p></div></article>
        <article><span>2</span><div><strong>Follow its behavior</strong><p><b>Brawler:</b> close distance, Charge, and Fight. <b>Marksman:</b> seek a legal shot and useful cover. <b>Sentinel:</b> engage nearby threats first, then act like a Marksman.</p></div></article>
        <article><span>3</span><div><strong>Evaluate the battlefield</strong><p>Your answers tell the Guide whether the NPO can Fight, Charge, Shoot, contest an objective, pursue a wounded target, operate a hatch, or reposition.</p></div></article>
        <article><span>4</span><div><strong>Choose the most dangerous legal option</strong><p>When several choices are legal, the AI favors damage, mission denial, and pressure against the Player.</p></div></article>
        <article><span>5</span><div><strong>Break true ties</strong><p>If two options remain genuinely equal, choose the result most favorable to the Tomb World. Randomize only when they are still indistinguishable.</p></div></article>
        <article><span>6</span><div><strong>Resolve it on the tabletop</strong><p>The Guide gives the action sequence, target priority, stance, and attack dice. You carry out movement, measuring, visibility, and special rules.</p></div></article>
      </div>
      <div class="golden-rule"><strong>Golden rule</strong><span>If the Guide cannot distinguish between two legal choices, use the option most favorable to the NPOs.</span></div>
    </section>`;

    const combat=`<section class="help-section">
      <h3>Player activation and combat</h3>
      <p>Select a remaining Player operative, set its APL, choose legal actions, and press <strong>Complete Activation</strong>. Selected Shooting or Melee attacks are then resolved. Damage remains pending until you confirm the entire activation, so canceling or going back does not alter NPO wounds.</p>
    </section>`;

    const quick=`<section class="help-section quick-reference-grid">
      <article><h4>Player</h4><p>Your solo kill-team operatives.</p></article>
      <article><h4>NPO</h4><p>A non-player operative controlled by the Guide.</p></article>
      <article><h4>APL</h4><p>The number of action points an operative may spend during its activation.</p></article>
      <article><h4>THREAT LEVEL</h4><p>A 0–15 alert meter. Higher grades generate more reinforcements and events.</p></article>
      <article><h4>Ready</h4><p>The operative can still activate during this Turning Point.</p></article>
      <article><h4>Expended</h4><p>The operative has activated or is otherwise unavailable.</p></article>
    </section>`;

    if(full) return overview+flow+ai+combat+quick;
    return ai+quick;
  }

  function renderHome(){
    const canContinue=Boolean(load()?.missionId && load()?.screen==='game');
    app.innerHTML=`<section class="hero-card">
      <img class="hero-symbol" src="Assets/icon.svg" alt="">
      <p class="eyebrow">A STEP-BY-STEP DIGITAL GAME MASTER</p>
      <h2>Enter the Tomb</h2>
      <p>Choose a mission, build the board, deploy the correct NPO roster, and follow one clear next action through every Turning Point.</p>
      <div class="button-row">
        <button class="btn primary" id="newGameBtn">New Game</button>
        <button class="btn secondary" id="continueBtn" ${canContinue?'':'disabled'}>Continue Game</button>
        <button class="btn ghost" id="homeHelpBtn">How It Works</button>
      </div>
    </section>`;
    $('#newGameBtn').onclick=()=>{ state=initialState(); state.screen='setup'; state.setupStep=0; expandedRosterCategories=null; save(); render(); };
    $('#continueBtn').onclick=()=>{ const saved=load(); if(saved){state=normalizeState(saved);state.screen='game';render();} };
    $('#homeHelpBtn').onclick=()=>{
      state.screen='help';
      render();
      window.scrollTo({top:0,left:0,behavior:'auto'});
    };
  }


  function renderHowItWorks(){
    app.innerHTML=`<section class="how-it-works-screen">
      <div class="screen-toolbar">
        <button class="btn ghost compact" id="howItWorksBackBtn" type="button" aria-label="Return to Home">← Back</button>
        <span class="screen-version">v${APP_VERSION}</span>
      </div>
      <header class="screen-heading">
        <p class="eyebrow">TOMB WORLD SOLO GUIDE</p>
        <h2>How It Works</h2>
        <p>Use the Guide as a digital game master while you handle models, measuring, visibility, and operative-specific rules on the tabletop.</p>
      </header>
      <div class="how-it-works-content">
        ${guideInstructionsHtml(true)}
      </div>
      <div class="wizard-actions how-it-works-footer">
        <button class="btn primary" id="howItWorksDoneBtn" type="button">Back to Home</button>
      </div>
    </section>`;

    const goHome=()=>{
      state.screen='home';
      render();
      window.scrollTo({top:0,left:0,behavior:'auto'});
    };
    $('#howItWorksBackBtn').onclick=goHome;
    $('#howItWorksDoneBtn').onclick=goHome;
  }

  function hasMultiplePlayerTeams(){return (playerManifest?.teams?.length||0)>1;}
  function renderTeamSelection(){
    const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}">
      <div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div>
      <p>${escapeHtml(team.description||'')}</p>
    </button>`).join('');
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Choose Kill Team</h2><p>Select the player-controlled Kill Team for this battle.</p></div></div><section class="wizard-card"><div class="team-select-grid">${cards}</div><div class="wizard-actions"><button class="btn ghost" id="teamSelectHome">Back</button></div></section></div>`;
    $('#teamSelectHome').onclick=()=>{state.screen='home';save();render();};
    $$('[data-player-team]').forEach(button=>button.onclick=async()=>{
      try{
        state.playerTeamId=button.dataset.playerTeam;
        state.playerRosterInitializedForTeamId='';
        state.playerRoster=[];
        state.playerCount=0;
        state.playerReady=0;
        state.playerCasualtyIds=[];
        state.playerWounds={};
        state.playerActivatedIds=[];
        state.playerDeployed=false;
        await loadPlayerTeamData(state.playerTeamId);
        save();
        render();
      }catch(error){
        console.error(error);
        showToast(error.message);
      }
    });
  }

  const setupStepDefinitions={
    mission:{title:'Choose Mission',subtitle:'Select the mission the Guide will run.'},
    killzone:{title:'Build the Killzone',subtitle:'Follow the board checklist before deploying models.'},
    team:{title:'Choose Player Kill Team',subtitle:'Select the player-controlled Kill Team for this battle.'},
    playerRoster:{title:'Build Player Roster',subtitle:'Choose the operatives you will use in this battle.'},
    deploy:{title:'Deploy Kill Teams',subtitle:'Place both forces on the battlefield and confirm deployment.'},
    ready:{title:'Ready to Begin',subtitle:'Review the mission, then begin Turning Point 1.'}
  };
  function activeSetupSteps(){
    const steps=['mission','killzone'];
    if(hasMultiplePlayerTeams())steps.push('team');
    steps.push('playerRoster','deploy','ready');
    return steps;
  }
  function currentSetupStepId(){
    const steps=activeSetupSteps();
    state.setupStep=Math.max(0,Math.min(Number(state.setupStep||0),steps.length-1));
    return steps[state.setupStep];
  }
  function renderSetup(){
    const steps=activeSetupSteps();
    const stepId=currentSetupStepId();
    if(stepId==='playerRoster'){
      autoSelectRequiredPlayerOperatives();
      save();
    }
    if(stepId==='deploy')ensureStartingNpoGeneration();
    const details=setupStepDefinitions[stepId];
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>${details.title}</h2><p>${details.subtitle}</p></div><div class="step-count">${state.setupStep+1} / ${steps.length}</div></div><div class="progress-bar"><span style="width:${((state.setupStep+1)/steps.length)*100}%"></span></div><section class="wizard-card">${setupContent(stepId)}</section></div>`;
    bindSetup(stepId);
  }
  function missionSetupChecks(stage){
    const checks=Array.isArray(mission().setupChecks)?mission().setupChecks:[];
    const currentIds=new Set(checks.map(check=>check.id));
    state.setupChecks=Object.fromEntries(Object.entries(state.setupChecks||{}).filter(([id])=>currentIds.has(id)));
    checks.forEach(check=>{if(typeof state.setupChecks[check.id]!=='boolean')state.setupChecks[check.id]=false;});
    return checks.filter(check=>check.stage===stage);
  }
  function clearMissionSetupChecks(stage){
    missionSetupChecks(stage).forEach(check=>{state.setupChecks[check.id]=false;});
  }
  function setupChecklistHtml(checks){
    return checks.map(check=>`<label class="check-row"><input type="checkbox" data-check="${escapeHtml(check.id)}" ${state.setupChecks[check.id]?'checked':''}><span><strong>${escapeHtml(check.label)}</strong><small>Confirm this step on the physical board.</small></span></label>`).join('');
  }
  function setupContent(stepId){
    if(stepId==='mission') return `<h3>Which mission are you playing?</h3><p>You can review the objective before committing.</p><div class="mission-list">${missions.map(m=>`<button class="mission-choice ${state.missionId===m.id?'selected':''}" data-mission="${m.id}"><div class="team-select-card-head"><div><small>${m.number}</small><strong>${m.name}</strong></div>${state.missionId===m.id?'<span>✓</span>':''}</div><span>${m.brief}</span></button>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupHome">Back</button><button class="btn primary" id="setupNext" ${state.missionId?'':'disabled'}>Next</button></div>`;
    if(stepId==='killzone'){
      const m=mission();
      const checks=missionSetupChecks('killzone');
      const allChecked=checks.length>0&&checks.every(check=>state.setupChecks[check.id]);
      return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${escapeHtml(m.objective)}</p>${boardSvg(m.id)}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllSetup" ${allChecked?'disabled':''}>Check All</button></div><div class="checklist">${setupChecklistHtml(checks)}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allChecked?'':'disabled'}>Board Ready</button></div>`;
    }
    if(stepId==='team'){
      const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}"><div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div><p>${escapeHtml(team.description||'')}</p></button>`).join('');
      return `<h3>Which Kill Team are you playing?</h3><p>Your choice determines the operatives available on the next step.</p><div class="team-select-grid">${cards}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${state.playerTeamId?'':'disabled'}>Build Roster</button></div>`;
    }
    if(stepId==='playerRoster'){
      const selected=new Set(state.playerRoster||[]);
      const selectedDefs=selectedPlayerOperatives();
      const gravisCount=selectedDefs.filter(o=>o.gravis).length;
      const gunnerCount=selectedDefs.filter(o=>o.role==='Gunner').length;
      const trooperCount=selectedDefs.filter(o=>o.role==='Trooper').length;
      const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners||Infinity);
      const maxGravis=Number(playerTeamData?.selectionRules?.maxGravis||1);
      const mandatoryTroopers=Number(playerTeamData?.selectionRules?.mandatoryTroopers||0);
      const requiredLeaderId=playerTeamData?.selectionRules?.leader?.operativeId||'';
      const leaderSelected=!requiredLeaderId||selected.has(requiredLeaderId);
      const requiredLeaderCategory=(playerTeamData?.rosterCategories||[]).find(category=>category.id==='leader'&&Number(category.requiredCount||0)>0);
      const requiredLeaderCount=requiredLeaderId?Number(playerTeamData?.selectionRules?.leader?.count||1):Number(requiredLeaderCategory?.requiredCount||0);
      const selectedLeaderCount=requiredLeaderId
        ? (leaderSelected?1:0)
        : (playerTeamData?.operatives||[]).filter(operative=>operative.category==='leader'&&selected.has(operative.id)).length;
      const requiredLeaderSelected=requiredLeaderId
        ? leaderSelected
        : selectedLeaderCount>=requiredLeaderCount;
      const hasGravis=(playerTeamData?.operatives||[]).some(o=>o.gravis);
      const {minRoster,maxRoster}=playerRosterLimits();
      const categoryMetadata=new Map((playerTeamData?.rosterCategories||[]).map(category=>[category.id,category]));
      const categories=[];
      (playerTeamData?.operatives||[]).forEach(operative=>{
        const categoryId=operative.category;
        let category=categories.find(entry=>entry.id===categoryId);
        if(!category){
          const metadata=categoryMetadata.get(categoryId)||{};
          category={id:categoryId,label:metadata.label||categoryId,order:Number(metadata.order??categories.length),operatives:[]};
          categories.push(category);
        }
        category.operatives.push(operative);
      });
      categories.sort((a,b)=>a.label.localeCompare(b.label));
      if(expandedRosterCategories===null)expandedRosterCategories=new Set();
      const sections=categories.map((category,index)=>{
        const categorySelected=category.operatives.filter(operative=>selected.has(operative.id)).length;
        const expanded=expandedRosterCategories.has(category.id);
        const panelId=`roster-category-${index}`;
        const cards=category.operatives.map(o=>{
          const chosen=selected.has(o.id);
          const rosterBlocked=!chosen&&selected.size>=maxRoster;
          const gravisBlocked=!chosen&&o.gravis&&gravisCount>=maxGravis;
          const gunnerBlocked=!chosen&&o.role==='Gunner'&&gunnerCount>=maxGunners;
          return `<button type="button" class="player-roster-card ${chosen?'selected':''}" data-select-player="${o.id}" ${rosterBlocked||gravisBlocked||gunnerBlocked?'disabled':''}><div class="player-roster-card-head"><div><strong>${escapeHtml(o.name)}</strong><small>${escapeHtml(o.role)}${o.gravis?' · GRAVIS':''}</small></div><span>${chosen?'✓':'+'}</span></div><div class="operative-stat-line"><span><small>APL</small><b>${o.apl}</b></span><span><small>MOVE</small><b>${o.move}"</b></span><span><small>SAVE</small><b>${o.save}+</b></span><span><small>WOUNDS</small><b>${o.wounds}</b></span></div></button>`;
        }).join('');
        return `<section class="roster-category"><button type="button" class="roster-category-heading" data-roster-category-toggle="${escapeHtml(category.id)}" aria-expanded="${expanded}" aria-controls="${panelId}"><span class="roster-category-title"><span class="roster-category-indicator" aria-hidden="true">›</span>${escapeHtml(category.label)}</span><span>${categorySelected} selected</span></button><div class="player-roster-grid roster-category-content" id="${panelId}" ${expanded?'':'hidden'}>${cards}</div></section>`;
      }).join('');
      const selectionPrompt=minRoster===maxRoster?`Select exactly ${maxRoster} operatives.`:`Select between ${minRoster} and ${maxRoster} operatives.`;
      const selectionCount=minRoster===maxRoster?`Total Operatives: ${selected.size} of ${maxRoster}`:`Total Operatives: ${selected.size} of ${maxRoster} (minimum ${minRoster})`;
      const requirements=[];
      if(hasGravis)requirements.push(`Required Gravis: ${gravisCount} of 1`);
      if(Number.isFinite(maxGunners))requirements.push(`Maximum Gunners: ${gunnerCount} of ${maxGunners}`);
      if(requiredLeaderId||requiredLeaderCategory)requirements.push(`Required Leader: ${selectedLeaderCount} of ${requiredLeaderCount}`);
      if(mandatoryTroopers)requirements.push(`Required Troopers: ${trooperCount} of ${mandatoryTroopers}`);
      requirements.push(selectionCount);
      const valid=requiredLeaderSelected&&gunnerCount<=maxGunners&&trooperCount>=mandatoryTroopers&&(!hasGravis||(gravisCount>=1&&gravisCount<=maxGravis))&&selected.size>=minRoster&&selected.size<=maxRoster;
      const requirementItems=requirements.map(requirement=>`<li>${escapeHtml(requirement)}</li>`).join('');
      return `<h3>Choose your ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Kill Team')} roster</h3><p>${selectionPrompt}</p><p class="muted">Build a legal kill team using its current official rules. The Guide tracks selected operatives but does not validate every team-building restriction. Cooperative team splitting is not currently supported.</p><div class="setup-bulk-row"><button class="btn secondary" id="randomPlayerTeam">Random Team</button></div><section class="player-roster-summary" aria-labelledby="roster-requirements-heading"><h4 id="roster-requirements-heading">Roster Requirements</h4><ul>${requirementItems}</ul></section><div class="roster-categories">${sections}</div>${selectedDefs.length?`<div class="summary-box"><strong>Selected roster</strong><br>${selectedDefs.map(o=>escapeHtml(o.name)).join(' · ')}</div>`:''}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${valid?'':'disabled'}>Roster Ready</button></div>`;
    }
    if(stepId==='deploy'){
      const generation=state.startingNpoGeneration;
      const dice=generation.dice.map(value=>dieHtml({value,kind:'hit'})).join('');
      const missionRoll=`<div class="starting-npo-event" id="startingNpoEvent" role="status" aria-live="polite"><small>MISSION ROLL</small><div class="dice-row ${generation.animationShown?'settled':'animated-roll'}" id="startingNpoDice">${generation.animationShown?dice:generation.dice.map(()=>rollingDieHtml()).join('')}</div><div class="starting-npo-result" id="startingNpoResult" ${generation.animationShown?'':'hidden'}><strong>${generation.missionRoll} Starting NPOs</strong><span>${generation.calculation}</span></div></div>`;
      const placementChecks=missionSetupChecks('deploy');
      const deploymentCheck=placementChecks.find(check=>check.id==='starting-npos');
      const otherPlacementChecks=placementChecks.filter(check=>check.id!=='starting-npos');
      const deploymentInstruction=`Deploy the ${generation.deploymentCount} selected starting NPOs.`;
      const deployedNpoRoster=generation.deployedNpoIds.map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean).map(npo=>escapeHtml(npoName(npo))).join(' • ');
      const playerRoster=(state.playerRoster||[]).map(id=>playerDefinition(id)).filter(Boolean).map(operative=>escapeHtml(operative.name)).join(' • ');
      const deploymentDetails=mission().startingNpos?.deployment||'Use the mission deployment rules.';
      const selectionComplete=generation.deployedNpoIds.length===generation.deploymentCount&&generation.deployedNpoIds.length+generation.reserveNpoIds.length===generation.availableNpos;
      const allNposPlaced=selectionComplete&&generation.deployedNpoIds.every(id=>state.roster.find(npo=>npo.id===id)?.deployed);
      const deploymentRow=deploymentCheck?`<label class="check-row deployment-check"><input id="npoDeployed" type="checkbox" data-check="${escapeHtml(deploymentCheck.id)}" ${state.setupChecks[deploymentCheck.id]&&allNposPlaced?'checked':''}><span><strong>${deploymentInstruction}</strong><span class="deployment-roster">• ${deployedNpoRoster}</span><small>${escapeHtml(deploymentDetails)}</small></span></label>`:'';
      const allPlacementChecked=placementChecks.length>0&&placementChecks.every(check=>state.setupChecks[check.id]);
      const {minRoster,maxRoster}=playerRosterLimits();
      const playerValid=(state.playerRoster||[]).length>=minRoster&&(state.playerRoster||[]).length<=maxRoster;
      return `<h3>Deploy Kill Teams</h3><p>Use the generated rosters to place both forces, then confirm every mission requirement and resource choice.</p>${missionRoll}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllDeployment" ${playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked?'disabled':''}>Check All</button></div><div class="checklist deployment-checklist">${deploymentRow}${setupChecklistHtml(otherPlacementChecks)}<label class="check-row deployment-check"><input id="playerDeployed" type="checkbox" ${state.playerDeployed?'checked':''} ${playerValid?'':'disabled'}><span><strong>Deploy ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} Kill Team</strong><span class="deployment-roster">• ${playerRoster}</span><small>All selected Player operatives are on the battlefield.</small></span></label></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked?'':'disabled'}>Deployment Complete</button></div>`;
    }
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name||'Special Rule')}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary||'')}</p></div>`).join('');
    return `<h3>Mission Briefing</h3><div class="mission-briefing"><div class="mission-briefing-section mission-heading"><span>Mission</span><strong>${escapeHtml(m.number)} · ${escapeHtml(m.name)}</strong></div><div class="mission-briefing-section"><h4>Objective</h4><p>${escapeHtml(m.objective)}</p></div><div class="mission-briefing-section"><h4>Special Rules</h4>${rules||`<p>${escapeHtml(missionSpecial())}</p>`}</div></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function bindSetup(stepId){
    $$('.mission-choice').forEach(b=>b.onclick=async()=>{state.missionId=b.dataset.mission;state.missionState=freshMissionState(mission());state.missionRuntime=null;await loadObjectiveMission();state.tracker=0;state.setupChecks={};state.roster=[];state.startingNpoGeneration=null;save();render();});
    $('#setupHome')?.addEventListener('click',()=>{state.screen='home';save();render();});
    $('#setupBack')?.addEventListener('click',()=>{state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>{const steps=activeSetupSteps();state.setupStep=Math.min(steps.length-1,state.setupStep+1);save();render();});
    $$('[data-player-team]').forEach(button=>button.onclick=async()=>{
      try{
        if(state.playerTeamId!==button.dataset.playerTeam){
          state.playerTeamId=button.dataset.playerTeam;
          state.playerRosterInitializedForTeamId='';
          state.playerRoster=[];state.playerCount=0;state.playerReady=0;state.playerCasualtyIds=[];state.playerWounds={};state.playerActivatedIds=[];state.playerDeployed=false;
          await loadPlayerTeamData(state.playerTeamId);
        }
        save();render();
      }catch(error){console.error(error);showToast(error.message);}
    });
    $$('[data-check]').forEach(c=>c.onchange=()=>{state.setupChecks[c.dataset.check]=c.checked;save();render();});
    $('#checkAllSetup')?.addEventListener('click',()=>{missionSetupChecks('killzone').forEach(check=>{state.setupChecks[check.id]=true;});save();render();});
    $('#randomPlayerTeam')?.addEventListener('click',()=>{randomPlayerRoster();save();render();});
    if(stepId==='deploy')runStartingNpoGeneration();
    $('#npoDeployed')?.addEventListener('change',e=>{const selected=new Set(state.startingNpoGeneration?.deployedNpoIds||[]);state.roster.filter(n=>selected.has(n.id)).forEach(n=>n.deployed=e.target.checked);save();render();});
    $('#checkAllDeployment')?.addEventListener('click',()=>{
      $$('.checklist input[type="checkbox"]:not(:disabled)').forEach(checkbox=>{
        if(!checkbox.checked){checkbox.checked=true;checkbox.dispatchEvent(new Event('change',{bubbles:true}));}
      });
    });
    $$('[data-roster-category-toggle]').forEach(button=>button.addEventListener('click',()=>{
      const expanded=button.getAttribute('aria-expanded')==='true';
      if(expanded)expandedRosterCategories.delete(button.dataset.rosterCategoryToggle);
      else expandedRosterCategories.add(button.dataset.rosterCategoryToggle);
      button.setAttribute('aria-expanded',String(!expanded));
      const content=document.getElementById(button.getAttribute('aria-controls'));
      if(content)content.hidden=expanded;
    }));
    $$('[data-select-player]').forEach(button=>button.addEventListener('click',()=>{
      const id=button.dataset.selectPlayer;
      const selected=new Set(state.playerRoster||[]);
      if(selected.has(id))selected.delete(id);
      else if(selected.size<playerRosterLimits().maxRoster){
        const candidate=playerDefinition(id);
        if(candidate?.gravis&&selectedPlayerOperatives().some(o=>o.gravis)){showToast('This Kill Team can include only one Gravis operative.');return;}
        const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners||Infinity);
        if(candidate?.role==='Gunner'&&selectedPlayerOperatives().filter(o=>o.role==='Gunner').length>=maxGunners){showToast(`This Kill Team can include only ${maxGunners} Gunners.`);return;}
        selected.add(id);
      }
      applyPlayerRoster(selected);
      save();render();
    }));
    $('#playerDeployed')?.addEventListener('change',e=>{state.playerDeployed=e.target.checked;save();render();});
    $('#beginGame')?.addEventListener('click',()=>{
      state.screen='game';state.tab='play';state.turningPoint=0;state.phase='between';state.nextSide='player';state.playerCount=(state.playerRoster||[]).length;state.playerReady=state.playerCount;
      if(!state.playerWounds||Object.keys(state.playerWounds).length===0)initializePlayerWounds();
      state.roster.forEach(n=>n.ready=false);log(`Mission started: ${mission().name}.`);startTurningPoint();
    });
  }

  function runStartingNpoGeneration(){
    if(typeof startingNpoTimer==='function')startingNpoTimer();
    else clearTimeout(startingNpoTimer);
    startingNpoTimer=null;
    const event=$('#startingNpoEvent'),generation=state.startingNpoGeneration;
    if(!event||!generation)return;
    const showResult=()=>{
      const result=$('#startingNpoResult');
      if(!result)return;
      result.hidden=false;
    };
    if(generation.animationShown)return;
    generation.animationShown=true;
    save();
    startingNpoTimer=settleAnimatedDice([{
      row:$('#startingNpoDice'),
      dice:generation.dice.map(value=>({value,kind:'hit'}))
    }],()=>{
      startingNpoTimer=null;
      showResult();
    });
  }

  function renderGame(){
    if(state.gameEnd){
      const victory=state.gameEnd==='victory';
      app.innerHTML=`<section class="hero-card mission-outcome"><p class="eyebrow">MISSION COMPLETE</p><img class="game-end-image" src="Assets/Images/${victory?'victory':'defeat'}.png" alt="${victory?'Victory':'Defeat'}"><h2>${victory?'Victory':'Defeat'}</h2><p>${escapeHtml(victory?missionEngine()?.success:missionEngine()?.failure)}</p>${missionProgressHtml(true)}<div class="button-row"><button class="btn secondary" id="reviewCompletedMission">Review Mission</button><button class="btn primary" id="gameEndNewGame">Start New Game</button></div></section>`;
      $('#reviewCompletedMission').onclick=()=>showModal(`${mission().number} · ${mission().name}`,`<p><strong>Objective:</strong> ${escapeHtml(mission().objective)}</p><p><strong>Outcome:</strong> ${escapeHtml(victory?missionEngine()?.success:missionEngine()?.failure)}</p><div class="wizard-actions"><button class="btn primary" data-close>Done</button></div>`);
      $('#gameEndNewGame').onclick=confirmNewGame;
      return;
    }
    if(state.tab==='play') renderPlay();
    else if(state.tab==='mission'){renderMission();bindMissionProgressControls();}
    else if(state.tab==='roster') renderRoster();
    else if(state.tab==='player-roster') renderPlayerRoster();
    else if(state.tab==='journal') renderJournal();
    else renderHelp();

    if(state.tab!=='play'){
      app.insertAdjacentHTML('afterbegin',`<div class="reference-return"><button class="btn primary" id="returnToGuide">Return to Guided Play</button><small>Reference screens do not change the current Turning Point or activation state.</small></div>`);
      $('#returnToGuide').onclick=()=>{state.tab='play';save();render();};
    }
  }

  function missionHudHtml(){
    const model=objectiveEngine?.getMissionHudModel();
    const visible=model?.visible!==false;
    if(!visible)return '';
    const label=model?.label||'MISSION';
    const value=model?(model.completed?'✓ COMPLETE':`${model.value} / ${model.target}`):'DETAILS';
    const status=model?`${model.value} of ${model.target}${model.completed?', objective complete':''}`:'details';
    const name=model?.name||mission()?.name||'selected mission';
    return `<button class="hud-cell mission-hud" id="missionHud" type="button" aria-label="Mission details, ${escapeHtml(name)}, ${escapeHtml(status)}"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong></button>`;
  }

  function hud(){return `<div class="hud"><div><small>Turning<span class="portrait-break"><br></span> Point</small><strong>${state.turningPoint||'Setup'}</strong></div><button class="hud-cell hud-threat" id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"><small>Threat<span class="portrait-break"><br></span> Level</small><strong>${state.threat}</strong></button><div><small>Grade<span class="portrait-break"><br></span> Level</small><strong>${threatGrade()}</strong></div><div><small>Player<span class="portrait-break"><br></span> Ready</small><strong>${state.playerReady}</strong></div><div><small>NPO<span class="portrait-break"><br></span> Ready</small><strong>${readyNpos().length}</strong></div>${missionHudHtml()}</div><div class="threat-strip ${threatAdjustOpen?'':'hidden'}" id="threatAdjuster"><div><strong>THREAT LEVEL: ${threatLabel()}</strong><small>${threatGrade()===3?'Maximum Grade':`Next Grade at Threat Level ${[1,6,11][threatGrade()]}`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function livingPlayerOptions(selected=''){
    return (state.playerRoster||[]).filter(id=>!state.playerCasualtyIds.includes(id)).map(id=>`<option value="${escapeHtml(id)}" ${id===selected?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
  }

  const missionProgressRenderers = {
    escape:(engine,progress)=>{
      const escaped=new Set(progress.escapedIds);
      const rows=(state.playerRoster||[]).map(id=>{const incapacitated=state.playerCasualtyIds.includes(id);return `<div class="mission-objective-row"><span><strong>${escapeHtml(playerName(id))}</strong><small>${escaped.has(id)?'Escaped via the Escape marker':incapacitated?'Incapacitated':'Still in the killzone'}</small></span>${incapacitated?'':`<button class="btn compact ${escaped.has(id)?'primary':'ghost'}" data-mission-escaped="${escapeHtml(id)}">${escaped.has(id)?'Escaped':'Confirm Escape'}</button>`}</div>`;}).join('');
      return `<p>${escaped.size} of ${state.playerRoster.length} operatives escaped. Resolve the mission only after every operative has left the killzone.</p><div class="mission-objective-list">${rows}</div>`;
    },
    sabotage:(engine,progress)=>{
      const completed=new Set(progress.completedFeatureIds);
      return `<p>${completed.size} of ${engine.required} required features have been permanently opened by Breach.</p><div class="mission-objective-grid">${engine.features.map(feature=>`<label class="mission-objective-check"><input type="checkbox" data-mission-feature="${feature.id}" ${completed.has(feature.id)?'checked':''}><span>${escapeHtml(feature.label)}</span></label>`).join('')}</div>`;
    },
    transponder:(engine,progress)=>{
      const transponderFound=Object.values(progress.sites).includes('found');
      const sites=engine.sites.map(site=>{const result=progress.sites[site.id];return `<div class="mission-objective-row"><span><strong>${escapeHtml(site.label)}</strong><small>${result==='found'?'Transponder found':result==='empty'?'Removed — no transponder':'Unresolved'}</small></span>${result||transponderFound?'' : `<button class="btn secondary compact" data-search-site="${site.id}">Pick Up & Resolve</button>`}</div>`;}).join('');
      const carrier=progress.carrierId?playerName(progress.carrierId):'None';
      return `<p>Pick up an unresolved marker, then roll D3. The transponder is found only if the result is higher than the number of other unresolved markers.</p>${progress.lastRoll?`<div class="summary-box"><strong>Last search:</strong> rolled ${progress.lastRoll.roll}; ${escapeHtml(progress.lastRoll.result)}.</div>`:''}${transponderFound?`<div class="field"><label for="transponderCarrier">Current carrier</label><select id="transponderCarrier"><option value="">Marker is not being carried…</option>${livingPlayerOptions(progress.carrierId)}</select></div>`:`<div class="field"><label for="transponderOperative">Operative resolving the marker</label><select id="transponderOperative"><option value="">Select operative…</option>${livingPlayerOptions()}</select></div>`}<div class="mission-objective-list">${sites}</div><div class="summary-box"><strong>Carrier:</strong> ${escapeHtml(carrier)}</div><button class="btn primary" id="transponderEscape" ${progress.carrierId&&!state.playerCasualtyIds.includes(progress.carrierId)&&!progress.escaped?'':'disabled'}>Confirm Carrier Escaped</button>`;
    },
    destruction:()=>{
      if(!objectiveEngine)return '<p class="muted">Mission automation is unavailable.</p>';
      const model=objectiveEngine.getMissionHudModel();
      const action=objectiveDefinition.actions[0];
      const objective=objectiveDefinition.objectives.find(item=>item.id===model.objectiveId);
      const dice=action.operations.find(operation=>operation.type==='requestDiceRoll')?.dice;
      const available=objectiveEngine.evaluateMissionConditions(action.availability);
      const diceLabel=dice?`${dice.count}D${dice.sides}`:'';
      return `<p>${escapeHtml(objectiveDefinition.briefing)}</p><p><strong>${model.value} / ${model.target} ${escapeHtml(objective.label)}</strong></p>${available?`<button class="btn primary" id="resolveMissionAction" ${missionOperationResolving?'disabled':''}>${escapeHtml(action.label)}${diceLabel?` (${diceLabel})`:''}</button>`:`<div class="summary-box"><strong>✓ COMPLETE</strong><br>${model.value} / ${model.target} ${escapeHtml(objective.label)}</div>`}`;
    },
    scout:(engine,progress)=>{
      const scouted=new Set(progress.scoutedRoomIds);
      const rooms=engine.rooms.map(room=>{const awakening=progress.awakenedRooms[room.id];return `<div class="mission-objective-row"><span><strong>${escapeHtml(room.label)}</strong><small>${scouted.has(room.id)?'Scouted':awakening?`${awakening.count} NPOs generated${awakening.placementConfirmed?' and placed':' — placement required'}`:'Unopened / unentered'}</small></span><div class="mission-objective-actions">${awakening?'':`<button class="btn secondary compact" data-awaken-room="${room.id}">First Open / Entry</button>`}${awakening&&!awakening.placementConfirmed?`<button class="btn secondary compact" data-confirm-room-placement="${room.id}">Confirm Placement</button>`:''}${awakening?.placementConfirmed&&!scouted.has(room.id)?`<button class="btn primary compact" data-scout-room="${room.id}">Confirm Cleared & Scout</button>`:''}</div></div>`;}).join('');
      return `<p>${scouted.size} of ${engine.required} rooms scouted. Confirm that an eligible room is cleared on the tabletop before resolving the 1AP Scout Room action.</p><div class="mission-objective-list">${rooms}</div>`;
    },
    regroup:(engine,progress)=>{
      const survivors=(state.playerRoster||[]).filter(id=>!state.playerCasualtyIds.includes(id));
      const rows=survivors.map(id=>{const check=progress.operativeChecks[id]||{};return `<div class="mission-regroup-row"><strong>${escapeHtml(playerName(id))}</strong><label><input type="checkbox" data-regroup-check="inDropZone" data-operative-id="${id}" ${check.inDropZone?'checked':''}> Wholly in NPO drop zone</label><label><input type="checkbox" data-regroup-check="outsideNpoControl" data-operative-id="${id}" ${check.outsideNpoControl?'checked':''}> Outside NPO control range</label><label><input type="checkbox" data-regroup-check="nearPlayer" data-operative-id="${id}" ${check.nearPlayer?'checked':''}> Within 3 inches of another Player operative</label></div>`;}).join('');
      return `<p>Record the position of every surviving operative. Victory is evaluated only when the Turning Point is finished.</p><div class="mission-objective-list">${rows}</div>`;
    }
  };

  function missionProgressHtml(readOnly=false){
    const engine=missionEngine(), progress=state.missionState||freshMissionState();
    const renderer=missionProgressRenderers[engine?.type];
    if(!renderer)return '';
    return `<section class="card mission-objective-card"><p class="eyebrow">MISSION OBJECTIVE</p><h3>${escapeHtml(engine.progressLabel)}</h3><div ${readOnly?'inert':''}>${renderer(engine,progress)}</div>${readOnly?'<p class="muted">Completed mission state is preserved for review.</p>':''}</section>`;
  }

  function updateMissionProgress(message){
    if(message)log(`${mission().name}: ${message}`);
    if(checkGameEnd())return;
    save();render();
  }

  function bindMissionProgressControls(){
    $$('[data-mission-escaped]').forEach(button=>button.onclick=()=>{
      const id=button.dataset.missionEscaped, ids=new Set(state.missionState.escapedIds);
      ids.has(id)?ids.delete(id):ids.add(id);
      state.missionState.escapedIds=[...ids];
      updateMissionProgress(`${playerName(id)} ${ids.has(id)?'escaped via the Escape marker':'escape status was corrected'}.`);
    });
    $$('[data-mission-feature]').forEach(input=>input.onchange=()=>{
      const ids=new Set(state.missionState.completedFeatureIds);
      input.checked?ids.add(input.dataset.missionFeature):ids.delete(input.dataset.missionFeature);
      state.missionState.completedFeatureIds=[...ids];
      updateMissionProgress(`${input.checked?'completed Breach on':'corrected'} ${input.dataset.missionFeature}.`);
    });
    $$('[data-search-site]').forEach(button=>button.onclick=()=>{
      const carrier=$('#transponderOperative')?.value;
      if(!carrier){showToast('Select the operative picking up this marker.');return;}
      const progress=state.missionState;
      const otherRemaining=missionEngine().sites.filter(site=>site.id!==button.dataset.searchSite&&!progress.sites[site.id]).length;
      const result=rollD3(), found=result>otherRemaining;
      progress.sites[button.dataset.searchSite]=found?'found':'empty';
      if(found)progress.carrierId=carrier;
      progress.lastRoll={siteId:button.dataset.searchSite,roll:result,result:found?'transponder found':'marker removed'};
      updateMissionProgress(`searched ${button.dataset.searchSite}, rolled ${result}, and ${found?'found the transponder':'removed the marker'}.`);
    });
    $('#transponderCarrier')?.addEventListener('change',event=>{state.missionState.carrierId=event.target.value||null;save();render();});
    $('#transponderEscape')?.addEventListener('click',()=>{state.missionState.escaped=true;updateMissionProgress(`${playerName(state.missionState.carrierId)} escaped carrying the transponder.`);});
    $('#resolveMissionAction')?.addEventListener('click',confirmMissionAction);
    $$('[data-awaken-room]').forEach(button=>button.onclick=()=>{
      const count=Math.min(5,rollD3()+threatGrade()), ids=[];
      for(let i=0;i<count&&activeNpos().length<MAX_NPOS;i++){
        const result=rollNpo(), n=createNpo(result.type,`${result.type} ${button.dataset.awakenRoom}`,{weaponId:result.weaponId,ready:true,dormant:false,deployed:false,order:'Conceal'});
        n.missionRoom=button.dataset.awakenRoom;state.roster.push(n);ids.push(n.id);
      }
      state.missionState.awakenedRooms[button.dataset.awakenRoom]={count:ids.length,operativeIds:ids,placementConfirmed:false};
      updateMissionProgress(`${button.dataset.awakenRoom} awakened; generated ${ids.length} ready NPO(s) with Conceal orders for tabletop placement.`);
    });
    $$('[data-confirm-room-placement]').forEach(button=>button.onclick=()=>{
      const awakening=state.missionState.awakenedRooms[button.dataset.confirmRoomPlacement];awakening.placementConfirmed=true;
      state.roster.filter(npo=>awakening.operativeIds.includes(npo.id)).forEach(npo=>{npo.deployed=true;npo.battlefieldState='deployed';});
      updateMissionProgress(`confirmed NPO placement in ${button.dataset.confirmRoomPlacement}.`);
    });
    $$('[data-scout-room]').forEach(button=>button.onclick=()=>{
      const ids=new Set(state.missionState.scoutedRoomIds);ids.add(button.dataset.scoutRoom);state.missionState.scoutedRoomIds=[...ids];
      const grade=threatGrade(), gradeFloor=[0,0,5,10][grade];
      if(state.threat>gradeFloor)setThreat(gradeFloor-state.threat,'Scout Room');
      updateMissionProgress(`scouted ${button.dataset.scoutRoom}.`);
    });
    $$('[data-regroup-check]').forEach(input=>input.onchange=()=>{
      const id=input.dataset.operativeId;
      state.missionState.operativeChecks[id]={...(state.missionState.operativeChecks[id]||{}),[input.dataset.regroupCheck]:input.checked};
      state.missionState.lastCheckedTurningPoint=state.turningPoint;save();
    });
  }

  function renderPlay(){
    const milestone=state.gradeMilestone?`<section class="grade-milestone"><div><small>THREAT ESCALATION</small><strong>Grade ${state.gradeMilestone.grade}: ${escapeHtml(state.gradeMilestone.label)}</strong><span>Threat has reached Level ${state.gradeMilestone.threat}.</span></div><button class="btn ghost compact" id="dismissGradeMilestone">Dismiss</button></section>`:'';
    app.innerHTML=hud()+milestone+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${state.phase!=='strategy'?activeEventEffectsHtml():''}${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
    bindPlay();
  }

  function activeEventEffectsHtml(){
    const active=state.eventState.active||[];
    if(!active.length)return '';
    return `<section class="card"><p class="eyebrow">ACTIVE TOMB WORLD ${active.length===1?'EVENT':'EVENTS'}</p>${active.map(event=>`<div class="summary-box"><strong>${escapeHtml(event.title)}</strong><br>${escapeHtml(event.text)}</div>`).join('')}</section>`;
  }

  function nextStepCard(){
    if(state.completed) return `<section class="next-card"><span class="phase">MISSION COMPLETE</span><h2>Record the outcome</h2><p>The mission has reached its conclusion. Review the Journal or begin a new game.</p><button class="btn primary big-action" id="newGameFromPlay">Start New Game</button></section>`;
    if(state.phase==='between'){
      return `<section class="next-card"><span class="phase">NEXT STEP</span><h2>Start Turning Point ${state.turningPoint+1}</h2><p>The Guide will ready operatives, apply mission Ready rules, determine initiative, then process current events and reinforcements.</p><button class="btn primary big-action" id="startTp">Start Next Turning Point</button></section>`;
    }
    if(state.phase==='strategy') return strategyCard();
    if(state.phase==='end'){
      const npoLosses=Math.max(0,destroyedNpoCount()-(state.tpStartDestroyedNpos||0));
      const playerLosses=Math.max(0,(state.playerCasualtyIds||[]).length-(state.tpStartPlayerCasualties||0));
      const threatChanged=state.threat!==(state.tpStartThreat??state.threat);
      const gradeChanged=threatGrade()!==(state.tpStartGrade??threatGrade());
      return `<section class="next-card"><span class="phase">TURNING POINT ${state.turningPoint} COMPLETE</span><h2>Battle summary</h2><div class="turn-summary-grid"><div><small>Threat</small><strong>${state.tpStartThreat??state.threat} → ${state.threat}</strong><span>${threatChanged?'Changed this Turning Point':'No change'}</span></div><div><small>Grade</small><strong>${state.tpStartGrade??threatGrade()} → ${threatGrade()}</strong><span>${gradeChanged?'Grade increased':'Grade unchanged'}</span></div><div><small>NPOs destroyed</small><strong>${npoLosses}</strong><span>This Turning Point</span></div><div><small>Player casualties</small><strong>${playerLosses}</strong><span>This Turning Point</span></div></div><h3>Score and clean up</h3><p>Score mission objectives, resolve end-of-turn effects, and confirm all temporary markers have been cleared.</p>${missionProgressHtml()}<div class="checklist"><label class="check-row"><input id="endChecked" type="checkbox"><span><strong>End-of-turn steps complete</strong><small>Objectives scored, temporary effects resolved, and physical tokens cleaned up.</small></span></label></div><button class="btn primary big-action" id="finishTp" disabled>Finish Turning Point</button></section>`;
    }
    setNextActivation(state.nextSide || state.initiative || 'player');
    if(state.phase==='end'){save();return nextStepCard();}
    if(state.nextSide==='player' && playerOperativesRemaining()>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ${activationProgressLabel()}</span><h2>Player Activation</h2>${initiativeStatusHtml()}<p>Activate one Player operative on the tabletop. After it completes, the Guide will alternate to an NPO if one is ready.</p><button class="btn primary big-action" id="playerActivation">Activate an Operative</button></section>`;
    if(state.nextSide==='npo' && readyNpos().length>0)return `<section class="next-card npo-activation-card"><span class="phase">NPO ACTIVATION · ${activationProgressLabel()}</span><h2 class="npo-activation-title">NPO Activation</h2><p class="npo-activation-meta">Identify the next ready NPO using the Threat Principle.</p><button class="btn primary big-action" id="npoActivation">Activate NPO</button></section>`;
    setNextActivation(state.nextSide==='player'?'npo':'player');
    save();
    return nextStepCard();
  }

  function initiativeStatusHtml(){
    const side=state.initiative==='npo'?'NPOs':'Player';
    const deployed=activeNpos();
    const dormantNote=deployed.length&&deployed.every(npo=>npo.dormant)
      ? ' All deployed NPOs are currently dormant. No NPO activation occurs.'
      : '';
    return `<div class="summary-box"><strong>${side} ${side==='NPOs'?'have':'has'} initiative.</strong>${dormantNote}</div>`;
  }

  function missionStrategyPending(){
    return missionEngine()?.type==='escape'&&state.turningPoint>1&&!state.missionState.escapedIds.length&&!state.missionState.auspexCalibrations[state.turningPoint];
  }

  function missionStrategyPromptHtml(){
    if(missionEngine()?.type!=='escape'||state.turningPoint<=1||state.missionState.escapedIds.length)return '';
    const calibration=state.missionState.auspexCalibrations[state.turningPoint];
    if(calibration)return `<div class="summary-box"><strong>Auspex Calibration:</strong> ${escapeHtml(calibration.instruction)}</div>`;
    return `<div class="summary-box"><strong>Auspex Calibration required.</strong><br>No operatives have escaped. Resolve the mission’s Strategic Gambit before continuing.<div class="event-controls"><button class="btn secondary" id="resolveAuspexCalibration">Roll Auspex Calibration</button></div></div>`;
  }

  function strategyCard(){
    const d=state.strategyData||{};
    if(state.strategyStage==='mission-ready')return `<section class="next-card"><span class="phase">STRATEGY PHASE · READY STEP</span><h2>Mission event pending</h2><p>Complete the mission Ready-step event before initiative is determined.</p><button class="btn primary big-action" id="retryMissionReady">Continue Mission Event</button></section>`;
    if(state.strategyStage==='summary'){
      const reinforcementPending=Boolean(d.eventPending);
      const placementPending=state.reinforcementState.status==='placement', missionPending=missionStrategyPending();
      const deployingNpos=(state.reinforcementState.operativeIds||[]).map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean);
      const blockedNpos=(state.reinforcementState.blockedOperativeIds||[]).map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean);
      const reinforcementCard=deployingNpos.length||d.blocked
        ? `<section class="card reinforcement-card"><p class="eyebrow">REINFORCEMENTS</p>${deployingNpos.length?`<h3>Deploy ${deployingNpos.length} NPO${deployingNpos.length===1?'':'s'}</h3><ul class="reinforcement-list">${deployingNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul><p>Deploy ${deployingNpos.length===1?'this NPO':'these NPOs'} onto the battlefield using the Tomb World reinforcement rules.</p>`:''}${d.blocked?`<div class="reinforcement-blocked"><h3>Unable to Deploy</h3>${blockedNpos.length?`<ul class="reinforcement-list">${blockedNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul>`:`<p>${d.blocked} reinforcement${d.blocked===1?'':'s'}</p>`}<p>Battlefield NPO limit reached.</p></div>`:''}</section>`:'';
      const placements=(state.reinforcementState.operativeIds||[]).map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean).map(npo=>`<div class="check-row"><input type="checkbox" data-reinforcement-placement="${escapeHtml(npo.id)}" aria-label="Confirm placement for ${escapeHtml(npoName(npo))}" ${npo.reinforcement?.placementConfirmed?'checked':''}><span><strong>${escapeHtml(npoName(npo))} · ${escapeHtml(npoWeapon(npoDefinition(npo.type),npo.weaponId)?.name||npo.weaponId)}</strong><small>Randomly determine an open hatchway, set up this operative with a Conceal order using the printed placement requirements, then confirm.</small><input type="text" data-reinforcement-hatchway="${escapeHtml(npo.id)}" value="${escapeHtml(npo.reinforcement?.hatchway||'')}" placeholder="Random hatchway" aria-label="Random hatchway for ${escapeHtml(npoName(npo))}"></span></div>`).join('');
      const resolvedEvents=(d.events||[]).filter(event=>event!==d.event&&event.status!=='drawn').map(strategyEventHtml).join('');
      const activeEvents=(state.eventState.active||[]).map(event=>`<div class="summary-box"><strong>${escapeHtml(event.title)}</strong><br>${escapeHtml(event.text)}</div>`).join('');
      const showStatTooltips=!window.matchMedia('(max-width:600px)').matches;
      const tooltipAttrs=text=>showStatTooltips?` tabindex="0" data-tooltip="${text}"`:'';
      const infoDot=showStatTooltips?'<span class="info-dot">i</span>':'';
      return `<section class="next-card"><span class="phase">STRATEGY PHASE</span><h2>Complete the Strategy Phase</h2><p class="strategy-intro">Before continuing to initiative, complete the tabletop Strategy Phase for Turning Point ${state.turningPoint}.</p><div class="strategy-phase-guide"><ol><li>Generate Command Points (CP) as required by the game rules.</li><li>Play any Strategic Ploys you want to use this Turning Point.</li><li>Resolve abilities and mission rules that occur during the Strategy Phase.</li><li>Review the Guide's Threat, reinforcement, and Tomb World event results below.</li></ol></div>${missionStrategyPromptHtml()}<div class="stat-grid strategy-stat-grid"><div class="stat tooltip-stat"${tooltipAttrs('Threat rises from loud or aggressive actions. Higher Threat can increase the Grade, reinforcements, and Tomb World events.')}><small>THREAT LEVEL ${infoDot}</small><strong>${state.threat}</strong></div><div class="stat tooltip-stat"${tooltipAttrs('Grade 0–3 is derived from Threat and determines reinforcement pressure and some events.')}><small>GRADE LEVEL ${infoDot}</small><strong>${threatGrade()}</strong></div><div class="stat tooltip-stat"${tooltipAttrs('The number of living NPOs that are Ready and may still activate during this Turning Point.')}><small>NPOs Ready ${infoDot}</small><strong>${readyNpos().length}</strong></div></div>${reinforcementPending?'<div class="summary-box"><strong>Resolve the Tomb World event before generating reinforcements.</strong></div>':`${reinforcementCard}${deployingNpos.length?`<div class="checklist">${placements}</div>`:''}`}${resolvedEvents}${d.event?.status==='drawn'?strategyEventHtml(d.event):''}${activeEvents?`<h3>Active event effects</h3>${activeEvents}`:''}<button class="btn primary big-action" id="continueStrategy" ${reinforcementPending||placementPending||missionPending?'disabled':''}>${reinforcementPending?'Resolve Event to Continue':placementPending?'Confirm Reinforcement Placement':missionPending?'Resolve Mission Rule to Continue':'Strategy Phase Complete'}</button></section>`;
    }
    return '';
  }

  function strategyEventHtml(event){
    const title=event.title||event[0],description=event.text||event.description||event[1];
    if(event.type!=='tomb-world-event')return `<div class="summary-box"><strong>${escapeHtml(title)}</strong><br>${escapeHtml(description)}</div>`;
    const eventHeader=`<div class="tomb-world-event-header"><span class="tomb-world-event-icon" aria-hidden="true"><svg
  class="tomb-world-event-anomaly-icon"
  viewBox="0 0 32 32"
  width="32"
  height="32"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  focusable="false"
>
  <!-- Outer broken energy ring -->
  <path
    d="M16 3.5A12.5 12.5 0 0 1 27.7 11.6"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <path
    d="M28.3 16A12.3 12.3 0 0 1 20.8 27.3"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <path
    d="M15.8 28.5A12.5 12.5 0 0 1 4.2 20.3"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <path
    d="M3.7 15.8A12.2 12.2 0 0 1 11.2 4.6"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <!-- Inner anomaly core -->
  <circle
    cx="16"
    cy="16"
    r="4.25"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Energy spokes -->
  <path
    d="M16 7.25V11.5"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <path
    d="M16 20.5V24.75"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <path
    d="M7.25 16H11.5"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <path
    d="M20.5 16H24.75"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <!-- Necron-like floating shards -->
  <path
    d="M9.4 8.9L11.9 8.2L11.2 10.7L9.4 8.9Z"
    fill="currentColor"
  />
  <path
    d="M22.7 9.4L24.9 11.2L22.3 11.8L22.7 9.4Z"
    fill="currentColor"
  />
  <path
    d="M22.8 22.6L20.4 23.5L21.1 20.9L22.8 22.6Z"
    fill="currentColor"
  />
  <path
    d="M9.1 22.1L7.2 20.3L9.8 19.8L9.1 22.1Z"
    fill="currentColor"
  />
  <!-- Center singularity -->
  <circle
    cx="16"
    cy="16"
    r="1.45"
    fill="currentColor"
  />
</svg></span><span class="tomb-world-event-label">TOMB WORLD EVENT</span></div>`;
    const eventDetails=`${eventHeader}<h3 class="tomb-world-event-title">${escapeHtml(title)}</h3><div class="tomb-world-event-effect"><div class="tomb-world-event-effect-label">Effect</div><p class="tomb-world-event-description">${escapeHtml(description)}</p></div>`;
    if(event.status!=='drawn')return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite">${eventDetails}<div class="event-resolution">${event.status==='redrawn'?'Redraw required':'Resolved'}: ${escapeHtml(event.result||'Complete')}</div></div>`;
    const labels={
      'awakened-warrior':'Confirm Warrior Placement',
      'chittering-drone':'Confirm Scarab Placement',
      'maze-reforms':'Confirm Terrain Changes',
      'tabletop-confirm':'Confirm Tabletop Resolution'
    };
    const scarabChoices=event.execution.type==='chittering-drone'&&Array.isArray(event.eligibleNpoIds)&&event.eligibleNpoIds.length>1
      ? `<div class="field"><label for="eventNpoSelect">Wounded Scarab Swarm</label><select id="eventNpoSelect"><option value="">Select a Scarab Swarm...</option>${event.eligibleNpoIds.map(id=>{const n=activeNpos().find(item=>item.id===id);return n?`<option value="${escapeHtml(id)}">${escapeHtml(npoName(n))} — ${n.wounds} of ${n.maxWounds} wounds</option>`:'';}).join('')}</select></div>`:'';
    const impossibleControl=event.execution.type==='maze-reforms'?'<button class="btn secondary" id="redrawStrategyEvent">No Valid Changes · Draw Again</button>':'';
    return `<div class="summary-box strategy-event tomb-world-event-card">${eventDetails}<div class="event-controls">${scarabChoices}<button class="btn primary" id="resolveStrategyEvent" ${scarabChoices?'disabled':''}>${labels[event.definitionId]||labels[event.execution.type]||'Resolve Event'}</button>${impossibleControl}</div></div>`;
  }

  function activationTracker(){
    const activatedIds=new Set(state.playerActivatedIds||[]);
    const casualtyIds=new Set(state.playerCasualtyIds||[]);
    const playerRows=(state.playerRoster||[]).map(operativeId=>{
      const operative=playerDefinition(operativeId);
      const casualty=casualtyIds.has(operativeId);
      const activated=activatedIds.has(operativeId);
      const status=casualty?'ELIMINATED':activated?'ACTIVATED':'READY';
      const cls=casualty?'eliminated':activated?'activated':'ready';
      return `<button type="button" class="tracker-operative player ${cls}" data-player-operative="${operativeId}" title="Select ${escapeHtml(operative?.name||operativeId)} to mark it eliminated or restore it">
        <span>${escapeHtml(operative?.name||operativeId)}</span><strong>${status}</strong>
      </button>`;
    }).join('');
    const npoRows=state.roster.map(n=>{
      const eliminated=n.wounds<=0;
      const status=eliminated?'ELIMINATED':n.dormant?'DORMANT':n.ready?'READY':'ACTIVATED';
      const cls=eliminated?'eliminated':n.ready?'ready':'activated';
      return `<div class="tracker-operative npo ${cls}"><span>${escapeHtml(npoName(n))}</span><strong>${status}</strong></div>`;
    }).join('');
    return `<section class="card activation-tracker"><details class="activation-details">
      <summary><div><p class="eyebrow">ACTIVATION TRACKER</p><h3>${state.activationNumber} activations completed</h3></div></summary>
      <div class="activation-details-content">
      <div class="tracker-section">
        <small>${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} operatives</small>
        <p class="muted compact-copy">All selected operatives are listed, including eliminated operatives. Select a Player operative to mark it eliminated or restore it.</p>
        <div class="tracker-operative-grid">${playerRows||'<span class="muted">No player operatives selected</span>'}</div>
      </div>
      <div class="tracker-section">
        <small>NPOs</small>
        <div class="tracker-operative-grid">${npoRows||'<span class="muted">No NPO operatives generated</span>'}</div>
      </div>
      </div>
    </details></section>`;
  }

  function showPlayerOperativeStatus(operativeId){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const eliminated=casualties.has(operativeId);
    const operativeName=playerName(operativeId);
    showModal(operativeName,`
      <p>This status carries across Turning Points and is reflected in the activation tracker and Player Ready count.</p>
      <div class="summary-box"><strong>Current status:</strong> ${eliminated?'Eliminated':'Active'}</div>
      <div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn ${eliminated?'secondary':'danger'}" id="togglePlayerCasualty">${eliminated?'Restore Operative':'Mark Eliminated'}</button></div>`);
    $('#togglePlayerCasualty').onclick=()=>{
      const ids=new Set(state.playerCasualtyIds||[]);
      state.playerWounds=state.playerWounds||{};
      if(ids.has(operativeId)){
        ids.delete(operativeId);
        state.playerWounds[operativeId]=Number(playerDefinition(operativeId)?.wounds||0);
        log(`${operativeName} restored.`);
      }else{
        ids.add(operativeId);
        state.playerWounds[operativeId]=0;
        if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
        log(`${operativeName} eliminated.`);
      }
      state.playerCasualtyIds=[...ids];
      state.playerReady=playerOperativesRemaining();
      if(checkGameEnd())return;
      setNextActivation(state.nextSide||'npo');
      closeModal();
      save();
      render();
    };
  }

  function bindPlay(){
    $('#dismissGradeMilestone')?.addEventListener('click',()=>{state.gradeMilestone=null;save();render();});
    $$('[data-player-operative]').forEach(button=>button.addEventListener('click',()=>showPlayerOperativeStatus(button.dataset.playerOperative)));
    $('#startTp')?.addEventListener('click',startTurningPoint);
    $$('[data-reinforcement-placement]').forEach(input=>input.addEventListener('change',()=>confirmReinforcementPlacement(input.dataset.reinforcementPlacement,input.checked)));
    $$('[data-reinforcement-hatchway]').forEach(input=>input.addEventListener('change',()=>recordReinforcementHatchway(input.dataset.reinforcementHatchway,input.value)));
    $('#eventNpoSelect')?.addEventListener('change',e=>{$('#resolveStrategyEvent').disabled=!e.target.value;});
    $('#resolveStrategyEvent')?.addEventListener('click',resolveStrategyEvent);
    $('#redrawStrategyEvent')?.addEventListener('click',()=>{redrawCurrentEvent('No breach or open hatchway could be changed.');save();render();});
    $('#continueStrategy')?.addEventListener('click',()=>beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player'));
    $('#retryMissionReady')?.addEventListener('click',continueTurningPointStart);
    $('#playerActivation')?.addEventListener('click',()=>showPlayerActivation());
    $('#npoActivation')?.addEventListener('click',showNpoSelection);
    $('#missionHud')?.addEventListener('click',showMissionDetails);
    bindMissionProgressControls();
    $('#resolveAuspexCalibration')?.addEventListener('click',()=>{
      const directionRoll=rollD3(),distance=rollD3()+3;
      const instruction=directionRoll===1?`Move the Escape marker ${distance} inches left.`:directionRoll===2?'Do not move the Escape marker.':`Move the Escape marker ${distance} inches right.`;
      state.missionState.auspexCalibrations[state.turningPoint]={directionRoll,distance,instruction};
      log(`Auspex Calibration: ${instruction}`);save();render();
    });
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',async()=>{
      if(await executeMissionLifecycleHook('onTurningPointEnded')===null)return;
      log(`Turning Point ${state.turningPoint} completed.`);
      state.eventState.active=state.eventState.active.filter(event=>event.expiresAfterTurningPoint!==state.turningPoint);
      state.strategyStage=null;
      state.strategyData=null;
      state.newIds=[];
      if(checkGameEnd('end-turning-point'))return;
      state.phase='between';
      save();render();
    });
    $('#newGameFromPlay')?.addEventListener('click',confirmNewGame);
    $('#threatHudToggle')?.addEventListener('click',()=>{threatAdjustOpen=!threatAdjustOpen;render();});
    $('#threatUp')?.addEventListener('click',()=>{setThreat(1,'Manual adjustment');save();render();});
    $('#threatDown')?.addEventListener('click',()=>{setThreat(-1,'Manual adjustment');save();render();});
  }

  async function startTurningPoint(){
    state.turningPoint++;
    if(missionEngine()?.type==='regroup')state.missionState={operativeChecks:{},lastCheckedTurningPoint:state.turningPoint};
    state.tpStartThreat=state.threat;
    state.tpStartGrade=threatGrade();
    state.tpStartDestroyedNpos=destroyedNpoCount();
    state.tpStartPlayerCasualties=(state.playerCasualtyIds||[]).length;
    state.gradeMilestone=null;
    state.playerReady=Math.max(0,state.playerCount-(state.playerCasualtyIds||[]).length);
    state.playerActivated=0;state.npoActivated=0;state.activationNumber=0;state.activationHistory=[];state.playerActivatedIds=[];
    state.strategyData={grade:threatGrade(),reinforcements:[],actualReinforcements:0,blocked:0,event:null,playerRoll:null,npoRoll:null,suggestedInitiative:'player',missionReadyHooks:[]};
    state.strategyPipeline={current:'ready',completed:[]};
    processReadyStep();
    const missionReadyCompleted=await applyMissionReadyHooks();
    if(!missionReadyCompleted){
      state.phase='strategy';state.strategyStage='mission-ready';state.nextSide='player';state.activeNpoId=null;
      save();render();return;
    }
    finishTurningPointStart();
  }

  async function continueTurningPointStart(){
    if(!await applyMissionReadyHooks())return;
    finishTurningPointStart();
  }

  function finishTurningPointStart(){
    determineInitiative();
    processEventStage();
    if(!state.strategyData.eventPending)processReinforcementStage();
    const {grade,reinforcements}=state.strategyData;
    state.phase='strategy';state.strategyStage='summary';state.nextSide='player';state.activeNpoId=null;
    log(`Turning Point ${state.turningPoint} started. Grade ${grade}; ${state.strategyData.eventPending?'reinforcements await event resolution':`${reinforcements.length} reinforcement(s)`}.`);
    save();render();
  }

  function completeStrategyStage(stage,next){
    state.strategyPipeline.completed.push(stage);
    state.strategyPipeline.current=next;
  }

  function processReadyStep(){
    recycleUsedEvents();
    const dormant=state.threat===0;
    activeNpos().forEach(npo=>{npo.dormant=dormant;npo.ready=!dormant;});
    completeStrategyStage('ready','mission-ready-hooks');
  }

  async function applyMissionReadyHooks(){
    const outcomes=await executeMissionLifecycleHook('onStrategyPhaseReadyStep',{phase:'strategy-ready'});
    if(outcomes===null)return false;
    if(outcomes)state.strategyData.missionReadyHooks.push(...outcomes.filter(outcome=>outcome.status==='completed'));
    completeStrategyStage('mission-ready-hooks','initiative');
    return true;
  }

  function determineInitiative(){
    rollInitiative();
    completeStrategyStage('initiative','event');
  }

  function processEventStage(){
    const d=state.strategyData;
    d.events=[];
    d.eventIndex=0;
    if(state.turningPoint>1&&d.grade===3){
      const drawCount=d.suggestedInitiative==='npo'||state.threat===15?2:1;
      for(let i=0;i<drawCount;i++)drawEvent();
    }
    d.event=d.events[0]||null;
    if(d.event){beginCurrentEvent();return;}
    completeStrategyStage('event','reinforcement');
  }

  function eventRecord(card){
    const definition=eventDefinitions[card.definitionId];
    return {...card,type:'tomb-world-event',title:definition.title,text:definition.text,execution:{...definition.execution},duration:definition.duration,status:'drawn'};
  }

  function recycleUsedEvents(){
    const used=state.eventState.used||[];
    if(!used.length)return;
    state.eventState.available=[...new Set([...(state.eventState.available||[]),...used])];
    state.eventState.used=[];
  }

  function drawEvent(insertAt=null){
    if(!state.eventState.available.length)return null;
    const index=roll(state.eventState.available.length)-1;
    const instanceId=state.eventState.available.splice(index,1)[0];
    const card=eventDeck.find(candidate=>candidate.instanceId===instanceId);
    if(!card)return null;
    state.eventState.used.push(instanceId);
    const event=eventRecord(card);
    if(Number.isInteger(insertAt))state.strategyData.events.splice(insertAt,0,event);
    else state.strategyData.events.push(event);
    return event;
  }

  function currentEvent(){return state.strategyData?.events?.[state.strategyData.eventIndex||0]||null;}

  function beginCurrentEvent(){
    const d=state.strategyData,event=currentEvent();
    d.event=event;
    if(!event){
      d.eventPending=false;
      completeStrategyStage('event','reinforcement');
      processReinforcementStage();
      return;
    }
    const type=event.execution.type;
    if(type==='living-metal-flux'){
      const restored=[];
      activeNpos().filter(npo=>npo.wounds<npo.maxWounds).forEach(npo=>{
        const amount=rollD3()+2,before=npo.wounds;
        npo.wounds=Math.min(npo.maxWounds,npo.wounds+amount);
        restored.push(`${npoName(npo)} ${before}→${npo.wounds}`);
      });
      completeCurrentEvent(restored.length?restored.join('; '):'No wounded NPOs.');
      return;
    }
    if(type==='stirrings'){
      if(state.threat===15){redrawCurrentEvent('Threat was already 15.');return;}
      setThreat(1,event.title);
      completeCurrentEvent(`Threat increased to ${state.threat}.`);
      return;
    }
    if(type==='activate'){
      state.eventState.active.push({...event,startedTurningPoint:state.turningPoint,expiresAfterTurningPoint:state.turningPoint,status:'active'});
      completeCurrentEvent('Effect active until the end of this Turning Point.');
      return;
    }
    if(type==='chittering-drone'){
      const wounded=activeNpos().filter(npo=>npo.type==='Canoptek Scarab Swarm'&&npo.wounds<npo.maxWounds);
      if(wounded.length===1){wounded[0].wounds=wounded[0].maxWounds;completeCurrentEvent(`${npoName(wounded[0])} regained all lost wounds.`);return;}
      if(wounded.length>1){event.eligibleNpoIds=wounded.map(npo=>npo.id);d.eventPending=true;return;}
      if(activeNpos().length>=MAX_NPOS){redrawCurrentEvent('No Scarab Swarm could be set up.');return;}
    }
    if(type==='maze-reforms'){
      event.openHatchwayLimit=rollD3();
      event.text=`Close one breach and up to ${event.openHatchwayLimit} open hatchway${event.openHatchwayLimit===1?'':'s'}. If this cannot be resolved, draw another event card.`;
    }
    if(type==='awakened-warrior'&&activeNpos().length>=MAX_NPOS){redrawCurrentEvent('No Necron Warrior could be set up.');return;}
    d.eventPending=true;
  }

  function completeCurrentEvent(result){
    const d=state.strategyData,event=currentEvent();
    if(!event)return;
    event.status='resolved';event.result=result;
    d.eventAction={eventId:event.instanceId,result};
    d.eventIndex=(d.eventIndex||0)+1;
    d.eventPending=false;
    log(`${event.title}: ${result}`);
    beginCurrentEvent();
  }

  function redrawCurrentEvent(reason){
    const event=currentEvent();
    event.status='redrawn';event.result=reason;
    drawEvent(state.strategyData.eventIndex+1);
    state.strategyData.eventIndex++;
    log(`${event.title}: ${reason} Another event card was drawn.`);
    beginCurrentEvent();
  }

  function processReinforcementStage(){
    if(state.strategyPipeline.completed.includes('reinforcement'))return;
    const d=state.strategyData,reinforcements=[];
    let blocked=0;
    state.reinforcementState={turningPoint:state.turningPoint,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0};
    d.grade=threatGrade();
    if(reinforcementTriggered(d)){
      const requested=d.grade,slots=Math.max(0,MAX_NPOS-activeNpos().length),actual=Math.min(requested,slots);
      blocked=requested-actual;
      for(let i=0;i<requested;i++){
        const rr=randomReinforcement(),type=rr.type;
        let n=reserveNpos().find(candidate=>candidate.type===type&&!state.reinforcementState.operativeIds.includes(candidate.id)&&!state.reinforcementState.blockedOperativeIds.includes(candidate.id));
        if(i>=actual){
          if(!n){
            n=createNpo(type,`${type} R${state.turningPoint}-${i+1}`,{weaponId:rr.weaponId,deployed:false});
            state.roster.push(n);state.newIds.push(n.id);
            if(state.startingNpoGeneration&&!state.startingNpoGeneration.reserveNpoIds.includes(n.id))state.startingNpoGeneration.reserveNpoIds.push(n.id);
          }
          state.reinforcementState.blockedOperativeIds.push(n.id);
          continue;
        }
        if(n){
          n.reinforcement={turningPoint:state.turningPoint,hatchway:'',placementConfirmed:false};
          n.battlefieldState='deployed';n.deployed=true;n.dormant=state.threat===0;n.ready=!n.dormant;
        }else{
          n=createNpo(type,`${type} R${state.turningPoint}-${i+1}`,{weaponId:rr.weaponId,deployed:true,reinforcement:{turningPoint:state.turningPoint,hatchway:'',placementConfirmed:false}});
          state.roster.push(n);state.newIds.push(n.id);
        }
        if(state.startingNpoGeneration)state.startingNpoGeneration.reserveNpoIds=(state.startingNpoGeneration.reserveNpoIds||[]).filter(id=>id!==n.id);
        reinforcements.push(rr);
        state.reinforcementState.operativeIds.push(n.id);
      }
    }
    d.reinforcements=reinforcements;
    d.actualReinforcements=reinforcements.length;
    d.blocked=blocked;
    state.reinforcementState.blocked=blocked;
    state.reinforcementState.status=reinforcements.length?'placement':blocked?'blocked':'complete';
    completeStrategyStage('reinforcement','complete');
    state.strategyPipeline.current='complete';
  }

  function reinforcementTriggered(data=state.strategyData||{}){
    return state.strategyPipeline?.current==='reinforcement'&&state.turningPoint>1&&Number(data.grade)>0;
  }

  function confirmReinforcementPlacement(id,confirmed){
    const npo=state.roster.find(item=>item.id===id&&state.reinforcementState.operativeIds.includes(item.id));
    if(!npo?.reinforcement)return;
    const placementConfirmed=Boolean(confirmed&&npo.reinforcement.hatchway);
    npo.reinforcement.placementConfirmed=placementConfirmed;
    npo.deployed=true;
    npo.battlefieldState='deployed';
    const complete=state.reinforcementState.operativeIds.every(operativeId=>state.roster.find(item=>item.id===operativeId)?.reinforcement?.placementConfirmed);
    state.reinforcementState.status=complete?'complete':'placement';
    save();render();
  }

  function recordReinforcementHatchway(id,hatchway){
    const npo=state.roster.find(item=>item.id===id&&state.reinforcementState.operativeIds.includes(item.id));
    if(!npo?.reinforcement)return;
    const recordedHatchway=hatchway.trim();
    if(recordedHatchway===npo.reinforcement.hatchway)return;
    npo.reinforcement.hatchway=recordedHatchway;
    npo.reinforcement.placementConfirmed=false;
    npo.deployed=true;
    npo.battlefieldState='deployed';
    state.reinforcementState.status='placement';
    save();
    setTimeout(render,0);
  }

  function rollInitiative(){
    if(!state.strategyData)state.strategyData={};
    if(state.turningPoint===1||state.threat===0){
      state.strategyData.playerRoll=null;
      state.strategyData.npoRoll=null;
      state.strategyData.suggestedInitiative='player';
      state.strategyData.initiativeMode='automatic';
      state.strategyData.initiativeReason=state.turningPoint===1?'Turning Point 1':'Threat was 0 when initiative was determined';
      return;
    }
    const p=roll(),n=roll();
    state.strategyData.playerRoll=p;
    state.strategyData.npoRoll=n;
    state.strategyData.suggestedInitiative=n>p?'npo':'player';
    state.strategyData.initiativeMode='rolled';
    state.strategyData.initiativeReason=null;
  }

  function beginFirefight(side){
    state.initiative=side;
    state.phase='firefight';
    state.strategyStage=null;
    setNextActivation(side);
    log(`${side==='npo'?'NPOs':'Player'} begin the Firefight Phase with initiative.`);
    save();
    render();
  }

  function resolveStrategyEvent(){
    const event=currentEvent();
    if(state.phase!=='strategy'||state.strategyStage!=='summary'||!event||!state.strategyData.eventPending)return;
    let result='Tabletop effect confirmed.';
    if(event.execution.type==='chittering-drone'&&event.eligibleNpoIds?.length){
      const operativeId=$('#eventNpoSelect')?.value;
      const n=activeNpos().find(item=>item.id===operativeId&&event.eligibleNpoIds.includes(item.id)&&item.wounds<item.maxWounds);
      if(!n)return;
      n.wounds=n.maxWounds;
      result=`${npoName(n)} regained all lost wounds.`;
    }else if(event.execution.type==='chittering-drone'||event.execution.type==='awakened-warrior'){
      const type=event.execution.type==='chittering-drone'?'Canoptek Scarab Swarm':'Necron Warrior';
      if(activeNpos().length>=MAX_NPOS){redrawCurrentEvent(`${type} could not be set up.`);save();render();return;}
      const n=createNpo(type,`${type} E${state.turningPoint}`,{order:'Conceal'});
      n.ready=true;n.dormant=false;
      state.roster.push(n);state.newIds.push(n.id);
      result=`${npoName(n)} was set up Ready with a Conceal order; printed placement confirmed.`;
    }
    if(event.execution.type==='maze-reforms')result='Breach and hatchway changes completed on the tabletop.';
    completeCurrentEvent(result);
    save();render();
  }

  function randomReinforcement(){return rollNpo();}
  function nextNpo(){return readyNpos().find(n=>n.id===state.activeNpoId)||null;}

  function showNpoSelection(){
    const candidates=readyNpos();
    if(candidates.length===1){state.activeNpoId=candidates[0].id;notifyMissionActivationStarted('npo',candidates[0].id);runNpoPrompt(candidates[0],0,{},[]);return;}
    const options=candidates.map(n=>`<option value="${escapeHtml(n.id)}">${escapeHtml(npoName(n))}</option>`).join('');
    showModal('Select NPO to Activate',`<p>Use the Threat Principle in order. Select an NPO that:</p><ol><li>has an ability, or is a threat, to Shoot or Fight a Player operative;</li><li>is not in cover;</li><li>is closest to a Player operative.</li></ol><p class="muted">If more than one NPO is still tied, determine one at random on the tabletop.</p><div class="field"><label for="officialNpoSelection">Next ready NPO</label><select id="officialNpoSelection"><option value="">Select matching NPO</option>${options}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Exit Guide</button><button class="btn primary" id="confirmNpoSelection" disabled>Continue</button></div>`);
    $('#officialNpoSelection').onchange=()=>{$('#confirmNpoSelection').disabled=!$('#officialNpoSelection').value;};
    $('#confirmNpoSelection').onclick=()=>{const n=candidates.find(item=>item.id===$('#officialNpoSelection').value);if(!n)return;state.activeNpoId=n.id;notifyMissionActivationStarted('npo',n.id);save();runNpoPrompt(n,0,{},[]);};
  }

  function remainingPlayerOperatives(){
    const used=new Set(state.playerActivatedIds||[]);
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!used.has(id)&&!casualties.has(id));
  }

  
  const PLAYER_ACTION_COSTS={
    move:1,
    dash:1,
    charge:1,
    fallBack:2,
    shoot:1,
    melee:1,
    damage:1,
    hatch:1,
    breach:1,
    objective:1,
    pass:0
  };

  function playerActionCost(stage){
    return Object.entries(PLAYER_ACTION_COSTS).reduce((total,[key,cost])=>total+(stage[key]?cost:0),0);
  }

  function playerActionConflicts(stage){
    const conflicts=[];
    if(stage.charge && (stage.move || stage.dash || stage.fallBack)){
      conflicts.push('Charge cannot be combined with Move, Dash, or Fall Back.');
    }
    if(stage.fallBack && (stage.move || stage.charge)){
      conflicts.push('Fall Back cannot be combined with Move or Charge.');
    }
    if(stage.pass && playerActionCost({...stage,pass:false})>0){
      conflicts.push('Pass cannot be combined with another action.');
    }
    return conflicts;
  }

function showPlayerActivation(stage={}){
    if(!Object.keys(stage).length&&state.combatState?.side==='player')stage={...state.combatState.stage};
    const remaining=remainingPlayerOperatives();
    if(!remaining.length){
      state.playerReady=0;
      setNextActivation('npo');
      save();
      render();
      return;
    }

    const selectOperative=(current,id)=>{
      const selectedOperative=playerDefinition(id);
      return {...current,playerOperativeId:id||'',apl:Number(selectedOperative?.apl||current.apl||3)};
    };
    const stagedId=String(stage.playerOperativeId||'');
    if(stagedId && !remaining.includes(stagedId)){
      showPlayerActivation(selectOperative(stage,''));
      return;
    }
    if(remaining.length===1 && stagedId!==remaining[0]){
      showPlayerActivation(selectOperative(stage,remaining[0]));
      return;
    }

    const checked=key=>stage[key]?'checked':'';
    const selectedId=stagedId;
    if(selectedId)notifyMissionActivationStarted('player',selectedId);
    const selectedOperative=playerDefinition(selectedId);
    const moveDistance=Number(selectedOperative?.move||6);
    const chargeDistance=moveDistance+2;
    const dashDistance=3;
    const fallBackDistance=moveDistance;
    const shootPending=stage.pendingShoot||null;
    const meleePending=stage.pendingMelee||null;

    showModal('Activate an Operative',`
      <p>Choose the Player operative being activated. That operative cannot activate again during this Turning Point after the activation is confirmed.</p>
      <div class="field">
        <label>Player operative</label>
        ${remaining.length===1
          ? `<div class="readonly-select">${escapeHtml(playerName(selectedId))}</div>`
          : `<select id="playerOperativeSelect">
          <option value="">Select a Player operative...</option>
          ${remaining.map(id=>`<option value="${id}" ${selectedId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('')}
        </select>`}
      </div>
      <fieldset id="playerActivationControls" class="${selectedId?'':'inactive'}" aria-disabled="${selectedId?'false':'true'}">
        <div class="activation-apl-bar ap-usage-only">
          <div class="ap-usage" id="apUsage"><small>AP used</small><strong>0 / ${Number(stage.apl||playerDefinition(selectedId)?.apl||3)}</strong></div>
        </div>
        <div id="apWarning" class="warning-text hidden"></div>
        <p class="muted">Select everything this operative will do. Shooting and Melee attacks are resolved only after you press Complete Activation.</p>
        <div class="activation-groups">
          <section class="activation-group">
            <div class="activation-group-title"><span>↔</span><div><strong>Movement</strong><small>Position and control actions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaMove" ${checked('move')}><span>Move <small>▲ ${moveDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaDash" ${checked('dash')}><span>Dash <small>▲ ${dashDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaCharge" ${checked('charge')}><span>Charge <small>▲ ${chargeDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaFallBack" ${checked('fallBack')}><span>Fall Back <small>▲ ${fallBackDistance}&quot; · 2 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group">
            <div class="activation-group-title"><span>⚔</span><div><strong>Combat</strong><small>Resolved after Complete Activation</small></div></div>
            <div class="combat-action-card">
              <label><input type="checkbox" id="eaShoot" ${checked('shoot')}><span><strong>Shoot</strong><small>1 AP · One Shooting action for this operative</small></span></label>
              ${shootPending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(shootPending.targetName)} · ${shootPending.damage} damage</div>`:''}
            </div>
            <div class="combat-action-card">
              <label><input type="checkbox" id="eaMelee" ${checked('melee')||checked('fight')}><span><strong>Melee</strong><small>1 AP · One Melee action for this operative</small></span></label>
              ${meleePending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(meleePending.targetName)} · ${meleePending.damage} damage</div>`:''}
            </div>
            <div class="toggle-list player-action-list compact-actions">
              <label><input type="checkbox" id="eaDamage" ${checked('damage')}><span>Damaged an NPO with another action <small>1 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group">
            <div class="activation-group-title"><span>▣</span><div><strong>Battlefield</strong><small>Terrain and mission interactions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaHatch" ${checked('hatch')}><span>Operate Hatch <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaBreach" ${checked('breach')}><span>Breach <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaObjective" ${checked('objective')}><span>Mission or objective action <small>1 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group pass-group">
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaPass" ${checked('pass')}>Pass / no action recorded</label>
            </div>
          </section>
        </div>
        <div class="wizard-actions"><button class="btn ghost" id="cancelPlayerActivation">Cancel</button><button class="btn primary" id="confirmPlayer">Complete Activation</button></div>
      </fieldset>`);

    const operativeSelect=$('#playerOperativeSelect');
    const controls=$('#playerActivationControls');

    // iOS Safari can retain focus on the button that opened the dialog,
    // which occasionally prevents the native select from opening on first tap.
    requestAnimationFrame(()=>{
      modal.scrollTop=0;
      modalBody.scrollTop=0;
      if(document.activeElement!==modal){
        try{modal.focus({preventScroll:true});}catch{modal.focus();}
      }
      if(operativeSelect){
        operativeSelect.style.pointerEvents='none';
        requestAnimationFrame(()=>{operativeSelect.style.pointerEvents='';});
      }
    });
    operativeSelect?.addEventListener('change',()=>showPlayerActivation(selectOperative(stage,operativeSelect.value)));

    const actionIds=['eaMove','eaDash','eaCharge','eaFallBack','eaShoot','eaMelee','eaDamage','eaHatch','eaBreach','eaObjective'];
    const clearPass=()=>{if($('#eaPass'))$('#eaPass').checked=false;};

    function updatePlayerActionAvailability(){
      const current=readPlayerActivationStage(stage);
      const apl=Number(playerDefinition(current.playerOperativeId)?.apl||current.apl||3);
      current.apl=apl;
      const used=playerActionCost(current);
      const conflicts=playerActionConflicts(current);
      const usage=$('#apUsage');
      if(usage)usage.innerHTML=`<small>AP used</small><strong>${used} / ${apl}</strong>`;
      const warning=$('#apWarning');
      const messages=[...conflicts];
      if(used>apl)messages.push(`This activation uses ${used} AP, but the operative only has ${apl} APL.`);
      if(warning){
        warning.textContent=messages.join(' ');
        warning.classList.toggle('hidden',messages.length===0);
      }
      $('#confirmPlayer').disabled=used>apl || conflicts.length>0;

      // Disable unchecked actions that would exceed APL if added.
      const map={
        eaMove:'move',eaDash:'dash',eaCharge:'charge',eaFallBack:'fallBack',
        eaShoot:'shoot',eaMelee:'melee',eaDamage:'damage',eaHatch:'hatch',
        eaBreach:'breach',eaObjective:'objective'
      };
      Object.entries(map).forEach(([id,key])=>{
        const box=$(`#${id}`);
        if(!box)return;
        if(box.checked){box.disabled=false;return;}
        const hypothetical={...current,[key]:true};
        box.disabled=playerActionCost(hypothetical)>apl || playerActionConflicts(hypothetical).length>0;
      });
    }

    $('#eaPass')?.addEventListener('change',e=>{
      if(e.target.checked)actionIds.forEach(id=>{const box=$(`#${id}`);if(box)box.checked=false;});
      updatePlayerActionAvailability();
    });
    actionIds.forEach(id=>$(`#${id}`)?.addEventListener('change',e=>{
      if(e.target.checked)clearPass();
      updatePlayerActionAvailability();
    }));
    updatePlayerActionAvailability();

    $('#cancelPlayerActivation').onclick=()=>{closeModal();render();};
    $('#confirmPlayer').onclick=()=>{
      const finalStage=readPlayerActivationStage(stage);
      const used=playerActionCost(finalStage);
      const conflicts=playerActionConflicts(finalStage);
      if(used>finalStage.apl || conflicts.length){
        showToast(conflicts[0] || `This operative is limited to ${finalStage.apl} AP.`);
        return;
      }
      if(!finalStage.playerOperativeId){
        showToast('Select a Player operative first.');
        return;
      }
      if(!playerActivationHasAction(finalStage)){
        showModal('No actions selected',`<p>Mark ${escapeHtml(playerName(finalStage.playerOperativeId))} as activated without recording an action?</p><div class="wizard-actions"><button class="btn ghost" id="returnPlayerActivation">Go Back</button><button class="btn primary" id="confirmEmptyPlayerActivation">Continue</button></div>`);
        $('#returnPlayerActivation').onclick=()=>showPlayerActivation(finalStage);
        $('#confirmEmptyPlayerActivation').onclick=()=>resolvePendingPlayerAttacks(finalStage);
        return;
      }
      resolvePendingPlayerAttacks(finalStage);
    };
  }

  function readPlayerActivationStage(previous={}){
    const shoot=Boolean($('#eaShoot')?.checked);
    const melee=Boolean($('#eaMelee')?.checked);
    return {
      playerOperativeId:String($('#playerOperativeSelect')?.value||previous.playerOperativeId||''),
      apl:Number(playerDefinition(previous.playerOperativeId)?.apl||previous.apl||3),
      move:Boolean($('#eaMove')?.checked),
      dash:Boolean($('#eaDash')?.checked),
      charge:Boolean($('#eaCharge')?.checked),
      fallBack:Boolean($('#eaFallBack')?.checked),
      shoot,
      melee,
      damage:Boolean($('#eaDamage')?.checked),
      hatch:Boolean($('#eaHatch')?.checked),
      breach:Boolean($('#eaBreach')?.checked),
      objective:Boolean($('#eaObjective')?.checked),
      pass:Boolean($('#eaPass')?.checked),
      pendingShoot:shoot?previous.pendingShoot||null:null,
      pendingMelee:melee?previous.pendingMelee||null:null,
      shootCombatDraft:shoot?previous.shootCombatDraft||null:null,
      meleeCombatDraft:melee?previous.meleeCombatDraft||null:null
    };
  }

  function playerActivationHasAction(stage){
    return Boolean(stage.move || stage.dash || stage.charge || stage.fallBack || stage.shoot || stage.melee ||
      stage.damage || stage.hatch || stage.breach || stage.objective || stage.pass);
  }

  function playerActivationSummary(stage){
    const actions=[];
    if(stage.move)actions.push('Move');
    if(stage.dash)actions.push('Dash');
    if(stage.charge)actions.push('Charge');
    if(stage.fallBack)actions.push('Fall Back');
    if(stage.shoot)actions.push('Shooting attack resolved');
    if(stage.melee)actions.push('Melee attack resolved');
    if(stage.damage)actions.push('Damaging action');
    if(stage.hatch)actions.push('Operate Hatch');
    if(stage.breach)actions.push('Breach');
    if(stage.objective)actions.push('Mission action');
    if(stage.pass)actions.push('Pass / no action recorded');
    return actions.length?actions.join(', '):'No actions recorded';
  }

  function newlyEliminated(attack){
    return attack&&Number(attack.before)>0&&Number(attack.after)<=0;
  }

  function renderEliminationSummary(attack){
    if(!newlyEliminated(attack))return '';
    const side=attack.side==='player'?'PLAYER':'NPO';
    return `<section class="elimination-banner" aria-label="${side} eliminated">
      <span class="elimination-icon" aria-hidden="true">☠</span>
      <div><small>${side} ELIMINATED</small><strong>${escapeHtml(attack.targetName)}</strong></div>
    </section>`;
  }

  function renderAttackSummary(attack){
    const lethal=newlyEliminated(attack);
    return `<section class="attack-confirmation-card ${lethal?'eliminated':''}">
      <div class="attack-confirmation-heading">
        <small>${attack.attackType==='shoot'?'SHOOTING':'MELEE'}</small>
        ${lethal?'<span class="eliminated-badge">☠ ELIMINATED</span>':''}
      </div>
      <strong class="attack-confirmation-target">${escapeHtml(attack.targetName)}</strong>
      <div class="attack-confirmation-stats">
        <div><small>Damage</small><strong>${attack.damage}</strong></div>
        <div><small>Wounds</small><strong>${attack.before} → <span class="${lethal?'zero-wounds':''}">${attack.after}</span></strong></div>
      </div>
    </section>`;
  }

  function renderCombatResolution(combat,{pending=false,animate=true,showParticipants=true}={}){
    const elimination=renderEliminationSummary({
      ...combat,side:combat.defenderSide,targetName:combat.defenderName
    });
    return `<section class="combat-resolution" aria-label="Combat resolution">
      ${showParticipants?`<div class="damage-summary combat-participants">
        <div><small>Attacker</small><strong>${escapeHtml(combat.attackerName)}</strong></div>
        <div><small>Defender</small><strong>${escapeHtml(combat.defenderName)}</strong></div>
        <div><small>Attack type</small><strong>${combat.attackType==='shoot'?'Shooting':'Melee'}</strong></div>
        ${combat.recordedOutcome?'':`<div><small>Retained saves</small><strong>${combat.retainedSaves??(combat.coverRetained?1:0)}</strong></div>`}
      </div>`:''}
      ${combat.recordedOutcome?'<div class="combat-stage"><small>TABLETOP RESOLUTION</small><p>Physical dice and retained successes resolved by the player.</p></div>':`<div class="combat-stage"><small>ATTACK DICE</small><div class="dice-row ${animate?'animated-roll':'settled'}" data-combat-attack-dice>${combat.attackDice.map(d=>animate?rollingDieHtml():dieHtml(d)).join('')}</div></div><div class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row ${animate?'animated-roll':'settled'}" data-combat-save-dice>${combat.saveDice.length?combat.saveDice.map(d=>animate?rollingDieHtml():dieHtml(d)).join(''):'<span class="muted">No defense dice rolled</span>'}</div>${combat.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div>`}
      ${elimination}
      ${combatAbilityReminder(combat)}
      <div class="damage-summary">
        <div><small>${combat.recordedOutcome?'Retained normal successes':'Unsaved normal hits'}</small><strong>${combat.normalRemaining}</strong></div>
        <div><small>${combat.recordedOutcome?'Retained critical successes':'Unsaved critical hits'}</small><strong>${combat.critRemaining}</strong></div>
        <div><small>${pending?'Pending damage':'Total damage'}</small><strong>${combat.damage}</strong></div>
        <div><small>Wounds</small><strong>${combat.before} → ${combat.after}</strong></div>
      </div>
    </section>`;
  }

  function combatAttackLabel(profile){
    return `${profile.dice} dice · ${profile.hit}+`;
  }

  function showSharedCombatResolutionScreen({title,attackerName,defenderName,attackType,weaponName,attackLabel='',defenseLabel,cancelId,continueId,extraHtml='',detailsHtml=''}){
    showModal(title,`
      <section class="dedicated-combat-screen" aria-label="Combat resolution screen">
        <div class="damage-summary combat-participants compact-combat-profile${attackLabel?' has-attack-profile':''}">
          <div><small>Attacker</small><strong>${escapeHtml(attackerName)}</strong></div>
          <div><small>Defender</small><strong>${escapeHtml(defenderName)}</strong></div>
          <div><small>Attack type</small><strong>${attackType==='shoot'?'Shooting':'Melee'}</strong></div>
          <div><small>Weapon</small><strong>${escapeHtml(weaponName)}</strong></div>
          ${attackLabel?`<div><small>Attack</small><strong>${escapeHtml(attackLabel)}</strong></div>`:''}
          <div><small>Defense</small><strong>${escapeHtml(defenseLabel)}</strong></div>
        </div>
        ${extraHtml}
        <div id="automaticCombat" class="combat-results combat-dice-area" aria-live="polite"></div>
        <div id="combatResults" class="combat-results" aria-live="polite"></div>
        <div id="combatDetails">${detailsHtml}</div>
        <div class="wizard-actions combat-resolution-footer"><button class="btn ghost" id="${cancelId}">Cancel</button><button class="btn primary" id="${continueId}" disabled>Continue</button></div>
      </section>`);
    modal.classList.add('combat-resolution-modal');
    window.scrollTo({top:0,left:0,behavior:'auto'});
    modal.scrollTop=0;
    modalBody.scrollTop=0;
    return {dice:$('#automaticCombat'),results:$('#combatResults'),continueButton:$(`#${continueId}`)};
  }

  function displaySharedCombatResult(combat,{pending=false,animate=false,waiting=false,message='',onContinue,extraHtml=''}={}){
    const results=$('#combatResults');
    const dice=$('#automaticCombat');
    const button=$('.combat-resolution-footer .btn.primary');
    if(dice)dice.replaceChildren();
    results.innerHTML=`${renderCombatResolution(combat,{pending,animate,showParticipants:false})}${extraHtml}${message?`<p class="muted">${escapeHtml(message)}</p>`:''}`;
    let visualComplete=!animate&&!waiting;
    button.textContent='Continue';
    button.disabled=!visualComplete;
    button.onclick=()=>{if(visualComplete&&onContinue)onContinue();};
    if(animate)settleCombatDice(combat,()=>{
      visualComplete=!waiting;
      if(button.isConnected)button.disabled=waiting;
    },results);
  }

  function settleCombatDice(combat,onSettled=()=>{},root=document){
    return settleAnimatedDice([
      {row:$('[data-combat-attack-dice]',root),dice:combat.attackDice},
      {row:$('[data-combat-save-dice]',root),dice:combat.saveDice}
    ],onSettled);
  }

  function settleAnimatedDice(rows,onSettled=()=>{}){
    const timer=setTimeout(()=>{
      rows.forEach(({row,dice})=>{
        if(!row)return;
        if(dice.length)row.innerHTML=dice.map(dieHtml).join('');
        row.classList.replace('animated-roll','settled');
      });
      onSettled();
    },700);
    return ()=>clearTimeout(timer);
  }

  function projectedNpoWounds(npoId,stage){
    let wounds=state.roster.find(n=>n.id===npoId)?.wounds||0;
    for(const pending of [stage.pendingShoot,stage.pendingMelee]){
      if(pending?.targetId===npoId)wounds=pending.after;
    }
    return wounds;
  }

  function resolvePendingPlayerAttacks(stage){
    if(stage.shoot&&!stage.pendingShoot){
      showPendingPlayerAttackWizard(
        stage,
        'shoot',
        result=>resolvePendingPlayerAttacks({...stage,pendingShoot:result}),
        ()=>showPlayerActivation(stage)
      );
      return;
    }
    if(stage.melee&&!stage.pendingMelee){
      const remainingTargets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
      if(!remainingTargets.length){
        resolvePendingPlayerAttacks({...stage,melee:false});
        return;
      }
      showPendingPlayerAttackWizard(
        stage,
        'melee',
        result=>resolvePendingPlayerAttacks({...stage,pendingMelee:result}),
        ()=>showPlayerActivation(stage)
      );
      return;
    }
    state.combatState=null;
    if(applyPendingPlayerDamage(stage))return;
    completePlayerActivation(stage);
  }

  function applyPendingPlayerDamage(stage){
    for(const pending of [stage.pendingShoot,stage.pendingMelee]){
      if(!pending||pending.committed)continue;
      const n=state.roster.find(x=>x.id===pending.targetId);
      if(!n)continue;
      const before=n.wounds;
      n.wounds=Math.max(0,pending.after);
      pending.committed=true;
      if(n.wounds===0)n.ready=false;
      if(n.wounds===0){n.deployed=false;n.battlefieldState='out-of-action';}
      log(`${playerName(stage.playerOperativeId)} ${pending.attackType==='shoot'?'shot':'made a Melee attack against'} ${npoName(n)} for ${pending.damage} damage (${before} → ${n.wounds} wounds).`);
      const aggressiveDamage=aggressiveDefenseDamageValue(pending);
      if(aggressiveDamage>0){
        const playerBefore=playerCurrentWounds(stage.playerOperativeId);
        const playerAfter=Math.max(0,playerBefore-aggressiveDamage);
        state.playerWounds[stage.playerOperativeId]=playerAfter;
        if(playerAfter<=0&&!state.playerCasualtyIds.includes(stage.playerOperativeId))state.playerCasualtyIds.push(stage.playerOperativeId);
        log(`Aggressive Defense Construct dealt ${aggressiveDamage} damage to ${playerName(stage.playerOperativeId)} (${playerBefore} → ${playerAfter} wounds).`);
      }
      if(checkGameEnd())return true;
    }
    return false;
  }

  async function completePlayerActivation(stage={}){
    state.combatState=null;
    let inc=0;
    if(stage.shoot)inc++;
    if(stage.melee)inc++;
    if(stage.damage)inc++;
    if(stage.hatch&&state.missionId!=='scout-sub-crypt'){
      const r=roll();
      if(r>=4)inc++;
    }
    if(stage.breach){
      inc++;
      const r=roll();
      if(r>=4)inc++;
    }
    if(inc)setThreat(inc,'Player activation');
    const operativeId=String(stage.playerOperativeId);
    const activationId=missionActivationId('player',operativeId);
    if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
    state.playerReady=playerOperativesRemaining();
    state.playerActivated=state.playerActivatedIds.length;
    state.activationNumber++;
    const summary=playerActivationSummary(stage);
    state.activationHistory.unshift({side:'player',label:playerName(operativeId),summary});
    advanceAfterActivation('player');
    log(`${playerName(operativeId)} completed activation: ${summary}.`);
    closeModal();
    save();
    render();
    await executeMissionLifecycleHook('onPlayerActivationCompleted',{activationId,operativeId});
  }

  function npoName(n){
    if(!n)return 'NPO';
    const sameType=state.roster.filter(x=>x.type===n.type);
    if(sameType.length<=1)return n.type;
    const index=sameType.findIndex(x=>x.id===n.id);
    return `${n.type} ${index+1}`;
  }

  function sortOperativesGlobally(){
    const compareText=(a,b)=>String(a||'').localeCompare(String(b||''),undefined,{sensitivity:'base',numeric:true});

    // Sort the complete Player team definition so setup, selectors, and roster views agree.
    if(Array.isArray(playerTeamData?.operatives)){
      playerTeamData.operatives.sort((a,b)=>compareText(a.name,b.name)||compareText(a.id,b.id));
    }

    // Sort selected Player operatives by their roster names.
    if(Array.isArray(state.playerRoster)){
      state.playerRoster.sort((a,b)=>compareText(playerName(a),playerName(b))||compareText(a,b));
    }

    // Sort the authoritative NPO roster by type. The centralized npoName()
    // function then assigns duplicate numbers consistently everywhere.
    if(Array.isArray(state.roster)){
      state.roster.sort((a,b)=>compareText(a.type,b.type)||compareText(a.id,b.id));
    }
  }

  function playerAttackWeapons(operativeId,attackType){
    const operative=playerDefinition(operativeId);
    const wantedType=attackType==='shoot'?'ranged':'melee';
    return (operative?.weapons||[]).filter(w=>w.type===wantedType);
  }

  function parseWeaponDamage(damage){
    const match=String(damage||'0/0').match(/(\d+)\s*\/\s*(\d+)/);
    return {normal:Number(match?.[1]||0),crit:Number(match?.[2]||0)};
  }

  function weaponPiercingValue(weapon){
    for(const rule of weapon?.rules||[]){
      const match=String(rule).match(/(?:Piercing|AP)\s*(\d+)/i);
      if(match)return Number(match[1]);
    }
    return 0;
  }

  function playerWeaponProfile(weapon){
    const damage=parseWeaponDamage(weapon?.damage);
    const lethalRule=(weapon?.rules||[]).map(String).map(rule=>rule.match(/Lethal\s*(\d)\+/i)).find(Boolean);
    return {
      dice:Number(weapon?.attacks||4),
      hit:Number(weapon?.hit||3),
      critThreshold:Number(lethalRule?.[1]||6),
      normal:damage.normal,
      crit:damage.crit,
      ap:weaponPiercingValue(weapon)
    };
  }

  const combatAbilityHandlers = {
    'dimensional-banishment':({criticalSuccesses,damage,targetIncapacitated})=>
      !targetIncapacitated&&(damage>0||criticalSuccesses>0),
    'aggressive-defence-construct':({targetIncapacitated,attackerWithinTwo})=>
      targetIncapacitated&&attackerWithinTwo
  };

  function weaponRulesHtml(profile){
    const rules=(profile?.rules||[]).map(rule=>`<li>${escapeHtml(rule)}</li>`).join('');
    return rules?`<section class="weapon-rules"><strong>Weapon rules</strong><ul>${rules}</ul></section>`:'';
  }

  function npoCombatGuidanceHtml(npo){
    const definition=npoDefinition(npo?.type);
    const weaponSentinel=(definition?.abilities||[]).find(ability=>ability.id==='weapon-sentinel');
    const items=[definition?.behavior?.weaponGuidance,weaponSentinel&&`${weaponSentinel.name}: ${weaponSentinel.text}`].filter(Boolean);
    return items.length?`<div class="summary-box"><strong>NPO combat guidance</strong><ul>${items.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ul></div>`:'';
  }

  function recordedCombat({attackerName,defenderName,attackType,attackerSide,defenderSide,profile,before,normalSuccesses=0,criticalSuccesses=0,damage=0}){
    const appliedDamage=Math.max(0,Math.round(Number(damage)||0));
    return {attackerName,defenderName,attackType,attackerSide,defenderSide,profile,
      normalRemaining:Math.max(0,Math.round(Number(normalSuccesses)||0)),
      critRemaining:Math.max(0,Math.round(Number(criticalSuccesses)||0)),damage:appliedDamage,
      before,after:Math.max(0,before-appliedDamage),attackDice:[],saveDice:[],retainedSaves:0,recordedOutcome:true};
  }

  function applyDimensionalBanishment(combat,rollTotal){
    const triggered=combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:combat.after<=0});
    const total=Math.max(0,Math.round(Number(rollTotal)||0));
    return {...combat,dimensionalBanishmentRoll:total,dimensionalBanishmentTriggered:triggered,
      after:triggered&&total>combat.after?0:combat.after};
  }

  function dimensionalBanishmentRequired(combat){
    return combat.profile?.weaponId==='transdimensional-isolator'
      &&!Number.isInteger(combat.dimensionalBanishmentRoll)
      &&combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:combat.after<=0});
  }

  function rolledCombatDice(count,threshold,critThreshold=6){
    return Array.from({length:Math.max(0,count)},()=>{
      const value=roll();
      return {value,kind:value>=critThreshold?'crit':value>=threshold?'hit':'miss',retained:false};
    });
  }

  function retainSuccessfulDice(dice=[]){
    return dice.map(die=>({...die,retained:die.kind==='hit'||die.kind==='crit'}));
  }

  function runAutomaticCombatRolls({container,profile,defenseSave,onComplete}){
    let timer=null;
    const attackDice=retainSuccessfulDice(rolledCombatDice(profile.dice,profile.hit,profile.critThreshold));
    container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row animated-roll">${attackDice.map(()=>rollingDieHtml()).join('')}</div></section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row"><span class="muted">Rolling after the attack…</span></div></section>`;
    timer=setTimeout(()=>{
      if(!container.isConnected)return;
      const defenseDice=retainSuccessfulDice(rolledCombatDice(Math.max(0,3-profile.ap),Number(defenseSave)||3));
      container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row settled" data-combat-attack-dice>${attackDice.map(dieHtml).join('')}</div></section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row animated-roll" data-combat-save-dice>${defenseDice.length?defenseDice.map(()=>rollingDieHtml()).join(''):'<span class="muted">No defense dice rolled</span>'}</div></section>`;
      timer=settleCombatDice({attackDice,saveDice:defenseDice},()=>{
        timer=null;
        if(container.isConnected)onComplete(attackDice,defenseDice);
      },container);
    },700);
    return ()=>{
      if(typeof timer==='function')timer();
      else if(timer)clearTimeout(timer);
      timer=null;
    };
  }

  function retainedDiceTotals(dice=[]){
    return dice.reduce((totals,die)=>{
      if(die.retained&&die.kind==='crit')totals.critical++;
      if(die.retained&&die.kind==='hit')totals.normal++;
      return totals;
    },{normal:0,critical:0});
  }

  function resolveRetainedCombat(attackDice=[],defenseDice=[],profile={}){
    const attack=retainedDiceTotals(attackDice);
    const defense=retainedDiceTotals(defenseDice);
    const criticalCancellations=Math.min(attack.critical,defense.critical);
    attack.critical-=criticalCancellations;
    defense.critical-=criticalCancellations;
    const criticalVsNormal=Math.min(attack.normal,defense.critical);
    attack.normal-=criticalVsNormal;
    const normalCancellations=Math.min(attack.normal,defense.normal);
    attack.normal-=normalCancellations;
    defense.normal-=normalCancellations;
    attack.critical-=Math.min(attack.critical,Math.floor(defense.normal/2));
    return {
      normal:attack.normal,
      critical:attack.critical,
      damage:attack.normal*Number(profile.normal||0)+attack.critical*Number(profile.crit||0)
    };
  }

  function dimensionalBanishmentField(profile){
    return profile?.weaponId==='transdimensional-isolator'
      ? spinnerField('dimensionalBanishmentRoll','Dimensional Banishment 2D6 result (0 if not triggered)',0,0,12)
      : '';
  }

  function aggressiveDefenseFields(npo){
    return npo?.type==='Canoptek Macrocyte'
      ? '<label class="check-row compact-check"><input type="checkbox" id="attackerWithinTwo"><span><strong>Attacker is within 2&quot; of this Macrocyte</strong></span></label>'
      : '';
  }

  function aggressiveDefenseDamage(rollResult){
    const result=Math.max(1,Math.min(3,Math.round(Number(rollResult)||1)));
    return result>=2?result:0;
  }

  function aggressiveDefenseDamageValue(combat){
    return Math.max(0,Number(combat?.aggressiveDefenseDamage??combat?.aggressiveDefenceDamage)||0);
  }

  function aggressiveDefenseRollHtml(){
    return `<section class="combat-stage" id="aggressiveDefenseRoll" aria-label="Aggressive Defense Construct roll">
      <small>AGGRESSIVE DEFENSE CONSTRUCT</small>
      <p>The destroyed Macrocyte retaliates.</p>
      <div class="dice-row animated-roll" id="aggressiveDefenseDie">${rollingDieHtml()}</div>
    </section>`;
  }

  function combatAbilityReminder(combat){
    if(combat.dimensionalBanishmentTriggered){
      const incapacitated=combat.after<=0;
      return `<div class="summary-box"><strong>Dimensional Banishment:</strong> 2D6 result ${combat.dimensionalBanishmentRoll}; the target ${incapacitated?'is incapacitated':'survives'}.</div>`;
    }
    if(combat.profile?.weaponId==='transdimensional-isolator'&&combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:combat.after<=0})){
      return '<div class="summary-box"><strong>Dimensional Banishment:</strong> The target survived after damage was inflicted or a critical success was retained. Roll 2D6 physically; if the result is higher than its remaining wounds, record it as incapacitated.</div>';
    }
    if(combat.aggressiveDefenseAnimating)return aggressiveDefenseRollHtml();
    const aggressiveDamage=aggressiveDefenseDamageValue(combat);
    if(Number.isInteger(combat.aggressiveDefenseRoll)||aggressiveDamage>0){
      const attackerName=String(combat.attackerName||'').trim();
      const retaliatoryDamageMessage=aggressiveDamage>0
        ? `${attackerName?`${escapeHtml(attackerName)} suffers`:'The attacking operative suffers'} ${aggressiveDamage} retaliatory damage.`
        : `No retaliatory damage inflicted${attackerName?` on ${escapeHtml(attackerName)}`:''}.`;
      return `<section class="combat-stage aggressive-defense-result" aria-label="Aggressive Defense Construct result">
        <small>AGGRESSIVE DEFENSE CONSTRUCT</small>
        <strong>D3 Roll: ${combat.aggressiveDefenseRoll}</strong>
        <p>${retaliatoryDamageMessage}</p>
      </section>`;
    }
    return '';
  }

  function cancelPendingPlayerCombat(stage,attackType,onCancel){
    stage[`${attackType}CombatDraft`]=null;
    state.combatState=null;
    save();
    onCancel();
  }

  function showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel){
    const targets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
    if(!targets.length){
      showToast('No active NPO is available as a target.');
      showPlayerActivation(stage);
      return;
    }

    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    if(!weapons.length){
      showToast(`${playerName(stage.playerOperativeId)} has no ${attackType==='shoot'?'ranged':'melee'} weapon in its roster profile.`);
      showPlayerActivation(stage);
      return;
    }

    const draft=stage[`${attackType}CombatDraft`];
    if(draft){
      showPlayerCombatResolution(stage,attackType,draft.targetId,draft.weaponIndex,onResolved,onCancel,{result:draft,animate:false});
      return;
    }

    const singleTarget=targets.length===1?targets[0]:null;
    const targetControl=singleTarget
      ? `<div class="field"><label>Target NPO</label><div class="readonly-select">${escapeHtml(npoName(singleTarget))} · Wounds ${projectedNpoWounds(singleTarget.id,stage)}/${singleTarget.maxWounds} · Save ${singleTarget.save}+</div><input type="hidden" id="combatTarget" value="${singleTarget.id}"></div>`
      : `<div class="field"><label>Target NPO</label><select id="combatTarget"><option value="">Select a target NPO...</option>${targets.map(n=>`<option value="${n.id}">${escapeHtml(npoName(n))} · Wounds ${projectedNpoWounds(n.id,stage)}/${n.maxWounds} · Save ${n.save}+</option>`).join('')}</select></div>`;
    const weaponControl=weapons.length===1
      ? `<div class="field"><label>Weapon</label><div class="readonly-select">${escapeHtml(weapons[0].name)}</div><input type="hidden" id="playerWeaponSelect" value="0"></div>`
      : `<div class="field"><label>Weapon</label><select id="playerWeaponSelect">${weapons.map((weapon,index)=>`<option value="${index}">${escapeHtml(weapon.name)}</option>`).join('')}</select></div>`;
    const priorElimination=attackType==='melee'&&Number(stage.pendingShoot?.after)<=0
      ? `<section class="compact-elimination-notice"><strong>☠ ${escapeHtml(stage.pendingShoot.targetName)} was eliminated by the Shoot attack.</strong><span>Choose another melee target, or Cancel to revise the activation.</span></section>`
      : '';

    showModal(`Resolve ${attackLabel} Attack`,`
      ${priorElimination}
      <p>Select the target and attack profile before rolling.</p>
      ${targetControl}
      ${weaponControl}
      <div id="aggressiveDefenseFields"></div>
      <div id="weaponRules"></div>
      <div class="wizard-actions"><button class="btn ghost" id="cancelPendingAttack">Cancel</button><button class="btn primary" id="openCombatResolution">Continue</button></div>`);

    const targetSelect=$('#combatTarget');
    const weaponSelect=$('#playerWeaponSelect');
    const renderChoices=()=>{
      const target=activeNpos().find(n=>n.id===targetSelect.value);
      const weapon=weapons[Number(weaponSelect.value)||0];
      $('#aggressiveDefenseFields').innerHTML=aggressiveDefenseFields(target);
      $('#weaponRules').innerHTML=weaponRulesHtml(weapon);
      $('#openCombatResolution').disabled=!target||!weapon;
    };
    targetSelect.addEventListener('change',renderChoices);
    weaponSelect.addEventListener('change',renderChoices);
    $('#cancelPendingAttack').onclick=()=>cancelPendingPlayerCombat(stage,attackType,onCancel);
    $('#openCombatResolution').onclick=()=>showPlayerCombatResolution(stage,attackType,targetSelect.value,Number(weaponSelect.value)||0,onResolved,onCancel);
    renderChoices();
    if(singleTarget&&weapons.length===1&&singleTarget.type!=='Canoptek Macrocyte')showPlayerCombatResolution(stage,attackType,singleTarget.id,0,onResolved,onCancel);
  }

  function showPlayerCombatResolution(stage,attackType,targetId,weaponIndex,onResolved,onCancel,{result=null,animate=true}={}){
    const target=activeNpos().find(n=>n.id===targetId);
    const weapon=playerAttackWeapons(stage.playerOperativeId,attackType)[weaponIndex];
    if(!target||!weapon){showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);return;}
    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    const profile=playerWeaponProfile(weapon);
    const attackerWithinTwo=Boolean($('#attackerWithinTwo')?.checked)||Boolean(result?.attackerWithinTwo);
    const screen=showSharedCombatResolutionScreen({
      title:`Resolve ${attackLabel} Attack`,attackerName:playerName(stage.playerOperativeId),defenderName:npoName(target),
      attackType,weaponName:weapon.name,attackLabel:attackType==='shoot'?combatAttackLabel(profile):'',
      defenseLabel:`${Math.max(0,3-profile.ap)} dice · ${target.save}+`,
      cancelId:'cancelPendingAttack',continueId:'continuePendingAttack'
    });

    $('#cancelPendingAttack').onclick=()=>{
      stage[`${attackType}CombatDraft`]=null;
      state.combatState=null;
      save();
      showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);
    };

    if(result){
      displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false);
      return;
    }

    const diceDraft={attackDice:[],defenseDice:[],attackerWithinTwo};
    runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,onComplete:(attackDice,defenseDice)=>{
      diceDraft.attackDice=attackDice;
      diceDraft.defenseDice=defenseDice;
      previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,{targetId,weaponIndex});
    }});
  }

  function previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,selection={}){
    const n=state.roster.find(x=>x.id===(selection.targetId||$('#combatTarget')?.value));
    if(!n)return;
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    const weaponIndex=Number(selection.weaponIndex??$('#playerWeaponSelect')?.value)||0;
    const weapon=weapons[weaponIndex];
    const profile=playerWeaponProfile(weapon);
    const before=projectedNpoWounds(n.id,stage);
    const resolution=resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile);
    const result={
      ...recordedCombat({attackerName:playerName(stage.playerOperativeId),defenderName:npoName(n),attackType,attackerSide:'player',defenderSide:'npo',profile:{...profile,rules:weapon.rules||[]},before,
        normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage}),
      targetId:n.id,targetName:npoName(n),weaponName:weapon.name,weaponIndex
    };
    result.rolledAttackDice=diceDraft.attackDice.map(die=>({...die}));
    result.rolledDefenseDice=diceDraft.defenseDice.map(die=>({...die}));
    result.attackDice=result.rolledAttackDice;
    result.saveDice=result.rolledDefenseDice;
    result.retainedSaves=retainedDiceTotals(result.saveDice).normal+retainedDiceTotals(result.saveDice).critical;
    result.recordedOutcome=false;
    result.attackerWithinTwo=Boolean(diceDraft.attackerWithinTwo);
    const retaliationApplies=n.type==='Canoptek Macrocyte'
      &&combatAbilityHandlers['aggressive-defence-construct']({targetIncapacitated:result.after<=0,attackerWithinTwo:Boolean(diceDraft.attackerWithinTwo)});
    if(retaliationApplies){
      const rolledValue=Math.ceil(roll()/2);
      result.aggressiveDefenseRoll=rolledValue;
      result.aggressiveDefenseDamage=aggressiveDefenseDamage(rolledValue);
      stage[`${attackType}CombatDraft`]=result;
      state.combatState={side:'player',stage:{...stage}};
      save();
      displayPendingPlayerCombat(stage,attackType,{...result,aggressiveDefenseAnimating:true},onResolved,onCancel,false,true);
      const aggressiveDefenseDie=$('#aggressiveDefenseDie');
      settleAnimatedDice([{row:aggressiveDefenseDie,dice:[{value:rolledValue,kind:'hit'}]}],()=>{
        if(aggressiveDefenseDie?.isConnected)displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false);
      });
      return;
    }
    result.aggressiveDefenseDamage=0;
    stage[`${attackType}CombatDraft`]=result;
    state.combatState={side:'player',stage:{...stage}};
    save();
    displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false);
  }

  function displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,animate,waiting=false){
    displaySharedCombatResult(result,{
      pending:true,animate,waiting,
      message:'This result has been recorded. Wounds will be applied exactly once when you Continue.',
      onContinue:()=>{
        if(stage[`${attackType}CombatDraft`]===result)onResolved(result);
      }
    });
  }

  function npoBehavior(n){return npoDefinition(n.type)?.behavior;}

  function npoActionQuestion(n,index){
    const action=npoBehavior(n)?.actions[index];
    if(!action)return null;
    return {key:`action-${index}`,action,title:`Can this NPO ${action}?`,help:'Check movement, visibility, cover, control range, measurement, action points, order and all other tabletop restrictions. Choose Yes only if this printed action is legal now.'};
  }

  const npoQuestionIcons = {
    Fight:'radar',Charge:'charge',Shoot:'crosshair','Fall Back':'charge',Reposition:'objective',Dash:'charge'
  };

  function npoIcon(type){
    const paths={
      crosshair:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>',
      objective:'<path d="M6 21V4m0 1h11l-2 4 2 4H6"/><circle cx="6" cy="21" r="2"/>',
      wounded:'<path d="M12 21s-7-4.4-7-10a4 4 0 017-2.7A4 4 0 0119 11c0 5.6-7 10-7 10z"/><path d="M9 12h2l1-3 2 6 1-3h2"/>',
      shield:'<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z"/><path d="M8 12h8"/>',
      group:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6m0-5c3 0 5 2 5 5"/>',
      command:'<path d="M12 2l3 6 6 1-4.5 4.5 1 6.5-5.5-3-5.5 3 1-6.5L3 9l6-1 3-6z"/><circle cx="12" cy="12" r="2"/>'
    };
    if(type==='charge')return `<svg
  class="npo-question-icon npo-question-icon--charge"
  viewBox="0 0 32 32"
  width="32"
  height="32"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  focusable="false"
>
  <!-- Charging operative -->
  <circle
    cx="6.5"
    cy="16"
    r="4.25"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Charging operative center -->
  <circle
    cx="6.5"
    cy="16"
    r="1.25"
    fill="currentColor"
  />
  <!-- Target operative -->
  <circle
    cx="25.5"
    cy="16"
    r="4.25"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Target operative center -->
  <circle
    cx="25.5"
    cy="16"
    r="1.25"
    fill="currentColor"
  />
  <!-- Charge path:
       Starts at the right edge of the first circle.
       Ends at the left edge of the second circle. -->
  <path
    d="M10.75 16H19.25"
    stroke="currentColor"
    stroke-width="2.5"
    stroke-linecap="round"
  />
  <!-- Arrowhead:
       Tip touches the target circle at x=21.25.
       The arrowhead does not overlap the target circle. -->
  <path
    d="M17.25 12.5L21.25 16L17.25 19.5"
    stroke="currentColor"
    stroke-width="2.5"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
  <!-- Small speed lines behind the charging operative -->
  <path
    d="M1.5 12.5H3"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    opacity="0.7"
  />
  <path
    d="M0.75 16H2.25"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    opacity="0.9"
  />
  <path
    d="M1.5 19.5H3"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    opacity="0.7"
  />
</svg>`;
    if(type==='radar')return `<svg
  class="npo-question-icon npo-question-icon--radar"
  viewBox="0 0 32 32"
  width="32"
  height="32"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  focusable="false"
>
  <!-- Outer radar housing -->
  <circle
    cx="16"
    cy="16"
    r="13"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Radar range rings -->
  <circle
    cx="16"
    cy="16"
    r="8.75"
    stroke="currentColor"
    stroke-width="1.25"
    opacity="0.48"
  />
  <circle
    cx="16"
    cy="16"
    r="4.5"
    stroke="currentColor"
    stroke-width="1.25"
    opacity="0.38"
  />
  <!-- Partial scanning arcs -->
  <path
    d="M5.9 13.2A10.5 10.5 0 0 1 11.2 6.9"
    stroke="currentColor"
    stroke-width="1.35"
    stroke-linecap="round"
    opacity="0.85"
  />
  <path
    d="M8.1 19.9A8.6 8.6 0 0 0 13 24"
    stroke="currentColor"
    stroke-width="1.2"
    stroke-linecap="round"
    opacity="0.55"
  />
  <!-- Radar sweep beam -->
  <path
    d="M16 16L20.8 3.95A13 13 0 0 1 27.4 8.95L16 16Z"
    fill="currentColor"
    opacity="0.92"
  />
  <!-- Sweep leading edge -->
  <path
    d="M16 16L24.1 5.85"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <!-- Center pivot -->
  <circle
    cx="16"
    cy="16"
    r="1.65"
    fill="var(--radar-center-fill, currentColor)"
    stroke="currentColor"
    stroke-width="1.35"
  />
  <!-- Radar contacts -->
  <circle
    cx="9.3"
    cy="8.7"
    r="1.45"
    fill="currentColor"
  />
  <circle
    cx="14"
    cy="6.6"
    r="1.55"
    fill="currentColor"
  />
  <circle
    cx="23.3"
    cy="14"
    r="1.45"
    fill="currentColor"
  />
  <circle
    cx="21.3"
    cy="21.6"
    r="1.45"
    fill="currentColor"
  />
  <circle
    cx="10.2"
    cy="21"
    r="1.35"
    fill="currentColor"
  />
</svg>`;
    if(type==='hatch')return `<svg
  class="npo-question-icon npo-question-icon--hatch"
  viewBox="0 0 32 32"
  width="32"
  height="32"
  fill="none"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  focusable="false"
>
  <!-- Outer hatch frame -->
  <rect
    x="5"
    y="3.5"
    width="22"
    height="25"
    rx="3"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Inner hatch door -->
  <rect
    x="8.5"
    y="7"
    width="15"
    height="18"
    rx="1.5"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Reinforced upper and lower door panels -->
  <path
    d="M9 11H23"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <path
    d="M9 21H23"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <!-- Central split between hatch doors -->
  <path
    d="M16 7.5V24.5"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
  <!-- Hatch locking wheel -->
  <circle
    cx="16"
    cy="16"
    r="3.25"
    fill="var(--icon-surface, currentColor)"
    stroke="currentColor"
    stroke-width="2"
  />
  <!-- Locking wheel spokes -->
  <path
    d="M16 12.75V19.25"
    stroke="var(--icon-detail, currentColor)"
    stroke-width="1.5"
    stroke-linecap="round"
  />
  <path
    d="M12.75 16H19.25"
    stroke="var(--icon-detail, currentColor)"
    stroke-width="1.5"
    stroke-linecap="round"
  />
  <!-- Floor threshold -->
  <path
    d="M3.5 28.5H28.5"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
  />
</svg>`;
    return `<svg class="npo-question-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[type]||paths.command}</svg>`;
  }

  function renderCompletedNpoQuestions(history){
    return history.map(item=>`<div class="npo-question-complete npo-question-history">${npoIcon(npoQuestionIcons[item.action.split(' ')[0]])}<span>${escapeHtml(item.action)}</span><strong>${item.answer?'Yes':'No'}</strong></div>`).join('');
  }

  function renderActiveNpoQuestion(q){
    return `<section class="npo-question-active npo-question-card--active" aria-live="polite" aria-atomic="true">
      ${npoIcon(npoQuestionIcons[q.action.split(' ')[0]])}<h3>${escapeHtml(q.title)}</h3><p>${escapeHtml(q.help)}</p>
      <div class="ai-choice-grid"><button class="ai-choice no" data-answer="no"><strong>No</strong></button><button class="ai-choice yes" data-answer="yes"><strong>Yes</strong></button></div>
    </section>`;
  }

  function runNpoPrompt(n,index,answers,history){
    const q=npoActionQuestion(n,index);
    if(!q){resolveNpo(n,answers,history);return;}
    const priorTop=$('.npo-question-active',modal)?.getBoundingClientRect().top;
    modalBody.innerHTML=`<div class="modal-inner"><h2>NPO Activation: ${escapeHtml(npoName(n))}</h2><div class="ai-wizard">
      <div class="npo-question-flow">${renderCompletedNpoQuestions(history)}${renderActiveNpoQuestion(q)}</div>
      <div class="wizard-actions">
        <button class="btn ghost" id="aiBack" ${history.length===0?'disabled':''}>Back</button>
        <button class="btn ghost" data-close>Exit Guide</button>
      </div>
    </div></div>`;
    if(!modal.open)modal.showModal();
    $('[data-close]',modal).onclick=closeModal;
    if(priorTop!==undefined)requestAnimationFrame(()=>{const active=$('.npo-question-active',modal);if(!active)return;const delta=active.getBoundingClientRect().top-priorTop;modal.scrollBy({top:delta,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
    $$('[data-answer]',modal).forEach(btn=>btn.onclick=()=>{
      const answer=btn.dataset.answer==='yes';
      const nextAnswers={...answers,[q.key]:answer};
      const action=npoBehavior(n).actions[index];
      const nextHistory=[...history,{index,answers,answer,action}];
      if(answer)resolveNpo(n,{...nextAnswers,action},nextHistory);
      else runNpoPrompt(n,index+1,nextAnswers,nextHistory);
    });
    $('#aiBack')?.addEventListener('click',()=>{
      const previous=history[history.length-1];
      if(previous)runNpoPrompt(n,previous.index,previous.answers,history.slice(0,-1));
    });
  }

  function chooseNpoDecision(n,c){
    const action=c.action||'Pass';
    const attack=/^(Fight|Shoot)/.test(action);
    const target=action.startsWith('Fight')?'Apply Fight target priority: most likely to incapacitate, greatest mission impact, then Ready; randomize any remaining tie':action.startsWith('Shoot')?'Apply Shoot target priority: most likely to incapacitate, greatest mission impact, not obscured, not in cover, closest, then Ready; randomize any remaining tie':'Follow the target and movement priority printed in this action';
    return {action,target,stance:'Engage',threat:attack?1:0,reason:c.action?'This is the first legal action in this operative’s printed behavior list.':'No printed action is currently legal; this NPO passes.',path:[action]};
  }

  function resolveNpo(n,c,questionHistory=[]){
    state.npoAttackTargetId=null;
    const decision=chooseNpoDecision(n,c);
    const attacks=decision.action.includes('Fight')||decision.action.includes('Shoot');
    const dice=[];
    state.lastActivation={npoId:n.id,name:npoName(n),...decision,dice,answers:c,questionHistory,attackRequired:attacks,targetConfirmed:false,committed:false};
    save();

    renderNpoDecisionResult(n,decision,dice,c,false,false,attacks,false,questionHistory);
  }

  function initiativeSummary(dice){
    const crits=dice.filter(d=>d.kind==='crit').length;
    const hits=dice.filter(d=>d.kind==='hit').length;
    const misses=dice.filter(d=>d.kind==='miss').length;
    if(crits===0&&hits===0)return 'Attack missed. No saves or damage required.';
    return `${crits} critical · ${hits} normal · ${misses} miss`;
  }

  function renderNpoDecisionResult(n,decision,dice,answers,attackResolved,animateDice=true,attackRequired=(decision.action.includes('Fight')||decision.action.includes('Shoot')),targetConfirmed=dice.length>0,questionHistory=state.lastActivation?.questionHistory||[]){
    const eligibleTargetIds=eligibleNpoAttackTargets();
    if(!targetConfirmed&&eligibleTargetIds.length===1)state.npoAttackTargetId=eligibleTargetIds[0];
    state.lastActivation={...state.lastActivation,name:npoName(n),...decision,dice,answers,questionHistory,attackResolved,attackRequired,targetConfirmed};save();
    const targetOptions=eligibleTargetIds.map(id=>`<option value="${escapeHtml(id)}" ${state.npoAttackTargetId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
    const targetName=state.npoAttackTargetId?playerName(state.npoAttackTargetId):'';
    const targetField=targetConfirmed||eligibleTargetIds.length===1
      ? `<input id="npoPriorityTarget" value="${escapeHtml(targetName)}" readonly>`
      : `<select id="npoPriorityTarget" ${attackResolved?'disabled':''}><option value="">Select matching operative</option>${targetOptions}</select>`;
    const attackSummary=attackResolved&&state.npoAttackSummary?{
      ...state.npoAttackSummary,
      side:'player',
      attackType:state.npoAttackSummary.attackType||(decision.action.includes('Fight')?'melee':'shoot')
    }:null;
    const eliminationAction=newlyEliminated(attackSummary)?` Eliminated ${escapeHtml(attackSummary.targetName)}.`:'';
    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <div class="npo-question-flow">${renderCompletedNpoQuestions(questionHistory)}</div>
      <div class="ai-result-title"><div><h2>${escapeHtml(npoName(n))}</h2><p>${escapeHtml(n.type)}</p></div></div>
      <div class="npo-result-card">${npoIcon('command')}<div><small>ACTIVATION PLAN</small><strong>${escapeHtml(decision.action)}</strong><p>${escapeHtml(decision.reason)}</p><div class="npo-target-priority"><small>TARGET PRIORITY</small><strong>${escapeHtml(decision.target)}</strong>${attackRequired?`<div class="field target-selection"><label for="npoPriorityTarget">Target Player Operative</label>${targetField}</div>`:''}</div></div></div>
      ${attackRequired&&!targetConfirmed?`<button class="btn secondary big-action" id="confirmNpoTarget" ${state.npoAttackTargetId?'':'disabled'}>Confirm Target</button>`:''}
      ${attackRequired&&targetConfirmed&&!attackResolved?`<button class="btn secondary big-action" id="rollPlayerSaves">Resolve Combat</button>`:''}
      ${attackSummary?`${renderEliminationSummary(attackSummary)}<section class="card npo-attack-summary">
        <p class="eyebrow">NPO ATTACK SUMMARY</p>
        ${renderAttackSummary(attackSummary)}
        <div class="combat-stage"><small>PLAYER SAVE ROLL</small><div class="dice-row settled">${attackSummary.saveDice.length?attackSummary.saveDice.map(dieHtml).join(''):'<span class="muted">No save dice rolled</span>'}</div></div>
        <div class="damage-summary">
          <div><small>Unsaved normal hits</small><strong>${attackSummary.normalRemaining}</strong></div>
          <div><small>Unsaved critical hits</small><strong>${attackSummary.critRemaining}</strong></div>
        </div>
      </section><div class="summary-box"><strong>Actions:</strong> ${attackSummary.attackType==='shoot'?'Shooting':'Melee'} attack resolved.${eliminationAction}</div>`:''}
      <div class="wizard-actions"><button class="btn primary" id="completeNpo" ${attackRequired&&!attackResolved?'disabled':''}>Complete Activation</button></div>
    </div>`;
    if(!modal.open)modal.showModal();
    const openSaveWizard=(resolvedDice,animate=false)=>showNpoAttackWizard(n,resolvedDice,(summary)=>{
      completeNpoActivation(summary);
    },()=>{
      save();
      renderNpoDecisionResult(n,decision,resolvedDice,answers,false,false,true,true);
    },animate);
    $('#npoPriorityTarget')?.addEventListener('change',()=>{state.npoAttackTargetId=$('#npoPriorityTarget').value||null;const b=$('#confirmNpoTarget');if(b)b.disabled=!state.npoAttackTargetId;save();});
    $('#rollPlayerSaves')?.addEventListener('click',()=>openSaveWizard(dice));
    $('#confirmNpoTarget')?.addEventListener('click',()=>{
      if(!state.npoAttackTargetId)return;
      state.npoAttackSummary=null;
      const rolledDice=[];
      const history=state.activationHistory.find(x=>x.side==='npo'&&x.label===npoName(n)&&!x.target);
      if(history)history.target=playerName(state.npoAttackTargetId);
      log(`${npoName(n)} confirmed ${playerName(state.npoAttackTargetId)} as the attack target.`);
      save();
      openSaveWizard(rolledDice,true);
    });

    $('#completeNpo').onclick=()=>completeNpoActivation();
  }

  async function completeNpoActivation(attackSummary=null){
    if(state.lastActivation?.committed)return;
    const n=state.roster.find(item=>item.id===state.lastActivation?.npoId);
    if(!n||!n.ready)return;
    if(attackSummary){
      state.lastActivation={...state.lastActivation,attackResolved:true,attackSummary};
      const history=state.activationHistory.find(entry=>entry.side==='npo'&&entry.label===state.lastActivation?.name);
      if(history)history.attackSummary=attackSummary;
    }
    if(state.lastActivation.threat)setThreat(state.lastActivation.threat,`${npoName(n)} ${state.lastActivation.action.includes('Fight')?'Fight':'Shoot'}`);
    const activationId=missionActivationId('npo',n.id);
    n.ready=false;state.npoActivated++;state.activationNumber++;
    state.activationHistory.unshift({side:'npo',label:npoName(n),action:state.lastActivation.action,target:state.npoAttackTargetId?playerName(state.npoAttackTargetId):null,attackSummary});
    state.lastActivation.committed=true;
    state.activeNpoId=null;advanceAfterActivation('npo');
    log(`${npoName(n)}: ${state.lastActivation.action}.`);
    state.npoAttackTargetId=null;
    state.npoAttackSummary=null;
    save();
    closeModal();
    await executeMissionLifecycleHook('onNpoActivationCompleted',{activationId,operativeId:n.id});
    const gameEnded=checkGameEnd();
    if(!gameEnded)render();
  }


  function applyNpoAttackDamage(n,target,summary){
    state.playerWounds=state.playerWounds||{};
    state.playerWounds[target.id]=summary.after;
    const casualties=new Set(state.playerCasualtyIds||[]);
    if(summary.after<=0){
      casualties.add(target.id);
      if(!state.playerActivatedIds.includes(target.id))state.playerActivatedIds.push(target.id);
    }else{
      casualties.delete(target.id);
    }
    state.playerCasualtyIds=[...casualties];
    state.playerReady=playerOperativesRemaining();
    log(`${npoName(n)} dealt ${summary.damage} damage to ${target.name} (${summary.before} → ${summary.after} wounds).`);
  }

  function showNpoAttackWizard(n,attackDice,onDone,onCancel,animateCombat=false){
    const target=selectedNpoAttackTarget();
    if(!target){showToast('Select the targeted Player operative first.');if(onCancel)onCancel();return;}
    const attackType=state.lastActivation?.action?.includes('Fight')?'melee':'shoot';
    const availableProfiles=npoAttackProfiles(n,attackType);
    const saved=state.lastActivation?.combatDraft;
    const sameCombat=saved&&saved.targetId===target.id&&saved.attackType===attackType;
    const initialProfile=sameCombat?saved.profile:canonicalAttackProfile(availableProfiles[0]);
    const profileControl=!sameCombat&&availableProfiles.length>1
      ? `<div class="field compact-combat-choice"><label>NPO Weapon Profile</label><select id="npoCombatProfile">${availableProfiles.map((profile,index)=>`<option value="${index}">${escapeHtml(canonicalAttackProfile(profile).name)}</option>`).join('')}</select></div>`
      : '';
    const screen=showSharedCombatResolutionScreen({
      title:'Resolve Combat',attackerName:npoName(n),defenderName:target.name,attackType,
      weaponName:initialProfile.name,attackLabel:combatAttackLabel(initialProfile),defenseLabel:`3 dice · ${target.save||3}+`,
      cancelId:'cancelNpoAttack',continueId:'completeNpoCombat',extraHtml:profileControl,
      detailsHtml:`${npoCombatGuidanceHtml(n)}<div id="npoCombatRules">${weaponRulesHtml(initialProfile)}</div>`
    });
    const cancel=()=>{
      if(combatTimer)combatTimer();
      if(!sameCombat)state.lastActivation={...state.lastActivation,combatDraft:null};
      save();
      if(onCancel)onCancel();
    };
    $('#cancelNpoAttack').onclick=cancel;

    let combatTimer=null;
    let resolutionCommitted=false;
    const commitCombat=(combat)=>{
      if(resolutionCommitted)return;
      resolutionCommitted=true;
      const complete=$('#completeNpoCombat');
      complete.disabled=true;
      const resolvedCombat=dimensionalBanishmentRequired(combat)?applyDimensionalBanishment(combat,num('dimensionalBanishmentRoll')):combat;
      state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
      save();
      const summary={...resolvedCombat,side:'player'};
      applyNpoAttackDamage(n,target,summary);
      if(onDone)onDone(summary);
    };
    const displayCombat=(combat,animate=false)=>{
      const banishmentRequired=dimensionalBanishmentRequired(combat);
      displaySharedCombatResult(combat,{
        animate,
        message:'Damage is applied exactly once when you Continue.',
        extraHtml:banishmentRequired?`<div id="dimensionalBanishmentField">${dimensionalBanishmentField(combat.profile)}</div>`:'',
        onContinue:()=>commitCombat(combat)
      });
      if(banishmentRequired)bindSpinners($('#dimensionalBanishmentField'));
    };
    const finishAutomaticCombat=(profile,rolledAttackDice,rolledDefenseDice)=>{
      const resolution=resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile);
      const combat={
        ...recordedCombat({attackerName:npoName(n),defenderName:target.name,attackType,attackerSide:'npo',defenderSide:'player',profile,before:target.wounds||10,
          normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage}),
        attackDice:rolledAttackDice,saveDice:rolledDefenseDice,
        retainedSaves:retainedDiceTotals(rolledDefenseDice).normal+retainedDiceTotals(rolledDefenseDice).critical,
        recordedOutcome:false,targetId:target.id,targetName:target.name
      };
      state.lastActivation={...state.lastActivation,combatDraft:combat};
      save();
      displayCombat(combat,false);
    };
    const startAutomaticCombat=()=>{
      if(combatTimer)combatTimer();
      const profile=canonicalAttackProfile(availableProfiles[Number($('#npoCombatProfile')?.value)||0]);
      const weapon=$('.compact-combat-profile div:nth-child(4) strong');
      if(weapon)weapon.textContent=profile.name;
      const attack=$('.compact-combat-profile div:nth-child(5) strong');
      if(attack)attack.textContent=combatAttackLabel(profile);
      const rules=$('#npoCombatRules');
      if(rules)rules.innerHTML=weaponRulesHtml(profile);
      $('#combatResults').replaceChildren();
      $('#completeNpoCombat').disabled=true;
      $('#completeNpoCombat').textContent='Rolling…';
      state.lastActivation={...state.lastActivation,dice:attackDice.map(d=>({...d})),targetConfirmed:true,combatDraft:null};
      save();
      combatTimer=runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,onComplete:(rolledAttackDice,rolledDefenseDice)=>{
        combatTimer=null;
        finishAutomaticCombat(profile,rolledAttackDice,rolledDefenseDice);
      }});
    };
    $('#npoCombatProfile')?.addEventListener('change',startAutomaticCombat);
    if(sameCombat)displayCombat(saved,animateCombat);
    else startAutomaticCombat();
  }

  function spinnerField(id,label,value,min,max){return `<div class="field spinner-field"><label>${label}</label><div class="spinner"><input id="${id}" type="number" value="${value}" min="${min}" max="${max}" inputmode="numeric"><button type="button" data-spin="${id}" data-delta="-1" aria-label="Decrease ${label}">−</button><button type="button" data-spin="${id}" data-delta="1" aria-label="Increase ${label}">+</button></div></div>`;}
  function bindSpinners(root){$$('[data-spin]',root).forEach(b=>b.onclick=()=>{const input=$(`#${b.dataset.spin}`);const min=Number(input.min||0),max=Number(input.max||99);input.value=Math.max(min,Math.min(max,(Number(input.value)||0)+Number(b.dataset.delta)));});}
  function num(id){return Number($(`#${id}`)?.value)||0;}

  function rollingDieHtml(){
    const value=roll();
    return `<div class="die hit rolling" aria-label="Rolling die">${pipPositions[value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;
  }

  const pipPositions={1:[5],2:[1,9],3:[1,5,9],4:[1,3,7,9],5:[1,3,5,7,9],6:[1,3,4,6,7,9]};
  function dieHtml(d){const kind=d.kind||'';return `<div class="die ${kind}" aria-label="${d.value}${kind?` ${kind}`:''}">${pipPositions[d.value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;}

  function renderMission(){
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name)}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary)}</p></div>`).join('');
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${m.brief}</p></div></div>
      <section class="card"><h3>Objective</h3><p>${m.objective}</p><div class="stat-grid"><div class="stat"><small>Starting NPOs</small><strong>${missionSetup(m)}</strong></div><div class="stat"><small>TP1 Initiative</small><strong>${missionFirstInitiative(m)==='npo'?'NPOs':'Player'}</strong></div><div class="stat"><small>Objective</small><strong>${escapeHtml(m.missionEngine?.progressLabel||missionTracker(m))}</strong></div></div><p><strong>NPO deployment:</strong> ${escapeHtml(m.startingNpos?.deployment||'Use the mission rules.')}</p></section>
      ${boardSvg(m.id)}
      <section class="card"><h3>Mission rules</h3><div class="mission-rules">${rules}</div></section>
      <section class="card"><h3>Victory</h3><p><strong>Win:</strong> ${escapeHtml(m.victory?.win||'See mission rules.')}</p><p><strong>Lose:</strong> ${escapeHtml(m.victory?.lose||'See mission rules.')}</p></section>${missionProgressHtml()}`;
  }
  function renderRoster(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>Wounds and Ready status update the guided activation flow.</p></div><button class="btn secondary" id="addNpo">Add NPO</button></div><div class="player-roster-grid npo-roster-grid">${state.roster.length?state.roster.map(n=>npoRosterCard(n,n.battlefieldState==='deployed')).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-player-attack]').forEach(b=>b.onclick=()=>showPlayerAttackWizard(b.dataset.playerAttack));$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-ready]').forEach(b=>b.onclick=()=>toggleReady(b.dataset.ready));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));}
  function renderPlayerRoster(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    const cards=(state.playerRoster||[]).map(id=>{
      const operative=livePlayerOperative(id);
      if(!operative)return '';
      const eliminated=casualties.has(id);
      const status=eliminated?'ELIMINATED':activated.has(id)?'ACTIVATED':'READY';
      const weaponNames=(operative.weapons||[]).map(w=>escapeHtml(w.name)).join(' · ');
      return `<article class="operative-card ${eliminated?'dead':''}"><div class="player-roster-card-heading"><div><h4>${escapeHtml(operative.name)}</h4><p>${escapeHtml(operative.role||'Operative')}</p></div><strong>${status}</strong></div><div class="stat-grid compact-stats"><div class="stat"><small>APL</small><strong>${operative.apl??'—'}</strong></div><div class="stat"><small>MOVE</small><strong>${operative.move??'—'}"</strong></div><div class="stat"><small>SAVE</small><strong>${operative.save??'—'}+</strong></div><div class="stat"><small>WOUNDS</small><strong>${playerCurrentWounds(id)}/${playerDefinition(id)?.wounds??operative.wounds}</strong></div></div>${weaponNames?`<p class="player-roster-weapons"><strong>Weapons:</strong> ${weaponNames}</p>`:''}<button class="btn ${eliminated?'secondary':'ghost'}" data-player-roster-status="${id}">${eliminated?'Restore Operative':'Update Status'}</button></article>`;
    }).join('');
    const teamName=playerTeamData?.teamName||playerTeamEntry()?.name||'Player';
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">PLAYER ROSTER</p><h2>${escapeHtml(teamName)}</h2><p>${livingPlayerOperativeCount()} active of ${(state.playerRoster||[]).length} selected operatives.</p></div></div><div class="roster-grid">${cards||'<div class="card empty">No Player operatives were selected for this game.</div>'}</div>`;
    $$('[data-player-roster-status]').forEach(button=>button.onclick=()=>showPlayerOperativeStatus(button.dataset.playerRosterStatus));
  }
  function npoRosterCard(n,controls){
    const status=n.battlefieldState==='reserve'?'RESERVE':n.wounds<=0?'ELIMINATED':n.dormant?'DORMANT':n.ready?'READY':'ACTIVATED';
    return `<article class="player-roster-card npo-roster-card ${n.wounds<=0?'dead':''}">
      <div class="player-roster-card-head"><div><strong>${escapeHtml(npoName(n))}</strong></div><span class="npo-status-badge ${status.toLowerCase()}">${status}</span></div>
      <div class="operative-stat-line"><span><small>ATTACK</small><b>${n.attack?.dice??'—'}</b></span><span><small>HIT</small><b>${n.attack?.hit??'—'}+</b></span><span><small>SAVE</small><b>${n.save}+</b></span><span><small>WOUNDS</small><b>${n.wounds}/${n.maxWounds}</b></span></div>
      ${controls?`<div class="quick-actions"><button class="btn secondary" data-player-attack="${n.id}">Player Attack</button><button class="btn ghost" data-wound="${n.id}">− Wound</button><button class="btn ghost" data-heal="${n.id}">+ Heal</button><button class="btn secondary" data-ready="${n.id}" ${n.dormant?'disabled':''}>${n.ready?'Expend':n.dormant?'Dormant':'Ready'}</button><button class="btn danger" data-delete="${n.id}">Delete</button></div>`:''}
    </article>`;
  }
  function operativeCard(n,controls){return npoRosterCard(n,controls);}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(j.text)}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Instructions & quick reference</h2><p>Review the NPO decision process and common gameplay terms without changing the current game.</p></div></div>${guideInstructionsHtml(false)}<section class="card help-list">
    <details><summary>What does Player mean?</summary><p>Your solo player-controlled Kill Team operatives.</p></details>
    <details><summary>What is an NPO?</summary><p>A non-player operative controlled by the Guide’s decision tree.</p></details>
    <details><summary>What is Threat Level?</summary><p>A 0–15 alert meter that rises from loud or destructive actions. Higher Threat produces higher grades, more reinforcements, and eventually Tomb World events.</p></details>
    <details><summary>What is Threat Grade?</summary><p>Grade 0 at Threat 0, Grade 1 at 1–5, Grade 2 at 6–10, and Grade 3 at 11–15. Reinforcements normally equal the current grade after Turning Point 1.</p></details>
    <details><summary>How does alternating activation work?</summary><p>The side with initiative activates first. The Guide then alternates Player and NPO activations whenever both sides still have ready operatives. If one side runs out, the other finishes its remaining activations.</p></details>
    <details><summary>What happens during the Strategy Phase?</summary><p>The Guide readies operatives, applies mission Ready rules, determines initiative, then processes Tomb World events and reinforcements.</p></details>
    <details><summary>How are saves and damage handled?</summary><p>Roll physical dice and resolve retained successes with the current Core rules. The Guide shows the canonical profile and records the resulting damage; Player damage remains pending until the whole activation is confirmed.</p></details>
  </section>`;}


  function boardSvg(id){
    const currentMission=mission();
    const missionNumber=String(currentMission.number).padStart(2,'0');
    const imagePath=`Assets/Maps/mission-${missionNumber}.png`;
    return `<figure class="official-map-card">
      <div class="official-map-heading">
        <div><span>OFFICIAL MISSION MAP</span><strong>${escapeHtml(currentMission.number)} · ${escapeHtml(currentMission.name)}</strong></div>
        <small>Extracted from the included Games Workshop mission-pack PDF</small>
      </div>
      <img class="official-map-image" src="${imagePath}" alt="Official board layout for ${escapeHtml(currentMission.name)}" loading="eager">
      <figcaption>Only the map for this mission is shown. The complete official PDF is stored locally in <code>Assets/Tomb-World-Mission-Pack.pdf</code>.</figcaption>
    </figure>`;
  }

  function renderGuideMapMarker(marker){
    const [x,y,rawLabel]=marker;
    const label=escapeHtml(rawLabel);
    if(rawLabel==='SARCOPHAGUS') return `<g class="guide-map-marker guide-map-sarcophagus" transform="translate(${x} ${y})"><rect x="-58" y="-22" width="116" height="44" rx="12"/><path d="M-38 0H38"/><text y="5" text-anchor="middle">S</text><text class="guide-map-marker-caption" y="42" text-anchor="middle">SARCOPHAGUS</text></g>`;
    if(rawLabel==='ESCAPE') return `<g class="guide-map-marker guide-map-exit" transform="translate(${x-12} ${y})"><path d="M-36 -21H-8V-35L23 0-8 35V21H-36Z"/><text class="guide-map-marker-caption" x="-46" y="5" text-anchor="end">ESCAPE</text></g>`;
    if(rawLabel==='BREACH') return `<g class="guide-map-marker guide-map-breach" transform="translate(${x} ${y})"><circle r="17"/><path d="M-8 8 8-8M-8-8 8 8"/><text class="guide-map-marker-caption" y="38" text-anchor="middle">BREACH</text></g>`;
    if(rawLabel==='REGROUP') return `<g class="guide-map-marker guide-map-regroup" transform="translate(${x} ${y})"><circle r="27"/><path d="M-12 0H12M0-12V12"/><text class="guide-map-marker-caption" y="46" text-anchor="middle">REGROUP</text></g>`;
    return `<g class="guide-map-marker guide-map-objective" transform="translate(${x} ${y})"><path d="M0-18 18 0 0 18-18 0Z"/><text y="5" text-anchor="middle">${label}</text></g>`;
  }
  function rosterBreakdown(){const counts={};state.roster.forEach(n=>counts[n.type]=(counts[n.type]||0)+1);return Object.entries(counts).map(([k,v])=>`${v} ${k}${v>1?'s':''}`).join(' · ')||'No starting NPOs';}
  function showAddNpo(){showModal('Add NPO',`<div class="field"><label>NPO type</label><select id="newNpoType">${Object.keys(npoDefinitions).map(x=>`<option>${x}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add NPO</button></div>`);$('#confirmAdd').onclick=()=>{if(activeNpos().length>=MAX_NPOS){showToast(`Only ${MAX_NPOS} active NPOs can be on the battlefield.`);return;}const type=$('#newNpoType').value;state.roster.push(createNpo(type));log(`${type} added to the battlefield.`);closeModal();save();render();};}
  function adjustWounds(id,d){const n=state.roster.find(x=>x.id===id);if(!n)return;const wasOut=n.battlefieldState==='out-of-action';n.wounds=Math.max(0,Math.min(n.maxWounds,n.wounds+d));if(n.wounds===0){n.ready=false;n.deployed=false;n.battlefieldState='out-of-action';}else if(wasOut){n.deployed=true;n.battlefieldState='deployed';}if(checkGameEnd())return;save();render();}
  function toggleReady(id){const n=state.roster.find(x=>x.id===id);if(n&&n.wounds>0&&!n.dormant)n.ready=!n.ready;save();render();}
  function deleteNpo(id){state.roster=state.roster.filter(x=>x.id!==id);save();render();}

  function animateMissionDice(operation){
    return new Promise((resolve,reject)=>{
      const dice=Array.from({length:operation.dice.count},()=>roll(operation.dice.sides));
      let settled=false;
      showModal(operation.label||'Mission Roll',`<div class="dice-row animated-roll" id="missionDiceRoll">${dice.map(()=>rollingDieHtml()).join('')}</div><p>Rolling ${operation.dice.count}D${operation.dice.sides}…</p>`,()=>{if(!settled)reject(new TombWorldMissionEngine.MissionEngineError('DICE_CANCELLED','Mission dice roll was cancelled.'));});
      missionDialogLocked=true;
      setTimeout(()=>{
        if(!modal.open)return;
        settled=true;
        $('#missionDiceRoll').className='dice-row settled';
        $('#missionDiceRoll').innerHTML=dice.map(value=>dieHtml({value})).join('');
        modalBody.querySelector('p').textContent=`Dice: ${dice.join(' + ')} · Total: ${dice.reduce((sum,value)=>sum+value,0)}`;
        setTimeout(()=>{missionDialogLocked=false;closeModal();resolve({dice,total:dice.reduce((sum,value)=>sum+value,0)});},450);
      },700);
    });
  }

  function requestMissionNumber(operation){
    return new Promise((resolve,reject)=>{
      let submitted=false;
      const minimum=operation.minimum??0;
      const maximum=Math.min(operation.maximum??20,Math.max(minimum,livingPlayerOperativeCount()));
      const label=operation.label||'Mission value';
      const initial=Math.max(minimum,Math.min(operation.default??minimum,maximum));
      showModal(operation.title||'Mission Input',`<div class="field"><label for="missionNumericInput">${escapeHtml(label)}</label><input id="missionNumericInput" type="number" inputmode="numeric" step="1" min="${minimum}" max="${maximum}" value="${initial}" aria-describedby="missionNumericError"><small class="field-error" id="missionNumericError" aria-live="polite"></small></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmMissionNumber">Continue</button></div>`,()=>{if(!submitted)reject(new TombWorldMissionEngine.MissionEngineError('INPUT_CANCELLED','Mission input was cancelled.'));});
      const input=$('#missionNumericInput'),confirm=$('#confirmMissionNumber'),error=$('#missionNumericError');
      const validate=()=>{
        const value=Number(input.value),valid=input.value.trim()!==''&&Number.isInteger(value)&&value>=minimum&&value<=maximum;
        error.textContent=valid?'':`Enter a whole number from ${minimum} to ${maximum}.`;
        confirm.disabled=!valid;
        input.setAttribute('aria-invalid',String(!valid));
        return valid;
      };
      input.addEventListener('input',validate);
      input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!confirm.disabled){event.preventDefault();confirm.click();}});
      confirm.onclick=()=>{
        if(!validate())return;
        const value=Number(input.value);
        submitted=true;closeModal();resolve(value);
      };
      validate();
    });
  }

  async function runMissionEvent(execute){
    if(missionOperationResolving||!objectiveEngine)return null;
    missionOperationResolving=true;
    try{return await execute();}
    catch(error){
      if(!['INPUT_CANCELLED','DICE_CANCELLED'].includes(error.code)){console.error('[MissionEngine]',error);showToast('The mission action could not be completed. Please try again.');}
      return null;
    }finally{missionOperationResolving=false;}
  }

  function missionLifecycleContext(overrides={}){
    return {
      turningPoint:state.turningPoint,
      phase:state.phase,
      activationId:overrides.activationId??null,
      gameplay:{
        turningPoint:state.turningPoint,
        phase:state.phase,
        activationNumber:state.activationNumber,
        activeSide:state.nextSide
      },
      ...overrides
    };
  }

  function missionActivationId(side,operativeId){
    return `${state.turningPoint}:${state.activationNumber+1}:${side}:${operativeId}`;
  }

  function notifyMissionActivationStarted(side,operativeId){
    const activationId=missionActivationId(side,operativeId);
    if(missionActivationStarts.has(activationId))return;
    missionActivationStarts.add(activationId);
    const hookName=side==='player'?'onPlayerActivationStarted':'onNpoActivationStarted';
    void executeMissionLifecycleHook(hookName,{activationId,operativeId});
  }

  async function executeMissionLifecycleHook(hookName,overrides={}){
    if(!objectiveEngine)return [];
    const events=objectiveDefinition?.hooks?.[hookName]||[];
    const outcomes=await runMissionEvent(()=>objectiveEngine.executeMissionHook(hookName,missionLifecycleContext(overrides)));
    if(!outcomes)return null;
    for(let index=0;index<outcomes.length;index++){
      const outcome=outcomes[index];
      if(outcome.status!=='completed')continue;
      const event=events[index]||{};
      const change=outcome.changes?.[0];
      if(change)log(`${event.label||event.id||'Mission event'}: progress changed from ${change.before} to ${change.after}.`);
      save();
      if(change)showMissionResult(String(event.label||event.id||'Mission event').toUpperCase(),outcome);
    }
    return outcomes;
  }

  function missionHistoryText(entry){
    const change=entry.changes?.[0];
    if(!change)return entry.summary||entry.title||'Mission activity recorded.';
    const delta=change.after-change.before;
    return `${entry.title||'Mission activity'}: ${delta>0?'+':''}${delta}`;
  }

  function missionOperation(operationId){
    const actions=objectiveDefinition?.actions||[];
    const hooks=Object.values(objectiveDefinition?.hooks||{}).flat();
    return [...actions,...hooks].flatMap(event=>event.operations||[]).find(operation=>operation.id===operationId)||null;
  }

  function missionDetailsContent(){
    if(!objectiveEngine){
      const selected=mission();
      return `<div class="mission-details"><h3>${escapeHtml(selected?.name||'Selected Mission')}</h3><section><h4>Objective</h4><p>${escapeHtml(selected?.objective||'Review the mission rules and track progress on the tabletop.')}</p></section><p class="muted">Automated mission progress is not available for this mission.</p></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
    }
    const model=objectiveEngine.getMissionDetailsModel();
    const objective=model.objectives[0];
    const history=model.history.slice(0,objectiveDefinition.presentation.historyDisplayCount||5);
    if(!objective)return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3><section><h4>Objective</h4><p>${escapeHtml(model.objectiveSummary)}</p></section><section><h4>Recent Activity</h4>${history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(missionHistoryText(entry))}</span></li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>'}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
    const completedDuring=objective.completedTurningPoint?`<section><h4>Completed during</h4><p>Turning Point ${objective.completedTurningPoint}</p></section>`:'';
    const activity=history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(missionHistoryText(entry))}</span>${entry.turningPoint?`<small>Turning Point ${entry.turningPoint}</small>`:''}</li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>';
    return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3>${objective.completed?'<p class="mission-complete-status">✓ Objective Complete</p>':`<section><h4>Objective</h4><p>${escapeHtml(model.objectiveSummary)}</p></section>`}${completedDuring}<section><h4>${objective.completed?'Final Progress':'Progress'}</h4><p class="mission-progress">${objective.value} / ${objective.target}</p></section><section><h4>Recent Activity</h4>${activity}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
  }

  function showMissionDetails(){
    const completed=Boolean(objectiveEngine?.getMissionHudModel().completed);
    showModal(completed?'MISSION STATUS':'MISSION DETAILS',missionDetailsContent());
  }

  function showMissionResult(title,outcome){
    const change=outcome.changes?.[0],dice=Object.values(outcome.results||{})[0]?.dice||[],model=objectiveEngine.getMissionHudModel();
    const objective=objectiveDefinition.objectives.find(item=>item.id===change?.objectiveId);
    const delta=change?Math.abs(change.after-change.before):0;
    const decreased=change&&change.after<=change.before;
    const detail=objective?(decreased?(delta?`${objective.label} repaired: ${delta}`:`No ${objective.label} repaired.`):`${objective.label} added: ${delta}`):'Mission result recorded.';
    const completed=Boolean(model.completed&&change&&change.before<model.target);
    const completionDialog=objectiveDefinition.dialogs[objectiveDefinition.completion.dialogId]||{};
    const total=dice.reduce((sum,value)=>sum+value,0);
    const inputs=Object.entries(outcome.inputs||{}).map(([id,value])=>`<p>${escapeHtml(missionOperation(id)?.label||id)}: <strong>${value}</strong></p>`).join('');
    const diceResult=dice.length?`<div class="dice-row settled">${dice.map(value=>dieHtml({value})).join('')}</div><p>Dice: ${dice.join(' + ')}${dice.length>1?` · Total: ${total}`:''}</p>`:'';
    const progress=objective?`<div class="summary-box"><strong>Progress: ${model.value} / ${model.target} ${escapeHtml(objective.label)}</strong></div>`:'';
    showModal(completed?(completionDialog.title||'MISSION OBJECTIVE COMPLETE'):title,`<div class="mission-roll-result">${completed?`<h3>${escapeHtml(objectiveDefinition.name)}</h3><p class="mission-complete-status">✓ ${escapeHtml(objective.label)}</p>`:''}${diceResult}${inputs}<p>${detail}</p>${progress}${completed?`<p>${escapeHtml(completionDialog.message||'Continue the battle.')}</p>`:''}</div><div class="wizard-actions"><button class="btn primary" data-close>${completed?'Continue the battle':'Continue'}</button></div>`);
  }

  function showMissionConfirmation(options,onConfirm){
    showModal(options.title||'Confirm Mission Action',`<p>${escapeHtml(options.description||'')}</p><p>${escapeHtml(options.message||'')}</p><div class="wizard-actions"><button class="btn ghost" data-close>${escapeHtml(options.cancelLabel||'Cancel')}</button><button class="btn primary" id="confirmMissionDialog">${escapeHtml(options.confirmLabel||'Confirm')}</button></div>`);
    $('#confirmMissionDialog').onclick=onConfirm;
  }

  function confirmMissionAction(){
    const action=objectiveDefinition.actions[0];
    const dice=action.operations.find(operation=>operation.type==='requestDiceRoll')?.dice;
    const diceLabel=dice?`${dice.count}D${dice.sides}`:'Dice';
    showMissionConfirmation({...action.confirmation,description:action.description,confirmLabel:`Roll ${diceLabel}`},async()=>{
      closeModal();
      const outcome=await runMissionEvent(()=>objectiveEngine.executeMissionAction(action.id,{turningPoint:state.turningPoint,phase:state.phase}));
      if(!outcome)return;
      save();log(`${action.label}: progress changed from ${outcome.changes[0].before} to ${outcome.changes[0].after}.`);render();showMissionResult(action.label.toUpperCase(),outcome);
    });
  }

  function showModal(title,content,onClose){
    const active=document.activeElement;
    if(active&&!modal.contains(active))modal._returnFocus=active;

    modal.classList.remove('combat-resolution-modal');
    modalBody.innerHTML=`<div class="modal-inner"><h2 id="modalTitle" tabindex="-1">${escapeHtml(title)}</h2>${content}</div>`;
    modal.setAttribute('aria-labelledby','modalTitle');
    modal.setAttribute('tabindex','-1');
    if(!modal.open)modal.showModal();
    modal._onClose=onClose;
    $$('[data-close]',modal).forEach(b=>b.onclick=closeModal);

    requestAnimationFrame(()=>{
      modal.scrollTop=0;
      modalBody.scrollTop=0;
      const target=$('#modalTitle',modal)||modal;
      try{target.focus({preventScroll:true});}catch{target.focus();}
    });
  }
  function closeModal(){
    missionDialogLocked=false;
    if(modal.open)modal.close();
    const cb=modal._onClose;
    const returnFocus=modal._returnFocus;
    modal._onClose=null;
    modal._returnFocus=null;
    if(cb)cb();
    if(returnFocus?.isConnected)requestAnimationFrame(()=>returnFocus.focus({preventScroll:true}));
  }
  modal.addEventListener('cancel',e=>{e.preventDefault();if(!missionDialogLocked)closeModal();});
  modal.addEventListener('keydown',event=>{
    if(event.key!=='Tab')return;
    const controls=$$('button:not([disabled]),input:not([disabled]),select:not([disabled]),[href],[tabindex]:not([tabindex="-1"])',modal).filter(element=>!element.hidden);
    if(!controls.length){event.preventDefault();modal.focus();return;}
    const first=controls[0],last=controls.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  });

  function showToast(text){toast.textContent=text;toast.hidden=false;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toast.hidden=true,6500);}
  function showGameMenu(){
    showModal('Game Menu',`<p>Open a reference screen without changing the guided play sequence, or begin a completely new game.</p>
      <div class="game-menu-grid">
        <button class="btn primary" data-game-view="play">Return to Guided Play</button>
        <button class="btn secondary" id="menuMissionDetails">Mission Details</button>
        <button class="btn secondary" data-game-view="mission">Mission & Map</button>
        <button class="btn secondary" data-game-view="roster">NPO Roster</button>
        <button class="btn secondary" data-game-view="player-roster">Player Roster</button>
        <button class="btn secondary" data-game-view="journal">Battle Journal</button>
        <button class="btn secondary" data-game-view="help">Help</button>
      </div>
      <div class="game-menu-session">
        <button class="btn ghost" id="menuExportSave">Export Save</button>
        <button class="btn ghost" id="menuImportSave">Import Save</button>
        <button class="btn danger" id="menuNewGame">Start New Game</button>
      </div>`);
    $$('[data-game-view]',modal).forEach(button=>button.onclick=()=>{
      state.tab=button.dataset.gameView;
      closeModal();
      save();
      render();
    });
    $('#menuMissionDetails').onclick=showMissionDetails;
    $('#menuExportSave').onclick=exportSave;
    $('#menuImportSave').onclick=()=>importInput.click();
    $('#menuNewGame').onclick=confirmNewGame;
  }

  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{localStorage.removeItem(STORAGE_KEY);state=initialState();state.screen='setup';objectiveEngine=null;objectiveDefinition=null;missionActivationStarts.clear();expandedRosterCategories=null;closeModal();save();render();};}
  function exportSave(){const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-solo-guide-save.json';a.click();URL.revokeObjectURL(a.href);}
  importInput.addEventListener('change',async()=>{const f=importInput.files?.[0];if(!f)return;try{const data=JSON.parse(await f.text());if(!isRecord(data))throw new Error();state=normalizeState(data);state.screen='game';const missionRecovered=recoverInvalidMission();await loadObjectiveMission();save();render();if(!missionRecovered)showToast('Save imported.');}catch{showToast('That file is not a valid Tomb World Solo Guide save.');}finally{importInput.value='';}});

  function bindCommon(){
    const versionBadge=$('.version');
    if(versionBadge) versionBadge.textContent=`v${APP_VERSION}`;
    gameMenuBtn.onclick=showGameMenu;
  }

  Promise.all([loadMissionPack(),loadPlayerManifest()])
    .then(async ([,manifest])=>{
      await loadObjectiveMission();
      recoverInvalidMission();
      const teams=manifest.teams||[];
      if(teams.length===1){
        state.playerTeamId=teams[0].id;
        await loadPlayerTeamData(teams[0].id);
      }else if(state.playerTeamId&&teams.some(team=>team.id===state.playerTeamId)){
        await loadPlayerTeamData(state.playerTeamId);
      }else{
        state.playerTeamId='';
        state.playerTeamFile='';
        playerTeamData=null;
      }
      state.missionState=normalizeMissionState(state.missionState,missionDefinition(state.missionId),state.tracker);
      render();
    })
    .catch(error=>{
      console.error(error);
      app.innerHTML=`<section class="card"><h2>Player operative data could not be loaded</h2><p>${escapeHtml(error.message)}</p><p>Run the app from a web server so it can load the mission and player-operative JSON files.</p></section>`;
      bindCommon();
    });
})();
