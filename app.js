(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
  const APP_VERSION = '8.6.44';
  const OPERATIVE_STATUS_PREFERENCE_KEY = 'tombWorldSoloGuide.showOperativeStatus';
  const BACKGROUND_MANIFEST_PATH = 'Assets/Images/Backgrounds/manifest.json';
  const BACKGROUND_IMAGE_PATH = 'Assets/Images/Backgrounds/';
  const WEAPON_RULE_HANDLERS = Object.freeze({
    hot:{mode:'automatic',phase:'after-weapon-use'},
    severe:{mode:'automatic',phase:'after-attack-roll'},
    'piercing-crits':{mode:'automatic',phase:'before-defense-roll'},
    stun:{mode:'automatic',phase:'after-attack-roll'},
    'seek-light':{mode:'tabletop-check',phase:'target-selection'},
    blast:{mode:'guided',phase:'secondary-targets'},
    torrent:{mode:'guided',phase:'secondary-targets'},
    shock:{mode:'guided',phase:'fight-resolution'},
    piercing:{mode:'automatic',phase:'before-defense-roll'},
    lethal:{mode:'automatic',phase:'attack-roll'},
    accurate:{mode:'automatic',phase:'attack-roll'},
    range:{mode:'tabletop-check',phase:'target-selection'}
  });
  const warnedUnsupportedWeaponRules=new Set();
  const warnedInvalidPiercingSummaries=new Set();
  const NPO_ACTION_TRANSITIONS = Object.freeze({
    AUTO_CONTINUE:'auto-continue',
    ACKNOWLEDGE:'acknowledge',
    COMPLETE_ACTIVATION:'complete-activation'
  });
  const ROUTINE_NPO_MOVEMENT_ACTIONS = new Set(['reposition','dash','charge','fall-back']);
  const {currentSaveVersion,migrateSaveDetailed,createPersistedSave,resetActiveBattle}=TombWorldPersistence;
  const DeadlyEncounters=TombWorldDeadlyEncounters;
  const EventEffects=TombWorldEventEffects;

let lastTouchEnd=0;
document.addEventListener('touchend',function(e){const now=Date.now();if(now-lastTouchEnd<=300){e.preventDefault();}lastTouchEnd=now;},{passive:false});
  const MAX_NPOS = 10;
  const MAX_TURNING_POINTS = 4;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const app = $('#app');
  const gameMenuBtn = $('#gameMenuBtn');
  const gameWorkspace = $('#gameWorkspace');
  const operativeStatusPanel = $('#operativeStatusPanel');
  const operativeStatusToggle = $('#operativeStatusToggle');
  const modal = $('#modal');
  const modalBody = $('#modalBody');
  const toast = $('#toast');
  const importInput = $('#importInput');
  const updateNotice = $('#updateNotice');
  const updateAppBtn = $('#updateAppBtn');
  const gameBackground = $('#gameBackground');
  const matchMediaProvider=window.matchMedia||globalThis.matchMedia;
  const desktopBackgroundMedia = matchMediaProvider.call(window,'(hover: hover) and (pointer: fine) and (min-width: 769px)');
  let backgroundManifest=[];
  let loadedBackgroundFilename=null;
  let loadingBackgroundFilename=null;
  const operativeStatusMedia=matchMediaProvider.call(window,'(min-width: 900px) and (orientation: landscape), (min-width: 900px) and (hover: hover) and (pointer: fine)');
  let showOperativeStatusPreference=localStorage.getItem(OPERATIVE_STATUS_PREFERENCE_KEY)==='true';
  let operativeStatusResizeTimer=null;

  async function loadBackgroundManifest(){
    try{
      const response=await fetch(BACKGROUND_MANIFEST_PATH,{cache:'no-store'});
      if(!response.ok)throw new Error(`Unable to load background manifest (${response.status})`);
      const data=await response.json();
      backgroundManifest=Array.isArray(data.landscape)?data.landscape.filter(filename=>/^Landscape-\d{2,}\.png$/.test(filename)):[];
      if(!backgroundManifest.length)throw new Error('Background manifest has no landscape images.');
    }catch(error){
      backgroundManifest=[];
      console.warn('[Background] Landscape backgrounds are unavailable; using the standard background.',error);
    }
    return backgroundManifest;
  }

  function selectRandomLandscapeBackground(){
    return backgroundManifest[Math.floor(Math.random()*backgroundManifest.length)]||null;
  }

  function isValidLandscapeBackground(filename){
    return backgroundManifest.includes(filename);
  }

  function ensureGameBackgroundSelection(sourceState=state){
    const current=sourceState.backgroundSelection?.landscape;
    if(isValidLandscapeBackground(current))return current;
    const selected=selectRandomLandscapeBackground();
    if(!selected)return null;
    if(current)console.warn(`[Background] Saved landscape "${current}" is unavailable; selected a replacement.`);
    sourceState.backgroundSelection={landscape:selected};
    return selected;
  }

  function updateGameBackground(){
    const filename=['setup','game'].includes(state.screen)&&isValidLandscapeBackground(state.backgroundSelection?.landscape)
      ? state.backgroundSelection.landscape
      : null;
    const shouldDisplay=Boolean(filename&&desktopBackgroundMedia.matches);
    if(!filename){
      document.documentElement.classList.remove('desktop-game-background');
      return;
    }
    if(loadedBackgroundFilename===filename){
      if(shouldDisplay){
        gameBackground.style.backgroundImage=`url("${BACKGROUND_IMAGE_PATH}${filename}")`;
        document.documentElement.classList.add('desktop-game-background');
      }else document.documentElement.classList.remove('desktop-game-background');
      return;
    }
    if(loadingBackgroundFilename===filename)return;
    document.documentElement.classList.remove('desktop-game-background');
    loadingBackgroundFilename=filename;
    const image=new Image();
    image.onload=()=>{
      loadingBackgroundFilename=null;
      loadedBackgroundFilename=filename;
      if(!['setup','game'].includes(state.screen)||state.backgroundSelection?.landscape!==filename||!desktopBackgroundMedia.matches)return;
      gameBackground.style.backgroundImage=`url("${BACKGROUND_IMAGE_PATH}${filename}")`;
      document.documentElement.classList.add('desktop-game-background');
    };
    image.onerror=()=>{
      loadingBackgroundFilename=null;
      if(state.backgroundSelection?.landscape===filename)console.warn(`[Background] Could not load "${filename}"; using the standard background.`);
    };
    image.src=`${BACKGROUND_IMAGE_PATH}${filename}`;
  }

  if(desktopBackgroundMedia.addEventListener)desktopBackgroundMedia.addEventListener('change',updateGameBackground);
  else desktopBackgroundMedia.addListener?.(updateGameBackground);

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
  let weaponRuleResumePending=false;
  let missionDialogLocked=false;
  let missionLoadRequestId=0;
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

  async function loadObjectiveMission(missionId=state.missionId){
    const requestId=++missionLoadRequestId;
    objectiveEngine=null;objectiveDefinition=null;
    const selectedMission=missionDefinition(missionId);
    const registered=missionManifest?.definitions?.some(entry=>entry.id===selectedMission?.number);
    if(!registered)return;
    try{
      const restoringRuntime=state.missionRuntime?.missionId===selectedMission.number;
      state.missionState=normalizeMissionState(state.missionState,selectedMission,state.tracker);
      const definition=await TombWorldMissionEngine.loadMissionDefinition(selectedMission.number);
      if(requestId!==missionLoadRequestId||state.missionId!==missionId)return;
      objectiveDefinition=definition;
      objectiveEngine=TombWorldMissionEngine.createMissionEngine({requestDiceRoll:animateMissionDice,requestNumericInput:requestMissionNumber,setOperativeInPlay});
      state.missionRuntime=objectiveEngine.restoreMissionRuntime(objectiveDefinition,state.missionRuntime,missionLifecycleContext());
      if(selectedMission.number==='04'){
        const destruction=objectiveEngine.getObjectiveValue('destructionPoints');
        state.missionState.destruction=destruction;
        if(destruction>=20&&!state.gameEnd)completeMission('victory');
      }
      if(missionEngine(selectedMission)?.type==='sabotage')objectiveEngine.setObjectiveValue('sabotagedFeatures',state.missionState?.completedFeatureIds?.length||0,missionLifecycleContext());
      if(missionEngine(selectedMission)?.type==='transponder')objectiveEngine.setObjectiveValue('transponderRecovered',state.missionState?.escaped?1:0,missionLifecycleContext());
      const configuredEngine=missionEngine(selectedMission), progressIds=configuredEngine?.progressIdsField&&state.missionState?.[configuredEngine.progressIdsField];
      if(configuredEngine?.objectiveId&&Array.isArray(progressIds))objectiveEngine.setObjectiveValue(configuredEngine.objectiveId,progressIds.length,missionLifecycleContext());
      if(!restoringRuntime)await executeMissionLifecycleHook('onMissionInitialized');
      if(requestId!==missionLoadRequestId||state.missionId!==missionId)return;
    }catch(error){
      if(requestId!==missionLoadRequestId||state.missionId!==missionId)return;
      objectiveEngine=null;objectiveDefinition=null;
      console.error('[MissionEngine] Mission automation unavailable.',{code:error.code||'LOAD_FAILED',missionId:selectedMission?.number,path:error.details?.path,reason:error.message});
      showToast('Mission automation could not be loaded. Track this mission manually.');
    }
  }

  let playerManifest=null;
  let playerTeamData=null;
  let playerTeamLoadRequestId=0;
  let loadedPlayerTeamId=null;
  let playerTeamLoadStatus='idle';
  let playerTeamLoadError=null;
  let setupNavigationInProgress=false;
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
  function canBuildPlayerRoster(){
    return Boolean(state.playerTeamId&&playerTeamLoadStatus==='loaded'&&loadedPlayerTeamId===state.playerTeamId&&playerTeamData);
  }
  async function loadPlayerTeamData(teamId=state.playerTeamId){
    const requestId=++playerTeamLoadRequestId;
    const entry=playerTeamEntry(teamId);
    if(!entry)throw new Error(`Kill Team "${teamId||'unknown'}" is not listed in manifest.json.`);
    playerTeamLoadStatus='loading';
    playerTeamLoadError=null;
    loadedPlayerTeamId=null;
    playerTeamData=null;
    render();
    try{
      const response=await fetch(`Player_Operatives/${entry.file}`,{cache:'no-store'});
      if(!response.ok)throw new Error(`Unable to load ${entry.file} (${response.status})`);
      const data=await response.json();
      validatePlayerTeamData(data,entry.file);
      if(requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId)return null;
      playerTeamData=data;
      loadedPlayerTeamId=teamId;
      state.playerTeamFile=entry.file;
      playerTeamLoadStatus='loaded';
      const operativeIds=new Set(data.operatives.map(operative=>operative.id));
      if((state.playerRoster||[]).some(id=>!operativeIds.has(id)))clearPlayerTeamDependentState();
      assignPlayerDisplayNumbers();
      save();
      render();
      return data;
    }catch(error){
      if(requestId!==playerTeamLoadRequestId||state.playerTeamId!==teamId)return null;
      playerTeamData=null;
      loadedPlayerTeamId=null;
      playerTeamLoadStatus='error';
      playerTeamLoadError=error;
      render();
      throw error;
    }
  }
  function validatePlayerTeamData(data,fileName){
    if(!data||!Array.isArray(data.operatives)||!data.operatives.length)throw new Error(`${fileName} has no operatives.`);
    const operativeIds=new Set(),categoryIds=new Set((data.rosterCategories||[]).map(category=>category.id));
    const requireStableIds=data.validation?.requireStableIds===true;
    const factionRuleIds=new Set();
    for(const rule of [...(data.factionRules||[]),...(data.strategicGambits||[])]){
      if(requireStableIds&&(!rule.id||factionRuleIds.has(rule.id)))throw new Error(`${fileName} has an invalid or duplicate faction rule ID.`);
      if(rule.id)factionRuleIds.add(rule.id);
    }
    for(const operative of data.operatives){
      if(!operative.id||operativeIds.has(operative.id))throw new Error(`${fileName} has an invalid or duplicate operative ID.`);
      operativeIds.add(operative.id);
      if(categoryIds.size&&!categoryIds.has(operative.category))throw new Error(`${fileName} references an unknown roster category.`);
      const weaponIds=new Set(),abilityIds=new Set();
      for(const weapon of operative.weapons||[]){
        if(!['ranged','melee'].includes(weapon.type))throw new Error(`${fileName} has an invalid weapon type.`);
        if(requireStableIds&&!weapon.id)throw new Error(`${fileName} has a weapon without a stable ID for ${operative.id}.`);
        if(weapon.id&&(weaponIds.has(weapon.id)))throw new Error(`${fileName} has a duplicate weapon ID for ${operative.id}.`);
        if(weapon.id)weaponIds.add(weapon.id);
      }
      for(const ability of operative.abilities||[]){
        if(requireStableIds&&(!ability.id||abilityIds.has(ability.id)))throw new Error(`${fileName} has an invalid or duplicate ability ID for ${operative.id}.`);
        if(ability.id)abilityIds.add(ability.id);
      }
    }
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
  function playerOperativeState(id){return state.playerOperativeStates?.[id]||{inPlay:true};}
  function isPlayerOperativeInPlay(id){return playerOperativeState(id).inPlay!==false;}
  function inPlayPlayerOperativeIds(){return (state.playerRoster||[]).filter(isPlayerOperativeInPlay);}
  function livingPlayerOperativeIds(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id));
  }
  function inPlayLivingPlayerOperativeIds(){return livingPlayerOperativeIds().filter(isPlayerOperativeInPlay);}
  function setOperativeInPlay(operation){
    if(operation.side==='npo'){
      const operative=state.roster.find(item=>item.id===operation.operativeId);
      if(!operative)return false;
      const currentlyInPlay=operative.battlefieldState==='deployed'&&operative.wounds>0;
      if(operation.inPlay===currentlyInPlay)return false;
      if(operation.inPlay){
        if(operative.wounds<=0||operative.offBoardReason!==operation.reason)return false;
        operative.battlefieldState='deployed';operative.deployed=true;delete operative.offBoardReason;
      }else{
        operative.battlefieldState='reserve';operative.deployed=false;operative.ready=false;
        if(operation.reason)operative.offBoardReason=operation.reason;
      }
      return true;
    }
    if(operation.side!=='player'||!(state.playerRoster||[]).includes(operation.operativeId))return false;
    const current=playerOperativeState(operation.operativeId);
    if(operation.inPlay===isPlayerOperativeInPlay(operation.operativeId))return false;
    if(operation.inPlay&&current.offBoardReason!==operation.reason)return false;
    state.playerOperativeStates[operation.operativeId]=operation.inPlay
      ? {inPlay:true}
      : {inPlay:false,...(operation.reason?{offBoardReason:operation.reason}:{})};
    if(!operation.inPlay){
      state.combatState=null;
      if(state.npoAttackTargetId===operation.operativeId)state.npoAttackTargetId=null;
    }
    state.playerReady=playerOperativesRemaining();
    return true;
  }
  function playerRosterLimits(){
    const maxRoster=Number(playerTeamData?.maxRoster??playerTeamData?.rosterSize??5);
    const minRoster=Number(playerTeamData?.minRoster??maxRoster);
    return {minRoster,maxRoster};
  }
  function playerRosterValidation(operativeIds=state.playerRoster||[]){
    const selected=operativeIds.map(playerDefinition).filter(Boolean);
    const rules=playerTeamData?.selectionRules||{};
    const {minRoster,maxRoster}=playerRosterLimits();
    const requirements=[];
    let valid=selected.length>=minRoster&&selected.length<=maxRoster;
    for(const category of playerTeamData?.rosterCategories||[]){
      const count=selected.filter(operative=>operative.category===category.id).length;
      const minimum=Number(category.requiredCount||0);
      const maximum=Number(category.maxCount??Infinity);
      if(minimum){requirements.push(`${category.label||category.id}: ${count} of ${minimum} required`);valid=valid&&count>=minimum;}
      if(Number.isFinite(maximum)){requirements.push(`${category.label||category.id}: ${count} of ${maximum} maximum`);valid=valid&&count<=maximum;}
    }
    const maxGunners=Number(rules.maxGunners??Infinity);
    const gunnerCount=selected.filter(operative=>operative.role==='Gunner').length;
    if(Number.isFinite(maxGunners)){requirements.push(`Maximum Gunners: ${gunnerCount} of ${maxGunners}`);valid=valid&&gunnerCount<=maxGunners;}
    const maxGravis=Number(rules.maxGravis??Infinity);
    const gravisCount=selected.filter(operative=>operative.gravis).length;
    if(Number.isFinite(maxGravis)){requirements.push(`Maximum Gravis: ${gravisCount} of ${maxGravis}`);valid=valid&&gravisCount<=maxGravis;}
    const requiredLeaderId=rules.leader?.operativeId;
    if(requiredLeaderId){
      const leaderCount=operativeIds.filter(id=>id===requiredLeaderId).length;
      const requiredLeaderCount=Number(rules.leader.count||1);
      requirements.push(`Required Leader: ${leaderCount} of ${requiredLeaderCount}`);
      valid=valid&&leaderCount===requiredLeaderCount;
    }
    const mandatoryTroopers=Number(rules.mandatoryTroopers||0);
    const trooperCount=selected.filter(operative=>operative.role==='Trooper').length;
    if(mandatoryTroopers){requirements.push(`Required Troopers: ${trooperCount} of ${mandatoryTroopers}`);valid=valid&&trooperCount>=mandatoryTroopers;}
    const selectionGroupMaximum=Number(rules.selectionGroupMax??Infinity);
    if(Number.isFinite(selectionGroupMaximum)){
      const groupCounts=new Map();
      selected.filter(operative=>operative.selectionGroup).forEach(operative=>groupCounts.set(operative.selectionGroup,(groupCounts.get(operative.selectionGroup)||0)+1));
      const conflictingGroups=[...groupCounts].filter(([,count])=>count>selectionGroupMaximum);
      requirements.push(conflictingGroups.length
        ? `Loadout choices: choose only one option for ${conflictingGroups.map(([group])=>group).join(', ')}`
        : 'Loadout choices: no mutually exclusive options selected');
      valid=valid&&!conflictingGroups.length;
    }
    requirements.push(minRoster===maxRoster?`Total Operatives: ${selected.length} of ${maxRoster}`:`Total Operatives: ${selected.length} of ${maxRoster} (minimum ${minRoster})`);
    return {valid,requirements};
  }
  function factionGuidanceHtml(kind='rules'){
    const entries=(kind==='gambits'?(playerTeamData?.strategicGambits||[]):(playerTeamData?.factionRules||[]))
      .filter(entry=>kind!=='gambits'||!Array.isArray(entry.turningPoints)||entry.turningPoints.includes(state.turningPoint));
    if(!entries.length)return '';
    const title=kind==='gambits'?'Faction Strategic Gambits':'Faction Rules Guidance';
    return `<section class="card faction-guidance"><h3>${title}</h3>${entries.map(entry=>`<div class="mission-rule"><strong>${escapeHtml(entry.name)}</strong>${entry.timing?`<small>${escapeHtml(entry.timing)}</small>`:''}<p>${escapeHtml(entry.text)}</p></div>`).join('')}<p class="muted">Resolve these rules on the tabletop; the Guide presents reminders without simulating positioning.</p></section>`;
  }
  function playerDisplayIdentity(id){
    const definition=playerDefinition(id);
    const sourceName=definition?.name||String(id);
    const match=definition?.officialName?sourceName.match(/^(.*?)\s+\d+(\s*\(.*\))?$/):null;
    return {
      groupName:definition?.officialName||match?.[1]||sourceName,
      baseName:match?.[1]||sourceName,
      suffix:match?.[2]||''
    };
  }
  function operativeName(operative,side){
    const isPlayer=side==='player';
    const id=isPlayer?operative:operative?.id;
    const definition=isPlayer?playerDefinition(id):npoDefinition(operative?.type);
    const identity=isPlayer?playerDisplayIdentity(id):null;
    const baseName=isPlayer?identity.baseName:(definition?.name||operative?.type||'NPO');
    const roster=isPlayer?(state.playerRoster||[]):(state.roster||[]);
    const matching=roster.filter(item=>isPlayer?playerDisplayIdentity(item).groupName===identity.groupName:(npoDefinition(item.type)?.name||item.type)===baseName);
    if(matching.length<=1)return `${baseName}${identity?.suffix||''}`;
    if(isPlayer){
      const storedNumber=state.playerDisplayNumbers?.[id];
      const index=matching.indexOf(id);
      return `${baseName} ${Number.isInteger(storedNumber)&&storedNumber>0?storedNumber:index>=0?index+1:1}${identity.suffix}`;
    }
    const index=matching.findIndex(item=>(isPlayer?item:item.id)===id);
    return `${baseName} ${index>=0?index+1:1}`;
  }

  function playerName(id){
    return operativeName(id,'player');
  }

  function playerTargetLabel(id){
    const name=playerName(id);
    const current=Math.max(0,Number(playerCurrentWounds(id)||0));
    const maximum=Number(playerDefinition(id)?.wounds);
    return Number.isFinite(maximum)&&maximum>0
      ? `${name} (${current}/${maximum} wounds)`
      : `${name} (${current} wounds)`;
  }

  function playerTargetAriaLabel(id){
    const name=playerName(id);
    const current=Math.max(0,Number(playerCurrentWounds(id)||0));
    const maximum=Number(playerDefinition(id)?.wounds);
    return Number.isFinite(maximum)&&maximum>0
      ? `Select ${name}, ${current} of ${maximum} wounds`
      : `Select ${name}, ${current} wounds`;
  }

  function allocateDisplayNumber(usedNumbers,preferredNumber){
    if(Number.isInteger(preferredNumber)&&preferredNumber>0&&!usedNumbers.has(preferredNumber)){
      usedNumbers.add(preferredNumber);
      return preferredNumber;
    }
    let displayNumber=1;
    while(usedNumbers.has(displayNumber))displayNumber++;
    usedNumbers.add(displayNumber);
    return displayNumber;
  }

  function assignPlayerDisplayNumbers(){
    const nameCounts={};
    (state.playerRoster||[]).forEach(id=>{
      const name=playerDisplayIdentity(id).groupName;
      if(name)nameCounts[name]=(nameCounts[name]||0)+1;
    });
    const usedDisplayNumbers={};
    state.playerDisplayNumbers={};
    (state.playerRoster||[]).forEach(id=>{
      const name=playerDisplayIdentity(id).groupName;
      if(!name||nameCounts[name]<=1)return;
      const used=usedDisplayNumbers[name]||(usedDisplayNumbers[name]=new Set());
      state.playerDisplayNumbers[id]=allocateDisplayNumber(used);
    });
  }

  let missions=[];
  let maps={};

  // Official NPO datacards, Tomb World Mission Pack pp. 6-7. Combat consumers use
  // these canonical profiles and delegate externally defined Core mechanics to tabletop play.
  const npoDefinitions = {
    'Canoptek Scarab Swarm': {
      id:'canoptek-scarab-swarm',name:'Canoptek Scarab Swarm',type:'Canoptek Scarab Swarm',faction:'Necron Host',physicalQuantity:3,move:6,apl:2,save:5,wounds:10,baseSize:40,
      keywords:['Necron Host','Necron','Canoptek','Scarab Swarm'],compatibilityBehavior:'Brawler',compatibilityAttack:{dice:5,hit:4,normal:2,crit:3},defaultWeaponId:'feeder-mandibles',loadoutOptions:null,
      rangedWeapons:[],meleeWeapons:[{id:'feeder-mandibles',name:'Feeder mandibles',type:'melee',attacks:5,hit:4,damage:{normal:1,critical:2},rules:[],ruleIds:[]}],
      actions:[],passiveRules:[],abilities:[],strategicRules:[],
      behavior:{summary:'Move towards the enemy to fight them, seeking cover on the way.',actions:['Fight','Charge the closest player operative via the shortest possible route','Reposition towards the closest player operative, to cover if possible','Dash towards the closest player operative, to cover if possible'],operatesHatches:true}
    },
    'Necron Warrior': {
      id:'necron-warrior',name:'Necron Warrior',type:'Necron Warrior',faction:'Necron Host',physicalQuantity:10,move:5,apl:2,save:4,wounds:9,baseSize:32,
      keywords:['Necron Host','Necron','Warrior'],compatibilityBehavior:'Marksman',compatibilityAttack:{dice:4,hit:4,normal:3,crit:4},defaultWeaponId:'gauss-flayer',loadoutOptions:[{id:'gauss-flayer',name:'Gauss flayer'},{id:'gauss-reaper',name:'Gauss reaper'}],
      rangedWeapons:[
        {id:'gauss-flayer',name:'Gauss flayer',type:'ranged',attacks:4,hit:4,damage:{normal:3,critical:4},rules:['Piercing 1'],ruleIds:['piercing']},
        {id:'gauss-reaper',name:'Gauss reaper',type:'ranged',attacks:4,hit:3,damage:{normal:3,critical:4},rules:['Range 8"','Piercing 1'],ruleIds:['range','piercing'],range:8}
      ],
      meleeWeapons:[{id:'combat-attachment',name:'Combat attachment',type:'melee',attacks:3,hit:4,damage:{normal:3,critical:4},rules:[],ruleIds:[]}],
      actions:[],passiveRules:[],abilities:[],strategicRules:[],
      behavior:{summary:'Move to an ideal position to shoot the enemy, but fight if unable to do anything else.',actions:['Fall Back','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission','Fight'],operatesHatches:true}
    },
    'Canoptek Tomb Crawler': {
      id:'canoptek-tomb-crawler',name:'Canoptek Tomb Crawler',type:'Canoptek Tomb Crawler',faction:'Canoptek Circle',physicalQuantity:2,move:5,apl:2,save:3,wounds:21,baseSize:50,
      keywords:['Canoptek Circle','Necron','Canoptek','Tomb Crawler'],compatibilityBehavior:'Guardian',compatibilityAttack:{dice:5,hit:4,normal:4,crit:5},defaultWeaponId:'twin-gauss-reapers',
      loadoutOptions:[{id:'twin-gauss-reapers',name:'Twin gauss reapers and claws'},{id:'transdimensional-isolator',name:'Transdimensional isolator and claws'}],
      rangedWeapons:[
        {id:'twin-gauss-reapers',name:'Twin gauss reapers',type:'ranged',profiles:[
          {id:'focused',name:'Focused',attacks:5,hit:4,damage:{normal:4,critical:5},rules:['Piercing 1','Severe'],ruleIds:['piercing','severe']},
          {id:'sweeping',name:'Sweeping',attacks:4,hit:4,damage:{normal:4,critical:5},rules:['Piercing 1','Severe','Torrent 1"'],ruleIds:['piercing','severe','torrent'],torrent:1,manualResolution:'Also attack each other target within 1 inch of the primary target. Resolve each attack separately. Do not attack the primary target twice.'}
        ]},
        {id:'transdimensional-isolator',name:'Transdimensional isolator',type:'ranged',attacks:5,hit:4,damage:{normal:5,critical:6},rules:['Dimensional Banishment'],ruleIds:['dimensional-banishment'],postAttackEffect:{id:'dimensional-banishment',trigger:{damageInflictedOrCriticalRetained:true,targetMustSurvive:true},roll:'2D6',comparison:'greater-than-post-damage-wounds',incapacitationPrecedence:true}}
      ],
      meleeWeapons:[{id:'claws',name:'Claws',type:'melee',attacks:4,hit:4,damage:{normal:4,critical:4},rules:[],ruleIds:[]}],actions:[],
      passiveRules:[
        {id:'weapon-sentinel',name:'Weapon Sentinel',targetValidity:{concealCannotUseLightTerrain:true,removeCoverSave:false},description:'With a Conceal order, this operative cannot use Light terrain to prevent selection as a valid target. It still retains any cover save.'},
        {id:'steadfast',name:'Steadfast',markerControlApl:3,overridesAplChangesForControl:true,description:'For marker-control determination only, this operative may be treated as having APL 3.'}
      ],
      abilities:[{id:'weapon-sentinel',name:'Weapon Sentinel',text:'With a Conceal order, this operative cannot use Light terrain to prevent selection as a valid target. It still retains any cover save.'},{id:'steadfast',name:'Steadfast',text:'For marker-control determination only, this operative may be treated as having APL 3.'}],strategicRules:[],
      behavior:{summary:'Fight if necessary; otherwise move to an ideal position to shoot when outside player control range.',actions:['Fight','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission'],operatesHatches:true,weaponGuidance:'Use Sweeping when it can hit at least two Player operatives.'}
    },
    'Geomancer': {
      id:'geomancer',name:'Geomancer',type:'Geomancer',faction:'Canoptek Circle',physicalQuantity:1,move:6,apl:3,save:3,wounds:14,baseSize:null,
      keywords:['Canoptek Circle','Necron','Leader','Cryptek','Geomancer'],compatibilityBehavior:'Support',compatibilityAttack:{dice:4,hit:3,normal:4,crit:5},defaultWeaponId:'tremorglaive',loadoutOptions:null,
      rangedWeapons:[{id:'tremorglaive',name:'Tremorglaive',type:'ranged',profiles:[
        {id:'part-matter',name:'Part matter',attacks:4,hit:3,damage:{normal:4,critical:5},rules:['Piercing 1','Piercing Crits 2'],ruleIds:['piercing','piercing-crits'],piercing:1,piercingCrits:2},
        {id:'quake',name:'Quake',attacks:5,hit:3,damage:{normal:1,critical:2},rules:['Blast 2"','Seek Light','Stun'],ruleIds:['blast','seek-light','stun'],blast:2,manualResolution:'Also attack each other target within 2 inches of the primary target. Resolve each attack separately. Do not attack the primary target twice.'}
      ]}],
      meleeWeapons:[{id:'tremorglaive-sweep',name:'Tremorglaive (sweep)',type:'melee',attacks:4,hit:4,damage:{normal:4,critical:5},rules:['Severe','Shock','Stun'],ruleIds:['severe','shock','stun']}],
      actions:[
        {id:'geomantic-disturbance',name:'Geomantic Disturbance',ap:1,target:{kind:'terrain-point',visible:true,range:8,affectedOperativesWithin:2},restrictions:{ordersExcluded:['Conceal'],actorOutsideEnemyControlRange:true},resolution:{manualTabletopSelection:true,dicePerTarget:'2D6',separateRollPerTarget:true,damage:'roll-minus-remaining-wounds-if-positive'},description:'1. Choose a terrain point the Geomancer can see within 8 inches. 2. Select every operative within 2 inches of that point. 3. Roll 2D6 separately for each. If the total is higher than its remaining wounds, deal damage equal to the difference. Cannot be used while the Geomancer has a Conceal order or is in enemy control range.'},
        {id:'canoptek-control',name:'Canoptek Control',ap:1,target:{side:'friendly',keywordsAll:['Canoptek Circle','Canoptek'],visible:true,range:6},restrictions:{actorOutsideEnemyControlRange:true,notCounteracting:true},freeAction:{ap:1,consumeTargetApl:false,startActivation:false,preserveActivatedState:true,obeyNormalRestrictions:true,maxMove:2,repositionWhollyWithin:2},description:'Choose a visible friendly Canoptek within 6 inches. It immediately performs one free 1 AP action. Any movement from that action is limited to 2 inches. Cannot be used while the Geomancer is in enemy control range or during a counteraction.'},
        {id:'molecular-breach',name:'Molecular Breach',ap:1,target:{side:'friendly',keywordsAll:['Canoptek Circle'],visible:true,range:6},restrictions:{actorOutsideEnemyControlRange:true},temporaryEffect:{id:'molecular-breach',scope:'target',trigger:'next-movement-action',consumeOnTrigger:true,persist:true,dashDistance:3,useMoveStatOtherwise:true,chargeGetsNoBonus:true,closeQuartersPassWalls:true,validPlacementRequired:true,enemyControlRangeAllowedOnlyForCharge:true},description:'Choose a visible friendly Canoptek Circle NPO within 6 inches. During its next movement action, remove it and set it up instead of moving normally. Use its Move distance, or 3 inches for Dash. In close quarters it can pass through Walls. Only Charge may end in enemy control range.'}
      ],passiveRules:[],abilities:[],strategicRules:[],behavior:{summary:'Support and control allies before attacking or repositioning.',actions:['Canoptek Control','Molecular Breach','Geomantic Disturbance','Shoot','Fight','Reposition','Dash'],operatesHatches:true}
    },
    'Canoptek Macrocyte Warrior': {
      id:'canoptek-macrocyte-warrior',name:'Canoptek Macrocyte Warrior',type:'Canoptek Macrocyte Warrior',faction:'Canoptek Circle',physicalQuantity:3,move:7,apl:2,save:4,wounds:7,baseSize:28,
      keywords:['Canoptek Circle','Necron','Canoptek','Macrocyte','Warrior'],compatibilityBehavior:'Sentinel',compatibilityAttack:{dice:4,hit:4,normal:2,crit:3},defaultWeaponId:'gauss-scalpel',loadoutOptions:[{id:'gauss-scalpel',name:'Gauss scalpel and claws & tail'},{id:'tesla-caster',name:'Tesla caster and claws & tail'}],
      rangedWeapons:[
        {id:'gauss-scalpel',name:'Gauss scalpel',type:'ranged',attacks:4,hit:4,damage:{normal:2,critical:3},rules:['Piercing 1'],ruleIds:['piercing']},
        {id:'tesla-caster',name:'Tesla caster',type:'ranged',profiles:[{id:'focused',name:'Focused',attacks:4,hit:4,damage:{normal:2,critical:3},rules:[],ruleIds:[]},{id:'living-lightning',name:'Living lightning',attacks:4,hit:4,damage:{normal:2,critical:3},rules:['Blast 2"'],ruleIds:['blast'],blast:2,manualResolution:'Also attack each other target within 2 inches of the primary target. Resolve each attack separately. Do not attack the primary target twice.'}]}
      ],
      meleeWeapons:[{id:'claws-and-tail',name:'Claws & tail',type:'melee',attacks:3,hit:4,damage:{normal:3,critical:4},rules:[],ruleIds:[]}],actions:[],
      passiveRules:[
        {id:'aggressive-defence',name:'Aggressive Defence',trigger:'incapacitated',sourceMustBeEnemyOperative:true,sourceRange:2,oncePerIncapacitation:true,roll:'D3',successThreshold:2,damage:1,resolveBeforeRemoval:true,description:'When an enemy operative within 2 inches incapacitates this operative, roll D3 before removal; on 2+, inflict exactly 1 damage on that enemy.'},
        {id:'expendable-construct',name:'Expendable Construct',excludeFromScoring:['escape','survive','incapacitated'],description:'Ignore this operative for scoring conditions that require operatives to escape, survive, or be incapacitated.'}
      ],abilities:[{id:'aggressive-defence',name:'Aggressive Defence',text:'When an enemy operative within 2 inches incapacitates this operative, roll D3 before removal; on 2+, inflict exactly 1 damage on that enemy.'},{id:'expendable-construct',name:'Expendable Construct',text:'Ignore this operative for scoring conditions that require operatives to escape, survive, or be incapacitated.'}],
      strategicRules:[{id:'a-ceaseless-scuttling',name:'A Ceaseless Scuttling',kind:'strategic-gambit',turningPointMinimum:2,requiresLivingFriendlyBelow:3,operativeType:'Canoptek Macrocyte Warrior',physicalLimit:3,setUp:{ready:true,order:'Conceal',location:'NPO drop zone'},manualResolution:true,description:'After Turning Point 1, if fewer than three friendly Warriors remain, another legally equipped Warrior may be set up ready with a Conceal order wholly within the NPO drop zone, subject to the three-model limit.'}],
      behavior:{summary:'Fight if necessary; otherwise move to an ideal position to shoot when outside player control range.',actions:['Fight','Shoot','Reposition to gain a valid unobscured target or better win the mission','Dash to gain a valid unobscured target or better win the mission'],operatesHatches:true,weaponGuidance:'Use Living Lightning when it can hit at least two Player operatives and no NPOs.'}
    },
    'Canoptek Macrocyte Accelerator': {
      id:'canoptek-macrocyte-accelerator',name:'Canoptek Macrocyte Accelerator',type:'Canoptek Macrocyte Accelerator',faction:'Canoptek Circle',physicalQuantity:1,move:7,apl:2,save:4,wounds:7,baseSize:null,
      keywords:['Canoptek Circle','Necron','Canoptek','Macrocyte','Accelerator'],compatibilityBehavior:'Support',compatibilityAttack:{dice:4,hit:4,normal:2,crit:3},defaultWeaponId:'spark',loadoutOptions:null,
      rangedWeapons:[{id:'spark',name:'Spark',type:'ranged',attacks:4,hit:4,damage:{normal:2,critical:3},rules:['Range 4"','Piercing 1'],ruleIds:['range','piercing'],range:4}],
      meleeWeapons:[{id:'claws-and-spark',name:'Claws & spark',type:'melee',attacks:3,hit:4,damage:{normal:3,critical:4},rules:['Lethal 5+','Stun'],ruleIds:['lethal','stun'],lethal:5}],
      actions:[
        {id:'overcharge',name:'Overcharge',ap:1,target:{side:'friendly',keywordsAll:['Canoptek Circle','Canoptek'],visible:true,range:3,excludeSelf:true},restrictions:{actorOutsideEnemyControlRange:true},temporaryAplModifier:{amount:1,expires:'end-of-target-next-activation',sourceUnique:true,persist:true},description:'Choose another visible friendly Canoptek within 3 inches. It gets 1 extra AP in its next activation (+1 APL). Cannot be used while the Accelerator is in enemy control range.'},
        {id:'cranial-overload',name:'Cranial Overload',ap:1,target:{side:'enemy',visible:true,range:3},restrictions:{actorOutsideEnemyControlRange:true},temporaryAplModifier:{amount:-1,minimumEffectiveApl:1,expires:'end-of-target-next-activation',sourceUnique:true,persist:true},description:'Choose a visible Player operative within 3 inches. It gets 1 fewer AP in its next activation, to a minimum of 1 (-1 APL). Cannot be used while the Accelerator is in enemy control range.'}
      ],passiveRules:[],abilities:[],strategicRules:[],behavior:{summary:'Improve an ally or disrupt an enemy before attacking or repositioning.',actions:['Overcharge','Cranial Overload','Shoot','Fight','Reposition','Dash'],operatesHatches:true}
    },
    'Canoptek Macrocyte Reanimator': {
      id:'canoptek-macrocyte-reanimator',name:'Canoptek Macrocyte Reanimator',type:'Canoptek Macrocyte Reanimator',faction:'Canoptek Circle',physicalQuantity:1,move:7,apl:2,save:4,wounds:7,baseSize:null,
      keywords:['Canoptek Circle','Necron','Canoptek','Macrocyte','Reanimator'],compatibilityBehavior:'Support',compatibilityAttack:{dice:4,hit:4,normal:3,crit:4},defaultWeaponId:'atomiser-beam',loadoutOptions:null,
      rangedWeapons:[{id:'atomiser-beam',name:'Atomiser beam',type:'ranged',attacks:4,hit:4,damage:{normal:3,critical:4},rules:['Range 6"','Lethal 5+'],ruleIds:['range','lethal'],range:6,lethal:5}],
      meleeWeapons:[{id:'claws-and-tail',name:'Claws & tail',type:'melee',attacks:4,hit:4,damage:{normal:3,critical:4},rules:[],ruleIds:[]}],
      actions:[{id:'nanoscarab-beam',name:'Nanoscarab Beam',ap:1,oncePerTurningPoint:true,target:{side:'friendly',keywordsAll:['Canoptek Circle'],visible:true,range:6,notIncapacitated:true,excludeReanimatedThisTurningPoint:true},restrictions:{actorOutsideEnemyControlRange:true},healing:{dice:'3D3',capAtMaximum:true,recordRolledAndRestored:true},description:'Choose a visible wounded Canoptek Circle NPO within 6 inches. Roll 3D3 and restore that many wounds, up to its maximum. It cannot target an incapacitated NPO or one saved by Reanimate this turning point.'}],
      passiveRules:[{id:'reanimate',name:'Reanimate',oncePerTurningPoint:true,optional:true,trigger:'another-friendly-would-be-incapacitated',target:{keywordsAll:['Canoptek Circle'],visible:true,range:6,excludeSelf:true},restrictions:{reanimatorAlive:true,bothOutsideEnemyControlRange:true,shootAttackCannotTargetReanimator:true},replacement:{wounds:1,preventIncapacitationForAction:true,freeDashAfterAction:true,dashEndsWithinSourceControlRange:true,endTargetActivationIfCurrent:true},temporaryAplModifiers:[{target:'source',amount:-1,expires:'end-of-next-activation'},{target:'saved-operative',amount:-1,expires:'end-of-next-activation'}],description:'Once per turning point, when another visible friendly Canoptek Circle operative within 6 inches would be incapacitated, it may remain at 1 wound and cannot be incapacitated again during that action. Afterward it may Dash for free, ending in the Reanimator control range. Both operatives suffer -1 APL through their next activation.'}],
      abilities:[{id:'reanimate',name:'Reanimate',text:'Once per turning point, optionally prevent another eligible friendly operative from being incapacitated, leave it at 1 wound, then resolve its free Dash and temporary APL penalties.'}],strategicRules:[],behavior:{summary:'Repair wounded allies before attacking or repositioning.',actions:['Nanoscarab Beam','Shoot','Fight','Reposition','Dash'],operatesHatches:true}
    }
  };

  // Official 2D6 table, Tomb World Mission Pack p. 5. The unavailable-model
  // instruction to use the next row is a tabletop contingency, not a fallback.
  const npoGenerationTable = [
    {min:2,max:3,type:'Canoptek Scarab Swarm',weaponIds:['feeder-mandibles']},
    {min:4,max:6,type:'Canoptek Macrocyte Warrior',weaponIds:['gauss-scalpel','tesla-caster']},
    {min:7,max:10,type:'Necron Warrior',weaponIds:['gauss-flayer','gauss-reaper']},
    {min:11,max:11,type:'Canoptek Tomb Crawler',weaponIds:['twin-gauss-reapers']},
    {min:12,max:12,type:'Canoptek Tomb Crawler',weaponIds:['transdimensional-isolator']}
  ];
  const MAX_PHYSICAL_NPOS = Object.values(npoDefinitions).reduce((total,definition)=>total+definition.physicalQuantity,0);
  const TOMB_CRAWLER_TYPE = 'Canoptek Tomb Crawler';
  const ISOLATOR_LOADOUT = 'transdimensional-isolator';

  // Physical Tomb World Event deck, Tomb World Mission Pack pp. 20-22.
  // Card-instance IDs preserve the printed duplicate weighting.
  const eventDefinitions = {
    'subjugation-glyphs':{title:'Subjugation Glyphs',text:'Randomly test eligible Player operatives without replacement. If a D6 is higher than an operative’s effective APL, subtract 1 from its APL.',execution:{type:'subjugation-glyphs'},lifecycle:'immediate',duration:'persistent',handlerId:'subjugation-glyphs',gameplayHooks:['effectivePlayerApl'],automationType:'automatic',priority:10},
    'transdimensional-relocation':{title:'Transdimensional Relocation',text:'Randomly select two Player operatives and swap their positions.',execution:{type:'transdimensional-relocation'},duration:'immediate',redrawIfImpossible:true},
    'my-will-be-done':{title:'My Will Be Done',text:'Until the end of the turning point, while an NPO is in the same room as the sarcophagus, its weapons have Accurate 1.',resultText:'Effect active until the end of this Turning Point. When an NPO attacks, the app will ask whether it is in the same room as the sarcophagus and automatically apply Accurate 1 if applicable.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'my-will-be-done',gameplayHooks:['effectiveWeapon'],automationType:'tabletop-answer',priority:20},
    'reanimation-protocols':{title:'Reanimation Protocols',text:'Until the end of the turning point, the first time each NPO would be incapacitated, roll one D6. On 4+, it reanimates with 1 wound.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'reanimation-protocols',gameplayHooks:['incapacitationCandidates'],automationType:'automatic',priority:10},
    'dark-of-the-tomb':{title:'Dark of the Tomb',text:'Until the end of the turning point, Player Shoot attack dice cannot be rerolled when the target is more than 8 inches away.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'dark-of-the-tomb',gameplayHooks:['attackRerolls'],automationType:'tabletop-answer',priority:10},
    'countertemporal-shifting':{title:'Countertemporal Shifting',text:'Until the end of the turning point, when an attack die would inflict 3 or more damage on an NPO, roll one D6. On 5+, subtract 1 damage from that die.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'countertemporal-shifting',gameplayHooks:['damagePackets'],automationType:'automatic',priority:30},
    'living-metal-flux':{title:'Living Metal Flux',text:'Each NPO that has lost any wounds regains D3+2 wounds.',execution:{type:'living-metal-flux'},duration:'immediate'},
    'maze-reforms':{title:'The Maze Reforms',text:'Close one breach and up to D3 open hatchways. If this cannot be resolved, draw another event card.',execution:{type:'maze-reforms'},duration:'immediate',redrawIfImpossible:true},
    'stirrings-of-horror':{title:'Stirrings of Horror',text:'Increase the Threat level by 1. If the Threat level is already 15, draw another event card instead.',execution:{type:'stirrings'},duration:'immediate',redrawIfImpossible:true},
    'chittering-drone':{title:'A Chittering Drone',text:'If a Canoptek Scarab Swarm has lost any wounds, it regains all lost wounds. Otherwise, set up one Ready Canoptek Scarab Swarm with a Conceal order using the placement instructions on the event card. If neither effect is possible, draw another event card.',execution:{type:'chittering-drone'},duration:'immediate',redrawIfImpossible:true},
    'awakened-warrior':{title:'Awakened Warrior',text:'Set up one Ready Necron Warrior with a Conceal order using the placement instructions on the event card. If no eligible Necron Warrior can be placed, draw another event card.',execution:{type:'awakened-warrior'},duration:'immediate',redrawIfImpossible:true}
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
    sabotage:()=>({completedFeatureIds:[],featureOpenDetails:{},featureTransactions:{}}),
    transponder:()=>({sites:{},carrierId:null,escaped:false,lastRoll:null}),
    destruction:()=>({destruction:0}),
    scout:()=>({awakenedRooms:{},scoutedRoomIds:[],scoutedByRoom:{}}),
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
      const completedIds=new Set(normalized.completedFeatureIds);
      normalized.featureOpenDetails=isRecord(raw.featureOpenDetails)
        ? Object.fromEntries(Object.entries(raw.featureOpenDetails).filter(([id,detail])=>completedIds.has(id)&&isRecord(detail)).map(([id,detail])=>[id,{...detail,featureId:id,isOpen:true}]))
        : {};
      normalized.featureTransactions=isRecord(raw.featureTransactions)?{...raw.featureTransactions}:{};
    }else if(engine.type==='transponder'){
      normalized.sites=isRecord(raw.sites)?Object.fromEntries(Object.entries(raw.sites).filter(([,value])=>['found','empty'].includes(value))):{};
      normalized.carrierId=typeof raw.carrierId==='string'&&raw.carrierId?raw.carrierId:null;
      normalized.escaped=Boolean(raw.escaped);
      normalized.lastRoll=isRecord(raw.lastRoll)?{...raw.lastRoll}:null;
    }else if(engine.type==='destruction'){
      normalized.destruction=Math.max(0,Number.isFinite(Number(raw.destruction))?Number(raw.destruction):Number(legacyTracker)||0);
    }else if(engine.type==='scout'){
      const roomIds=engine.rooms.map(room=>room.id), allowedRooms=new Set(roomIds), rosterIds=new Set(state.playerRoster||[]);
      normalized.awakenedRooms=isRecord(raw.awakenedRooms)?Object.fromEntries(Object.entries(raw.awakenedRooms).filter(([roomId,awakening])=>allowedRooms.has(roomId)&&isRecord(awakening)).map(([roomId,awakening])=>[roomId,{count:boundedInteger(awakening.count,0,5),operativeIds:normalizeIdList(awakening.operativeIds),placementConfirmed:Boolean(awakening.placementConfirmed)}])):{};
      normalized.scoutedRoomIds=Array.isArray(raw.scoutedRoomIds)
        ? normalizeIdList(raw.scoutedRoomIds,roomIds)
        : engine.rooms.slice(0,boundedInteger(legacyTracker,0,engine.rooms.length)).map(room=>room.id);
      normalized.scoutedByRoom=isRecord(raw.scoutedByRoom)?Object.fromEntries(Object.entries(raw.scoutedByRoom).filter(([roomId,operativeId])=>allowedRooms.has(roomId)&&rosterIds.has(operativeId))):{};
    }else if(engine.type==='regroup'){
      normalized.operativeChecks=isRecord(raw.operativeChecks)?{...raw.operativeChecks}:{};
      normalized.lastCheckedTurningPoint=boundedInteger(raw.lastCheckedTurningPoint,0,999);
    }
    return normalized;
  }

  const initialState = () => ({
    version:APP_VERSION, saveVersion:currentSaveVersion(), screen:'home', tab:'play', setupStep:0, missionId:null,
    backgroundSelection:null,
    setupChecks:{}, restlessTombEnabled:false, deadlyEncountersEnabled:false, deadlyEncountersState:DeadlyEncounters.emptyState(), roster:[], playerTeamId:'', playerTeamFile:'', playerRoster:[], playerDisplayNumbers:{}, playerRosterInitializedForTeamId:'', playerCount:0, playerReady:0, playerDeployed:false, turningPoint:0,
    threat:0, initiative:'player', phase:'setup', nextSide:'player', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, strategyPipeline:null, missionReadyContext:{sarcophagusControllers:0}, activationNumber:0,totalActivationsThisTP:0, playerActivated:0, npoActivated:0,
    activationHistory:[], playerActivatedIds:[], playerCasualtyIds:[], playerWounds:{}, playerOperativeStates:{}, reinforcementState:{turningPoint:0,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0,blockedByCapacity:0,blockedByInventory:0},
    gradeMilestone:null, tpStartThreat:0, tpStartGrade:0, tpStartDestroyedNpos:0, tpStartPlayerCasualties:0,
    npoAttackTargetId:null,
    npoAttackSummary:null, combatState:null, weaponRuleResolution:null, hotResolution:null, missionState:null, missionRuntime:null, missionActionContext:null, startingNpoGeneration:null,
    npoRuleState:{aplModifiers:[],pendingMovementEffects:[],oncePerTurningPoint:{},reanimatedTargetIds:[],incapacitationTriggers:[]},
    eventState:{available:eventDeck.map(card=>card.instanceId),used:[],active:[],transactions:{},playerAplModifiers:[],reanimationAttempts:{}}, gameEnd:null,
    finalResolution:{pending:false,turningPointEnded:false,cleanupComplete:false,battleEndHookComplete:false,resultLogged:false,invalidSaveCorrected:false}
  });

  const loadedSave = load();
  const pendingStoredMigration=loadedSave?.report?.requiresRegeneration?loadedSave:null;
  const loadedState=pendingStoredMigration?null:loadedSave?.state;
  let storedMigrationNoticeShown=false;
  let state;
  let startupInitializationError=null;
  try{state=normalizeState(loadedState || initialState());}
  catch(error){
    startupInitializationError=error;
    state=initialState();
    console.error('[Startup] Saved activation restoration failed; the stored save was preserved.',error);
  }
  let lastRenderedStepKey = null;
  let focusedRelocationInstanceId = null;
  let startingNpoTimer = null;
  let threatAdjustOpen = false;
  let expandedRosterCategories = null;
  const eventRedrawsInProgress = new Set();
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
    objectiveEngine?.refreshMissionContext(missionLifecycleContext());
  }

  function applyPlayerRoster(operativeIds){
    state.playerRoster=[...operativeIds];
    state.playerDisplayNumbers={};
    state.playerCount=state.playerRoster.length;
    state.playerReady=state.playerCount;
    state.playerCasualtyIds=[];
    state.playerOperativeStates=Object.fromEntries(state.playerRoster.map(id=>[id,{inPlay:true}]));
    initializePlayerWounds();
    state.playerActivatedIds=[];
    state.playerDeployed=false;
    objectiveEngine?.refreshMissionContext(missionLifecycleContext());
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
      const category=(playerTeamData?.rosterCategories||[]).find(candidate=>candidate.id===operative.category);
      const categoryMaximum=Number(category?.maxCount??Infinity);
      if(Number.isFinite(categoryMaximum)&&operatives.filter(candidate=>candidate.category===operative.category&&selected.has(candidate.id)).length>=categoryMaximum)continue;
      const maxGunners=Number(rules.maxGunners||Infinity);
      if(operative.role==='Gunner'&&operatives.filter(candidate=>candidate.role==='Gunner'&&selected.has(candidate.id)).length>=maxGunners)continue;
      const maxGravis=Number(rules.maxGravis||1);
      if(operative.gravis&&operatives.filter(candidate=>candidate.gravis&&selected.has(candidate.id)).length>=maxGravis)continue;
      const selectionGroupMaximum=Number(rules.selectionGroupMax??Infinity);
      if(operative.selectionGroup&&Number.isFinite(selectionGroupMaximum)&&operatives.filter(candidate=>candidate.selectionGroup===operative.selectionGroup&&selected.has(candidate.id)).length>=selectionGroupMaximum)continue;
      selected.add(operative.id);
    }
    applyPlayerRoster(selected);
  }

  function save(){
    if(objectiveEngine)state.missionRuntime=objectiveEngine.getMissionRuntime();
    state.version=APP_VERSION;
    state.saveVersion=currentSaveVersion();
    try{localStorage.setItem(STORAGE_KEY,JSON.stringify(createPersistedSave(state)));return true;}
    catch{showToast('The game could not be saved. Check available browser storage.');return false;}
  }
  function load(){
    try{
      const saved=localStorage.getItem(STORAGE_KEY);
      if(!saved)return null;
      const parsed=JSON.parse(saved);
      return migrateSaveDetailed(parsed,npoDefinitions);
    }catch(error){
      console.warn('[Persistence] Saved game could not be loaded; the original save was left unchanged.',error);
      return null;
    }
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
    if(Array.isArray(raw.roster)){
      const validation=validateNpoRoster(raw.roster);
      if(!validation.valid)throw new Error(`Saved NPO roster is invalid: ${validation.errors.join(' ')}`);
    }
    const base=initialState(), merged={...base,...raw};
    if(!['home','help','setup','game'].includes(merged.screen))merged.screen='home';
    if(!['play','mission','roster','player-roster','journal','help'].includes(merged.tab))merged.tab='play';
    const beyondTurningPointLimit=Number(raw.turningPoint)>MAX_TURNING_POINTS;
    const invalidTurningPoint=beyondTurningPointLimit&&!['victory','defeat'].includes(raw.gameEnd);
    merged.turningPoint=Math.min(boundedInteger(raw.turningPoint,0,999),MAX_TURNING_POINTS);
    merged.threat=boundedInteger(raw.threat,0,15);
    merged.restlessTombEnabled=raw.restlessTombEnabled===true;
    merged.deadlyEncountersEnabled=raw.deadlyEncountersEnabled===true;
    merged.deadlyEncountersState=DeadlyEncounters.normalizeState(raw.deadlyEncountersState);
    merged.roster=Array.isArray(raw.roster)?raw.roster.map(normalizeNpo).filter(Boolean):[];
    const usedDisplayNumbers={};
    merged.roster.forEach(npo=>{
      const definition=npoDefinition(npo.type);
      if(definition?.physicalQuantity<=1){npo.displayNumber=null;return;}
      const used=usedDisplayNumbers[npo.type]||(usedDisplayNumbers[npo.type]=new Set());
      const preferredNumber=Number.isInteger(npo.displayNumber)?npo.displayNumber:null;
      npo.displayNumber=allocateDisplayNumber(used,preferredNumber);
    });
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
    const importedFinalResolution=isRecord(raw.finalResolution)?raw.finalResolution:{};
    merged.finalResolution={
      pending:Boolean(importedFinalResolution.pending),
      turningPointEnded:Boolean(importedFinalResolution.turningPointEnded),
      cleanupComplete:Boolean(importedFinalResolution.cleanupComplete),
      battleEndHookComplete:Boolean(importedFinalResolution.battleEndHookComplete),
      resultLogged:Boolean(importedFinalResolution.resultLogged),
      invalidSaveCorrected:Boolean(importedFinalResolution.invalidSaveCorrected)
    };
    if(invalidTurningPoint){
      merged.finalResolution.pending=true;
      merged.finalResolution.turningPointEnded=true;
      merged.finalResolution.cleanupComplete=true;
      if(!merged.finalResolution.invalidSaveCorrected){
        merged.journal.unshift({time:new Date().toISOString(),text:`Battle corrected to the ${MAX_TURNING_POINTS}-Turning-Point limit; mission and roster progress were preserved.`});
        merged.finalResolution.invalidSaveCorrected=true;
      }
    }
    merged.newIds=normalizeIdList(raw.newIds,merged.roster.map(npo=>npo.id));
    const importedReinforcements=isRecord(raw.reinforcementState)?raw.reinforcementState:{};
    const reinforcementIds=normalizeIdList(importedReinforcements.operativeIds,merged.roster.map(npo=>npo.id));
    const blockedReinforcementIds=normalizeIdList(importedReinforcements.blockedOperativeIds,merged.roster.map(npo=>npo.id))
      .filter(id=>!reinforcementIds.includes(id)&&merged.roster.some(npo=>npo.id===id&&npo.battlefieldState==='reserve'));
    const reinforcementStatus=['idle','placement','complete','blocked'].includes(importedReinforcements.status)?importedReinforcements.status:'idle';
    const blockedReinforcements=boundedInteger(importedReinforcements.blocked,0,MAX_NPOS);
    const hasCapacityReason=Number.isFinite(Number(importedReinforcements.blockedByCapacity));
    const hasInventoryReason=Number.isFinite(Number(importedReinforcements.blockedByInventory));
    const hasBlockedReasons=hasCapacityReason||hasInventoryReason;
    const deployedCount=merged.roster.filter(npo=>npo.battlefieldState==='deployed'&&npo.wounds>0).length;
    const legacyCapacityBlocked=Math.min(blockedReinforcements,Math.max(0,reinforcementIds.length+blockedReinforcements-Math.max(0,MAX_NPOS-deployedCount)));
    const blockedByCapacity=hasBlockedReasons
      ? hasCapacityReason?boundedInteger(importedReinforcements.blockedByCapacity,0,blockedReinforcements):Math.max(0,blockedReinforcements-boundedInteger(importedReinforcements.blockedByInventory,0,blockedReinforcements))
      : legacyCapacityBlocked;
    const blockedByInventory=hasInventoryReason?boundedInteger(importedReinforcements.blockedByInventory,0,blockedReinforcements-blockedByCapacity):blockedReinforcements-blockedByCapacity;
    merged.reinforcementState={
      turningPoint:boundedInteger(importedReinforcements.turningPoint,0,merged.turningPoint),
      status:reinforcementStatus==='placement'&&!reinforcementIds.length?'idle':reinforcementStatus,
      operativeIds:reinforcementIds,
      blockedOperativeIds:blockedReinforcementIds,
      blocked:blockedReinforcements,
      blockedByCapacity,
      blockedByInventory
    };
    if(merged.reinforcementState.status==='placement'){
      merged.reinforcementState.operativeIds.forEach(id=>{
        const npo=merged.roster.find(item=>item.id===id);
        if(!npo||npo.reinforcement?.placementConfirmed)return;
        npo.battlefieldState='reserve';npo.deployed=false;npo.dormant=false;npo.ready=false;
      });
    }
    merged.activationHistory=Array.isArray(raw?.activationHistory)?raw.activationHistory:[];
    merged.playerActivatedIds=Array.isArray(raw?.playerActivatedIds)?raw.playerActivatedIds:[];
    merged.playerCasualtyIds=Array.isArray(raw?.playerCasualtyIds)?raw.playerCasualtyIds:[];
    merged.playerWounds=raw?.playerWounds&&typeof raw.playerWounds==='object'?{...raw.playerWounds}:{};
    merged.combatState=isRecord(raw.combatState)&&raw.combatState.side==='player'&&isRecord(raw.combatState.stage)
      ? {side:'player',stage:normalizePendingAttackResultLists(raw.combatState.stage)}
      : null;
    merged.weaponRuleResolution=normalizeMultiTargetAttackSequence(raw.weaponRuleResolution,
      raw.lastActivation?.combatDraft?.profile||raw.combatState?.stage?.shootCombatDraft?.profile);
    merged.hotResolution=normalizeHotResolution(raw.hotResolution);
    merged.playerRoster=Array.isArray(raw?.playerRoster)?raw.playerRoster:[];
    merged.playerDisplayNumbers=isRecord(raw?.playerDisplayNumbers)
      ? Object.fromEntries(Object.entries(raw.playerDisplayNumbers).filter(([id,number])=>merged.playerRoster.includes(id)&&Number.isInteger(number)&&number>0))
      : {};
    const importedPlayerStates=isRecord(raw?.playerOperativeStates)?raw.playerOperativeStates:{};
    merged.playerOperativeStates=Object.fromEntries(merged.playerRoster.map(id=>{
      const imported=isRecord(importedPlayerStates[id])?importedPlayerStates[id]:null;
      return [id,imported?.inPlay===false
        ? {...imported,inPlay:false,...(typeof imported.offBoardReason==='string'&&imported.offBoardReason?{offBoardReason:imported.offBoardReason}:{})}
        : {...(imported||{}),inPlay:true}];
    }));
    merged.setupChecks=raw?.setupChecks&&!Array.isArray(raw.setupChecks)&&typeof raw.setupChecks==='object'?{...raw.setupChecks}:{};
    const importedRuleState=isRecord(raw?.npoRuleState)?raw.npoRuleState:{};
    merged.npoRuleState={
      aplModifiers:Array.isArray(importedRuleState.aplModifiers)?importedRuleState.aplModifiers.filter(isRecord).map(modifier=>({...modifier})):[],
      pendingMovementEffects:Array.isArray(importedRuleState.pendingMovementEffects)?importedRuleState.pendingMovementEffects.filter(isRecord).map(effect=>({...effect})):[],
      oncePerTurningPoint:isRecord(importedRuleState.oncePerTurningPoint)?{...importedRuleState.oncePerTurningPoint}:{},
      reanimatedTargetIds:normalizeIdList(importedRuleState.reanimatedTargetIds),
      incapacitationTriggers:normalizeIdList(importedRuleState.incapacitationTriggers)
    };
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
        initiativeReason:raw.strategyData.initiativeReason||(raw?.turningPoint===1?'Turning Point 1':'Threat was 0 when initiative was determined'),
        viewStep:['actions','events','review'].includes(raw.strategyData.viewStep)
          ? raw.strategyData.viewStep
          : raw.strategyData.eventPending
            ? 'events'
            : raw.reinforcementState?.status==='placement'
              ? 'review'
              : 'actions'
      };
    }else merged.strategyData=null;
    const importedEvents=isRecord(raw.eventState)?raw.eventState:{};
    const validInstances=new Set(eventDeck.map(card=>card.instanceId));
    const available=Array.isArray(importedEvents.available)?normalizeIdList(importedEvents.available,validInstances):eventDeck.map(card=>card.instanceId);
    const used=normalizeIdList(importedEvents.used,validInstances).filter(id=>!available.includes(id));
    const normalizedActive=Array.isArray(importedEvents.active)?importedEvents.active.map(event=>{
      if(!isRecord(event))return null;
      const deckRecord=eventDeck.find(card=>card.instanceId===event.instanceId);
      const definitionId=event.definitionId||deckRecord?.definitionId;
      return eventDefinitions[definitionId]?{...event,definitionId}:null;
    }).filter(event=>event&&event.expiresAfterTurningPoint>=merged.turningPoint&&(!invalidTurningPoint||!Number.isFinite(Number(event.startedTurningPoint))||event.startedTurningPoint<=MAX_TURNING_POINTS)):[];
    merged.eventState={
      available,
      used,
      active:normalizedActive,
      transactions:isRecord(importedEvents.transactions)?{...importedEvents.transactions}:{},
      playerAplModifiers:Array.isArray(importedEvents.playerAplModifiers)?importedEvents.playerAplModifiers.filter(isRecord).map(item=>({...item})):[],
      reanimationAttempts:isRecord(importedEvents.reanimationAttempts)?{...importedEvents.reanimationAttempts}:{}
    };
    if(invalidTurningPoint)merged.eventState.active=merged.eventState.active.filter(event=>event.expiresAfterTurningPoint>MAX_TURNING_POINTS);
    const livingImportedPlayers=merged.playerRoster.filter(id=>merged.playerOperativeStates[id]?.inPlay!==false&&!merged.playerCasualtyIds.includes(id)).length;
    merged.missionReadyContext=raw?.missionReadyContext&&typeof raw.missionReadyContext==='object'
      ? {sarcophagusControllers:normalizeSarcophagusControllers(raw.missionReadyContext.sarcophagusControllers,livingImportedPlayers)}
      : {sarcophagusControllers:0};
    merged.strategyPipeline=isRecord(raw.strategyPipeline)
      ? {...raw.strategyPipeline,completed:Array.isArray(raw.strategyPipeline.completed)?raw.strategyPipeline.completed:[]}
      : null;
    merged.gameEnd=['victory','defeat'].includes(raw?.gameEnd)?raw.gameEnd:null;
    const savedMission=missionDefinition(merged.missionId);
    merged.missionState=normalizeMissionState(raw?.missionState,savedMission,raw?.tracker);
    for(const id of merged.missionState?.escapedIds||[]){
      if(merged.playerRoster.includes(id))merged.playerOperativeStates[id]={inPlay:false,offBoardReason:'escaped'};
    }
    const legacyEscapeCount=Number(raw?.missionRuntime?.missionId)==1&&!merged.missionState?.escapedIds?.length
      ? boundedInteger(raw?.missionRuntime?.objectives?.escapedOperatives?.value,0,merged.playerRoster.length)
      : 0;
    if(legacyEscapeCount)merged.missionState.legacyEscapedCount=legacyEscapeCount;
    if(merged.turningPoint>0){
      const unavailable=new Set([...merged.playerActivatedIds,...merged.playerCasualtyIds]);
      merged.playerReady=merged.playerRoster.filter(id=>merged.playerOperativeStates[id]?.inPlay!==false&&!unavailable.has(id)).length;
    }
    merged.completed=Boolean(merged.gameEnd);
    merged.playerCount=merged.playerRoster.length;
    if(isRecord(merged.lastActivation)&&typeof merged.lastActivation.npoId==='string'){
      const activationNpo=merged.roster.find(npo=>npo.id===merged.lastActivation.npoId),definition=npoDefinition(activationNpo?.type);
      const effective=Number(merged.lastActivation.effectiveApl??definition?.apl??0),remaining=Math.max(0,Number(merged.lastActivation.remainingAp??effective));
      merged.lastActivation={
        ...merged.lastActivation,activationId:merged.lastActivation.activationId||activationIdFromState(merged,'npo',merged.lastActivation.npoId),
        baseApl:Number(merged.lastActivation.baseApl??definition?.apl??effective),effectiveApl:effective,
        startingAp:Number(merged.lastActivation.startingAp??effective),remainingAp:remaining,
        actionSequence:Number(merged.lastActivation.actionSequence??merged.lastActivation.resolvedActions?.length??0),
        completedActionIds:Array.isArray(merged.lastActivation.completedActionIds)?merged.lastActivation.completedActionIds:[],
        resolvedActions:Array.isArray(merged.lastActivation.resolvedActions)?merged.lastActivation.resolvedActions:[],
        decisionPass:Math.max(1,Number(merged.lastActivation.decisionPass||1)),
        declinedActionIds:Array.isArray(merged.lastActivation.declinedActionIds)?merged.lastActivation.declinedActionIds:[],
        declinedMovementIntentIds:Array.isArray(merged.lastActivation.declinedMovementIntentIds)?merged.lastActivation.declinedMovementIntentIds:[],
        movementIntent:isRecord(merged.lastActivation.movementIntent)&&typeof merged.lastActivation.movementIntent.id==='string'
          ? {...merged.lastActivation.movementIntent}
          : null,
        pendingFollowUpAction:isRecord(merged.lastActivation.pendingFollowUpAction)
          &&typeof merged.lastActivation.pendingFollowUpAction.actionId==='string'
          &&merged.lastActivation.pendingFollowUpAction.activationId===merged.lastActivation.activationId
          ? {...merged.lastActivation.pendingFollowUpAction}
          : null,
        questionHistory:Array.isArray(merged.lastActivation.questionHistory)
          ? merged.lastActivation.questionHistory.filter(item=>isRecord(item)&&typeof item.action==='string').map(item=>({...item}))
          : [],
        pendingAction:isRecord(merged.lastActivation.pendingAction)
          &&typeof merged.lastActivation.pendingAction.id==='string'
          &&typeof merged.lastActivation.pendingAction.name==='string'
          &&Number.isFinite(Number(merged.lastActivation.pendingAction.apCost))
          ? {...merged.lastActivation.pendingAction,apCost:Number(merged.lastActivation.pendingAction.apCost),decisionPass:Math.max(1,Number(merged.lastActivation.pendingAction.decisionPass||merged.lastActivation.decisionPass||1))}
          : null,
        currentContext:{inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null,...(isRecord(merged.lastActivation.currentContext)?merged.lastActivation.currentContext:{})},
        awaitingActionResult:isRecord(merged.lastActivation.awaitingActionResult)
          &&typeof merged.lastActivation.awaitingActionResult.id==='string'
          &&typeof merged.lastActivation.awaitingActionResult.name==='string'
          &&Number.isFinite(Number(merged.lastActivation.awaitingActionResult.apCost))
          &&Number.isFinite(Number(merged.lastActivation.awaitingActionResult.apBefore))
          &&Number.isFinite(Number(merged.lastActivation.awaitingActionResult.apRemaining))
          ? {...merged.lastActivation.awaitingActionResult}
          : null,
        attackPerformed:Boolean(merged.lastActivation.attackPerformed||merged.lastActivation.resolvedActions?.some(action=>['shoot','fight'].includes(action.id))),
        fightPerformed:Boolean(merged.lastActivation.fightPerformed||merged.lastActivation.resolvedActions?.some(action=>action.id==='fight')),
        committed:Boolean(merged.lastActivation.committed),completed:Boolean(merged.lastActivation.completed||merged.lastActivation.committed)
      };
    }
    if(merged.phase==='strategy'&&merged.strategyStage==='initiative'){
      const resolvedSide=merged.strategyData?.suggestedInitiative==='npo'?'npo':'player';
      merged.initiative=resolvedSide;
      merged.phase='firefight';
      merged.strategyStage=null;
      merged.nextSide=resolvedSide;
    }
    if(invalidTurningPoint){
      merged.phase='battle-resolution';
      merged.strategyStage=null;merged.strategyData=null;merged.strategyPipeline=null;
      merged.activeNpoId=null;merged.combatState=null;merged.npoAttackTargetId=null;merged.npoAttackSummary=null;
      merged.newIds=[];merged.activationHistory=[];merged.playerActivatedIds=[];
      merged.reinforcementState={turningPoint:MAX_TURNING_POINTS,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0,blockedByCapacity:0,blockedByInventory:0};
    }
    if(Array.isArray(raw.roster)){
      const validation=validateNpoRoster(merged.roster);
      if(!validation.valid)throw new Error(`Saved NPO roster is invalid: ${validation.errors.join(' ')}`);
    }
    return merged;
  }
  function npoDefinition(type){return npoDefinitions[type]||null;}
  function uniqueNpoInstances(roster=state.roster){
    const seen=new Set();
    return (Array.isArray(roster)?roster:[]).filter(npo=>isRecord(npo)&&typeof npo.id==='string'&&npo.id&&!seen.has(npo.id)&&seen.add(npo.id));
  }
  function npoInventory(roster=state.roster){
    const used=Object.fromEntries(Object.keys(npoDefinitions).map(type=>[type,0]));
    uniqueNpoInstances(roster).forEach(npo=>{if(npoDefinitions[npo.type])used[npo.type]++;});
    return Object.fromEntries(Object.entries(npoDefinitions).map(([type,definition])=>[type,{
      maximum:definition.physicalQuantity,used:used[type],remaining:Math.max(0,definition.physicalQuantity-used[type])
    }]));
  }
  function lowestAvailableNpoInstances(type,quantity,allocationContext={}){
    const definition=npoDefinition(type),roster=Array.isArray(allocationContext.roster)?allocationContext.roster:state.roster;
    if(!definition||!Number.isInteger(quantity)||quantity<1)return [];
    const allocated=uniqueNpoInstances(roster).filter(npo=>npo.type===type);
    if(definition.physicalQuantity===1)return allocated.length?[]:[{id:`${definition.id}-1`,displayNumber:null}];
    const allocatedIds=new Set(allocated.map(npo=>npo.id));
    const allocatedNumbers=new Set(allocated.map(npo=>Number(npo.displayNumber)).filter(Number.isInteger));
    const available=[];
    for(let displayNumber=1;displayNumber<=definition.physicalQuantity;displayNumber++){
      const id=`${definition.id}-${displayNumber}`;
      if(!allocatedIds.has(id)&&!allocatedNumbers.has(displayNumber))available.push({id,displayNumber:definition.physicalQuantity>1?displayNumber:null});
    }
    return available.slice(0,quantity);
  }
  function validateNpoRoster(roster=state.roster){
    const errors=[], ids=new Set(), displayNumbers={},counts=Object.fromEntries(Object.keys(npoDefinitions).map(type=>[type,0]));
    if(!Array.isArray(roster))return {valid:false,errors:['NPO roster must be an array.']};
    roster.forEach((npo,index)=>{
      if(!isRecord(npo)){errors.push(`NPO ${index+1} is invalid.`);return;}
      if(typeof npo.id!=='string'||!npo.id)errors.push(`NPO ${index+1} is missing an instance ID.`);
      else if(ids.has(npo.id))errors.push(`Duplicate NPO instance ID: ${npo.id}.`);
      else ids.add(npo.id);
      const definition=npoDefinition(npo.type);
      if(!definition){errors.push(`Unsupported NPO type: ${npo.type||'missing'}.`);return;}
      counts[npo.type]++;
      if(!npo.name)errors.push(`NPO ${npo.id||index+1} is missing a name.`);
      if(definition.physicalQuantity>1){
        const used=displayNumbers[npo.type]||(displayNumbers[npo.type]=new Set());
        if(!Number.isInteger(npo.displayNumber)||npo.displayNumber<1)errors.push(`${definition.name} is missing a display number.`);
        else if(used.has(npo.displayNumber))errors.push(`${definition.name} has duplicate display number ${npo.displayNumber}.`);
        else used.add(npo.displayNumber);
      }
      if(definition.loadoutOptions&&!definition.loadoutOptions.some(option=>option.id===npo.weaponId))errors.push(`${definition.name} has an unsupported loadout.`);
    });
    Object.entries(counts).forEach(([type,count])=>{
      const definition=npoDefinitions[type];
      const scuttlingException=type==='Canoptek Macrocyte Warrior'
        && roster.filter(npo=>npo?.type===type&&npo.wounds>0).length<=definition.physicalQuantity
        && count-definition.physicalQuantity<=roster.filter(npo=>npo?.type===type&&npo.createdBy==='a-ceaseless-scuttling').length;
      if(count>definition.physicalQuantity&&!scuttlingException)errors.push(`${type} exceeds its physical quantity of ${definition.physicalQuantity}.`);
    });
    const excessIsScuttlingHistory=ids.size>MAX_PHYSICAL_NPOS
      && ids.size-MAX_PHYSICAL_NPOS<=roster.filter(npo=>npo?.createdBy==='a-ceaseless-scuttling').length;
    if(ids.size>MAX_PHYSICAL_NPOS&&!excessIsScuttlingHistory)errors.push(`Allocated NPOs exceed the ${MAX_PHYSICAL_NPOS}-model Tomb World inventory.`);
    if(roster.filter(npo=>npo?.type===TOMB_CRAWLER_TYPE&&npo.weaponId===ISOLATOR_LOADOUT).length>1)errors.push('Only one Tomb Crawler can have a transdimensional isolator.');
    return {valid:errors.length===0,errors,inventory:npoInventory(roster)};
  }
  function commitNpoRoster(candidate,action='update the NPO roster'){
    const validation=validateNpoRoster(candidate);
    if(validation.valid){state.roster=candidate;return true;}
    console.warn(`[NPO inventory] Could not ${action}.`,validation.errors);
    showToast(validation.errors[0]);
    return false;
  }
  function npoWeapon(definition,weaponId){
    return [...(definition?.rangedWeapons||[]),...(definition?.meleeWeapons||[])].find(weapon=>weapon.id===weaponId)||null;
  }
  function weaponProfiles(weapon){
    if(!weapon)return [];
    return (weapon.profiles||[weapon]).map(profile=>({...profile,type:weapon.type,weaponId:weapon.id,weaponName:weapon.name}));
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
    const lethal=(profile?.rules||[]).map(String).map(rule=>rule.match(/Lethal\s*(\d)\+/i)).find(Boolean);
    return {
      dice:Number(profile?.attacks||0),hit:Number(profile?.hit||0),
      critThreshold:Number(lethal?.[1]||6),
      normal:Number(profile?.damage?.normal||0),crit:Number(profile?.damage?.critical||0),
      ap:Number(piercing?.[1]||0),
      rules:[...(profile?.rules||[])],ruleIds:[...(profile?.ruleIds||[])],weaponId:profile?.weaponId||'',profileId:profile?.id||'',
      weaponName:profile?.weaponName||profile?.name||'',profileName:profile?.name||'',
      name:profile?.weaponName===profile?.name?profile?.name:`${profile?.weaponName}: ${profile?.name}`
    };
  }
  function normalizeNpo(npo){
    if(!isRecord(npo))return null;
    const type=npo.type,definition=npoDefinition(type);
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
      displayNumber:Number.isInteger(npo.displayNumber)&&npo.displayNumber>0?npo.displayNumber:null,
      move:Number(npo.move)>0?Number(npo.move):definition.move,
      apl:Number(npo.apl)>0?Number(npo.apl):definition.apl,
      save:Number(npo.save)>0?Number(npo.save):definition.save,
      maxWounds:Number(npo.maxWounds)>0?Number(npo.maxWounds):definition.wounds,
      wounds:Number.isFinite(Number(npo.wounds))&&npo.wounds!==null?Math.max(0,Number(npo.wounds)):definition.wounds,
      baseSize:Number.isFinite(Number(npo.baseSize))?Number(npo.baseSize):definition.baseSize,
      behavior:npo.behavior||definition.compatibilityBehavior,
      attack:canonicalAttackProfile(npoAttackProfiles({...npo,type,weaponId},'shoot')[0]||npoAttackProfiles({...npo,type,weaponId},'melee')[0]) || {...definition.compatibilityAttack},
      weaponId,
      order:npo.order||'Conceal',
      battlefieldState,
      deployed:battlefieldState==='deployed',
      ...(typeof npo.offBoardReason==='string'&&npo.offBoardReason?{offBoardReason:npo.offBoardReason}:{}),
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
  function rollDice(count,sides){return Array.from({length:count},()=>roll(sides));}
  function selectRandomDistinctPlayerOperatives(operativeIds,count=2){
    const available=[...new Set(operativeIds)];
    for(let index=available.length-1;index>0;index--){
      const swapIndex=roll(index+1)-1;
      [available[index],available[swapIndex]]=[available[swapIndex],available[index]];
    }
    return available.slice(0,count);
  }
  function eligibleTransdimensionalRelocationOperativeIds(){
    return inPlayLivingPlayerOperativeIds();
  }
  function validTransdimensionalRelocationSelection(event,eligibleIds=eligibleTransdimensionalRelocationOperativeIds()){
    const selected=event?.resolution?.playerOperativeIds;
    return event?.resolution?.type==='transdimensional-relocation'
      &&Array.isArray(selected)&&selected.length===2&&new Set(selected).size===2
      &&selected.every(id=>eligibleIds.includes(id));
  }
  function prepareTransdimensionalRelocation(event){
    if(!event||event.definitionId!=='transdimensional-relocation'||event.status==='resolved')return true;
    const eligibleIds=eligibleTransdimensionalRelocationOperativeIds();
    if(validTransdimensionalRelocationSelection(event,eligibleIds))return true;
    event.resolution=null;
    if(eligibleIds.length<2)return false;
    event.resolution={
      type:'transdimensional-relocation',
      playerOperativeIds:selectRandomDistinctPlayerOperatives(eligibleIds,2),
      confirmed:false
    };
    save();
    return true;
  }
  function npoProfileSchemaValid(definition){
    return Boolean(definition?.id&&definition?.type&&definition?.name
      &&['apl','move','save','wounds'].every(field=>Number.isFinite(definition[field]))
      &&['rangedWeapons','meleeWeapons','actions','passiveRules','strategicRules','keywords'].every(field=>Array.isArray(definition[field])));
  }
  function effectivePlayerApl(operativeId,baseApl){return EventEffects.effectivePlayerApl(state,operativeId,baseApl);}
  function effectiveNpoApl(operativeId,baseApl){return EventEffects.effectiveNpoApl(state,operativeId,baseApl);}
  function effectiveApl(operativeId,baseApl){
    return state.playerRoster?.includes(operativeId)?effectivePlayerApl(operativeId,baseApl):effectiveNpoApl(operativeId,baseApl);
  }
  function effectiveWeaponProfile(profile,context={}){return EventEffects.effectiveWeaponProfile(state,profile,{turningPoint:state.turningPoint,...context});}
  function effectiveAttackRerolls(context={}){return EventEffects.effectiveAttackRerolls(state,{turningPoint:state.turningPoint,...context});}
  function applyActiveTombWorldEventHooks(hookName,context={}){return EventEffects.applyActiveTombWorldEventHooks(state,hookName,{turningPoint:state.turningPoint,...context});}
  function resolveNpoIncapacitation(context={}){return EventEffects.resolveNpoIncapacitation(state,{turningPoint:state.turningPoint,...context});}
  function eventTransaction(id,defaults={}){
    state.eventState.transactions=state.eventState.transactions||{};
    return state.eventState.transactions[id]||(state.eventState.transactions[id]={id,turningPoint:state.turningPoint,committed:false,...defaults});
  }
  function applyTemporaryAplModifier({sourceId,targetId,ruleId,amount,deferCurrentActivation=false}){
    const modifiers=state.npoRuleState.aplModifiers;
    const duplicate=modifiers.find(item=>item.sourceId===sourceId&&item.targetId===targetId&&item.ruleId===ruleId);
    if(duplicate)return false;
    modifiers.push({id:`${ruleId}:${sourceId}:${targetId}`,sourceId,targetId,ruleId,amount,expires:'end-of-target-next-activation',deferCurrentActivation});
    return true;
  }
  function expireActivationEffects(operativeId){
    state.npoRuleState.aplModifiers=state.npoRuleState.aplModifiers.filter(item=>{
      if(item.targetId!==operativeId)return true;
      if(item.deferCurrentActivation){item.deferCurrentActivation=false;return true;}
      return false;
    });
    state.eventState.playerAplModifiers=state.eventState.playerAplModifiers.filter(item=>{
      if(item.targetId!==operativeId||item.expires!=='end-of-target-next-activation')return true;
      if(item.deferCurrentActivation){item.deferCurrentActivation=false;return true;}
      return false;
    });
  }
  function applyMolecularBreach(sourceId,targetId){
    const effects=state.npoRuleState.pendingMovementEffects;
    if(effects.some(effect=>effect.targetId===targetId&&effect.ruleId==='molecular-breach'))return false;
    effects.push({id:`molecular-breach:${sourceId}:${targetId}`,ruleId:'molecular-breach',sourceId,targetId,trigger:'next-movement-action',consumeOnTrigger:true});
    return true;
  }
  function consumeMolecularBreach(targetId,actionName){
    if(!['Reposition','Dash','Charge','Fall Back'].includes(actionName))return null;
    const index=state.npoRuleState.pendingMovementEffects.findIndex(effect=>effect.targetId===targetId&&effect.ruleId==='molecular-breach');
    return index<0?null:state.npoRuleState.pendingMovementEffects.splice(index,1)[0];
  }
  function resolveGeomanticDisturbance(operatives,rollTwoD6=()=>rollDice(2,6)){
    return operatives.map(operative=>{const dice=rollTwoD6(operative),total=dice.reduce((sum,value)=>sum+value,0);return {operativeId:operative.id,dice,total,damage:Math.max(0,total-operative.wounds)};});
  }
  function markerControlApl(npo){return npo?.type===TOMB_CRAWLER_TYPE?3:effectiveApl(npo?.id,npo?.apl);}
  function npoThreatRating(npo){
    const definition=npoDefinition(npo?.type);
    if(!definition)return 0;
    const profiles=[...npoAttackProfiles(npo,'shoot'),...npoAttackProfiles(npo,'melee')];
    const peakDamage=Math.max(0,...profiles.map(profile=>Number(profile.attacks||0)*Number(profile.damage?.normal||0)));
    const durability=Math.max(0,Number(npo.wounds||0))*(7-Math.max(2,Number(definition.save||6)))/5;
    return Math.max(0,Math.round((durability+Number(definition.apl||0)+peakDamage/4)*10)/10);
  }
  function activeNpoThreat(){return activeNpos().reduce((total,npo)=>total+npoThreatRating(npo),0);}
  function ceaselessScuttlingEligible(turningPoint=state.turningPoint,roster=state.roster){
    const living=roster.filter(npo=>npo.type==='Canoptek Macrocyte Warrior'&&npo.wounds>0).length;
    const deployed=roster.filter(npo=>npo.battlefieldState==='deployed'&&npo.wounds>0).length;
    return turningPoint>1&&living<3&&deployed<MAX_NPOS;
  }
  function createCeaselessScuttlingWarrior(weaponId){
    if(!ceaselessScuttlingEligible())return null;
    const definition=npoDefinition('Canoptek Macrocyte Warrior');
    if(!definition.loadoutOptions.some(option=>option.id===weaponId))return null;
    const returned=state.roster
      .filter(npo=>npo.type===definition.type&&(npo.battlefieldState==='out-of-action'||npo.wounds<=0))
      .sort((a,b)=>(Number(a.displayNumber)||0)-(Number(b.displayNumber)||0))[0];
    const warrior=returned||createNpo(definition.type,definition.name,{weaponId,ready:true,dormant:false});
    if(returned)Object.assign(warrior,{weaponId,wounds:definition.wounds,maxWounds:definition.wounds,attack:canonicalAttackProfile(npoAttackProfiles({type:definition.type,weaponId},'shoot')[0]||npoAttackProfiles({type:definition.type,weaponId},'melee')[0]),ready:true,dormant:false,deployed:true,battlefieldState:'deployed'});
    warrior.createdBy='a-ceaseless-scuttling';
    warrior.order='Conceal';
    if(!returned)state.roster.push(warrior);
    log(`A Ceaseless Scuttling created ${npoName(warrior)} (${definition.loadoutOptions.find(option=>option.id===weaponId).name}) ready with a Conceal order in the NPO drop zone.`);
    return warrior;
  }
  function aggressiveDefenceDamage(rollResult){return Number(rollResult)>=2?1:0;}
  function reanimateEligible({reanimator,target,visible,distance,sourceInControlRange=false,targetInControlRange=false,shootTargets=[]}){
    const used=state.npoRuleState.oncePerTurningPoint.reanimate===state.turningPoint;
    return !used&&reanimator&&target&&reanimator.id!==target.id&&reanimator.wounds>0&&target.type&&npoDefinition(target.type)?.keywords.includes('Canoptek Circle')
      &&visible&&distance<=6&&!sourceInControlRange&&!targetInControlRange&&!shootTargets.includes(reanimator.id);
  }
  function applyReanimate(reanimator,target,{duringTargetActivation=false}={}){
    target.wounds=1;
    state.npoRuleState.oncePerTurningPoint.reanimate=state.turningPoint;
    state.npoRuleState.reanimatedTargetIds.push(target.id);
    applyTemporaryAplModifier({sourceId:reanimator.id,targetId:reanimator.id,ruleId:'reanimate-source',amount:-1});
    applyTemporaryAplModifier({sourceId:reanimator.id,targetId:target.id,ruleId:'reanimate-target',amount:-1,deferCurrentActivation:duringTargetActivation});
    target.preventIncapacitationActionId=state.activationNumber;
    if(duringTargetActivation)target.ready=false;
    return {wounds:1,freeDash:{mustEndWithinSourceControlRange:true},activationEnded:duringTargetActivation};
  }
  function useNanoscarabBeam(target,rollResults=rollDice(3,3)){
    if(state.npoRuleState.oncePerTurningPoint.nanoscarabBeam===state.turningPoint||target.wounds<=0||state.npoRuleState.reanimatedTargetIds.includes(target.id))return null;
    const rolled=rollResults.reduce((sum,value)=>sum+value,0),before=target.wounds;
    const maximum=Number(target.maxWounds||npoDefinition(target.type)?.wounds||playerDefinition(target.id)?.wounds||before);
    target.wounds=Math.min(maximum,before+rolled);
    state.npoRuleState.oncePerTurningPoint.nanoscarabBeam=state.turningPoint;
    return {dice:rollResults,rolled,restored:target.wounds-before};
  }
  function generationResult(total){return npoGenerationTable.find(row=>total>=row.min&&total<=row.max)||null;}
  function generatedWeaponId(result){return result.weaponIds[roll(result.weaponIds.length)-1];}
  function createNpo(type,name=`${type} ${state.roster.length+1}`,options={}){
    const definition=npoDefinition(type);
    if(!definition)throw new Error(`Unknown NPO type: ${type}`);
    const [physicalInstance]=lowestAvailableNpoInstances(type,1,options.allocationContext||{});
    if(!physicalInstance)throw new Error(`No ${type} model remains available.`);
    let weaponId=npoWeapon(definition,options.weaponId)?.id||definition.defaultWeaponId;
    if(type===TOMB_CRAWLER_TYPE&&weaponId===ISOLATOR_LOADOUT&&state.roster.some(npo=>npo.type===type&&npo.weaponId===ISOLATOR_LOADOUT))weaponId=definition.defaultWeaponId;
    const battlefieldState=options.battlefieldState||(options.deployed===false?'reserve':'deployed');
    const dormant=battlefieldState==='deployed'&&(options.dormant??state.threat===0);
    return {
      id:physicalInstance.id,name,type,displayNumber:physicalInstance.displayNumber,move:definition.move,apl:definition.apl,save:definition.save,
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
  function availableGenerationResult(){
    const inventory=npoInventory(), available=npoGenerationTable.filter(row=>inventory[row.type]?.remaining>0&&!(row.weaponIds.length===1&&row.weaponIds[0]===ISOLATOR_LOADOUT&&state.roster.some(npo=>npo.type===TOMB_CRAWLER_TYPE&&npo.weaponId===ISOLATOR_LOADOUT)));
    if(!available.length)return null;
    for(let attempts=0;attempts<24;attempts++){
      const result=rollNpo();
      if(available.includes(npoGenerationTable.find(row=>row.min===result.min&&row.max===result.max)))return result;
    }
    const result=available[roll(available.length)-1];
    return {...result,rolls:[],total:null,weaponId:generatedWeaponId(result)};
  }
  function activeNpos(){ return state.roster.filter(n => n.battlefieldState==='deployed'&&n.wounds > 0); }
  function hasValidPlayerCombatTargets(stage={}){
    return activeNpos().some(npo=>projectedNpoWounds(npo.id,stage)>0);
  }
  function reserveNpos(){ return state.roster.filter(n => n.battlefieldState==='reserve'&&n.wounds > 0); }
  function readyNpos(){ return activeNpos().filter(n => n.ready&&!n.dormant); }
  function trackerNpos(){
    return state.roster.filter(npo=>npo.battlefieldState==='deployed'||npo.battlefieldState==='out-of-action');
  }
  function npoTrackerStatus(npo){
    if(npo.wounds<=0||npo.battlefieldState==='out-of-action')return {status:'ELIMINATED',className:'eliminated'};
    if(npo.battlefieldState==='reserve')return {status:'RESERVE',className:'reserve'};
    if(npo.battlefieldState==='deployed'&&npo.dormant)return {status:'DORMANT',className:'dormant'};
    if(npo.battlefieldState==='deployed'&&npo.ready)return {status:'READY',className:'ready'};
    if(npo.battlefieldState==='deployed'&&state.npoActivated>0)return {status:'ACTIVATED',className:'activated'};
    if(npo.battlefieldState==='deployed')return {status:'READY',className:'ready'};
    return {status:'RESERVE',className:'reserve'};
  }
  function npoStatus(npo){
    if(npo.wounds<=0||npo.battlefieldState==='out-of-action')return 'ELIMINATED';
    if(npo.id===state.activeNpoId&&state.lastActivation?.npoId===npo.id&&!state.lastActivation?.committed)return 'ACTIVE';
    if(npo.battlefieldState==='reserve')return 'RESERVE';
    if(npo.dormant)return 'DORMANT';
    return npo.ready?'READY':'ACTIVATED';
  }
  function livingPlayerOperativeCount(){
    return livingPlayerOperativeIds().length;
  }
  function inPlayLivingPlayerOperativeCount(){return inPlayLivingPlayerOperativeIds().length;}

  function playerStatus(operativeId,activePlayerId=null){
    const operativeState=playerOperativeState(operativeId);
    if(operativeState.inPlay===false)return operativeState.offBoardReason==='escaped'?'ESCAPED':'NOT IN PLAY';
    if(playerCurrentWounds(operativeId)<=0||(state.playerCasualtyIds||[]).includes(operativeId))return 'ELIMINATED';
    if(activePlayerId===operativeId||state.combatState?.side==='player'&&state.combatState.stage?.playerOperativeId===operativeId)return 'ACTIVE';
    return (state.playerActivatedIds||[]).includes(operativeId)?'ACTIVATED':'READY';
  }
  function statusWoundsHtml(current,maximum){
    const woundClass=current<=0||current<=maximum/2?'severe':current<maximum?'wounded':'';
    return `<span class="operative-status-wounds"><span class="operative-status-current ${woundClass}">${current}</span><span>/${maximum}</span></span>`;
  }
  function operativeStatusRow({name,type,current,maximum,status}){
    const active=status==='ACTIVE';
    return `<div class="operative-status-row${active?' active':''}"><strong>${escapeHtml(name)}</strong><div><span class="operative-status-type">${escapeHtml(type)}</span>${statusWoundsHtml(current,maximum)}<span class="operative-status-value">${status}</span></div></div>`;
  }
  function renderOperativeStatusPanel(activePlayerId=null){
    const eligible=state.screen==='game'&&operativeStatusMedia.matches;
    const visible=eligible&&showOperativeStatusPreference;
    operativeStatusToggle.hidden=!eligible;
    operativeStatusToggle.setAttribute('aria-pressed',String(visible));
    operativeStatusToggle.setAttribute('aria-label',visible?'Hide operative status':'Show operative status');
    operativeStatusToggle.classList.toggle('active',visible);
    gameWorkspace.classList.toggle('operative-status-visible',visible);
    operativeStatusPanel.hidden=!visible;
    if(!visible)return;
    const npoRows=sortedNposForDisplay(state.roster).map(npo=>{
      const status=npoStatus(npo);
      return operativeStatusRow({name:npoName(npo),type:npoDefinition(npo.type)?.name||npo.type,current:Math.max(0,npo.wounds),maximum:npo.maxWounds,status});
    }).join('');
    const playerRows=(state.playerRoster||[]).map(id=>{
      const definition=playerDefinition(id),maximum=Number(definition?.wounds||0);
      return operativeStatusRow({name:playerName(id),type:definition?.role||'Operative',current:Math.max(0,playerCurrentWounds(id)),maximum,status:playerStatus(id,activePlayerId)});
    }).join('');
    operativeStatusPanel.innerHTML=`<section class="operative-status-section"><h2>NPO Operatives</h2><div class="operative-status-list">${npoRows||'<p class="muted">No NPO operatives</p>'}</div></section><section class="operative-status-section"><h2>Player Operatives</h2><div class="operative-status-list">${playerRows||'<p class="muted">No Player operatives</p>'}</div></section>`;
    requestAnimationFrame(fitOperativeStatusPanel);
  }
  function fitOperativeStatusPanel(){
    if(operativeStatusPanel.hidden)return;
    const sections=$$('.operative-status-section',operativeStatusPanel);
    sections.forEach(section=>{
      const list=$('.operative-status-list',section);
      section.classList.remove('two-column','extra-compact','allow-scroll');
      list.style.removeProperty('--status-column-rows');
      if(list.scrollHeight<=list.clientHeight)return;
      section.classList.add('two-column');
      list.style.setProperty('--status-column-rows',Math.ceil(list.children.length/2));
      if(list.scrollHeight<=list.clientHeight)return;
      section.classList.add('extra-compact');
      if(list.scrollHeight>list.clientHeight)section.classList.add('allow-scroll');
    });
  }
  function scheduleOperativeStatusLayout(){
    clearTimeout(operativeStatusResizeTimer);
    operativeStatusResizeTimer=setTimeout(()=>{renderOperativeStatusPanel();},120);
  }
  operativeStatusToggle.addEventListener('click',()=>{
    showOperativeStatusPreference=!showOperativeStatusPreference;
    localStorage.setItem(OPERATIVE_STATUS_PREFERENCE_KEY,String(showOperativeStatusPreference));
    renderOperativeStatusPanel();
  });
  if(operativeStatusMedia.addEventListener)operativeStatusMedia.addEventListener('change',scheduleOperativeStatusLayout);
  else operativeStatusMedia.addListener?.(scheduleOperativeStatusLayout);
  window.addEventListener('resize',scheduleOperativeStatusLayout);
  window.addEventListener('orientationchange',scheduleOperativeStatusLayout);

  function normalizeSarcophagusControllers(value,max=livingPlayerOperativeCount()){
    const limit=Math.max(0,Math.round(Number(max)||0));
    return Math.max(0,Math.min(limit,Math.round(Number(value)||0)));
  }

  const missionOutcomeEvaluators = {
    escape:(engine,progress,timing)=>{
      const total=state.playerRoster.length, departed=new Set([...progress.escapedIds,...state.playerCasualtyIds]);
      if(!total)return null;
      if(departed.size<total)return timing==='turning-point-limit'?'defeat':null;
      return progress.escapedIds.length>=Math.ceil(total/2)?'victory':'defeat';
    },
    sabotage:(engine,progress,timing)=>progress.completedFeatureIds.length>=engine.required?'victory':timing==='turning-point-limit'?'defeat':null,
    transponder:(engine,progress,timing)=>progress.escaped?'victory':timing==='turning-point-limit'?'defeat':null,
    destruction:(engine,progress,timing)=>progress.destruction>=engine.required?'victory':timing==='turning-point-limit'?'defeat':null,
    scout:(engine,progress,timing)=>progress.scoutedRoomIds.length>=engine.required?'victory':timing==='turning-point-limit'?'defeat':null,
    regroup:(engine,progress,timing)=>{
      if(!['end-turning-point','turning-point-limit'].includes(timing))return null;
      const survivors=inPlayLivingPlayerOperativeIds();
      if(!survivors.length)return null;
      return survivors.every(id=>{
        const check=progress.operativeChecks[id]||{};
        return check.inDropZone&&check.outsideNpoControl&&check.nearPlayer;
      })?'victory':timing==='turning-point-limit'?'defeat':null;
    }
  };

  function missionOutcome(timing='immediate'){
    const engine=missionEngine(), progress=state.missionState||freshMissionState();
    const defeat=(state.playerRoster||[]).length>0&&livingPlayerOperativeCount()===0;
    if(defeat&&engine?.type!=='escape')return 'defeat';
    const evaluator=missionOutcomeEvaluators[engine?.type];
    return evaluator?evaluator(engine,progress,timing):null;
  }

  let battleEndHookPending=false;

  async function finalizeMissionCompletion(outcome,previousPhase){
    if(battleEndHookPending)return;
    battleEndHookPending=true;
    if(!state.finalResolution.battleEndHookComplete){
      const hookResult=await executeMissionLifecycleHook('onBattleEnded',{outcome});
      if(hookResult===null){
        battleEndHookPending=false;
        state.gameEnd=null;state.completed=false;
        state.phase=state.finalResolution.pending?'battle-resolution':previousPhase;
        save();render();
        showToast('The battle result could not be recorded. Please try again.');
        return;
      }
      state.finalResolution.battleEndHookComplete=true;
    }
    const engine=missionEngine();
    if(!state.finalResolution.resultLogged){
      log(`${mission().name}: ${outcome}. ${outcome==='victory'?engine?.success:engine?.failure}`);
      state.finalResolution.resultLogged=true;
    }
    state.finalResolution.pending=false;
    battleEndHookPending=false;
    closeModal();save();render();
  }

  function completeMission(outcome){
    if(!['victory','defeat'].includes(outcome)||state.gameEnd)return false;
    const previousPhase=state.phase;
    state.gameEnd=outcome;
    state.completed=true;
    state.phase='end';
    state.finalResolution=state.finalResolution||{};
    void finalizeMissionCompletion(outcome,previousPhase);
    return true;
  }

  function checkGameEnd(timing='immediate'){
    const outcome=missionOutcome(timing);
    return outcome?completeMission(outcome):false;
  }

  function completeTurningPointCleanup(){
    state.eventState.active=state.eventState.active.filter(event=>event.expiresAfterTurningPoint!==state.turningPoint);
    state.strategyStage=null;state.strategyData=null;state.newIds=[];
    state.finalResolution.cleanupComplete=true;
  }

  let turningPointLimitPending=false;

  async function resolveTurningPointLimit(){
    if(turningPointLimitPending)return false;
    turningPointLimitPending=true;
    state.finalResolution=state.finalResolution||{};
    if(!state.finalResolution.turningPointEnded){
      if(await executeMissionLifecycleHook('onTurningPointEnded')===null){turningPointLimitPending=false;return false;}
      state.finalResolution.turningPointEnded=true;
      log(`Turning Point ${state.turningPoint} completed.`);
    }
    if(!state.finalResolution.cleanupComplete)completeTurningPointCleanup();
    const outcome=missionOutcome('turning-point-limit');
    if(outcome){turningPointLimitPending=false;return completeMission(outcome);}
    state.finalResolution.pending=true;
    state.phase='battle-resolution';
    save();render();
    showToast(`Turning Point ${MAX_TURNING_POINTS} is the final Turning Point. Record the mission outcome.`);
    turningPointLimitPending=false;
    return true;
  }

  function totalLivingOperatives(){
    return inPlayLivingPlayerOperativeCount()+activeNpos().length;
  }

  function activationProgressLabel(){
    const current=Math.max(1,state.activationNumber+1);
    return `ACTIVATION ${current} OF ${totalLivingOperatives()}`;
  }

  function playerOperativesRemaining(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    return inPlayPlayerOperativeIds().filter(id=>!casualties.has(id)&&!activated.has(id)).length;
  }
  function destroyedNpoCount(){ return state.roster.filter(n=>n.wounds<=0).length; }
  function eligibleNpoAttackTargets(){
    return inPlayLivingPlayerOperativeIds();
  }
  function selectedNpoAttackTarget(){
    const descriptor=state.weaponRuleResolution?.orderedTargets?.find(target=>target.targetId===state.npoAttackTargetId);
    if(descriptor?.targetSide==='npo')return activeNpos().find(npo=>npo.id===state.npoAttackTargetId)||null;
    return isPlayerOperativeInPlay(state.npoAttackTargetId)?livePlayerOperative(state.npoAttackTargetId):null;
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

  const GRADE_CONFIG = [
    {grade:0,name:'Dormant',minThreat:0,maxThreat:0,reinforcements:0},
    {grade:1,name:'Stirring',minThreat:1,maxThreat:5,reinforcements:1},
    {grade:2,name:'Awakened',minThreat:6,maxThreat:10,reinforcements:2},
    {grade:3,name:'Overrun',minThreat:11,maxThreat:15,reinforcements:3}
  ];
  function gradeConfig(grade){return GRADE_CONFIG.find(config=>config.grade===Number(grade))||GRADE_CONFIG[0];}
  function threatGrade(){return GRADE_CONFIG.find(config=>state.threat>=config.minThreat&&state.threat<=config.maxThreat)?.grade??0;}
  function normalStrategyEventCount({turningPoint,grade,suggestedInitiative,threat}){
    if(turningPoint<=1||grade!==3)return 0;
    return suggestedInitiative==='npo'||threat===15?2:1;
  }
  function strategyEventCount(data=state.strategyData||{},context={}){
    const turningPoint=context.turningPoint??state.turningPoint;
    const threat=context.threat??state.threat;
    const restlessTombEnabled=context.restlessTombEnabled??state.restlessTombEnabled;
    const normalCount=normalStrategyEventCount({turningPoint,grade:data.grade,suggestedInitiative:data.suggestedInitiative,threat});
    return restlessTombEnabled&&turningPoint>=2?Math.max(normalCount,1):normalCount;
  }
  function gradeGameplayDescription(grade,context={}){
    const config=gradeConfig(grade);
    const turningPoint=context.turningPoint??Math.max(2,state.turningPoint);
    const threat=context.threat??config.minThreat;
    const suggestedInitiative=context.suggestedInitiative??'player';
    const restlessTombEnabled=context.restlessTombEnabled??state.restlessTombEnabled;
    const normalEvents=normalStrategyEventCount({turningPoint,grade:config.grade,suggestedInitiative,threat});
    const effectiveEvents=strategyEventCount({grade:config.grade,suggestedInitiative},{turningPoint,threat,restlessTombEnabled});
    const standardEvents=normalStrategyEventCount({turningPoint,grade:config.grade,suggestedInitiative:'player',threat:config.minThreat});
    const elevatedEvents=Math.max(
      normalStrategyEventCount({turningPoint,grade:config.grade,suggestedInitiative:'npo',threat:config.minThreat}),
      normalStrategyEventCount({turningPoint,grade:config.grade,suggestedInitiative:'player',threat:config.maxThreat})
    );
    const reinforcementEffect={
      id:'npo-reinforcements',
      subject:'NPO reinforcements',
      automation:config.reinforcements?'guided':'informational',
      text:config.reinforcements
        ? `The Guide will prompt you to place ${config.reinforcements} NPO reinforcement${config.reinforcements===1?'':'s'} during each Strategy Phase after Turning Point 1.`
        : 'No NPO reinforcements will be added through the normal Grade rules.'
    };
    let eventText;
    if(effectiveEvents===0)eventText='Grade 1 will not trigger any Tomb World events. Other enabled rules may still trigger them.';
    else if(restlessTombEnabled&&effectiveEvents>normalEvents)eventText=`The Guide will prompt you to resolve at least ${effectiveEvents} Tomb World event${effectiveEvents===1?'':'s'} during each Strategy Phase after Turning Point 1 because Restless Tomb is enabled.`;
    else if(elevatedEvents>standardEvents)eventText=`The Guide will prompt you to resolve ${standardEvents} Tomb World event${standardEvents===1?'':'s'} during each Strategy Phase after Turning Point 1, or ${elevatedEvents} when NPOs have initiative or Threat reaches ${config.maxThreat}.`;
    else eventText=`The Guide will prompt you to resolve ${effectiveEvents} Tomb World event${effectiveEvents===1?'':'s'} during each Strategy Phase after Turning Point 1.`;
    const eventEffect={id:'tomb-world-events',subject:'Tomb World events',automation:effectiveEvents?'guided':'informational',text:eventText};
    const awakeningEffect={
      id:'npo-deployment-state',
      subject:'NPO deployment state',
      automation:'automatic',
      text:config.grade===0
        ? 'Deployed NPOs will remain Dormant unless another rule makes them Ready.'
        : 'Deployed NPOs will enter play Ready instead of Dormant.'
    };
    return {grade:config.grade,name:config.name,threatRange:`Threat Level ${config.minThreat}${config.minThreat===config.maxThreat?'':`–${config.maxThreat}`}`,effects:[reinforcementEffect,eventEffect,awakeningEffect].filter(Boolean)};
  }
  function threatLabel(){return gradeConfig(threatGrade()).name;}
  function nextGradeThreat(){return GRADE_CONFIG[threatGrade()+1]?.minThreat??null;}
  function threatToNext(){const next=nextGradeThreat();return next===null?0:next-state.threat;}
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
  function inlineOperativeList(names){return names.filter(Boolean).join(' · ');}

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
    const selectedTypeCounts=shuffled.slice(0,generation.deploymentCount).reduce((counts,npo)=>({...counts,[npo.type]:(counts[npo.type]||0)+1}),{});
    generation.deployedNpoIds=Object.entries(selectedTypeCounts).flatMap(([type,quantity])=>available
      .filter(npo=>npo.type===type)
      .sort((a,b)=>(Number(a.displayNumber)||0)-(Number(b.displayNumber)||0))
      .slice(0,quantity)
      .map(npo=>npo.id));
    const deployedIds=new Set(generation.deployedNpoIds);
    generation.reserveNpoIds=available.filter(npo=>!deployedIds.has(npo.id)).map(npo=>npo.id);
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
    const previousRoster=state.roster;
    state.roster=[];
    for(let i=0;i<count;i++){
      const result=availableGenerationResult();
      if(!result){
        console.warn(`[NPO inventory] ${m.name} requested ${count} models, but only ${state.roster.length} legal generated models were available.`);
        state.roster=previousRoster;showToast('A complete legal NPO roster could not be generated.');return null;
      }
      state.roster.push(createNpo(result.type,`${result.type} ${i+1}`,{weaponId:result.weaponId,ready:false,deployed:false}));
    }
    const validation=validateNpoRoster(state.roster);
    if(!validation.valid){state.roster=previousRoster;console.warn('[NPO inventory] Generated roster was rejected.',validation.errors);showToast('A legal NPO roster could not be generated.');return null;}
    selectStartingNpos(generation);
    state.newIds=[]; log(`${m.name}: selected ${generation.deploymentCount} of ${state.roster.length} starting NPOs (${formula}).`); return {count:state.roster.length,formula};
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

    gameMenuBtn.hidden = !['setup','game'].includes(state.screen);
    if(state.screen==='home') renderHome();
    else if(state.screen==='help') renderHowItWorks();
    else if(state.screen==='setup') renderSetup();
    else renderGame();
    bindCommon();
    updateGameBackground();
    renderOperativeStatusPanel();

    if(state.hotResolution&&!state.hotResolution.acknowledged&&!modal.open){
      showHotResult(state.hotResolution,()=>resumePersistedHotContinuation(state.hotResolution));
    }

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

    const npoRoster=`<section class="help-section">
      <h3>Tomb World NPO roster</h3>
      <p>The supported pool uses the physical models in the Tomb World box: the <strong>Canoptek Circle</strong> (Geomancer, Canoptek Tomb Crawler, Canoptek Macrocyte Warrior, Canoptek Macrocyte Accelerator, and Canoptek Macrocyte Reanimator), <strong>Necron Warriors</strong>, and <strong>Canoptek Scarab Swarms</strong>.</p>
      <p>NPO lists are alphabetical, and applicable loadouts are selected for each operative instance. NPO portraits are intentionally not displayed. The Obelisk Node Matrix is not supported by the Guide.</p>
      <p>Current saves and older saves use the v7 migration flow. If an active legacy battle contains an unsupported retired NPO, the Guide asks before returning that battle to setup so a legal roster can be regenerated.</p>
    </section>`;

    const quick=`<section class="help-section quick-reference-grid">
      <article><h4>Player</h4><p>Your solo kill-team operatives.</p></article>
      <article><h4>NPO</h4><p>A non-player operative controlled by the Guide.</p></article>
      <article><h4>APL</h4><p>The number of action points an operative may spend during its activation.</p></article>
      <article><h4>THREAT LEVEL</h4><p>A 0–15 alert meter. Higher grades generate more reinforcements and events.</p></article>
      <article><h4>Ready</h4><p>The operative can still activate during this Turning Point.</p></article>
      <article><h4>Expended</h4><p>The operative has activated or is otherwise unavailable.</p></article>
    </section>`;

    if(full) return overview+npoRoster+flow+ai+combat+quick;
    return npoRoster+ai+quick;
  }

  function renderHome(){
    const saved=load();
    const savedGame=saved?.report?.requiresRegeneration?null:saved?.state;
    const canContinue=Boolean(savedGame?.missionId&&savedGame?.screen==='game');
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
    $('#newGameBtn').onclick=startNewGameSetup;
    $('#continueBtn').onclick=()=>{ if(savedGame){state=normalizeState(savedGame);state.screen='game';render();} };
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
  function clearPlayerTeamDependentState(){
    state.playerRosterInitializedForTeamId='';
    state.playerRoster=[];
    state.playerDisplayNumbers={};
    state.playerCount=0;
    state.playerReady=0;
    state.playerCasualtyIds=[];
    state.playerWounds={};
    state.playerActivatedIds=[];
    state.playerDeployed=false;
  }
  function selectPlayerTeam(teamId){
    ++playerTeamLoadRequestId;
    state.playerTeamId=teamId;
    state.playerTeamFile='';
    playerTeamData=null;
    loadedPlayerTeamId=null;
    playerTeamLoadStatus='loading';
    playerTeamLoadError=null;
    clearPlayerTeamDependentState();
    save();
    render();
    loadPlayerTeamData(teamId).catch(error=>{
      if(state.playerTeamId===teamId){
        console.error(error);
        showToast('Unable to load this Kill Team. Select it again to retry.');
      }
    });
  }
  function playerTeamLoadPresentation(){
    if(playerTeamLoadStatus==='error')return '<p class="muted" role="alert">Unable to load this Kill Team. Select it again to retry.</p>';
    return '';
  }
  function playerTeamLoadingAnnouncement(){
    return playerTeamLoadStatus==='loading'?'<span class="visually-hidden" role="status" aria-live="polite">Loading selected Kill Team operatives.</span>':'';
  }
  function buildPlayerRosterButton(id){
    const loading=playerTeamLoadStatus==='loading';
    const reason=loading?'The selected Kill Team is still loading.':playerTeamLoadStatus==='error'?'The selected Kill Team could not be loaded.':'Select a Kill Team first.';
    return `<button class="btn primary" id="${id}" ${canBuildPlayerRoster()?'':`disabled aria-disabled="true" title="${reason}"`}>${loading?'Loading Team...':'Build Roster'}</button>`;
  }
  function renderTeamSelection(){
    const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}">
      <div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div>
      <p>${escapeHtml(team.description||'')}</p>
    </button>`).join('');
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Choose Kill Team</h2><p>Select the player-controlled Kill Team for this battle.</p></div></div><section class="wizard-card" aria-busy="${playerTeamLoadStatus==='loading'}">${playerTeamLoadingAnnouncement()}<div class="team-select-grid">${cards}</div>${playerTeamLoadPresentation()}<div class="wizard-actions"><button class="btn ghost" id="teamSelectHome">Back</button>${buildPlayerRosterButton('teamSelectNext')}</div></section></div>`;
    $('#teamSelectHome').onclick=()=>{state.screen='home';save();render();};
    $('#teamSelectNext').onclick=()=>{if(!canBuildPlayerRoster()){showToast('Wait for the selected Kill Team to finish loading.');return;}state.screen='setup';state.setupStep=activeSetupSteps().indexOf('playerRoster');save();render();};
    $$('[data-player-team]').forEach(button=>button.onclick=()=>selectPlayerTeam(button.dataset.playerTeam));
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
      if(!canBuildPlayerRoster()){
        if(playerTeamLoadStatus==='loading'){
          const teamStep=steps.indexOf('team');
          app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Build Player Roster</h2><p>Loading the selected Kill Team before displaying its operatives.</p></div></div><section class="wizard-card" aria-busy="true">${playerTeamLoadingAnnouncement()}${teamStep>=0?'<div class="wizard-actions"><button class="btn ghost" id="playerRosterLoadBack">Back</button></div>':''}</section></div>`;
          $('#playerRosterLoadBack')?.addEventListener('click',()=>{state.setupStep=teamStep;save();render();});
          return;
        }
        const teamStep=steps.indexOf('team');
        if(teamStep<0){
          const failed=playerTeamLoadStatus==='error';
          app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Build Player Roster</h2><p>Loading the selected Kill Team before displaying its operatives.</p></div></div><section class="wizard-card" aria-busy="${!failed}">${failed?'<p role="alert">Unable to load this Kill Team.</p>':playerTeamLoadingAnnouncement()}${failed?'<div class="wizard-actions"><button class="btn primary" id="retryPlayerTeamLoad" aria-label="Retry selected Kill Team load">Retry Team Load</button></div>':''}</section></div>`;
          $('#retryPlayerTeamLoad')?.addEventListener('click',()=>loadPlayerTeamData(state.playerTeamId).catch(()=>{}));
          return;
        }
        state.setupStep=teamStep;
        save();
        render();
        if(state.playerTeamId&&playerTeamLoadStatus!=='loading')setTimeout(()=>loadPlayerTeamData(state.playerTeamId).catch(()=>{}),0);
        setTimeout(()=>showToast('Wait for the selected Kill Team to finish loading.'),0);
        return;
      }
      autoSelectRequiredPlayerOperatives();
      save();
    }
    if(stepId==='deploy')ensureStartingNpoGeneration();
    if(stepId==='deploy')satisfyEmptyStartingNpoDeployment();
    const details=setupStepDefinitions[stepId];
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>${details.title}</h2><p>${details.subtitle}</p></div><div class="step-count">${state.setupStep+1} / ${steps.length}</div></div><div class="progress-bar"><span style="width:${((state.setupStep+1)/steps.length)*100}%"></span></div><section class="wizard-card"${stepId==='team'?` aria-busy="${playerTeamLoadStatus==='loading'}"`:''}>${setupContent(stepId)}</section></div>`;
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
  function satisfyEmptyStartingNpoDeployment(){
    const generation=state.startingNpoGeneration;
    if(!generation||generation.deployedNpoIds.length)return;
    const deploymentCheck=missionSetupChecks('deploy').find(check=>check.id==='starting-npos');
    if(deploymentCheck&&!state.setupChecks[deploymentCheck.id]){
      state.setupChecks[deploymentCheck.id]=true;
      save();
    }
  }
  function setupChecklistHtml(checks){
    return checks.map(check=>`<label class="check-row"><input type="checkbox" data-check="${escapeHtml(check.id)}" ${state.setupChecks[check.id]?'checked':''}><span><strong>${escapeHtml(check.label)}</strong><small>Confirm this step on the physical board.</small></span></label>`).join('');
  }
  function setupContent(stepId){
    if(stepId==='mission') return `<h3>Which mission are you playing?</h3><p>You can review the objective before committing.</p><div class="mission-list">${missions.map(m=>`<button class="mission-choice ${state.missionId===m.id?'selected':''}" data-mission="${m.id}" aria-pressed="${state.missionId===m.id}"><div class="team-select-card-head"><div><small>${m.number}</small><strong>${m.name}</strong></div>${state.missionId===m.id?'<span>✓</span>':''}</div><span>${m.brief}</span></button>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupHome">Back</button><button class="btn primary" id="setupNext" ${state.missionId?'':'disabled'}>Next</button></div>`;
    if(stepId==='killzone'){
      const m=mission();
      const checks=missionSetupChecks('killzone');
      const allChecked=checks.length>0&&checks.every(check=>state.setupChecks[check.id]);
      return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${escapeHtml(m.objective)}</p>${boardSvg(m.id)}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllSetup" ${allChecked?'disabled':''}>Check All</button></div><div class="checklist">${setupChecklistHtml(checks)}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allChecked?'':'disabled'}>Board Ready</button></div>`;
    }
    if(stepId==='team'){
      const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}"><div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div><p>${escapeHtml(team.description||'')}</p></button>`).join('');
      return `<h3>Which Kill Team are you playing?</h3><p>Your choice determines the operatives available on the next step.</p>${playerTeamLoadingAnnouncement()}<div class="team-select-grid">${cards}</div>${playerTeamLoadPresentation()}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button>${buildPlayerRosterButton('setupNext')}</div>`;
    }
    if(stepId==='playerRoster'){
      const selected=new Set(state.playerRoster||[]);
      const selectedDefs=selectedPlayerOperatives();
      const gravisCount=selectedDefs.filter(o=>o.gravis).length;
      const gunnerCount=selectedDefs.filter(o=>o.role==='Gunner').length;
      const trooperCount=selectedDefs.filter(o=>o.role==='Trooper').length;
      const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners??Infinity);
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
          const categoryMaximum=Number(categoryMetadata.get(o.category)?.maxCount??Infinity);
          const categoryBlocked=!chosen&&Number.isFinite(categoryMaximum)&&categorySelected>=categoryMaximum;
          const selectionGroupMaximum=Number(playerTeamData?.selectionRules?.selectionGroupMax??Infinity);
          const selectionGroupBlocked=!chosen&&o.selectionGroup&&Number.isFinite(selectionGroupMaximum)&&selectedDefs.filter(candidate=>candidate.selectionGroup===o.selectionGroup).length>=selectionGroupMaximum;
          return `<button type="button" class="player-roster-card ${chosen?'selected':''}" data-select-player="${o.id}" ${rosterBlocked||gravisBlocked||gunnerBlocked||categoryBlocked||selectionGroupBlocked?'disabled':''}><div class="player-roster-card-head"><div><strong>${escapeHtml(chosen?playerName(o.id):o.name)}</strong><small>${escapeHtml(o.role)}${o.gravis?' · GRAVIS':''}</small></div><span>${chosen?'✓':'+'}</span></div><div class="operative-stat-line"><span><small>APL</small><b>${o.apl}</b></span><span><small>MOVE</small><b>${o.move}"</b></span><span><small>SAVE</small><b>${o.save}+</b></span><span><small>WOUNDS</small><b>${o.wounds}</b></span></div></button>`;
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
      const validation=playerRosterValidation([...selected]);
      if((playerTeamData?.rosterCategories||[]).some(category=>category.id!=='leader'&&(category.requiredCount||category.maxCount)))requirements.splice(0,requirements.length,...validation.requirements);
      const valid=validation.valid&&requiredLeaderSelected&&(!hasGravis||(gravisCount>=1&&gravisCount<=maxGravis));
      const requirementItems=requirements.map(requirement=>`<li>${escapeHtml(requirement)}</li>`).join('');
      return `<h3>Choose your ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Kill Team')} roster</h3><p>${selectionPrompt}</p><p class="muted">Build a legal kill team using its current official rules. Cooperative team splitting is not currently supported.</p><div class="setup-bulk-row"><button class="btn secondary" id="randomPlayerTeam">Random Team</button></div><section class="player-roster-summary" aria-labelledby="roster-requirements-heading"><h4 id="roster-requirements-heading">Roster Requirements</h4><ul>${requirementItems}</ul></section><div class="roster-categories">${sections}</div>${selectedDefs.length?`<div class="summary-box"><strong>Selected roster</strong><br>${inlineOperativeList(selectedDefs.map(o=>escapeHtml(playerName(o.id))))}</div>`:''}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${valid?'':'disabled'}>Roster Ready</button></div>`;
    }
    if(stepId==='deploy'){
      const generation=state.startingNpoGeneration;
      const hasStartingNpos=generation.deployedNpoIds.length>0;
      const dice=generation.dice.map(value=>dieHtml({value,kind:'hit'})).join('');
      const missionRoll=hasStartingNpos
        ? `<div class="starting-npo-event" id="startingNpoEvent" role="status" aria-live="polite"><small>MISSION ROLL</small><div class="dice-row ${generation.animationShown?'settled':'animated-roll'}" id="startingNpoDice">${generation.animationShown?dice:generation.dice.map(()=>rollingDieHtml()).join('')}</div><div class="starting-npo-result" id="startingNpoResult" ${generation.animationShown?'':'hidden'}><strong>${generation.missionRoll} Starting NPOs</strong><span>${generation.calculation}</span></div></div>`
        : `<div class="no-npo-message" role="status"><small>STARTING NPOS</small><strong>None</strong><span>This mission begins with no NPOs deployed. Enemy operatives will enter play later according to the mission rules.</span></div>`;
      const placementChecks=missionSetupChecks('deploy');
      const deploymentCheck=placementChecks.find(check=>check.id==='starting-npos');
      const otherPlacementChecks=placementChecks.filter(check=>check.id!=='starting-npos');
      const deploymentInstruction=`Deploy the ${generation.deploymentCount} selected starting NPOs.`;
      const deployedNpoRoster=inlineOperativeList(sortedNposForDisplay(generation.deployedNpoIds.map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean)).map(npo=>escapeHtml(npoName(npo))));
      const playerRoster=inlineOperativeList((state.playerRoster||[]).map(id=>escapeHtml(playerName(id))));
      const playerRosterHtml=playerRoster?`<span class="deployment-roster">${playerRoster}</span>`:'';
      const deploymentDetails=mission().startingNpos?.deployment||'Use the mission deployment rules.';
      const selectionComplete=generation.deployedNpoIds.length===generation.deploymentCount&&generation.deployedNpoIds.length+generation.reserveNpoIds.length===generation.availableNpos;
      const allNposPlaced=selectionComplete&&generation.deployedNpoIds.every(id=>state.roster.find(npo=>npo.id===id)?.deployed);
      const deploymentRow=hasStartingNpos&&deploymentCheck?`<label class="check-row deployment-check"><input id="npoDeployed" type="checkbox" data-check="${escapeHtml(deploymentCheck.id)}" ${state.setupChecks[deploymentCheck.id]&&allNposPlaced?'checked':''}><span><strong>${deploymentInstruction}</strong><span class="deployment-roster">${deployedNpoRoster}</span><small>${escapeHtml(deploymentDetails)}</small></span></label>`:'';
      const requiredPlacementChecks=hasStartingNpos?placementChecks:otherPlacementChecks;
      const allPlacementChecked=requiredPlacementChecks.every(check=>state.setupChecks[check.id]);
      const {minRoster,maxRoster}=playerRosterLimits();
      const playerValid=playerRosterValidation().valid;
      return `<h3>Deploy Kill Teams</h3><p>Place the generated NPO roster and selected Player roster, then confirm every mission deployment requirement.</p>${missionRoll}${factionGuidanceHtml()}${hasStartingNpos?`<div class="setup-bulk-row"><button class="btn secondary" id="checkAllDeployment" ${playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked?'disabled':''}>Check All</button></div>`:''}<div class="checklist deployment-checklist">${deploymentRow}${setupChecklistHtml(otherPlacementChecks)}<label class="check-row deployment-check"><input id="playerDeployed" type="checkbox" ${state.playerDeployed?'checked':''} ${playerValid?'':'disabled'}><span><strong>Deploy ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} Kill Team</strong>${playerRosterHtml}<small>All selected Player operatives are on the battlefield.</small></span></label></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${playerValid&&state.playerDeployed&&allNposPlaced&&allPlacementChecked?'':'disabled'}>Deployment Complete</button></div>`;
    }
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name||'Special Rule')}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary||'')}</p></div>`).join('');
    return `<h3>Mission Briefing</h3><div class="mission-briefing"><div class="mission-briefing-section mission-heading"><span>Mission</span><strong>${escapeHtml(m.number)} · ${escapeHtml(m.name)}</strong></div><div class="mission-briefing-section"><h4>Objective</h4><p>${escapeHtml(m.objective)}</p></div><div class="mission-briefing-section"><h4>Special Rules</h4>${rules||`<p>${escapeHtml(missionSpecial())}</p>`}</div><div class="mission-briefing-section optional-rules"><h4>Optional Rules</h4><label class="check-row restless-tomb-option"><input id="restlessTombEnabled" type="checkbox" ${state.restlessTombEnabled?'checked':''}><span><strong>Restless Tomb</strong><span class="rule-classification">House Rule</span><small>Beginning with Turning Point 2, resolve at least one Tomb World event during each Strategy Phase, regardless of Threat Grade. Turning Point 1 is unaffected, and standard event rules may require additional events at higher Threat. This optional house rule increases activity and difficulty.</small></span></label><label class="check-row deadly-encounters-option"><input id="deadlyEncountersEnabled" type="checkbox" ${state.deadlyEncountersEnabled?'checked':''}><span><strong>Deadly Encounters: Tomb Worlds</strong><span class="rule-classification official">Official Expansion - White Dwarf 521</span><small>Reveal persistent Room and Objective Features using the official D33 tables when Player operatives explore the tomb. PvE Player actions reveal features; NPOs never reveal them, but revealed features can affect NPOs. This independent expansion increases battlefield complexity and danger.</small></span></label></div></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function bindSetup(stepId){
    $$('.mission-choice').forEach(b=>b.onclick=()=>{const missionId=b.dataset.mission;state.missionId=missionId;state.missionState=freshMissionState(mission());state.missionRuntime=null;state.tracker=0;state.setupChecks={};state.roster=[];state.startingNpoGeneration=null;save();render();setTimeout(()=>loadObjectiveMission(missionId).then(()=>{if(state.missionId===missionId)save();}),0);});
    $('#setupHome')?.addEventListener('click',()=>{state.screen='home';save();render();});
    $('#setupBack')?.addEventListener('click',()=>{state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>{
      if(setupNavigationInProgress)return;
      if(currentSetupStepId()!==stepId)return;
      if(stepId==='team'&&!canBuildPlayerRoster()){showToast('Wait for the selected Kill Team to finish loading.');return;}
      setupNavigationInProgress=true;
      if(stepId==='playerRoster')assignPlayerDisplayNumbers();
      const steps=activeSetupSteps();state.setupStep=Math.min(steps.length-1,state.setupStep+1);save();render();
      setupNavigationInProgress=false;
    });
    $$('[data-player-team]').forEach(button=>button.onclick=()=>selectPlayerTeam(button.dataset.playerTeam));
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
        const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners??Infinity);
        if(candidate?.role==='Gunner'&&selectedPlayerOperatives().filter(o=>o.role==='Gunner').length>=maxGunners){showToast(`This Kill Team can include only ${maxGunners} Gunners.`);return;}
        const selectionGroupMaximum=Number(playerTeamData?.selectionRules?.selectionGroupMax??Infinity);
        if(candidate?.selectionGroup&&Number.isFinite(selectionGroupMaximum)&&selectedPlayerOperatives().filter(o=>o.selectionGroup===candidate.selectionGroup).length>=selectionGroupMaximum){showToast('Choose only one loadout for each operative.');return;}
        selected.add(id);
      }
      applyPlayerRoster(selected);
      save();render();
    }));
    $('#playerDeployed')?.addEventListener('change',e=>{state.playerDeployed=e.target.checked;save();render();});
    $('#restlessTombEnabled')?.addEventListener('change',e=>{state.restlessTombEnabled=e.target.checked;save();render();});
    $('#deadlyEncountersEnabled')?.addEventListener('change',e=>{state.deadlyEncountersEnabled=e.target.checked;save();render();});
    $('#beginGame')?.addEventListener('click',async()=>{
      state.screen='game';state.tab='play';state.turningPoint=0;state.phase='between';state.nextSide='player';state.playerCount=(state.playerRoster||[]).length;state.playerReady=state.playerCount;
      if(!backgroundManifest.length)await loadBackgroundManifest();
      ensureGameBackgroundSelection();
      objectiveEngine?.refreshMissionContext(missionLifecycleContext());
      if(!state.playerWounds||Object.keys(state.playerWounds).length===0)initializePlayerWounds();
      state.roster.forEach(n=>n.ready=false);log(`Mission started: ${mission().name}.`);if(state.deadlyEncountersEnabled)log('Deadly Encounters: Tomb Worlds enabled (official PvE expansion, White Dwarf 521).');startTurningPoint();
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
      const atLimit=state.turningPoint>=MAX_TURNING_POINTS&&state.finalResolution?.turningPointEnded;
      const resultLabel=victory?'Victory':'Defeat';
      const resultClass=victory?'victory':'defeat';
      app.innerHTML=`<section class="hero-card mission-outcome"><p class="eyebrow">${atLimit?'BATTLE COMPLETE':'MISSION COMPLETE'}</p><img class="game-end-image" src="Assets/Images/${resultClass}.png" alt="">${atLimit?`<h2>Battle Complete</h2><p role="status">Turning Point ${MAX_TURNING_POINTS} has ended.</p><h3 class="battle-result battle-result--${resultClass}">MISSION ${resultLabel.toUpperCase()}</h3>`:`<h2 class="battle-result battle-result--${resultClass}">${resultLabel}</h2>`}<p>${escapeHtml(victory?missionEngine()?.success:missionEngine()?.failure)}</p>${missionProgressHtml(true)}<div class="button-row"><button class="btn secondary" id="reviewCompletedMission">Review Mission</button><button class="btn primary" id="gameEndNewGame">Start New Game</button></div></section>`;
      $('#reviewCompletedMission').onclick=()=>showModal(`${mission().number} · ${mission().name}`,`<p><strong>Objective:</strong> ${escapeHtml(mission().objective)}</p><p><strong>Outcome:</strong> ${escapeHtml(victory?missionEngine()?.success:missionEngine()?.failure)}</p><div class="wizard-actions"><button class="btn primary" data-close>Done</button></div>`);
      $('#gameEndNewGame').onclick=confirmNewGame;
      requestAnimationFrame(()=>$('#reviewCompletedMission')?.focus());
      return;
    }
    if(state.finalResolution?.pending&&state.turningPoint>=MAX_TURNING_POINTS){
      const engine=missionEngine();
      app.innerHTML=`<section class="hero-card mission-outcome" aria-live="polite"><p class="eyebrow">BATTLE COMPLETE</p><h2>Battle Complete</h2><p>Turning Point ${MAX_TURNING_POINTS} has ended. Resolve the mission’s final success condition and record the outcome.</p>${engine?.type==='destruction'?`<div class="summary-box"><strong>Current Destruction score:</strong> ${state.missionState?.destruction||0}</div>`:''}<div class="summary-box"><strong>Success:</strong> ${escapeHtml(engine?.success||mission()?.victory?.win||'Resolve the mission success condition.')}</div><div class="summary-box"><strong>Failure:</strong> ${escapeHtml(engine?.failure||mission()?.victory?.lose||'Resolve the mission failure condition.')}</div><div class="button-row"><button class="btn danger" id="recordFinalDefeat" aria-label="Record mission defeat">Record Defeat</button><button class="btn primary" id="recordFinalVictory" aria-label="Record mission victory">Record Victory</button></div></section>`;
      $('#recordFinalDefeat').onclick=()=>completeMission('defeat');
      $('#recordFinalVictory').onclick=()=>completeMission('victory');
      requestAnimationFrame(()=>$('#recordFinalDefeat')?.focus());
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
    const value=model?(model.completed?'COMPLETE':`${model.value} / ${model.target}`):'DETAILS';
    const completeMark=model?.completed?'<span class="mission-complete-mark" aria-hidden="true">✓ </span>':'';
    const status=model?`${model.value} of ${model.target}${model.completed?', objective complete':''}`:'details';
    const name=model?.name||mission()?.name||'selected mission';
    return `<button class="hud-cell mission-hud" id="missionHud" type="button" aria-label="Mission details, ${escapeHtml(name)}, ${escapeHtml(status)}"><small>${escapeHtml(label)}</small><strong>${completeMark}${escapeHtml(value)}</strong></button>`;
  }

  function hud(){return `<div class="hud"><div><small>Turning<span class="portrait-break"><br></span> Point</small><strong>${state.turningPoint||'Setup'}</strong></div><button class="hud-cell hud-threat" id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"><small>Threat<span class="portrait-break"><br></span> Level</small><strong>${state.threat}</strong></button><div><small>Grade<span class="portrait-break"><br></span> Level</small><strong>${threatGrade()}</strong></div><div><small>Player<span class="portrait-break"><br></span> Ready</small><strong>${state.playerReady}</strong></div><div><small>NPO<span class="portrait-break"><br></span> Ready</small><strong>${readyNpos().length}</strong></div>${missionHudHtml()}</div><div class="threat-strip ${threatAdjustOpen?'':'hidden'}" id="threatAdjuster"><div><strong>THREAT LEVEL: ${threatLabel()}</strong><small>${threatGrade()===3?'Maximum Grade':`Next Grade at Threat Level ${nextGradeThreat()}`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function livingPlayerOptions(selected=''){
    return inPlayPlayerOperativeIds().filter(id=>!state.playerCasualtyIds.includes(id)).map(id=>`<option value="${escapeHtml(id)}" ${id===selected?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
  }

  const missionProgressRenderers = {
    escape:(engine,progress,{readOnly=false}={})=>{
      const escaped=new Set(progress.escapedIds);
      const rows=(state.playerRoster||[]).map(id=>{const incapacitated=state.playerCasualtyIds.includes(id), operativeState=playerOperativeState(id), escapedHere=escaped.has(id)&&operativeState.offBoardReason==='escaped', unavailable=operativeState.inPlay===false&&!escapedHere;return `<div class="mission-objective-row"><span><strong>${escapeHtml(playerName(id))}</strong><small>${escapedHere?'Escaped · Off Board':unavailable?`Off Board${operativeState.offBoardReason?` · ${escapeHtml(operativeState.offBoardReason)}`:''}`:incapacitated?'Incapacitated':'Still in the killzone'}</small></span>${readOnly||incapacitated||unavailable?'':`<button class="btn compact ${escapedHere?'secondary':'ghost'}" data-mission-escaped="${escapeHtml(id)}">${escapedHere?'Undo Escape':'Confirm Escape'}</button>`}</div>`;}).join('');
      const migrationWarning=progress.legacyEscapedCount&&!escaped.size?`<div class="summary-box"><strong>Legacy escape progress needs confirmation.</strong><br>This save recorded ${progress.legacyEscapedCount} escaped operative${progress.legacyEscapedCount===1?'':'s'} without names. No identity was guessed; confirm a named operative to replace the aggregate progress safely.</div>`:'';
      return `${migrationWarning}<p>${escaped.size} of ${state.playerRoster.length} operatives escaped. Resolve the mission only after every operative has left the killzone.</p><div class="mission-objective-list">${rows}</div>`;
    },
    sabotage:(engine,progress,{readOnly=false}={})=>{
      const completed=new Set(progress.completedFeatureIds);
      const model=objectiveEngine?.getMissionHudModel();
      const featureCard=feature=>{
        const labelParts=feature.label.match(/^(.*\S)\s+(\d+)$/);
        const featureLabel=labelParts?.[1]||feature.label;
        const featureNumber=labelParts?.[2]||'';
        const label=`${featureLabel}${featureNumber?` ${featureNumber}`:''}`;
        const openedBy=progress.featureOpenDetails?.[feature.id]?.openedBy;
        const status=completed.has(feature.id)?`Opened by ${openedBy==='operate-hatch'?'Operate Hatch':'Breach'}`:'Not opened';
        return `<span class="mission-feature-card__text"><span class="mission-feature-card__label">${escapeHtml(label)}</span><span class="mission-feature-card__status">${escapeHtml(status)}</span></span>`;
      };
      return `<p>${model?.value??completed.size} of ${model?.target??engine.required} required features have been permanently opened by Breach.</p><div class="mission-objective-grid">${engine.features.map(feature=>readOnly?`<div class="mission-objective-check">${featureCard(feature)}</div>`:`<label class="mission-objective-check"><input type="checkbox" data-mission-feature="${feature.id}" ${completed.has(feature.id)?'checked':''} ${missionOperationResolving?'disabled':''}>${featureCard(feature)}</label>`).join('')}</div>`;
    },
    transponder:(engine,progress,{readOnly=false}={})=>{
      const transponderFound=Object.values(progress.sites).includes('found');
      const sites=engine.sites.map(site=>{const result=progress.sites[site.id];return `<div class="mission-objective-row"><span><strong>${escapeHtml(site.label)}</strong><small>${result==='found'?'Transponder found':result==='empty'?'Removed — no transponder':'Unresolved'}</small></span>${readOnly||result||transponderFound?'' : `<button class="btn secondary compact" data-search-site="${site.id}">Pick Up & Resolve</button>`}</div>`;}).join('');
      const carrier=progress.carrierId?playerName(progress.carrierId):'None';
      const assignment=readOnly?'':transponderFound?`<div class="field"><label for="transponderCarrier">Current carrier</label><select id="transponderCarrier"><option value="">Marker is not being carried…</option>${livingPlayerOptions(progress.carrierId)}</select></div>`:`<div class="field"><label for="transponderOperative">Operative resolving the marker</label><select id="transponderOperative"><option value="">Select operative…</option>${livingPlayerOptions()}</select></div>`;
      const escapeControl=readOnly?'':`<button class="btn primary" id="transponderEscape" ${progress.carrierId&&isPlayerOperativeInPlay(progress.carrierId)&&!state.playerCasualtyIds.includes(progress.carrierId)&&!progress.escaped?'':'disabled'}>Confirm Carrier Escaped</button>`;
      return `<p>Pick up an unresolved marker, then roll D3. The transponder is found only if the result is higher than the number of other unresolved markers.</p>${progress.lastRoll?`<div class="summary-box"><strong>Last search:</strong> rolled ${progress.lastRoll.roll}; ${escapeHtml(progress.lastRoll.result)}.</div>`:''}${assignment}<div class="mission-objective-list">${sites}</div><div class="summary-box"><strong>Carrier:</strong> ${escapeHtml(carrier)}${readOnly&&progress.escaped?' · Escaped':''}</div>${escapeControl}`;
    },
    destruction:(engine,progress,{readOnly=false}={})=>{
      if(!objectiveEngine)return '<p class="muted">Mission automation is unavailable.</p>';
      const model=objectiveEngine.getMissionHudModel();
      const objective=objectiveDefinition.objectives.find(item=>item.id===model.objectiveId);
      const finalState=`<div class="summary-box"><strong>${model.completed?'✓ COMPLETE':'FINAL PROGRESS'}</strong><br>${model.value} / ${model.target} ${escapeHtml(objective.label)}</div>`;
      return `<p><strong>${model.value} / ${model.target} ${escapeHtml(objective.label)}</strong></p>${readOnly?finalState:'<p>Player operatives can perform Breach Sarcophagus during their activations while within the sarcophagus’s control range.</p>'}`;
    },
    scout:(engine,progress,{readOnly=false}={})=>{
      const scouted=new Set(progress.scoutedRoomIds);
      const rooms=engine.rooms.map(room=>{const awakening=progress.awakenedRooms[room.id],scout=progress.scoutedByRoom?.[room.id];const actions=readOnly?'':`<div class="mission-objective-actions">${awakening?'':`<button class="btn secondary compact" data-awaken-room="${room.id}">First Open / Entry</button>`}${awakening&&!awakening.placementConfirmed?`<button class="btn secondary compact" data-confirm-room-placement="${room.id}">Confirm Placement</button>`:''}${awakening?.placementConfirmed&&!scouted.has(room.id)?`<select aria-label="Operative scouting ${escapeHtml(room.label)}" data-scout-operative="${room.id}"><option value="">Select operative…</option>${livingPlayerOptions()}</select><button class="btn primary compact" data-scout-room="${room.id}">Confirm Cleared & Scout (1AP)</button>`:''}${scouted.has(room.id)?`<button class="btn ghost compact" data-correct-scout-room="${room.id}">Correct</button>`:''}</div>`;return `<div class="mission-objective-row"><span><strong>${escapeHtml(room.label)}</strong><small>${scouted.has(room.id)?`Scouted${scout?` by ${escapeHtml(playerName(scout))}`:''}`:awakening?`${awakening.count} NPOs generated${awakening.placementConfirmed?' and placed':' — placement required'}`:'Unopened / unentered'}</small></span>${actions}</div>`;}).join('');
      return `<p>${objectiveEngine?.getMissionHudModel().value??scouted.size} of ${objectiveEngine?.getMissionHudModel().target??engine.required} rooms scouted. Confirm that an eligible room is cleared on the tabletop before resolving the 1AP Scout Room action.</p><div class="mission-objective-list">${rooms}</div>`;
    },
    regroup:(engine,progress,{readOnly=false}={})=>{
      const survivors=inPlayLivingPlayerOperativeIds();
      const rows=survivors.map(id=>{const check=progress.operativeChecks[id]||{};const item=(key,label)=>readOnly?`<span>${check[key]?'✓':'—'} ${label}</span>`:`<label><input type="checkbox" data-regroup-check="${key}" data-operative-id="${id}" ${check[key]?'checked':''}> ${label}</label>`;return `<div class="mission-regroup-row"><strong>${escapeHtml(playerName(id))}</strong>${item('inDropZone','Wholly in NPO drop zone')}${item('outsideNpoControl','Outside NPO control range')}${item('nearPlayer','Within 3 inches of another Player operative')}</div>`;}).join('');
      return `<p>Record the position of every surviving operative. Victory is evaluated only when the Turning Point is finished.</p><div class="mission-objective-list">${rows}</div>`;
    }
  };

  function missionProgressHtml(readOnly=false){
    const engine=missionEngine(), progress=state.missionState||freshMissionState();
    const renderer=missionProgressRenderers[engine?.type];
    if(!renderer)return '';
    return `<section class="card mission-objective-card${readOnly?' mission-objective-readonly':''}"><p class="eyebrow">MISSION OBJECTIVE</p><h3>${escapeHtml(engine.progressLabel)}</h3><div>${renderer(engine,progress,{readOnly})}</div>${readOnly?'<p class="muted">Completed mission state is preserved for review.</p>':''}</section>`;
  }

  function updateMissionProgress(message){
    if(message)log(`${mission().name}: ${message}`);
    if(checkGameEnd())return;
    save();render();
  }

  function missionFeatureIdentity(feature){
    const match=String(feature?.id||'').match(/^(hatchway|breach)-(\d+)$/);
    if(!match)return null;
    return {featureId:feature.id,featureType:match[1]==='breach'?'breach-point':'hatchway',featureNumber:Number(match[2])};
  }

  function closedMissionFeatures(featureType){
    const engine=missionEngine(),opened=new Set(state.missionState?.completedFeatureIds||[]);
    if(engine?.type!=='sabotage')return [];
    return engine.features.filter(feature=>missionFeatureIdentity(feature)?.featureType===featureType&&!opened.has(feature.id));
  }

  function commitMissionFeatureOpened({missionId,featureId,featureType,featureNumber,openedBy='breach',source='mission-map',operativeId=null,turningPoint=state.turningPoint,transactionId}={}){
    const selectedMission=missionDefinition(missionId||state.missionId),engine=missionEngine(selectedMission);
    if(selectedMission?.id!=='demolition-protocol'||selectedMission.id!==state.missionId||engine?.type!=='sabotage')return {status:'unavailable'};
    const feature=engine.features.find(item=>item.id===featureId),identity=missionFeatureIdentity(feature);
    if(!feature||!identity||identity.featureType!==featureType||identity.featureNumber!==Number(featureNumber))return {status:'invalid-target'};
    const progress=state.missionState||(state.missionState=freshMissionState(selectedMission));
    const ids=new Set(progress.completedFeatureIds||[]),transactionKey=String(transactionId||`manual:${featureId}:${turningPoint}:${ids.has(featureId)?'existing':'open'}`);
    progress.featureTransactions=isRecord(progress.featureTransactions)?progress.featureTransactions:{};
    if(progress.featureTransactions[transactionKey]||ids.has(featureId))return {status:'already-open',feature};
    ids.add(featureId);
    const completedFeatureIds=engine.features.map(item=>item.id).filter(id=>ids.has(id));
    const before=completedFeatureIds.length-1,after=completedFeatureIds.length;
    const runtimeSnapshot=objectiveEngine?JSON.parse(JSON.stringify(objectiveEngine.getMissionRuntime())):null;
    try{
      if(objectiveEngine){
        objectiveEngine.setObjectiveValue('sabotagedFeatures',after,missionLifecycleContext({activationId:transactionKey,operativeId}));
        const historyId=`mission-feature-open:${transactionKey}`;
        const history=objectiveEngine.getMissionRuntime().history||[];
        const actionLabel=openedBy==='operate-hatch'?'Operate Hatch':'Breach';
        if(!history.some(entry=>entry.id===historyId))objectiveEngine.recordMissionHistory({id:historyId,type:'mission-feature-opened',title:`${actionLabel}: Opened ${feature.label}`,summary:`${actionLabel}: Opened ${feature.label}: +1`,featureId,openedBy,source,operativeId,turningPoint,delta:1,changes:[{objectiveId:'sabotagedFeatures',before,after}]},missionLifecycleContext({activationId:transactionKey,operativeId}));
      }
    }catch(error){
      if(objectiveEngine&&runtimeSnapshot)state.missionRuntime=objectiveEngine.restoreMissionRuntime(objectiveDefinition,runtimeSnapshot,missionLifecycleContext());
      console.error('[MissionFeature] Feature commit failed.',error);
      return {status:'commit-failed',feature};
    }
    progress.completedFeatureIds=completedFeatureIds;
    progress.featureOpenDetails=isRecord(progress.featureOpenDetails)?progress.featureOpenDetails:{};
    progress.featureOpenDetails[featureId]={...identity,isOpen:true,openedBy,source,operativeId,turningPoint,transactionId:transactionKey};
    progress.featureTransactions[transactionKey]=featureId;
    const actionLabel=openedBy==='operate-hatch'?'Operate Hatch':'Breach';
    const activity=`${source==='player-activation'?`${playerName(operativeId)} used ${actionLabel} on`:'Opened'} ${feature.label}${source==='player-activation'?'':' by Breach'}: +1.`;
    log(`${mission().name}: ${activity}`);
    return {status:'completed',feature,before,after,transactionId:transactionKey};
  }

  function bindMissionProgressControls(){
    $$('[data-mission-escaped]').forEach(button=>button.onclick=async()=>{
      const id=button.dataset.missionEscaped, ids=new Set(state.missionState.escapedIds);
      const wasEscaped=ids.has(id);
      if(!wasEscaped&&!isPlayerOperativeInPlay(id)){showToast(`${playerName(id)} is already off the battlefield.`);return;}
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction(wasEscaped?'correctEscape':'recordEscape',{...missionLifecycleContext(),operativeId:id,gameplay:{...missionLifecycleContext().gameplay,escapedOperativeCount:ids.size+(wasEscaped?-1:1)}})):null;
      if(objectiveEngine&&!outcome)return;
      wasEscaped?ids.delete(id):ids.add(id);
      state.missionState.escapedIds=[...ids];
      delete state.missionState.legacyEscapedCount;
      if(objectiveEngine)objectiveEngine.setObjectiveValue('escapedOperatives',state.missionState.escapedIds.length,missionLifecycleContext());
      const model=objectiveEngine?.getMissionHudModel();
      if(outcome&&model?.completed&&outcome.changes?.[0]?.before<model.target)showMissionResult('ESCAPE RECORDED',outcome);
      updateMissionProgress(`${playerName(id)} ${ids.has(id)?'escaped via the Escape marker':'escape status was corrected'}.`);
    });
    $$('[data-mission-feature]').forEach(input=>input.onchange=async()=>{
      const ids=new Set(state.missionState.completedFeatureIds);
      $$('[data-mission-feature]').forEach(control=>{control.disabled=true;});
      const feature=missionEngine()?.features.find(item=>item.id===input.dataset.missionFeature),identity=missionFeatureIdentity(feature);
      if(input.checked){
        const outcome=commitMissionFeatureOpened({...identity,missionId:state.missionId,source:'mission-map',transactionId:`mission-map:${identity?.featureId}:${Date.now()}`});
        if(outcome.status!=='completed'){input.checked=false;$$('[data-mission-feature]').forEach(control=>{control.disabled=false;});return;}
        updateMissionProgress();
        return;
      }
      ids.delete(input.dataset.missionFeature);
      state.missionState.completedFeatureIds=missionEngine().features.map(item=>item.id).filter(id=>ids.has(id));
      delete state.missionState.featureOpenDetails?.[input.dataset.missionFeature];
      if(objectiveEngine){
        const before=ids.size+1,after=ids.size;
        objectiveEngine.setObjectiveValue('sabotagedFeatures',after,missionLifecycleContext());
        objectiveEngine.recordMissionHistory({type:'mission-feature-corrected',title:`Corrected ${feature.label}`,summary:`Corrected ${feature.label}: -1`,featureId:feature.id,turningPoint:state.turningPoint,delta:-1,changes:[{objectiveId:'sabotagedFeatures',before,after}]},missionLifecycleContext());
      }
      updateMissionProgress(`corrected ${feature.label}.`);
    });
    $$('[data-search-site]').forEach(button=>button.onclick=async()=>{
      const carrier=$('#transponderOperative')?.value;
      if(!carrier){showToast('Select the operative picking up this marker.');return;}
      const progress=state.missionState;
      const otherRemaining=missionEngine().sites.filter(site=>site.id!==button.dataset.searchSite&&!progress.sites[site.id]).length;
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('searchTransponder',{...missionLifecycleContext(),operativeId:carrier})):null;
      if(objectiveEngine&&!outcome)return;
      const result=outcome?.results?.searchRoll?.total??rollD3(), found=result>otherRemaining;
      progress.sites[button.dataset.searchSite]=found?'found':'empty';
      if(found)progress.carrierId=carrier;
      progress.lastRoll={siteId:button.dataset.searchSite,roll:result,result:found?'transponder found':'marker removed'};
      updateMissionProgress(`searched ${button.dataset.searchSite}, rolled ${result}, and ${found?'found the transponder':'removed the marker'}.`);
    });
    $('#transponderCarrier')?.addEventListener('change',event=>{state.missionState.carrierId=event.target.value||null;save();render();});
    $('#transponderEscape')?.addEventListener('click',async()=>{
      const carrierId=state.missionState.carrierId;
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('recordTransponderEscape',{...missionLifecycleContext(),operativeId:carrierId})):null;
      if(objectiveEngine&&!outcome)return;
      state.missionState.escaped=true;
      updateMissionProgress(`${playerName(carrierId)} escaped carrying the transponder.`);
    });
    $('#resolveMissionAction')?.addEventListener('click',confirmMissionAction);
    $$('[data-awaken-room]').forEach(button=>button.onclick=async()=>{
      const actionId=missionEngine().actions?.awakenRoom;
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction(actionId,missionLifecycleContext())):null;
      if(objectiveEngine&&!outcome)return;
      const count=Math.min(5,(outcome?.results?.awakenRoll?.total??rollD3())+threatGrade()), ids=[];
      for(let i=0;i<count&&activeNpos().length<MAX_NPOS;i++){
        const result=availableGenerationResult();if(!result)break;
        const n=createNpo(result.type,`${result.type} ${button.dataset.awakenRoom}`,{weaponId:result.weaponId,ready:true,dormant:false,deployed:false,order:'Conceal'});
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
    $$('[data-scout-room]').forEach(button=>button.onclick=async()=>{
      const operativeId=$(`[data-scout-operative="${button.dataset.scoutRoom}"]`)?.value;
      if(!operativeId||!inPlayLivingPlayerOperativeIds().includes(operativeId)){showToast('Select an in-play Player operative to perform Scout Room.');return;}
      const actionId=missionEngine().actions?.recordScout;
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction(actionId,{...missionLifecycleContext(),operativeId})):null;
      if(objectiveEngine&&!outcome)return;
      const ids=new Set(state.missionState.scoutedRoomIds);ids.add(button.dataset.scoutRoom);state.missionState.scoutedRoomIds=[...ids];
      state.missionState.scoutedByRoom[button.dataset.scoutRoom]=operativeId;
      const grade=threatGrade(), gradeFloor=[0,0,5,10][grade];
      if(state.threat>gradeFloor)setThreat(gradeFloor-state.threat,'Scout Room');
      updateMissionProgress(`scouted ${button.dataset.scoutRoom}.`);
    });
    $$('[data-correct-scout-room]').forEach(button=>button.onclick=async()=>{
      const actionId=missionEngine().actions?.correctScout;
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction(actionId,missionLifecycleContext())):null;
      if(objectiveEngine&&!outcome)return;
      const ids=new Set(state.missionState.scoutedRoomIds);ids.delete(button.dataset.correctScoutRoom);state.missionState.scoutedRoomIds=[...ids];
      delete state.missionState.scoutedByRoom[button.dataset.correctScoutRoom];
      updateMissionProgress(`corrected the Scout Room record for ${button.dataset.correctScoutRoom}.`);
    });
    $$('[data-regroup-check]').forEach(input=>input.onchange=()=>{
      const id=input.dataset.operativeId;
      state.missionState.operativeChecks[id]={...(state.missionState.operativeChecks[id]||{}),[input.dataset.regroupCheck]:input.checked};
      state.missionState.lastCheckedTurningPoint=state.turningPoint;save();
    });
  }

  function renderPlay(){
    const gradeDescription=state.gradeMilestone?gradeGameplayDescription(state.gradeMilestone.grade,{threat:state.gradeMilestone.threat,turningPoint:Math.max(2,state.turningPoint),suggestedInitiative:state.strategyData?.suggestedInitiative,restlessTombEnabled:state.restlessTombEnabled}):null;
    const milestone=gradeDescription?`<section class="grade-milestone" role="dialog" aria-labelledby="grade-milestone-heading" aria-describedby="grade-milestone-description"><div><small>THREAT ESCALATION</small><h2 id="grade-milestone-heading">Grade ${gradeDescription.grade}: ${escapeHtml(gradeDescription.name)}</h2><span>${escapeHtml(gradeDescription.threatRange)}</span><section id="grade-milestone-description" class="grade-gameplay-changes" aria-labelledby="grade-gameplay-heading"><h3 id="grade-gameplay-heading">GAMEPLAY CHANGES</h3><ul>${gradeDescription.effects.map(effect=>`<li>${escapeHtml(effect.text)}</li>`).join('')}</ul></section></div><button class="btn ghost compact" id="dismissGradeMilestone">Dismiss</button></section>`:'';
    app.innerHTML=hud()+milestone+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${state.phase!=='strategy'?activeEventEffectsHtml():''}${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
    bindPlay();
    if(gradeDescription)requestAnimationFrame(()=>$('#dismissGradeMilestone')?.focus({preventScroll:true}));
  }

  function activeEventEffectsHtml(){
    const active=state.eventState.active||[];
    if(!active.length)return '';
    const heading=`ACTIVE TOMB WORLD ${active.length===1?'EVENT':'EVENTS'}`;
    return `<section class="card active-events-panel"><details class="active-events-details"><summary class="active-events-summary" aria-label="${active.length===1?'Active Tomb World Event':'Active Tomb World Events'}, ${active.length} active"><span>${heading}</span><span class="active-events-count">${active.length} ACTIVE</span></summary><div class="active-events-content">${active.map(event=>`<div class="summary-box"><strong>${escapeHtml(event.title)}</strong><br>${escapeHtml(event.text)}</div>`).join('')}</div></details></section>`;
  }

  function tombWorldEventActive(definitionId){
    return EventEffects.activeRecords(state,state.turningPoint).some(event=>event.definitionId===definitionId);
  }

  function nextStepCard(){
    if(state.completed) return `<section class="next-card"><span class="phase">MISSION COMPLETE</span><h2>Record the outcome</h2><p>The mission has reached its conclusion. Review the Journal or begin a new game.</p><button class="btn primary big-action" id="newGameFromPlay">Start New Game</button></section>`;
    if(state.phase==='between'){
      if(state.turningPoint>=MAX_TURNING_POINTS){
        return `<section class="next-card"><span class="phase">BATTLE COMPLETE</span><h2>Resolving final mission outcome</h2><p>Turning Point ${MAX_TURNING_POINTS} has ended. No further Turning Point can begin.</p></section>`;
      }
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
    if(state.nextSide==='player' && playerOperativesRemaining()>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ${activationProgressLabel()}</span><h2>Player Activation</h2><p>Activate one Player operative on the tabletop. After it completes, the Guide will alternate to an NPO if one is ready.</p><button class="btn primary big-action" id="playerActivation">Activate an Operative</button></section>`;
    if(state.nextSide==='npo' && readyNpos().length>0)return `<section class="next-card npo-activation-card"><span class="phase">NPO ACTIVATION · ${activationProgressLabel()}</span><h2 class="npo-activation-title">NPO Activation</h2><p class="npo-activation-meta">Identify the next ready NPO using the Threat Principle.</p><button class="btn primary big-action" id="npoActivation">Activate NPO</button></section>`;
    setNextActivation(state.nextSide==='player'?'npo':'player');
    save();
    return nextStepCard();
  }

  function missionStrategyPending(){
    return missionEngine()?.type==='escape'&&state.turningPoint>1&&!state.missionState.escapedIds.length&&!state.missionState.auspexCalibrations[state.turningPoint];
  }

  function missionStrategyPromptHtml(){
    if(missionEngine()?.type!=='escape'||state.turningPoint<=1||state.missionState.escapedIds.length)return '';
    const calibration=state.missionState.auspexCalibrations[state.turningPoint];
    if(calibration)return `<div class="summary-box"><p class="eyebrow">MISSION RULE</p><strong>Auspex Calibration</strong><br>${escapeHtml(calibration.instruction)}</div>`;
    return `<div class="summary-box"><p class="eyebrow">MISSION RULE</p><strong>Auspex Calibration</strong><br>No operatives have escaped. Resolve this mission rule before continuing.<div class="event-controls"><button class="btn secondary" id="resolveAuspexCalibration">Roll Auspex Calibration</button></div></div>`;
  }

  function strategyEventPresentation(data=state.strategyData||{}){
    const currentRequirement=data.eventRequirementTurningPoint===state.turningPoint;
    const currentEvents=currentRequirement&&Array.isArray(data.events)?data.events:[];
    return {
      required:currentRequirement?(Number(data.requiredEventCount)||0):0,
      cardsDrawn:currentEvents.length,
      resolved:currentEvents.filter(event=>event.status==='resolved').length,
      events:currentEvents
    };
  }

  function strategyEventRequirementLabel(data,presentation){
    if(!presentation.required)return '';
    const eventWord=presentation.required===1?'event':'events';
    const standardRequired=Number(data.normalEventCount)>0||presentation.events.some(event=>event.requiredBy==='standard');
    const source=standardRequired?'the standard Tomb World rules':'Restless Tomb';
    return `${presentation.required} ${eventWord} required by ${source}.`;
  }

  function strategyEventActiveEffect(event,activeEffects=state.eventState.active||[]){
    return activeEffects.find(active=>{
      if(event.instanceId&&active.instanceId)return event.instanceId===active.instanceId;
      return Boolean(event.definitionId&&active.definitionId&&event.definitionId===active.definitionId);
    })||null;
  }

  function strategyEventSummary(presentation){
    const {required,cardsDrawn,resolved}=presentation;
    return {
      visible:`${required} required • ${cardsDrawn} ${cardsDrawn===1?'card':'cards'} drawn • ${resolved} resolved`,
      accessible:`${required} ${required===1?'event':'events'} required, ${cardsDrawn} event ${cardsDrawn===1?'card':'cards'} drawn, ${resolved} ${resolved===1?'event':'events'} resolved`
    };
  }

  function strategyViewStep(data=state.strategyData||{}){
    return ['actions','events','review'].includes(data.viewStep)?data.viewStep:'actions';
  }

  function strategyProgressHtml(step){
    const steps={actions:[1,'Strategy Actions'],events:[2,'Tomb World Events'],review:[3,'Reinforcements & Review']};
    const [number,label]=steps[step];
    return `<div class="strategy-progress" role="status" aria-label="Strategy Phase, step ${number} of 3: ${label}"><span>STRATEGY PHASE · STEP ${number} OF 3</span><div class="strategy-progress-bar" aria-hidden="true">${[1,2,3].map(item=>`<i class="${item<=number?'complete':''}"></i>`).join('')}</div></div>`;
  }

  function strategyNavigationHtml({backId,backLabel,continueId,continueLabel,disabled=false,disabledReason=''}){
    return `<div class="strategy-navigation${backId?' two-actions':''}">${backId?`<button type="button" class="btn ghost" id="${backId}">${backLabel}</button>`:''}<button type="button" class="btn primary" id="${continueId}" ${disabled?'disabled':''}${disabledReason?` title="${escapeHtml(disabledReason)}"`:''}>${continueLabel}</button></div>`;
  }

  function strategyRequiredRedrawPending(){
    return Object.values(state.eventState.transactions||{}).some(transaction=>transaction?.type==='event-redraw'&&transaction.turningPoint===state.turningPoint&&!transaction.committed);
  }

  function canLeaveStrategyActions(){return !missionStrategyPending();}

  function canLeaveStrategyEvents(){
    const d=state.strategyData||{};
    return !d.eventPending&&(d.events||[])[d.eventIndex||0]?.status!=='drawn'&&!strategyRequiredRedrawPending();
  }

  function canCompleteStrategyPhase(){
    return state.phase==='strategy'&&state.strategyStage==='summary'&&canLeaveStrategyActions()&&canLeaveStrategyEvents()&&state.reinforcementState.status!=='placement';
  }

  function showStrategyViewStep(step,fromStep){
    const d=state.strategyData;
    if(state.phase!=='strategy'||state.strategyStage!=='summary'||!d||strategyViewStep(d)!==fromStep)return;
    const allowed=fromStep==='actions'&&step==='events'?canLeaveStrategyActions()
      : fromStep==='events'&&step==='review'?canLeaveStrategyEvents()
      : (fromStep==='events'&&step==='actions')||(fromStep==='review'&&step==='events');
    if(!allowed)return;
    d.viewStep=step;
    save();render();
    requestAnimationFrame(()=>{
      window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
      focusInitialDialogControl(app);
    });
  }

  function strategyActionsStepHtml(d){
    const missionPending=missionStrategyPending();
    const scuttlingEligible=ceaselessScuttlingEligible()&&d.ceaselessScuttlingTurningPoint!==state.turningPoint;
    const scuttlingCard=state.turningPoint>1?`<section class="card reinforcement-card"><p class="eyebrow">STRATEGIC GAMBIT</p><h3>A Ceaseless Scuttling</h3><p>${scuttlingEligible?'Fewer than three Macrocyte Warriors remain. You may reuse an incapacitated miniature to set up a new operative instance.':'Unavailable: three Warriors remain, or this gambit was already resolved this turning point.'}</p><button class="btn secondary" id="ceaselessScuttling" ${scuttlingEligible?'':'disabled'}>Use A Ceaseless Scuttling</button></section>`:'';
    const actionsHtml=`${missionStrategyPromptHtml()}${factionGuidanceHtml('gambits')}${scuttlingCard}`;
    return `${strategyProgressHtml('actions')}<h2 id="strategy-step-heading">Resolve Strategy Phase Actions</h2><div class="strategy-phase-guide"><h3>Strategy Phase Checklist</h3><ol><li>Generate Command Points as required.</li><li>Play any Strategic Ploys.</li><li>Resolve abilities and mission rules.</li><li>Review optional Strategic Gambits.</li></ol></div>${actionsHtml||'<p class="strategy-empty-message">No additional guided Strategy Phase actions are required.</p>'}${strategyNavigationHtml({continueId:'continueStrategyEvents',continueLabel:'Continue to Tomb World Events',disabled:missionPending,disabledReason:missionPending?'Resolve the mandatory mission Strategy Phase rule before continuing.':''})}`;
  }

  function strategyEventsStepHtml(d){
    const presentation=strategyEventPresentation(d);
    const displayedEvents=presentation.events.filter((event,index)=>event.status!=='drawn'||index===d.eventIndex);
    const activeEffects=state.eventState.active||[];
    const unmatched=activeEffects.filter(active=>!displayedEvents.some(event=>strategyEventActiveEffect(event,[active]))).map(event=>`<div class="summary-box"><strong>${escapeHtml(event.title)}</strong><br>${escapeHtml(event.text)}</div>`).join('');
    const requirement=strategyEventRequirementLabel(d,presentation), summary=strategyEventSummary(presentation);
    const hasEvents=presentation.required||presentation.cardsDrawn||unmatched;
    const content=hasEvents?`${requirement?`<p class="strategy-event-requirement">${escapeHtml(requirement)}</p>`:''}<p class="strategy-event-summary" aria-label="${summary.accessible}">${summary.visible}</p>${displayedEvents.map(event=>strategyEventHtml(event,activeEffects)).join('')}${unmatched?`<h3 class="strategy-section-heading">Other Active Event Effects</h3>${unmatched}`:''}`:'<div class="summary-box"><strong>No Tomb World Event</strong><p>No Tomb World event is required during this Strategy Phase.</p></div>';
    const blocked=!canLeaveStrategyEvents();
    return `${strategyProgressHtml('events')}<h2 id="strategy-step-heading">Resolve Tomb World Events</h2>${content}${strategyNavigationHtml({backId:'backStrategyActions',backLabel:'Back to Strategy Actions',continueId:'continueStrategyReview',continueLabel:'Continue to Reinforcements',disabled:blocked,disabledReason:blocked?'Resolve the required Tomb World event or redraw before continuing.':''})}`;
  }

  function strategyReviewStepHtml(d){
    const deployingNpos=sortedNposForDisplay((state.reinforcementState.operativeIds||[]).map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean));
    const deployedNpos=deployingNpos.filter(npo=>npo.reinforcement?.placementConfirmed);
    const pendingNpos=deployingNpos.filter(npo=>!npo.reinforcement?.placementConfirmed);
    const blockedCount=state.reinforcementState.blocked||d.blocked||0;
    const capacityBlocked=state.reinforcementState.blockedByCapacity||0;
    const inventoryBlocked=state.reinforcementState.blockedByInventory||0;
    const blockedReason=reinforcementBlockedReason(capacityBlocked,inventoryBlocked,blockedCount);
    const deployedSection=deployedNpos.length?`<div class="reinforcement-deployed"><h3>${deployedNpos.length} NPO${deployedNpos.length===1?'':'s'} deployed</h3><ul class="reinforcement-list">${deployedNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul></div>`:'';
    const pendingSection=pendingNpos.length?`<div class="reinforcement-pending"><h3>Deploy ${pendingNpos.length} NPO${pendingNpos.length===1?'':'s'}</h3><ul class="reinforcement-list">${pendingNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul><p>Deploy ${pendingNpos.length===1?'this NPO':'these NPOs'} onto the battlefield using the Tomb World reinforcement rules.</p></div>`:'';
    const reinforcementCard=deployingNpos.length||blockedCount
      ? `<section class="card reinforcement-card" aria-live="polite"><p class="eyebrow">REINFORCEMENTS</p>${deployedSection}${pendingSection}${blockedCount?`<div class="reinforcement-blocked" role="status"><h3>${deployingNpos.length?`${blockedCount} additional reinforcement${blockedCount===1?'':'s'} could not be deployed`:'No reinforcements could be deployed'}</h3><p>${blockedReason}</p></div>`:''}</section>`
      : '<div class="summary-box strategy-empty-message">No reinforcements were generated this Turning Point.</div>';
    const placements=deployingNpos.map(npo=>`<label class="check-row"><input type="checkbox" data-reinforcement-placement="${escapeHtml(npo.id)}" aria-label="Confirm placement for ${escapeHtml(npoName(npo))}" ${npo.reinforcement?.placementConfirmed?'checked':''}><span><strong>${escapeHtml(npoName(npo))} · ${escapeHtml(npoWeapon(npoDefinition(npo.type),npo.weaponId)?.name||npo.weaponId)}</strong><small>Randomly determine an open hatchway, set up this operative with a Conceal order following the Tomb World reinforcement placement restrictions, then confirm.</small></span></label>`).join('');
    const showStatTooltips=!window.matchMedia('(max-width:600px)').matches;
    const tooltipAttrs=text=>showStatTooltips?` tabindex="0" data-tooltip="${text}"`:'';
    const infoDot=showStatTooltips?'<span class="info-dot">i</span>':'';
    const battlefield=`<section class="battlefield-state-section" aria-labelledby="battlefield-state-heading"><h3 id="battlefield-state-heading" class="strategy-section-heading">Current Battlefield State</h3><div class="stat-grid strategy-stat-grid"><div class="stat tooltip-stat"${tooltipAttrs('Threat rises from loud or aggressive actions. Higher Threat can increase the Grade, reinforcements, and Tomb World events.')}><small>THREAT LEVEL ${infoDot}</small><strong>${state.threat}</strong></div><div class="stat tooltip-stat"${tooltipAttrs('Grade 0–3 is derived from Threat and determines reinforcement pressure and some events.')}><small>GRADE LEVEL ${infoDot}</small><strong>${threatGrade()}</strong></div><div class="stat tooltip-stat"${tooltipAttrs('The number of living NPOs that are Ready and may still activate during this Turning Point.')}><small>NPOs Ready ${infoDot}</small><strong>${readyNpos().length}</strong></div></div></section>`;
    const unresolved=!canLeaveStrategyEvents();
    const blocked=!canCompleteStrategyPhase();
    const warning=unresolved?'<div class="summary-box strategy-warning"><strong>Event resolution is incomplete.</strong><p>Return to Tomb World Events and finish the required event transaction.</p></div>':'';
    const reason=state.reinforcementState.status==='placement'?'Confirm every reinforcement placement before completing the Strategy Phase.':missionStrategyPending()?'Resolve the mandatory mission Strategy Phase rule before completing the Strategy Phase.':unresolved?'Resolve the required Tomb World event or redraw before completing the Strategy Phase.':'';
    return `${strategyProgressHtml('review')}<h2 id="strategy-step-heading">Deploy Reinforcements and Review</h2>${warning}${reinforcementCard}${deployingNpos.length?`<div class="checklist">${placements}</div>`:''}${battlefield}${strategyNavigationHtml({backId:'backStrategyEvents',backLabel:'Back to Tomb World Events',continueId:'continueStrategy',continueLabel:'Strategy Phase Complete',disabled:blocked,disabledReason:reason})}`;
  }

  function reinforcementBlockedReason(capacityBlocked,inventoryBlocked,totalBlocked){
    if(capacityBlocked&&inventoryBlocked)return 'The battlefield limit was reached and no eligible physical NPO models remain.';
    if(capacityBlocked)return `The battlefield limit of ${MAX_NPOS} NPOs was reached.`;
    if(inventoryBlocked)return 'No eligible physical NPO models remain in the Tomb World inventory.';
    return totalBlocked?`The battlefield limit of ${MAX_NPOS} NPOs was reached.`:'';
  }

  function strategyCard(){
    const d=state.strategyData||{};
    if(state.strategyStage==='mission-ready')return `<section class="next-card"><span class="phase">STRATEGY PHASE · READY STEP</span><h2>Mission event pending</h2><p>Complete the mission Ready-step event before initiative is determined.</p><button class="btn primary big-action" id="retryMissionReady">Continue Mission Event</button></section>`;
    if(state.strategyStage!=='summary')return '';
    const step=strategyViewStep(d);
    return `<section class="next-card strategy-step">${step==='actions'?strategyActionsStepHtml(d):step==='events'?strategyEventsStepHtml(d):strategyReviewStepHtml(d)}</section>`;
  }

  function strategyEventHtml(event,activeEffects=state.eventState.active||[]){
    const title=event.title||event[0],description=event.text||event.description||event[1];
    if(event.type!=='tomb-world-event')return `<div class="summary-box"><strong>${escapeHtml(title)}</strong><br>${escapeHtml(description)}</div>`;
    const isRelocation=event.definitionId==='transdimensional-relocation';
    if(isRelocation&&event.status==='drawn')prepareTransdimensionalRelocation(event);
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
    const activeEffect=event.status==='resolved'?strategyEventActiveEffect(event,activeEffects):null;
    const statusLabels={drawn:'PENDING',resolved:activeEffect?'RESOLVED • ACTIVE':'RESOLVED',redrawn:'REDRAWN'};
    const activeLabel=activeEffect?.expiresAfterTurningPoint!==undefined?'Resolved and active until the end of the Turning Point':'Resolved and active';
    const statusLabel=statusLabels[event.status]||escapeHtml(event.status).toUpperCase();
    const resolvedHeadingId=isRelocation&&event.status==='resolved'?' id="resolved-transdimensional-relocation-heading"':'';
    const eventDetails=`${eventHeader}<div class="tomb-world-event-heading"><h3 class="tomb-world-event-title"${resolvedHeadingId}>${escapeHtml(title)}</h3><span class="strategy-event-status" data-event-status="${escapeHtml(event.status)}"${activeEffect?` data-event-active="true" aria-label="${activeLabel}"`:''}>${statusLabel}</span></div><div class="tomb-world-event-effect"><div class="tomb-world-event-effect-label">Effect</div><p class="tomb-world-event-description">${escapeHtml(description)}</p></div>`;
    if(event.status!=='drawn')return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite">${eventDetails}<div class="event-resolution">${escapeHtml(event.result||'Complete')}</div></div>`;
    if(isRelocation){
      const selected=event.resolution?.playerOperativeIds||[];
      if(selected.length!==2)return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite">${eventDetails}<div class="event-resolution">Another event card is being drawn because fewer than two Player operatives are on the battlefield.</div></div>`;
      const names=selected.map(playerName);
      const accessibleNames=names.join(' and ');
      return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite" aria-label="Transdimensional Relocation. Operatives to swap: ${escapeHtml(accessibleNames)}.">${eventDetails}<div class="event-resolution"><h4 id="transdimensional-relocation-selection-heading">OPERATIVES TO SWAP</h4><ol>${names.map(name=>`<li>${escapeHtml(name)}</li>`).join('')}</ol><p>Remove both operatives from the killzone. Set each operative up in the other operative’s previous position.</p><p>Keep their wounds, order, Ready or Expended state, and all other statuses unchanged.</p></div><div class="event-controls"><button class="btn primary" id="resolveStrategyEvent" aria-label="Confirm positions swapped for ${escapeHtml(accessibleNames)}">Confirm Positions Swapped</button></div></div>`;
    }
    const labels={
      'awakened-warrior':'Confirm Necron Warrior Placement',
      'chittering-drone':'Confirm Scarab Placement',
      'maze-reforms':'Confirm Terrain Changes'
    };
    const scarabChoices=event.execution.type==='chittering-drone'&&Array.isArray(event.eligibleNpoIds)&&event.eligibleNpoIds.length>1
      ? `<div class="field"><label for="eventNpoSelect">Wounded Scarab Swarm</label><select id="eventNpoSelect"><option value="">Select a Scarab Swarm...</option>${sortedNposForDisplay(event.eligibleNpoIds.map(id=>activeNpos().find(item=>item.id===id)).filter(Boolean)).map(n=>`<option value="${escapeHtml(n.id)}">${escapeHtml(npoName(n))} — ${n.wounds} of ${n.maxWounds} wounds</option>`).join('')}</select></div>`:'';
    const impossibleControl=event.execution.type==='maze-reforms'?'<button type="button" class="btn secondary" id="redrawStrategyEvent" aria-label="No valid terrain changes are possible; draw another Tomb World event card">No Valid Changes · Draw Again</button>':'';
    return `<div class="summary-box strategy-event tomb-world-event-card">${eventDetails}<div class="event-controls">${scarabChoices}<button class="btn primary" id="resolveStrategyEvent" ${scarabChoices?'disabled':''}>${labels[event.definitionId]||labels[event.execution.type]||'Resolve Event'}</button>${impossibleControl}</div></div>`;
  }

  function activationTracker(){
    const activatedIds=new Set(state.playerActivatedIds||[]);
    const casualtyIds=new Set(state.playerCasualtyIds||[]);
    const playerRows=(state.playerRoster||[]).map(operativeId=>{
      const casualty=casualtyIds.has(operativeId);
      const activated=activatedIds.has(operativeId);
      const operativeState=playerOperativeState(operativeId);
      const status=operativeState.inPlay===false?(operativeState.offBoardReason==='escaped'?'ESCAPED':'OFF BOARD'):casualty?'ELIMINATED':activated?'ACTIVATED':'READY';
      const cls=operativeState.inPlay===false?'activated':casualty?'eliminated':activated?'activated':'ready';
      return `<button type="button" class="tracker-operative player ${cls}" data-player-operative="${operativeId}" title="Select ${escapeHtml(playerName(operativeId))} to mark it eliminated or restore it">
        <span>${escapeHtml(playerName(operativeId))}</span><span class="tracker-operative-status">${casualty?'<span class="tracker-elimination-icon" aria-hidden="true">☠</span>':''}<strong>${status}</strong></span>
      </button>`;
    }).join('');
    const npoRows=sortedNposForDisplay(trackerNpos()).map(n=>{
      const trackerStatus=npoTrackerStatus(n);
      return `<div class="tracker-operative npo ${trackerStatus.className}"><span>${escapeHtml(npoName(n))}</span><span class="tracker-operative-status">${trackerStatus.status==='ELIMINATED'?'<span class="tracker-elimination-icon" aria-hidden="true">☠</span>':''}<strong>${trackerStatus.status}</strong></span></div>`;
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
    const battlefieldState=playerOperativeState(operativeId);
    if(battlefieldState.inPlay===false){showToast(`${playerName(operativeId)} is off the battlefield.`);return;}
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
    if(state.phase==='between'&&state.turningPoint>=MAX_TURNING_POINTS)void resolveTurningPointLimit();
    $('#dismissGradeMilestone')?.addEventListener('click',()=>{state.gradeMilestone=null;save();render();});
    $$('[data-player-operative]').forEach(button=>button.addEventListener('click',()=>showPlayerOperativeStatus(button.dataset.playerOperative)));
    $('#startTp')?.addEventListener('click',startTurningPoint);
    $$('[data-reinforcement-placement]').forEach(input=>input.addEventListener('change',()=>confirmReinforcementPlacement(input.dataset.reinforcementPlacement,input.checked)));
    $('#eventNpoSelect')?.addEventListener('change',e=>{$('#resolveStrategyEvent').disabled=!e.target.value;});
    $('#resolveStrategyEvent')?.addEventListener('click',event=>{
      const button=event.currentTarget;
      if(button.disabled)return;
      if(currentEvent()?.definitionId==='transdimensional-relocation')button.disabled=true;
      resolveStrategyEvent(button);
    });
    const pendingRelocation=currentEvent();
    const relocationVisible=strategyViewStep(state.strategyData)==='events'&&pendingRelocation?.definitionId==='transdimensional-relocation'&&pendingRelocation.status==='drawn';
    if(relocationVisible){
      if(validTransdimensionalRelocationSelection(pendingRelocation)){
        if(focusedRelocationInstanceId!==pendingRelocation.instanceId){
          focusedRelocationInstanceId=pendingRelocation.instanceId;
          requestAnimationFrame(()=>focusInitialDialogControl(app));
        }
      }
      else setTimeout(()=>redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.'),0);
    }else focusedRelocationInstanceId=null;
    $('#redrawStrategyEvent')?.addEventListener('click',event=>{
      const button=event.currentTarget;
      if(button.disabled)return;
      button.disabled=true;
      if(!redrawCurrentEvent('No breach or open hatchway could be changed.'))button.disabled=false;
    });
    $('#continueStrategyEvents')?.addEventListener('click',()=>showStrategyViewStep('events','actions'));
    $('#backStrategyActions')?.addEventListener('click',()=>showStrategyViewStep('actions','events'));
    $('#continueStrategyReview')?.addEventListener('click',()=>showStrategyViewStep('review','events'));
    $('#backStrategyEvents')?.addEventListener('click',()=>showStrategyViewStep('events','review'));
    $('#continueStrategy')?.addEventListener('click',()=>{if(!canCompleteStrategyPhase())return;beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player');});
    $('#ceaselessScuttling')?.addEventListener('click',showCeaselessScuttling);
    $('#retryMissionReady')?.addEventListener('click',continueTurningPointStart);
    $('#playerActivation')?.addEventListener('click',()=>showPlayerActivation());
    $('#npoActivation')?.addEventListener('click',showNpoSelection);
    $('#missionHud')?.addEventListener('click',showMissionDetails);
    bindMissionProgressControls();
    $('#resolveAuspexCalibration')?.addEventListener('click',async()=>{
      const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('auspexCalibration',missionLifecycleContext())):null;
      if(objectiveEngine&&!outcome)return;
      const directionRoll=outcome?.results?.directionRoll?.total||rollD3(),distance=(outcome?.results?.distanceRoll?.total||rollD3())+3;
      const instruction=directionRoll===1?`Move the Escape marker ${distance} inches left.`:directionRoll===2?'Do not move the Escape marker.':`Move the Escape marker ${distance} inches right.`;
      state.missionState.auspexCalibrations[state.turningPoint]={directionRoll,distance,instruction};
      log(`Auspex Calibration: ${instruction}`);save();render();
    });
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',async()=>{
      if(state.turningPoint>=MAX_TURNING_POINTS){await resolveTurningPointLimit();return;}
      if(await executeMissionLifecycleHook('onTurningPointEnded')===null)return;
      log(`Turning Point ${state.turningPoint} completed.`);
      completeTurningPointCleanup();
      if(checkGameEnd('end-turning-point'))return;
      state.phase='between';
      save();render();
    });
    $('#newGameFromPlay')?.addEventListener('click',confirmNewGame);
    $('#threatHudToggle')?.addEventListener('click',()=>{threatAdjustOpen=!threatAdjustOpen;render();});
    $('#threatUp')?.addEventListener('click',()=>{setThreat(1,'Manual adjustment');save();render();});
    $('#threatDown')?.addEventListener('click',()=>{setThreat(-1,'Manual adjustment');save();render();});
  }

  function showCeaselessScuttling(){
    if(!ceaselessScuttlingEligible())return;
    showModal('A Ceaseless Scuttling',`<p>Select a supported loadout for the new operative instance, then confirm a valid setup wholly within the NPO drop zone.</p><div class="field"><label for="scuttlingLoadout">Loadout</label><select id="scuttlingLoadout"><option value="gauss-scalpel">Gauss scalpel and claws &amp; tail</option><option value="tesla-caster">Tesla caster and claws &amp; tail</option></select></div><label class="check-row"><input id="scuttlingPlacement" type="checkbox"><span>Valid NPO drop-zone setup location confirmed</span></label><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmScuttling" disabled>Create New Warrior</button></div>`);
    $('#scuttlingPlacement').onchange=()=>{$('#confirmScuttling').disabled=!$('#scuttlingPlacement').checked;};
    $('#confirmScuttling').onclick=()=>{
      const warrior=createCeaselessScuttlingWarrior($('#scuttlingLoadout').value);
      if(!warrior)return;
      state.strategyData.ceaselessScuttlingTurningPoint=state.turningPoint;
      state.activationHistory.unshift({side:'npo',label:npoName(warrior),action:'A Ceaseless Scuttling',loadout:warrior.weaponId,turningPoint:state.turningPoint,instanceId:warrior.id});
      save();closeModal();render();
    };
  }

  async function startTurningPoint(){
    if(state.turningPoint>=MAX_TURNING_POINTS){
      await resolveTurningPointLimit();
      return;
    }
    state.turningPoint++;
    state.finalResolution={...state.finalResolution,pending:false,turningPointEnded:false,cleanupComplete:false};
    state.npoRuleState.reanimatedTargetIds=[];
    state.npoRuleState.incapacitationTriggers=[];
    if(missionEngine()?.type==='regroup')state.missionState={operativeChecks:{},lastCheckedTurningPoint:state.turningPoint};
    state.tpStartThreat=state.threat;
    state.tpStartGrade=threatGrade();
    state.tpStartDestroyedNpos=destroyedNpoCount();
    state.tpStartPlayerCasualties=(state.playerCasualtyIds||[]).length;
    state.gradeMilestone=null;
    state.playerReady=Math.max(0,state.playerCount-(state.playerCasualtyIds||[]).length);
    state.playerActivated=0;state.npoActivated=0;state.activationNumber=0;state.activationHistory=[];state.playerActivatedIds=[];
    state.strategyData={grade:threatGrade(),reinforcements:[],actualReinforcements:0,blocked:0,event:null,playerRoll:null,npoRoll:null,suggestedInitiative:'player',missionReadyHooks:[],viewStep:'actions'};
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
    d.normalEventCount=normalStrategyEventCount({turningPoint:state.turningPoint,grade:d.grade,suggestedInitiative:d.suggestedInitiative,threat:state.threat});
    d.requiredEventCount=strategyEventCount(d);
    d.eventRequirementTurningPoint=state.turningPoint;
    d.eventSlotsDrawn=0;
    for(let i=0;i<d.requiredEventCount;i++){
      const event=drawEvent();
      if(event){event.requiredBy=i>=d.normalEventCount?'restless-tomb':'standard';d.eventSlotsDrawn++;}
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

  function drawReplacementEvent(originalEvent,insertAt){
    const available=state.eventState.available||[],used=state.eventState.used||[];
    let pool=available.filter(instanceId=>instanceId!==originalEvent.instanceId);
    let recycling=false;
    if(!pool.length){
      pool=[...new Set([...available,...used])].filter(instanceId=>instanceId!==originalEvent.instanceId);
      recycling=true;
    }
    const validPool=pool.filter(instanceId=>eventDeck.some(card=>card.instanceId===instanceId));
    if(!validPool.length)return null;
    const instanceId=validPool[roll(validPool.length)-1];
    const card=eventDeck.find(candidate=>candidate.instanceId===instanceId);
    if(!card)return null;
    if(recycling){
      state.eventState.available=[...new Set([...available,...used])].filter(id=>id!==instanceId);
      state.eventState.used=[instanceId];
    }else{
      state.eventState.available=available.filter(id=>id!==instanceId);
      if(!used.includes(instanceId))state.eventState.used=[...used,instanceId];
    }
    const replacement=eventRecord(card);
    state.strategyData.events.splice(insertAt,0,replacement);
    return replacement;
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
    if(type==='transdimensional-relocation'){
      if(!prepareTransdimensionalRelocation(event)){
        redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.');
        return;
      }
      d.eventPending=true;
      save();
      return;
    }
    if(type==='subjugation-glyphs'){
      const transaction=eventTransaction(`event:${event.instanceId}:${state.turningPoint}`,{definitionId:event.definitionId,selections:[],rolls:[]});
      if(!transaction.committed){
        const eligible=(state.playerRoster||[]).filter(id=>!state.playerCasualtyIds.includes(id)&&playerOperativeState(id).inPlay!==false);
        const remaining=[...eligible];
        while(remaining.length){
          const selectedIndex=roll(remaining.length)-1;
          const operativeId=remaining.splice(selectedIndex,1)[0];
          const die=roll(),baseApl=Number(playerDefinition(operativeId)?.apl||3),apl=effectivePlayerApl(operativeId,baseApl);
          transaction.selections.push(operativeId);transaction.rolls.push(die);
          if(die>apl){
            const modifierId=`subjugation-glyphs:${event.instanceId}:${operativeId}`;
            if(!state.eventState.playerAplModifiers.some(item=>item.id===modifierId))state.eventState.playerAplModifiers.push({id:modifierId,sourceId:event.instanceId,targetId:operativeId,ruleId:'subjugation-glyphs',amount:-1,expires:null});
            transaction.affectedOperativeId=operativeId;
            break;
          }
        }
        transaction.committed=true;
      }
      const tested=transaction.selections.map((id,index)=>`${playerName(id)} rolled ${transaction.rolls[index]}`).join('; ');
      completeCurrentEvent(`${tested||'No eligible operatives.'}${transaction.affectedOperativeId?`; ${playerName(transaction.affectedOperativeId)} suffers -1 APL.`:'; no operative was affected.'}`);
      return;
    }
    if(type==='living-metal-flux'){
      const restored=[];
      activeNpos().filter(npo=>npo.wounds<npo.maxWounds).forEach(npo=>{
        const amount=rollD3()+2,before=npo.wounds;
        npo.wounds=Math.min(npo.maxWounds,npo.wounds+amount);
        restored.push({npo,result:`${npoName(npo)} ${before}→${npo.wounds}`});
      });
      const summary=sortedNposForDisplay(restored.map(entry=>entry.npo))
        .map(npo=>restored.find(entry=>entry.npo===npo).result)
        .join('; ');
      completeCurrentEvent(summary||'No wounded NPOs.');
      return;
    }
    if(type==='stirrings'){
      if(state.threat===15){redrawCurrentEvent('Threat was already 15.');return;}
      setThreat(1,event.title);
      completeCurrentEvent(`Threat increased to ${state.threat}.`);
      return;
    }
    if(type==='activate'){
      if(!state.eventState.active.some(active=>active.instanceId===event.instanceId&&active.startedTurningPoint===state.turningPoint)){
        const definition=eventDefinitions[event.definitionId];
        state.eventState.active.push({...event,lifecycle:definition.lifecycle,handlerId:definition.handlerId,gameplayHooks:[...definition.gameplayHooks],automationType:definition.automationType,priority:definition.priority,startedTurningPoint:state.turningPoint,expiresAfterTurningPoint:state.turningPoint,status:'active'});
      }
      completeCurrentEvent(eventDefinitions[event.definitionId]?.resultText||'Effect active until the end of this Turning Point.');
      return;
    }
    if(type==='chittering-drone'){
      const wounded=activeNpos().filter(npo=>npo.type==='Canoptek Scarab Swarm'&&npo.wounds<npo.maxWounds);
      if(wounded.length===1){wounded[0].wounds=wounded[0].maxWounds;completeCurrentEvent(`${npoName(wounded[0])} regained all lost wounds.`);return;}
      if(wounded.length>1){event.eligibleNpoIds=wounded.map(npo=>npo.id);d.eventPending=true;return;}
      if(activeNpos().length>=MAX_NPOS||!npoInventory()['Canoptek Scarab Swarm'].remaining){redrawCurrentEvent('No Scarab Swarm could be set up.');return;}
    }
    if(type==='maze-reforms'){
      event.openHatchwayLimit=rollD3();
      event.text=`Close one breach and up to ${event.openHatchwayLimit} open hatchway${event.openHatchwayLimit===1?'':'s'}. If this cannot be resolved, draw another event card.`;
    }
    if(type==='awakened-warrior'&&(activeNpos().length>=MAX_NPOS||!npoInventory()['Necron Warrior'].remaining)){redrawCurrentEvent('No Necron Warrior could be set up.');return;}
    d.eventPending=true;
  }

  function completeCurrentEvent(result){
    const d=state.strategyData,event=currentEvent();
    if(!event)return;
    event.status='resolved';event.result=result;
    d.eventAction={eventId:event.instanceId,result};
    d.eventIndex=(d.eventIndex||0)+1;
    d.eventPending=false;
    const source=event.requiredBy==='restless-tomb'?'Restless Tomb minimum':'standard rules';
    log(`Turning Point ${state.turningPoint} · ${event.title} (${source}): ${result}`);
    beginCurrentEvent();
  }

  function redrawCurrentEvent(reason){
    const data=state.strategyData,event=currentEvent();
    if(!data||!event||event.status!=='drawn')return false;
    const eventIndex=data.eventIndex||0;
    const transactionId=`event-redraw:${state.turningPoint}:${event.instanceId}:${eventIndex}`;
    if(eventRedrawsInProgress.has(transactionId))return false;
    const existing=state.eventState.transactions?.[transactionId];
    if(existing&&typeof existing==='object'&&existing.committed&&existing.originalEventInstanceId===event.instanceId){
      const replacementIndex=data.events.findIndex(item=>item.instanceId===existing.replacementInstanceId);
      if(replacementIndex>=0){
        data.eventIndex=replacementIndex;
        data.event=data.events[replacementIndex];
        data.eventPending=data.event.status==='drawn';
        return false;
      }
    }
    eventRedrawsInProgress.add(transactionId);
    const replacement=drawReplacementEvent(event,eventIndex+1);
    if(!replacement){
      data.event=event;
      data.eventPending=true;
      state.eventState.transactions[transactionId]={
        transactionId,type:'event-redraw',turningPoint:state.turningPoint,
        originalEventInstanceId:event.instanceId,originalDefinitionId:event.definitionId,
        replacementInstanceId:null,reason,status:'failed',committed:false
      };
      log(`${event.title}: another event card could not be drawn; the redraw remains available.`);
      save();
      eventRedrawsInProgress.delete(transactionId);
      showModal('Another event card could not be drawn.',`<p>The event deck has no valid replacement card available. Try again or use the Game Menu to review the battle state.</p><div class="wizard-actions"><button type="button" class="btn primary" data-close>Return to Event</button></div>`);
      return false;
    }
    event.status='redrawn';event.result=reason;
    replacement.requiredBy=event.requiredBy;
    data.eventIndex=eventIndex+1;
    data.event=replacement;
    data.eventPending=true;
    state.eventState.transactions[transactionId]={
      transactionId,type:'event-redraw',turningPoint:state.turningPoint,
      originalEventInstanceId:event.instanceId,originalDefinitionId:event.definitionId,
      replacementInstanceId:replacement.instanceId,reason,status:'committed',committed:true
    };
    log(`${event.title}: ${reason} Another event card was drawn.`);
    beginCurrentEvent();
    save();
    eventRedrawsInProgress.delete(transactionId);
    render();
    return true;
  }

  function processReinforcementStage(){
    if(state.strategyPipeline.completed.includes('reinforcement'))return;
    const d=state.strategyData,reinforcements=[];
    let blocked=0;
    state.reinforcementState={turningPoint:state.turningPoint,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0,blockedByCapacity:0,blockedByInventory:0};
    d.grade=threatGrade();
    if(reinforcementTriggered(d)){
      const requested=gradeConfig(d.grade).reinforcements,slots=Math.max(0,MAX_NPOS-activeNpos().length),actual=Math.min(requested,slots);
      blocked=requested-actual;
      state.reinforcementState.blockedByCapacity=blocked;
      for(let i=0;i<actual;i++){
        const rr=randomReinforcement();
        if(!rr){blocked++;state.reinforcementState.blockedByInventory++;continue;}
        const type=rr.type;
        let n=reserveNpos().find(candidate=>candidate.type===type&&!state.reinforcementState.operativeIds.includes(candidate.id)&&!state.reinforcementState.blockedOperativeIds.includes(candidate.id));
        if(n){
          n.reinforcement={turningPoint:state.turningPoint,placementConfirmed:false};
          n.battlefieldState='reserve';n.deployed=false;n.dormant=false;n.ready=false;
        }else{
          n=createNpo(type,`${type} R${state.turningPoint}-${i+1}`,{weaponId:rr.weaponId,deployed:false,reinforcement:{turningPoint:state.turningPoint,placementConfirmed:false}});
          if(!commitNpoRoster([...state.roster,n],'add a reinforcement')){blocked++;state.reinforcementState.blockedByInventory++;continue;}
          state.newIds.push(n.id);
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
    npo.reinforcement.placementConfirmed=Boolean(confirmed);
    npo.deployed=npo.reinforcement.placementConfirmed;
    npo.battlefieldState=npo.deployed?'deployed':'reserve';
    npo.dormant=npo.deployed&&state.threat===0;
    npo.ready=npo.deployed&&!npo.dormant;
    const complete=state.reinforcementState.operativeIds.every(operativeId=>state.roster.find(item=>item.id===operativeId)?.reinforcement?.placementConfirmed);
    state.reinforcementState.status=complete?'complete':'placement';
    save();render();
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

  function resolveStrategyEvent(button=null){
    const event=currentEvent();
    if(state.phase!=='strategy'||state.strategyStage!=='summary'||!event||!state.strategyData.eventPending)return;
    let result='Tabletop effect confirmed.';
    if(event.execution.type==='transdimensional-relocation'){
      if(event.status!=='drawn'||event.resolution?.confirmed){if(button)button.disabled=false;return;}
      if(!validTransdimensionalRelocationSelection(event)){
        if(!prepareTransdimensionalRelocation(event))redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.');
        else render();
        return;
      }
      const names=event.resolution.playerOperativeIds.map(playerName);
      event.resolution.confirmed=true;
      result=`${names[0]} and ${names[1]} swapped positions.`;
    }else if(event.execution.type==='chittering-drone'&&event.eligibleNpoIds?.length){
      const operativeId=$('#eventNpoSelect')?.value;
      const n=activeNpos().find(item=>item.id===operativeId&&event.eligibleNpoIds.includes(item.id)&&item.wounds<item.maxWounds);
      if(!n)return;
      n.wounds=n.maxWounds;
      result=`${npoName(n)} regained all lost wounds.`;
    }else if(event.execution.type==='chittering-drone'||event.execution.type==='awakened-warrior'){
      const type=event.execution.type==='chittering-drone'?'Canoptek Scarab Swarm':'Necron Warrior';
      if(activeNpos().length>=MAX_NPOS||!npoInventory()[type]?.remaining){redrawCurrentEvent(`${type} could not be set up.`);return;}
      const n=createNpo(type,`${type} E${state.turningPoint}`,{order:'Conceal'});
      n.ready=true;n.dormant=false;
      if(!commitNpoRoster([...state.roster,n],'resolve that event')){redrawCurrentEvent(`${type} could not be set up.`);return;}
      state.newIds.push(n.id);
      result=`${npoName(n)} was set up Ready with a Conceal order using the event card’s placement instructions.`;
    }
    if(event.execution.type==='maze-reforms')result='Breach and hatchway changes completed on the tabletop.';
    completeCurrentEvent(result);
    save();render();
    if(event.definitionId==='transdimensional-relocation')requestAnimationFrame(()=>focusInitialDialogControl(app));
  }

  function randomReinforcement(){
    const canAllocate=result=>reserveNpos().some(npo=>npo.type===result.type)||npoInventory()[result.type]?.remaining>0;
    for(let attempts=0;attempts<24;attempts++){const result=rollNpo();if(canAllocate(result))return result;}
    const legal=npoGenerationTable.filter(canAllocate);
    if(!legal.length){console.warn('[NPO inventory] No legal physical model remains for reinforcement.');return null;}
    const result=legal[roll(legal.length)-1];return {...result,weaponId:generatedWeaponId(result)};
  }
  function nextNpo(){return readyNpos().find(n=>n.id===state.activeNpoId)||null;}
  function beginNpoActivation(n){
    const definition=npoDefinition(n.type),apl=effectiveApl(n.id,definition.apl);
    state.activeNpoId=n.id;
    state.lastActivation={
      activationId:missionActivationId('npo',n.id),npoId:n.id,name:npoName(n),baseApl:definition.apl,effectiveApl:apl,
      startingAp:apl,remainingAp:apl,actionSequence:0,completedActionIds:[],resolvedActions:[],decisionPass:1,
      declinedActionIds:[],declinedMovementIntentIds:[],movementIntent:null,pendingFollowUpAction:null,questionHistory:[],pendingAction:null,currentContext:{inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null},attackPerformed:false,fightPerformed:false,
      committed:false,completed:false
    };
    notifyMissionActivationStarted('npo',n.id);
    save();
    continueNpoActivation();
  }

  function showNpoSelection(){
    if(state.activeNpoId&&state.lastActivation?.npoId===state.activeNpoId&&!state.lastActivation.committed){continueNpoActivation();return;}
    const candidates=readyNpos();
    if(candidates.length===1){state.activeNpoId=candidates[0].id;beginNpoActivation(candidates[0]);return;}
    const options=sortedNposForDisplay(candidates).map(n=>`<option value="${escapeHtml(n.id)}">${escapeHtml(npoName(n))}</option>`).join('');
    showModal('Select NPO to Activate',`<p>Use the Threat Principle in order. Select an NPO that:</p><ol><li>has an ability, or is a threat, to Shoot or Fight a Player operative;</li><li>is not in cover;</li><li>is closest to a Player operative.</li></ol><p class="muted">If more than one NPO is still tied, determine one at random on the tabletop.</p><div class="field"><label for="officialNpoSelection">Next ready NPO</label><select id="officialNpoSelection" data-dialog-focus><option value="">Select matching NPO</option>${options}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmNpoSelection" disabled>Continue</button></div>`);
    $('#officialNpoSelection').onchange=()=>{$('#confirmNpoSelection').disabled=!$('#officialNpoSelection').value;};
    $('#confirmNpoSelection').onclick=()=>{const n=candidates.find(item=>item.id===$('#officialNpoSelection').value);if(n)beginNpoActivation(n);};
  }

  function remainingPlayerOperatives(){
    const used=new Set(state.playerActivatedIds||[]);
    const casualties=new Set(state.playerCasualtyIds||[]);
    return inPlayPlayerOperativeIds().filter(id=>!used.has(id)&&!casualties.has(id));
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
    return Object.entries(PLAYER_ACTION_COSTS).reduce((total,[key,cost])=>total+(stage[key]?cost:0),0)
      + (stage.missionBreachCommitted?Math.max(1,Number(stage.missionBreachCost)||2):0);
  }

  function qualifyingBreachDiscount(operative){
    if(!operative)return false;
    const operativeRules=[...(operative.abilities||[]),...(operative.rules||[])].map(String);
    if(operativeRules.some(rule=>/breach/i.test(rule)&&/(?:1\s*AP|reduce|costs?\s*1)/i.test(rule)))return true;
    return (operative.weapons||[]).some(weapon=>{
      const rules=(weapon.rules||[]).map(String);
      return rules.some(rule=>/^Piercing(?:\s|$)/i.test(rule))&&!rules.some(rule=>/^(?:Blast|Torrent)(?:\s|$)/i.test(rule));
    });
  }

  function breachSarcophagusApCost(operativeId){
    return Math.max(1,qualifyingBreachDiscount(playerDefinition(operativeId))?1:2);
  }

  function canOfferBreachSarcophagus(stage,operativeId){
    if(state.missionId!=='destroy-sarcophagus'||state.gameEnd||state.nextSide!=='player'||state.phase!=='firefight')return false;
    if(!operativeId||!isPlayerOperativeInPlay(operativeId)||state.playerCasualtyIds.includes(operativeId))return false;
    if(stage.missionBreachCommitted)return false;
    return Number(objectiveEngine?.getMissionHudModel().value||state.missionState?.destruction||0)<20;
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
    stage=normalizeImpossiblePlayerCombat(stage);
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
      const baseApl=Number(selectedOperative?.apl||current.baseApl||current.apl||3);
      return {...current,playerOperativeId:id||'',baseApl,apl:id?effectiveApl(id,baseApl):baseApl};
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
    const shootPending=pendingAttackResults(stage,'shoot')[0]||null;
    const meleePending=pendingAttackResults(stage,'melee')[0]||null;
    const breachAvailable=canOfferBreachSarcophagus(stage,selectedId);
    const breachCost=selectedId?breachSarcophagusApCost(selectedId):2;
    const breachRemainingAp=Number(stage.apl||selectedOperative?.apl||3)-playerActionCost(stage);
    const combatTargetsAvailable=hasValidPlayerCombatTargets(stage);

    if(selectedId&&state.missionActionContext?.actionId==='breachSarcophagus'&&state.missionActionContext.operativeId===selectedId){
      renderBreachSarcophagusStep(stage);
      return;
    }

    showModal('Activate an Operative',`
      <p>Choose the Player operative being activated. That operative cannot activate again during this Turning Point after the activation is confirmed.</p>
      <div class="field" data-touch-dialog-focus-container>
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
            ${combatTargetsAvailable?`<div class="combat-action-card">
              <label><input type="checkbox" id="eaShoot" ${checked('shoot')}><span><strong>Shoot</strong><small>1 AP · One Shooting action for this operative</small></span></label>
              ${shootPending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(shootPending.targetName)} · ${shootPending.damage} damage</div>`:''}
            </div>
            <div class="combat-action-card">
              <label><input type="checkbox" id="eaMelee" ${checked('melee')||checked('fight')}><span><strong>Melee</strong><small>1 AP · One Melee action for this operative</small></span></label>
              ${meleePending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(meleePending.targetName)} · ${meleePending.damage} damage</div>`:''}
            </div>`:''}
            <div class="toggle-list player-action-list compact-actions">
              <label><input type="checkbox" id="eaDamage" ${checked('damage')}><span>Other damage (ability, terrain, mission, etc.) <small>1 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group">
            <div class="activation-group-title"><span>▣</span><div><strong>Battlefield</strong><small>Terrain and mission interactions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaHatch" ${checked('hatch')} ${state.missionId==='demolition-protocol'&&!stage.hatch&&!closedMissionFeatures('hatchway').length?'disabled':''}><span>Operate Hatch <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaBreach" ${checked('breach')} ${state.missionId==='demolition-protocol'&&!stage.breach&&!closedMissionFeatures('breach-point').length?'disabled':''}><span>Breach <small>1 AP</small></span></label>
              ${state.missionId==='destroy-sarcophagus'?'':`<label><input type="checkbox" id="eaObjective" ${checked('objective')}><span>Mission-specific action <small>1 AP</small></span></label>`}
              ${breachAvailable?`<button type="button" class="btn secondary" id="breachSarcophagus" ${breachRemainingAp<breachCost?'disabled':''}>Breach Sarcophagus (${breachCost} AP)</button>${breachRemainingAp<breachCost?'<small class="warning-text">Not enough AP to Breach the sarcophagus.</small>':''}`:''}
            </div>
          </section>

          <section class="activation-group pass-group">
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaPass" ${checked('pass')}>Pass / no action recorded</label>
            </div>
          </section>
        </div>
        <div class="wizard-actions"><button class="btn ghost" id="cancelPlayerActivation">Cancel</button><button class="btn primary" id="confirmPlayer">Complete Activation</button></div>
      </fieldset>`,undefined,'player-activation');
    renderOperativeStatusPanel(selectedId);

    const operativeSelect=$('#playerOperativeSelect');
    const controls=$('#playerActivationControls');
    operativeSelect?.addEventListener('change',event=>{
      const select=event.currentTarget;
      const operativeId=select.value;
      if(!operativeId)return;
      const selectedStage=selectOperative(stage,operativeId);
      modal._skipFocusRestoreId=select.id;
      closeTouchSelectAfterCommit(select,()=>showPlayerActivation(selectedStage));
    });

    const actionIds=['eaMove','eaDash','eaCharge','eaFallBack','eaShoot','eaMelee','eaDamage','eaHatch','eaBreach','eaObjective'];
    const clearPass=()=>{if($('#eaPass'))$('#eaPass').checked=false;};

    function updatePlayerActionAvailability(){
      const current=readPlayerActivationStage(stage);
      const baseApl=Number(playerDefinition(current.playerOperativeId)?.apl||current.baseApl||current.apl||3);
      const apl=effectiveApl(current.playerOperativeId,baseApl);
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
        const hasMissionTarget=state.missionId!=='demolition-protocol'||key!=='hatch'&&key!=='breach'||closedMissionFeatures(key==='hatch'?'hatchway':'breach-point').length>0;
        box.disabled=!hasMissionTarget||playerActionCost(hypothetical)>apl||playerActionConflicts(hypothetical).length>0;
      });
      const missionBreach=$('#breachSarcophagus');
      if(missionBreach){
        const cost=breachSarcophagusApCost(current.playerOperativeId);
        missionBreach.disabled=apl-used<cost||(cost===1&&(current.shoot||current.charge));
      }
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

    $('#breachSarcophagus')?.addEventListener('click',()=>beginBreachSarcophagus(readPlayerActivationStage(stage)));

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
      if(state.missionId==='demolition-protocol'&&finalStage.hatch&&!finalStage.hatchTargetId){
        showActivationFeatureTargetSelection(finalStage,'operate-hatch');
        return;
      }
      if(state.missionId==='demolition-protocol'&&finalStage.breach&&!finalStage.breachTargetId){
        showActivationFeatureTargetSelection(finalStage,'breach');
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
      baseApl:Number(playerDefinition(previous.playerOperativeId)?.apl||previous.baseApl||previous.apl||3),
      apl:effectiveApl(previous.playerOperativeId,Number(playerDefinition(previous.playerOperativeId)?.apl||previous.baseApl||previous.apl||3)),
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
      pendingShootResults:shoot?pendingAttackResults(previous,'shoot'):[],
      pendingMeleeResults:melee?pendingAttackResults(previous,'melee'):[],
      shootCombatDraft:shoot?previous.shootCombatDraft||null:null,
      meleeCombatDraft:melee?previous.meleeCombatDraft||null:null
      ,missionBreachCommitted:Boolean(previous.missionBreachCommitted)
      ,missionBreachCost:previous.missionBreachCost
      ,missionBreachRecord:previous.missionBreachRecord||null
      ,breachTargetId:previous.breachTargetId||null
      ,hatchTargetId:previous.hatchTargetId||null
      ,breachFeatureType:previous.breachFeatureType||previous.missionFeatureType||null
      ,hatchFeatureType:previous.hatchFeatureType||null
      ,breachTransactionId:previous.breachTransactionId||previous.missionFeatureTransactionId||null
      ,hatchTransactionId:previous.hatchTransactionId||null
      ,missionFeatureCommitted:Boolean(previous.missionFeatureCommitted)
      ,missionFeatureCommittedActions:isRecord(previous.missionFeatureCommittedActions)?{...previous.missionFeatureCommittedActions}:{}
    };
  }

  function playerActivationHasAction(stage){
    return Boolean(stage.move || stage.dash || stage.charge || stage.fallBack || stage.shoot || stage.melee ||
      stage.damage || stage.hatch || stage.breach || stage.objective || stage.missionBreachCommitted || stage.pass);
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
    if(stage.missionBreachCommitted)actions.push('Breach Sarcophagus');
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
    const hot=attack.hot;
    const hotSummary=hot?`<div class="summary-box hot-attack-summary"><strong>Hot roll: ${hot.roll}</strong><p>${hot.damage?`Attacker suffered ${hot.damage} damage (${hot.woundsBefore} → ${hot.woundsAfter} wounds).`:'Attacker suffered no damage.'}</p></div>`:'';
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
      ${hotSummary}
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
      ${combat.recordedOutcome?'<div class="combat-stage"><small>TABLETOP RESOLUTION</small><p>Physical dice and retained successes resolved by the player.</p></div>':`<div class="combat-stage"><small>ATTACK DICE</small><div class="dice-row ${animate?'animated-roll':'settled'}" data-combat-attack-dice>${combat.attackDice.map(d=>animate?rollingDieHtml():dieHtml(d)).join('')}</div>${severeAppliedHtml(combat.attackDice,combat.severeApplied)}</div><div class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row ${animate?'animated-roll':'settled'}" data-combat-save-dice>${combat.saveDice.length?combat.saveDice.map(d=>animate?rollingDieHtml():dieHtml(d)).join(''):'<span class="muted">No defense dice rolled</span>'}</div>${combat.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div>`}
      ${elimination}
      ${combatAbilityReminder(combat)}
      ${(combat.eventMessages||combat.profile?.eventMessages||[]).map(message=>`<div class="summary-box"><strong>${escapeHtml(message)}</strong></div>`).join('')}
      ${combat.dimensionalBanishmentTriggered?`<div class="summary-box"><strong>Normal attack damage:</strong> ${combat.before} → ${combat.dimensionalBanishmentRemainingWounds}<br><strong>Dimensional Banishment:</strong> ${combat.dimensionalBanishmentIncapacitated?'incapacitated':'survived'}</div>`:''}
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
        <div class="damage-summary combat-participants compact-combat-profile combat-summary-grid${attackLabel?' has-attack-profile':''}">
          <div><small>Attacker</small><strong class="combat-summary-value">${escapeHtml(attackerName)}</strong></div>
          <div><small>Defender</small><strong class="combat-summary-value">${escapeHtml(defenderName)}</strong></div>
          <div><small>Attack type</small><strong class="combat-summary-value">${attackType==='shoot'?'Shooting':'Melee'}</strong></div>
          <div><small>Weapon</small><strong class="combat-summary-value">${escapeHtml(weaponName)}</strong></div>
          ${attackLabel?`<div><small>Attack</small><strong class="combat-summary-value">${escapeHtml(attackLabel)}</strong></div>`:''}
          <div><small>Defense</small><strong class="combat-summary-value">${escapeHtml(defenseLabel)}</strong></div>
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

  function showCombatResumeRecovery(onReturn){
    console.error('[Combat] Guided weapon-rule combat screen could not be restored.');
    showModal('Combat could not resume',`<p>No dice or damage were committed. Return to the combat screen and try again.</p><div class="wizard-actions"><button class="btn primary" id="returnToCombat">Return to Combat</button></div>`);
    $('#returnToCombat').onclick=onReturn;
  }

  function resumeCombatAfterWeaponRuleCheck({render,onMounted,onRecovery}){
    if(weaponRuleResumePending)return;
    weaponRuleResumePending=true;
    save();
    requestAnimationFrame(()=>{
      let mounted=null;
      try{
        mounted=render();
      }catch(error){
        console.error('[Combat] Guided weapon-rule combat screen render failed.',error);
      }finally{
        weaponRuleResumePending=false;
      }
      const combatResults=$('#combatResults');
      const completeButton=mounted?.continueButton;
      if(!combatResults||!completeButton||!mounted?.dice?.isConnected){
        showCombatResumeRecovery(onRecovery||render);
        return;
      }
      onMounted(mounted);
    });
  }

  function displaySharedCombatResult(combat,{pending=false,animate=false,waiting=false,message='',onContinue,extraHtml=''}={}){
    const results=$('#combatResults');
    const dice=$('#automaticCombat');
    const button=$('.combat-resolution-footer .btn.primary');
    if(!results||!button||!dice?.isConnected){
      showCombatResumeRecovery(closeModal);
      return;
    }
    dice.replaceChildren();
    results.innerHTML=`${renderCombatResolution(combat,{pending,animate,showParticipants:false})}${extraHtml}${message?`<p class="muted">${escapeHtml(message)}</p>`:''}`;
    let visualComplete=!animate&&!waiting;
    const completeWaiting=()=>{
      visualComplete=true;
      if(button.isConnected)button.disabled=false;
    };
    button.textContent='Continue';
    button.disabled=!visualComplete;
    button.onclick=()=>{if(visualComplete&&onContinue)onContinue();};
    if(animate)settleCombatDice(combat,()=>{
      visualComplete=!waiting;
      if(button.isConnected)button.disabled=waiting;
    },results);
    return {completeWaiting};
  }

  function settleDimensionalBanishment(combat,onSettled=()=>{}){
    const row=$('[data-dimensional-banishment-dice]');
    const values=combat.dimensionalBanishmentDice||[];
    if(!row||values.length!==2){onSettled();return ()=>{};}
    return settleAnimatedDice([{row,dice:values.map((value,index)=>({value,ariaLabel:`Dimensional Banishment die ${index+1}: ${value}`}))}],()=>{
      const rolling=$('[data-dimensional-banishment-rolling]');
      const result=$('[data-dimensional-banishment-result]');
      if(rolling)rolling.remove();
      if(result)result.hidden=false;
      onSettled();
    });
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
    for(const pending of [...pendingAttackResults(stage,'shoot'),...pendingAttackResults(stage,'melee')]){
      if(pending?.targetId===npoId)wounds=pending.after;
    }
    return wounds;
  }

  function pendingAttackResults(stage,attackType){
    const list=stage?.[attackType==='shoot'?'pendingShootResults':'pendingMeleeResults'];
    if(Array.isArray(list)&&list.length)return list;
    const legacy=stage?.[attackType==='shoot'?'pendingShoot':'pendingMelee'];
    return legacy?[legacy]:[];
  }

  function normalizePendingAttackResultLists(stage={}){
    const normalized={...stage};
    for(const attackType of ['shoot','melee']){
      const listKey=attackType==='shoot'?'pendingShootResults':'pendingMeleeResults';
      const legacyKey=attackType==='shoot'?'pendingShoot':'pendingMelee';
      normalized[listKey]=Array.isArray(stage[listKey])?stage[listKey].filter(isRecord):stage[legacyKey]?[stage[legacyKey]]:[];
    }
    return normalized;
  }

  function normalizeImpossiblePlayerCombat(stage={}){
    const normalized=normalizePendingAttackResultLists(stage);
    if(hasValidPlayerCombatTargets(normalized))return normalized;
    let cleared=false;
    for(const attackType of ['shoot','melee']){
      const selected=normalized[attackType]||(attackType==='melee'&&normalized.fight);
      if(!selected||pendingAttackResults(normalized,attackType).length)continue;
      normalized[attackType]=false;
      if(attackType==='melee')normalized.fight=false;
      normalized[attackType==='shoot'?'pendingShoot':'pendingMelee']=null;
      normalized[attackType==='shoot'?'pendingShootResults':'pendingMeleeResults']=[];
      normalized[`${attackType}CombatDraft`]=null;
      cleared=true;
    }
    if(cleared){
      state.weaponRuleResolution=null;
      if(state.combatState?.side==='player')state.combatState={side:'player',stage:{...normalized}};
      save();
    }
    return normalized;
  }

  function resolvePendingPlayerAttacks(stage){
    stage=normalizeImpossiblePlayerCombat(stage);
    if(stage.shoot&&!pendingAttackResults(stage,'shoot').length){
      showPendingPlayerAttackWizard(
        stage,
        'shoot',
        result=>continuePlayerMultiTargetAttack(stage,'shoot',result),
        ()=>showPlayerActivation(stage)
      );
      return;
    }
    if(stage.melee&&!pendingAttackResults(stage,'melee').length){
      const remainingTargets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
      if(!remainingTargets.length){
        resolvePendingPlayerAttacks({...stage,melee:false});
        return;
      }
      showPendingPlayerAttackWizard(
        stage,
        'melee',
        result=>continuePlayerMultiTargetAttack(stage,'melee',result),
        ()=>showPlayerActivation(stage)
      );
      return;
    }
    state.combatState={side:'player',stage:{...stage}};
    save();
    if(applyPendingPlayerDamage(stage))return;
    finishPlayerAttackResolution(stage);
  }

  function finishPlayerAttackResolution(stage){
    const shootResults=pendingAttackResults(stage,'shoot').filter(result=>result?.committed&&!result.skipped);
    const result=shootResults[0];
    const finish=()=>{state.combatState=null;completePlayerActivation(stage);};
    if(!result){finish();return;}
    completeShootingWeaponUse({
      attackerSide:'player',attackerId:stage.playerOperativeId,
      activationId:missionActivationId('player',stage.playerOperativeId),actionId:'shoot',
      profile:result.profile,weaponName:result.weaponName
    },finish);
  }

  function showActivationFeatureTargetSelection(stage,action){
    const isHatch=action==='operate-hatch',featureType=isHatch?'hatchway':'breach-point';
    const targetKey=isHatch?'hatchTargetId':'breachTargetId';
    const typeKey=isHatch?'hatchFeatureType':'breachFeatureType';
    const transactionKey=isHatch?'hatchTransactionId':'breachTransactionId';
    const actionLabel=isHatch?'Operate Hatch':'Breach';
    const available=closedMissionFeatures(featureType);
    const pendingId=available.some(feature=>feature.id===stage[targetKey])?stage[targetKey]:null;
    state.combatState={side:'player',stage:{...stage,[targetKey]:pendingId,[typeKey]:featureType}};
    save();
    if(!available.length){
      showModal(`${actionLabel} target unavailable`,`<p>No closed ${isHatch?'hatchways':'breach points'} remain. No action was spent and no mission progress was changed.</p><div class="wizard-actions"><button class="btn ghost" id="returnFromBreachTarget">Return to Activation</button></div>`);
      $('#returnFromBreachTarget').onclick=()=>showPlayerActivation(stage);
      return;
    }
    showModal(`Select ${actionLabel} Target`,`<p>Choose the ${isHatch?'hatchway':'breach point'} this operative successfully opened. Mission progress changes only when the entire activation is completed.</p><div class="field"><label for="activationBreachTarget">Target feature</label><select id="activationBreachTarget"><option value="">Select target…</option>${available.map(feature=>`<option value="${escapeHtml(feature.id)}" ${feature.id===pendingId?'selected':''}>${escapeHtml(feature.label)}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" id="cancelActivationBreach">Back</button><button class="btn primary" id="confirmActivationBreach" ${pendingId?'':'disabled'}>Confirm Target</button></div>`,undefined,'activation-breach-target');
    const select=$('#activationBreachTarget'),confirm=$('#confirmActivationBreach');
    select.onchange=()=>{confirm.disabled=!available.some(feature=>feature.id===select.value);};
    $('#cancelActivationBreach').onclick=()=>showPlayerActivation(stage);
    confirm.onclick=()=>{
      if(confirm.disabled)return;
      const feature=available.find(item=>item.id===select.value);
      if(!feature)return showActivationFeatureTargetSelection(stage,action);
      confirm.disabled=true;
      const transactionId=stage[transactionKey]||`${missionActivationId('player',stage.playerOperativeId)}:${action}`;
      const nextStage={...stage,[targetKey]:feature.id,[typeKey]:featureType,[transactionKey]:transactionId};
      state.combatState={side:'player',stage:nextStage};
      save();
      if(isHatch&&nextStage.breach&&!nextStage.breachTargetId){
        showActivationFeatureTargetSelection(nextStage,'breach');
        return;
      }
      resolvePendingPlayerAttacks(nextStage);
    };
  }

  function showActivationBreachTargetSelection(stage){showActivationFeatureTargetSelection(stage,'breach');}

  function continuePlayerMultiTargetAttack(stage,attackType,result){
    const listKey=attackType==='shoot'?'pendingShootResults':'pendingMeleeResults';
    const legacyKey=attackType==='shoot'?'pendingShoot':'pendingMelee';
    const results=[...pendingAttackResults(stage,attackType).filter(item=>item.targetId!==result.targetId),result];
    const nextStage={...stage,[listKey]:results,[legacyKey]:results[0]||null,[`${attackType}CombatDraft`]:null};
    const sequence=state.weaponRuleResolution;
    if(sequence?.currentTargetId===result.targetId){
      state.weaponRuleResolution=advanceMultiTargetAttackSequence(sequence,result.targetId,result);
      state.combatState={side:'player',stage:{...nextStage}};
      save();
      if(state.weaponRuleResolution.currentTargetId){
        showPlayerCombatResolution(nextStage,attackType,state.weaponRuleResolution.currentTargetId,result.weaponIndex,
          nextResult=>continuePlayerMultiTargetAttack(nextStage,attackType,nextResult),
          ()=>showPlayerActivation(nextStage),{deferRoll:false});
        return;
      }
      const completed=state.weaponRuleResolution;
      showMultiTargetAttackSummary(completed,'player',()=>{
        state.weaponRuleResolution=null;
        save();
        resolvePendingPlayerAttacks(nextStage);
      });
      return;
    }
    resolvePendingPlayerAttacks(nextStage);
  }

  function applyPendingPlayerDamage(stage){
    for(const pending of [...pendingAttackResults(stage,'shoot'),...pendingAttackResults(stage,'melee')]){
      if(!pending||pending.committed)continue;
      if(pending.side==='player'||pending.defenderSide==='player'){
        const before=playerCurrentWounds(pending.targetId);
        state.playerWounds[pending.targetId]=Math.max(0,pending.after);
        if(pending.after<=0&&!state.playerCasualtyIds.includes(pending.targetId))state.playerCasualtyIds.push(pending.targetId);
        pending.committed=true;
        log(`${playerName(stage.playerOperativeId)} dealt ${pending.damage} Blast damage to ${playerName(pending.targetId)} (${before} → ${pending.after} wounds).`);
        continue;
      }
      const n=state.roster.find(x=>x.id===pending.targetId);
      if(!n)continue;
      const incapacitationId=`${state.turningPoint}:${state.activationNumber}:${pending.attackType}:${n.id}`;
      if(pending.after<=0&&!state.npoRuleState.incapacitationTriggers.includes(incapacitationId)){
        const eventAttemptKey=`${state.turningPoint}:${n.id}`;
        const candidates=resolveNpoIncapacitation({npoId:n.id,eventAttempts:state.eventState.reanimationAttempts,candidates:[]}).candidates;
        const eventEligible=candidates.some(candidate=>candidate.sourceId==='tomb-world-event:reanimation-protocols');
        const reanimator=activeNpos().find(item=>item.type==='Canoptek Macrocyte Reanimator'&&item.id!==n.id);
        const reanimateAvailable=Boolean(reanimator&&state.npoRuleState.oncePerTurningPoint.reanimate!==state.turningPoint);
        const pipelineTransaction=eventTransaction(`incapacitation:${incapacitationId}:pipeline`,{npoId:n.id});
        if(eventEligible&&reanimateAvailable&&!pipelineTransaction.firstSourceId){
          showIncapacitationOrderChoice(stage,pending,n,reanimator,incapacitationId,pipelineTransaction);
          return true;
        }
        if(reanimateAvailable&&pipelineTransaction.firstSourceId==='macrocyte-reanimate'){
          offerReanimateForPendingDamage(stage,pending,n,reanimator,incapacitationId,()=>{
            pipelineTransaction.firstSourceId='tomb-world-event:reanimation-protocols';
            save();
            if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);
          });
          return true;
        }
        if(eventEligible){
          const transaction=eventTransaction(`incapacitation:${incapacitationId}:reanimation-protocols`,{definitionId:'reanimation-protocols',npoId:n.id});
          if(!Number.isInteger(transaction.roll))transaction.roll=roll();
          state.eventState.reanimationAttempts[eventAttemptKey]={roll:transaction.roll,transactionId:transaction.id,consumed:true};
          transaction.committed=true;
          state.npoRuleState.incapacitationTriggers.push(incapacitationId);
          if(transaction.roll>=4){
            pending.after=1;pending.damage=Math.max(0,pending.before-1);pending.discardRemainingAttackDice=true;pending.eventReanimation={sourceId:'tomb-world-event:reanimation-protocols',roll:transaction.roll};
            n.ready=false;
            applyTemporaryAplModifier({sourceId:pending.transactionId||incapacitationId,targetId:n.id,ruleId:'tomb-world-event-reanimation-protocols',amount:-1});
            n.preventIncapacitationActionId=state.activationNumber;
            log(`Reanimation Protocols event: ${npoName(n)} rolled ${transaction.roll} and reanimated with 1 wound; remaining attack dice from this action were discarded.`);
          }else log(`Reanimation Protocols event: ${npoName(n)} rolled ${transaction.roll}; its once-per-Turning-Point attempt was consumed.`);
          save();
        }
        if(pending.after<=0&&reanimator&&state.npoRuleState.oncePerTurningPoint.reanimate!==state.turningPoint){
          offerReanimateForPendingDamage(stage,pending,n,reanimator,incapacitationId);
          return true;
        }
      }
      const before=n.wounds;
      const protectedForAction=n.preventIncapacitationActionId===state.activationNumber;
      if(pending.after<=0&&!protectedForAction&&n.type==='Canoptek Macrocyte Warrior'&&pending.attackerWithinTwo&&!pending.aggressiveDefenseResolved){
        showAggressiveDefenseResolution(stage,pending,n,incapacitationId);
        return true;
      }
      n.wounds=Math.max(0,pending.after);
      if(protectedForAction)n.wounds=Math.max(1,n.wounds);
      pending.committed=true;
      if(n.wounds===0)n.ready=false;
      if(n.wounds===0){n.deployed=false;n.battlefieldState='out-of-action';}
      const normalAfter=pending.dimensionalBanishmentRemainingWounds??n.wounds;
      log(`${playerName(stage.playerOperativeId)} ${pending.attackType==='shoot'?'shot':'made a Melee attack against'} ${npoName(n)} for ${pending.damage} damage (${before} → ${normalAfter} wounds).`);
      if(pending.dimensionalBanishmentTriggered&&!pending.dimensionalBanishmentJournaled){
        const outcome=pending.dimensionalBanishmentIncapacitated
          ? `${pending.dimensionalBanishmentRoll} exceeded ${normalAfter} remaining wounds, so ${npoName(n)} was incapacitated.`
          : `${npoName(n)} survived with ${normalAfter} wounds.`;
        log(`${playerName(stage.playerOperativeId)} rolled ${pending.dimensionalBanishmentRoll} for Dimensional Banishment against ${npoName(n)}. ${outcome}`);
        pending.dimensionalBanishmentJournaled=true;
      }
      if(checkGameEnd())return true;
    }
    return false;
  }

  function showAggressiveDefenseResolution(stage,pending,target,incapacitationId){
    const retaliation=eventTransaction(`aggressive-defence:${incapacitationId}`);
    if(!Number.isInteger(retaliation.roll))retaliation.roll=Math.ceil(roll()/2);
    pending.aggressiveDefenseRoll=retaliation.roll;
    pending.aggressiveDefenseDamage=aggressiveDefenseDamage(retaliation.roll);
    retaliation.committed=true;
    state.combatState={side:'player',stage:{...stage}};
    save();
    missionDialogLocked=true;
    showModal('Aggressive Defence',`<p><strong>${escapeHtml(npoName(target))}</strong> was incapacitated by an enemy operative within 2 inches.</p><p>Roll one D3 before removing it.</p><section class="combat-stage" aria-label="Aggressive Defence roll"><div class="dice-row animated-roll" id="aggressiveDefenseDie">${rollingDieHtml()}</div><div id="aggressiveDefenseResult" aria-live="polite"></div></section><div class="wizard-actions"><button class="btn primary" id="continueAggressiveDefense" disabled>Continue</button></div>`);
    const button=$('#continueAggressiveDefense');
    const die=$('#aggressiveDefenseDie');
    setTimeout(()=>{
      if(!button?.isConnected)return;
      die.innerHTML=dieHtml({value:retaliation.roll,kind:'hit',retained:true});
      die.classList.replace('animated-roll','settled');
      $('#aggressiveDefenseResult').innerHTML=`<strong>D3 Roll: ${retaliation.roll}</strong><p>${pending.aggressiveDefenseDamage?'The attacking operative suffers 1 damage.':'The attacking operative suffers no damage.'}</p>`;
      button.disabled=false;
    },700);
    button.onclick=()=>{
      if(button.disabled||pending.aggressiveDefenseResolved)return;
      pending.aggressiveDefenseResolved=true;
      const aggressiveDamage=aggressiveDefenseDamageValue(pending);
      if(aggressiveDamage>0&&!pending.aggressiveDefenseDamageApplied){
        const playerBefore=playerCurrentWounds(stage.playerOperativeId);
        const playerAfter=Math.max(0,playerBefore-aggressiveDamage);
        state.playerWounds[stage.playerOperativeId]=playerAfter;
        pending.aggressiveDefenseDamageApplied=true;
        if(playerAfter<=0&&!state.playerCasualtyIds.includes(stage.playerOperativeId))state.playerCasualtyIds.push(stage.playerOperativeId);
        log(`Aggressive Defence dealt ${aggressiveDamage} damage to ${playerName(stage.playerOperativeId)} (${playerBefore} → ${playerAfter} wounds).`);
      }
      state.combatState={side:'player',stage:{...stage}};
      save();missionDialogLocked=false;closeModal();
      if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);
    };
  }

  function showIncapacitationOrderChoice(stage,pending,target,reanimator,incapacitationId,transaction){
    showModal('Choose Incapacitation Effect',`<p>${escapeHtml(npoName(target))} would be incapacitated and two prevention effects are available. Choose which one to resolve first; the other remains available if the first does not prevent incapacitation.</p><div class="wizard-actions"><button class="btn secondary" id="eventReanimationFirst">Event Reanimation Protocols</button><button class="btn secondary" id="macrocyteReanimateFirst">${escapeHtml(npoName(reanimator))} Reanimate</button></div>`);
    const choose=sourceId=>{
      if(transaction.firstSourceId)return;
      transaction.firstSourceId=sourceId;
      save();closeModal();
      if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);
    };
    $('#eventReanimationFirst').onclick=()=>choose('tomb-world-event:reanimation-protocols');
    $('#macrocyteReanimateFirst').onclick=()=>choose('macrocyte-reanimate');
  }

  function offerReanimateForPendingDamage(stage,pending,target,reanimator,incapacitationId,onDecline=null){
    showModal('Reanimate?',`<p>${escapeHtml(npoName(target))} would be incapacitated. ${escapeHtml(npoName(reanimator))} may use Reanimate before removal if all tabletop restrictions are met.</p><div class="checklist"><label class="check-row"><input id="reanimateVisible" type="checkbox"><span>The target is visible to and within 6 inches of the Reanimator.</span></label><label class="check-row"><input id="reanimateControl" type="checkbox"><span>Neither operative is within enemy control range.</span></label>${pending.attackType==='shoot'?'<label class="check-row"><input id="reanimateShoot" type="checkbox"><span>The Reanimator was not a primary or secondary target of this Shoot action.</span></label>':''}</div><div class="wizard-actions"><button class="btn ghost" id="declineReanimate">Decline</button><button class="btn primary" id="acceptReanimate" disabled>Use Reanimate</button></div>`);
    const update=()=>{$('#acceptReanimate').disabled=!$('#reanimateVisible').checked||!$('#reanimateControl').checked||(pending.attackType==='shoot'&&!$('#reanimateShoot').checked);};
    $$('input',modal).forEach(input=>input.onchange=update);
    const resume=()=>{save();closeModal();if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);};
    $('#declineReanimate').onclick=()=>{
      if(onDecline){closeModal();onDecline();return;}
      state.npoRuleState.incapacitationTriggers.push(incapacitationId);resume();
    };
    $('#acceptReanimate').onclick=()=>{
      if(!reanimateEligible({reanimator,target,visible:true,distance:6,shootTargets:[]}))return;
      state.npoRuleState.incapacitationTriggers.push(incapacitationId);
      pending.after=1;pending.damage=Math.max(0,pending.before-1);
      const effect=applyReanimate(reanimator,target,{duringTargetActivation:false});
      log(`${npoName(reanimator)} used Reanimate on ${npoName(target)}; it remains at 1 wound. Apply the optional free Dash within the Reanimator's control range and both -1 APL effects.`);
      pending.reanimate=effect;
      resume();
    };
  }

  async function completePlayerActivation(stage={}){
    stage=normalizeImpossiblePlayerCombat(stage);
    const operativeId=String(stage.playerOperativeId||'');
    const incapacitatedByCurrentHot=state.hotResolution?.attackerSide==='player'
      &&state.hotResolution.attackerId===operativeId&&state.hotResolution.incapacitated;
    if(!remainingPlayerOperatives().includes(operativeId)){
      if(!incapacitatedByCurrentHot){
        state.combatState=null;
        showToast('That operative is no longer available to activate.');
        closeModal();
        setNextActivation('player');
        save();render();
        return;
      }
    }
    const activationId=missionActivationId('player',operativeId);
    const missionFeatureActions=[
      ...(stage.hatch?[{action:'operate-hatch',targetKey:'hatchTargetId',typeKey:'hatchFeatureType',transactionKey:'hatchTransactionId',featureType:'hatchway'}]:[]),
      ...(stage.breach?[{action:'breach',targetKey:'breachTargetId',typeKey:'breachFeatureType',transactionKey:'breachTransactionId',featureType:'breach-point'}]:[])
    ];
    if(state.missionId==='demolition-protocol'&&missionFeatureActions.length&&!stage.missionFeatureCommitted){
      const pending=missionFeatureActions.map(item=>{
        const feature=missionEngine()?.features.find(feature=>feature.id===stage[item.targetKey]);
        const identity=missionFeatureIdentity(feature);
        const transactionId=stage[item.transactionKey]||(item.action==='breach'&&stage.missionFeatureTransactionId)||`${activationId}:${item.action}`;
        const alreadyOpen=Boolean(feature&&state.missionState?.completedFeatureIds?.includes(feature.id));
        const replayed=alreadyOpen&&state.missionState?.featureTransactions?.[transactionId]===feature.id;
        return {...item,feature,identity,transactionId,alreadyOpen,replayed,valid:identity?.featureType===item.featureType&&(!alreadyOpen||replayed)};
      });
      const invalid=pending.find(item=>!item.valid);
      if(invalid){
        const alreadyOpen=invalid.alreadyOpen;
        const retryStage={...stage,[invalid.targetKey]:null,[invalid.typeKey]:invalid.featureType,[invalid.transactionKey]:invalid.transactionId};
        state.combatState={side:'player',stage:retryStage};
        save();
        showModal(alreadyOpen?'Feature already open':`${invalid.action==='operate-hatch'?'Operate Hatch':'Breach'} target unavailable`,`<p>${alreadyOpen?'This feature is already open and does not add additional mission progress. No action was spent.':'The selected feature is missing, stale, or is the wrong type for this action. No action was spent and no mission progress was changed.'}</p><div class="wizard-actions"><button class="btn primary" id="recoverActivationBreach">Return to Target Selection</button></div>`);
        $('#recoverActivationBreach').onclick=()=>showActivationFeatureTargetSelection(retryStage,invalid.action);
        return;
      }
      const missionStateSnapshot=JSON.parse(JSON.stringify(state.missionState));
      const missionRuntimeSnapshot=objectiveEngine?JSON.parse(JSON.stringify(objectiveEngine.getMissionRuntime())):null;
      const journalSnapshot=[...(state.journal||[])];
      for(const item of pending){
        const outcome=commitMissionFeatureOpened({...item.identity,missionId:state.missionId,openedBy:item.action,source:'player-activation',operativeId,turningPoint:state.turningPoint,transactionId:item.transactionId});
        const replayed=outcome.status==='already-open'&&state.missionState?.featureTransactions?.[item.transactionId]===item.feature.id;
        if(outcome.status!=='completed'&&!replayed){
          state.missionState=missionStateSnapshot;
          state.journal=journalSnapshot;
          if(objectiveEngine&&missionRuntimeSnapshot)state.missionRuntime=objectiveEngine.restoreMissionRuntime(objectiveDefinition,missionRuntimeSnapshot,missionLifecycleContext());
          const retryStage={...stage,[item.targetKey]:null,[item.typeKey]:item.featureType,[item.transactionKey]:item.transactionId};
          state.combatState={side:'player',stage:retryStage};
          save();
          showModal(`${item.action==='operate-hatch'?'Operate Hatch':'Breach'} could not be recorded`,'<p>The mission update could not be completed. No action was spent and no mission progress was changed.</p><div class="wizard-actions"><button class="btn primary" id="recoverActivationBreach">Return to Target Selection</button></div>');
          $('#recoverActivationBreach').onclick=()=>showActivationFeatureTargetSelection(retryStage,item.action);
          return;
        }
      }
      stage.missionFeatureCommitted=true;
      stage.missionFeatureCommittedActions=Object.fromEntries(pending.map(item=>[item.action,{featureId:item.feature.id,featureType:item.featureType,transactionId:item.transactionId}]));
      stage.missionFeatureRecord=pending.at(-1)?{featureId:pending.at(-1).feature.id,featureType:pending.at(-1).featureType,openedBy:pending.at(-1).action,transactionId:pending.at(-1).transactionId}:null;
      state.combatState={side:'player',stage:{...stage}};
    }
    state.combatState=null;
    state.missionActionContext=null;
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
    if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
    state.playerReady=playerOperativesRemaining();
    state.playerActivated=state.playerActivatedIds.length;
    state.activationNumber++;
    const summary=playerActivationSummary(stage);
    const attackSummaries=[...pendingAttackResults(stage,'shoot'),...pendingAttackResults(stage,'melee')].map(attack=>({
      targetId:attack.targetId,targetName:attack.targetName,before:attack.before,after:attack.after,damage:attack.damage,attackType:attack.attackType
    }));
    if(state.hotResolution?.attackerSide==='player'&&state.hotResolution.attackerId===operativeId){
      const hot=state.hotResolution;
      const shootingSummary=attackSummaries.find(attack=>attack.attackType==='shoot');
      if(shootingSummary)shootingSummary.hot={roll:hot.roll,damage:hot.damage,woundsBefore:hot.woundsBefore,woundsAfter:hot.woundsAfter,incapacitated:hot.incapacitated};
    }
    state.activationHistory.unshift({side:'player',label:playerName(operativeId),summary,attackSummary:attackSummaries.at(-1)||null,attackSummaries,...(stage.missionBreachRecord?{missionAction:stage.missionBreachRecord}:{})});
    expireActivationEffects(operativeId);
    advanceAfterActivation('player');
    log(`${playerName(operativeId)} completed activation: ${summary}.`);
    if(stage.missionFeatureCommitted)checkGameEnd();
    closeModal();
    save();
    render();
    await executeMissionLifecycleHook('onPlayerActivationCompleted',{activationId,operativeId});
  }

  function npoName(n){
    return operativeName(n,'npo');
  }

  function compareNpoDisplayNames(a,b){
    const displayName=value=>typeof value==='string'?value:npoName(value);
    return String(displayName(a)||'').localeCompare(String(displayName(b)||''),undefined,{numeric:true,sensitivity:'base'});
  }

  function sortedNposForDisplay(npos){
    return [...(Array.isArray(npos)?npos:[])]
      .map((npo,index)=>({npo,index}))
      .sort((a,b)=>compareNpoDisplayNames(a.npo,b.npo)||a.index-b.index)
      .map(item=>item.npo);
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

  function normalizeStableId(value){
    return typeof value==='string'?value.trim():'';
  }

  function stablePlayerIdentityPart(value,fallback){
    const normalized=String(value||'').trim().toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    return normalized||fallback;
  }

  function canonicalPlayerWeaponIdentity({operativeId,attackType,weapon,weaponIndex}){
    const explicitWeaponId=normalizeStableId(weapon?.id);
    const stableIndex=Number.isInteger(weaponIndex)&&weaponIndex>=0?weaponIndex:0;
    const fallbackWeaponId=`player:${stablePlayerIdentityPart(operativeId,'operative')}:${stablePlayerIdentityPart(attackType,'attack')}:${stableIndex}:${stablePlayerIdentityPart(weapon?.name,'weapon')}`;
    const weaponId=explicitWeaponId||fallbackWeaponId;
    const explicitProfileId=normalizeStableId(weapon?.profileKey)||normalizeStableId(weapon?.profileId);
    return {weaponId,profileId:explicitProfileId||`${weaponId}:default`};
  }

  function playerWeaponProfile(weapon,{operativeId,attackType,weaponIndex}={}){
    const damage=parseWeaponDamage(weapon?.damage);
    const lethalRule=(weapon?.rules||[]).map(String).map(rule=>rule.match(/Lethal\s*(\d)\+/i)).find(Boolean);
    const identity=canonicalPlayerWeaponIdentity({operativeId,attackType,weapon,weaponIndex});
    return {
      dice:Number(weapon?.attacks||4),
      hit:Number(weapon?.hit||3),
      critThreshold:Number(lethalRule?.[1]||6),
      normal:damage.normal,
      crit:damage.crit,
      ap:weaponPiercingValue(weapon),
      rules:[...(weapon?.rules||[])],
      ruleIds:[...(weapon?.ruleIds||[])],
      weaponId:identity.weaponId,profileId:identity.profileId,
      weaponName:weapon?.name||'',profileName:weapon?.profileName||weapon?.name||'',
      name:weapon?.profileName||weapon?.name||''
    };
  }

  const combatAbilityHandlers = {
    'dimensional-banishment':({criticalSuccesses,damage,targetIncapacitated})=>
      !targetIncapacitated&&(damage>0||criticalSuccesses>0),
    'aggressive-defence':({targetIncapacitated,attackerWithinTwo})=>
      targetIncapacitated&&attackerWithinTwo
  };

  function weaponRulesHtml(profile){
    const summaries=weaponRuleSummaries(profile).map(summary=>`<li>${escapeHtml(summary.label)}</li>`).join('');
    return summaries?`<section class="weapon-rules"><strong>Weapon rules</strong><ul>${summaries}</ul></section>`:'';
  }

  function normalizedGuidanceMatchText(value){
    return String(value||'').toLowerCase().replace(/&/g,' and ').replace(/[^a-z0-9\s]/g,' ').trim().replace(/\s+/g,' ');
  }

  function inferWeaponGuidanceContext(definition,guidanceText){
    const guidance=` ${normalizedGuidanceMatchText(guidanceText)} `;
    if(!guidance.trim())return null;
    const matches=[];
    for(const [attackType,weapons] of [['shoot',definition?.rangedWeapons||[]],['melee',definition?.meleeWeapons||[]]]){
      for(const weapon of weapons){
        const weaponName=normalizedGuidanceMatchText(weapon.name);
        const candidates=[{name:weaponName,context:{attackType,weaponId:weapon.id}}];
        for(const profile of weapon.profiles||[]){
          const profileName=normalizedGuidanceMatchText(profile.name);
          const context={attackType,weaponId:weapon.id,profileId:profile.id};
          candidates.push(
            {name:`${profileName} ${weaponName}`,context},
            {name:`${weaponName} ${profileName}`,context},
            {name:profileName,context}
          );
        }
        for(const candidate of candidates){
          if(candidate.name&&guidance.includes(` ${candidate.name} `))matches.push(candidate);
        }
      }
    }
    if(!matches.length)return null;
    matches.sort((a,b)=>b.name.length-a.name.length||Number(Boolean(b.context.profileId))-Number(Boolean(a.context.profileId)));
    const mostSpecific=matches.filter(match=>match.name.length===matches[0].name.length);
    const contexts=new Map(mostSpecific.map(match=>[`${match.context.attackType}|${match.context.weaponId}|${match.context.profileId||''}`,match.context]));
    return contexts.size===1?[...contexts.values()][0]:null;
  }

  function npoCombatGuidanceHtml(npo,{attackType,profile}={}){
    const definition=npoDefinition(npo?.type);
    const weaponSentinel=(definition?.abilities||[]).find(ability=>ability.id==='weapon-sentinel');
    const rawGuidance=definition?.behavior?.weaponGuidance;
    const guidance=typeof rawGuidance==='string'
      ? {text:rawGuidance,...inferWeaponGuidanceContext(definition,rawGuidance)}
      : rawGuidance&&typeof rawGuidance==='object'
        ? {...(inferWeaponGuidanceContext(definition,rawGuidance.text)||{}),...rawGuidance}
        : null;
    const items=[guidance,weaponSentinel&&{text:`${weaponSentinel.name}: ${weaponSentinel.text}`,attackType:'shoot'}]
      .filter(item=>item?.text&&item.attackType===attackType&&(!profile||!item.weaponId||item.weaponId===profile.weaponId));
    return items.length?`<div class="summary-box"><strong>Weapon guidance</strong><ul>${items.map(item=>`<li>${escapeHtml(item.text)}</li>`).join('')}</ul></div>`:'';
  }

  function recordedCombat({attackerName,defenderName,attackType,attackerSide,defenderSide,profile,before,normalSuccesses=0,criticalSuccesses=0,damage=0}){
    const appliedDamage=Math.max(0,Math.round(Number(damage)||0));
    return {attackerName,defenderName,attackType,attackerSide,defenderSide,profile,
      normalRemaining:Math.max(0,Math.round(Number(normalSuccesses)||0)),
      critRemaining:Math.max(0,Math.round(Number(criticalSuccesses)||0)),damage:appliedDamage,
      before,after:Math.max(0,before-appliedDamage),attackDice:[],saveDice:[],retainedSaves:0,recordedOutcome:true};
  }

  function resolveDimensionalBanishment(combat,dice){
    if(combat.dimensionalBanishmentResolved)return {...combat};
    const legacyRemaining=Number.isInteger(combat.dimensionalBanishmentRoll)&&combat.dimensionalBanishmentRoll>0&&combat.dimensionalBanishmentTriggered
      ? Math.max(0,Number(combat.before||0)-Number(combat.damage||0))
      : combat.after;
    const normalAfter=Math.max(0,Number(combat.dimensionalBanishmentRemainingWounds??legacyRemaining)||0);
    const triggered=combat.profile?.weaponId==='transdimensional-isolator'
      &&combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:normalAfter<=0});
    if(!triggered)return {...combat,dimensionalBanishmentTriggered:false,dimensionalBanishmentResolved:true};

    const values=Array.isArray(dice)&&dice.length>=2
      ? dice.slice(0,2).map(value=>Math.max(1,Math.min(6,Math.round(Number(value)||1))))
      : [];
    const recordedTotal=!values.length&&Number.isInteger(combat.dimensionalBanishmentRoll)&&combat.dimensionalBanishmentRoll>0
      ? combat.dimensionalBanishmentRoll
      : null;
    const total=recordedTotal??values.reduce((sum,value)=>sum+value,0);
    const incapacitated=total>normalAfter;
    return {...combat,
      dimensionalBanishmentTriggered:true,dimensionalBanishmentResolved:true,
      dimensionalBanishmentDice:values,dimensionalBanishmentRoll:total,
      dimensionalBanishmentRemainingWounds:normalAfter,
      dimensionalBanishmentIncapacitated:incapacitated,
      dimensionalBanishmentAnimationShown:recordedTotal!==null,
      after:incapacitated?0:normalAfter};
  }

  function resolveAutomaticDimensionalBanishment(combat){
    if(combat.dimensionalBanishmentResolved)return {...combat};
    if(Number.isInteger(combat.dimensionalBanishmentRoll)&&combat.dimensionalBanishmentRoll>0){
      return resolveDimensionalBanishment(combat,[]);
    }
    const triggered=combat.profile?.weaponId==='transdimensional-isolator'
      &&combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:combat.after<=0});
    return resolveDimensionalBanishment(combat,triggered?rollDice(2,6):[]);
  }

  function rolledCombatDice(count,threshold,critThreshold=6){
    return Array.from({length:Math.max(0,count)},()=>{
      const value=roll();
      return {value,kind:value>=critThreshold?'crit':value>=threshold?'hit':'miss',retained:false};
    });
  }
  function rolledAttackDiceForProfile(profile){
    const accurate=Math.min(Number(profile?.accurate||0),Math.max(0,Number(profile?.dice||0)));
    const retainedDice=retainSuccessfulDice([
      ...Array.from({length:accurate},()=>({value:Number(profile.hit||2),kind:'hit',retained:true,automatic:'Accurate 1'})),
      ...rolledCombatDice(Math.max(0,Number(profile.dice||0)-accurate),profile.hit,profile.critThreshold)
    ]);
    return applySevereToAttackDice(retainedDice,profile).dice;
  }

  function retainSuccessfulDice(dice=[]){
    return dice.map(die=>({...die,retained:die.kind==='hit'||die.kind==='crit'}));
  }

  function weaponHasRule(profile,ruleId){
    const normalizedId=String(ruleId).trim().toLowerCase();
    return (profile?.ruleIds||[]).some(id=>String(id).trim().toLowerCase()===normalizedId)
      ||(profile?.rules||[]).some(rule=>String(rule||'').trim().toLowerCase()===normalizedId
        ||String(rule||'').trim().toLowerCase().startsWith(`${normalizedId.replace(/-/g,' ')} `));
  }

  function normalizedWeaponRuleId(rule){
    const normalized=String(rule||'').trim().toLowerCase().replace(/[“”"]/g,'').replace(/\s+/g,' ');
    if(/^piercing crits(?:\s+\d+)?$/.test(normalized))return 'piercing-crits';
    if(/^seek light$/.test(normalized))return 'seek-light';
    const match=normalized.match(/^([a-z]+)(?:\s+\d+(?:\+)?)?$/);
    return match?.[1]||normalized.replace(/\s+/g,'-');
  }

  function normalizedWeaponRuleWarningKey(rule){
    return String(rule||'').trim().toLowerCase().replace(/[“”]/g,'"').replace(/\s+/g,' ');
  }

  function weaponRuleValue(profile,ruleId){
    const normalizedId=String(ruleId||'').trim().toLowerCase();
    const direct=Number(profile?.[normalizedId.replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]);
    if(Number.isFinite(direct)&&direct>0)return direct;
    for(const rule of profile?.rules||[]){
      if(normalizedWeaponRuleId(rule)!==normalizedId)continue;
      const value=String(rule).match(/(\d+)/);
      if(value)return Number(value[1]);
    }
    return 0;
  }

  function effectiveDefenseDiceCount(profile,attackDice,baseDice=3){
    let reduction=Math.max(0,Number(profile?.ap||0));
    const piercingCrits=weaponRuleValue(profile,'piercing-crits');
    if(piercingCrits>0&&(attackDice||[]).some(die=>die.retained&&die.kind==='crit'))reduction=Math.max(reduction,piercingCrits);
    return Math.max(0,Number(baseDice||0)-reduction);
  }

  function automaticWeaponRuleMessages(profile,attackDice){
    const messages=[];
    const piercingCrits=weaponRuleValue(profile,'piercing-crits');
    const hasCritical=(attackDice||[]).some(die=>die.retained&&die.kind==='crit');
    if(piercingCrits>0&&hasCritical)messages.push(`Piercing Crits ${piercingCrits} applied: the defender rolls ${piercingCrits} fewer defense dice.`);
    return messages;
  }

  function applyStunForAttack({profile,attackDice,sourceAttackId,targetId,targetName='the target',targetSide='npo'}){
    if(!weaponHasRule(profile,'stun')||!(attackDice||[]).some(die=>die.retained&&die.kind==='crit'))return {applied:false,message:''};
    const modifiers=targetSide==='player'?state.eventState.playerAplModifiers:state.npoRuleState.aplModifiers;
    const id=`stun:${sourceAttackId}:${targetId}`;
    if(modifiers.some(modifier=>modifier.id===id))return {applied:false,message:''};
    modifiers.push({id,sourceId:sourceAttackId,targetId,ruleId:'stun',amount:-1,expires:'end-of-target-next-activation',deferCurrentActivation:false});
    return {applied:true,message:`Stun applied: ${targetName} has -1 APL until the end of its next activation.`};
  }

  function resolveShockCriticalStrike(opponentDice,shockApplied=false){
    const dice=(opponentDice||[]).map(die=>({...die}));
    if(shockApplied)return {dice,applied:false,discardedKind:null};
    let index=dice.findIndex(die=>die.retained&&die.kind==='hit');
    if(index<0)index=dice.findIndex(die=>die.retained&&die.kind==='crit');
    if(index<0)return {dice,applied:true,discardedKind:null};
    const discardedKind=dice[index].kind==='hit'?'normal':'critical';
    dice[index]={...dice[index],retained:false,discardedByShock:true};
    return {dice,applied:true,discardedKind,message:`Shock applied: one unresolved ${discardedKind} success was discarded.`};
  }

  function showGuidedShockStep(combat,onContinue,onBack){
    showModal('Shock',`<p id="shockHelp">Did this NPO just strike with its first critical success?</p><p class="muted">Check the unresolved successes in this Fight sequence. Shock triggers only once.</p><div class="wizard-actions"><button class="btn ghost" id="shockBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn secondary" id="shockNo">No</button><button class="btn primary" id="shockYes">Yes</button></div>`);
    $('#shockBack').onclick=onBack;
    $('#shockNo').onclick=()=>onContinue({...combat,shockResolved:true,shockApplied:false});
    $('#shockYes').onclick=()=>{
      showModal('Shock',`<p id="shockDiscardHelp">Which unresolved opponent success was discarded?</p><p class="muted">Discard one unresolved normal success. Only discard a critical success if no normal success remains.</p><div class="wizard-actions"><button class="btn ghost" id="shockChoiceBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn secondary" id="shockCritical">Critical success</button><button class="btn primary" id="shockNormal">Normal success</button></div>`);
      $('#shockChoiceBack').onclick=()=>showGuidedShockStep(combat,onContinue,onBack);
      const finish=discardedKind=>onContinue({...combat,shockResolved:true,shockApplied:true,shockDiscardedKind:discardedKind,eventMessages:[...(combat.eventMessages||[]),`Shock applied: one unresolved ${discardedKind} success was discarded.`]});
      $('#shockNormal').onclick=()=>finish('normal');
      $('#shockCritical').onclick=()=>finish('critical');
    };
  }

  function weaponRuleSummary(profile,rule){
    const id=normalizedWeaponRuleId(rule),handler=WEAPON_RULE_HANDLERS[id];
    if(!handler){
      const warningKey=normalizedWeaponRuleWarningKey(rule);
      if(!warnedUnsupportedWeaponRules.has(warningKey)){
        warnedUnsupportedWeaponRules.add(warningKey);
        console.warn(`[Weapon rules] ${rule} is not yet supported by the Guide.`);
      }
      return {id:normalizedWeaponRuleWarningKey(rule),label:`${rule} is not yet supported by the Guide.`};
    }
    if(id==='piercing'){
      const value=Number(profile?.ap);
      if(Number.isInteger(value)&&value>0){
        const defenseDice=value===1?'defense die':'defense dice';
        return {id:`piercing-${value}`,label:`Piercing ${value}: Defender rolls ${value} fewer ${defenseDice}. Handled automatically.`};
      }
      const warningKey=`${profile?.weaponId||''}:${profile?.profileId||''}:${String(rule)}`;
      if(!warnedInvalidPiercingSummaries.has(warningKey)){
        warnedInvalidPiercingSummaries.add(warningKey);
        console.warn('[Weapon rules] Piercing has no valid positive value for its summary.');
      }
      return {id:'piercing',label:'Piercing: Handled automatically.'};
    }
    if(id==='hot')return {id,label:"Hot: After this weapon is used, the Guide will roll one D6. If the result is lower than the weapon's Hit stat, the attacker suffers twice the result in damage. Handled automatically."};
    if(handler.mode==='automatic')return {id,label:`${rule}: Handled automatically.`};
    if(id==='range')return {id:`${id}-${weaponRuleValue(profile,id)}`,label:`${rule}: target distance checked before combat`};
    if(id==='blast'||id==='torrent')return {id:`${id}-${weaponRuleValue(profile,id)}`,label:`${rule}: additional targets will be selected next`};
    if(id==='seek-light')return {id,label:'Seek Light: target terrain will be checked'};
    if(id==='shock')return {id,label:'Shock: resolved during the Fight sequence'};
    return {id,label:`${rule}: informational only`};
  }

  function weaponRuleSummaries(profile){
    const summaries=[],seen=new Set();
    for(const rule of profile?.rules||[]){
      const summary=weaponRuleSummary(profile,rule);
      if(seen.has(summary.id))continue;
      seen.add(summary.id);
      summaries.push(summary);
    }
    return summaries;
  }

  function weaponRuleStatuses(profile){
    return weaponRuleSummaries(profile).map(summary=>summary.label);
  }

  function normalizeEffectiveHit(value){
    const hit=Number(value);
    return Number.isInteger(hit)&&hit>=2&&hit<=6?hit:null;
  }

  function normalizeHotResolution(record){
    if(!isRecord(record)||typeof record.id!=='string'||!record.id.startsWith('hot:'))return null;
    const rollValue=Number(record.roll),damageValue=Number(record.damage);
    return {...record,effectiveHit:normalizeEffectiveHit(record.effectiveHit),
      roll:Number.isInteger(rollValue)&&rollValue>=1&&rollValue<=6?rollValue:null,
      damage:Number.isInteger(damageValue)&&damageValue>=0?damageValue:null,
      applied:record.applied===true,acknowledged:record.acknowledged===true,
      historyRecorded:record.historyRecorded===true,continuation:isRecord(record.continuation)?record.continuation:null,
      status:record.status==='error'?'error':record.acknowledged?'complete':'pending'};
  }

  function hotWeaponUseContext({attackerSide,attackerId,activationId,actionId,profile,weaponName,continuation=null}){
    if(!profile||!weaponHasRule(profile,'hot'))return null;
    const duplicateCount=(profile.rules||[]).filter(rule=>normalizedWeaponRuleId(rule)==='hot').length;
    if(duplicateCount>1)console.warn('[Weapon rules] Duplicate Hot rules were normalized to one resolution.',{attackerId,weaponId:profile.weaponId,profileId:profile.profileId});
    return {activationId,actionId,attackerSide,attackerId,weaponId:profile.weaponId,profileId:profile.profileId,
      weaponName:weaponName||profile.weaponName||profile.name,effectiveHit:normalizeEffectiveHit(profile.hit),continuation};
  }

  function createHotResolution(context){
    if(!context)return null;
    const id=`hot:${context.activationId}:${context.actionId}:${context.weaponId}:${context.profileId}`;
    if(state.hotResolution?.id===id)return state.hotResolution;
    return {id,...context,status:'pending',roll:null,damage:null,woundsBefore:null,woundsAfter:null,
      applied:false,acknowledged:false,historyRecorded:false};
  }

  function applyHotDamage(record){
    if(record.applied)return record;
    const attacker=record.attackerSide==='player'?livePlayerOperative(record.attackerId):state.roster.find(npo=>npo.id===record.attackerId);
    const before=record.attackerSide==='player'?playerCurrentWounds(record.attackerId):Number(attacker?.wounds);
    if(!attacker||!Number.isFinite(before))return {...record,status:'error',damage:0,applied:true};
    const damage=record.roll<record.effectiveHit?record.roll*2:0;
    const after=Math.max(0,before-damage),incapacitated=after===0&&before>0;
    if(record.attackerSide==='player'){
      state.playerWounds[record.attackerId]=after;
      if(incapacitated&&!state.playerCasualtyIds.includes(record.attackerId))state.playerCasualtyIds.push(record.attackerId);
      if(incapacitated&&!state.playerActivatedIds.includes(record.attackerId))state.playerActivatedIds.push(record.attackerId);
      state.playerReady=playerOperativesRemaining();
    }else if(attacker){
      attacker.wounds=after;
      if(incapacitated){attacker.ready=false;attacker.deployed=false;attacker.battlefieldState='out-of-action';}
    }
    return {...record,damage,woundsBefore:before,woundsAfter:after,incapacitated,applied:true};
  }

  function resolveHotTransaction(record){
    if(record.acknowledged)return record;
    if(!record.effectiveHit){
      console.warn('[Hot] Effective Hit stat is unavailable.',{attackerId:record.attackerId,weaponId:record.weaponId,profileId:record.profileId,storedHit:record.effectiveHit});
      return {...record,status:'error',damage:0,applied:true};
    }
    if(!Number.isInteger(record.roll)){
      record={...record,roll:roll()};
      state.hotResolution=record;
      save();
    }
    if(!record.applied){
      record=applyHotDamage(record);
      state.hotResolution=record;
      save();
    }
    if(!record.historyRecorded&&!state.journal.some(entry=>entry.transactionId===record.id)){
      const name=record.attackerSide==='player'?playerName(record.attackerId):npoName(state.roster.find(npo=>npo.id===record.attackerId));
      const text=record.incapacitated
        ? `${name} rolled ${record.roll} for Hot, suffered ${record.damage} damage, and was incapacitated.`
        : record.damage?`${name} rolled ${record.roll} for Hot and suffered ${record.damage} damage (${record.woundsBefore} -> ${record.woundsAfter} wounds).`
          : `${name} rolled ${record.roll} for Hot and suffered no damage.`;
      state.journal.unshift({time:new Date().toISOString(),text,transactionId:record.id});
      state.journal=state.journal.slice(0,150);
      record={...record,historyRecorded:true};
      state.hotResolution=record;
      save();
    }else if(!record.historyRecorded){
      record={...record,historyRecorded:true};
      state.hotResolution=record;
      save();
    }
    return record;
  }

  function showHotResult(record,onContinue){
    record=resolveHotTransaction(record);
    state.hotResolution=record;save();
    missionDialogLocked=true;
    if(record.status==='error'){
      showModal('Hot could not be resolved',`<p>The weapon's Hit stat could not be determined. The shooting attack was preserved and no Hot damage was applied.</p><div class="wizard-actions"><button class="btn primary" id="continueHot">Continue</button></div>`);
    }else{
      const name=record.attackerSide==='player'?playerName(record.attackerId):npoName(state.roster.find(npo=>npo.id===record.attackerId));
      const comparison=record.damage?`${record.roll} is lower than ${record.effectiveHit}.`:`The result is not lower than the weapon's Hit stat.`;
      const outcome=record.incapacitated?`${escapeHtml(name)} is incapacitated by Hot.`:record.damage?`${escapeHtml(name)} suffers ${record.damage} damage.<br>Wounds: ${record.woundsBefore} -&gt; ${record.woundsAfter}`:'No damage.';
      const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
      const die=reducedMotion?dieHtml({value:record.roll,ariaLabel:`Hot roll: ${record.roll}`}):rollingDieHtml();
      showModal('HOT',`<section class="combat-stage" aria-label="Hot result"><div class="dice-row ${reducedMotion?'settled':'animated-roll'}" id="hotRollDie">${die}</div><p><strong>Hot roll: ${record.roll}</strong><br>Hit stat: ${record.effectiveHit}+</p><p>${escapeHtml(comparison)}</p><strong>${outcome}</strong></section><div class="wizard-actions"><button class="btn primary" id="continueHot">Continue</button></div>`,undefined,`hot:${record.id}`);
      if(!reducedMotion)setTimeout(()=>{
        const rollDie=$('#hotRollDie');
        if(!rollDie?.isConnected)return;
        rollDie.innerHTML=dieHtml({value:record.roll,ariaLabel:`Hot roll: ${record.roll}`});
        rollDie.classList.replace('animated-roll','settled');
      },700);
    }
    const button=$('#continueHot');button.focus({preventScroll:true});
    button.onclick=()=>{
      if(state.hotResolution?.acknowledged)return;
      button.disabled=true;
      state.hotResolution={...state.hotResolution,acknowledged:true,status:'complete'};
      save();missionDialogLocked=false;closeModal();onContinue();
    };
  }

  function completeShootingWeaponUse(context,onContinue){
    const hotContext=hotWeaponUseContext(context);
    if(!hotContext){onContinue();return;}
    const record=createHotResolution(hotContext);
    state.hotResolution=record;save();
    if(record.acknowledged){onContinue();return;}
    showHotResult(record,onContinue);
  }

  function resumePersistedHotContinuation(record){
    if(record.attackerSide==='player'){
      const stage=state.combatState?.side==='player'?state.combatState.stage:null;
      if(stage)completePlayerActivation(stage);
      else render();
      return;
    }
    const continuation=record.continuation,activation=state.lastActivation;
    if(!continuation||!activation?.pendingAction||activation.npoId!==record.attackerId){render();return;}
    const pending=activation.pendingAction;
    state.weaponRuleResolution=null;
    const hot={roll:record.roll,damage:record.damage,woundsBefore:record.woundsBefore,woundsAfter:record.woundsAfter,incapacitated:record.incapacitated};
    const attackSummary=continuation.attackSummary?{...continuation.attackSummary,hot}:null;
    commitNpoAction({actionId:pending.id,actionName:pending.name,apCost:pending.apCost,
      result:continuation.result,attackSummary,
      attackSummaries:continuation.attackSummaries,transitionMode:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE});
  }

  function createWeaponRuleResolution({activationId,actionId,attackerSide,attackerId,attackType='shoot',weaponId,weaponName,profileKey,profileName,weaponRules=[],ruleId,primaryTargetId,secondaryTargetIds=[],targetDescriptors=[]}){
    if(attackerSide==='player'&&(!weaponId||!profileKey))return null;
    const orderedTargetIds=[...new Set([primaryTargetId,...secondaryTargetIds].filter(Boolean))];
    const descriptorById=new Map(targetDescriptors.filter(isRecord).map(target=>[target.targetId||target.id,target]));
    const orderedTargets=orderedTargetIds.map(targetId=>({targetId,targetSide:descriptorById.get(targetId)?.targetSide||null}));
    return {activationId,actionId,attackerSide,attackerId,attackType,weaponId,weaponName,profileKey,profileName,weaponRules:[...weaponRules],ruleId,primaryTargetId,
      secondaryTargetIds:orderedTargetIds.slice(1),orderedTargetIds,orderedTargets,currentSequenceIndex:0,
      currentTargetId:orderedTargetIds[0]||null,completedTargetIds:[],committedTargetIds:[],sequenceResults:[],
      tabletopCheckConfirmed:true,continueConfirmed:false,completed:orderedTargetIds.length===0};
  }

  function normalizeMultiTargetAttackSequence(resolution,legacyCombatProfile=null){
    if(!isRecord(resolution))return null;
    const orderedTargetIds=[...new Set((Array.isArray(resolution.orderedTargetIds)
      ? resolution.orderedTargetIds
      : [resolution.primaryTargetId,...(resolution.secondaryTargetIds||[])]).filter(Boolean))];
    const completedTargetIds=normalizeIdList(resolution.completedTargetIds).filter(id=>orderedTargetIds.includes(id));
    const nextIndex=orderedTargetIds.findIndex(id=>!completedTargetIds.includes(id));
    const currentId=resolution.currentTargetId&&!completedTargetIds.includes(resolution.currentTargetId)
      ? resolution.currentTargetId
      : nextIndex>=0?orderedTargetIds[nextIndex]:null;
    const legacyProfile=!resolution.weaponId&&legacyCombatProfile?.weaponId&&legacyCombatProfile?.profileId
      ? {weaponId:legacyCombatProfile.weaponId,weaponName:legacyCombatProfile.weaponName,profileKey:legacyCombatProfile.profileId,profileName:legacyCombatProfile.profileName||legacyCombatProfile.name,weaponRules:[...(legacyCombatProfile.rules||[])]}
      : {};
    return {...resolution,...legacyProfile,orderedTargetIds,secondaryTargetIds:orderedTargetIds.slice(1),completedTargetIds,
      committedTargetIds:normalizeIdList(resolution.committedTargetIds),sequenceResults:Array.isArray(resolution.sequenceResults)?resolution.sequenceResults.filter(isRecord):[],
      currentTargetId:currentId,currentSequenceIndex:currentId?orderedTargetIds.indexOf(currentId):orderedTargetIds.length,
      totalSequences:orderedTargetIds.length,completed:currentId===null};
  }

  function advanceMultiTargetAttackSequence(sequence,completedTargetId,result){
    const normalized=normalizeMultiTargetAttackSequence(sequence);
    const completedTargetIds=[...new Set([...(normalized.completedTargetIds||[]),completedTargetId])];
    const sequenceResults=[...(normalized.sequenceResults||[]).filter(item=>item.targetId!==completedTargetId),{...result,targetId:completedTargetId}];
    const nextIndex=normalized.orderedTargetIds.findIndex(id=>!completedTargetIds.includes(id));
    return {...normalized,completedTargetIds,sequenceResults,currentSequenceIndex:nextIndex>=0?nextIndex:normalized.orderedTargetIds.length,
      currentTargetId:nextIndex>=0?normalized.orderedTargetIds[nextIndex]:null,completed:nextIndex<0};
  }

  const advanceWeaponRuleResolution=advanceMultiTargetAttackSequence;

  function lockedMultiTargetProfile(sequence,attacker){
    if(!sequence?.weaponId||!sequence?.profileKey||!attacker)return null;
    if(sequence.attackerSide==='npo'){
      const definition=npoDefinition(attacker.type);
      const weapon=npoWeapon(definition,sequence.weaponId);
      const allowedWeapons=sequence.attackType==='shoot'?definition?.rangedWeapons:definition?.meleeWeapons;
      if(!weapon||!allowedWeapons?.includes(weapon))return null;
      const profile=weaponProfiles(weapon).map(canonicalAttackProfile)
        .find(candidate=>candidate.weaponId===sequence.weaponId&&candidate.profileId===sequence.profileKey);
      return profile?{weapon,profile}:null;
    }
    const operativeId=attacker.id||attacker;
    const weapons=playerAttackWeapons(operativeId,sequence.attackType);
    for(let weaponIndex=0;weaponIndex<weapons.length;weaponIndex++){
      const weapon=weapons[weaponIndex];
      const profile=playerWeaponProfile(weapon,{operativeId,attackType:sequence.attackType,weaponIndex});
      if(profile.weaponId===sequence.weaponId&&profile.profileId===sequence.profileKey)return {weapon,profile,weaponIndex};
    }
    return null;
  }

  function normalizeLegacyPlayerMultiTargetIdentity(sequence,operativeId){
    if(!sequence||sequence.attackerSide!=='player'||(sequence.weaponId&&sequence.profileKey))return {sequence,status:'current'};
    if(!operativeId||!sequence.attackType||!sequence.weaponName||!sequence.profileName)return {sequence,status:'ambiguous'};
    const comparable=value=>String(value||'').trim().toLowerCase();
    const matches=playerAttackWeapons(operativeId,sequence.attackType).map((weapon,weaponIndex)=>({
      weapon,profile:playerWeaponProfile(weapon,{operativeId,attackType:sequence.attackType,weaponIndex})
    })).filter(candidate=>comparable(candidate.profile.weaponName)===comparable(sequence.weaponName)
      &&comparable(candidate.profile.profileName)===comparable(sequence.profileName));
    if(matches.length!==1)return {sequence,status:'ambiguous'};
    const normalized={...sequence,weaponId:matches[0].profile.weaponId,profileKey:matches[0].profile.profileId};
    state.weaponRuleResolution=normalized;
    save();
    return {sequence:normalized,status:'normalized'};
  }

  function showLegacyPlayerWeaponRecovery(onReselect){
    showModal('Weapon selection must be confirmed',`<div class="modal-inner"><div class="summary-box"><strong>Weapon selection must be confirmed</strong><p>The saved attack did not contain a stable weapon identifier. Select the weapon again to continue. No dice or damage were committed.</p></div><div class="wizard-actions"><button class="btn primary" id="reselectLegacyPlayerWeapon">Select Weapon</button></div></div>`);
    $('#reselectLegacyPlayerWeapon').onclick=onReselect;
  }

  function showMultiTargetProfileRecovery(attackerSide,onReturn){
    showModal('Attack profile unavailable',`<div class="modal-inner"><div class="summary-box"><strong>Attack profile unavailable</strong><p>The weapon selected for this multi-target attack could not be restored. Completed target results were preserved.</p></div><div class="wizard-actions"><button class="btn primary" id="returnFromMissingProfile">Return to ${attackerSide==='npo'?'NPO':'Player'} Activation</button></div></div>`);
    $('#returnFromMissingProfile').onclick=onReturn;
  }

  function weaponRuleTargetOption(target){
    const id=escapeHtml(target.id),label=escapeHtml(target.label);
    const ariaLabel=target.ariaLabel?` aria-label="${escapeHtml(target.ariaLabel)}"`:'';
    return `<label class="check-row" for="weapon-rule-target-${id}"><input id="weapon-rule-target-${id}" type="checkbox" value="${id}" data-weapon-rule-target${ariaLabel}><span>${label}</span></label>`;
  }

  function showSeekLightCheck({target,resolutionKey,onContinue,onBack}){
    const saved=state.weaponRuleResolution;
    if(target?.order!=='Conceal'){onContinue(null);return;}
    const savedAnswer=saved?.resolutionKey===resolutionKey?saved.seekLightAnswer:null;
    showModal('Seek Light',`<p id="seekLightHelp">Is the target visible and using Light terrain for cover?</p><p class="muted">Seek Light only bypasses Conceal when the target is using Light terrain for cover. It does not remove a cover save.</p><div class="wizard-actions"><button class="btn ghost" id="seekLightBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn secondary" id="seekLightNo" aria-pressed="${savedAnswer==='no'}">No${savedAnswer==='no'?' (selected)':''}</button><button class="btn primary" id="seekLightYes" aria-pressed="${savedAnswer==='yes'}">Yes${savedAnswer==='yes'?' (selected)':''}</button></div>`);
    const answer=value=>{state.weaponRuleResolution={...(saved?.resolutionKey===resolutionKey?saved:{}),resolutionKey,primaryTargetId:target.id,seekLightAnswer:value,tabletopCheckConfirmed:false};save();onContinue(value);};
    $('#seekLightBack').onclick=onBack;
    $('#seekLightNo').onclick=()=>answer('no');
    $('#seekLightYes').onclick=()=>answer('yes');
  }

  function showSecondaryTargetCheck({ruleId,distance,attackerSide,attackerId,primaryTargetId,targets,weaponId,weaponName,profileKey,profileName,weaponRules,onContinue,onBack}){
    const isBlast=ruleId==='blast';
    const eligible=(targets||[]).filter(target=>target.id!==attackerId&&target.id!==primaryTargetId&&target.inPlay!==false&&Number(target.wounds)>0);
    const question=isBlast
      ? `Which other operatives are visible to and within ${distance} inches of the primary target?`
      : `Are there other valid targets within ${distance} inches of the primary target?`;
    const help=isBlast
      ? `Blast attacks every other operative visible to and within ${distance} inches of the primary target, including friendly operatives.`
      : `Torrent attacks each selected valid enemy target within ${distance} inches of the primary target.`;
    const automaticallySelected=ruleId==='torrent'&&attackerSide==='npo';
    const saved=state.weaponRuleResolution;
    const sameStep=saved?.ruleId===ruleId&&saved?.primaryTargetId===primaryTargetId&&saved?.profileKey===profileKey;
    showModal(ruleId[0].toUpperCase()+ruleId.slice(1),`<p id="secondaryTargetHelp">${escapeHtml(question)}</p><p class="muted">${escapeHtml(help)}</p><div class="checklist" aria-describedby="secondaryTargetHelp">${eligible.length?eligible.map(weaponRuleTargetOption).join(''):'<p class="muted">No other operatives are available.</p>'}</div><label class="check-row"><input id="tabletopCheckConfirmed" type="checkbox"><span>I have confirmed visibility and distance on the tabletop.</span></label><div class="wizard-actions"><button class="btn ghost" id="secondaryTargetsBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmSecondaryTargets" disabled>Continue</button></div>`);
    $$('[data-weapon-rule-target]').forEach(input=>{input.checked=sameStep?(saved.secondaryTargetIds||[]).includes(input.value):automaticallySelected;});
    const confirmation=$('#tabletopCheckConfirmed');
    confirmation.checked=Boolean(sameStep&&saved.tabletopCheckConfirmed);
    const persistStep=()=>{
      const secondaryTargetIds=$$('[data-weapon-rule-target]:checked').map(input=>input.value).filter(id=>id!==primaryTargetId);
      const seekLightAnswer=state.weaponRuleResolution?.primaryTargetId===primaryTargetId?state.weaponRuleResolution.seekLightAnswer:null;
      const selectedTargets=[{id:primaryTargetId,targetSide:attackerSide==='player'?'npo':'player'},...eligible.filter(target=>secondaryTargetIds.includes(target.id))];
      const targetDescriptors=selectedTargets.map(target=>({targetId:target.id,targetSide:target.targetSide||(attackerSide==='player'?'npo':'player')}));
      const resolution=createWeaponRuleResolution({activationId:`${state.turningPoint}:${state.activationNumber}`,actionId:attackerSide==='npo'?'npo-attack':'player-attack',attackerSide,attackerId,weaponId,weaponName,profileKey,profileName,weaponRules,ruleId,primaryTargetId,secondaryTargetIds,targetDescriptors});
      if(!resolution)return;
      state.weaponRuleResolution={...resolution,tabletopCheckConfirmed:confirmation.checked,continueConfirmed:false,...(seekLightAnswer?{seekLightAnswer}:{})};
      save();
    };
    $('#secondaryTargetsBack').onclick=onBack;
    $$('[data-weapon-rule-target]').forEach(input=>input.onchange=persistStep);
    confirmation.onchange=()=>{persistStep();$('#confirmSecondaryTargets').disabled=!confirmation.checked;};
    $('#confirmSecondaryTargets').disabled=!confirmation.checked;
    $('#confirmSecondaryTargets').onclick=event=>{
      if(weaponRuleResumePending)return;
      event.currentTarget.disabled=true;
      persistStep();
      state.weaponRuleResolution={...state.weaponRuleResolution,continueConfirmed:true};
      save();onContinue(state.weaponRuleResolution);
    };
  }

  function weaponRuleSequenceProgress(resolution,targetName,wounds=''){
    if(!resolution||resolution.totalSequences<2)return '';
    const displayRule=resolution.profileKey==='sweeping'?'Sweeping':resolution.ruleId;
    const label=displayRule[0].toUpperCase()+displayRule.slice(1);
    const weapon=resolution.weaponName?`<strong>${escapeHtml(resolution.weaponName)}</strong><br>`:'';
    return `<p class="weapon-rule-progress" aria-live="polite"><strong>${label.toUpperCase()} ATTACK</strong><br>${weapon}Target ${resolution.currentSequenceIndex+1} of ${resolution.totalSequences}<br>${escapeHtml(targetName)}${wounds?` (${escapeHtml(wounds)})`:''}</p>`;
  }

  function showMultiTargetAttackSummary(sequence,attackerSide,onContinue){
    const results=sequence?.sequenceResults||[];
    const ruleName=String(sequence?.ruleId||'multi-target').toUpperCase();
    const rows=results.map(result=>result.skipped
      ? `<div class="attack-confirmation-card"><strong>${escapeHtml(result.targetName||result.targetId)}</strong><p>Skipped: ${escapeHtml(result.skipReason||'Target unavailable')}</p></div>`
      : renderAttackSummary(result)).join('');
    const pending=attackerSide==='player'?'<p class="muted">These results remain pending until the Player activation is completed.</p>':'';
    const buttonLabel=attackerSide==='player'?'Continue Player Activation':'Continue Activation';
    showModal(`${ruleName} ATTACK COMPLETE`,`<div class="modal-inner"><div aria-live="polite">${rows}</div>${pending}<div class="wizard-actions"><button class="btn primary" id="continueMultiTargetSummary">${buttonLabel}</button></div></div>`);
    $('#continueMultiTargetSummary').onclick=onContinue;
  }

  function applySevereToAttackDice(dice,profile){
    const updatedDice=(dice||[]).map(die=>({...die}));
    if(!weaponHasRule(profile,'severe')||updatedDice.some(die=>die.retained&&die.kind==='crit')){
      return {dice:updatedDice,applied:false,convertedIndex:-1};
    }
    const convertedIndex=updatedDice.findIndex(die=>die.retained&&die.kind==='hit');
    if(convertedIndex<0)return {dice:updatedDice,applied:false,convertedIndex:-1};
    updatedDice[convertedIndex]={...updatedDice[convertedIndex],kind:'crit',retained:true,originalKind:'hit',severeConverted:true};
    return {dice:updatedDice,applied:true,convertedIndex};
  }

  function severeAppliedHtml(dice=[],severeApplied=false){
    return severeApplied||dice.some(die=>die.severeConverted)
      ? '<p class="severe-applied" role="status">Severe applied: one normal success became a critical success.</p>'
      : '';
  }

  function runAutomaticCombatRolls({container,profile,defenseSave,rolledAttackDice=null,rolledDefenseDice=null,onComplete}){
    let timer=null;
    const attackDice=rolledAttackDice
      ? applySevereToAttackDice(retainSuccessfulDice(rolledAttackDice),profile).dice
      : rolledAttackDiceForProfile(profile);
    container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row animated-roll">${attackDice.map(()=>rollingDieHtml()).join('')}</div></section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row"><span class="muted">Rolling after the attack…</span></div></section>`;
    timer=setTimeout(()=>{
      if(!container.isConnected)return;
      const defenseCount=effectiveDefenseDiceCount(profile,attackDice,3);
      const defenseDice=rolledDefenseDice||retainSuccessfulDice(rolledCombatDice(defenseCount,Number(defenseSave)||3));
      const automaticMessages=automaticWeaponRuleMessages(profile,attackDice);
      container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row settled" data-combat-attack-dice>${attackDice.map(dieHtml).join('')}</div>${severeAppliedHtml(attackDice)}${automaticMessages.map(message=>`<p role="status">${escapeHtml(message)}</p>`).join('')}</section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row animated-roll" data-combat-save-dice>${defenseDice.length?defenseDice.map(()=>rollingDieHtml()).join(''):'<span class="muted">No defense dice rolled</span>'}</div></section>`;
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

  function aggressiveDefenseFields(npo){
    return npo?.type==='Canoptek Macrocyte Warrior'
      ? '<label class="check-row compact-check"><input type="checkbox" id="attackerWithinTwo"><span><strong>Attacker is within 2&quot; of this Macrocyte</strong><small>Required only if this attack incapacitates the Macrocyte.</small></span></label>'
      : '';
  }

  function aggressiveDefenseDamage(rollResult){
    const result=Math.max(1,Math.min(3,Math.round(Number(rollResult)||1)));
    return result>=2?1:0;
  }

  function aggressiveDefenseDamageValue(combat){
    return Math.max(0,Number(combat?.aggressiveDefenseDamage??combat?.aggressiveDefenceDamage)||0);
  }

  function aggressiveDefenseRollHtml(){
    return `<section class="combat-stage" id="aggressiveDefenseRoll" aria-label="Aggressive Defence roll">
      <small>AGGRESSIVE DEFENSE CONSTRUCT</small>
      <p>The destroyed Macrocyte retaliates.</p>
      <div class="dice-row animated-roll" id="aggressiveDefenseDie">${rollingDieHtml()}</div>
    </section>`;
  }

  function combatAbilityReminder(combat){
    if(combat.dimensionalBanishmentTriggered){
      const dice=combat.dimensionalBanishmentDice||[];
      const total=combat.dimensionalBanishmentRoll;
      const remaining=combat.dimensionalBanishmentRemainingWounds;
      const target=escapeHtml(combat.defenderName||combat.targetName||'The target');
      const rolling=!combat.dimensionalBanishmentAnimationShown&&dice.length===2;
      const diceHtml=dice.length===2
        ? `<div class="dice-row ${rolling?'animated-roll':'settled'}" data-dimensional-banishment-dice>${dice.map((value,index)=>rolling?rollingDieHtml():dieHtml({value,ariaLabel:`Dimensional Banishment die ${index+1}: ${value}`})).join('')}</div>`
        : '';
      const rollText=dice.length===2?`Rolled ${dice[0]} + ${dice[1]} = ${total}.`:`Recorded Dimensional Banishment total: ${total}`;
      const comparison=combat.dimensionalBanishmentIncapacitated
        ? `${total} is greater than the target’s ${remaining} remaining wounds.`
        : `${total} is not greater than the target’s ${remaining} remaining wounds.`;
      const outcome=combat.dimensionalBanishmentIncapacitated?`${target} is incapacitated.`:`${target} survives with ${remaining} wounds.`;
      return `<section class="combat-stage dimensional-banishment-result" aria-label="Dimensional Banishment result"><small>DIMENSIONAL BANISHMENT</small>${diceHtml}<div data-dimensional-banishment-result ${rolling?'hidden':''} aria-live="polite"><p>${rollText}</p><p aria-label="Dimensional Banishment total: ${total}">${comparison}</p><strong>${outcome}</strong></div>${rolling?'<p data-dimensional-banishment-rolling>Rolling 2D6...</p>':''}</section>`;
    }
    if(combat.aggressiveDefenseAnimating)return aggressiveDefenseRollHtml();
    const aggressiveDamage=aggressiveDefenseDamageValue(combat);
    if(Number.isInteger(combat.aggressiveDefenseRoll)||aggressiveDamage>0){
      const attackerName=String(combat.attackerName||'').trim();
      const retaliatoryDamageMessage=aggressiveDamage>0
        ? `${attackerName?`${escapeHtml(attackerName)} suffers`:'The attacking operative suffers'} ${aggressiveDamage} retaliatory damage.`
        : `No retaliatory damage inflicted${attackerName?` on ${escapeHtml(attackerName)}`:''}.`;
      return `<section class="combat-stage aggressive-defense-result" aria-label="Aggressive Defence result">
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

  function showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel,preferredTargetId=''){
    const targets=sortedNposForDisplay(activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0));
    if(!targets.length){
      showToast('No active NPO is available as a target.');
      showPlayerActivation(normalizeImpossiblePlayerCombat(stage));
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
      : `<div class="field"><label>Target NPO</label><select id="combatTarget"><option value="">Select a target NPO...</option>${targets.map(n=>`<option value="${n.id}"${n.id===preferredTargetId?' selected':''}>${escapeHtml(npoName(n))} · Wounds ${projectedNpoWounds(n.id,stage)}/${n.maxWounds} · Save ${n.save}+</option>`).join('')}</select></div>`;
    const weaponControl=weapons.length===1
      ? `<div class="field"><label>Weapon</label><div class="readonly-select">${escapeHtml(weapons[0].name)}</div><input type="hidden" id="playerWeaponSelect" value="0"></div>`
      : `<div class="field"><label>Weapon</label><select id="playerWeaponSelect"><option value="">Select a weapon...</option>${weapons.map((weapon,index)=>`<option value="${index}">${escapeHtml(weapon.name)}</option>`).join('')}</select></div>`;
    const priorShoot=pendingAttackResults(stage,'shoot').find(item=>Number(item.after)<=0);
    const priorElimination=attackType==='melee'&&priorShoot
      ? `<section class="compact-elimination-notice"><strong>☠ ${escapeHtml(priorShoot.targetName)} was eliminated by the Shoot attack.</strong><span>Choose another melee target, or Cancel to revise the activation.</span></section>`
      : '';

    const darkDistance=attackType==='shoot'&&tombWorldEventActive('dark-of-the-tomb')
      ? '<label class="check-row compact-check"><input type="checkbox" id="darkOfTombDistance"><span><strong>Target is more than 8 inches away</strong><small>Required for Dark of the Tomb because the Guide cannot measure tabletop distance.</small></span></label>'
      : '';
    showModal(`Resolve ${attackLabel} Attack`,`
      ${priorElimination}
      <p>Select the target and attack profile before rolling.</p>
      ${targetControl}
      ${weaponControl}
      ${darkDistance}
      <div class="summary-box" id="playerWeaponSummary"><strong>Weapon:</strong> —</div>
      <div id="aggressiveDefenseFields"></div>
      <div id="weaponRules"></div>
      <div class="wizard-actions"><button class="btn ghost" id="cancelPendingAttack">Cancel</button><button class="btn primary" id="openCombatResolution">Continue</button></div>`);

    const targetSelect=$('#combatTarget');
    const weaponSelect=$('#playerWeaponSelect');
    const renderChoices=()=>{
      const target=activeNpos().find(n=>n.id===targetSelect.value);
      const weapon=weaponSelect.value===''?null:weapons[Number(weaponSelect.value)];
      $('#playerWeaponSummary').innerHTML=weapon
        ? `<strong>Weapon:</strong> ${escapeHtml(weapon.name)} · ${weapon.attacks} dice · ${weapon.hit}+ · ${escapeHtml(weapon.damage)}`
        : '<strong>Weapon:</strong> —';
      $('#aggressiveDefenseFields').innerHTML=aggressiveDefenseFields(target);
      const weaponIndex=weapon?weapons.indexOf(weapon):-1;
      $('#weaponRules').innerHTML=weaponRulesHtml(weapon?playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex}):null);
      $('#openCombatResolution').disabled=!target||!weapon;
    };
    targetSelect.addEventListener('change',renderChoices);
    weaponSelect.addEventListener('change',renderChoices);
    $('#cancelPendingAttack').onclick=()=>cancelPendingPlayerCombat(stage,attackType,onCancel);
    $('#openCombatResolution').onclick=()=>{
      const target=activeNpos().find(n=>n.id===targetSelect.value);
      const weaponIndex=Number(weaponSelect.value);
      const weapon=weapons[weaponIndex],profile=playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex});
      const moreThanEight=Boolean($('#darkOfTombDistance')?.checked);
      const proceed=()=>{
        resumeCombatAfterWeaponRuleCheck({
          render:()=>showPlayerCombatResolution(stage,attackType,target.id,weaponIndex,onResolved,onCancel,{moreThanEight,deferRoll:true}),
          onMounted:mounted=>mounted.startRoll(),
          onRecovery:()=>showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel)
        });
      };
      const back=()=>showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);
      const ruleId=weaponHasRule(profile,'blast')?'blast':weaponHasRule(profile,'torrent')?'torrent':null;
      const resolutionKey=`player:${state.turningPoint}:${state.activationNumber}:${stage.playerOperativeId}:${target.id}:${profile.weaponId}`;
      const selectSecondaryTargets=()=>{
        if(!ruleId){proceed();return;}
        const playerTargets=(state.playerRoster||[]).map(id=>({id,targetSide:'player',label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id),wounds:playerCurrentWounds(id),inPlay:state.playerOperativeStates?.[id]?.inPlay!==false}));
        const npoTargets=activeNpos().map(npo=>({id:npo.id,targetSide:'npo',label:npoName(npo),wounds:npo.wounds,inPlay:npo.battlefieldState==='deployed'}));
        showSecondaryTargetCheck({ruleId,distance:weaponRuleValue(profile,ruleId),attackerSide:'player',attackerId:stage.playerOperativeId,primaryTargetId:target.id,targets:ruleId==='blast'?[...playerTargets,...npoTargets]:npoTargets,weaponId:profile.weaponId,weaponName:profile.weaponName,profileKey:profile.profileId,profileName:profile.profileName,weaponRules:profile.rules,onContinue:proceed,onBack:back});return;
      };
      if(weaponHasRule(profile,'seek-light')&&target.order==='Conceal'){showSeekLightCheck({target,resolutionKey,onContinue:selectSecondaryTargets,onBack:back});return;}
      selectSecondaryTargets();
    };
    renderChoices();
    const singleProfile=weapons.length===1?playerWeaponProfile(weapons[0],{operativeId:stage.playerOperativeId,attackType,weaponIndex:0}):null;
    const requiresTabletopCheck=singleProfile&&['seek-light','blast','torrent'].some(ruleId=>weaponHasRule(singleProfile,ruleId));
    if(singleTarget&&weapons.length===1&&singleTarget.type!=='Canoptek Macrocyte Warrior'&&!darkDistance&&!requiresTabletopCheck)showPlayerCombatResolution(stage,attackType,singleTarget.id,0,onResolved,onCancel);
  }

  function showPlayerCombatResolution(stage,attackType,targetId,weaponIndex,onResolved,onCancel,{result=null,animate=true,moreThanEight=false,deferRoll=false}={}){
    let sequence=state.weaponRuleResolution;
    const legacyIdentity=normalizeLegacyPlayerMultiTargetIdentity(sequence,stage.playerOperativeId);
    sequence=legacyIdentity.sequence;
    if(legacyIdentity.status==='ambiguous'){
      showLegacyPlayerWeaponRecovery(()=>{
        const preferredTargetId=sequence.primaryTargetId;
        stage[`${attackType}CombatDraft`]=null;
        state.weaponRuleResolution=null;
        state.combatState={side:'player',stage};
        save();
        showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel,preferredTargetId);
      });
      return;
    }
    const targetSide=state.weaponRuleResolution?.orderedTargets?.find(item=>item.targetId===targetId)?.targetSide||'npo';
    const target=targetSide==='player'?livePlayerOperative(targetId):activeNpos().find(n=>n.id===targetId);
    const locked=sequence?.orderedTargetIds?.length>1?lockedMultiTargetProfile(sequence,stage.playerOperativeId):null;
    if(sequence?.orderedTargetIds?.length>1&&!locked){
      showMultiTargetProfileRecovery('player',()=>{state.weaponRuleResolution=null;state.combatState={side:'player',stage:{...stage,[`${attackType}CombatDraft`]:null}};save();showPlayerActivation(stage);});
      return;
    }
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    const weapon=locked?.weapon||weapons[weaponIndex];
    weaponIndex=locked?locked.weaponIndex:weaponIndex;
    if(!target&&state.weaponRuleResolution?.currentTargetId===targetId){
      console.error('[Combat] Multi-target Player attack target unavailable.',{targetId,sequence:state.weaponRuleResolution});
      const skipped={targetId,targetName:targetId,skipped:true,skipReason:'Target is no longer on the battlefield.'};
      state.weaponRuleResolution=advanceMultiTargetAttackSequence(state.weaponRuleResolution,targetId,skipped);
      save();
      if(state.weaponRuleResolution.currentTargetId){
        showPlayerCombatResolution(stage,attackType,state.weaponRuleResolution.currentTargetId,weaponIndex,onResolved,onCancel,{deferRoll:false});
      }else showMultiTargetAttackSummary(state.weaponRuleResolution,'player',()=>{state.weaponRuleResolution=null;save();resolvePendingPlayerAttacks(stage);});
      return;
    }
    if(!target||!weapon){showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);return;}
    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    const profile=locked?.profile||playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex});
    const targetName=targetSide==='player'?playerName(targetId):npoName(target);
    const attackerWithinTwo=Boolean($('#attackerWithinTwo')?.checked)||Boolean(result?.attackerWithinTwo);
    const screen=showSharedCombatResolutionScreen({
      title:`Resolve ${attackLabel} Attack`,attackerName:playerName(stage.playerOperativeId),defenderName:targetName,
      attackType,weaponName:weapon.name,attackLabel:attackType==='shoot'?combatAttackLabel(profile):'',
      defenseLabel:`${Math.max(0,3-profile.ap)} dice · ${target.save}+`,
      cancelId:'cancelPendingAttack',continueId:'continuePendingAttack',
      detailsHtml:weaponRuleSequenceProgress(sequence,targetName,`${targetSide==='player'?playerCurrentWounds(targetId):projectedNpoWounds(targetId,stage)}/${target.maxWounds||playerDefinition(targetId)?.wounds||0} wounds`)
    });

    $('#cancelPendingAttack').onclick=()=>{
      stage[`${attackType}CombatDraft`]=null;
      if(sequence){
        const listKey=attackType==='shoot'?'pendingShootResults':'pendingMeleeResults';
        const legacyKey=attackType==='shoot'?'pendingShoot':'pendingMelee';
        stage[listKey]=[];
        stage[legacyKey]=null;
        state.weaponRuleResolution=null;
      }
      state.combatState=null;
      save();
      if(sequence)showPlayerActivation(stage);
      else showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);
    };

    if(result){
      displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false);
      return;
    }

    const transactionId=`attack:${state.turningPoint}:${state.activationNumber}:${attackType}:${stage.playerOperativeId}:${targetId}`;
    const transaction=eventTransaction(transactionId,{definitionAnswers:{}});
    transaction.definitionAnswers.attackerWithinTwo=attackerWithinTwo;
    if(result?.moreThanEight!==undefined)transaction.definitionAnswers.moreThanEight=result.moreThanEight;
    else if(transaction.definitionAnswers.moreThanEight===undefined)transaction.definitionAnswers.moreThanEight=Boolean(moreThanEight);
    const rerolls=effectiveAttackRerolls({attackerSide:'player',attackType,moreThanEight:transaction.definitionAnswers.moreThanEight});
    const diceDraft={attackDice:[],defenseDice:[],attackerWithinTwo:transaction.definitionAnswers.attackerWithinTwo,moreThanEight:transaction.definitionAnswers.moreThanEight,rerolls,transactionId};
    save();
    let rollStarted=false;
    const startRoll=()=>{
      if(rollStarted)return;
      rollStarted=true;
      runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,onComplete:(attackDice,defenseDice)=>{
        diceDraft.attackDice=attackDice;
        diceDraft.defenseDice=defenseDice;
        previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,{targetId,weaponIndex,targetSide});
      }});
    };
    if(!deferRoll)startRoll();
    return {...screen,startRoll};
  }

  function previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,selection={}){
    const targetId=selection.targetId||$('#combatTarget')?.value;
    const targetSide=selection.targetSide||state.weaponRuleResolution?.orderedTargets?.find(item=>item.targetId===targetId)?.targetSide||'npo';
    const n=targetSide==='player'?livePlayerOperative(targetId):state.roster.find(x=>x.id===targetId);
    if(!n)return;
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    const weaponIndex=Number(selection.weaponIndex??$('#playerWeaponSelect')?.value)||0;
    const weapon=weapons[weaponIndex];
    const locked=state.weaponRuleResolution?.orderedTargetIds?.length>1?lockedMultiTargetProfile(state.weaponRuleResolution,stage.playerOperativeId):null;
    const profile=locked?.profile||playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex});
    const targetName=targetSide==='player'?playerName(n.id):npoName(n);
    const before=targetSide==='player'?playerCurrentWounds(n.id):projectedNpoWounds(n.id,stage);
    const resolution=resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile);
    const result={
      ...recordedCombat({attackerName:playerName(stage.playerOperativeId),defenderName:targetName,attackType,attackerSide:'player',defenderSide:targetSide,profile:{...profile,rules:weapon.rules||[]},before,
        normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage}),
      targetId:n.id,targetName,side:targetSide,weaponName:weapon.name,weaponIndex,
      severeApplied:diceDraft.attackDice.some(die=>die.severeConverted)
    };
    const stun=applyStunForAttack({profile,attackDice:diceDraft.attackDice,sourceAttackId:diceDraft.transactionId,targetId:n.id,targetName,targetSide});
    result.rolledAttackDice=diceDraft.attackDice.map(die=>({...die}));
    result.rolledDefenseDice=diceDraft.defenseDice.map(die=>({...die}));
    result.attackDice=result.rolledAttackDice;
    result.saveDice=result.rolledDefenseDice;
    result.retainedSaves=retainedDiceTotals(result.saveDice).normal+retainedDiceTotals(result.saveDice).critical;
    result.recordedOutcome=false;
    result.attackerWithinTwo=Boolean(diceDraft.attackerWithinTwo);
    result.moreThanEight=Boolean(diceDraft.moreThanEight);
    result.rerolls=diceDraft.rerolls;
    result.transactionId=diceDraft.transactionId;
    const transaction=eventTransaction(result.transactionId,{definitionAnswers:{}});
    const packets=EventEffects.damagePackets(resolution.normal,resolution.critical,profile);
    result.damagePackets=EventEffects.resolveCountertemporalPackets(state,packets,{turningPoint:state.turningPoint,attackerSide:'player',defenderSide:'npo',attackType,savedRolls:transaction.countertemporalRolls,rollD6:()=>roll()});
    transaction.countertemporalRolls=result.damagePackets.map(packet=>Number.isInteger(packet.countertemporalRoll)?packet.countertemporalRoll:null);
    result.eventMessages=[...(diceDraft.rerolls.messages||[]),...(stun.message?[stun.message]:[])];
    if(result.damagePackets.some(packet=>Number.isInteger(packet.countertemporalRoll)))result.eventMessages.push('Countertemporal Shifting: Resolved one D6 for each qualifying attack die.');
    result.damage=result.damagePackets.reduce((total,packet)=>total+packet.finalDamage,0);
    result.after=Math.max(0,result.before-result.damage);
    result.aggressiveDefenseDamage=0;
    const resolvedResult=resolveAutomaticDimensionalBanishment(result);
    stage[`${attackType}CombatDraft`]=resolvedResult;
    state.combatState={side:'player',stage:{...stage}};
    save();
    displayPendingPlayerCombat(stage,attackType,resolvedResult,onResolved,onCancel,false);
  }

  function displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,animate,waiting=false){
    const banishmentAnimating=result.dimensionalBanishmentTriggered&&!result.dimensionalBanishmentAnimationShown;
    let resolutionCommitted=false;
    const display=displaySharedCombatResult(result,{
      pending:true,animate,waiting:waiting||banishmentAnimating,
      message:'This result has been recorded. Wounds will be applied exactly once when you Continue.',
      onContinue:()=>{
        if(resolutionCommitted||stage[`${attackType}CombatDraft`]!==result)return;
        resolutionCommitted=true;
        onResolved(result);
      }
    });
    if(banishmentAnimating){
      result.dimensionalBanishmentAnimationShown=true;
      stage[`${attackType}CombatDraft`]=result;
      state.combatState={side:'player',stage:{...stage}};
      save();
      settleDimensionalBanishment(result,()=>{
        display?.completeWaiting();
      });
    }
  }

  function npoBehavior(n){return npoDefinition(n.type)?.behavior;}

  function npoActionId(actionName){
    const normalized=String(actionName).toLowerCase();
    return normalized.startsWith('fight')?'fight':normalized.startsWith('shoot')?'shoot':normalized.startsWith('charge')?'charge':normalized.startsWith('dash')?'dash':normalized.startsWith('fall back')?'fall-back':normalized.startsWith('reposition')?'reposition':normalized.replace(/\s+/g,'-');
  }
  const NPO_CORE_ACTION_COSTS={'reposition':1,'dash':1,'charge':1,'shoot':1,'fight':1,'fall-back':2};
  const NPO_ACTION_INQUIRIES={
    'fall-back':{
      concernsControlRange:true,
      applicabilityQuestion:'Is this NPO within the control range of any Player operative?',
      feasibilityQuestion:'Can it move away and finish outside every Player operative’s control range?',
      applicabilityHelp:'Select Yes if this NPO is currently within a Player operative’s control range. Do not move the NPO yet.',
      feasibilityHelp:n=>`Move it up to ${npoDefinition(n.type)?.move} inches. Select Yes only if its base fits at a destination outside every Player operative’s control range.`,
      selectedInstruction:'Fall Back using the shortest available route and finish outside every Player operative’s control range.'
    },
    shoot:{
      feasibilityQuestion:'Does this NPO currently have a Player operative it can Shoot without moving?',
      help:'Select Yes if it can make a shooting attack from its current position. Do not move the NPO.',
      selectedInstruction:'Shoot the first Player operative that matches the target priority.'
    },
    fight:{
      concernsControlRange:true,
      feasibilityQuestion:'Is a valid Player operative currently within this NPO’s control range?',
      help:'Select Yes if this NPO can Fight a Player operative from its current position. Do not move the NPO.',
      selectedInstruction:'Fight the first Player operative that matches the target priority.'
    },
    charge:{
      feasibilityQuestion:'Can this NPO reach a Player operative with a Charge?',
      help:'Measure the Charge. Select Yes only if its base can reach and fit next to a target. The app will choose which target to Charge.',
      selectedInstruction:'Charge the first Player operative that matches the target priority.'
    },
    'geomantic-disturbance':{
      feasibilityQuestion:'Can the Geomancer see a terrain point within 8 inches?',
      help:'Select Yes only if it has an Engage order, is outside enemy control range, and can see a terrain point within 8 inches.'
    },
    'canoptek-control':{
      feasibilityQuestion:'Can the Geomancer see a friendly Canoptek within 6 inches?',
      help:'Select Yes only if the Geomancer is outside enemy control range and is not counteracting.'
    },
    'molecular-breach':{
      feasibilityQuestion:'Can the Geomancer see a friendly Canoptek Circle NPO within 6 inches?',
      help:'Select Yes only if the Geomancer is outside enemy control range.'
    },
    overcharge:{
      feasibilityQuestion:'Can the Accelerator see another friendly Canoptek within 3 inches?',
      help:'Select Yes only if the Accelerator is outside enemy control range.'
    },
    'cranial-overload':{
      feasibilityQuestion:'Can the Accelerator see a Player operative within 3 inches?',
      help:'Select Yes only if the Accelerator is outside enemy control range.'
    },
    'nanoscarab-beam':{
      feasibilityQuestion:'Can the Reanimator see a wounded Canoptek Circle NPO within 6 inches?',
      help:'Select Yes only if the target is not incapacitated and was not saved by Reanimate this turning point.'
    }
  };
  function npoMovementFocus(n,action){
    const id=npoDefinition(n.type)?.id;
    if(['geomancer','canoptek-macrocyte-accelerator','canoptek-macrocyte-reanimator'].includes(id))return 'support';
    if(String(action).includes('closest player operative'))return 'fight';
    if(String(action).includes('valid unobscured target'))return 'shoot';
    return 'mission';
  }
  const missingNpoRepositionMoveWarnings=new Set();
  function npoRepositionDistance(npo){
    const currentMove=Number(npo?.move),definitionMove=Number(npoDefinition(npo?.type)?.move);
    if(Number.isFinite(currentMove)&&currentMove>0)return currentMove;
    if(Number.isFinite(definitionMove)&&definitionMove>0)return definitionMove;
    const warningKey=npo?.type||npo?.id||'unknown';
    if(!missingNpoRepositionMoveWarnings.has(warningKey)){
      missingNpoRepositionMoveWarnings.add(warningKey);
      console.warn(`Unable to resolve Reposition distance for NPO: ${warningKey}`);
    }
    return null;
  }
  function formatMovementDistance(distance){
    if(!Number.isFinite(distance))return '';
    return `${distance} ${distance===1?'inch':'inches'}`;
  }
  function npoMovementInquiry(n,action,id){
    const activation=state.lastActivation,focus=npoMovementFocus(n,action),remainingAp=Number(activation?.remainingAp||0);
    const declined=new Set(activation?.declinedMovementIntentIds||[]);
    const shootCanFollow=remainingAp>=2&&!(activation?.completedActionIds||[]).includes('shoot')&&!(activation?.completedActionIds||[]).includes('fight');
    const fightCanFollow=remainingAp>=2&&!(activation?.completedActionIds||[]).includes('fight')&&!(activation?.completedActionIds||[]).includes('shoot');
    if(id==='reposition'){
      const distance=formatMovementDistance(npoRepositionDistance(n));
      if(focus==='shoot'&&shootCanFollow&&!declined.has('reposition-enable-shoot'))return {id:'reposition-enable-shoot',purpose:'enable-shoot',followUpActionId:'shoot',guaranteesFollowUp:true,question:distance?`Can this NPO Reposition up to ${distance} and finish where it can Shoot?`:'Can this NPO Reposition to a position where it can Shoot?',help:'Select Yes only if it can finish the Reposition with a Player operative it can Shoot.'};
      if(focus==='shoot')return {id:'reposition-general-position',purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false,question:distance?`Can this NPO Reposition up to ${distance} to improve its position for the next activation or the mission?`:'Can this NPO Reposition to improve its position for the next activation or the mission?',help:'Select Yes if it can move closer to a future shooting position, gain useful cover, or help complete or defend the mission.'};
      if(focus==='fight'&&fightCanFollow)return {id:'reposition-enable-fight',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:false,question:distance?`Can this NPO Reposition up to ${distance} closer to its target?`:'Can this NPO Reposition closer to its target?',help:'Select Yes if it can move closer to the nearest Player operative, using cover when possible.'};
      if(focus==='fight')return {question:distance?`Can this NPO Reposition up to ${distance} closer to its target?`:'Can this NPO Reposition closer to its target?',help:'Select Yes if it can move closer to the nearest Player operative, using cover when possible.'};
      if(focus==='support')return {question:distance?`Can this NPO Reposition up to ${distance} to use a support action or help the mission?`:'Can this NPO Reposition to use a support action or help the mission?',help:'Select Yes if moving would help it use a higher-priority action or improve its mission position.'};
      return {question:distance?`Can this NPO Reposition up to ${distance} to help complete or defend the mission?`:'Can this NPO Reposition to help complete or defend the mission?',help:'Select Yes only if it can reach a clearly better mission position.'};
    }
    if(remainingAp===1)return {id:'dash-final-position',purpose:'final-position',followUpActionId:null,guaranteesFollowUp:false,endsActivation:true,question:'Can this NPO use its last AP to Dash to a better position?',help:'Select Yes if the Dash improves cover, mission position, or its setup for the next Turning Point. The activation will end after the Dash.'};
    if(focus==='shoot'&&shootCanFollow&&!declined.has('dash-enable-shoot'))return {id:'dash-enable-shoot',purpose:'enable-shoot',followUpActionId:'shoot',guaranteesFollowUp:true,question:'Can a 3-inch Dash move this NPO to a position where it can Shoot?',help:'Select Yes only if it can finish the Dash with a Player operative it can Shoot.'};
    if(focus==='shoot')return {id:'dash-general-position',purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false,question:'Can a 3-inch Dash improve this NPO’s position?',help:'Select Yes if it improves cover, moves it toward the mission, or sets up a better position for a later activation.'};
    if(focus==='fight'&&fightCanFollow)return {id:'dash-enable-fight',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:false,question:'Can a 3-inch Dash move this NPO closer to its target?',help:'Select Yes if the Dash moves it closer to the nearest Player operative, using cover when possible.'};
    if(focus==='fight')return {question:'Can a 3-inch Dash move this NPO closer to its target?',help:'Select Yes if the Dash moves it closer to the nearest Player operative, using cover when possible.'};
    if(focus==='support')return {question:'Can a 3-inch Dash help this NPO use a support action?',help:'Select Yes if the Dash helps it reach an ally, enemy, or mission position needed for a higher-priority action.'};
    return {question:'Can a 3-inch Dash put this NPO in a better position?',help:'Select Yes if the Dash moves it toward a clear shot or a better mission position.'};
  }
  function npoMovementInstruction(n,action){
    const name=npoActionId(action)==='dash'?'Dash':'Reposition';
    const distance=name==='Dash'?'3 inches':formatMovementDistance(npoRepositionDistance(n)),focus=npoMovementFocus(n,action);
    if(name==='Reposition'&&state.lastActivation?.movementIntent?.purpose==='enable-shoot')return distance?`Move this NPO up to ${distance} and finish where it can Shoot.`:'Move this NPO and finish where it can Shoot.';
    if(name==='Reposition'&&state.lastActivation?.movementIntent?.purpose==='general-position')return distance?`Move this NPO up to ${distance} to improve its cover, mission position, or setup for a later activation.`:'Move this NPO to improve its cover, mission position, or setup for a later activation.';
    if(focus==='fight')return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward the selected Player operative, using cover when possible.`:`Move this NPO toward the selected Player operative, using cover when possible.`;
    if(focus==='shoot')return name==='Dash'?`Dash this NPO up to 3 inches toward a clear shot or a better mission position.`:distance?`Move this NPO up to ${distance} to get a clear shot. If that is not possible, move it to help the mission.`:'Move this NPO to get a clear shot. If that is not possible, move it to help the mission.';
    if(focus==='support')return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward an ally, enemy, or mission position needed for its next support action.`:`Move this NPO toward an ally, enemy, or mission position needed for its next support action.`;
    return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward the mission objective or a position that helps defend it.`:`Move this NPO toward the mission objective or a position that helps defend it.`;
  }
  function npoActionCost(n,actionId){
    const profileAction=(npoDefinition(n?.type)?.actions||[]).find(action=>action.id===actionId);
    if(profileAction&&Number.isFinite(Number(profileAction.ap)))return Math.max(0,Number(profileAction.ap));
    return Object.prototype.hasOwnProperty.call(NPO_CORE_ACTION_COSTS,actionId)?NPO_CORE_ACTION_COSTS[actionId]:null;
  }
  function npoActionChangesContext(actionId){
    return ['reposition','dash','charge','fall-back'].includes(actionId);
  }
  function conciseNpoActionName(action){
    if(NPO_CORE_ACTION_COSTS[action.id]===undefined)return action.name;
    return action.id==='fall-back'?'Fall Back':action.id[0].toUpperCase()+action.id.slice(1);
  }
  function legalNpoActions(n,context={}){
    const definition=npoDefinition(n?.type);
    if(!definition||n.wounds<=0||!n.ready)return [];
    const activation=state.lastActivation?.npoId===n.id?state.lastActivation:null;
    const remainingAp=Number.isFinite(context.remainingAp)?context.remainingAp:Number(activation?.remainingAp??effectiveApl(n.id,definition.apl));
    const completed=new Set(context.completedActionIds||activation?.completedActionIds||[]);
    return (npoBehavior(n)?.actions||[]).filter(actionName=>{
      const id=npoActionId(actionName),profileAction=(definition.actions||[]).find(action=>action.id===id),cost=npoActionCost(n,id);
      if(cost===null||cost>remainingAp||completed.has(id))return false;
      if(['shoot','fight','charge'].includes(id)&&!inPlayLivingPlayerOperativeIds().length)return false;
      if(id==='shoot'&&!(definition.rangedWeapons||[]).length)return false;
      if(id==='fight'&&!(definition.meleeWeapons||[]).length)return false;
      if((id==='shoot'&&completed.has('fight'))||(id==='fight'&&completed.has('shoot')))return false;
      if(id==='charge'&&['reposition','fall-back'].some(done=>completed.has(done)))return false;
      if(['reposition','dash','fall-back'].includes(id)&&completed.has('charge'))return false;
      if(id==='fall-back'&&['reposition','charge'].some(done=>completed.has(done)))return false;
      if(context.inEnemyControlRange&&profileAction?.restrictions?.actorOutsideEnemyControlRange)return false;
      if(context.counteracting&&profileAction?.restrictions?.notCounteracting)return false;
      if(profileAction?.restrictions?.ordersExcluded?.includes(n.order))return false;
      if(profileAction?.oncePerTurningPoint&&state.npoRuleState.oncePerTurningPoint[id]===state.turningPoint)return false;
      return true;
    });
  }
  function rankLegalNpoActions(n,legalActions,context={}){
    const definition=npoDefinition(n.type);
    const priorities={
      'geomancer':['Canoptek Control','Molecular Breach','Geomantic Disturbance','Shoot','Fight','Reposition','Dash'],
      'canoptek-tomb-crawler':context.inEnemyControlRange?['Fight','Shoot','Charge','Reposition','Dash']:['Shoot','Charge','Fight','Reposition','Dash'],
      'canoptek-macrocyte-warrior':context.inEnemyControlRange?['Fight','Shoot','Charge','Reposition','Dash']:['Shoot','Charge','Fight','Reposition','Dash'],
      'canoptek-macrocyte-accelerator':['Overcharge','Cranial Overload','Shoot','Fight','Reposition','Dash'],
      'canoptek-macrocyte-reanimator':['Nanoscarab Beam','Reposition','Dash','Shoot','Fight']
    };
    const order=priorities[definition.id]||npoBehavior(n)?.actions||[];
    return [...legalActions].sort((a,b)=>order.indexOf(a)-order.indexOf(b));
  }
  function recommendedNpoActions(n,context={}){
    return rankLegalNpoActions(n,legalNpoActions(n,context),context);
  }

  function attackAvailabilityForMovementIntent(activation,intent){
    if(intent?.followUpActionId==='shoot')return activation.currentContext.hasValidShootTarget;
    if(intent?.followUpActionId==='fight')return activation.currentContext.hasValidFightTarget;
    return undefined;
  }

  function directNpoAttackQuestion(n,action,availability=null){
    const actionId=npoActionId(action),inquiry=NPO_ACTION_INQUIRIES[actionId];
    return {key:`${actionId}-feasibility`,action,actionId,type:'feasibility',title:inquiry.feasibilityQuestion,help:inquiry.help,movementIntent:null,autoSelect:availability===true,concernsControlRange:Boolean(inquiry.concernsControlRange)};
  }

  function npoActionQuestion(n,index){
    const activation=state.lastActivation;
    const action=recommendedNpoActions(n,activation?.currentContext||{}).filter(name=>!(activation?.declinedActionIds||[]).includes(npoActionId(name)))[index];
    if(!action)return null;
    const id=npoActionId(action),inquiry=NPO_ACTION_INQUIRIES[id];
    const legalActions=legalNpoActions(n,activation?.currentContext||{});
    const directAvailability=id==='shoot'?activation.currentContext.hasValidShootTarget:id==='fight'?activation.currentContext.hasValidFightTarget:undefined;
    if(directAvailability===true)return directNpoAttackQuestion(n,action,directAvailability);
    const fightAction=legalActions.find(name=>npoActionId(name)==='fight');
    const chargeIntent=id==='charge'&&fightAction?{id:'charge-enable-fight',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:activation.remainingAp>=2}:null;
    let movementInquiry=['reposition','dash'].includes(id)?npoMovementInquiry(n,action,id):chargeIntent;
    const intendedAttack=movementInquiry?.followUpActionId&&legalActions.find(name=>npoActionId(name)===movementInquiry.followUpActionId);
    if(movementInquiry?.followUpActionId&&!intendedAttack){
      movementInquiry={...movementInquiry,id:`${id}-general-position`,purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false};
    }
    const availability=attackAvailabilityForMovementIntent(activation,movementInquiry);
    if(availability===null||availability===true){
      if(intendedAttack)return directNpoAttackQuestion(n,intendedAttack,availability);
    }
    const applicability=id==='fall-back'&&activation.currentContext?.inEnemyControlRange===null;
    const title=applicability?inquiry.applicabilityQuestion:(movementInquiry?.question||inquiry?.feasibilityQuestion||`Can this NPO use ${action} now?`);
    const inquiryHelp=applicability?inquiry?.applicabilityHelp:(id==='charge'&&activation.remainingAp===1
      ? 'Measure the Charge. Select Yes only if its base can reach and fit next to a target. This will spend its last AP, so it will not Fight afterward.'
      : inquiry?.feasibilityHelp??inquiry?.help);
    const help=movementInquiry?.help||(typeof inquiryHelp==='function'?inquiryHelp(n):inquiryHelp);
    return {key:movementInquiry?.id||`${id}-${applicability?'applicability':'feasibility'}`,action,actionId:id,type:applicability?'applicability':'feasibility',title,help:help||'Check the action’s target, distance, and placement. Select Yes only if the action can be completed now.',movementIntent:movementInquiry||null,concernsControlRange:Boolean(inquiry?.concernsControlRange)};
  }

  const npoMovementIcons = Object.freeze({
    reposition:'movement',dash:'movement',repositionToShoot:'moveToShoot',dashToShoot:'moveToShoot'
  });
  const npoQuestionIcons = {
    Fight:'radar',Charge:'charge-movement',Shoot:'crosshair','Fall Back':'charge',Reposition:npoMovementIcons.reposition,Dash:npoMovementIcons.dash
  };

  function npoIcon(type){
    if(type==='command')return npoIcon('radar');
    if(type==='moveToShoot')return `<svg class="npo-question-icon npo-question-icon--movement is-move-to-shoot" viewBox="0 0 42 32" fill="none" aria-hidden="true" focusable="false"><g fill="currentColor" stroke="currentColor"><circle cx="3" cy="16" r="3" stroke="none"/><path d="M6 16h20" fill="none" stroke-width="2"/><path d="m8 12.5 5 3.5-5 3.5Z" stroke="none"/><path d="m13.5 12.5 5 3.5-5 3.5Z" stroke="none"/><path d="m19 12.5 5 3.5-5 3.5Z" stroke="none"/><circle cx="35" cy="16" r="4" fill="none" stroke-width="2"/><circle cx="35" cy="16" r="1.25" stroke="none"/><path d="M35 6v6M35 20v6M25 16h6M39 16h2" fill="none" stroke-width="2"/></g></svg>`;
    const paths={
      crosshair:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>',
      objective:'<path d="M6 21V4m0 1h11l-2 4 2 4H6"/><circle cx="6" cy="21" r="2"/>',
      wounded:'<path d="M12 21s-7-4.4-7-10a4 4 0 017-2.7A4 4 0 0119 11c0 5.6-7 10-7 10z"/><path d="M9 12h2l1-3 2 6 1-3h2"/>',
      shield:'<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z"/><path d="M8 12h8"/>',
      group:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6m0-5c3 0 5 2 5 5"/>'
    };
    if(type==='movement'||type==='charge-movement')return `<svg
  class="npo-question-icon ${type==='movement'?'npo-question-icon--movement':'npo-question-icon--charge'} is-movement"
  viewBox="0 0 32 32"
  width="32"
  height="32"
  fill="currentColor"
  stroke="currentColor"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  focusable="false"
>
  <circle cx="4" cy="16" r="3" stroke="none" />
  <line x1="7" y1="16" x2="25" y2="16" fill="none" stroke-width="2" />
  <path d="M9 12.5L14 16L9 19.5Z" stroke="none" />
  <path d="M14 12.5L19 16L14 19.5Z" stroke="none" />
  <path d="M19 12.5L24 16L19 19.5Z" stroke="none" />
  <circle cx="28" cy="16" r="3" fill="none" stroke-width="2" />
</svg>`;
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
    if(!paths[type])return npoIcon('radar');
    return `<svg class="npo-question-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths[type]}</svg>`;
  }

  function iconForNpoQuestion(question){
    const actionId=npoActionId(question?.action||'');
    const enablesShoot=question?.movementIntent?.purpose==='enable-shoot'||question?.movementIntentId?.endsWith('-enable-shoot');
    if(enablesShoot&&['reposition','dash'].includes(actionId))return npoMovementIcons[`${actionId}ToShoot`];
    if(question.concernsControlRange)return 'radar';
    return npoQuestionIcons[question.action.split(' ')[0]];
  }

  function iconForNpoDecision(attackRequired,targetConfirmed){
    return attackRequired&&!targetConfirmed?'crosshair':'command';
  }

  function renderCompletedNpoQuestions(history){
    return history.map(item=>`<div class="npo-question-complete npo-question-history">${npoIcon(iconForNpoQuestion(item))}<span>${escapeHtml(item.question||item.action)}</span><strong>${item.type==='selected'?'Selected':item.answer?'Yes':'No'}</strong></div>`).join('');
  }

  function renderActiveNpoQuestion(q){
    return `<section class="npo-question-active npo-question-card--active npo-active-question" aria-live="polite" aria-atomic="true" aria-labelledby="activeNpoQuestion" aria-describedby="activeNpoQuestionHelp">
      ${npoIcon(iconForNpoQuestion(q))}<h3 id="activeNpoQuestion">${escapeHtml(q.title)}</h3><p id="activeNpoQuestionHelp">${escapeHtml(q.help)}</p>
      <div class="ai-choice-grid"><button class="ai-choice no" data-answer="no"><strong>No</strong></button><button class="ai-choice yes" data-answer="yes"><strong>Yes</strong></button></div>
    </section>`;
  }

  function renderNpoActionProgress(activation=state.lastActivation){
    const actions=activation?.resolvedActions||[];
    if(!actions.length||activation.remainingAp<=0)return '';
    const names=actions.map(action=>escapeHtml(conciseNpoActionName(action))).join(', ');
    return `<p class="npo-action-progress" role="status" aria-live="polite">${activation.remainingAp} AP left (${names} complete)</p>`;
  }

  function titleCaseRuleId(ruleId){return String(ruleId).split('-').map(word=>word[0]?.toUpperCase()+word.slice(1)).join(' ');}

  function renderNpoActivationHeader(n){
    const definition=npoDefinition(n.type),modifiers=(state.npoRuleState.aplModifiers||[]).filter(item=>item.targetId===n.id);
    const pendingBreach=(state.npoRuleState.pendingMovementEffects||[]).some(item=>item.targetId===n.id&&item.ruleId==='molecular-breach');
    const loadout=definition.loadoutOptions?.find(option=>option.id===n.weaponId)?.name,effective=effectiveApl(n.id,definition.apl);
    return `<h2 id="activeNpoQuestionHeading">NPO Activation: ${escapeHtml(npoName(n))}</h2><div class="activation-profile-strip" role="status" aria-live="polite" aria-label="Activation profile"><span>Wounds: ${n.wounds}/${n.maxWounds}</span><span>APL ${definition.apl}${effective===definition.apl?'':` (${effective} AP this activation)`}</span><span>Order: ${escapeHtml(n.order)}</span>${loadout?`<span>${escapeHtml(loadout)}</span>`:''}${modifiers.map(item=>`<span>${item.amount>0?'+':''}${item.amount} AP this activation (${escapeHtml(titleCaseRuleId(item.ruleId))})</span>`).join('')}${pendingBreach?'<span>Next movement uses Molecular Breach</span>':''}</div>${renderNpoActionProgress()}`;
  }

  function renderNpoGuideFooter({backDisabled=false}={}){
    return `<div class="wizard-actions npo-guide-footer"><button class="btn ghost" id="aiBack" ${backDisabled?'disabled':''}>Back</button><button class="btn ghost" data-close>Close Guide</button></div>`;
  }

  function runNpoPrompt(n,index,answers,history){
    const q=npoActionQuestion(n,index);
    if(!q){renderNpoActivationEnd(n,'No useful actions remain.');return;}
    if(q.autoSelect){
      resolveNpo(n,{...answers,action:q.action},history);
      return;
    }
    const priorTop=$('.npo-question-active',modal)?.getBoundingClientRect().top;
    const wasOpen=modal.open;
    modalBody.innerHTML=`<div class="modal-inner">${renderNpoActivationHeader(n)}${state.lastActivation.autoTransitionAnnouncement?`<span class="visually-hidden" role="status" aria-live="polite">${escapeHtml(state.lastActivation.autoTransitionAnnouncement)}</span>`:''}<div class="ai-wizard">
      <div class="npo-question-flow">${renderCompletedNpoQuestions(history)}${renderActiveNpoQuestion(q)}</div>
      ${renderNpoGuideFooter({backDisabled:history.length===0})}
    </div></div>`;
    if(!modal.open)modal.showModal();
    modal.setAttribute('aria-labelledby','activeNpoQuestionHeading');
    modal.setAttribute('tabindex','-1');
    if(!wasOpen)focusInitialDialogControl(modal);
    if(state.lastActivation.autoTransitionAnnouncement){state.lastActivation.autoTransitionAnnouncement=null;save();requestAnimationFrame(()=>focusInitialDialogControl(modal));}
    $('[data-close]',modal).onclick=closeModal;
    if(priorTop!==undefined)requestAnimationFrame(()=>{const active=$('.npo-question-active',modal);if(!active)return;const delta=active.getBoundingClientRect().top-priorTop;modal.scrollBy({top:delta,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
    $$('[data-answer]',modal).forEach(btn=>btn.onclick=()=>{
      $$('[data-answer]',modal).forEach(choice=>choice.disabled=true);
      const answer=btn.dataset.answer==='yes';
      const nextAnswers={...answers,[q.key]:answer};
      const action=q.action;
      const contextBefore={...(state.lastActivation.currentContext||{})};
      const nextHistory=[...history,{index,answers,answer,action,type:q.type,question:q.title,contextBefore,movementIntentId:q.movementIntent?.id||null,concernsControlRange:q.concernsControlRange}];
      state.lastActivation.questionHistory=nextHistory;
      if(q.type==='applicability'){
        state.lastActivation.currentContext.inEnemyControlRange=answer;
        if(answer){save();runNpoPrompt(n,0,nextAnswers,nextHistory);}
        else{
          state.lastActivation.declinedActionIds=[...(state.lastActivation.declinedActionIds||[]),q.actionId];
          save();runNpoPrompt(n,0,nextAnswers,nextHistory);
        }
      }else if(answer){
        if(q.movementIntent&&attackAvailabilityForMovementIntent(state.lastActivation,q.movementIntent)===null){
          console.warn(`Blocked ${q.actionId} before checking current ${q.movementIntent.followUpActionId} availability.`);
          state.lastActivation.questionHistory=history;
          save();runNpoPrompt(n,0,answers,history);return;
        }
        if(q.actionId==='shoot')state.lastActivation.currentContext.hasValidShootTarget=true;
        if(q.actionId==='fight')state.lastActivation.currentContext.hasValidFightTarget=true;
        if(q.movementIntent){
          state.lastActivation.movementIntent={...q.movementIntent,actionId:q.actionId,decisionPass:state.lastActivation.decisionPass};
          state.lastActivation.pendingFollowUpAction=q.movementIntent.guaranteesFollowUp?{activationId:state.lastActivation.activationId,movementActionId:q.actionId,actionId:q.movementIntent.followUpActionId,decisionPass:state.lastActivation.decisionPass,movementCommitted:false}:null;
        }else if(q.actionId==='charge'&&state.lastActivation.remainingAp>=2&&!(state.lastActivation.completedActionIds||[]).includes('fight')&&!(state.lastActivation.completedActionIds||[]).includes('shoot')){
          state.lastActivation.movementIntent={id:'charge-enable-fight',actionId:'charge',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:true,decisionPass:state.lastActivation.decisionPass};
          state.lastActivation.pendingFollowUpAction={activationId:state.lastActivation.activationId,movementActionId:'charge',actionId:'fight',decisionPass:state.lastActivation.decisionPass,movementCommitted:false};
        }
        nextHistory.push({action,type:'selected',question:conciseNpoActionName({id:q.actionId,name:action})});
        resolveNpo(n,{...nextAnswers,action},nextHistory);
      }
      else{
        if(q.actionId==='shoot')state.lastActivation.currentContext.hasValidShootTarget=false;
        if(q.actionId==='fight')state.lastActivation.currentContext.hasValidFightTarget=false;
        if(q.movementIntent?.id&&['reposition','dash'].includes(q.actionId)){
          state.lastActivation.declinedMovementIntentIds=[...new Set([...(state.lastActivation.declinedMovementIntentIds||[]),q.movementIntent.id])];
          const nextIntent=npoMovementInquiry(n,action,q.actionId);
          if(!nextIntent||state.lastActivation.declinedMovementIntentIds.includes(nextIntent.id))state.lastActivation.declinedActionIds=[...(state.lastActivation.declinedActionIds||[]),q.actionId];
        }else state.lastActivation.declinedActionIds=[...(state.lastActivation.declinedActionIds||[]),npoActionId(action)];
        save();runNpoPrompt(n,0,nextAnswers,nextHistory);
      }
    });
    $('#aiBack')?.addEventListener('click',()=>{
      const previous=history[history.length-1];
      if(previous){
        state.lastActivation.declinedActionIds=(state.lastActivation.declinedActionIds||[]).filter(id=>id!==npoActionId(previous.action));
        state.lastActivation.declinedMovementIntentIds=(state.lastActivation.declinedMovementIntentIds||[]).filter(id=>id!==previous.movementIntentId);
        state.lastActivation.currentContext={...previous.contextBefore};
        state.lastActivation.questionHistory=history.slice(0,-1);save();runNpoPrompt(n,0,previous.answers,history.slice(0,-1));
      }
    });
  }

  function chooseNpoDecision(n,c){
    const action=c.action||'Pass';
    const attack=/^(Fight|Shoot)/.test(action);
    const target=action.startsWith('Fight')?['Most likely to be taken out','Most important to the mission','A Ready operative']:action.startsWith('Shoot')?['Most likely to be taken out','Most important to the mission','Clearest shot','Not in cover','Closest','A Ready operative']:[];
    const inquiry=NPO_ACTION_INQUIRIES[npoActionId(action)];
    const skippedFallBack=(state.lastActivation?.questionHistory||[]).some(item=>item.type==='applicability'&&item.action==='Fall Back'&&item.answer===false);
    const priorityReason=action==='Fall Back'?' This NPO is in a Player operative’s control range, so Fall Back is its first available action.':skippedFallBack?' Fall Back was not available, so use the next action in its priority list.':' This is the first action in its priority list that works now.';
    const movementInstruction=['reposition','dash'].includes(npoActionId(action))?npoMovementInstruction(n,action):null;
    const reason=c.action?`${movementInstruction||inquiry?.selectedInstruction||`Use ${action}.`}${priorityReason}`:'No useful actions remain.';
    return {action,target,stance:'Engage',threat:attack?1:0,reason,path:[action]};
  }

  function continueNpoActivation(){
    const activation=state.lastActivation,n=state.roster.find(item=>item.id===activation?.npoId);
    if(!activation||activation.committed)return;
    if(activation.pendingFollowUpAction?.movementCommitted){continueGuaranteedNpoFollowUp();return;}
    if(activation.awaitingActionResult&&ROUTINE_NPO_MOVEMENT_ACTIONS.has(activation.awaitingActionResult.id)){
      const record=activation.awaitingActionResult;
      activation.awaitingActionResult=null;
      activation.autoTransitionAnnouncement=`${conciseNpoActionName(record)} completed. ${activation.remainingAp} AP remaining. Continuing activation.`;
      save();
      if(activation.remainingAp<=0||activation.completed){completeNpoActivation();return;}
    }
    if(activation.completed)return;
    if(!n||n.wounds<=0||!n.deployed||!n.ready){completeNpoActivation();return;}
    if(activation.awaitingActionResult){renderNpoActionResult(n,activation.awaitingActionResult,Boolean(activation.awaitingActionResult.endsActivation));return;}
    if(activation.pendingAction&&normalizeUnknownAttackMovement(activation)){
      save();runNpoPrompt(n,0,{},activation.questionHistory||[]);return;
    }
    if(activation.pendingAction){resolveNpoAction(n,activation.pendingAction);return;}
    if(activation.remainingAp<=0){completeNpoActivation();return;}
    const available=recommendedNpoActions(n,activation.currentContext||{}).filter(name=>!(activation.declinedActionIds||[]).includes(npoActionId(name)));
    if(!available.length){renderNpoActivationEnd(n,'No useful actions remain.');return;}
    runNpoPrompt(n,0,{},activation.questionHistory||[]);
  }

  function normalizeUnknownAttackMovement(activation){
    if(!npoActionChangesContext(activation.pendingAction?.id))return false;
    if(attackAvailabilityForMovementIntent(activation,activation.movementIntent)!==null)return false;
    console.warn(`Restored ${activation.pendingAction.id} was blocked before its current-position attack check.`);
    const history=activation.questionHistory||[];
    let movementIndex=-1;
    for(let index=history.length-1;index>=0;index--){
      if(history[index].movementIntentId===activation.movementIntent?.id){movementIndex=index;break;}
    }
    activation.questionHistory=movementIndex<0?history:history.slice(0,movementIndex);
    activation.pendingAction=null;activation.pendingFollowUpAction=null;activation.movementIntent=null;
    return true;
  }

  function continueGuaranteedNpoFollowUp(){
    const activation=state.lastActivation,followUp=activation?.pendingFollowUpAction;
    const n=state.roster.find(item=>item.id===activation?.npoId);
    if(!activation||!followUp||followUp.activationId!==activation.activationId||followUp.movementCommitted!==true||!n)return false;
    const actionId=followUp.actionId,alreadyCompleted=(activation.completedActionIds||[]).includes(actionId);
    const actionName=recommendedNpoActions(n,activation.currentContext||{}).find(name=>npoActionId(name)===actionId);
    const apCost=npoActionCost(n,actionId);
    if(alreadyCompleted||!actionName||apCost===null||apCost>activation.remainingAp){
      activation.pendingFollowUpAction=null;activation.movementIntent=null;
      activation.autoTransitionAnnouncement=`The planned ${actionId==='fight'?'Fight':'Shoot'} is no longer available. Reevaluate the NPO’s remaining actions.`;
      save();showToast(activation.autoTransitionAnnouncement);runNpoPrompt(n,0,{},activation.questionHistory||[]);return false;
    }
    if(actionId==='shoot')activation.currentContext.hasValidShootTarget=true;
    if(actionId==='fight')activation.currentContext.hasValidFightTarget=true;
    activation.pendingAction={id:actionId,name:actionName,apCost,decisionPass:activation.decisionPass};
    activation.pendingFollowUpAction=null;activation.movementIntent=null;
    activation.answers={action:actionName};
    activation.questionHistory=[...(activation.questionHistory||[]),{action:actionName,type:'selected',question:conciseNpoActionName({id:actionId,name:actionName})}];
    save();resolveNpoAction(n,activation.pendingAction);return true;
  }

  function canCommitNpoAction(actionId,apCost){
    const activation=state.lastActivation,n=state.roster.find(item=>item.id===activation?.npoId),pending=activation?.pendingAction;
    return Boolean(activation&&n&&!activation.committed&&!activation.completed&&pending?.id===actionId
      &&pending.decisionPass===activation.decisionPass&&Number.isFinite(apCost)&&apCost>=0&&apCost<=activation.remainingAp
      &&!(activation.completedActionIds||[]).includes(actionId));
  }

  function scheduleNpoActionTransition(activation,npoId,transitionMode){
    requestAnimationFrame(()=>{
      const current=state.lastActivation;
      if(current!==activation||current.activationId!==activation.activationId||current.npoId!==npoId||state.activeNpoId!==npoId||current.committed)return;
      if(transitionMode===NPO_ACTION_TRANSITIONS.COMPLETE_ACTIVATION||current.remainingAp<=0||current.completed){completeNpoActivation();return;}
      continueNpoActivation();
    });
  }

  function commitNpoAction({actionId,actionName,apCost,result=null,changesPosition=false,endsActivation=false,attackSummary=null,attackSummaries=null,transitionMode=NPO_ACTION_TRANSITIONS.ACKNOWLEDGE}){
    const activation=state.lastActivation,n=state.roster.find(item=>item.id===activation?.npoId);
    if(!canCommitNpoAction(actionId,apCost))return false;
    const before=activation.remainingAp;
    activation.remainingAp=Math.max(0,before-apCost);
    activation.completedActionIds=[...(activation.completedActionIds||[]),actionId];
    activation.actionSequence=(activation.actionSequence||0)+1;
    const allAttackSummaries=Array.isArray(attackSummaries)?attackSummaries:attackSummary?[attackSummary]:[];
    const record={sequence:activation.actionSequence,id:actionId,name:actionName,apCost,apBefore:before,apRemaining:activation.remainingAp,result,
      ...(allAttackSummaries.length?{attackSummary:attackSummary||allAttackSummaries.at(-1),attackSummaries:allAttackSummaries}:{})};
    activation.resolvedActions=[...(activation.resolvedActions||[]),record];
    activation.attackPerformed=activation.attackPerformed||actionId==='shoot'||actionId==='fight';
    activation.fightPerformed=activation.fightPerformed||actionId==='fight';
    activation.pendingAction=null;activation.combatDraft=null;activation.attackResolved=false;activation.attackRequired=false;
    activation.specialActionResolved=false;activation.specialActionResult=null;
    activation.decisionPass++;
    activation.declinedActionIds=[];
    activation.declinedMovementIntentIds=[];
    activation.questionHistory=[];
    if(changesPosition)activation.currentContext={inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null};
    if(changesPosition&&activation.pendingFollowUpAction?.movementActionId===actionId)activation.pendingFollowUpAction={...activation.pendingFollowUpAction,movementCommitted:true,decisionPass:activation.decisionPass};
    else if(changesPosition)activation.movementIntent=null;
    state.npoAttackTargetId=null;state.npoAttackSummary=null;
    const journalAction=['reposition','dash'].includes(actionId)?npoMovementInstruction(n,actionName):actionName;
    log(`${npoName(n)} completed ${journalAction}. ${activation.remainingAp} AP remaining.`);
    if(transitionMode===NPO_ACTION_TRANSITIONS.ACKNOWLEDGE){
      activation.awaitingActionResult={...record,endsActivation};
      if(endsActivation)activation.completed=true;
      save();renderNpoActionResult(n,record,endsActivation);
      return true;
    }
    activation.awaitingActionResult=null;
    activation.autoTransitionAnnouncement=`${conciseNpoActionName(record)} completed. ${activation.remainingAp} AP remaining. Continuing activation.`;
    if(endsActivation)activation.completed=true;
    save();
    scheduleNpoActionTransition(activation,n.id,transitionMode);
    return true;
  }

  function renderNpoActionResult(n,record,endsActivation=false){
    const activation=state.lastActivation,canContinue=!endsActivation&&activation.remainingAp>0;
    const history=activation.resolvedActions.map(action=>escapeHtml(conciseNpoActionName(action))).join(', ');
    modalBody.innerHTML=`<div class="modal-inner ai-result"><div class="ai-result-title"><div><h2>${escapeHtml(npoName(n))}</h2><p>${escapeHtml(n.type)}</p></div></div><div class="summary-box"><strong>${escapeHtml(conciseNpoActionName(record))} completed</strong><p>AP: ${record.apBefore} → ${record.apRemaining} · ${record.apCost} AP spent</p>${record.result?`<p>${escapeHtml(typeof record.result==='string'?record.result:record.result.summary||'Action resolved.')}</p>`:''}<p><strong>Completed actions:</strong> ${history}</p></div><div class="wizard-actions"><button class="btn primary" id="continueNpoActivation">${canContinue?'Continue Activation':'Complete Activation'}</button></div></div>`;
    if(!modal.open)modal.showModal();
    focusInitialDialogControl(modal);
    $('#continueNpoActivation').onclick=()=>{const button=$('#continueNpoActivation');button.disabled=true;activation.awaitingActionResult=null;save();if(canContinue)continueNpoActivation();else completeNpoActivation();};
  }

  function renderNpoActivationEnd(n,message){
    const remaining=state.lastActivation.remainingAp;
    modalBody.innerHTML=`<div class="modal-inner ai-result"><h2>${escapeHtml(npoName(n))}</h2><div class="summary-box"><strong>${escapeHtml(message)}</strong>${remaining?`<p>${remaining} AP remain${remaining===1?'s':''} unused.</p>`:''}</div><div class="wizard-actions"><button class="btn primary" id="finishNpoActivation">Complete Activation</button></div></div>`;
    if(!modal.open)modal.showModal();
    focusInitialDialogControl(modal);
    $('#finishNpoActivation').onclick=()=>{const button=$('#finishNpoActivation');button.disabled=true;completeNpoActivation();};
  }

  function npoSpecialAction(n,actionName){
    const id=npoActionId(actionName);
    return (npoDefinition(n.type)?.actions||[]).find(action=>action.id===id)||null;
  }
  function npoSpecialActionDescription(action){
    if(action.id==='geomantic-disturbance')return `<ol><li>Choose a terrain point the Geomancer can see within 8 inches.</li><li>Select every operative within 2 inches of that point.</li><li>Roll 2D6 separately for each. If the total is higher than its remaining wounds, deal damage equal to the difference.</li></ol><p>Cannot be used while the Geomancer has a Conceal order or is in enemy control range.</p>`;
    const paragraphs={
      'canoptek-control':['Choose a visible friendly Canoptek within 6 inches. It immediately performs one free 1 AP action. Any movement from that action is limited to 2 inches.','Cannot be used while the Geomancer is in enemy control range or during a counteraction.'],
      'molecular-breach':['Choose a visible friendly Canoptek Circle NPO within 6 inches. During its next movement action, remove it and set it up instead of moving normally.','Use its Move distance, or 3 inches for Dash. In close quarters it can pass through Walls. Only Charge may end in enemy control range.'],
      overcharge:['Choose another visible friendly Canoptek within 3 inches. It gets 1 extra AP in its next activation (+1 APL).','Cannot be used while the Accelerator is in enemy control range.'],
      'cranial-overload':['Choose a visible Player operative within 3 inches. It gets 1 fewer AP in its next activation, to a minimum of 1 (-1 APL).','Cannot be used while the Accelerator is in enemy control range.'],
      'nanoscarab-beam':['Choose a visible wounded Canoptek Circle NPO within 6 inches. Roll 3D3 and restore that many wounds, up to its maximum.','It cannot target an incapacitated NPO or one saved by Reanimate this turning point.']
    };
    return (paragraphs[action.id]||[action.description]).map(text=>`<p>${escapeHtml(text)}</p>`).join('');
  }
  function resolveNpoSpecialAction(n,decision,answers,questionHistory){
    const action=npoSpecialAction(n,decision.action);
    if(!action){completeNpoActivation();return;}
    const friendlies=sortedNposForDisplay(activeNpos().filter(target=>(action.id==='nanoscarab-beam'||target.id!==n.id)
      &&(!action.target?.keywordsAll||action.target.keywordsAll.every(keyword=>npoDefinition(target.type)?.keywords.includes(keyword)))
      &&(action.id!=='nanoscarab-beam'||target.wounds<target.maxWounds&&!state.npoRuleState.reanimatedTargetIds.includes(target.id))));
    const friendlyOptions=friendlies.map(target=>`<option value="${escapeHtml(target.id)}">${escapeHtml(npoName(target))}</option>`).join('');
    const enemyOptions=remainingPlayerOperatives().map(id=>`<option value="${escapeHtml(id)}">${escapeHtml(playerTargetLabel(id))}</option>`).join('');
    const targetOptions=action.target?.side==='enemy'?enemyOptions:friendlyOptions;
    const targetLabel=action.target?.side==='enemy'?'Player operative':'Friendly NPO';
    if(action.id==='geomantic-disturbance'){
      const affected=[...sortedNposForDisplay(activeNpos()),...inPlayLivingPlayerOperativeIds().map(id=>({id:`player:${id}`,label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id)}))];
      showModal(action.name,`<p>Choose a visible terrain point within 8 inches, then select every operative within 2 inches of it.</p><div class="checklist">${affected.map(target=>`<label class="check-row"><input type="checkbox" data-disturbance-target="${escapeHtml(target.id)}"${target.ariaLabel?` aria-label="${escapeHtml(target.ariaLabel)}"`:''}><span>${escapeHtml(target.label||npoName(target))}</span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="cancelSpecialAction">Cancel</button><button class="btn primary" id="confirmSpecialAction">Roll Damage</button></div>`);
      $('#cancelSpecialAction').onclick=()=>resolveNpoAction(n,state.lastActivation.pendingAction);
      $('#confirmSpecialAction').onclick=()=>{
        const button=$('#confirmSpecialAction');
        if(!canCommitNpoAction(action.id,npoActionCost(n,action.id)))return;
        button.disabled=true;
        const selected=$$('[data-disturbance-target]:checked').map(input=>input.dataset.disturbanceTarget);
        const targets=selected.map(id=>id.startsWith('player:')?livePlayerOperative(id.slice(7)):state.roster.find(item=>item.id===id)).filter(Boolean);
        const results=resolveGeomanticDisturbance(targets);
        results.forEach(result=>{
          const targetId=selected[results.indexOf(result)],target=targets[results.indexOf(result)],before=target.wounds;
          if(targetId.startsWith('player:'))state.playerWounds[target.id]=Math.max(0,before-result.damage);
          else {target.wounds=Math.max(0,before-result.damage);if(!target.wounds){target.ready=false;target.deployed=false;target.battlefieldState='out-of-action';}}
          log(`${npoName(n)} used Geomantic Disturbance on ${targetId.startsWith('player:')?playerName(target.id):npoName(target)}: ${result.dice.join('+')}=${result.total}; ${result.damage} damage.`);
        });
        finishNpoSpecialAction(n,action,{targets:selected,results},decision,answers,questionHistory);
      };
      return;
    }
    const confirmation=action.id==='molecular-breach'?'I confirmed that this NPO can be placed as instructed.':'I confirmed that this target is visible and within range.';
    const buttonLabels={'canoptek-control':'Use Canoptek Control','molecular-breach':'Apply Molecular Breach',overcharge:'Use Overcharge','cranial-overload':'Use Cranial Overload','nanoscarab-beam':'Roll Healing'};
    showModal(action.name,`${npoSpecialActionDescription(action)}<div class="field"><label for="specialActionTarget">${targetLabel}</label><select id="specialActionTarget"><option value="">Select operative…</option>${targetOptions}</select></div>${action.id==='canoptek-control'?'<div class="field"><label for="freeActionChoice">Choose the free 1 AP action</label><select id="freeActionChoice"><option>Reposition</option><option>Dash</option><option>Charge</option><option>Shoot</option><option>Fight</option><option>Mission action</option></select></div>':''}<label class="check-row" for="specialRangeConfirmed"><input id="specialRangeConfirmed" type="checkbox"><span>${escapeHtml(confirmation)}</span></label><div class="wizard-actions"><button class="btn ghost" id="cancelSpecialAction">Cancel</button><button class="btn primary" id="confirmSpecialAction" disabled>${escapeHtml(buttonLabels[action.id]||`Use ${action.name}`)}</button></div>`);
    const update=()=>{$('#confirmSpecialAction').disabled=!$('#specialActionTarget').value||!$('#specialRangeConfirmed').checked;};
    $('#specialActionTarget').onchange=update;$('#specialRangeConfirmed').onchange=update;
    $('#cancelSpecialAction').onclick=()=>resolveNpoAction(n,state.lastActivation.pendingAction);
    $('#confirmSpecialAction').onclick=()=>{
      const button=$('#confirmSpecialAction');
      if(!canCommitNpoAction(action.id,npoActionCost(n,action.id)))return;
      button.disabled=true;
      const targetId=$('#specialActionTarget').value;
      const target=action.target?.side==='enemy'?{id:targetId,name:playerName(targetId),apl:playerDefinition(targetId)?.apl||2}:state.roster.find(item=>item.id===targetId);
      let result={targetId};
      if(action.id==='canoptek-control'){
        const freeAction=$('#freeActionChoice').value;
        result={...result,freeAction,maxMove:2,preservedReady:target.ready};
        if(['Reposition','Dash','Charge'].includes(freeAction))result.molecularBreach=consumeMolecularBreach(target.id,freeAction);
      }
      if(action.id==='molecular-breach')result.applied=applyMolecularBreach(n.id,target.id);
      if(action.id==='overcharge')result.applied=applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'overcharge',amount:1});
      if(action.id==='cranial-overload')result.applied=applyTemporaryAplModifier({sourceId:n.id,targetId:target.id,ruleId:'cranial-overload',amount:-1});
      if(action.id==='nanoscarab-beam')result=useNanoscarabBeam(target);
      if(!result){button.disabled=false;showToast('That action is no longer legal.');return;}
      const targetName=action.target?.side==='enemy'?playerName(targetId):npoName(target);
      log(`${npoName(n)} used ${action.name} on ${targetName}${action.id==='canoptek-control'?` for a free ${result.freeAction} (maximum 2 inches of movement)`:''}.`);
      finishNpoSpecialAction(n,action,result,decision,answers,questionHistory);
    };
  }
  function finishNpoSpecialAction(n,action,result,decision,answers,questionHistory){
    if(action.oncePerTurningPoint)state.npoRuleState.oncePerTurningPoint[action.id]=state.turningPoint;
    commitNpoAction({actionId:action.id,actionName:action.name,apCost:npoActionCost(n,action.id),result,changesPosition:Boolean(action.changesPosition||action.materiallyChangesContext)});
  }

  function resolveNpo(n,c,questionHistory=[]){
    state.npoAttackTargetId=null;
    const decision=chooseNpoDecision(n,c);
    const id=npoActionId(decision.action),cost=npoActionCost(n,id);
    if(cost===null||cost>state.lastActivation.remainingAp){showToast('That action is no longer legal.');continueNpoActivation();return;}
    state.lastActivation={...state.lastActivation,npoId:n.id,name:npoName(n),...decision,answers:c,questionHistory,pendingAction:{id,name:decision.action,apCost:cost,decisionPass:state.lastActivation.decisionPass},committed:false};
    save();resolveNpoAction(n,state.lastActivation.pendingAction);
  }

  function backFromNpoMovementConfirmation(n){
    const activation=state.lastActivation,history=activation?.questionHistory||[];
    const selected=history[history.length-1],previous=history[history.length-2];
    if(!activation?.pendingAction||selected?.type!=='selected'||!previous||previous.answer!==true)return;
    const earlierHistory=history.slice(0,-2);
    activation.pendingAction=null;
    if(!previous.movementIntentId||activation.movementIntent?.id===previous.movementIntentId)activation.movementIntent=null;
    if(activation.pendingFollowUpAction?.movementActionId===npoActionId(previous.action))activation.pendingFollowUpAction=null;
    activation.currentContext={...previous.contextBefore};
    activation.answers={...previous.answers};
    activation.questionHistory=earlierHistory;
    save();
    runNpoPrompt(n,previous.index,previous.answers,earlierHistory);
    requestAnimationFrame(()=>focusInitialDialogControl(modal));
  }

  function backFromNpoAttackSelection(n){
    const activation=state.lastActivation,history=activation?.questionHistory||[];
    const selected=history[history.length-1],previous=history[history.length-2];
    if(!activation?.pendingAction||selected?.type!=='selected'||!previous||previous.answer!==true)return;
    activation.pendingAction=null;
    activation.currentContext={...previous.contextBefore};
    activation.answers={...previous.answers};
    activation.questionHistory=history.slice(0,-2);
    state.npoAttackTargetId=null;state.npoAttackSummary=null;
    save();runNpoPrompt(n,0,previous.answers,activation.questionHistory);
    requestAnimationFrame(()=>focusInitialDialogControl(modal));
  }

  function renderNpoMovementConfirmation(n,pendingAction,decision){
    const displayAction=conciseNpoActionName(pendingAction),headingId='activeNpoMovementHeading',instructionId='activeNpoMovementInstruction';
    const icon=iconForNpoQuestion({action:displayAction,movementIntent:state.lastActivation?.movementIntent});
    modalBody.innerHTML=`<div class="modal-inner">${renderNpoActivationHeader(n)}<div class="ai-wizard"><div class="npo-question-flow"><section class="npo-question-active npo-question-card--active npo-movement-confirmation" aria-labelledby="${headingId}" aria-describedby="${instructionId}">${npoIcon(icon)}<h3 id="${headingId}">${escapeHtml(displayAction)}</h3><p id="${instructionId}">${escapeHtml(decision.reason)}</p><p class="npo-movement-cost">Costs ${pendingAction.apCost} AP (${state.lastActivation.remainingAp} AP to ${state.lastActivation.remainingAp-pendingAction.apCost} AP)</p><div class="ai-choice-grid"><button class="ai-choice yes npo-movement-confirm" id="confirmNpoMovement"><strong>Confirm ${escapeHtml(displayAction)} Complete</strong></button></div></section></div>${renderNpoGuideFooter()}</div></div>`;
    if(!modal.open)modal.showModal();
    modal.setAttribute('aria-labelledby','activeNpoQuestionHeading');
    modal.setAttribute('tabindex','-1');
    $('[data-close]',modal).onclick=closeModal;
    $('#aiBack').onclick=()=>backFromNpoMovementConfirmation(n);
    requestAnimationFrame(()=>focusInitialDialogControl(modal));
  }

  function resolveNpoAction(n,pendingAction){
    if(!pendingAction||state.lastActivation?.pendingAction?.id!==pendingAction.id)return;
    if(normalizeUnknownAttackMovement(state.lastActivation)){
      save();runNpoPrompt(n,0,{},state.lastActivation.questionHistory||[]);return;
    }
    const decision=chooseNpoDecision(n,{action:pendingAction.name});
    if(npoSpecialAction(n,pendingAction.name)){resolveNpoSpecialAction(n,decision,state.lastActivation.answers||{},state.lastActivation.questionHistory||[]);return;}
    if(npoActionChangesContext(pendingAction.id)){
      renderNpoMovementConfirmation(n,pendingAction,decision);
      $('#confirmNpoMovement').onclick=()=>{const button=$('#confirmNpoMovement');if(!canCommitNpoAction(pendingAction.id,pendingAction.apCost))return;button.disabled=true;const effect=consumeMolecularBreach(n.id,pendingAction.id==='fall-back'?'Fall Back':pendingAction.name.split(' ')[0]);const finalApDash=pendingAction.id==='dash'&&state.lastActivation.remainingAp===pendingAction.apCost&&!state.lastActivation.pendingFollowUpAction;commitNpoAction({actionId:pendingAction.id,actionName:pendingAction.name,apCost:pendingAction.apCost,result:effect||decision.reason,changesPosition:true,endsActivation:finalApDash,transitionMode:finalApDash?NPO_ACTION_TRANSITIONS.COMPLETE_ACTIVATION:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE});};
      return;
    }
    const activation=state.lastActivation;
    renderNpoDecisionResult(n,decision,activation.dice||[],activation.answers||{},Boolean(activation.attackResolved),false,/^(shoot|fight)$/.test(pendingAction.id),Boolean(activation.targetConfirmed),activation.questionHistory||[]);
  }

  function initiativeSummary(dice){
    const crits=dice.filter(d=>d.kind==='crit').length;
    const hits=dice.filter(d=>d.kind==='hit').length;
    const misses=dice.filter(d=>d.kind==='miss').length;
    if(crits===0&&hits===0)return 'Attack missed. No saves or damage required.';
    return `${crits} critical · ${hits} normal · ${misses} miss`;
  }

  function updateNpoTargetConfirmationAvailability(){
    const targetId=String($('#npoPriorityTarget')?.tagName==='SELECT'?$('#npoPriorityTarget').value:'');
    const button=$('#confirmNpoTarget');
    if(button)button.disabled=!eligibleNpoAttackTargets().includes(targetId||String(state.npoAttackTargetId||''));
  }

  function showNpoTargetRecovery(n,decision){
    const activation=state.lastActivation;
    console.error('[NPO Target] Target confirmation failed because the pending attack was not preserved.',{
      npoId:n.id,pendingAction:activation?.pendingAction,targetId:state.npoAttackTargetId
    });
    modalBody.innerHTML=`<div class="modal-inner"><h2>Target could not be confirmed</h2><div class="summary-box">The attack state was not preserved. No AP, dice, or damage were committed.</div><div class="wizard-actions"><button class="btn primary" id="recoverNpoActivation">Return to NPO Activation</button></div></div>`;
    if(!modal.open)modal.showModal();
    $('#recoverNpoActivation').onclick=()=>{
      const current=state.lastActivation;
      state.npoAttackTargetId=null;state.npoAttackSummary=null;state.weaponRuleResolution=null;
      state.lastActivation={...current,pendingAction:null,targetConfirmed:false,attackRequired:false,attackResolved:false,combatDraft:null};
      save();runNpoPrompt(n,0,current?.answers||{},current?.questionHistory||[]);
    };
  }

  function confirmNpoAttackTarget(n,decision){
    const targetControl=$('#npoPriorityTarget');
    const selectedTargetId=String((targetControl?.tagName==='SELECT'?targetControl.value:'')||state.npoAttackTargetId||'');
    const eligibleTargetIds=eligibleNpoAttackTargets();
    if(!selectedTargetId||!eligibleTargetIds.includes(selectedTargetId)){
      state.npoAttackTargetId=null;
      state.npoAttackSummary=null;
      save();
      renderNpoDecisionResult(n,decision,[],state.lastActivation?.answers||{},false,false,true,false,state.lastActivation?.questionHistory||[]);
      showToast('That Player operative is no longer an eligible target. Select another target.');
      return false;
    }
    const activation=state.lastActivation,pendingAction=activation?.pendingAction;
    if(!pendingAction||!['shoot','fight'].includes(pendingAction.id)){
      showNpoTargetRecovery(n,decision);
      return false;
    }
    state.npoAttackTargetId=selectedTargetId;
    state.npoAttackSummary=null;
    state.lastActivation={...activation,targetConfirmed:true,attackRequired:true,attackResolved:false};
    const history=state.activationHistory.find(item=>item.side==='npo'&&item.label===npoName(n)&&!item.target);
    if(history)history.target=playerName(selectedTargetId);
    log(`${npoName(n)} confirmed ${playerName(selectedTargetId)} as the attack target.`);
    save();
    openNpoCombat(n,decision,[],state.lastActivation.answers||{});
    return true;
  }

  function openNpoCombat(n,decision,resolvedDice=[],answers=state.lastActivation?.answers||{},animate=false){
    showNpoAttackWizard(n,resolvedDice,(summary,attackSummaries=[summary])=>{
      const pending=state.lastActivation?.pendingAction;
      if(pending)commitNpoAction({actionId:pending.id,actionName:pending.name,apCost:pending.apCost,
        result:attackSummaries.map(item=>`${item.targetName} ${item.skipped?'skipped':`${item.damage} damage`}`).join(', '),
        attackSummary:summary,attackSummaries,transitionMode:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE});
    },()=>{
      save();
      renderNpoDecisionResult(n,decision,resolvedDice,answers,false,false,true,false);
    },animate);
  }

  function renderNpoDecisionResult(n,decision,dice,answers,attackResolved,animateDice=true,attackRequired=(decision.action.includes('Fight')||decision.action.includes('Shoot')),targetConfirmed=dice.length>0,questionHistory=state.lastActivation?.questionHistory||[]){
    const eligibleTargetIds=eligibleNpoAttackTargets();
    if(state.npoAttackTargetId&&!eligibleTargetIds.includes(state.npoAttackTargetId)){
      state.npoAttackTargetId=null;
      state.npoAttackSummary=null;
      dice=[];
      attackResolved=false;
      targetConfirmed=false;
    }
    if(!targetConfirmed&&eligibleTargetIds.length===1)state.npoAttackTargetId=eligibleTargetIds[0];
    state.lastActivation={...state.lastActivation,name:npoName(n),...decision,dice,answers,questionHistory,attackResolved,attackRequired,targetConfirmed};save();
    if(attackRequired&&targetConfirmed&&!attackResolved){
      openNpoCombat(n,decision,dice,answers);
      return;
    }
    const targetOptions=eligibleTargetIds.map(id=>`<option value="${escapeHtml(id)}" ${state.npoAttackTargetId===id?'selected':''}>${escapeHtml(playerTargetLabel(id))}</option>`).join('');
    const targetName=state.npoAttackTargetId?playerTargetLabel(state.npoAttackTargetId):'';
    const targetField=targetConfirmed||eligibleTargetIds.length===1
      ? `<input id="npoPriorityTarget" value="${escapeHtml(targetName)}" readonly>`
      : `<select id="npoPriorityTarget" ${attackResolved?'disabled':''}><option value="" ${state.npoAttackTargetId?'':'selected'}>Select the first operative that matches the priority above.</option>${targetOptions}</select>`;
    const targetPriority=decision.target.length?`<p>Choose the target in this order:</p><ol>${decision.target.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ol><p>Randomize only if still tied.</p>`:'';
    const attackSummary=attackResolved&&state.npoAttackSummary?{
      ...state.npoAttackSummary,
      side:'player',
      attackType:state.npoAttackSummary.attackType||(decision.action.includes('Fight')?'melee':'shoot')
    }:null;
    const eliminationAction=newlyEliminated(attackSummary)?` Eliminated ${escapeHtml(attackSummary.targetName)}.`:'';
    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <div class="ai-result-title"><div><h2>${escapeHtml(npoName(n))}</h2><p>${escapeHtml(n.type)}</p></div></div>
      ${attackRequired&&questionHistory.length?`<div class="npo-question-flow">${renderCompletedNpoQuestions(questionHistory.filter(item=>item.type!=='selected'))}</div>`:''}
      <div class="npo-result-card">${npoIcon(iconForNpoDecision(attackRequired,targetConfirmed))}<div><small>NEXT ACTION</small><strong>${escapeHtml(decision.action)}</strong><p>${escapeHtml(decision.reason)}</p><div class="npo-target-priority"><small>TARGET PRIORITY</small>${targetPriority}${attackRequired?`<div class="field target-selection"><label for="npoPriorityTarget">Select Target</label>${targetField}</div>`:''}</div></div></div>
      ${attackRequired&&!targetConfirmed&&eligibleTargetIds.length>1?`<button class="btn secondary big-action" id="confirmNpoTarget" ${state.npoAttackTargetId?'':'disabled'}>Confirm Target</button>`:''}
      ${attackRequired&&!targetConfirmed&&eligibleTargetIds.length===1?`<button class="btn secondary big-action" id="resolveNpoTarget">Resolve Combat</button>`:''}
      ${attackSummary?`${renderEliminationSummary(attackSummary)}<section class="card npo-attack-summary">
        <p class="eyebrow">NPO ATTACK SUMMARY</p>
        ${renderAttackSummary(attackSummary)}
        <div class="combat-stage"><small>PLAYER SAVE ROLL</small><div class="dice-row settled">${attackSummary.saveDice.length?attackSummary.saveDice.map(dieHtml).join(''):'<span class="muted">No save dice rolled</span>'}</div></div>
        <div class="damage-summary">
          <div><small>Unsaved normal hits</small><strong>${attackSummary.normalRemaining}</strong></div>
          <div><small>Unsaved critical hits</small><strong>${attackSummary.critRemaining}</strong></div>
        </div>
      </section><div class="summary-box"><strong>Actions:</strong> ${attackSummary.attackType==='shoot'?'Shooting':'Melee'} attack resolved.${eliminationAction}</div>`:''}
      ${!attackRequired?`<div class="wizard-actions"><button class="btn primary" id="completeNpo">Confirm ${escapeHtml(decision.action)} Complete</button></div>`:''}
      ${attackRequired&&!targetConfirmed?renderNpoGuideFooter():''}
    </div>`;
    if(!modal.open)modal.showModal();
    focusInitialDialogControl(modal);
    $('[data-close]',modal)?.addEventListener('click',closeModal);
    $('#aiBack')?.addEventListener('click',()=>backFromNpoAttackSelection(n));
    $('#npoPriorityTarget')?.addEventListener('change',event=>{state.npoAttackTargetId=event.currentTarget.value||null;save();updateNpoTargetConfirmationAvailability();});
    const resolveTargetButton=$('#resolveNpoTarget');
    if(resolveTargetButton)resolveTargetButton.onclick=()=>{
      if(resolveTargetButton.disabled)return;
      resolveTargetButton.disabled=true;
      const confirmed=confirmNpoAttackTarget(n,decision);
      if(!confirmed&&resolveTargetButton.isConnected)resolveTargetButton.disabled=false;
    };
    const confirmTargetButton=$('#confirmNpoTarget');
    if(confirmTargetButton)confirmTargetButton.onclick=()=>{
      if(confirmTargetButton.disabled)return;
      confirmTargetButton.disabled=true;
      const confirmed=confirmNpoAttackTarget(n,decision);
      if(!confirmed&&confirmTargetButton.isConnected)confirmTargetButton.disabled=false;
    };
    updateNpoTargetConfirmationAvailability();

    $('#completeNpo')?.addEventListener('click',()=>{
      const pending=state.lastActivation?.pendingAction;
      if(pending)commitNpoAction({actionId:pending.id,actionName:pending.name,apCost:pending.apCost,result:decision.reason});
    });
  }

  async function completeNpoActivation(){
    if(state.lastActivation?.committed)return;
    const n=state.roster.find(item=>item.id===state.lastActivation?.npoId);
    if(!n)return;
    state.lastActivation.committed=true;state.lastActivation.completed=true;
    if(state.lastActivation.attackPerformed)setThreat(1,`${npoName(n)} Shoot or Fight`);
    const activationId=state.lastActivation.activationId||missionActivationId('npo',n.id);
    n.ready=false;state.npoActivated++;state.activationNumber++;
    const resolvedActions=[...(state.lastActivation.resolvedActions||[])],attackSummaries=resolvedActions.flatMap(action=>action.attackSummaries||action.attackSummary?[...(action.attackSummaries||[]),...(!action.attackSummaries&&action.attackSummary?[action.attackSummary]:[])]:[]);
    const actionNames=resolvedActions.map(conciseNpoActionName);
    state.activationHistory.unshift({side:'npo',label:npoName(n),action:actionNames.join(', ')||'Pass',actions:resolvedActions,attackSummary:attackSummaries.at(-1)||null,attackSummaries});
    expireActivationEffects(n.id);
    state.activeNpoId=null;advanceAfterActivation('npo');
    log(`${npoName(n)} completed its activation: ${actionNames.join(', ')||'Pass'}.`);
    state.npoAttackTargetId=null;
    state.npoAttackSummary=null;
    save();
    closeModal();
    await executeMissionLifecycleHook('onNpoActivationCompleted',{activationId,operativeId:n.id});
    const gameEnded=checkGameEnd();
    if(!gameEnded)render();
  }


  function applyNpoAttackDamage(n,target,summary){
    if(summary.side==='npo'){
      const friendly=state.roster.find(operative=>operative.id===target.id);
      if(!friendly)return;
      friendly.wounds=Math.max(0,summary.after);
      if(friendly.wounds<=0){friendly.ready=false;friendly.deployed=false;friendly.battlefieldState='out-of-action';}
      log(`${npoName(n)} dealt ${summary.damage} Blast damage to ${npoName(friendly)} (${summary.before} → ${summary.after} wounds).`);
      return;
    }
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
    const normalAfter=summary.dimensionalBanishmentRemainingWounds??summary.after;
    log(`${npoName(n)} dealt ${summary.damage} damage to ${playerName(target.id)} (${summary.before} → ${normalAfter} wounds).`);
    if(summary.dimensionalBanishmentTriggered){
      const outcome=summary.dimensionalBanishmentIncapacitated
        ? `${summary.dimensionalBanishmentRoll} exceeded ${normalAfter} remaining wounds, so ${playerName(target.id)} was incapacitated.`
        : `${playerName(target.id)} survived with ${normalAfter} wounds.`;
      log(`${npoName(n)} rolled ${summary.dimensionalBanishmentRoll} for Dimensional Banishment against ${playerName(target.id)}. ${outcome}`);
    }
  }

  function showNpoAttackWizard(n,attackDice,onDone,onCancel,animateCombat=false,resumeGuided=false){
    const target=selectedNpoAttackTarget();
    if(!target&&state.weaponRuleResolution?.currentTargetId){
      const attackType=state.lastActivation?.action?.includes('Fight')?'melee':'shoot';
      const locked=lockedMultiTargetProfile(state.weaponRuleResolution,n);
      const targetId=state.weaponRuleResolution.currentTargetId;
      console.error('[Combat] Multi-target NPO attack target unavailable.',{targetId,sequence:state.weaponRuleResolution});
      const skipped={targetId,targetName:targetId,skipped:true,skipReason:'Target is no longer on the battlefield.'};
      state.weaponRuleResolution=advanceMultiTargetAttackSequence(state.weaponRuleResolution,targetId,skipped);
      if(state.weaponRuleResolution.currentTargetId){state.npoAttackTargetId=state.weaponRuleResolution.currentTargetId;save();showNpoAttackWizard(n,attackDice,onDone,onCancel,false);return;}
      const completed=state.weaponRuleResolution;
      save();
      const completeSequence=()=>{state.weaponRuleResolution=null;save();if(onDone)onDone(completed.sequenceResults.at(-1),completed.sequenceResults);};
      const finish=()=>showMultiTargetAttackSummary(completed,'npo',completeSequence);
      const used=completed.sequenceResults.some(result=>!result.skipped);
      const pending=state.lastActivation?.pendingAction;
      if(used&&attackType==='shoot'&&locked?.profile)completeShootingWeaponUse({attackerSide:'npo',attackerId:n.id,
        activationId:state.lastActivation?.activationId||missionActivationId('npo',n.id),actionId:state.lastActivation?.pendingAction?.id||attackType,
        profile:locked.profile,weaponName:locked.profile.weaponName||locked.profile.name,
        continuation:{result:completed.sequenceResults.map(item=>`${item.targetName} ${item.skipped?'skipped':`${item.damage} damage`}`).join(', '),
          attackSummary:completed.sequenceResults.at(-1),attackSummaries:completed.sequenceResults,pendingAction:pending}},completeSequence);
      else finish();
      return;
    }
    if(!target){showToast('Select the targeted Player operative first.');if(onCancel)onCancel();return;}
    const targetSide=state.weaponRuleResolution?.orderedTargets?.find(item=>item.targetId===target.id)?.targetSide||'player';
    const targetName=targetSide==='npo'?npoName(target):playerName(target.id);
    const attackType=state.lastActivation?.action?.includes('Fight')?'melee':'shoot';
    const availableProfiles=npoAttackProfiles(n,attackType);
    const sequence=state.weaponRuleResolution;
    const locked=sequence?.orderedTargetIds?.length>1?lockedMultiTargetProfile(sequence,n):null;
    if(sequence?.orderedTargetIds?.length>1&&!locked){
      showMultiTargetProfileRecovery('npo',()=>{state.weaponRuleResolution=null;state.npoAttackTargetId=null;state.lastActivation={...state.lastActivation,combatDraft:null};save();closeModal();render();});
      return;
    }
    const saved=state.lastActivation?.combatDraft;
    const savedCombat=saved&&saved.targetId===target.id&&saved.attackType===attackType;
    const rollingCombat=savedCombat&&saved.rolling===true;
    const selectingCombat=savedCombat&&saved.selecting===true;
    const sameCombat=savedCombat&&!rollingCombat&&!selectingCombat;
    if(!availableProfiles.length){
      const weaponType=attackType==='shoot'?'shooting':'melee';
      showModal('Unable to Resolve Combat',`<div class="modal-inner"><div class="summary-box"><strong>This NPO has no weapon it can use for this ${weaponType} attack.</strong></div><div class="wizard-actions"><button class="btn ghost" id="cancelNpoAttack">Back</button></div></div>`);
      $('#cancelNpoAttack').onclick=()=>{if(onCancel)onCancel();};
      return;
    }
    const initialProfile=savedCombat?saved.profile:locked?.profile||(availableProfiles.length===1?canonicalAttackProfile(availableProfiles[0]):null);
    let selectedProfileIndex=initialProfile?availableProfiles.findIndex(profile=>{
      const candidate=canonicalAttackProfile(profile);
      return candidate.weaponId===initialProfile.weaponId&&candidate.profileId===initialProfile.profileId;
    }):-1;
    const profileControl=availableProfiles.length>1&&!locked&&!sameCombat&&!rollingCombat
      ? `<div class="field compact-combat-choice"><label for="npoCombatProfile">Choose Weapon Profile</label><select id="npoCombatProfile"><option value="" ${selectedProfileIndex<0?'selected ':''}disabled>Choose a profile...</option>${availableProfiles.map((profile,index)=>`<option value="${index}" ${index===selectedProfileIndex?'selected':''}>${escapeHtml(canonicalAttackProfile(profile).name)}</option>`).join('')}</select></div>`
      : '';
    const willBeDone=tombWorldEventActive('my-will-be-done')&&!sameCombat&&!rollingCombat
      ? '<label class="check-row compact-check" for="sameRoomAsC1"><input type="checkbox" id="sameRoomAsC1"><span><strong>Is this NPO in the same room as the sarcophagus?</strong><small>This matters only while My Will Be Done is active.</small></span></label>'
      : '';
    const guidance=npoCombatGuidanceHtml(n,{attackType,profile:initialProfile});
    const screen=showSharedCombatResolutionScreen({
      title:'Resolve Combat',attackerName:npoName(n),defenderName:targetName,attackType,
      weaponName:initialProfile?.name||'—',attackLabel:initialProfile?combatAttackLabel(initialProfile):'—',defenseLabel:`3 dice · ${target.save||3}+`,
      cancelId:'cancelNpoAttack',continueId:'completeNpoCombat',extraHtml:`<div id="npoCombatGuidance">${guidance}</div>${profileControl}${willBeDone}`,
      detailsHtml:`${weaponRuleSequenceProgress(sequence,targetName,`${target.wounds}/${target.maxWounds||playerDefinition(target.id)?.wounds||0} wounds`)}<div id="npoCombatRules">${weaponRulesHtml(initialProfile)}</div>`
    });
    const cancel=()=>{
      if(combatTimer)combatTimer();
      if(!sameCombat)state.lastActivation={...state.lastActivation,combatDraft:null};
      else if(sequence)state.lastActivation={...state.lastActivation,combatDraft:null};
      if(sequence){state.weaponRuleResolution=null;state.npoAttackTargetId=null;}
      save();
      if(onCancel)onCancel();
    };
    $('#cancelNpoAttack').onclick=cancel;

    let combatTimer=null;
    let resolutionCommitted=false;
    const commitCombat=(combat)=>{
      const pending=state.lastActivation?.pendingAction;
      if(resolutionCommitted||!pending||!canCommitNpoAction(pending.id,pending.apCost))return;
      if(attackType==='melee'&&weaponHasRule(combat.profile,'shock')&&!combat.shockResolved){
        showGuidedShockStep(combat,updated=>{state.lastActivation={...state.lastActivation,combatDraft:updated};save();showNpoAttackWizard(n,attackDice,onDone,onCancel,false);},()=>showNpoAttackWizard(n,attackDice,onDone,onCancel,false));
        return;
      }
      resolutionCommitted=true;
      const complete=$('#completeNpoCombat');
      complete.disabled=true;
      const resolvedCombat=resolveAutomaticDimensionalBanishment(combat);
      state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
      save();
      let summary={...resolvedCombat,side:targetSide};
      const finishWeaponUse=(done,attackSummaries=[summary])=>attackType==='shoot'?completeShootingWeaponUse({
        attackerSide:'npo',attackerId:n.id,
        activationId:state.lastActivation?.activationId||missionActivationId('npo',n.id),
        actionId:state.lastActivation?.pendingAction?.id||attackType,
        profile:resolvedCombat.profile,weaponName:resolvedCombat.profile?.weaponName||resolvedCombat.profile?.name,
        continuation:{result:attackSummaries.map(item=>`${item.targetName} ${item.skipped?'skipped':`${item.damage} damage`}`).join(', '),
          attackSummary:summary,attackSummaries,pendingAction:state.lastActivation?.pendingAction}
      },done):done();
      const queue=state.weaponRuleResolution;
      if(queue?.currentTargetId===target.id){
        if((queue.committedTargetIds||[]).includes(target.id))return;
        applyNpoAttackDamage(n,target,summary);
        const committedTargetIds=[...new Set([...(queue.committedTargetIds||[]),target.id])];
        state.weaponRuleResolution={...advanceMultiTargetAttackSequence(queue,target.id,summary),committedTargetIds};
        if(state.weaponRuleResolution.currentTargetId){
          state.npoAttackTargetId=state.weaponRuleResolution.currentTargetId;
          state.lastActivation={...state.lastActivation,combatDraft:null};
          save();
          showNpoAttackWizard(n,attackDice,onDone,onCancel,false);
          return;
        }
        const completed=state.weaponRuleResolution;
        save();
        const completeSequence=()=>{
            state.weaponRuleResolution=null;
            save();
            const hot=state.hotResolution?.attackerId===n.id?state.hotResolution:null;
            if(hot)summary={...summary,hot:{roll:hot.roll,damage:hot.damage,woundsBefore:hot.woundsBefore,woundsAfter:hot.woundsAfter,incapacitated:hot.incapacitated}};
            if(onDone)onDone(summary,completed.sequenceResults);
        };
        if(weaponHasRule(resolvedCombat.profile,'hot'))finishWeaponUse(completeSequence,completed.sequenceResults);
        else showMultiTargetAttackSummary(completed,'npo',completeSequence);
        return;
      }
      applyNpoAttackDamage(n,target,summary);
      finishWeaponUse(()=>{
        const hot=state.hotResolution?.attackerId===n.id?state.hotResolution:null;
        if(onDone)onDone(hot?{...summary,hot:{roll:hot.roll,damage:hot.damage,woundsBefore:hot.woundsBefore,woundsAfter:hot.woundsAfter,incapacitated:hot.incapacitated}}:summary);
      });
    };
    const displayCombat=(combat,animate=false)=>{
      const resolvedCombat=resolveAutomaticDimensionalBanishment(combat);
      const banishmentAnimating=resolvedCombat.dimensionalBanishmentTriggered&&!resolvedCombat.dimensionalBanishmentAnimationShown;
      if(resolvedCombat!==combat){
        state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
        save();
      }
      const display=displaySharedCombatResult(resolvedCombat,{
        animate,
        waiting:banishmentAnimating,
        message:'Damage is applied exactly once when you Continue.',
        onContinue:()=>commitCombat(resolvedCombat)
      });
      if(banishmentAnimating){
        resolvedCombat.dimensionalBanishmentAnimationShown=true;
        state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
        save();
        settleDimensionalBanishment(resolvedCombat,()=>{
          display?.completeWaiting();
        });
      }
    };
    const finishAutomaticCombat=(profile,rolledAttackDice,rolledDefenseDice)=>{
      const stun=applyStunForAttack({profile,attackDice:rolledAttackDice,sourceAttackId:`attack:${state.turningPoint}:${state.activationNumber}:npo:${n.id}:${target.id}`,targetId:target.id,targetName:targetName,targetSide});
      const resolution=resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile);
      const combat={
        ...recordedCombat({attackerName:npoName(n),defenderName:targetName,attackType,attackerSide:'npo',defenderSide:targetSide,profile,before:target.wounds||10,
          normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage}),
        attackDice:rolledAttackDice,saveDice:rolledDefenseDice,
        retainedSaves:retainedDiceTotals(rolledDefenseDice).normal+retainedDiceTotals(rolledDefenseDice).critical,
        recordedOutcome:false,targetId:target.id,targetName:targetName,
        severeApplied:rolledAttackDice.some(die=>die.severeConverted)
      };
      combat.eventMessages=stun.message?[stun.message]:[];
      const resolvedCombat=resolveAutomaticDimensionalBanishment(combat);
      state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
      save();
      displayCombat(resolvedCombat,false);
    };
    let rollStarted=false;
    const startAutomaticCombat=(restoredRoll=null,guidedConfirmed=false)=>{
      if(rollStarted)return;
      const profileIndex=restoredRoll
        ? availableProfiles.findIndex(profile=>canonicalAttackProfile(profile).weaponId===restoredRoll.profile.weaponId&&canonicalAttackProfile(profile).profileId===restoredRoll.profile.profileId)
        : locked?availableProfiles.findIndex(profile=>canonicalAttackProfile(profile).weaponId===sequence.weaponId&&canonicalAttackProfile(profile).profileId===sequence.profileKey)
        : availableProfiles.length===1?0:selectedProfileIndex;
      if(profileIndex<0||!Number.isInteger(profileIndex))return;
      const baseProfile=canonicalAttackProfile(availableProfiles[profileIndex]);
      if(!restoredRoll&&!guidedConfirmed&&!state.weaponRuleResolution?.continueConfirmed){
        const back=()=>{rollStarted=false;showNpoAttackWizard(n,attackDice,onDone,onCancel,false);};
        const resume=()=>resumeCombatAfterWeaponRuleCheck({
          render:()=>showNpoAttackWizard(n,attackDice,onDone,onCancel,false,true),
          onMounted:mounted=>mounted.startAutomaticCombat(null,true),
          onRecovery:back
        });
        const ruleId=weaponHasRule(baseProfile,'blast')?'blast':weaponHasRule(baseProfile,'torrent')?'torrent':null;
        const resolutionKey=`npo:${state.turningPoint}:${state.activationNumber}:${n.id}:${target.id}:${baseProfile.weaponId}:${baseProfile.profileId}`;
        const selectSecondaryTargets=()=>{
          if(!ruleId){resume();return;}
          const playerTargets=inPlayLivingPlayerOperativeIds().map(id=>({id,targetSide,label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id),wounds:playerCurrentWounds(id),inPlay:true}));
          const npoTargets=activeNpos().map(operative=>({id:operative.id,targetSide:'npo',label:npoName(operative),wounds:operative.wounds,inPlay:true}));
          showSecondaryTargetCheck({ruleId,distance:weaponRuleValue(baseProfile,ruleId),attackerSide:'npo',attackerId:n.id,primaryTargetId:target.id,targets:ruleId==='blast'?[...playerTargets,...npoTargets]:playerTargets,weaponId:baseProfile.weaponId,weaponName:baseProfile.weaponName,profileKey:baseProfile.profileId,profileName:baseProfile.profileName,weaponRules:baseProfile.rules,onContinue:resume,onBack:back});return;
        };
        if(weaponHasRule(baseProfile,'seek-light')&&target.order==='Conceal'){showSeekLightCheck({target,resolutionKey,onContinue:selectSecondaryTargets,onBack:back});return;}
        selectSecondaryTargets();return;
      }
      rollStarted=true;
      if(combatTimer)combatTimer();
      const transaction=eventTransaction(`attack:${state.turningPoint}:${state.activationNumber}:npo:${n.id}:${target.id}`,{definitionAnswers:{}});
      if(transaction.definitionAnswers.sameRoomAsC1===undefined)transaction.definitionAnswers.sameRoomAsC1=Boolean($('#sameRoomAsC1')?.checked);
      const profile=effectiveWeaponProfile(baseProfile,{attackerSide:'npo',attackType,sameRoomAsC1:transaction.definitionAnswers.sameRoomAsC1});
      const profileSelect=$('#npoCombatProfile');
      if(profileSelect)profileSelect.disabled=true;
      const weapon=$('.compact-combat-profile div:nth-child(4) strong');
      if(weapon)weapon.textContent=profile.name;
      const attack=$('.compact-combat-profile div:nth-child(5) strong');
      if(attack)attack.textContent=combatAttackLabel(profile);
      const rules=$('#npoCombatRules');
      if(rules)rules.innerHTML=weaponRulesHtml(profile);
      const guidance=$('#npoCombatGuidance');
      if(guidance)guidance.innerHTML=npoCombatGuidanceHtml(n,{attackType,profile});
      const combatResults=$('#combatResults');
      const completeButton=$('#completeNpoCombat');
      if(!combatResults||!completeButton||!screen?.dice?.isConnected){
        showCombatResumeRecovery(()=>showNpoAttackWizard(n,attackDice,onDone,onCancel,false));
        return;
      }
      combatResults.replaceChildren();
      completeButton.disabled=true;
      completeButton.textContent='Rolling…';
      const rolledAttackDice=restoredRoll?.attackDice||rolledAttackDiceForProfile(profile);
      const rolledDefenseDice=restoredRoll?.saveDice||retainSuccessfulDice(rolledCombatDice(effectiveDefenseDiceCount(profile,rolledAttackDice,3),Number(target.save)||3));
      state.lastActivation={...state.lastActivation,dice:attackDice.map(d=>({...d})),targetConfirmed:true,combatDraft:{
        rolling:true,attackType,targetId:target.id,targetName:targetName,profile,attackDice:rolledAttackDice,saveDice:rolledDefenseDice,
        severeApplied:rolledAttackDice.some(die=>die.severeConverted)
      }};
      save();
      combatTimer=runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,rolledAttackDice,rolledDefenseDice,onComplete:(completedAttackDice,completedDefenseDice)=>{
        combatTimer=null;
        finishAutomaticCombat(profile,completedAttackDice,completedDefenseDice);
      }});
    };
    $('#npoCombatProfile')?.addEventListener('change',event=>{
      const profileIndex=Number(event.currentTarget.value);
      if(event.currentTarget.value===''||!Number.isInteger(profileIndex)||!availableProfiles[profileIndex])return;
      const profile=canonicalAttackProfile(availableProfiles[profileIndex]);
      selectedProfileIndex=profileIndex;
      state.lastActivation={...state.lastActivation,combatDraft:{selecting:true,attackType,targetId:target.id,targetName:targetName,profile}};
      save();
      const weapon=$('.compact-combat-profile div:nth-child(4) strong');
      if(weapon)weapon.textContent=profile.name;
      const attack=$('.compact-combat-profile div:nth-child(5) strong');
      if(attack)attack.textContent=combatAttackLabel(profile);
      const rules=$('#npoCombatRules');
      if(rules)rules.innerHTML=weaponRulesHtml(profile);
      const guidance=$('#npoCombatGuidance');
      if(guidance)guidance.innerHTML=npoCombatGuidanceHtml(n,{attackType,profile});
      screen.continueButton.disabled=false;
      screen.continueButton.onclick=()=>startAutomaticCombat();
    });
    if(sameCombat)displayCombat(saved,animateCombat);
    else if(rollingCombat)startAutomaticCombat(saved);
    else if(availableProfiles.length===1&&willBeDone){
      screen.continueButton.disabled=false;
      screen.continueButton.textContent='Roll Attack';
      screen.continueButton.onclick=()=>startAutomaticCombat();
    }
    else if(availableProfiles.length===1&&!resumeGuided)startAutomaticCombat();
    else if(locked&&!resumeGuided)startAutomaticCombat();
    else if(selectingCombat){
      if(!resumeGuided){
        screen.continueButton.disabled=false;
        screen.continueButton.onclick=()=>startAutomaticCombat();
      }
    }
    return {...screen,startAutomaticCombat};
  }

  function spinnerField(id,label,value,min,max){return `<div class="field spinner-field"><label>${label}</label><div class="spinner"><input id="${id}" type="number" value="${value}" min="${min}" max="${max}" inputmode="numeric"><button type="button" data-spin="${id}" data-delta="-1" aria-label="Decrease ${label}">−</button><button type="button" data-spin="${id}" data-delta="1" aria-label="Increase ${label}">+</button></div></div>`;}
  function bindSpinners(root){$$('[data-spin]',root).forEach(b=>b.onclick=()=>{const input=$(`#${b.dataset.spin}`);const min=Number(input.min||0),max=Number(input.max||99);input.value=Math.max(min,Math.min(max,(Number(input.value)||0)+Number(b.dataset.delta)));});}
  function num(id){return Number($(`#${id}`)?.value)||0;}

  function rollingDieHtml(){
    const value=roll();
    return `<div class="die hit rolling" aria-label="Rolling die">${pipPositions[value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;
  }

  const pipPositions={1:[5],2:[1,9],3:[1,5,9],4:[1,3,7,9],5:[1,3,5,7,9],6:[1,3,4,6,7,9]};
  function dieHtml(d){const kind=d.kind||'';const label=d.ariaLabel|| (d.severeConverted?`Critical success, converted from a normal success by Severe. Rolled value ${d.value}.`:`${d.value}${kind?` ${kind}`:''}`);return `<div class="die ${kind}" aria-label="${label}">${pipPositions[d.value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;}

  function renderMission(){
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name)}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary)}</p></div>`).join('');
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${m.brief}</p></div></div>
      <section class="card"><h3>Objective</h3><p>${m.objective}</p><div class="stat-grid"><div class="stat"><small>Starting NPOs</small><strong>${missionSetup(m)}</strong></div><div class="stat"><small>TP1 Initiative</small><strong>${missionFirstInitiative(m)==='npo'?'NPOs':'Player'}</strong></div><div class="stat"><small>Objective</small><strong>${escapeHtml(m.missionEngine?.progressLabel||missionTracker(m))}</strong></div></div><p><strong>NPO deployment:</strong> ${escapeHtml(m.startingNpos?.deployment||'Use the mission rules.')}</p></section>
      ${boardSvg(m.id)}
      <section class="card"><h3>Battle settings</h3><p><strong>Restless Tomb:</strong> ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p><p><strong>Deadly Encounters:</strong> ${state.deadlyEncountersEnabled?'On':'Off'} (Official Expansion - White Dwarf 521)</p></section>
      <section class="card"><h3>Mission rules</h3><div class="mission-rules">${rules}</div></section>
      <section class="card"><h3>Victory</h3><p><strong>Win:</strong> ${escapeHtml(m.victory?.win||'See mission rules.')}</p><p><strong>Lose:</strong> ${escapeHtml(m.victory?.lose||'See mission rules.')}</p></section>${missionProgressHtml()}`;
  }
  function renderRoster(){const available=Object.values(npoInventory()).reduce((sum,item)=>sum+item.remaining,0);app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>${available} of ${MAX_PHYSICAL_NPOS} physical models remain available. Activation status is tracked automatically.</p></div><button class="btn secondary" id="addNpo" ${available?'':'disabled'}>Add NPO</button></div><div class="player-roster-grid npo-roster-grid">${state.roster.length?sortedNposForDisplay(state.roster).map(n=>npoRosterCard(n,n.battlefieldState==='deployed'||n.wounds<=0)).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));$$('[data-npo-loadout]').forEach(select=>select.onchange=()=>changeNpoLoadout(select.dataset.npoLoadout,select.value));}
  function renderPlayerRoster(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    const cards=(state.playerRoster||[]).map(id=>{
      const operative=livePlayerOperative(id);
      if(!operative)return '';
      const eliminated=casualties.has(id);
      const operativeState=playerOperativeState(id);
      const status=operativeState.inPlay===false?(operativeState.offBoardReason==='escaped'?'ESCAPED':'OFF BOARD'):eliminated?'ELIMINATED':activated.has(id)?'ACTIVATED':'READY';
      const weaponNames=(operative.weapons||[]).map(w=>escapeHtml(w.name)).join(' · ');
      const abilities=(operative.abilities||[]).map(ability=>typeof ability==='string'?{name:ability,text:''}:ability);
      const abilityGuidance=abilities.length?`<details class="operative-guidance"><summary>Operative abilities (${abilities.length})</summary>${abilities.map(ability=>`<div><strong>${escapeHtml(ability.name)}</strong>${ability.text?`<p>${escapeHtml(ability.text)}</p>`:''}</div>`).join('')}<small>Resolve these abilities on the tabletop unless the Guide explicitly prompts you.</small></details>`:'';
      const wounds=playerCurrentWounds(id), maxWounds=Number(playerDefinition(id)?.wounds??operative.wounds);
      return `<article class="operative-card roster-operative-card ${eliminated?'dead':''}"><div class="operative-card-header"><div class="operative-identity"><h4>${escapeHtml(playerName(id))}</h4><p>${escapeHtml(operative.role||'Operative')}</p></div><span class="operative-status-badge ${status.toLowerCase().replace(' ','-')}">${status}</span></div><div class="operative-stat-line"><span><small>APL</small><b>${operative.apl??'—'}</b></span><span><small>MOVE</small><b>${operative.move??'—'}"</b></span><span><small>SAVE</small><b>${operative.save??'—'}+</b></span><span><small>WOUNDS</small><b class="${wounds===0?'zero-wounds':''}">${wounds}/${maxWounds}</b></span></div>${weaponNames?`<p class="player-roster-weapons"><strong>Weapons:</strong> ${weaponNames}</p>`:''}${abilityGuidance}<div class="wound-controls"><button class="btn ghost" data-player-wound="${id}" ${wounds<=0||operativeState.inPlay===false?'disabled':''}>− Wound</button><button class="btn ghost" data-player-heal="${id}" ${wounds>=maxWounds||operativeState.inPlay===false?'disabled':''}>+ Heal</button></div></article>`;
    }).join('');
    const teamName=playerTeamData?.teamName||playerTeamEntry()?.name||'Player';
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">PLAYER ROSTER</p><h2>${escapeHtml(teamName)}</h2><p>${inPlayPlayerOperativeIds().filter(id=>!casualties.has(id)).length} active on the battlefield of ${(state.playerRoster||[]).length} selected operatives.</p></div></div>${factionGuidanceHtml()}<div class="roster-grid">${cards||'<div class="card empty">No Player operatives were selected for this game.</div>'}</div>`;
    $$('[data-player-wound]').forEach(button=>button.onclick=()=>adjustPlayerWounds(button.dataset.playerWound,-1));
    $$('[data-player-heal]').forEach(button=>button.onclick=()=>adjustPlayerWounds(button.dataset.playerHeal,1));
  }
  function npoProfileWeaponHtml(weapon){
    return weaponProfiles(weapon).map(profile=>{const label=profile.name===weapon.name?weapon.name:`${weapon.name} (${profile.name.toLowerCase()})`;return `<li><strong>${escapeHtml(label)}</strong><span>${profile.attacks}A · ${profile.hit}+ · ${profile.damage.normal}/${profile.damage.critical}${profile.rules?.length?` · ${escapeHtml(profile.rules.join(', '))}`:''}</span></li>`;}).join('');
  }
  function npoProfileDetailsHtml(n,definition){
    const ranged=(definition.rangedWeapons||[]).filter(weapon=>!definition.loadoutOptions||weapon.id===n.weaponId);
    const melee=definition.meleeWeapons||[];
    const selectedLoadout=definition.loadoutOptions?.find(option=>option.id===n.weaponId)?.name||'Fixed weapons';
    const actionItems=(definition.actions||[]).map(action=>`<div><strong>${escapeHtml(action.name)} · ${action.ap} AP</strong><p>${escapeHtml(action.description)}</p>${action.oncePerTurningPoint?`<small>${state.npoRuleState.oncePerTurningPoint[action.id]===state.turningPoint?'Used this turning point':'Available this turning point'}</small>`:''}</div>`).join('');
    const passiveItems=(definition.passiveRules||[]).map(rule=>`<div><strong>${escapeHtml(rule.name)}</strong><p>${escapeHtml(rule.description)}</p>${rule.oncePerTurningPoint?`<small>${state.npoRuleState.oncePerTurningPoint[rule.id]===state.turningPoint?'Used this turning point':'Available this turning point'}</small>`:''}</div>`).join('');
    return `<details class="operative-guidance npo-profile-details"><summary>Gameplay profile</summary><p><strong>Selected loadout:</strong> ${escapeHtml(selectedLoadout)}</p>${ranged.length?`<strong>Ranged weapons</strong><ul class="npo-weapon-list">${ranged.map(npoProfileWeaponHtml).join('')}</ul>`:''}${melee.length?`<strong>Melee weapons</strong><ul class="npo-weapon-list">${melee.map(npoProfileWeaponHtml).join('')}</ul>`:''}${actionItems?`<strong>Operative actions</strong>${actionItems}`:''}${passiveItems?`<strong>Passive rules</strong>${passiveItems}`:''}</details>`;
  }
  function npoRosterCard(n,controls){
    const hasProfile=Number.isFinite(n.maxWounds)&&n.maxWounds>0;
    const eliminated=hasProfile&&n.wounds<=0;
    const status=n.battlefieldState==='reserve'?'RESERVE':!hasProfile?'PROFILE PENDING':eliminated?'ELIMINATED':n.dormant?'DORMANT':n.ready?'READY':'ACTIVATED';
    const save=Number.isFinite(n.save)?`${n.save}+`:'—';
    const wounds=hasProfile?`${n.wounds}/${n.maxWounds}`:'—';
    const definition=npoDefinition(n.type),isolatorUsed=state.roster.some(other=>other.id!==n.id&&other.type===TOMB_CRAWLER_TYPE&&other.weaponId===ISOLATOR_LOADOUT);
    const loadout=definition?.loadoutOptions&&state.turningPoint===0?`<div class="field"><label for="loadout-${escapeHtml(n.id)}">Loadout</label><select id="loadout-${escapeHtml(n.id)}" data-npo-loadout="${escapeHtml(n.id)}">${definition.loadoutOptions.map(option=>`<option value="${option.id}" ${option.id===n.weaponId?'selected':''} ${option.id===ISOLATOR_LOADOUT&&isolatorUsed?'disabled':''}>${escapeHtml(option.name)}</option>`).join('')}</select></div>`:'';
    return `<article class="player-roster-card npo-roster-card ${eliminated?'dead':''}">
      <div class="operative-card-header"><div class="operative-identity"><strong>${escapeHtml(npoName(n))}</strong><small>${escapeHtml(n.type)}</small></div><span class="operative-status-badge ${status.toLowerCase().replace(' ','-')}">${status}</span></div>
      <div class="operative-stat-line"><span><small>APL</small><b>${effectiveApl(n.id,n.apl)||'—'}</b></span><span><small>MOVE</small><b>${Number.isFinite(n.move)?`${n.move}&quot;`:'—'}</b></span><span><small>SAVE</small><b>${save}</b></span><span><small>WOUNDS</small><b class="${eliminated?'zero-wounds':''}">${wounds}</b></span></div>
      ${loadout}${npoProfileDetailsHtml(n,definition)}<div class="npo-card-actions">${controls?`<div class="wound-controls"><button class="btn ghost" data-wound="${n.id}" ${!hasProfile||n.wounds<=0?'disabled':''}>− Wound</button><button class="btn ghost" data-heal="${n.id}" ${!hasProfile||n.wounds>=n.maxWounds?'disabled':''}>+ Heal</button></div>`:''}<div class="quick-actions"><button class="btn danger" data-delete="${n.id}" ${state.turningPoint>0?'disabled':''}>Remove NPO</button></div></div>
    </article>`;
  }
  function operativeCard(n,controls){return npoRosterCard(n,controls);}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(j.text)}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Instructions & quick reference</h2><p>Review the NPO decision process and common gameplay terms without changing the current game.</p></div></div>${guideInstructionsHtml(false)}<section class="card help-list">
    <details><summary>Deadly Encounters: Tomb Worlds</summary><p>This is the official optional expansion from White Dwarf 521, February 2026. The Guide implements only its PvE solo method. Player operatives reveal persistent features; NPOs never reveal them, although revealed features can affect NPOs. Rooms and eligible markers use separate D33 tables, and every feature rule is unique across the battle. Deadly Encounters is independent from Restless Tomb. Consult the official publication for authoritative wording.</p></details>
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
  function rosterBreakdown(){const counts={};state.roster.forEach(n=>counts[n.type]=(counts[n.type]||0)+1);return Object.entries(counts).sort(([a],[b])=>compareNpoDisplayNames(a,b)).map(([k,v])=>`${v} ${k}${v>1?'s':''}`).join(' · ')||'No starting NPOs';}
  function showAddNpo(){
    const inventory=npoInventory(),types=sortedNposForDisplay(Object.keys(npoDefinitions));
    showModal('Add NPO',`<div class="field"><label>NPO type</label><select id="newNpoType">${types.map(type=>`<option value="${escapeHtml(type)}" ${inventory[type].remaining?'':'disabled'}>${escapeHtml(type)} — ${inventory[type].remaining} remaining</option>`).join('')}</select></div><div id="newNpoLoadout"></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add NPO</button></div>`);
    const renderLoadout=()=>{const type=$('#newNpoType').value,definition=npoDefinition(type),isolatorUsed=state.roster.some(npo=>npo.type===TOMB_CRAWLER_TYPE&&npo.weaponId===ISOLATOR_LOADOUT);$('#newNpoLoadout').innerHTML=definition?.loadoutOptions?`<div class="field"><label>Loadout</label><select id="newNpoWeapon">${definition.loadoutOptions.map(option=>`<option value="${option.id}" ${option.id===ISOLATOR_LOADOUT&&isolatorUsed?'disabled':''}>${escapeHtml(option.name)}</option>`).join('')}</select></div>`:'';};
    $('#newNpoType').onchange=renderLoadout;renderLoadout();
    $('#confirmAdd').onclick=()=>{const type=$('#newNpoType').value;if(!type||!npoInventory()[type]?.remaining){showToast(`No ${type||'NPO'} model remains available.`);return;}const npo=createNpo(type,undefined,{weaponId:$('#newNpoWeapon')?.value});if(!commitNpoRoster([...state.roster,npo],'add that NPO'))return;if(state.startingNpoGeneration)selectStartingNpos(state.startingNpoGeneration);log(`${npoName(npo)} added to the battlefield.`);closeModal();save();render();};
  }
  function changeNpoLoadout(id,weaponId){
    if(state.turningPoint>0)return;
    const candidate=state.roster.map(npo=>npo.id===id?{...npo,weaponId,attack:canonicalAttackProfile(npoAttackProfiles({...npo,weaponId},'shoot')[0]||npoAttackProfiles({...npo,weaponId},'melee')[0])}:npo);
    if(!commitNpoRoster(candidate,'change that loadout')){render();return;}
    save();render();
  }
  function adjustPlayerWounds(id,d){
    const definition=playerDefinition(id);
    if(!definition||!isPlayerOperativeInPlay(id))return;
    const maxWounds=Number(definition.wounds||0), before=playerCurrentWounds(id);
    const wounds=Math.max(0,Math.min(maxWounds,before+d));
    if(wounds===before)return;
    state.playerWounds=state.playerWounds||{};
    state.playerWounds[id]=wounds;
    const casualties=new Set(state.playerCasualtyIds||[]);
    if(wounds===0){
      casualties.add(id);
      if(!state.playerActivatedIds.includes(id))state.playerActivatedIds.push(id);
    }else if(before===0)casualties.delete(id);
    state.playerCasualtyIds=[...casualties];
    state.playerReady=playerOperativesRemaining();
    if(checkGameEnd())return;
    setNextActivation(state.nextSide||'npo');
    save();render();
  }
  function adjustWounds(id,d){
    const n=state.roster.find(x=>x.id===id);
    if(!n)return;
    const wasOut=n.battlefieldState==='out-of-action';
    const wounds=Math.max(0,Math.min(n.maxWounds,n.wounds+d));
    if(wasOut&&wounds>0&&activeNpos().length>=MAX_NPOS){
      showToast(`Only ${MAX_NPOS} active NPOs can be on the battlefield.`);
      return;
    }
    n.wounds=wounds;
    if(n.wounds===0){
      n.ready=false;
      n.deployed=false;
      n.battlefieldState='out-of-action';
    }else if(wasOut){
      n.deployed=true;
      n.battlefieldState='deployed';
      n.dormant=true;
      n.ready=false;
    }
    if(checkGameEnd())return;
    save();render();
  }
  function deleteNpo(id){
    if(state.turningPoint>0){showToast('NPOs remain allocated after gameplay begins.');return;}
    state.roster=state.roster.filter(x=>x.id!==id);
    if(state.startingNpoGeneration)selectStartingNpos(state.startingNpoGeneration);
    save();render();
  }

  function animateMissionDice(operation,context={}){
    return new Promise((resolve,reject)=>{
      const supplied=context.missionDice;
      const dice=Array.isArray(supplied)&&supplied.length===operation.dice.count?supplied:Array.from({length:operation.dice.count},()=>roll(operation.dice.sides));
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
      const maximum=Math.min(operation.maximum??20,Math.max(minimum,inPlayLivingPlayerOperativeCount()));
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
        activeSide:state.nextSide,
        playerOperativeCount:Array.isArray(state.playerRoster)?state.playerRoster.length:0,
        escapedOperativeCount:state.missionState?.escapedIds?.length||0
      },
      ...overrides
    };
  }

  function activationIdFromState(sourceState,side,operativeId){
    const turningPoint=Number(sourceState?.turningPoint||0);
    const activationNumber=Number(sourceState?.activationNumber||0);
    return `${turningPoint}:${activationNumber+1}:${side}:${operativeId}`;
  }

  function missionActivationId(side,operativeId){
    return activationIdFromState(state,side,operativeId);
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
    if(entry.type==='mission-feature-opened'||entry.type==='mission-feature-corrected')return entry.summary||entry.title;
    if(entry.operativeId)return `${entry.title||'Mission activity'}: ${playerName(entry.operativeId)}`;
    if(!change)return entry.summary||entry.title||'Mission activity recorded.';
    const delta=change.after-change.before;
    return `${entry.title||'Mission activity'}: ${delta>0?'+':''}${delta}`;
  }

  function missionOperation(operationId){
    const actions=objectiveDefinition?.actions||[];
    const hooks=Object.values(objectiveDefinition?.hooks||{}).flat();
    return [...actions,...hooks].flatMap(event=>event.operations||[]).find(operation=>operation.id===operationId)||null;
  }

  function missionDetailsContentFallback(){
    const selected=mission();
    return `<div class="mission-details"><h3>${escapeHtml(selected?.name||'Selected Mission')}</h3><section><h4>Objective</h4><p>${escapeHtml(selected?.objective||'Review the mission rules and track progress on the tabletop.')}</p></section><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p><p>Deadly Encounters: ${state.deadlyEncountersEnabled?'On':'Off'} (Official Expansion - White Dwarf 521)</p></section><p class="muted">Automated mission progress is not available for this mission.</p></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
  }

  function missionDetailsContent(){
    if(!objectiveEngine)return missionDetailsContentFallback();
    const model=objectiveEngine.getMissionDetailsModel();
    const objective=model.objectives[0];
    const history=model.history.slice(0,objectiveDefinition.presentation.historyDisplayCount||5);
    if(!objective)return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p><p>Deadly Encounters: ${state.deadlyEncountersEnabled?'On':'Off'} (Official Expansion - White Dwarf 521)</p></section><section><h4>Objective</h4><p>${escapeHtml(model.objectiveSummary)}</p></section><section><h4>Recent Activity</h4>${history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(missionHistoryText(entry))}</span></li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>'}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
    const completedDuring=objective.completedTurningPoint?`<section><h4>Completed during</h4><p>Turning Point ${objective.completedTurningPoint}</p></section>`:'';
    const activity=history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(missionHistoryText(entry))}</span>${entry.turningPoint?`<small>Turning Point ${entry.turningPoint}</small>`:''}</li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>';
    return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p><p>Deadly Encounters: ${state.deadlyEncountersEnabled?'On':'Off'} (Official Expansion - White Dwarf 521)</p></section>${objective.completed?'<p class="mission-complete-status">✓ Objective Complete</p>':`<section><h4>Objective</h4><p>${escapeHtml(model.objectiveSummary)}</p></section>`}${completedDuring}<section><h4>${objective.completed?'Final Progress':'Progress'}</h4><p class="mission-progress">${objective.value} / ${objective.target}</p></section><section><h4>Recent Activity</h4>${activity}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
  }

  function showMissionDetails(){
    let completed=false;
    let content;
    try{completed=Boolean(objectiveEngine?.getMissionHudModel().completed);content=missionDetailsContent();}
    catch(error){console.warn('[MissionEngine] Mission details unavailable.',error);content=missionDetailsContentFallback();}
    showModal(completed?'MISSION STATUS':'MISSION DETAILS',content);
  }

  function showMissionResult(title,outcome){
    if(!objectiveEngine||!objectiveDefinition||!outcome){console.warn('[MissionEngine] Mission result dialog skipped because result data is unavailable.');return;}
    const change=outcome.changes?.[0],dice=Object.values(outcome.results||{})[0]?.dice||[],model=objectiveEngine.getMissionHudModel();
    const objective=objectiveDefinition.objectives.find(item=>item.id===change?.objectiveId);
    const delta=change?Math.abs(change.after-change.before):0;
    const decreased=change&&change.after<=change.before;
    const detail=objective?(decreased?(delta?`${objective.label} repaired: ${delta}`:`No ${objective.label} repaired.`):`${objective.label} added: ${delta}`):'Mission result recorded.';
    const completed=Boolean(model.completed&&change&&change.before<model.target);
    const completionDialog=objectiveDefinition.dialogs?.[objectiveDefinition.completion?.dialogId]||{};
    const total=dice.reduce((sum,value)=>sum+value,0);
    const inputs=Object.entries(outcome.inputs||{}).map(([id,value])=>`<p>${escapeHtml(missionOperation(id)?.label||id)}: <strong>${value}</strong></p>`).join('');
    const diceResult=dice.length?`<div class="dice-row settled">${dice.map(value=>dieHtml({value})).join('')}</div><p>Dice: ${dice.join(' + ')}${dice.length>1?` · Total: ${total}`:''}</p>`:'';
    const progress=objective?`<div class="summary-box"><strong>Progress: ${model.value} / ${model.target} ${escapeHtml(objective.label)}</strong></div>`:'';
    showModal(completed?(completionDialog.title||'MISSION OBJECTIVE COMPLETE'):title,`<div class="mission-roll-result">${completed?`<h3>${escapeHtml(objectiveDefinition.name)}</h3><p class="mission-complete-status">✓ ${escapeHtml(objective.label)}</p>`:''}${diceResult}${inputs}<p>${detail}</p>${progress}${completed?`<p>${escapeHtml(completionDialog.message||'Continue the battle.')}</p>`:''}</div><div class="wizard-actions"><button class="btn primary" data-close>${completed?'Continue the battle':'Continue'}</button></div>`);
  }

  function showMissionConfirmation(options,onConfirm){
    options=options&&typeof options==='object'?options:{};
    showModal(options.title||'Confirm Mission Action',`<p>${escapeHtml(options.description||'')}</p><p>${escapeHtml(options.message||'')}</p><div class="wizard-actions"><button class="btn ghost" data-close>${escapeHtml(options.cancelLabel||'Cancel')}</button><button class="btn primary" id="confirmMissionDialog">${escapeHtml(options.confirmLabel||'Confirm')}</button></div>`);
    $('#confirmMissionDialog').onclick=typeof onConfirm==='function'?onConfirm:closeModal;
  }

  function clearPendingBreach(stage){
    state.missionActionContext=null;
    state.combatState={side:'player',stage:{...stage}};
    save();
    showPlayerActivation(stage);
  }

  function beginBreachSarcophagus(stage){
    const operativeId=stage.playerOperativeId;
    const activationId=missionActivationId('player',operativeId);
    const apCost=breachSarcophagusApCost(operativeId);
    const remainingAp=Number(stage.apl||3)-playerActionCost(stage);
    if(!canOfferBreachSarcophagus(stage,operativeId))return;
    if(remainingAp<apCost){showToast('Not enough AP to Breach the sarcophagus.');return;}
    if(apCost===1&&(stage.shoot||stage.charge)){showToast('The Breach reduction cannot be combined with Shoot or Charge in this activation.');return;}
    state.combatState={side:'player',stage:{...stage}};
    state.missionActionContext={missionId:'04',actionId:'breachSarcophagus',side:'player',operativeId,activationId,apCost,remainingAp,step:'control-range',controlRangeConfirmed:null,enemyControlRangeConfirmed:null,committed:false,diceRolled:false,dice:[],previousTotal:null,newTotal:null,victoryCommitted:false};
    save();renderBreachSarcophagusStep(stage);
  }

  function renderBreachSarcophagusStep(stage){
    const context=state.missionActionContext;
    if(!context||context.missionId!=='04'||context.actionId!=='breachSarcophagus')return showPlayerActivation(stage);
    if(context.operativeId!==stage.playerOperativeId||context.activationId!==missionActivationId('player',stage.playerOperativeId)){
      state.missionActionContext=null;save();showToast('The active operative changed. Breach was not performed.');showPlayerActivation(stage);return;
    }
    if(context.committed&&context.diceRolled&&!context.newTotal){performBreachSarcophagus(stage,true);return;}
    if(context.step==='control-range'){
      showModal('Breach Sarcophagus',`<h3 id="breachControlQuestion">Is this operative within the sarcophagus’s control range?</h3><p>Select Yes only if the operative is close enough to control the sarcophagus objective marker.</p><div class="wizard-actions"><button class="btn ghost" id="breachControlNo">No</button><button class="btn primary" id="breachControlYes">Yes</button></div><div class="wizard-actions breach-navigation"><button class="btn ghost" id="cancelBreach" aria-label="Cancel and abandon Breach Sarcophagus">Cancel</button></div>`,undefined,'breach-control-range');
      $('#breachControlNo').onclick=()=>clearPendingBreach(stage);
      $('#breachControlYes').onclick=()=>{context.controlRangeConfirmed=true;context.step='enemy-control-range';save();renderBreachSarcophagusStep(stage);};
      $('#cancelBreach').onclick=()=>clearPendingBreach(stage);
      return;
    }
    if(context.step==='enemy-control-range'){
      showModal('Breach Sarcophagus',`<h3 id="breachEnemyQuestion">Is this operative outside the control range of every NPO?</h3><p>An operative cannot perform Breach while it is within an enemy operative’s control range.</p><div class="wizard-actions"><button class="btn ghost" id="breachEnemyNo">No</button><button class="btn primary" id="breachEnemyYes">Yes</button></div><div class="wizard-actions breach-navigation"><button class="btn ghost" id="breachBackToControl" aria-label="Back to the sarcophagus control-range question">Back</button></div>`,undefined,'breach-enemy-range');
      $('#breachEnemyNo').onclick=()=>clearPendingBreach(stage);
      $('#breachEnemyYes').onclick=()=>{context.enemyControlRangeConfirmed=true;context.step='confirmation';save();renderBreachSarcophagusStep(stage);};
      $('#breachBackToControl').onclick=()=>{context.enemyControlRangeConfirmed=null;context.step='control-range';save();renderBreachSarcophagusStep(stage);};
      return;
    }
    const total=Number(objectiveEngine?.getObjectiveValue('destructionPoints')||state.missionState?.destruction||0);
    showModal('Breach Sarcophagus',`<div class="summary-box"><strong>${escapeHtml(playerName(context.operativeId))}</strong><br>AP available: ${context.remainingAp}<br>Breach AP cost: ${context.apCost}<br>Destruction Points: ${total} / 20</div><p>Spend ${context.apCost} AP and roll 2D6. Add the total to the sarcophagus’s Destruction Points.</p><div class="wizard-actions breach-navigation"><button class="btn primary" id="performBreach">Perform Breach</button></div><div class="wizard-actions breach-navigation"><button class="btn ghost" id="breachBackToEnemy" aria-label="Back to the enemy control-range question">Back</button></div>`,undefined,'breach-confirmation');
    $('#breachBackToEnemy').onclick=()=>{context.enemyControlRangeConfirmed=null;context.step='enemy-control-range';save();renderBreachSarcophagusStep(stage);};
    $('#performBreach').onclick=()=>performBreachSarcophagus(stage);
  }

  async function performBreachSarcophagus(stage,resume=false){
    const context=state.missionActionContext,button=$('#performBreach');
    if(button)button.disabled=true;
    if(!context||context.newTotal!=null||context.operativeId!==stage.playerOperativeId||context.activationId!==missionActivationId('player',stage.playerOperativeId))return;
    if(!context.controlRangeConfirmed||!context.enemyControlRangeConfirmed)return clearPendingBreach(stage);
    if(!context.committed){
      if(Number(stage.apl||3)-playerActionCost(stage)<context.apCost){showToast('Not enough AP to Breach the sarcophagus.');return clearPendingBreach(stage);}
      context.committed=true;context.diceRolled=true;context.dice=[roll(),roll()];context.step='result';
      stage.missionBreachCommitted=true;stage.missionBreachCost=context.apCost;
      state.combatState={side:'player',stage:{...stage}};save();
    }
    const outcome=await runMissionEvent(()=>objectiveEngine.executeMissionAction('breachSarcophagus',{...missionLifecycleContext({activationId:context.activationId,operativeId:context.operativeId}),side:'player',remainingAp:context.remainingAp,apCost:context.apCost,controlRangeConfirmed:true,enemyControlRangeConfirmed:true,missionDice:context.dice}));
    if(!outcome)return;
    const change=outcome.changes[0];context.previousTotal=change.before;context.newTotal=change.after;
    state.missionState.destruction=change.after;
    stage.missionBreachRecord={operativeId:context.operativeId,activationId:context.activationId,apCost:context.apCost,dice:[...context.dice],previousTotal:change.before,newTotal:change.after};
    state.combatState={side:'player',stage:{...stage}};
    log(`${playerName(context.operativeId)} performed Breach Sarcophagus for ${context.apCost} AP. Rolled ${context.dice.join(' and ')} and added ${change.after-change.before} Destruction Points: ${change.before} to ${change.after}.`);
    save();
    const won=change.after>=20;
    if(won&&!state.gameEnd){
      context.previousPhase=state.phase;
      context.victoryCommitted=true;
      state.gameEnd='victory';state.completed=true;state.phase='end';
      state.finalResolution=state.finalResolution||{};
      save();
    }
    showModal(won?'MISSION OBJECTIVE COMPLETE':'BREACH SARCOPHAGUS',`<div class="mission-roll-result"><div class="dice-row settled">${context.dice.map(value=>dieHtml({value})).join('')}</div><p>Dice: ${context.dice.join(' + ')} · Total: ${context.dice.reduce((sum,value)=>sum+value,0)}</p><p>Destruction Points added: ${change.after-change.before}</p><div class="summary-box"><strong>Progress: ${change.after} / 20 Destruction Points</strong></div>${won?'<p>The sarcophagus has been destroyed. The Player team is victorious.</p>':''}</div><div class="wizard-actions"><button class="btn primary" id="breachResultContinue">${won?'View Victory':'Return to Activation'}</button></div>`);
    $('#breachResultContinue').onclick=()=>{
      if(won){void finalizeMissionCompletion('victory',context.previousPhase||'firefight');}
      else {state.missionActionContext=null;save();showPlayerActivation(stage);}
    };
  }

  function confirmMissionAction(){
    const action=objectiveDefinition?.actions?.[0];
    if(!action){console.warn('[MissionEngine] No mission action is available.');return;}
    const dice=action.operations.find(operation=>operation.type==='requestDiceRoll')?.dice;
    const diceLabel=dice?`${dice.count}D${dice.sides}`:'Dice';
    showMissionConfirmation({...action.confirmation,description:action.description,confirmLabel:`Roll ${diceLabel}`},async()=>{
      closeModal();
      const outcome=await runMissionEvent(()=>objectiveEngine.executeMissionAction(action.id,{turningPoint:state.turningPoint,phase:state.phase}));
      if(!outcome)return;
      save();log(`${action.label}: progress changed from ${outcome.changes[0].before} to ${outcome.changes[0].after}.`);render();showMissionResult(action.label.toUpperCase(),outcome);
    });
  }

  function isUsableFocusTarget(element){
    if(!element||element.hidden||element.disabled||element.getAttribute('aria-hidden')==='true')return false;
    if(element.closest('[hidden],[inert],[aria-hidden="true"]'))return false;
    const collapsedDetails=element.closest('details:not([open])');
    if(collapsedDetails&&!collapsedDetails.querySelector(':scope > summary')?.contains(element))return false;
    const style=getComputedStyle(element);
    return style.display!=='none'&&style.visibility!=='hidden';
  }

  let modalFocusGeneration=0;
  function focusInitialDialogControl(dialog,focusContainerOnTouch=false,focusGeneration=modalFocusGeneration){
    if(!dialog)return;
    const selectors='select:not([disabled]),input:not([disabled]),textarea:not([disabled]),button:not([disabled]),a[href],[role="button"][tabindex="0"]';
    const preferred=$$('[data-dialog-focus]:not([disabled])',dialog).find(isUsableFocusTarget);
    const firstInteractive=$$(selectors,dialog).find(isUsableFocusTarget);
    const coarsePointer=window.matchMedia('(hover: none) and (pointer: coarse)').matches;
    const target=focusContainerOnTouch&&coarsePointer?dialog:preferred||firstInteractive||dialog;
    requestAnimationFrame(()=>{
      if(focusGeneration!==modalFocusGeneration||!target?.isConnected)return;
      try{target.focus({preventScroll:true});}catch{target.focus();}
    });
  }

  function restoreDialogControlFocus(dialog,controlId,focusGeneration=modalFocusGeneration){
    if(!controlId)return;
    requestAnimationFrame(()=>{
      if(focusGeneration!==modalFocusGeneration)return;
      const target=document.getElementById(controlId);
      if(!dialog.contains(target)||!isUsableFocusTarget(target))return;
      try{target.focus({preventScroll:true});}catch{target.focus();}
    });
  }

  function closeTouchSelectAfterCommit(select,onComplete){
    const coarsePointer=window.matchMedia('(hover: none) and (pointer: coarse)').matches;
    if(!coarsePointer){onComplete();return;}
    const focusGeneration=modalFocusGeneration;
    requestAnimationFrame(()=>{
      if(focusGeneration!==modalFocusGeneration||!modal.open)return;
      if(document.activeElement===select)select.blur();
      onComplete();
    });
  }

  let modalFocusSequence=0;
  function showModal(title,content,onClose,focusKey=null){
    const focusGeneration=++modalFocusGeneration;
    const active=document.activeElement;
    if(active&&!modal.contains(active))modal._returnFocus=active;
    const activeControlId=modal.contains(active)?active.id:null;
    const nextFocusKey=focusKey??++modalFocusSequence;
    const shouldFocus=!modal.open||modal._focusKey!==nextFocusKey;
    const shouldRestoreFocus=modal._skipFocusRestoreId!==activeControlId;
    modal._skipFocusRestoreId=null;

    modal.classList.remove('combat-resolution-modal');
    modalBody.innerHTML=`<div class="modal-inner"><h2 id="modalTitle">${escapeHtml(title)}</h2>${content}</div>`;
    modal.setAttribute('aria-labelledby','modalTitle');
    modal.setAttribute('tabindex','-1');
    if(!modal.open)modal.showModal();
    modal._focusKey=nextFocusKey;
    modal._onClose=onClose;
    $$('[data-close]',modal).forEach(b=>b.onclick=closeModal);
    renderOperativeStatusPanel();

    modal.scrollTop=0;
    modalBody.scrollTop=0;
    if(shouldFocus){
      if(modal.querySelector('[data-touch-dialog-focus-container]'))focusInitialDialogControl(modal,true,focusGeneration);
      else focusInitialDialogControl(modal);
    }
    else if(shouldRestoreFocus)restoreDialogControlFocus(modal,activeControlId);
  }
  function closeModal(){
    const focusGeneration=++modalFocusGeneration;
    missionDialogLocked=false;
    if(modal.open)modal.close();
    const cb=modal._onClose;
    const returnFocus=modal._returnFocus;
    const returnFocusId=returnFocus?.id;
    modal._onClose=null;
    modal._returnFocus=null;
    modal._focusKey=null;
    modal._skipFocusRestoreId=null;
    if(cb)cb();
    if(returnFocus?.isConnected||returnFocusId)requestAnimationFrame(()=>{
      if(focusGeneration!==modalFocusGeneration||modal.open)return;
      const target=returnFocus.isConnected?returnFocus:document.getElementById(returnFocusId);
      if(target?.isConnected)target.focus({preventScroll:true});
    });
  }
  modal.addEventListener('cancel',e=>{e.preventDefault();if(!missionDialogLocked)closeModal();});
  modal.addEventListener('keydown',event=>{
    if(event.key!=='Tab')return;
    const controls=$$('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[href],[role="button"][tabindex="0"]',modal).filter(isUsableFocusTarget);
    if(!controls.length){event.preventDefault();modal.focus();return;}
    const first=controls[0],last=controls.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  });

  function showToast(text){toast.textContent=text;toast.hidden=false;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toast.hidden=true,6500);}
  function deadlyFeatureNames(ids){return (ids||[]).map(id=>DeadlyEncounters.features.find(feature=>feature.id===id)?.name).filter(Boolean);}
  function deadlyStableId(prefix){return `${prefix}-${globalThis.crypto?.randomUUID?.()||`${Date.now().toString(36)}-${state.deadlyEncountersState.resolutionHistory.length.toString(36)}`}`;}
  function deadlyEntityList(records,emptyText){
    const entries=Object.values(records||{});
    if(!entries.length)return `<p class="muted">${escapeHtml(emptyText)}</p>`;
    return `<ul class="deadly-entity-list">${entries.map(entity=>{const names=deadlyFeatureNames(entity.featureIds);return `<li><strong>${escapeHtml(entity.label)}</strong><span class="feature-status">${names.length?`Active — ${names.map(escapeHtml).join(' + ')}`:`${entity.eligible?'Eligible':'Not unexplored'} — unresolved`}</span>${names.length?`<small>Revealed in Turning Point ${entity.turningPoint||'—'}. ${escapeHtml(entity.featureIds.map(id=>DeadlyEncounters.features.find(feature=>feature.id===id)?.summary).filter(Boolean).join(' '))}</small>`:''}</li>`;}).join('')}</ul>`;
  }
  function deadlyOperativeOptions(){
    const players=selectedPlayerOperatives().filter(operative=>playerCurrentWounds(operative.id)>0).map(operative=>({id:operative.id,label:`Player — ${playerName(operative.id)}`}));
    const npos=activeNpos().map(operative=>({id:operative.id,label:`NPO — ${npoName(operative)}`}));
    return [...players,...npos];
  }
  function showDeadlyEncountersPanel(){
    const de=state.deadlyEncountersState,locations=Object.entries(de.operativeLocations).filter(([,roomId])=>roomId);
    showModal('Deadly Encounters: Tomb Worlds',`<p><strong>Status:</strong> ${state.deadlyEncountersEnabled?'On':'Off'} · <span class="rule-classification official">Official Expansion - White Dwarf 521</span></p>${state.deadlyEncountersEnabled?`<section class="deadly-section"><h3>Rooms</h3>${deadlyEntityList(de.rooms,'No rooms registered.')}</section><section class="deadly-section"><h3>Eligible markers</h3>${deadlyEntityList(de.objectives,'No markers registered.')}${Object.keys(de.objectives).length>3?'<p class="nonblocking-note">More than three markers are registered. Three is an official recommendation, not a limit.</p>':''}</section><section class="deadly-section"><h3>Operative room locations</h3>${locations.length?`<ul>${locations.map(([operativeId,roomId])=>`<li>${escapeHtml(deadlyOperativeOptions().find(item=>item.id===operativeId)?.label||operativeId)} — ${escapeHtml(de.rooms[roomId]?.label||'Outside registered rooms')}</li>`).join('')}</ul>`:'<p class="muted">No battlefield room locations recorded.</p>'}</section><section class="deadly-section"><h3>Active and pending effects</h3><p>${de.temporaryEffects.length?`${de.temporaryEffects.length} temporary effect(s) active.`:'No temporary effects.'}</p><p>${de.pendingResolution?'A mandatory resolution is pending.':'No resolution pending.'}</p></section><div class="game-menu-grid"><button class="btn primary" id="recordDeadlyEncounter">Record Deadly Encounter</button><button class="btn secondary" id="registerDeadlyRoom">Register Room</button><button class="btn secondary" id="registerDeadlyObjective">Register Marker</button><button class="btn secondary" id="updateDeadlyLocation">Update Room Location</button><button class="btn secondary" id="updateDeadlyCarrier">Update Carried Marker</button><button class="btn ghost" id="correctDeadlyRecord">Correct Location or Encounter</button></div>`:'<p>Deadly Encounters is disabled for this battle. No feature prompts or effects apply.</p>'}<p class="source-note">Concise play aid based on White Dwarf 521, February 2026. Consult the official publication for authoritative wording.</p><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`);
    if(!state.deadlyEncountersEnabled)return;
    $('#registerDeadlyRoom').onclick=showRegisterDeadlyRoom;
    $('#registerDeadlyObjective').onclick=showRegisterDeadlyObjective;
    $('#recordDeadlyEncounter').onclick=showRecordDeadlyEncounter;
    $('#updateDeadlyLocation').onclick=showUpdateDeadlyLocation;
    $('#updateDeadlyCarrier').onclick=showUpdateDeadlyCarrier;
    $('#correctDeadlyRecord').onclick=showCorrectDeadlyRecord;
  }
  function showRegisterDeadlyRoom(){
    showModal('Register Unexplored Room',`<div class="field"><label for="deadlyRoomLabel">Room label</label><input id="deadlyRoomLabel" maxlength="60" placeholder="Northern Chamber"></div><div class="field"><label for="deadlyDropZone">Drop-zone classification</label><select id="deadlyDropZone"><option value="none">No drop zone</option><option value="player">Player drop zone</option><option value="npo">NPO drop zone</option><option value="both">Both drop zones</option></select></div><p class="muted">Rooms with no drop zone, an NPO drop zone, or both drop zones are unexplored. A Player-only drop-zone room is not.</p><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn primary" id="confirmDeadlyRoom">Register Room</button></div>`);
    $('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;$('#confirmDeadlyRoom').onclick=()=>{const label=$('#deadlyRoomLabel').value.trim();if(!label){showToast('Enter a room label.');return;}const id=deadlyStableId('room');state.deadlyEncountersState=DeadlyEncounters.registerRoom(state.deadlyEncountersState,{id,label,missionId:state.missionId,dropZone:$('#deadlyDropZone').value});log(`Deadly Encounters: registered room ${label}.`);save();showDeadlyEncountersPanel();};
  }
  function showRegisterDeadlyObjective(){
    showModal('Register Eligible Marker',`<div class="field"><label for="deadlyObjectiveLabel">Objective or mission marker label</label><input id="deadlyObjectiveLabel" maxlength="60" placeholder="Objective A"></div><p>Register only markers the player declares eligible. The recommendation of three markers is not a hard limit.</p><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn primary" id="confirmDeadlyObjective">Register Marker</button></div>`);
    $('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;$('#confirmDeadlyObjective').onclick=()=>{const label=$('#deadlyObjectiveLabel').value.trim();if(!label){showToast('Enter a marker label.');return;}const id=deadlyStableId('marker');state.deadlyEncountersState=DeadlyEncounters.registerObjective(state.deadlyEncountersState,{id,label,missionId:state.missionId,eligible:true});log(`Deadly Encounters: registered eligible marker ${label}.`);save();showDeadlyEncountersPanel();};
  }
  function showRecordDeadlyEncounter(){
    const de=state.deadlyEncountersState,roomOptions=Object.values(de.rooms).filter(room=>room.eligible&&!room.featureIds.length),objectiveOptions=Object.values(de.objectives).filter(marker=>marker.eligible&&!marker.featureIds.length),operatives=deadlyOperativeOptions();
    showModal('Record Deadly Encounter',`<p>Only a Player operative can reveal a feature. Room entry interrupts movement; resolve the feature before completing affected movement.</p><div class="field"><label for="deadlyTrigger">Discovery trigger</label><select id="deadlyTrigger"><option value="opened">Opened an unexplored room</option><option value="entered">Entered an unexplored room</option><option value="contested">First contested an eligible marker</option><option value="controlled">First controlled an eligible marker</option></select></div><div class="field"><label for="deadlyEntity">Room or marker</label><select id="deadlyEntity"></select></div><div class="field"><label for="deadlyOperative">Triggering Player operative</label><select id="deadlyOperative"><option value="">Select operative</option>${operatives.filter(item=>item.label.startsWith('Player')).map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn primary" id="confirmDeadlyDiscovery">Roll official D33</button></div>`);
    const refresh=()=>{const room=['opened','entered'].includes($('#deadlyTrigger').value),items=room?roomOptions:objectiveOptions;$('#deadlyEntity').innerHTML=items.length?items.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join(''):'<option value="">No unresolved eligible record</option>';};refresh();$('#deadlyTrigger').onchange=refresh;$('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;
    $('#confirmDeadlyDiscovery').onclick=()=>{const triggerType=$('#deadlyTrigger').value,entityId=$('#deadlyEntity').value,operativeId=$('#deadlyOperative').value;if(!entityId||!operativeId){showToast('Select an unresolved record and Player operative.');return;}const room=['opened','entered'].includes(triggerType),actionId=`manual-${Date.now().toString(36)}`,context={missionId:state.missionId,turningPoint:state.turningPoint,activationId:`tp${state.turningPoint}-a${state.activationNumber}`,actionId,actionType:'manual-record',actingSide:'player',operativeId,triggerType,...(room?{roomId:entityId,entityType:'room',entityId}:{objectiveId:entityId,entityType:'objective',entityId})};const result=DeadlyEncounters.discover(state.deadlyEncountersState,true,context);state.deadlyEncountersState=result.state;result.attempts?.forEach(attempt=>log(`Deadly Encounters D33 ${attempt.result}: ${attempt.status}${attempt.reason?` — ${attempt.reason}`:''}`));const names=deadlyFeatureNames(result.featureIds);log(`Deadly Encounters: ${room?'room':'marker'} ${result.entity?.label||entityId} revealed ${names.join(' and ')||result.message}.`);save();showDeadlyResult(result,room,triggerType);};
  }
  function showDeadlyResult(result,isRoom,triggerType){
    const names=deadlyFeatureNames(result.featureIds),features=result.featureIds.map(id=>DeadlyEncounters.features.find(feature=>feature.id===id)).filter(Boolean);
    showModal(result.exhausted?'Official Table Exhausted':'Deadly Encounter Revealed',`<p class="d33-result" aria-label="D33 results ${result.attempts.map(attempt=>attempt.result).join(', ')}"><strong>D33:</strong> ${result.attempts.map(attempt=>`<span>${attempt.result}</span>`).join(' ')}</p>${names.length?`<h3>${names.map(escapeHtml).join(' + ')}</h3><ol class="resolution-steps">${features.map(feature=>`<li><strong>${escapeHtml(feature.automation)}</strong>: ${escapeHtml(feature.summary)}</li>`).join('')}</ol>`:`<p>${escapeHtml(result.message)}</p>`}${isRoom&&triggerType==='entered'?'<p><strong>Resume movement now</strong>, applying the revealed rule to the remaining action.</p>':''}<p class="source-note">Consult White Dwarf 521 for authoritative wording.</p><div class="wizard-actions"><button class="btn primary" id="ackDeadlyResult">Acknowledge and Continue</button></div>`);$('#ackDeadlyResult').onclick=showDeadlyEncountersPanel;
  }
  function showUpdateDeadlyLocation(){
    const rooms=Object.values(state.deadlyEncountersState.rooms),operatives=deadlyOperativeOptions();showModal('Update Operative Room Location',`<div class="field"><label for="deadlyLocationOperative">Deployed living operative</label><select id="deadlyLocationOperative">${operatives.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join('')}</select></div><div class="field"><label for="deadlyLocationRoom">Current room</label><select id="deadlyLocationRoom"><option value="">Outside registered rooms</option>${rooms.map(room=>`<option value="${escapeHtml(room.id)}">${escapeHtml(room.label)}</option>`).join('')}</select></div><p class="muted">Use after Reposition, Dash, Charge, Fall Back, teleportation, or NPO movement. Pause first if a Player operative enters an unexplored room.</p><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn primary" id="confirmDeadlyLocation">Save Location</button></div>`);$('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;$('#confirmDeadlyLocation').onclick=()=>{const operativeId=$('#deadlyLocationOperative').value,roomId=$('#deadlyLocationRoom').value||null;if(!operativeId)return;state.deadlyEncountersState.operativeLocations[operativeId]=roomId;log(`Deadly Encounters: corrected room location for ${deadlyOperativeOptions().find(item=>item.id===operativeId)?.label||operativeId}.`);save();showDeadlyEncountersPanel();};
  }
  function showUpdateDeadlyCarrier(){
    const markers=Object.values(state.deadlyEncountersState.objectives),operatives=deadlyOperativeOptions();showModal('Update Carried Marker',`<div class="field"><label for="deadlyCarrierMarker">Objective or mission marker</label><select id="deadlyCarrierMarker">${markers.map(marker=>`<option value="${escapeHtml(marker.id)}">${escapeHtml(marker.label)}</option>`).join('')}</select></div><div class="field"><label for="deadlyCarrierOperative">Current carrier</label><select id="deadlyCarrierOperative"><option value="">Not carried</option>${operatives.map(item=>`<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join('')}</select></div><p class="muted">The feature remains attached when the marker is picked up, dropped, or transferred. Measure from the carrier while carried.</p><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn primary" id="confirmDeadlyCarrier">Save Carrier</button></div>`);$('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;$('#confirmDeadlyCarrier').onclick=()=>{const marker=state.deadlyEncountersState.objectives[$('#deadlyCarrierMarker').value];if(!marker)return;marker.carrierId=$('#deadlyCarrierOperative').value||null;log(`Deadly Encounters: ${marker.label} is ${marker.carrierId?'now carried':'no longer carried'}.`);save();showDeadlyEncountersPanel();};
  }
  function showCorrectDeadlyRecord(){showModal('Correct Location or Encounter',`<p>Location corrections can be recorded directly. To correct a committed encounter, record a note; damage, movement, dice, and model placement are not silently reversed.</p><div class="field"><label for="deadlyCorrection">Correction note</label><textarea id="deadlyCorrection" rows="4" maxlength="300"></textarea></div><label class="check-row"><input id="confirmPhysicalCorrection" type="checkbox"><span>I understand physical tabletop effects may require manual reversal.</span></label><div class="wizard-actions"><button class="btn ghost" id="backDeadlyPanel">Cancel</button><button class="btn danger" id="confirmDeadlyCorrection">Record Correction</button></div>`);$('#backDeadlyPanel').onclick=showDeadlyEncountersPanel;$('#confirmDeadlyCorrection').onclick=()=>{const note=$('#deadlyCorrection').value.trim();if(!note||!$('#confirmPhysicalCorrection').checked){showToast('Enter a note and confirm the tabletop warning.');return;}state.deadlyEncountersState.resolutionHistory.push({type:'correction',note,time:new Date().toISOString()});log(`Deadly Encounters correction: ${note}`);save();showDeadlyEncountersPanel();};}
  function isNewGameSetupActive(){return state.screen==='setup';}
  function isBattleComplete(){return state.screen==='game'&&Boolean(state.gameEnd||state.finalResolution?.pending);}
  function isGuidedPlayActive(){return state.screen==='game'&&!isBattleComplete();}
  function canOpenHelp(){return isNewGameSetupActive()||isGuidedPlayActive()||isBattleComplete();}
  function openHelpFromGameMenu(){
    closeModal();
    renderHelp();
    app.insertAdjacentHTML('afterbegin',`<div class="reference-return"><button class="btn primary" id="returnToGameMenu">Return to Game Menu</button><small>Reference screens do not change setup or guided play.</small></div>`);
    $('#returnToGameMenu').onclick=()=>{
      showGameMenu();
      requestAnimationFrame(()=>$('#menuHelp')?.focus({preventScroll:true}));
    };
  }
  function showGameMenu(){
    const inGame=state.screen==='game';
    showModal('Game Menu',`<p>Open a reference screen without changing the guided play sequence, or begin a completely new game.</p>
      <div class="game-menu-grid">
        <button class="btn primary" data-game-view="play">Return to Guided Play</button>
        ${inGame?`<button class="btn secondary" id="menuMissionDetails">Mission Details</button>
        <button class="btn secondary" id="menuDeadlyEncounters">Deadly Encounters</button>
        <button class="btn secondary" data-game-view="mission">Mission & Map</button>
        <button class="btn secondary" data-game-view="roster">NPO Roster</button>
        <button class="btn secondary" data-game-view="player-roster">Player Roster</button>
        <button class="btn secondary" data-game-view="journal">Battle Journal</button>`:''}
        ${canOpenHelp()?'<button class="btn secondary" id="menuHelp" type="button">Help</button>':''}
        <button class="btn secondary" id="menuAbout" type="button">About</button>
      </div>
      <div class="game-menu-session">
        <button class="btn ghost" id="menuExportSave">Export Save</button>
        <button class="btn ghost" id="menuImportSave">Import Save</button>
        <button class="btn danger" id="menuNewGame">Start New Game</button>
      </div>`);
    $$('[data-game-view]',modal).forEach(button=>button.onclick=()=>{
      if(inGame){state.tab=button.dataset.gameView;save();}
      closeModal();
      render();
    });
    if(inGame){
      $('#menuMissionDetails').onclick=showMissionDetails;
      $('#menuDeadlyEncounters').onclick=showDeadlyEncountersPanel;
    }
    if(canOpenHelp())$('#menuHelp').onclick=openHelpFromGameMenu;
    $('#menuAbout').onclick=showAbout;
    $('#menuExportSave').onclick=exportSave;
    $('#menuImportSave').onclick=()=>importInput.click();
    $('#menuNewGame').onclick=confirmNewGame;
  }

  function showAbout(){
    showModal('About',`<div class="about-intro">
        <p class="about-app-name">Tomb World Solo Guide</p>
        <p class="screen-version">Version ${APP_VERSION}</p>
        <p><strong>Created by J.R. Benning</strong></p>
        <p>Tomb World Solo Guide is a free, unofficial, fan-created companion for managing solo tabletop play. It is not a replacement for the official rules, publications, miniatures, terrain, cards, or other materials required to play.</p>
      </div>
      <div class="about-content">
        <section><h3>Project Status</h3><p>This project is provided without charge and is not operated for commercial gain.</p></section>
        <section><h3>Games Workshop Notice</h3><p>Tomb World Solo Guide is an unofficial fan-created project. It is not affiliated with, endorsed by, sponsored by, licensed by, or approved by Games Workshop Limited or any of its affiliates.</p><p>Games Workshop, Warhammer, Warhammer 40,000, Kill Team, Necron, Tomb World, and all associated names, logos, characters, factions, settings, artwork, and distinctive likenesses are trademarks, copyrights, or other intellectual property of Games Workshop Limited and/or its licensors.</p><p>All such intellectual property remains the property of its respective owners. No challenge to any ownership, trademark, copyright, or other proprietary right is intended.</p></section>
        <section><h3>Official Rules and Materials</h3><p>This application is intended only as an organizational and gameplay aid for players who own or otherwise have lawful access to the required official products and rules.</p><p>It does not grant access to, replace, or authorize reproduction of any Games Workshop rulebook, publication, data card, mission pack, image, artwork, model, terrain component, or other official material.</p><p>Players are responsible for consulting the current official rules, errata, balance updates, and publications. If this application conflicts with an official Games Workshop source, the official source controls.</p><p>No part of this application should be interpreted as legal permission to copy, distribute, publish, or commercially exploit Games Workshop intellectual property.</p></section>
        <section><h3>Project Content</h3><p>Original application code, interface design, and original project content are created by J.R. Benning except where otherwise stated.</p><p>Third-party names and references are used solely to identify the games, products, rules, and fictional elements with which this unofficial companion is intended to be used.</p><p>Any third-party material remains subject to the rights and terms of its respective owner.</p></section>
        <section><h3>Software Disclaimer</h3><p>This application is provided &quot;as is&quot; and &quot;as available,&quot; without warranties of any kind, express or implied, including warranties of accuracy, completeness, reliability, merchantability, fitness for a particular purpose, availability, compatibility, or non-infringement.</p><p>Use of this application is at the user’s own risk. The author does not guarantee that the application is error-free, that its interpretation of any rule is correct, or that saved data will always remain available or compatible.</p><p>To the fullest extent permitted by applicable law, the author will not be liable for any direct, indirect, incidental, consequential, special, exemplary, or other damages arising from use of, inability to use, or reliance on this application.</p><p>Nothing in this notice excludes or limits liability where doing so would be prohibited by applicable law.</p></section>
        <section><h3>User Responsibility</h3><p>Users are responsible for verifying gameplay decisions against the official rules and for ensuring that their use of this application and any related materials complies with applicable laws and the terms imposed by the relevant rights holders.</p></section>
        <section><h3>Privacy</h3><p>Tomb World Solo Guide does not intentionally collect or transmit personal information. Game state and preferences are stored locally in the user’s browser unless the user explicitly exports or shares them.</p><p class="muted">The app is hosted on GitHub Pages, whose server request logs are governed by GitHub’s own practices. The app uses no analytics, advertising, tracking, cookies, external fonts, or third-party APIs.</p></section>
        <section><h3>Contact</h3><p>Questions, corrections, attribution concerns, or rights-holder requests may be submitted through the project’s GitHub repository.</p><p>The author intends to address good-faith attribution, ownership, or rights-holder concerns promptly.</p><a class="btn secondary external-link" href="https://github.com/ImTheKeyMaster/TombWorldSoloGuide" target="_blank" rel="noopener noreferrer">Open Project Repository <span aria-hidden="true">↗</span><span class="sr-only"> (opens in a new tab)</span></a></section>
      </div>
      <div class="wizard-actions about-footer"><button class="btn primary" id="aboutBack" type="button">Back</button></div>`);
    $('#aboutBack').onclick=()=>{
      showGameMenu();
      requestAnimationFrame(()=>$('#menuAbout')?.focus({preventScroll:true}));
    };
  }

  function startNewGameSetup(){
    document.documentElement.classList.remove('desktop-game-background');
    gameBackground.style.backgroundImage='none';
    loadedBackgroundFilename=null;
    loadingBackgroundFilename=null;
    localStorage.removeItem(STORAGE_KEY);
    state=initialState();
    state.screen='setup';
    state.setupStep=0;
    ensureGameBackgroundSelection();
    objectiveEngine=null;
    objectiveDefinition=null;
    missionActivationStarts.clear();
    expandedRosterCategories=null;
    save();
    updateGameBackground();
    render();
  }
  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{closeModal();startNewGameSetup();};}
  function exportSave(){if(objectiveEngine)state.missionRuntime=objectiveEngine.getMissionRuntime();const blob=new Blob([JSON.stringify(createPersistedSave(state),null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-solo-guide-save.json';a.click();URL.revokeObjectURL(a.href);}
  function migrationDetails(report){
    const details=[];
    if(report.aliasesApplied.length)details.push(`${report.aliasesApplied.length} legacy NPO ${report.aliasesApplied.length===1?'name was':'names were'} updated.`);
    if(report.instanceNamesRepaired.length)details.push(`${report.instanceNamesRepaired.length} missing NPO instance ${report.instanceNamesRepaired.length===1?'name was':'names were'} repaired.`);
    if(report.loadoutsNormalized.length)details.push(`${report.loadoutsNormalized.length} missing or legacy ${report.loadoutsNormalized.length===1?'loadout was':'loadouts were'} assigned a supported value.`);
    if(report.woundsClamped.length)details.push(`${report.woundsClamped.length} invalid wound ${report.woundsClamped.length===1?'value was':'values were'} corrected.`);
    if(report.pendingStateCleared.length)details.push('An unresolved action was returned to a stable game screen; committed wounds and effects were preserved.');
    return details.map(detail=>`<li>${escapeHtml(detail)}</li>`).join('');
  }
  function showMigrationNotice(report){
    showModal('NPO roster updated for v7',`<p>This save was updated to the current Tomb World NPO system. Known legacy names and loadouts were normalized, and obsolete NPO portrait and Obelisk Node Matrix fields were removed where present.</p>${migrationDetails(report)?`<ul>${migrationDetails(report)}</ul>`:''}<p>The game can continue.</p><div class="wizard-actions"><button class="btn primary" data-close>Continue</button></div>`);
  }
  function hasMeaningfulMigrationChanges(report){
    return report?.outcome==='migrated'&&Boolean(report.aliasesApplied.length||report.instanceNamesRepaired.length||report.instanceIdsCreated.length||report.instanceIdsRepaired.length||report.loadoutsNormalized.length||report.woundsClamped.length||report.portraitFieldsRemoved||report.matrixFieldsRemoved||report.temporaryEffectsRemoved||report.pendingStateCleared.length);
  }
  async function commitImported(candidate,report){
    const previous=state;
    try{state=normalizeState(candidate);state.screen=report.requiresRegeneration?'setup':'game';await loadObjectiveMission();ensureGameBackgroundSelection();if(!save())throw new Error('Browser storage rejected the migrated save.');render();return true;}
    catch(error){state=previous;await loadObjectiveMission();console.warn('[Persistence] Migrated import was not committed.',error);showToast('The imported save could not be committed; the current game is unchanged.');return false;}
  }
  function showRegenerationNotice(migration,source){
    const causes=[...migration.report.unsupportedRetiredTypes,...migration.report.invalidPhysicalLimits,...migration.report.errors];
    showModal('Current battle cannot be resumed',`<p>The current battle uses retired or invalid NPO data and cannot be resumed safely.</p>${causes.length?`<p><strong>Cause:</strong> ${causes.map(escapeHtml).join('; ')}</p>`:''}<p>The battle will return to setup and a new legal NPO roster must be generated. The selected mission, player team and roster choices, completed battle history, settings, and preferences will be preserved where possible.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmLegacyReset">Return to Setup</button></div>`);
    $('#confirmLegacyReset').onclick=async()=>{
      const reset=resetActiveBattle(migration.state);closeModal();
      if(await commitImported(reset,{...migration.report,requiresRegeneration:true}))showToast(source==='import'?'Save imported and returned to setup.':'Legacy battle returned to setup.');
    };
  }
  importInput.addEventListener('change',async()=>{
    const f=importInput.files?.[0];if(!f)return;
    try{
      const data=JSON.parse(await f.text()),migration=migrateSaveDetailed(data,npoDefinitions);
      if(migration.report.requiresRegeneration){showRegenerationNotice(migration,'import');return;}
      if(await commitImported(migration.state,migration.report)){
        if(hasMeaningfulMigrationChanges(migration.report))showMigrationNotice(migration.report);else showToast('Save imported.');
      }
    }catch(error){console.warn('[Persistence] Imported save could not be migrated; browser progress was left unchanged.',error);showToast(error.message?.includes('newer than supported')?'That save was created by a newer unsupported version.':'That file is not a valid Tomb World Solo Guide save.');}
    finally{importInput.value='';}
  });

  function bindCommon(){
    const versionBadge=$('.version');
    if(versionBadge) versionBadge.textContent=`v${APP_VERSION}`;
    gameMenuBtn.onclick=showGameMenu;
  }

  function renderStartupRecovery(error){
    console.error('[Startup] Application restoration could not continue.',error);
    app.innerHTML=`<section class="card startup-recovery" role="alert"><p class="eyebrow">RECOVERY</p><h2>Your saved game could not be loaded</h2><p>Your stored save has been preserved. Retry loading, or export a backup before troubleshooting.</p><div class="wizard-actions"><button class="btn primary" id="retryStartup">Retry Loading</button><button class="btn ghost" id="exportStoredSave">Export Save</button></div></section>`;
    $('#retryStartup').onclick=()=>window.location.reload();
    $('#exportStoredSave').onclick=()=>{
      const stored=localStorage.getItem(STORAGE_KEY);
      if(!stored){showToast('No stored save is available to export.');return;}
      const blob=new Blob([stored],{type:'application/json'}),link=document.createElement('a');
      link.href=URL.createObjectURL(blob);link.download='tomb-world-solo-guide-recovery-save.json';link.click();URL.revokeObjectURL(link.href);
    };
    bindCommon();
  }

  if(startupInitializationError)renderStartupRecovery(startupInitializationError);
  else Promise.all([loadMissionPack(),loadPlayerManifest(),loadBackgroundManifest()])
    .then(async ([,manifest])=>{
      await loadObjectiveMission();
      recoverInvalidMission();
      if(['setup','game'].includes(state.screen)){
        const previousBackground=state.backgroundSelection?.landscape;
        ensureGameBackgroundSelection();
        if(state.backgroundSelection?.landscape!==previousBackground)save();
      }
      const teams=manifest.teams||[];
      if(teams.length===1){
        state.playerTeamId=teams[0].id;
        try{await loadPlayerTeamData(teams[0].id);}catch(error){console.error(error);}
      }else if(state.playerTeamId&&teams.some(team=>team.id===state.playerTeamId)){
        try{await loadPlayerTeamData(state.playerTeamId);}catch(error){console.error(error);}
      }else{
        state.playerTeamId='';
        state.playerTeamFile='';
        playerTeamData=null;
      }
      state.missionState=normalizeMissionState(state.missionState,missionDefinition(state.missionId),state.tracker);
      if(state.finalResolution?.invalidSaveCorrected&&state.finalResolution.pending)await resolveTurningPointLimit();
      else render();
      if(pendingStoredMigration)showRegenerationNotice(pendingStoredMigration,'storage');
      else if(!storedMigrationNoticeShown&&hasMeaningfulMigrationChanges(loadedSave?.report)){
        if(save()){storedMigrationNoticeShown=true;showMigrationNotice(loadedSave.report);}
      }
    })
    .catch(error=>{
      renderStartupRecovery(error);
    });
})();
