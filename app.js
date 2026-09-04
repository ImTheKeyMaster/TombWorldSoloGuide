(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldBattleGuide.v1';
  const APP_VERSION = '9.2.38';
  const DICE_ROLL_ANIMATION_MS = 750;
  if (typeof navigator !== 'undefined' && 'mediaSession' in navigator && typeof window.MediaMetadata === 'function') {
    try {
      navigator.mediaSession.metadata = new window.MediaMetadata({
        title: 'Tomb World Battle Guide',
        artwork: [
          {src:'Assets/icon-192.png',sizes:'192x192',type:'image/png'},
          {src:'Assets/icon-512.png',sizes:'512x512',type:'image/png'},
          {src:'Assets/icon-1024.png',sizes:'1024x1024',type:'image/png'}
        ]
      });
    } catch (error) {
      console.warn('[Media Session] Now Playing artwork could not be initialized.', error);
    }
  }
  const TombWorldNarration=window.TombWorldNarration||Object.freeze({
    init:()=>Promise.resolve(),unlock:()=>Promise.resolve(false),activateFromGesture:()=>Promise.resolve(false),playMissionIntro:()=>Promise.resolve(false),playEvent:()=>Promise.resolve(false),playGradeEscalation:()=>Promise.resolve(false),playOutcome:()=>Promise.resolve(false),playDeadlyEncounter:()=>Promise.resolve(false),replayLast:()=>Promise.resolve(false),stop:()=>{},setPreferenceEnabled:()=>{},isPreferenceEnabled:()=>true,setMasterEnabled:()=>{},isMasterEnabled:()=>true,isPlaybackEnabled:()=>true,setVolumeMultiplier:()=>{},canReplay:()=>false
  });
  const TombWorldAmbient=window.TombWorldAmbient||Object.freeze({init:()=>Promise.resolve(false),playFromGesture:()=>Promise.resolve(false),setActive:()=>{},setVolumeMultiplier:()=>{},stop:()=>{},reset:()=>{},removeGestureRecovery:()=>{}});
  function createDiceSfxFallback(){
    const preferenceKey='tombWorldBattleGuide.diceRollEnabled';
    let preferenceEnabled=true;
    try{preferenceEnabled=localStorage.getItem(preferenceKey)!=='false';}
    catch{/* Missing storage keeps the documented default-on behavior. */}
    return Object.freeze({
      init:()=>Promise.resolve(false),activateFromGesture:()=>Promise.resolve(false),play:()=>Promise.resolve(false),
      setPreferenceEnabled:enabled=>{
        preferenceEnabled=Boolean(enabled);
        try{localStorage.setItem(preferenceKey,String(preferenceEnabled));}
        catch{/* The fallback preference remains active for this session. */}
      },
      isPreferenceEnabled:()=>preferenceEnabled,setMasterEnabled:()=>{},setVolumeMultiplier:()=>{},stop:()=>{}
    });
  }
  const TombWorldDiceSfx=window.TombWorldDiceSfx||createDiceSfxFallback();
  const OPERATIVE_STATUS_PREFERENCE_KEY = 'tombWorldBattleGuide.showOperativeStatus';
  const AMBIENT_ENABLED_PREFERENCE_KEY = 'tombWorldBattleGuide.ambientEnabled';
  const GAME_VOLUME_PREFERENCE_KEY = 'tombWorldBattleGuide.gameVolume';
  const BACKGROUND_MANIFEST_PATH = 'Assets/Images/Backgrounds/manifest.json';
  const BACKGROUND_IMAGE_PATH = 'Assets/Images/Backgrounds/';
  const WEAPON_RULE_HANDLERS = Object.freeze({
    'dimensional-banishment':{mode:'automatic',phase:'after-attack'},
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
    balanced:{mode:'guided',phase:'attack-reroll'},
    ceaseless:{mode:'guided',phase:'attack-reroll'},
    rending:{mode:'automatic',phase:'after-attack-roll'},
    devastating:{mode:'automatic',phase:'after-attack-roll'},
    saturate:{mode:'automatic',phase:'before-defense-roll'},
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
document.addEventListener('touchend',function(e){
  if(e.target?.closest?.('button, input, select, textarea, a, label, summary, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="switch"], [role="tab"], [role="menuitem"]'))return;
  const now=Date.now();
  if(now-lastTouchEnd<=300)e.preventDefault();
  lastTouchEnd=now;
},{passive:false});
  const MAX_NPOS = 10;
  const MAX_TURNING_POINTS = 4;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const app = $('#app');
  const appHeader = $('.app-header');
  const gameMenuBtn = $('#gameMenuBtn');
  const narrationSpeakerBtn=$('#narrationSpeakerBtn');
  const supportsInAppVolumeControl=()=>window.TombWorldAudioCapabilities?.supportsInAppVolumeControl()!==false;
  let pendingBoardSetupMissionIntro=null;
  let ambientEnabled=localStorage.getItem(AMBIENT_ENABLED_PREFERENCE_KEY)!=='false';
  function readPreferredGameVolume(){
    try{
      const saved=Number(localStorage.getItem(GAME_VOLUME_PREFERENCE_KEY));
      return Number.isFinite(saved)&&saved>=0.01&&saved<=1?saved:1;
    }catch{return 1;}
  }
  function writePreferredGameVolume(){
    try{localStorage.setItem(GAME_VOLUME_PREFERENCE_KEY,String(preferredGameVolume));}
    catch{/* Live volume control remains available when preference storage is unavailable. */}
  }
  let preferredGameVolume=readPreferredGameVolume();
  TombWorldNarration.setVolumeMultiplier(preferredGameVolume);
  TombWorldAmbient.setVolumeMultiplier(preferredGameVolume);
  TombWorldDiceSfx.setMasterEnabled(TombWorldNarration.isMasterEnabled());
  TombWorldDiceSfx.setVolumeMultiplier(preferredGameVolume);
  void TombWorldDiceSfx.init();
  void TombWorldAmbient.init();
  let appliedAmbientEnabled=TombWorldNarration.isMasterEnabled()&&ambientEnabled;
  let needsAudioGestureRecovery=false;
  let narrationGestureRecoveryRequired=false;
  let audioRecoveryHandler=null;
  const gradeNarrationInFlight=new Set();
  function shouldAmbientBeActive(){
    return TombWorldNarration.isMasterEnabled()&&appliedAmbientEnabled&&Boolean(state.missionId)&&['setup','game'].includes(state.screen);
  }
  function reconcileAmbientActiveState(){TombWorldAmbient.setActive(shouldAmbientBeActive());}
  function removeAudioGestureRecovery(){
    if(audioRecoveryHandler)document.removeEventListener('click',audioRecoveryHandler,true);
    audioRecoveryHandler=null;
    needsAudioGestureRecovery=false;
  }
  function armAudioGestureRecovery(event){
    if(event?.detail?.category==='ambient')return;
    needsAudioGestureRecovery=true;
    if(audioRecoveryHandler)return;
    audioRecoveryHandler=async()=>{
      if(!needsAudioGestureRecovery||!TombWorldNarration.isMasterEnabled()){removeAudioGestureRecovery();return;}
      await applySelectedAudioFromGesture(true);
    };
    document.addEventListener('click',audioRecoveryHandler,true);
  }
  async function applySelectedAudioFromGesture(recoveryOnly=false){
    if(!TombWorldNarration.isMasterEnabled()){removeAudioGestureRecovery();return false;}
    const attempts=[];
    if(TombWorldNarration.isPlaybackEnabled()&&(!recoveryOnly||narrationGestureRecoveryRequired))attempts.push({category:'narration',promise:TombWorldNarration.activateFromGesture()});
    const results=await Promise.allSettled(attempts.map(attempt=>attempt.promise));
    reconcileAmbientActiveState();
    results.forEach((result,index)=>{
      const required=!(result.status==='fulfilled'&&result.value===true);
      if(attempts[index].category==='narration')narrationGestureRecoveryRequired=required;
    });
    if(!narrationGestureRecoveryRequired)removeAudioGestureRecovery();
    else if(attempts.length)armAudioGestureRecovery();
    if(!narrationGestureRecoveryRequired)void narrateVisibleGradeMilestone();
    return !narrationGestureRecoveryRequired;
  }
  function handleNarrationUsable(){
    narrationGestureRecoveryRequired=false;
    removeAudioGestureRecovery();
    void narrateVisibleGradeMilestone();
  }
  function syncNarrationControls(){
    const masterEnabled=TombWorldNarration.isMasterEnabled();
    const narrationEnabled=TombWorldNarration.isPreferenceEnabled();
    narrationSpeakerBtn.classList.toggle('is-muted',!masterEnabled);
    const enabledIcon=narrationSpeakerBtn.querySelector('.narration-icon-enabled');
    const disabledIcon=narrationSpeakerBtn.querySelector('.narration-icon-disabled');
    enabledIcon.toggleAttribute('hidden',!masterEnabled);
    disabledIcon.toggleAttribute('hidden',masterEnabled);
    narrationSpeakerBtn.setAttribute('aria-label',`Master audio ${masterEnabled?'on':'off'}`);
    narrationSpeakerBtn.setAttribute('aria-pressed',String(masterEnabled));
    narrationSpeakerBtn.title=`Master audio ${masterEnabled?'on':'off'}`;
    const narrationToggle=globalThis.document?.querySelector('#narrationToggle');
    if(narrationToggle){
      narrationToggle.setAttribute('aria-checked',String(narrationEnabled));
      narrationToggle.querySelector('.ambient-toggle-state').textContent=narrationEnabled?'On':'Off';
    }
    const ambientToggle=globalThis.document?.querySelector('#ambientNoiseToggle');
    if(ambientToggle){
      ambientToggle.setAttribute('aria-checked',String(ambientEnabled));
      ambientToggle.querySelector('.ambient-toggle-state').textContent=ambientEnabled?'On':'Off';
    }
    const diceRollToggle=globalThis.document?.querySelector('#diceRollToggle');
    if(diceRollToggle){
      const diceRollEnabled=TombWorldDiceSfx.isPreferenceEnabled();
      diceRollToggle.setAttribute('aria-checked',String(diceRollEnabled));
      diceRollToggle.querySelector('.ambient-toggle-state').textContent=diceRollEnabled?'On':'Off';
    }
    const volumeSlider=globalThis.document?.querySelector('#gameVolume');
    if(volumeSlider){
      const percentage=masterEnabled?Math.round(preferredGameVolume*100):0;
      volumeSlider.value=String(percentage);
      volumeSlider.setAttribute('aria-valuetext',percentage===0?'Muted':`${percentage} percent`);
      volumeSlider.style?.setProperty?.('--volume-percent',`${percentage}%`);
    }
  }
  async function setGameAudioEnabled(enabled){
    TombWorldNarration.setMasterEnabled(enabled);
    TombWorldDiceSfx.setMasterEnabled(enabled);
    if(enabled){
      const diceActivation=TombWorldDiceSfx.activateFromGesture();
      appliedAmbientEnabled=ambientEnabled;
      reconcileAmbientActiveState();
      const narrationUnlock=applySelectedAudioFromGesture();
      const ambientPlayback=shouldAmbientBeActive()?TombWorldAmbient.playFromGesture():Promise.resolve(false);
      playPendingBoardSetupMissionIntro();
      void Promise.allSettled([diceActivation,narrationUnlock,ambientPlayback]);
    }else{
      appliedAmbientEnabled=false;
      TombWorldAmbient.stop();
      narrationGestureRecoveryRequired=false;
      TombWorldAmbient.removeGestureRecovery();
      removeAudioGestureRecovery();
    }
    syncNarrationControls();
  }
  function playPendingBoardSetupMissionIntro(){
    if(!pendingBoardSetupMissionIntro||state.screen!=='setup'||currentSetupStepId()!=='killzone'||!TombWorldNarration.isPlaybackEnabled())return false;
    const missionId=pendingBoardSetupMissionIntro;
    pendingBoardSetupMissionIntro=null;
    void TombWorldNarration.playMissionIntro(missionId,true);
    return true;
  }
  function clearPendingBoardSetupMissionIntro(){pendingBoardSetupMissionIntro=null;}
  function enterBoardSetup(){
    void TombWorldDiceSfx.activateFromGesture();
    pendingBoardSetupMissionIntro=state.missionId;
    playPendingBoardSetupMissionIntro();
  }
  narrationSpeakerBtn.addEventListener('click',async()=>{
    const enabled=!TombWorldNarration.isMasterEnabled();
    await setGameAudioEnabled(enabled);
  });
  function handleNarrationChange(){
    syncNarrationControls();
    const replay=$('#replayNarration');
    if(replay)replay.disabled=!TombWorldNarration.canReplay();
  }
  window.addEventListener('tombworldnarrationchange',handleNarrationChange);
  window.addEventListener('tombworldnarrationusable',handleNarrationUsable);
  window.addEventListener('tombworldaudiorecoveryrequired',armAudioGestureRecovery);
  const gameWorkspace = $('#gameWorkspace');
  const operativeStatusPanel = $('#operativeStatusPanel');
  const operativeStatusToggle = $('#operativeStatusToggle');
  const modal = $('#modal');
  const modalBody = $('#modalBody');
  const diceEntryDialog = $('#diceEntryDialog');
  const diceEntryTitle = $('#diceEntryTitle');
  const diceEntryRoller = $('#diceEntryRoller');
  const diceEntryInstruction = $('#diceEntryInstruction');
  const diceEntryResults = $('#diceEntryResults');
  const diceEntryProgress = $('#diceEntryProgress');
  const diceEntryKeypad = $('#diceEntryKeypad');
  const diceEntryUndo = $('#diceEntryUndo');
  const diceEntryCommit = $('#diceEntryCommit');
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

  function isStandalonePwa(){
    return window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
  }

  function registerServiceWorker(){
    if(!('serviceWorker' in navigator))return;
    const standalonePwa=isStandalonePwa();
    let waitingWorker=null;
    let updateRequested=false;
    let offlineInstallPercent=0;
    let offlineInstallDismissTimer=null;
    const offlineInstallStatus=$('#offlineInstallStatus');
    const offlineInstallMessage=$('#offlineInstallMessage');
    const offlineInstallPercentText=$('#offlineInstallPercent');
    const offlineInstallProgress=$('#offlineInstallProgress');
    const offlineInstallProgressBar=$('span',offlineInstallProgress);
    const updateOfflineInstallStatus=data=>{
      if(!data||!Number.isFinite(data.completed)||!Number.isFinite(data.total)||data.total<=0)return;
      const calculated=Math.round((data.completed/data.total)*100);
      const percent=Math.max(offlineInstallPercent,Math.min(100,Math.max(0,Number.isFinite(data.percent)?data.percent:calculated)));
      offlineInstallPercent=percent;
      clearTimeout(offlineInstallDismissTimer);
      offlineInstallStatus.hidden=false;
      offlineInstallProgress.hidden=false;
      offlineInstallStatus.classList.toggle('complete',data.type==='OFFLINE_INSTALL_COMPLETE');
      offlineInstallMessage.textContent=data.type==='OFFLINE_INSTALL_COMPLETE'?'Ready for offline play':'Preparing for offline play…';
      offlineInstallPercentText.textContent=`${percent}%`;
      offlineInstallProgress.setAttribute('aria-valuenow',String(percent));
      offlineInstallProgressBar.style.width=`${percent}%`;
      if(data.type==='OFFLINE_INSTALL_COMPLETE')offlineInstallDismissTimer=setTimeout(()=>{offlineInstallStatus.hidden=true;},1800);
    };
    navigator.serviceWorker.addEventListener('message',event=>{
      if(!standalonePwa)return;
      if(['OFFLINE_INSTALL_START','OFFLINE_INSTALL_PROGRESS','OFFLINE_INSTALL_COMPLETE'].includes(event.data?.type))updateOfflineInstallStatus(event.data);
      if(event.data?.type==='OFFLINE_PACKAGE_READY')offlineInstallStatus.hidden=true;
      if(event.data?.type==='OFFLINE_INSTALL_ERROR'){
        clearTimeout(offlineInstallDismissTimer);
        offlineInstallStatus.classList.remove('complete');
        offlineInstallStatus.hidden=false;
        offlineInstallMessage.textContent=event.data.message||'Offline setup could not be completed. It will be retried next time.';
        offlineInstallPercentText.textContent='';
        offlineInstallProgress.hidden=true;
        offlineInstallDismissTimer=setTimeout(()=>{offlineInstallStatus.hidden=true;},4000);
      }
    });
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
          if(standalonePwa)navigator.serviceWorker.ready.then(readyRegistration=>{
            readyRegistration.active?.postMessage({type:'ENSURE_OFFLINE_PACKAGE'});
          });
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
  function isPvpMode(){return state.gameMode==='pvp';}
  function selectedPlayerTeamName(fallback='Kill Team'){return playerTeamData?.teamName||playerTeamEntry()?.name||fallback;}
  function transdimensionalRelocationSelectionSummary(){return `Two ${selectedPlayerTeamName('Player')} operatives were randomly selected to swap positions.`;}
  function playerSideLabel(){return isPvpMode()?selectedPlayerTeamName():'Player';}
  function opponentSingularLabel(){return isPvpMode()?'Necron':'NPO';}
  function opponentPluralLabel(){return isPvpMode()?'Necrons':'NPOs';}
  function deadlyEncountersActive(){return !isPvpMode()&&state.deadlyEncountersEnabled===true;}
  function deadlyEncountersStatusLabel(){return deadlyEncountersActive()?'On':'Off';}
  function presentSideTerminology(text){
    if(!isPvpMode())return text;
    return String(text)
      .replace(/NPOs\b/g,()=>opponentPluralLabel())
      .replace(/NPO\b/g,()=>opponentSingularLabel())
      .replace(/Player\b/g,()=>playerSideLabel());
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
    const forwardScoutingOptions=kind==='rules'
      ? [...(playerTeamData?.factionRules||[]),...(playerTeamData?.strategicGambits||[])]
        .filter(entry=>entry.forwardScoutingOption===true)
        .sort((a,b)=>(a.forwardScoutingOrder||0)-(b.forwardScoutingOrder||0))
      : [];
    const ruleHtml=entry=>`<div class="mission-rule"><strong>${escapeHtml(entry.name)}</strong>${entry.timing?`<small>${escapeHtml(entry.timing)}</small>`:''}<p>${escapeHtml(entry.text)}</p></div>`;
    const forwardScoutingHtml=entry=>{
      const count=forwardScoutingOptions.length;
      const options=forwardScoutingOptions.map(option=>`<article class="forward-scouting-option"><header><strong>${escapeHtml(option.name)}</strong>${Number.isFinite(option.selectionLimit)?`<span>Maximum ${option.selectionLimit}</span>`:''}</header>${option.timing?`<small>${escapeHtml(option.timing)}</small>`:''}<p>${escapeHtml(option.text)}</p></article>`).join('');
      return `<div class="mission-rule forward-scouting-rule"><strong>${escapeHtml(entry.name)}</strong>${entry.timing?`<small>${escapeHtml(entry.timing)}</small>`:''}<p>${escapeHtml(entry.text)}</p><details class="forward-scouting-disclosure"><summary><span class="when-closed">View ${count} scouting options</span><span class="when-open">Hide ${count} scouting options</span></summary><div class="forward-scouting-options">${options}</div></details></div>`;
    };
    const visibleEntries=kind==='rules'&&forwardScoutingOptions.length?entries.filter(entry=>entry.forwardScoutingOption!==true):entries;
    return `<section class="card faction-guidance"><h3>${title}</h3>${visibleEntries.map(entry=>entry.forwardScoutingParent===true&&forwardScoutingOptions.length?forwardScoutingHtml(entry):ruleHtml(entry)).join('')}<p class="muted">Resolve these rules on the tabletop; the Guide presents reminders without simulating positioning.</p></section>`;
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

  // Expansion datacards remain separate from the Standard physical inventory. Variant
  // hooks introduce them through rules-driven generation, not the manual Add NPO tool.
  const tombsBeyondCountingNpoDefinitions = Object.freeze({
    'Flayed One': {
      id:'flayed-one',name:'Flayed One',type:'Flayed One',faction:'Necron',move:5,apl:2,save:4,wounds:9,baseSize:32,
      keywords:['Necron','Flayed One'],compatibilityBehavior:null,compatibilityAttack:{dice:4,hit:3,normal:4,crit:5},defaultWeaponId:'flayer-claws',loadoutOptions:null,
      rangedWeapons:[],meleeWeapons:[{id:'flayer-claws',name:'Flayer claws',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:5},rules:['Ceaseless','Rending'],ruleIds:['ceaseless','rending']}],
      actions:[],passiveRules:[],abilities:[{id:'horrifying-flaying',name:'Horrifying Flaying',deferred:true}],strategicRules:[],behavior:{summary:'Move toward the enemy to Fight, seeking cover.',actions:['Fight','Charge','Reposition','Dash'],focus:'fight',operatesHatches:true,orderRule:'engage-if-fight-or-charge'}
    },
    'Skorpekh Destroyer': {
      id:'skorpekh-destroyer',name:'Skorpekh Destroyer',type:'Skorpekh Destroyer',faction:'Necron',move:6,apl:2,save:3,wounds:18,baseSize:50,
      keywords:['Necron','Destroyer Cult','Skorpekh Destroyer'],compatibilityBehavior:null,compatibilityAttack:{dice:4,hit:3,normal:4,crit:6},defaultWeaponId:'skorpekh-hyperphase-weapons',loadoutOptions:null,
      rangedWeapons:[],meleeWeapons:[{id:'skorpekh-hyperphase-weapons',name:'Skorpekh hyperphase weapons',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:6},rules:['Balanced','Lethal 5+','Whirling Onslaught*'],ruleIds:['balanced','lethal'],lethal:5,deferredRules:['Whirling Onslaught']}],
      actions:[],passiveRules:[{id:'hulking',name:'Hulking',deferred:true}],abilities:[{id:'hulking',name:'Hulking',deferred:true}],strategicRules:[],behavior:{summary:'Move toward the enemy to Fight, seeking cover.',actions:['Fight','Charge','Reposition','Dash'],focus:'fight',operatesHatches:true,orderRule:'engage-if-fight-or-charge'}
    },
    'Hexmark Destroyer': {
      id:'hexmark-destroyer',name:'Hexmark Destroyer',type:'Hexmark Destroyer',faction:'Necron',move:6,apl:2,save:3,wounds:15,baseSize:50,
      keywords:['Necron','Destroyer Cult','Hexmark Destroyer'],compatibilityBehavior:null,compatibilityAttack:{dice:5,hit:3,normal:3,crit:2},defaultWeaponId:'enmitic-disintegrator-pistols',loadoutOptions:null,
      rangedWeapons:[{id:'enmitic-disintegrator-pistols',name:'Enmitic disintegrator pistols',type:'ranged',profiles:[
        {id:'focused',name:'Focused',attacks:5,hit:3,damage:{normal:3,critical:2},rules:['Range 9"','Ceaseless','Devastating 2','Piercing 1','Saturate'],ruleIds:['range','ceaseless','devastating','piercing','saturate'],range:9,devastating:2,piercing:1},
        {id:'sweeping',name:'Sweeping',attacks:4,hit:3,damage:{normal:3,critical:2},rules:['Range 9"','Devastating 2','Piercing 1','Saturate','Torrent 2"'],ruleIds:['range','devastating','piercing','saturate','torrent'],range:9,devastating:2,piercing:1,torrent:2,manualResolution:'Also attack each other target within 2 inches of the primary target. Resolve each attack separately. Do not attack the primary target twice.'}
      ]}],
      meleeWeapons:[{id:'enmitic-disintegrator-pistols-point-blank',name:'Enmitic disintegrator pistols (point-blank)',type:'melee',attacks:5,hit:3,damage:{normal:3,critical:4},rules:[],ruleIds:[]}],
      actions:[],passiveRules:[],abilities:[{id:'multi-threat-eliminator',name:'Multi-Threat Eliminator',deferred:true}],strategicRules:[],behavior:{summary:'Seek an unobscured shot, otherwise improve the mission position.',actions:['Fall Back','Shoot','Reposition','Dash','Fight'],focus:'shoot',operatesHatches:true,orderRule:'engage-if-shoot-or-fight'}
    },
    'Royal Warden': {
      id:'royal-warden',name:'Royal Warden',type:'Royal Warden',faction:'Necron',move:5,apl:3,save:3,wounds:14,baseSize:32,
      keywords:['Necron','Royal Warden'],compatibilityBehavior:null,compatibilityAttack:{dice:4,hit:3,normal:4,crit:6},defaultWeaponId:'relic-gauss-blaster',loadoutOptions:null,
      rangedWeapons:[{id:'relic-gauss-blaster',name:'Relic gauss blaster',type:'ranged',attacks:4,hit:3,damage:{normal:4,critical:6},rules:['Lethal 5+','Piercing 1'],ruleIds:['lethal','piercing'],lethal:5,piercing:1}],
      meleeWeapons:[{id:'bayonet',name:'Bayonet',type:'melee',attacks:4,hit:3,damage:{normal:3,critical:4},rules:[],ruleIds:[]}],
      actions:[],passiveRules:[],abilities:[{id:'engrammatic-logic',name:'Engrammatic Logic',deferred:true}],strategicRules:[],behavior:{summary:'Seek an unobscured shot, otherwise improve the mission position.',actions:['Fall Back','Shoot','Reposition','Dash','Fight'],focus:'shoot',operatesHatches:true,orderRule:'engage-if-shoot-or-fight'}
    },
    'Lychguard': {
      id:'lychguard',name:'Lychguard',type:'Lychguard',faction:'Necron',move:5,apl:2,save:3,wounds:13,baseSize:32,exclusiveMeleeLoadout:true,
      keywords:['Necron','Lychguard'],compatibilityBehavior:null,compatibilityAttack:{dice:4,hit:3,normal:4,crit:6},defaultWeaponId:'hyperphase-sword',loadoutOptions:[{id:'hyperphase-sword',name:'Hyperphase sword'},{id:'warscythe',name:'Warscythe'}],
      rangedWeapons:[],meleeWeapons:[
        {id:'hyperphase-sword',name:'Hyperphase sword',type:'melee',attacks:4,hit:3,damage:{normal:4,critical:6},rules:['Lethal 5+','Shield*'],ruleIds:['lethal'],lethal:5,deferredRules:['Shield']},
        {id:'warscythe',name:'Warscythe',type:'melee',attacks:4,hit:3,damage:{normal:5,critical:7},rules:['Lethal 5+'],ruleIds:['lethal'],lethal:5}
      ],
      actions:[],passiveRules:[],abilities:[{id:'guardian-protocol',name:'Guardian Protocol',deferred:true}],strategicRules:[],behavior:{summary:'Stay near the Royal Warden unless an enemy can be fought or charged.',actions:['Fight','Charge','Reposition','Dash'],focus:'warden',operatesHatches:true,orderRule:'engage-if-fight-charge-or-warden'}
    }
  });
  const tombsBeyondCountingEventDefinitions=Object.freeze({
    'flesh-hunger':{title:'Flesh Hunger',text:'If no Flayed One is in the killzone, set one up Ready with a Conceal order. Otherwise, one Flayed One immediately performs a free Charge or Reposition towards the closest Player operative.',execution:{type:'flesh-hunger'},duration:'immediate',redrawIfImpossible:true},
    'rewards-of-annihilation':{title:'Rewards of Annihilation',text:'Until the end of the turning point, whenever a Skorpekh Destroyer or Hexmark Destroyer incapacitates a Player operative, that NPO regains D3 lost wounds, or 2D3 if that operative has a Wounds characteristic of 12 or more.',resultText:'Effect active until the end of this Turning Point.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'rewards-of-annihilation',gameplayHooks:[],automationType:'automatic',priority:20},
    'enforcer-of-the-phaerons':{title:'Enforcer of the Phaerons',text:'Until the end of the turning point, an NPO in the same room as a Royal Warden has Ceaseless on its weapons.',resultText:'Effect active until the end of this Turning Point.',execution:{type:'activate'},lifecycle:'persistent',duration:'turning-point',handlerId:'enforcer-of-the-phaerons',gameplayHooks:['effectiveWeapon'],automationType:'tabletop-answer',priority:20}
  });
  const STAGE3_RULE_TEXT=Object.freeze({
    multiThreatRange:'Is the attacking operative within 8 inches of the Hexmark Destroyer?',
    engrammatic:'Engrammatic Logic: if this NPO is within 6 inches of the Royal Warden, it can ignore stat changes caused by being Injured.',
    horrifyingCandidates:'Which other living Player operatives are visible to and within 3 inches of either the Flayed One or the incapacitated operative?',
    guardianRange:'Is this Royal Warden within Control Range of an Engaged Lychguard?',
    guardianPrevented:'Guardian Protocol prevents this Royal Warden from being selected.',
    lychguardMovement:'Can the Lychguard end this movement within Control Range of the Royal Warden?'
  });

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
      meleeWeapons:[{id:'claws',name:'Claws',type:'melee',attacks:4,hit:4,damage:{normal:4,critical:4},rules:['Brutal'],ruleIds:['brutal']}],actions:[],
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
  const tombsBeyondCountingNpoDefinitionsForValidation=tombsBeyondCountingNpoDefinitions;
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
    'awakened-warrior':{title:'Awakened Warrior',text:'Set up one Ready Necron Warrior with a Conceal order using the placement instructions on the event card. If no eligible Necron Warrior can be placed, draw another event card.',execution:{type:'awakened-warrior'},duration:'immediate',redrawIfImpossible:true},
    ...tombsBeyondCountingEventDefinitions
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
    transponder:()=>({sites:{},transponderFound:false,transponderMarkerId:null,carrierId:null,transponderStatus:'unknown',searchSitesResolved:0,escaped:false,extractionConfirmed:false,completed:false,outcome:null,lastRoll:null,transactions:{}}),
    destruction:()=>({destruction:0}),
    scout:()=>({awakenedRooms:{},scoutedRoomIds:[],scoutedByRoom:{}}),
    regroup:()=>({operativeChecks:{},lastCheckedTurningPoint:0})
  };
  function eventDefinition(definitionId){return eventDefinitions[definitionId]||null;}

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
      normalized.sites=isRecord(raw.sites)?Object.fromEntries(Object.entries(raw.sites).filter(([id,value])=>engine.sites.some(site=>site.id===id)&&['found','empty','available','cleared','transponder','removed'].includes(value)).map(([id,value])=>[id,{found:'transponder',empty:'cleared'}[value]||value])):{};
      const foundEntry=Object.entries(normalized.sites).find(([,value])=>value==='transponder');
      normalized.transponderFound=Boolean(raw.transponderFound||foundEntry||raw.escaped);
      normalized.transponderMarkerId=normalized.transponderFound&&(typeof raw.transponderMarkerId==='string'?engine.sites.some(site=>site.id===raw.transponderMarkerId)&&raw.transponderMarkerId:foundEntry?.[0])||null;
      normalized.carrierId=typeof raw.carrierId==='string'&&raw.carrierId?raw.carrierId:null;
      normalized.escaped=Boolean(raw.escaped);
      normalized.extractionConfirmed=Boolean(raw.extractionConfirmed||normalized.escaped);
      normalized.transponderStatus=normalized.extractionConfirmed?'escaped':normalized.transponderFound?(normalized.carrierId?'carried':'onBattlefield'):'unknown';
      normalized.searchSitesResolved=normalized.transponderFound?engine.sites.length:engine.sites.filter(site=>['cleared','removed'].includes(normalized.sites[site.id])).length;
      normalized.completed=Boolean(raw.completed||normalized.extractionConfirmed);
      normalized.outcome=['victory','defeat'].includes(raw.outcome)?raw.outcome:normalized.extractionConfirmed?'victory':null;
      normalized.transactions=isRecord(raw.transactions)?{...raw.transactions}:{};
      normalized.lastRoll=isRecord(raw.lastRoll)?{...raw.lastRoll}:null;
      if(normalized.transponderMarkerId)engine.sites.forEach(site=>{if(site.id!==normalized.transponderMarkerId&&!normalized.sites[site.id])normalized.sites[site.id]='removed';});
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

  const inertVariantHooks=Object.freeze({
    startingRosterGeneration:value=>value,
    reinforcementGeneration:value=>value,
    eventGeneratedNpoReplacement:value=>value,
    eventDeckAdditions:()=>[],
    missionRequestedNpoReplacement:value=>value,
    npoSetupReplacement:value=>value
  });
  const optionalReplacement=(request,originalType,replacements)=>request?.type===originalType?{...request,replacementOptions:[request.type,...replacements]}:request;
  const variantHooks=({replaceType=null,replacements=[],eventId=null,crownworld=false}={})=>Object.freeze({
    ...inertVariantHooks,
    startingRosterGeneration:value=>optionalReplacement(value,replaceType,replacements),
    reinforcementGeneration:value=>optionalReplacement(value,replaceType,replacements),
    eventGeneratedNpoReplacement:value=>optionalReplacement(value,replaceType,replacements),
    missionRequestedNpoReplacement:value=>optionalReplacement(value,replaceType,replacements),
    eventDeckAdditions:()=>eventId?[{instanceId:`${eventId}-1`,definitionId:eventId}]:[],
    npoSetupReplacement:value=>crownworld&&value?.type===TOMB_CRAWLER_TYPE?{...value,mandatoryPair:['Royal Warden','Lychguard']}:value
  });
  const TOMB_WORLD_VARIANTS=Object.freeze({
    standard:Object.freeze({id:'standard',name:'Standard Tomb World',available:true,summary:'Use the normal Tomb World NPO generation table and event deck.',briefing:'Standard Tomb World',hooks:inertVariantHooks}),
    'flayer-curse':Object.freeze({id:'flayer-curse',name:'Flayer Curse Infected Tomb',available:true,summary:'Flayed Ones may replace Necron Warriors. Adds the Flesh Hunger event.',briefing:'Flayed One replacements + Flesh Hunger',hooks:variantHooks({replaceType:'Necron Warrior',replacements:['Flayed One'],eventId:'flesh-hunger'})}),
    'destroyer-cult':Object.freeze({id:'destroyer-cult',name:'Destroyer Cult Tomb',available:true,summary:'Skorpekh and Hexmark Destroyers may replace Tomb Crawlers. Adds Rewards of Annihilation.',briefing:'Destroyer replacements + Rewards of Annihilation',hooks:variantHooks({replaceType:TOMB_CRAWLER_TYPE,replacements:['Skorpekh Destroyer','Hexmark Destroyer'],eventId:'rewards-of-annihilation'})}),
    crownworld:Object.freeze({id:'crownworld',name:'Crownworld of the Dynasty Tomb',available:true,summary:'The first Tomb Crawler setup becomes a Royal Warden and Lychguard. Awakened Warrior may instead create a Lychguard. Adds Enforcer of the Phaerons.',briefing:'Royal Warden/Lychguard replacements + Enforcer of the Phaerons',hooks:variantHooks({eventId:'enforcer-of-the-phaerons',crownworld:true})})
  });
  function currentTombWorldVariant(){return TOMB_WORLD_VARIANTS[state?.tombWorldVariant]||TOMB_WORLD_VARIANTS.standard;}
  function isFlayerCurseTomb(){return currentTombWorldVariant().id==='flayer-curse';}
  function isDestroyerCultTomb(){return currentTombWorldVariant().id==='destroyer-cult';}
  function isCrownworldTomb(){return currentTombWorldVariant().id==='crownworld';}
  function tombWorldVariantHook(name,value){
    const hook=currentTombWorldVariant().hooks[name];
    return typeof hook==='function'?hook(value):value;
  }
  function tombWorldEventDeckAdditions(){return tombWorldVariantHook('eventDeckAdditions',undefined);}
  function eventDeckForVariant(variantId=state?.tombWorldVariant){
    const variant=TOMB_WORLD_VARIANTS[variantId]||TOMB_WORLD_VARIANTS.standard;
    return [...eventDeck,...variant.hooks.eventDeckAdditions()];
  }
  function replaceEventGeneratedNpo(request){return tombWorldVariantHook('eventGeneratedNpoReplacement',request);}
  function replaceMissionRequestedNpo(request){return tombWorldVariantHook('missionRequestedNpoReplacement',request);}
  function replaceNpoAtSetup(request){return tombWorldVariantHook('npoSetupReplacement',request);}
  function resolveVariantNpoRequest(request,{choice=null,transactionId=null}={}){
    if(!request?.replacementOptions?.length)return request;
    const options=request.replacementOptions.filter(type=>Boolean(npoDefinition(type)));
    const prior=transactionId&&state.variantState?.replacementTransactions?.[transactionId];
    const pvpDecisionPending=isPvpMode()&&!options.includes(choice)&&!prior?.committed;
    const selected=options.includes(prior?.selectedType)?prior.selectedType
      :options.includes(choice)?choice
      :isPvpMode()?options[0]
      :isFlayerCurseTomb()&&options.includes('Flayed One')?'Flayed One'
      :isDestroyerCultTomb()&&options.includes('Skorpekh Destroyer')?'Skorpekh Destroyer'
      :options[Math.floor(Math.random()*options.length)];
    const resolved={...request,type:selected,...(pvpDecisionPending?{replacementOptions:[...options],replacementTransactionId:transactionId}:{})};
    if(selected!==request.type)delete resolved.weaponId;
    if(transactionId){
      state.variantState.replacementTransactions[transactionId]={id:transactionId,originalType:request.type,originalWeaponId:request.weaponId,options:[...options],selectedType:selected,owner:isPvpMode()?'necron-controller':'guide',committed:!pvpDecisionPending};
      if(!pvpDecisionPending)log(`${currentTombWorldVariant().name}: ${request.type} request generated ${selected}.`);
    }
    return resolved;
  }

  const initialState = () => ({
    version:APP_VERSION, saveVersion:currentSaveVersion(), gameMode:null, screen:'home', tab:'play', setupStep:0, missionId:null,
    backgroundSelection:null,
    setupChecks:{}, restlessTombEnabled:false, deadlyEncountersEnabled:false, deadlyEncountersState:DeadlyEncounters.emptyState(), tombWorldVariant:'standard', roster:[], playerTeamId:'', playerTeamFile:'', playerRoster:[], playerDisplayNumbers:{}, playerRosterInitializedForTeamId:'', playerCount:0, playerReady:0, playerDeployed:false, turningPoint:0,
    threat:0, initiative:'player', phase:'setup', nextSide:'player', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, strategyPipeline:null, missionReadyContext:{turningPoint:null,sarcophagusControllers:0}, activationNumber:0,totalActivationsThisTP:0, playerActivated:0, npoActivated:0,
    activationHistory:[], playerActivatedIds:[], playerCasualtyIds:[], playerWounds:{}, playerOperativeStates:{}, reinforcementState:{turningPoint:0,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0,blockedByCapacity:0,blockedByInventory:0},
    gradeMilestone:null, gradeMilestoneSequence:0, tpStartThreat:0, tpStartGrade:0, tpStartDestroyedNpos:0, tpStartPlayerCasualties:0,
    npoAttackTargetId:null,
    npoAttackSummary:null, combatState:null, fightState:null, pendingDice:null, weaponRuleResolution:null, hotResolution:null, missionState:null, missionRuntime:null, missionActionContext:null, startingNpoGeneration:null,
    npoRuleState:{aplModifiers:[],pendingMovementEffects:[],oncePerTurningPoint:{},reanimatedTargetIds:[],incapacitationTriggers:[],stage3Triggers:{}},
    eventState:{available:eventDeck.map(card=>card.instanceId),used:[],active:[],transactions:{},playerAplModifiers:[],reanimationAttempts:{},rewardsTriggers:[]}, variantState:{crownworldFirstCrawlerConsumed:false,replacementTransactions:{}}, gameEnd:null,
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
  let rewardsQueueInProgress=false;
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
    if(objectiveEngine){
      const pendingDiceResults=state.missionRuntime?.pendingDiceResults;
      state.missionRuntime=objectiveEngine.getMissionRuntime();
      if(pendingDiceResults)state.missionRuntime.pendingDiceResults=pendingDiceResults;
    }
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
    merged.gameMode=raw.gameMode===null?null:(raw.gameMode==='pvp'?'pvp':'solo');
    merged.gradeMilestoneSequence=Math.max(0,Math.trunc(Number(raw.gradeMilestoneSequence)||0));
    if(isRecord(raw.gradeMilestone)){
      const tracked=typeof raw.gradeMilestone.instanceId==='string'&&typeof raw.gradeMilestone.narrationSeen==='boolean';
      const trackedSequence=tracked?Number(raw.gradeMilestone.instanceId.match(/^grade:\d+:(\d+)$/)?.[1]):0;
      merged.gradeMilestoneSequence=Math.max(merged.gradeMilestoneSequence,Math.trunc(trackedSequence)||0);
      merged.gradeMilestone={...raw.gradeMilestone,
        instanceId:tracked?raw.gradeMilestone.instanceId:`grade:${raw.gradeMilestone.grade}:legacy`,
        narrationSeen:tracked?raw.gradeMilestone.narrationSeen:true};
    }else merged.gradeMilestone=null;
    if(!['home','help','setup','game'].includes(merged.screen))merged.screen='home';
    if(!['play','mission','roster','player-roster','journal','help'].includes(merged.tab))merged.tab='play';
    const beyondTurningPointLimit=Number(raw.turningPoint)>MAX_TURNING_POINTS;
    const invalidTurningPoint=beyondTurningPointLimit&&!['victory','defeat'].includes(raw.gameEnd);
    merged.turningPoint=Math.min(boundedInteger(raw.turningPoint,0,999),MAX_TURNING_POINTS);
    merged.threat=boundedInteger(raw.threat,0,15);
    merged.restlessTombEnabled=raw.restlessTombEnabled===true;
    merged.deadlyEncountersEnabled=raw.deadlyEncountersEnabled===true;
    merged.deadlyEncountersState=DeadlyEncounters.normalizeState(raw.deadlyEncountersState);
    merged.tombWorldVariant=TOMB_WORLD_VARIANTS[raw.tombWorldVariant]?raw.tombWorldVariant:'standard';
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
      ? {side:'player',stage:{...normalizePendingAttackResultLists(raw.combatState.stage),threatDiceResolving:false}}
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
      incapacitationTriggers:normalizeIdList(importedRuleState.incapacitationTriggers),
      stage3Triggers:isRecord(importedRuleState.stage3Triggers)?Object.fromEntries(Object.entries(importedRuleState.stage3Triggers).filter(([,trigger])=>isRecord(trigger)).map(([id,trigger])=>[id,{...trigger}])):{}
    };
    merged.fightState=isRecord(raw?.fightState)&&raw.fightState.version===1
      ? normalizeFightState(raw.fightState)
      : null;
    // Aggregate pre-v9.1.1 melee drafts cannot be converted into alternating
    // Strike/Block state. Reset only that unfinished action; preserve the battle.
    if(!merged.fightState&&merged.combatState?.side==='player'&&isRecord(merged.combatState.stage?.meleeCombatDraft)){
      merged.combatState={...merged.combatState,stage:{...merged.combatState.stage,meleeCombatDraft:null,pendingMelee:null,pendingMeleeResults:[]}};
    }
    if(!merged.fightState&&merged.lastActivation?.pendingAction?.id==='fight'&&isRecord(merged.lastActivation.combatDraft)){
      merged.lastActivation={...merged.lastActivation,combatDraft:null,targetConfirmed:false,attackResolved:false};
    }
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
        initiativeMode:['rolled','automatic','pending'].includes(raw.strategyData.initiativeMode)
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
    const importedEvents=isRecord(raw.eventState)?raw.eventState:{},variantDeck=eventDeckForVariant(merged.tombWorldVariant);
    const validInstances=new Set(variantDeck.map(card=>card.instanceId));
    const available=Array.isArray(importedEvents.available)?normalizeIdList(importedEvents.available,validInstances):variantDeck.map(card=>card.instanceId);
    const used=normalizeIdList(importedEvents.used,validInstances).filter(id=>!available.includes(id));
    variantDeck.forEach(card=>{if(!available.includes(card.instanceId)&&!used.includes(card.instanceId))available.push(card.instanceId);});
    const normalizedActive=Array.isArray(importedEvents.active)?importedEvents.active.map(event=>{
      if(!isRecord(event))return null;
      const deckRecord=variantDeck.find(card=>card.instanceId===event.instanceId);
      const definitionId=event.definitionId||deckRecord?.definitionId;
      return eventDefinitions[definitionId]?{...event,definitionId}:null;
    }).filter(event=>event&&event.expiresAfterTurningPoint>=merged.turningPoint&&(!invalidTurningPoint||!Number.isFinite(Number(event.startedTurningPoint))||event.startedTurningPoint<=MAX_TURNING_POINTS)):[];
    merged.eventState={
      available,
      used,
      active:normalizedActive,
      transactions:isRecord(importedEvents.transactions)?{...importedEvents.transactions}:{},
      playerAplModifiers:Array.isArray(importedEvents.playerAplModifiers)?importedEvents.playerAplModifiers.filter(isRecord).map(item=>({...item})):[],
      reanimationAttempts:isRecord(importedEvents.reanimationAttempts)?{...importedEvents.reanimationAttempts}:{},
      rewardsTriggers:Array.isArray(importedEvents.rewardsTriggers)?importedEvents.rewardsTriggers.filter(isRecord).map(trigger=>({...trigger})):[]
    };
    const importedVariantState=isRecord(raw.variantState)?raw.variantState:{};
    merged.variantState={crownworldFirstCrawlerConsumed:Boolean(importedVariantState.crownworldFirstCrawlerConsumed),replacementTransactions:isRecord(importedVariantState.replacementTransactions)?{...importedVariantState.replacementTransactions}:{}};
    if(invalidTurningPoint)merged.eventState.active=merged.eventState.active.filter(event=>event.expiresAfterTurningPoint>MAX_TURNING_POINTS);
    const livingImportedPlayers=merged.playerRoster.filter(id=>merged.playerOperativeStates[id]?.inPlay!==false&&!merged.playerCasualtyIds.includes(id)).length;
    merged.missionReadyContext=raw?.missionReadyContext&&typeof raw.missionReadyContext==='object'
      ? {turningPoint:Number.isInteger(raw.missionReadyContext.turningPoint)?raw.missionReadyContext.turningPoint:null,sarcophagusControllers:normalizeSarcophagusControllers(raw.missionReadyContext.sarcophagusControllers,livingImportedPlayers)}
      : {turningPoint:null,sarcophagusControllers:0};
    merged.strategyPipeline=isRecord(raw.strategyPipeline)
      ? {...raw.strategyPipeline,completed:Array.isArray(raw.strategyPipeline.completed)?raw.strategyPipeline.completed:[]}
      : null;
    merged.gameEnd=['victory','defeat'].includes(raw?.gameEnd)?raw.gameEnd:null;
    const savedMission=missionDefinition(merged.missionId);
    merged.missionState=normalizeMissionState(raw?.missionState,savedMission,raw?.tracker);
    for(const id of merged.missionState?.escapedIds||[]){
      if(merged.playerRoster.includes(id))merged.playerOperativeStates[id]={inPlay:false,offBoardReason:'escaped'};
    }
    if(missionEngine(savedMission)?.type==='transponder'&&merged.missionState?.escaped&&merged.playerRoster.includes(merged.missionState.carrierId)){
      merged.playerOperativeStates[merged.missionState.carrierId]={inPlay:false,offBoardReason:'escaped'};
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
    }else if(isRecord(merged.lastActivation)&&merged.lastActivation.side==='player'&&typeof merged.lastActivation.operativeId==='string'){
      const operative=playerDefinition(merged.lastActivation.operativeId);
      const effective=Number(merged.lastActivation.effectiveApl??operative?.apl??0);
      merged.lastActivation={...merged.lastActivation,
        playerOperativeId:merged.lastActivation.operativeId,
        activationId:merged.lastActivation.activationId||activationIdFromState(merged,'player',merged.lastActivation.operativeId),
        baseApl:Number(merged.lastActivation.baseApl??operative?.apl??effective),effectiveApl:effective,
        startingAp:Number(merged.lastActivation.startingAp??effective),remainingAp:Math.max(0,Number(merged.lastActivation.remainingAp??effective)),
        actionSequence:Number(merged.lastActivation.actionSequence??merged.lastActivation.resolvedActions?.length??0),
        completedActionIds:Array.isArray(merged.lastActivation.completedActionIds)?merged.lastActivation.completedActionIds:[],
        resolvedActions:Array.isArray(merged.lastActivation.resolvedActions)?merged.lastActivation.resolvedActions:[],
        pendingAction:isRecord(merged.lastActivation.pendingAction)?{...merged.lastActivation.pendingAction}:null,
        committed:Boolean(merged.lastActivation.committed),completed:Boolean(merged.lastActivation.completed||merged.lastActivation.committed)
      };
    }
    if(merged.phase==='strategy'&&merged.strategyStage==='initiative'&&merged.strategyData?.initiativeMode!=='pending'){
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
      const variantValidation=validateNpoRoster(merged.roster,merged.tombWorldVariant);
      if(!validation.valid||!variantValidation.valid)throw new Error(`Saved NPO roster is invalid: ${[...validation.errors,...variantValidation.errors].join(' ')}`);
    }
    return merged;
  }
  function npoDefinition(type){return npoDefinitions[type]||tombsBeyondCountingNpoDefinitions[type]||null;}
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
    if(!Number.isFinite(definition.physicalQuantity)){
      const allocatedIds=new Set(allocated.map(npo=>npo.id)),available=[];
      for(let number=1;available.length<quantity;number++){
        const id=`${definition.id}-${number}`;
        if(!allocatedIds.has(id))available.push({id,displayNumber:number});
      }
      return available;
    }
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
  function validateNpoRoster(roster=state.roster,variantId=null){
    const errors=[], ids=new Set(), displayNumbers={},counts=Object.fromEntries(Object.keys(npoDefinitions).map(type=>[type,0]));
    if(!Array.isArray(roster))return {valid:false,errors:['NPO roster must be an array.']};
    roster.forEach((npo,index)=>{
      if(!isRecord(npo)){errors.push(`NPO ${index+1} is invalid.`);return;}
      if(typeof npo.id!=='string'||!npo.id)errors.push(`NPO ${index+1} is missing an instance ID.`);
      else if(ids.has(npo.id))errors.push(`Duplicate NPO instance ID: ${npo.id}.`);
      else ids.add(npo.id);
      const definition=npoDefinition(npo.type);
      if(!definition){errors.push(`Unsupported NPO type: ${npo.type||'missing'}.`);return;}
      if(variantId!==null&&tombsBeyondCountingNpoDefinitionsForValidation[npo.type]&&!variantAllowsExpansionNpo(npo.type,variantId)){
        errors.push(`${npo.type} is not legal for the ${(TOMB_WORLD_VARIANTS[variantId]||TOMB_WORLD_VARIANTS.standard).name} variant.`);return;
      }
      if(npoDefinitions[npo.type])counts[npo.type]++;
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
    const standardAllocated=roster.filter(npo=>npoDefinitions[npo?.type]).length;
    const excessIsScuttlingHistory=standardAllocated>MAX_PHYSICAL_NPOS
      && standardAllocated-MAX_PHYSICAL_NPOS<=roster.filter(npo=>npo?.createdBy==='a-ceaseless-scuttling').length;
    if(standardAllocated>MAX_PHYSICAL_NPOS&&!excessIsScuttlingHistory)errors.push(`Allocated NPOs exceed the ${MAX_PHYSICAL_NPOS}-model Tomb World inventory.`);
    if(roster.filter(npo=>npo?.type===TOMB_CRAWLER_TYPE&&npo.weaponId===ISOLATOR_LOADOUT).length>1)errors.push('Only one Tomb Crawler can have a transdimensional isolator.');
    return {valid:errors.length===0,errors,inventory:npoInventory(roster)};
  }
  function variantAllowsExpansionNpo(type,variantId=state?.tombWorldVariant){
    if(variantId==='flayer-curse')return type==='Flayed One';
    if(variantId==='destroyer-cult')return ['Skorpekh Destroyer','Hexmark Destroyer'].includes(type);
    if(variantId==='crownworld')return ['Royal Warden','Lychguard'].includes(type);
    return false;
  }
  function commitNpoRoster(candidate,action='update the NPO roster'){
    const validation=validateNpoRoster(candidate,state.tombWorldVariant);
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
      : (definition.meleeWeapons||[]).filter(weapon=>!definition.exclusiveMeleeLoadout||weapon.id===npo.weaponId);
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

  let activeManualDiceRequest=null;
  function discardActiveManualDiceRequest(){
    activeManualDiceRequest=null;
    if(diceEntryDialog.open)diceEntryDialog.close();
  }
  const cloneDiceData=value=>JSON.parse(JSON.stringify(value||{}));
  function diceRequestKey(kind,...parts){
    return [kind,`tp${state.turningPoint}`,`activation${state.activationNumber}`,...parts].filter(part=>part!==undefined&&part!==null&&String(part)!=='').map(String).join(':');
  }
  function validateDiceRequest(request){
    if(!request||typeof request!=='object')throw new TypeError('Dice request must be an object.');
    const {count,sides}=request;
    if(!Number.isInteger(count)||count<=0)throw new RangeError('Dice request count must be a positive integer.');
    if(!Number.isInteger(sides)||sides<2||sides>6)throw new RangeError('Dice request sides must be an integer from 2 through 6.');
    const title=typeof request.title==='string'&&request.title.trim()?request.title.trim():'Enter Dice Results';
    const instruction=typeof request.instruction==='string'&&request.instruction.trim()
      ?request.instruction.trim()
      :`Roll ${count}D${sides} on the tabletop and enter each result.`;
    const rollerLabel=typeof request.rollerLabel==='string'?request.rollerLabel.trim():'';
    const requestKey=typeof request.requestKey==='string'?request.requestKey.trim():'';
    const resumeKind=typeof request.resumeKind==='string'?request.resumeKind.trim():'';
    const resumeData=request.resumeData&&typeof request.resumeData==='object'&&!Array.isArray(request.resumeData)?cloneDiceData(request.resumeData):{};
    return {count,sides,title,instruction,rollerLabel,requestKey,resumeKind,resumeData};
  }
  function pendingDiceMatches(request,pending=state.pendingDice){
    return Boolean(pending&&request.requestKey&&pending.requestKey===request.requestKey&&pending.count===request.count&&pending.sides===request.sides);
  }
  function persistManualDice(active,status='collecting'){
    if(!active.request.requestKey||!active.request.resumeKind)return true;
    const previousPending=state.pendingDice;
    state.pendingDice={version:1,requestKey:active.request.requestKey,status,count:active.request.count,sides:active.request.sides,
      title:active.request.title,instruction:active.request.instruction,rollerLabel:active.request.rollerLabel,values:active.values.slice(),
      resumeKind:active.request.resumeKind,resumeData:cloneDiceData(active.request.resumeData)};
    if(save())return true;
    state.pendingDice=previousPending;
    return false;
  }
  function acknowledgeDiceRequest(requestKey){
    if(!requestKey||state.pendingDice?.requestKey!==requestKey||state.pendingDice.status!=='committed')return false;
    state.pendingDice=null;save();return true;
  }
  function acknowledgeCurrentDiceRequest(){return acknowledgeDiceRequest(state.pendingDice?.requestKey);}
  function renderManualDiceEntry(){
    const active=activeManualDiceRequest;
    if(!active)return;
    const complete=active.values.length===active.request.count;
    diceEntryResults.innerHTML=active.values.map((value,index)=>dieHtml({value,ariaLabel:`Die ${index+1}: ${value}`})).join('');
    diceEntryProgress.textContent=`${active.values.length} of ${active.request.count} entered`;
    diceEntryUndo.disabled=active.values.length===0||active.committed;
    diceEntryCommit.disabled=!complete||active.committed;
    $$('button',diceEntryKeypad).forEach(button=>button.disabled=complete||active.committed);
  }
  function enterManualDie(value){
    const active=activeManualDiceRequest;
    if(!active||active.committed||!Number.isInteger(value)||value<1||value>active.request.sides||active.values.length>=active.request.count)return false;
    active.values.push(value);
    if(!persistManualDice(active)){active.values.pop();return false;}
    renderManualDiceEntry();
    return true;
  }
  function undoManualDie(){
    const active=activeManualDiceRequest;
    if(!active||active.committed||!active.values.length)return false;
    const value=active.values.pop();
    if(!persistManualDice(active)){active.values.push(value);return false;}
    renderManualDiceEntry();
    return true;
  }
  function commitManualDiceResults(){
    const active=activeManualDiceRequest;
    if(!active||active.committed||active.values.length!==active.request.count)return false;
    active.committed=true;
    if(!persistManualDice(active,'committed')){active.committed=false;renderManualDiceEntry();return false;}
    renderManualDiceEntry();
    const results=active.values.slice(),resolve=active.resolve,returnFocus=active.returnFocus;
    activeManualDiceRequest=null;
    diceEntryDialog.close();
    if(returnFocus?.isConnected)try{returnFocus.focus({preventScroll:true});}catch{returnFocus.focus();}
    resolve(results);
    return true;
  }
  function requestManualDiceResults(request,restoredValues=[]){
    if(activeManualDiceRequest)return Promise.reject(new Error('A manual dice request is already active.'));
    let resolveRequest;
    const promise=new Promise(resolve=>{resolveRequest=resolve;});
    try{
      activeManualDiceRequest={request,values:restoredValues.slice(),resolve:resolveRequest,promise,committed:false,returnFocus:document.activeElement};
      if(!persistManualDice(activeManualDiceRequest))throw new Error('The manual dice request could not be saved.');
      diceEntryTitle.textContent=request.title;
      diceEntryInstruction.textContent=request.instruction;
      diceEntryRoller.textContent=request.rollerLabel;
      diceEntryRoller.hidden=!request.rollerLabel;
      diceEntryKeypad.innerHTML=Array.from({length:request.sides},(_,index)=>{
        const value=index+1;
        return `<button class="btn secondary" type="button" data-die-value="${value}" aria-label="Enter ${value}">${value}</button>`;
      }).join('');
      $$('[data-die-value]',diceEntryKeypad).forEach(button=>button.onclick=()=>enterManualDie(Number(button.dataset.dieValue)));
      renderManualDiceEntry();
      diceEntryDialog.showModal();
      requestAnimationFrame(()=>{
        const focusTarget=diceEntryKeypad.querySelector('button:not(:disabled)')||diceEntryCommit;
        focusTarget?.focus({preventScroll:true});
      });
    }catch(error){activeManualDiceRequest=null;throw error;}
    return promise;
  }
  async function requestDiceResults(request){
    const validatedRequest=validateDiceRequest(request);
    if(!isPvpMode())return rollDice(validatedRequest.count,validatedRequest.sides);
    const pending=state.pendingDice;
    if(pending){
      if(!pendingDiceMatches(validatedRequest,pending))throw new Error('A different manual dice request is already pending.');
      if(pending.status==='committed')return pending.values.slice();
      return requestManualDiceResults(validatedRequest,pending.values);
    }
    return requestManualDiceResults(validatedRequest);
  }
  function pendingDiceContextIsCurrent(pending=state.pendingDice){
    if(!pending||!isPvpMode()||state.completed||state.gameEnd)return false;
    const data=pending.resumeData||{};
    if(Number.isInteger(data.turningPoint)&&data.turningPoint!==state.turningPoint)return false;
    if(data.missionId&&data.missionId!==state.missionId)return false;
    if(data.npoId&&!state.roster.some(npo=>npo.id===data.npoId&&npo.wounds>0))return false;
    if(data.operativeId){
      const playerId=String(data.operativeId).replace(/^player:/,'');
      const livingPlayer=state.playerRoster.includes(playerId)&&!state.playerCasualtyIds.includes(playerId)&&playerOperativeState(playerId).inPlay!==false;
      const livingNpo=state.roster.some(npo=>npo.id===data.operativeId&&npo.wounds>0);
      if(!livingPlayer&&!livingNpo)return false;
    }
    if(data.targetId){
      const playerId=String(data.targetId).replace(/^player:/,'');
      const livingPlayer=state.playerRoster.includes(playerId)&&!state.playerCasualtyIds.includes(playerId)&&playerOperativeState(playerId).inPlay!==false;
      const livingNpo=state.roster.some(npo=>npo.id===data.targetId&&npo.wounds>0);
      if(!livingPlayer&&!livingNpo)return false;
    }
    if(data.eventInstanceId&&!state.strategyData?.events?.some(event=>event.instanceId===data.eventInstanceId&&event.status!=='resolved'))return false;
    if(pending.resumeKind==='strategy'&&state.phase!=='strategy')return false;
    if(pending.resumeKind==='combat'&&!state.combatState&&!state.lastActivation?.combatDraft&&!state.hotResolution&&!state.fightState)return false;
    if(pending.resumeKind==='rewards'&&!state.eventState.transactions?.[data.transactionId])return false;
    if(pending.resumeKind==='hot'&&(state.hotResolution?.id!==data.hotResolutionId||state.hotResolution.acknowledged))return false;
    if(pending.resumeKind==='player-activation'){
      const operativeId=state.combatState?.stage?.playerOperativeId;
      if(state.combatState?.side!=='player'||operativeId!==data.operativeId||missionActivationId('player',operativeId)!==data.activationId)return false;
    }
    if(pending.resumeKind==='npo-special-action'&&(state.lastActivation?.npoId!==data.npoId||!state.lastActivation.pendingAction||state.lastActivation.pendingAction.id!==data.actionId))return false;
    if(pending.resumeKind==='breach-sarcophagus'&&state.missionActionContext?.activationId!==data.activationId)return false;
    if(pending.resumeKind==='mission'){
      const operationId=data.operationId||data.resultId;
      if(operationId==='repairRoll')return state.phase==='strategy'&&state.strategyPipeline?.current==='mission-ready-hooks'&&state.missionReadyContext?.turningPoint===state.turningPoint;
      if(!['searchRoll','awakenRoll','directionRoll','distanceRoll'].includes(operationId)||state.missionActionContext?.missionId!==state.missionId)return false;
      const expectedAction={searchRoll:'searchTransponder',awakenRoll:missionEngine()?.actions?.awakenRoom,directionRoll:'auspexCalibration',distanceRoll:'auspexCalibration'}[operationId];
      if(state.missionActionContext.actionId!==expectedAction)return false;
    }
    return true;
  }
  async function resumePendingDiceWorkflow(){
    const pending=state.pendingDice;
    if(!pending)return false;
    if(!pendingDiceContextIsCurrent(pending)){
      state.pendingDice=null;save();
      return resumeCheckpointedGameplayContext();
    }
    const data=pending.resumeData||{};
    if(pending.resumeKind==='strategy'){await finishTurningPointStart();return true;}
    if(pending.resumeKind==='event'){await beginCurrentEvent();return true;}
    if(pending.resumeKind==='rewards'){
      const transaction=state.eventState.transactions?.[data.transactionId],npo=state.roster.find(item=>item.id===data.npoId);
      if(!transaction||!npo||transaction.committed){acknowledgeCurrentDiceRequest();return false;}
      delete transaction.requesting;
      await processRewardsOfAnnihilationQueue();
      return true;
    }
    if(pending.resumeKind==='combat'){
      if(state.fightState){await resumePersistedFight();return true;}
      if(state.combatState?.side==='player'){resolvePendingPlayerAttacks({...state.combatState.stage});return true;}
      if(state.lastActivation?.npoId){continueHumanNecronActivation();return true;}
      render();return true;
    }
    if(pending.resumeKind==='hot'){render();return true;}
    if(pending.resumeKind==='player-activation'){await completePlayerActivation({...state.combatState.stage,threatDiceResolving:false});return true;}
    if(pending.resumeKind==='breach-sarcophagus'){await performBreachSarcophagus({...state.combatState.stage},true);return true;}
    if(pending.resumeKind==='mission'){
      const operationId=data.operationId||data.resultId;
      if(['searchRoll','awakenRoll','directionRoll','distanceRoll'].includes(operationId))return resumeMissionActionContext();
      if(operationId==='repairRoll'){await continueTurningPointStart();return true;}
      return false;
    }
    if(pending.resumeKind==='npo-special-action'){
      return resumeNpoSpecialActionContext(data);
    }
    render();
    return true;
  }
  async function resumeMissionActionContext(){
    const context=state.missionActionContext;
    if(!context||context.missionId!==state.missionId)return false;
    if(context.actionId==='breachSarcophagus'&&state.combatState?.side==='player'){
      if(context.newTotal!=null&&state.combatState.stage?.sequential){await completePlayerActivation({...state.combatState.stage});return true;}
      await performBreachSarcophagus({...state.combatState.stage},true);return true;
    }
    if(context.actionId==='searchTransponder'){await performLocateItem(context.siteId,context.operativeId);return true;}
    if(context.actionId===missionEngine()?.actions?.awakenRoom){await performAwakenRoom(context.roomId);return true;}
    if(context.actionId==='auspexCalibration'){await performAuspexCalibration();return true;}
    return false;
  }
  function resumeNpoSpecialActionContext(data={}){
    const activation=state.lastActivation,n=state.roster.find(npo=>npo.id===(data.npoId||activation?.npoId));
    if(!n||!activation?.pendingAction)return false;
    const actionId=data.actionId||activation.pendingAction.id;
    if(activation.pendingAction.resolvedResult){
      const action=npoSpecialAction(n,activation.pendingAction.name);
      if(action)finishNpoSpecialAction(n,action,activation.pendingAction.resolvedResult,activation,activation.answers||{},activation.questionHistory||[]);
      return Boolean(action);
    }
    resolveNpoSpecialAction(n,activation,activation.answers||{},activation.questionHistory||[]);
    if(actionId==='geomantic-disturbance'){
      (activation.pendingAction.selectedTargets||[]).forEach(id=>{const input=$(`[data-disturbance-target="${CSS.escape(id)}"]`);if(input)input.checked=true;});
    }else{
      const targetId=data.targetId||activation.pendingAction.targetId;
      const select=$('#specialActionTarget');if(select&&targetId){select.value=targetId;select.dispatchEvent(new Event('change'));}
    }
    $('#confirmSpecialAction')?.click();return true;
  }
  async function resumeCheckpointedGameplayContext(){
    if(state.fightState){await resumePersistedFight();return true;}
    if(await resumeMissionActionContext())return true;
    if(state.lastActivation?.side==='player'&&state.lastActivation.committed&&state.lastActivation.completionHookPending){await completeHumanPlayerActivation();return true;}
    if(state.lastActivation?.npoId&&state.lastActivation.committed&&state.lastActivation.completionHookPending){await completeNpoActivation();return true;}
    if(isPvpMode()&&Boolean(state.lastActivation?.pendingAction?.diceResults||state.lastActivation?.pendingAction?.resolvedResult))return resumeNpoSpecialActionContext();
    if(state.combatState?.side==='player'){
      const stage={...state.combatState.stage};
      const resumableSequentialAction=stage.shoot||stage.melee||stage.missionFeatureCommitted||stage.missionBreachCommitted||Object.keys(stage.threatRolls||{}).length>0;
      if(stage.sequential&&!resumableSequentialAction){cancelCurrentHumanPlayerAction();return true;}
      resolvePendingPlayerAttacks(stage);return true;
    }
    if(activePlayerActivation()){renderHumanPlayerActionPicker();return true;}
    if(isPvpMode()&&state.lastActivation?.npoId&&!state.lastActivation.committed){continueHumanNecronActivation();return true;}
    if(state.phase==='strategy'&&state.strategyPipeline?.current==='mission-ready-hooks'){await continueTurningPointStart();return true;}
    if(state.phase==='strategy'&&['initiative','event'].includes(state.strategyPipeline?.current)){await finishTurningPointStart();return true;}
    return false;
  }
  async function missionDiceTotal(outcome,resultId,{count=1,sides=3,title='MISSION ROLL'}={}){
    const requestKey=diceRequestKey('mission-result',state.missionId,resultId);
    const supplied=outcome?.results?.[resultId]?.dice||state.missionRuntime?.pendingDiceResults?.[requestKey];
    if(Array.isArray(supplied)&&supplied.length===count&&supplied.every(value=>Number.isInteger(value)&&value>=1&&value<=sides))return supplied.reduce((sum,value)=>sum+value,0);
    const dice=await requestDiceResults({count,sides,title,instruction:`Roll ${count}D${sides} on the tabletop and enter each result.`,requestKey,resumeKind:'mission',resumeData:{missionId:state.missionId,resultId}});
    state.missionRuntime=state.missionRuntime||{};state.missionRuntime.pendingDiceResults={...(state.missionRuntime.pendingDiceResults||{}),[requestKey]:[...dice]};save();acknowledgeDiceRequest(requestKey);
    return dice.reduce((sum,value)=>sum+value,0);
  }
  diceEntryUndo.addEventListener('click',undoManualDie);
  diceEntryCommit.addEventListener('click',commitManualDiceResults);
  diceEntryDialog.addEventListener('cancel',event=>event.preventDefault());
  diceEntryDialog.addEventListener('keydown',event=>{
    if(!activeManualDiceRequest)return;
    const value=Number(event.key);
    if(Number.isInteger(value)&&value>=1&&value<=activeManualDiceRequest.request.sides){event.preventDefault();enterManualDie(value);}
    else if(event.key==='Backspace'){event.preventDefault();undoManualDie();}
    else if(event.key==='Enter'){
      event.preventDefault();
      if(!diceEntryCommit.disabled)commitManualDiceResults();
    }
  });
  window.TombWorldDiceProvider=Object.freeze({requestDiceResults,acknowledgeDiceRequest,resumePendingDiceWorkflow});
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
  async function effectiveEnforcerNpoWeaponProfile(npo,profile,attackType){
    if(!tombWorldEventActive('enforcer-of-the-phaerons')||weaponHasRule(profile,'ceaseless')||!activeNpos().some(item=>item.type==='Royal Warden'))return effectiveWeaponProfile(profile,{attackerSide:'npo',attackType,sameRoomAsRoyalWarden:false});
    const sameRoom=npo.type==='Royal Warden'||await askYesNoRuleQuestion('Enforcer of the Phaerons',`Is ${npoName(npo)} in the same room as a Royal Warden?`);
    const transaction=eventTransaction(`enforcer-room:${state.turningPoint}:${state.activationNumber}:${npo.id}:${attackType}`,{definitionAnswers:{}});
    transaction.definitionAnswers.sameRoomAsRoyalWarden=sameRoom;save();
    return effectiveWeaponProfile(profile,{attackerSide:'npo',attackType,sameRoomAsRoyalWarden:sameRoom});
  }
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
  function choosePriorityPlayerTarget(candidateIds){
    return [...candidateIds].sort((a,b)=>playerCurrentWounds(a)-playerCurrentWounds(b)
      ||Number(state.playerActivatedIds.includes(a))-Number(state.playerActivatedIds.includes(b))
      ||String(a).localeCompare(String(b)))[0]||null;
  }
  function chooseTabletopOperatives(title,question,candidateIds,{humanChoosesAll=false,allowNone=true}={}){
    return new Promise(resolve=>{
      const candidates=candidateIds.filter(id=>inPlayLivingPlayerOperativeIds().includes(id));
      showModal(title,`<p id="stage3TabletopQuestion">${escapeHtml(question)}</p><div class="checklist" aria-describedby="stage3TabletopQuestion">${candidates.map(id=>`<label class="check-row"><input type="${humanChoosesAll?'checkbox':'radio'}" name="stage3Target" value="${escapeHtml(id)}"><span>${escapeHtml(playerTargetLabel(id))}</span></label>`).join('')||'<p class="muted">No other living Player operatives are available.</p>'}</div><div class="wizard-actions">${allowNone?'<button class="btn ghost" id="stage3NoEligible">No eligible operative</button>':''}<button class="btn primary" id="stage3ConfirmTargets">Continue</button></div>`);
      const finish=ids=>{closeModal();resolve(ids);};
      $('#stage3NoEligible')?.addEventListener('click',()=>finish([]));
      $('#stage3ConfirmTargets').onclick=()=>finish($$('[name="stage3Target"]:checked',modal).map(input=>input.value));
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
  function ceaselessScuttlingAvailable(roster=state.roster){
    return roster.some(npo=>npo.type==='Canoptek Macrocyte Warrior');
  }
  function ceaselessScuttlingEligible(turningPoint=state.turningPoint,roster=state.roster,strategyData=state.strategyData){
    const living=roster.filter(npo=>npo.type==='Canoptek Macrocyte Warrior'&&npo.wounds>0).length;
    const deployed=roster.filter(npo=>npo.battlefieldState==='deployed'&&npo.wounds>0).length;
    return ceaselessScuttlingAvailable(roster)&&turningPoint>1&&living<3&&deployed<MAX_NPOS
      &&strategyData?.ceaselessScuttlingTurningPoint!==turningPoint;
  }
  function ceaselessScuttlingUnavailableReason(turningPoint=state.turningPoint,roster=state.roster,strategyData=state.strategyData){
    if(strategyData?.ceaselessScuttlingTurningPoint===turningPoint)return 'Unavailable: A Ceaseless Scuttling was already resolved this Turning Point.';
    const living=roster.filter(npo=>npo.type==='Canoptek Macrocyte Warrior'&&npo.wounds>0).length;
    if(living>=3)return `Unavailable: ${living} of 3 Macrocyte Warriors remain.`;
    const deployed=roster.filter(npo=>npo.battlefieldState==='deployed'&&npo.wounds>0).length;
    if(deployed>=MAX_NPOS)return `Unavailable: the battlefield already has the maximum ${MAX_NPOS} NPOs.`;
    return '';
  }
  function ceaselessScuttlingSoloWeaponId(){
    const definition=npoDefinition('Canoptek Macrocyte Warrior');
    const saved=state.strategyData?.ceaselessScuttlingWeaponId;
    if(definition.loadoutOptions.some(option=>option.id===saved))return saved;
    const generatedResult=npoGenerationTable.find(result=>result.type===definition.type);
    const weaponId=generatedWeaponId(generatedResult);
    state.strategyData.ceaselessScuttlingWeaponId=weaponId;
    save();
    return weaponId;
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
    state.strategyData.ceaselessScuttlingTurningPoint=state.turningPoint;
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
      reinforcement:options.reinforcement||null,
      replacementOptions:Array.isArray(options.replacementOptions)?[...options.replacementOptions]:null,
      replacementTransactionId:options.replacementTransactionId||null
    };
  }
  function commitPvpNpoReplacement(npo,selectedType){
    const options=npo?.replacementOptions||[],transaction=state.variantState.replacementTransactions[npo?.replacementTransactionId];
    if(!isPvpMode()||!transaction||transaction.committed||!options.includes(selectedType))return npo;
    if(selectedType===npo.type){transaction.selectedType=selectedType;transaction.committed=true;delete npo.replacementOptions;delete npo.replacementTransactionId;log(`${currentTombWorldVariant().name}: the Necron controller retained ${npoName(npo)}.`);return npo;}
    const remaining=state.roster.filter(item=>item.id!==npo.id),replacement=createNpo(selectedType,`${selectedType} ${npo.displayNumber||''}`.trim(),{
      deployed:false,ready:npo.ready,dormant:false,reinforcement:npo.reinforcement,allocationContext:{roster:remaining}
    });
    replacement.order=npo.order;replacement.missionRoom=npo.missionRoom;
    if(!commitNpoRoster([...remaining,replacement],'apply the Necron controller replacement'))return null;
    const replaceId=list=>(list||[]).map(id=>id===npo.id?replacement.id:id);
    state.reinforcementState.operativeIds=replaceId(state.reinforcementState.operativeIds);
    if(state.startingNpoGeneration){state.startingNpoGeneration.deployedNpoIds=replaceId(state.startingNpoGeneration.deployedNpoIds);state.startingNpoGeneration.reserveNpoIds=replaceId(state.startingNpoGeneration.reserveNpoIds);}
    Object.values(state.missionState?.awakenedRooms||{}).forEach(awakening=>{awakening.operativeIds=replaceId(awakening.operativeIds);});
    transaction.selectedType=selectedType;transaction.committed=true;transaction.createdNpoId=replacement.id;
    log(`${currentTombWorldVariant().name}: the Necron controller replaced ${npo.type} with ${selectedType}.`);
    return replacement;
  }
  function setupCrownworldCrawlerPair(crawler,transactionId){
    const replacement=replaceNpoAtSetup({type:crawler?.type,npoId:crawler?.id,transactionId});
    if(!replacement?.mandatoryPair||state.variantState.crownworldFirstCrawlerConsumed)return {replaced:false,npos:[crawler]};
    const transactions=state.variantState.replacementTransactions,prior=transactions[transactionId];
    if(prior?.committed)return {replaced:true,npos:prior.createdIds.map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean)};
    const otherDeployed=activeNpos().filter(npo=>npo.id!==crawler.id).length;
    if(otherDeployed+2>MAX_NPOS)return {replaced:false,blocked:true,npos:[]};
    const weaponId=isPvpMode()?'hyperphase-sword':(Math.random()<0.5?'hyperphase-sword':'warscythe');
    const remaining=state.roster.filter(npo=>npo.id!==crawler.id);
    const warden=createNpo('Royal Warden','Royal Warden',{ready:true,dormant:false,allocationContext:{roster:remaining}});
    const lychguard=createNpo('Lychguard','Lychguard',{weaponId,ready:true,dormant:false,allocationContext:{roster:[...remaining,warden]}});
    warden.createdBy='crownworld-first-crawler';lychguard.createdBy='crownworld-first-crawler';
    if(!commitNpoRoster([...remaining,warden,lychguard],'set up the Crownworld replacement pair'))return {replaced:false,blocked:true,npos:[]};
    transactions[transactionId]={id:transactionId,originalNpoId:crawler.id,createdIds:[warden.id,lychguard.id],lychguardWeaponId:weaponId,instruction:"Set up the Lychguard within the Royal Warden's Control Range.",committed:true};
    state.variantState.crownworldFirstCrawlerConsumed=true;
    log(`Crownworld: ${npoName(crawler)} was replaced by Royal Warden and Lychguard (${weaponId==='warscythe'?'Warscythe':'Hyperphase sword'}). Set up the Lychguard within the Royal Warden's Control Range.`);
    return {replaced:true,npos:[warden,lychguard]};
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
    if(npo.id===state.activeNpoId&&state.lastActivation?.npoId===npo.id&&!state.lastActivation?.committed)return {status:'ACTIVE',className:'active'};
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
    return `<span class="operative-status-wounds">${current} / ${maximum}</span>`;
  }
  function operativeStatusRow({name,type,current,maximum,status,side}){
    const eliminated=status==='ELIMINATED';
    const active=!eliminated&&status==='ACTIVE';
    const wounded=!eliminated&&current>0&&current<maximum;
    return `<div class="operative-status-row${eliminated?' eliminated':''}${active?' active':''}${wounded?' wounded':''}"><strong>${escapeHtml(name)}</strong>${statusWoundsHtml(current,maximum)}<span class="operative-status-type">${escapeHtml(type)}</span><span class="operative-status-value">${status}</span></div>`;
  }
  function renderOperativeStatusPanel(activePlayerId=null){
    const eligible=state.screen==='game'&&operativeStatusMedia.matches;
    const visible=eligible&&showOperativeStatusPreference;
    operativeStatusToggle.hidden=!eligible;
    operativeStatusToggle.setAttribute('aria-pressed',String(visible));
    operativeStatusToggle.setAttribute('aria-label',visible?'Hide operative status':'Show operative status');
    gameWorkspace.classList.toggle('operative-status-visible',visible);
    operativeStatusPanel.hidden=!visible;
    if(!visible)return;
    const npoRows=sortedNposForDisplay(state.roster).map(npo=>{
      const status=npoStatus(npo);
      return operativeStatusRow({name:npoName(npo),type:npoDefinition(npo.type)?.name||npo.type,current:Math.max(0,npo.wounds),maximum:npo.maxWounds,status,side:'npo'});
    }).join('');
    const playerRows=(state.playerRoster||[]).map(id=>{
      const definition=playerDefinition(id),maximum=Number(definition?.wounds||0);
      return operativeStatusRow({name:playerName(id),type:definition?.role||'Operative',current:Math.max(0,playerCurrentWounds(id)),maximum,status:playerStatus(id,activePlayerId),side:'player'});
    }).join('');
    operativeStatusPanel.innerHTML=`<section class="operative-status-section npo"><h2>${escapeHtml(opponentSingularLabel())} Operatives</h2><div class="operative-status-list">${npoRows||`<p class="muted">No ${escapeHtml(opponentSingularLabel())} operatives</p>`}</div></section><section class="operative-status-section player"><h2>${escapeHtml(playerSideLabel())} Operatives</h2><div class="operative-status-list">${playerRows||`<p class="muted">No ${escapeHtml(playerSideLabel())} operatives</p>`}</div></section>`;
    requestAnimationFrame(fitOperativeStatusPanel);
  }
  function fitOperativeStatusPanel(){
    if(operativeStatusPanel.hidden)return;
    const minimumOperativeCardWidth=220;
    const sections=$$('.operative-status-section',operativeStatusPanel);
    const availableHeight=operativeStatusPanel.clientHeight;
    const listHeightNeeded=list=>{
      const listTop=list.getBoundingClientRect().top;
      return [...list.children].reduce((height,row)=>Math.max(height,row.getBoundingClientRect().bottom-listTop),0);
    };
    const sectionChromeHeight=section=>{
      const list=$('.operative-status-list',section);
      const sectionStyle=getComputedStyle(section);
      return list.getBoundingClientRect().top-section.getBoundingClientRect().top
        +(parseFloat(sectionStyle.paddingBottom)||0)+(parseFloat(sectionStyle.borderBottomWidth)||0);
    };
    const sectionHeightNeeded=section=>{
      const list=$('.operative-status-list',section);
      return listHeightNeeded(list)+sectionChromeHeight(section);
    };
    const totalHeightNeeded=()=>sections.reduce((total,section)=>total+sectionHeightNeeded(section),0);
    operativeStatusPanel.style.removeProperty('--status-npo-height');
    operativeStatusPanel.style.removeProperty('--status-player-height');
    sections.forEach(section=>{
      const list=$('.operative-status-list',section);
      section.classList.remove('two-column','extra-compact','allow-scroll');
      list.style.removeProperty('--status-column-rows');
    });
    sections.forEach(section=>{
      const list=$('.operative-status-list',section);
      if(totalHeightNeeded()<=availableHeight)return;
      const twoColumnGap=parseFloat(getComputedStyle(list).columnGap)||0;
      const twoColumnCardWidth=(list.clientWidth-twoColumnGap)/2;
      if(twoColumnCardWidth>=minimumOperativeCardWidth){
        section.classList.add('two-column');
        list.style.setProperty('--status-column-rows',Math.ceil(list.children.length/2));
      }
    });
    sections.forEach(section=>{
      if(totalHeightNeeded()<=availableHeight)return;
      section.classList.add('extra-compact');
    });
    const needs=sections.map(section=>sectionHeightNeeded(section));
    const minimums=sections.map((section,index)=>{
      const list=$('.operative-status-list',section);
      const rows=[...list.children];
      const visibleCards=Math.min(rows.length,index===0?1:2);
      const gap=parseFloat(getComputedStyle(list).rowGap)||0;
      const cardsHeight=rows.slice(0,visibleCards).reduce((height,row)=>height+row.getBoundingClientRect().height,0);
      return sectionChromeHeight(section)+cardsHeight+Math.max(0,visibleCards-1)*gap;
    });
    let heights=[...needs];
    if(needs[0]+needs[1]<=availableHeight){
      heights[0]+=availableHeight-needs[0]-needs[1];
    }else{
      heights=[...minimums];
      const minimumTotal=minimums[0]+minimums[1];
      if(minimumTotal>availableHeight){
        heights=minimums.map(height=>height*availableHeight/minimumTotal);
      }
      let remaining=Math.max(0,availableHeight-heights[0]-heights[1]);
      [...sections.keys()].sort((a,b)=>(needs[a]-minimums[a])-(needs[b]-minimums[b])).forEach(index=>{
        const addition=Math.min(remaining,Math.max(0,needs[index]-minimums[index]));
        heights[index]+=addition;
        remaining-=addition;
      });
      heights[0]+=remaining;
    }
    operativeStatusPanel.style.setProperty('--status-npo-height',`${heights[0]}px`);
    operativeStatusPanel.style.setProperty('--status-player-height',`${heights[1]}px`);
    sections.forEach(section=>{
      const list=$('.operative-status-list',section);
      if(list.scrollHeight>list.clientHeight+1)section.classList.add('allow-scroll');
    });
  }
  function scheduleOperativeStatusLayout(){
    clearTimeout(operativeStatusResizeTimer);
    operativeStatusResizeTimer=setTimeout(()=>{renderOperativeStatusPanel();},120);
  }
  function syncAppHeaderHeight(){
    document.documentElement.style.setProperty('--app-header-height',`${appHeader.getBoundingClientRect().height}px`);
  }
  syncAppHeaderHeight();
  const appHeaderResizeObserver=typeof ResizeObserver==='function'?new ResizeObserver(()=>{
    syncAppHeaderHeight();
    scheduleOperativeStatusLayout();
  }):null;
  appHeaderResizeObserver?.observe(appHeader);
  operativeStatusToggle.addEventListener('click',()=>{
    showOperativeStatusPreference=!showOperativeStatusPreference;
    localStorage.setItem(OPERATIVE_STATUS_PREFERENCE_KEY,String(showOperativeStatusPreference));
    renderOperativeStatusPanel();
  });
  if(operativeStatusMedia.addEventListener)operativeStatusMedia.addEventListener('change',scheduleOperativeStatusLayout);
  else operativeStatusMedia.addListener?.(scheduleOperativeStatusLayout);
  window.addEventListener('resize',()=>{syncAppHeaderHeight();scheduleOperativeStatusLayout();});
  window.addEventListener('orientationchange',()=>{syncAppHeaderHeight();scheduleOperativeStatusLayout();});

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

  function resetOutcomeScroll(){
    const scrollContainer=document.scrollingElement||document.documentElement;
    scrollContainer.scrollTop=0;
    scrollContainer.scrollLeft=0;
  }

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
    void TombWorldNarration.playOutcome(state.missionId,outcome);
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
    handleTransponderCarrierIncapacitation();
    const outcome=missionOutcome(timing);
    if(outcome&&missionEngine()?.type==='transponder'&&state.missionState){state.missionState.completed=true;state.missionState.outcome=outcome;}
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
      state.gradeMilestoneSequence=(state.gradeMilestoneSequence||0)+1;
      state.gradeMilestone={grade:afterGrade,threat:state.threat,label:threatLabel(),instanceId:`grade:${afterGrade}:${state.gradeMilestoneSequence}`,narrationSeen:false};
      log(`Threat reached Grade ${afterGrade}: ${threatLabel()}.`);
    }
  }
  function escapeHtml(s){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
  function rosterCategoryRequirementText(category,accessible=false){
    const parts=[];
    const required=Number(category.requiredCount||0);
    const maximum=Number(category.maxCount??Infinity);
    if(required)parts.push(`${accessible?'required':'Req'} ${required}`);
    if(Number.isFinite(maximum))parts.push(`${accessible?'maximum':'Max'} ${maximum}`);
    return parts;
  }
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

  function startingNpoDeploymentComplete(generation=state.startingNpoGeneration){
    const deployedIds=generation?.deployedNpoIds||[],deployedIdSet=new Set(deployedIds);
    const reserveIds=generation?.reserveNpoIds||[],reserveIdSet=new Set(reserveIds);
    return deployedIds.length>0&&deployedIdSet.size===deployedIds.length
      &&reserveIdSet.size===reserveIds.length
      &&deployedIds.every(id=>!reserveIdSet.has(id)&&state.roster.some(npo=>npo.id===id&&npo.deployed&&npo.battlefieldState==='deployed'))
      &&reserveIds.every(id=>state.roster.some(npo=>npo.id===id&&!npo.deployed&&npo.battlefieldState==='reserve'));
  }

  function setStartingNposDeployed(deployed){
    const generation=state.startingNpoGeneration;
    if(!generation)return false;
    const selected=new Set(generation.deployedNpoIds||[]);
    if(deployed&&!state.variantState.crownworldFirstCrawlerConsumed){
      const crawler=state.roster.find(npo=>selected.has(npo.id)&&npo.type===TOMB_CRAWLER_TYPE);
      if(crawler){
        const pair=setupCrownworldCrawlerPair(crawler,`crownworld:starting:${crawler.id}`);
        if(pair.blocked){
          state.setupChecks['starting-npos']=false;
          showToast('The Royal Warden and Lychguard pair requires two available NPO battlefield slots.');
          return false;
        }
        if(pair.replaced){
          selected.delete(crawler.id);
          pair.npos.forEach(npo=>selected.add(npo.id));
          generation.deployedNpoIds=[...selected];
        }
      }
    }
    state.roster.filter(npo=>selected.has(npo.id)).forEach(npo=>{
      npo.deployed=deployed;
      npo.battlefieldState=deployed?'deployed':'reserve';
    });
    const reserves=new Set(generation.reserveNpoIds||[]);
    state.roster.filter(npo=>reserves.has(npo.id)).forEach(npo=>{
      npo.deployed=false;
      npo.battlefieldState='reserve';
    });
    state.setupChecks['starting-npos']=Boolean(deployed);
    return true;
  }

  function generateRoster(generation){
    const m=mission(),count=MAX_NPOS,formula=generation.calculation;
    const previousRoster=state.roster;
    state.roster=[];
    for(let i=0;i<count;i++){
      const request=tombWorldVariantHook('startingRosterGeneration',availableGenerationResult());
      const result=resolveVariantNpoRequest(request,{transactionId:`starting:${i}:${request?.type||'none'}`});
      if(!result){
        console.warn(`[NPO inventory] ${m.name} requested ${count} models, but only ${state.roster.length} legal generated models were available.`);
        state.roster=previousRoster;showToast('A complete legal NPO roster could not be generated.');return null;
      }
      state.roster.push(createNpo(result.type,`${result.type} ${i+1}`,{weaponId:result.weaponId,ready:false,deployed:false,replacementOptions:result.replacementOptions,replacementTransactionId:result.replacementTransactionId}));
    }
    const validation=validateNpoRoster(state.roster,state.tombWorldVariant);
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
    if(state.fightState&&fightDicePoolsComplete(state.fightState)&&!fightCompletionInProgress&&!modal.open){
      if(restoreFightContinuation()){
        if(state.fightState.history.length)renderFightResolution();
        else renderFightRoll(state.fightState,{animate:false});
      }
    }

    if(movedToNewStep){
      requestAnimationFrame(()=>{
        window.scrollTo({top:0,left:0,behavior:'auto'});
        document.documentElement.scrollTop=0;
        document.body.scrollTop=0;
        const setupHeading=document.querySelector('.wizard-shell .progress-head h2');
        if(setupHeading){setupHeading.tabIndex=-1;setupHeading.focus({preventScroll:true});}
      });
    }
  }

  function guideInstructionsHtml(full=false){
    const overview=`<section class="help-section">
      <h3>What the Guide does</h3>
      <p>Tomb World Battle Guide walks you through setup, Turning Points, alternating Player and NPO activations, Threat, reinforcements, combat, and the battle record. ${isPvpMode()?'The second player chooses Necron actions and targets while the Guide handles legal choices, rules, state, and bookkeeping.':'The Guide controls NPO decisions while you control your Kill Team.'} You still move models, measure distances, determine line of sight, and apply any operative-specific rules on the tabletop.</p>
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

    const ai=isPvpMode()?`<section class="help-section ai-help-section">
      <h3>How Necron decisions work</h3>
      <p>The second player controls the Necrons and chooses their legal actions, targets, and weapon profiles. The Guide tracks action points, wounds, effects, activation state, and mission consequences; it does not choose Necron actions or targets.</p>
      <p>Roll physical gameplay dice on the tabletop and enter the results when prompted. The appropriate player confirms visibility, range, control range, and other tabletop facts.</p>
    </section>`:`<section class="help-section ai-help-section">
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
      <p>Select a Ready Player operative, choose one legal action, and resolve it completely. The Guide commits that action and its AP before returning to the action picker. Canceling a later uncommitted action never rolls back actions already completed.</p>
    </section>`;

    const npoRoster=`<section class="help-section">
      <h3>Tomb World NPO roster</h3>
      <p>The supported pool uses the physical models in the Tomb World box: the <strong>Canoptek Circle</strong> (Geomancer, Canoptek Tomb Crawler, Canoptek Macrocyte Warrior, Canoptek Macrocyte Accelerator, and Canoptek Macrocyte Reanimator), <strong>Necron Warriors</strong>, and <strong>Canoptek Scarab Swarms</strong>.</p>
      <p>NPO lists are alphabetical, and applicable loadouts are selected for each operative instance. NPO portraits are intentionally not displayed. The Obelisk Node Matrix is not supported by the Guide.</p>
      <p>Current saves and older saves use the v7 migration flow. If an active legacy battle contains an unsupported retired NPO, the Guide asks before returning that battle to setup so a legal roster can be regenerated.</p>
    </section>`;

    const quick=`<section class="help-section quick-reference-grid">
      <article><h4>${escapeHtml(playerSideLabel())}</h4><p>${isPvpMode()?'The operatives from the selected player-controlled Kill Team.':'Your solo kill-team operatives.'}</p></article>
      <article><h4>${escapeHtml(opponentSingularLabel())}</h4><p>${isPvpMode()?'A Necron operative controlled by the second player.':'A non-player operative controlled by the Guide.'}</p></article>
      <article><h4>APL</h4><p>The number of action points an operative may spend during its activation.</p></article>
      <article><h4>THREAT LEVEL</h4><p>A 0–15 alert meter. Higher grades generate more reinforcements and events.</p></article>
      <article><h4>Ready</h4><p>The operative can still activate during this Turning Point.</p></article>
      <article><h4>Expended</h4><p>The operative has activated or is otherwise unavailable.</p></article>
    </section>`;

    if(full)return presentSideTerminology(overview+npoRoster+flow+ai+combat+quick);
    return presentSideTerminology(npoRoster+ai+quick);
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
    options:{title:'Optional Rules & Expansions',subtitle:'Configure optional game content before the Necron roster is generated.'},
    deploy:{title:'Deploy Kill Teams',subtitle:'Place both forces on the battlefield and confirm deployment.'},
    ready:{title:'Ready to Begin',subtitle:'Review the mission, then begin Turning Point 1.'}
  };
  function activeSetupSteps(){
    const steps=['mission','killzone'];
    if(hasMultiplePlayerTeams())steps.push('team');
    steps.push('playerRoster','options','deploy','ready');
    return steps;
  }
  function currentSetupStepId(){
    const steps=activeSetupSteps();
    state.setupStep=Math.max(0,Math.min(Number(state.setupStep||0),steps.length-1));
    return steps[state.setupStep];
  }
  function renderSetup(){
    if(!state.gameMode){renderGameModeSelection();return;}
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
  function renderGameModeSelection(){
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Choose Game Mode</h2><p>Choose who will control the Necrons for this battle.</p></div></div><section class="wizard-card"><div class="team-select-grid game-mode-grid">
      <button type="button" class="team-select-card" data-game-mode="solo" aria-label="Solo: play your Kill Team against Necrons controlled by the Guide"><div class="team-select-card-head"><div><strong>Solo</strong><small>Guide-controlled Necrons</small></div></div><p>Play your Kill Team against Necrons controlled by the Guide.</p></button>
      <button type="button" class="team-select-card" data-game-mode="pvp" aria-label="Player vs. Player: one player controls the selected Kill Team and the second player controls the Necrons"><div class="team-select-card-head"><div><strong>Player vs. Player</strong><small>Two players</small></div></div><p>One player controls the selected Kill Team. The second player controls the Necrons.</p></button>
      </div><div class="wizard-actions"><button class="btn ghost" id="gameModeBack" type="button">Back</button></div></section></div>`;
    $('#gameModeBack').onclick=()=>{state.screen='home';save();render();};
    $$('[data-game-mode]').forEach(button=>button.onclick=()=>{
      if(state.gameMode)return;
      state.gameMode=button.dataset.gameMode;
      save();render();
    });
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
  function invalidateStartingNpoSetup(){
    state.roster=[];
    state.startingNpoGeneration=null;
    delete state.setupChecks['starting-npos'];
  }
  function setTombWorldVariant(variantId){
    if(state.screen!=='setup'||!TOMB_WORLD_VARIANTS[variantId]?.available||variantId===state.tombWorldVariant)return false;
    state.tombWorldVariant=variantId;
    invalidateStartingNpoSetup();
    state.variantState={crownworldFirstCrawlerConsumed:false,replacementTransactions:{}};
    state.eventState.available=[...eventDeck,...tombWorldEventDeckAdditions()].map(card=>card.instanceId);
    state.eventState.used=[];
    state.eventState.active=[];
    state.eventState.transactions={};
    state.eventState.rewardsTriggers=[];
    return true;
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
    return checks.map(check=>`<label class="check-row"><input type="checkbox" data-check="${escapeHtml(check.id)}" ${state.setupChecks[check.id]?'checked':''}><span><strong>${escapeHtml(presentSideTerminology(check.label))}</strong><small>Confirm this step on the physical board.</small></span></label>`).join('');
  }
  function setupContent(stepId){
    if(stepId==='mission') return `<h3>Which mission are you playing?</h3><p>You can review the objective before committing.</p><div class="mission-list">${missions.map(m=>`<button class="mission-choice ${state.missionId===m.id?'selected':''}" data-mission="${m.id}" aria-pressed="${state.missionId===m.id}"><div class="team-select-card-head"><div><small>${m.number}</small><strong>${m.name}</strong></div>${state.missionId===m.id?'<span>✓</span>':''}</div><span>${escapeHtml(presentSideTerminology(m.brief))}</span></button>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupHome">Back</button><button class="btn primary" id="setupNext" ${state.missionId?'':'disabled'}>Next</button></div>`;
    if(stepId==='killzone'){
      const m=mission();
      const checks=missionSetupChecks('killzone');
      const allChecked=checks.length>0&&checks.every(check=>state.setupChecks[check.id]);
      return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${escapeHtml(presentSideTerminology(m.objective))}</p>${boardSvg(m.id)}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllSetup" ${allChecked?'disabled':''}>Check All</button></div><div class="checklist">${setupChecklistHtml(checks)}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allChecked?'':'disabled'}>Board Ready</button></div>`;
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
      const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners??Infinity);
      const maxGravis=Number(playerTeamData?.selectionRules?.maxGravis||1);
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
          category={
            id:categoryId,
            label:metadata.label||categoryId,
            order:Number(metadata.order??categories.length),
            requiredCount:metadata.requiredCount,
            maxCount:metadata.maxCount,
            operatives:[]
          };
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
        const constraints=rosterCategoryRequirementText(category);
        const accessibleConstraints=rosterCategoryRequirementText(category,true);
        const categoryStatus=`${categorySelected} selected${constraints.length?` · ${constraints.join(' · ')}`:''}`;
        const accessibleStatus=`${categorySelected} selected${accessibleConstraints.length?`, ${accessibleConstraints.join(', ')}`:''}`;
        return `<section class="roster-category"><button type="button" class="roster-category-heading" data-roster-category-toggle="${escapeHtml(category.id)}" aria-expanded="${expanded}" aria-controls="${panelId}" aria-label="${escapeHtml(`${category.label}, ${accessibleStatus}`)}"><span class="roster-category-title"><span class="roster-category-indicator" aria-hidden="true">›</span>${escapeHtml(category.label)}</span><span class="roster-category-status" aria-hidden="true">${escapeHtml(categoryStatus)}</span></button><div class="player-roster-grid roster-category-content" id="${panelId}" ${expanded?'':'hidden'}>${cards}</div></section>`;
      }).join('');
      const selectionPrompt=minRoster===maxRoster?`Select exactly ${maxRoster} operatives.`:`Select between ${minRoster} and ${maxRoster} operatives.`;
      const validation=playerRosterValidation([...selected]);
      const valid=validation.valid&&requiredLeaderSelected&&(!hasGravis||(gravisCount>=1&&gravisCount<=maxGravis));
      const rosterCount=minRoster===maxRoster?`${selected.size} of ${maxRoster} operatives`:`${selected.size} of ${maxRoster} operatives (minimum ${minRoster})`;
      return `<h3>Choose your ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Kill Team')} roster</h3><p>${selectionPrompt}</p><div class="setup-bulk-row"><button class="btn secondary" id="randomPlayerTeam">Random Team</button></div><div class="roster-categories">${sections}</div><section class="summary-box selected-roster-summary" aria-label="Selected roster"><div class="selected-roster-heading"><strong>Selected roster</strong><span class="selected-roster-readiness${valid?' ready':''}">${valid?'✓ Ready':'Incomplete'}</span></div><p><strong>Roster Status:</strong> ${rosterCount}</p><div>${selectedDefs.length?inlineOperativeList(selectedDefs.map(o=>escapeHtml(playerName(o.id)))):'No operatives selected.'}</div></section><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${valid?'':'disabled'}>Roster Ready</button></div>`;
    }
    if(stepId==='options'){
      const variantOptions=Object.values(TOMB_WORLD_VARIANTS).filter(variant=>variant.available).map(variant=>`<label class="variant-card"><input type="radio" name="tombWorldVariant" value="${escapeHtml(variant.id)}" aria-describedby="variant-${escapeHtml(variant.id)}-description" ${state.tombWorldVariant===variant.id?'checked':''}><span><strong>${escapeHtml(variant.name)}</strong>${variant.id==='standard'?'':`<span class="rule-classification official">Official Expansion - White Dwarf 517</span>`}<small id="variant-${escapeHtml(variant.id)}-description">${escapeHtml(variant.summary)}</small></span></label>`).join('');
      const deadlyOption=isPvpMode()?''
        : `<label class="check-row deadly-encounters-option"><input id="deadlyEncountersEnabled" type="checkbox" aria-label="Enable Deadly Encounters: Tomb Worlds official expansion" ${state.deadlyEncountersEnabled?'checked':''}><span><strong>Deadly Encounters: Tomb Worlds</strong><span class="rule-classification official">Official Expansion - White Dwarf 521</span><small>Official expansion. Reveal persistent Room and Objective Features using the official D33 tables when Player operatives explore the tomb. PvE Player actions reveal features; NPOs never reveal them, but revealed features can affect NPOs. This independent expansion increases battlefield complexity and danger.</small></span></label>`;
      return `<h3>Choose optional game content</h3><p>Choose one variant for this battle. The starting Necron roster is generated after this step.</p><fieldset class="variant-selector"><legend>Tomb World Variant</legend><div class="variant-card-grid">${variantOptions}</div></fieldset><section class="other-optional-rules" aria-labelledby="other-optional-rules-heading"><h4 id="other-optional-rules-heading">Other Optional Rules</h4><div class="checklist optional-rules"><label class="check-row restless-tomb-option"><input id="restlessTombEnabled" type="checkbox" aria-label="Enable Restless Tomb house rule" ${state.restlessTombEnabled?'checked':''}><span><strong>Restless Tomb</strong><span class="rule-classification">House Rule</span><small>Beginning with Turning Point 2, resolve at least one Tomb World event during each Strategy Phase, regardless of Threat Grade. Turning Point 1 is unaffected, and standard event rules may require additional events at higher Threat. This optional house rule increases activity and difficulty.</small></span></label>${deadlyOption}</div></section><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext">Continue</button></div>`;
    }
    if(stepId==='deploy'){
      const generation=state.startingNpoGeneration;
      const hasStartingNpos=generation.deployedNpoIds.length>0;
      const dice=generation.dice.map(value=>dieHtml({value,kind:'hit'})).join('');
      const missionRoll=hasStartingNpos
        ? `<div class="starting-npo-event" id="startingNpoEvent" role="status" aria-live="polite"><small>MISSION ROLL</small><div class="dice-row ${generation.animationShown?'settled':'animated-roll'}" id="startingNpoDice">${generation.animationShown?dice:generation.dice.map(()=>rollingDieHtml()).join('')}</div><div class="starting-npo-result" id="startingNpoResult" ${generation.animationShown?'':'hidden'}><strong>${generation.missionRoll} Starting ${escapeHtml(opponentPluralLabel())}</strong><span>${generation.calculation}</span></div></div>`
        : `<div class="no-npo-message" role="status"><small>STARTING ${escapeHtml(opponentPluralLabel().toUpperCase())}</small><strong>None</strong><span>This mission begins with no ${escapeHtml(opponentPluralLabel())} deployed. Enemy operatives will enter play later according to the mission rules.</span></div>`;
      const placementChecks=missionSetupChecks('deploy');
      const deploymentCheck=placementChecks.find(check=>check.id==='starting-npos');
      const otherPlacementChecks=placementChecks.filter(check=>check.id!=='starting-npos');
      const deploymentInstruction=`Deploy the ${generation.deployedNpoIds.length} selected starting ${opponentPluralLabel()}.`;
      const deployedNpoRoster=inlineOperativeList(sortedNposForDisplay(generation.deployedNpoIds.map(id=>state.roster.find(npo=>npo.id===id)).filter(Boolean)).map(npo=>escapeHtml(npoName(npo))));
      const playerRoster=inlineOperativeList((state.playerRoster||[]).map(id=>escapeHtml(playerName(id))));
      const playerRosterHtml=playerRoster?`<span class="deployment-roster">${playerRoster}</span>`:'';
      const deploymentDetails=presentSideTerminology(mission().startingNpos?.deployment||'Use the mission deployment rules.');
      const allNposPlaced=startingNpoDeploymentComplete(generation);
      const npoDeploymentSatisfied=!hasStartingNpos||allNposPlaced;
      const deploymentRow=hasStartingNpos&&deploymentCheck?`<label class="check-row deployment-check"><input id="npoDeployed" type="checkbox" data-check="${escapeHtml(deploymentCheck.id)}" ${state.setupChecks[deploymentCheck.id]&&allNposPlaced?'checked':''}><span><strong>${deploymentInstruction}</strong><span class="deployment-roster">${deployedNpoRoster}</span><small>${escapeHtml(deploymentDetails)}</small></span></label>`:'';
      const requiredPlacementChecks=hasStartingNpos?placementChecks:otherPlacementChecks;
      const allPlacementChecked=requiredPlacementChecks.every(check=>state.setupChecks[check.id]);
      const {minRoster,maxRoster}=playerRosterLimits();
      const playerValid=playerRosterValidation().valid;
      return `<h3>Deploy Kill Teams</h3><p>Place the generated ${escapeHtml(opponentSingularLabel())} roster and selected ${escapeHtml(playerSideLabel())} roster, then confirm every mission deployment requirement.</p>${missionRoll}${factionGuidanceHtml()}${hasStartingNpos?`<div class="setup-bulk-row"><button class="btn secondary" id="checkAllDeployment" ${playerValid&&state.playerDeployed&&npoDeploymentSatisfied&&allPlacementChecked?'disabled':''}>Check All</button></div>`:''}<div class="checklist deployment-checklist">${deploymentRow}${setupChecklistHtml(otherPlacementChecks)}<label class="check-row deployment-check"><input id="playerDeployed" type="checkbox" ${state.playerDeployed?'checked':''} ${playerValid?'':'disabled'}><span><strong>Deploy ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||(isPvpMode()?'Kill Team':'Player'))} Kill Team</strong>${playerRosterHtml}<small>All selected ${escapeHtml(playerSideLabel())} operatives are on the battlefield.</small></span></label></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${playerValid&&state.playerDeployed&&npoDeploymentSatisfied&&allPlacementChecked?'':'disabled'}>Deployment Complete</button></div>`;
    }
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(presentSideTerminology(rule.name||'Special Rule'))}</strong>${rule.timing?`<small>${escapeHtml(presentSideTerminology(rule.timing))}</small>`:''}<p>${escapeHtml(presentSideTerminology(rule.summary||''))}</p></div>`).join('');
    const deadlyBriefing=isPvpMode()?'':`<section class="mission-rule" aria-labelledby="briefing-deadly-encounters-title"><strong id="briefing-deadly-encounters-title">Deadly Encounters</strong><small>Official Expansion<br>White Dwarf 521</small><p>${state.deadlyEncountersEnabled?'Enabled':'Disabled'}</p></section>`;
    const selectedVariant=currentTombWorldVariant();
    const variantBriefing=selectedVariant.briefing===selectedVariant.name?'':`<p>${escapeHtml(selectedVariant.briefing)}</p>`;
    const variantSource=selectedVariant.id==='standard'?'<small>Tomb World Variant</small>':'<small>Tomb World Variant<br>Tombs Beyond Counting · Official Expansion<br>White Dwarf 517</small>';
    return `<h3>Mission Briefing</h3><div class="mission-briefing"><div class="mission-briefing-section mission-heading"><span>Mission</span><strong>${escapeHtml(m.number)} · ${escapeHtml(m.name)}</strong></div><div class="mission-briefing-section"><h4>Objective</h4><p>${escapeHtml(presentSideTerminology(m.objective))}</p></div><div class="mission-briefing-section"><h4>Special Rules</h4>${rules||`<p>${escapeHtml(presentSideTerminology(missionSpecial()))}</p>`}</div><div class="mission-briefing-section optional-rules-summary"><h4>Optional Rules &amp; Expansions</h4><section class="mission-rule" aria-labelledby="briefing-variant-title"><strong id="briefing-variant-title">${escapeHtml(selectedVariant.name)}</strong>${variantSource}${variantBriefing}</section><section class="mission-rule" aria-labelledby="briefing-restless-tomb-title"><strong id="briefing-restless-tomb-title">Restless Tomb</strong><small>House Rule</small><p>${state.restlessTombEnabled?'On':'Off'}</p></section>${deadlyBriefing}<small class="optional-rules-instruction">Go Back to Optional Rules &amp; Expansions to change these settings before beginning the battle.</small></div></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function advanceSetupStep(stepId){
    if(setupNavigationInProgress)return;
    if(currentSetupStepId()!==stepId)return;
    if(stepId==='team'&&!canBuildPlayerRoster()){showToast('Wait for the selected Kill Team to finish loading.');return;}
    setupNavigationInProgress=true;
    if(stepId==='playerRoster')assignPlayerDisplayNumbers();
    if(stepId==='killzone')clearPendingBoardSetupMissionIntro();
    const steps=activeSetupSteps();state.setupStep=Math.min(steps.length-1,state.setupStep+1);save();render();
    if(stepId==='mission')enterBoardSetup();
    setupNavigationInProgress=false;
  }

  function bindSetup(stepId){
    $$('.mission-choice').forEach(button=>button.onclick=()=>{
      const missionId=button.dataset.mission;
      state.missionId=missionId;
      state.missionState=freshMissionState(mission());
      state.missionRuntime=null;
      state.tracker=0;
      state.setupChecks={};
      state.roster=[];
      state.startingNpoGeneration=null;
      save();

      const narrationUnlock=TombWorldNarration.isPlaybackEnabled()
        ? TombWorldNarration.activateFromGesture()
        : Promise.resolve(false);
      reconcileAmbientActiveState();
      const ambientPlayback=shouldAmbientBeActive()
        ? TombWorldAmbient.playFromGesture()
        : Promise.resolve(false);

      render();
      void Promise.allSettled([narrationUnlock,ambientPlayback]);
      setTimeout(()=>loadObjectiveMission(missionId).then(()=>{
        if(state.missionId===missionId)save();
      }),0);
    });
    $('#setupHome')?.addEventListener('click',()=>{state.gameMode=null;save();render();});
    $('#setupBack')?.addEventListener('click',()=>{if(stepId==='killzone'){clearPendingBoardSetupMissionIntro();TombWorldNarration.stop();}state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>advanceSetupStep(stepId));
    $$('[data-player-team]').forEach(button=>button.onclick=()=>selectPlayerTeam(button.dataset.playerTeam));
    $$('[data-check]').filter(c=>c.id!=='npoDeployed').forEach(c=>c.onchange=()=>{state.setupChecks[c.dataset.check]=c.checked;save();render();});
    $('#checkAllSetup')?.addEventListener('click',()=>{missionSetupChecks('killzone').forEach(check=>{state.setupChecks[check.id]=true;});save();render();});
    $('#randomPlayerTeam')?.addEventListener('click',()=>{randomPlayerRoster();save();render();});
    if(stepId==='deploy')runStartingNpoGeneration();
    $('#npoDeployed')?.addEventListener('change',e=>{
      setStartingNposDeployed(e.target.checked);
      save();render();
    });
    $('#checkAllDeployment')?.addEventListener('click',()=>{
      missionSetupChecks('deploy').filter(check=>check.id!=='starting-npos').forEach(check=>{state.setupChecks[check.id]=true;});
      setStartingNposDeployed(true);
      if(playerRosterValidation().valid)state.playerDeployed=true;
      save();render();
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
    $('#deadlyEncountersEnabled')?.addEventListener('change',e=>{if(isPvpMode())return;state.deadlyEncountersEnabled=e.target.checked;save();render();});
    $$('input[name="tombWorldVariant"]').forEach(input=>input.addEventListener('change',e=>{if(e.target.checked&&setTombWorldVariant(e.target.value)){save();render();}}));
    $('#beginGame')?.addEventListener('click',async()=>{
      state.screen='game';state.tab='play';state.turningPoint=0;state.phase='between';state.nextSide='player';state.playerCount=(state.playerRoster||[]).length;state.playerReady=state.playerCount;
      if(!backgroundManifest.length)await loadBackgroundManifest();
      ensureGameBackgroundSelection();
      objectiveEngine?.refreshMissionContext(missionLifecycleContext());
      if(!state.playerWounds||Object.keys(state.playerWounds).length===0)initializePlayerWounds();
      state.roster.forEach(n=>n.ready=false);log(`Mission started: ${mission().name}.`);if(deadlyEncountersActive())log('Deadly Encounters: Tomb Worlds enabled (official PvE expansion, White Dwarf 521).');startTurningPoint();
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
      requestAnimationFrame(()=>{resetOutcomeScroll();$('#reviewCompletedMission')?.focus({preventScroll:true});});
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
    const transponder=missionEngine()?.type==='transponder'?state.missionState:null;
    const value=transponder?(transponder.transponderFound?'TRANSPONDER FOUND':`SEARCH ${transponder.searchSitesResolved||0}/3`):model?(model.completed?'COMPLETE':`${model.value} / ${model.target}`):'DETAILS';
    const completeMark=model?.completed?'<span class="mission-complete-mark" aria-hidden="true">✓ </span>':'';
    const status=transponder?transponder.transponderFound?`transponder found, ${transponder.carrierId?`carried by ${playerName(transponder.carrierId)}`:'on battlefield with no carrier'}`:`${transponder.searchSitesResolved||0} of 3 search sites resolved`:model?`${model.value} of ${model.target}${model.completed?', objective complete':''}`:'details';
    const name=model?.name||mission()?.name||'selected mission';
    return `<button class="hud-cell mission-hud" id="missionHud" type="button" aria-label="Mission Details, ${escapeHtml(name)}, ${escapeHtml(status)}"><small>${escapeHtml(label)}</small><strong>${completeMark}${escapeHtml(value)}</strong></button>`;
  }

  function hud(){return `<div class="hud"><div><small>Turning<span class="portrait-break"><br></span> Point</small><strong>${state.turningPoint||'Setup'}</strong></div><button class="hud-cell hud-threat" id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"><small>Threat<span class="portrait-break"><br></span> Level</small><strong>${state.threat}</strong></button><div><small>Grade<span class="portrait-break"><br></span> Level</small><strong>${threatGrade()}</strong></div><div><small>${escapeHtml(playerSideLabel())}<span class="portrait-break"><br></span> Ready</small><strong>${state.playerReady}</strong></div><div><small>${escapeHtml(opponentSingularLabel())}<span class="portrait-break"><br></span> Ready</small><strong>${readyNpos().length}</strong></div>${missionHudHtml()}</div><div class="threat-strip ${threatAdjustOpen?'':'hidden'}" id="threatAdjuster"><div><strong>THREAT LEVEL: ${threatLabel()}</strong><small>${threatGrade()===3?'Maximum Grade':`Next Grade at Threat Level ${nextGradeThreat()}`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function livingPlayerOptions(selected=''){
    return inPlayPlayerOperativeIds().filter(id=>!state.playerCasualtyIds.includes(id)).map(id=>`<option value="${escapeHtml(id)}" ${id===selected?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
  }

  const missionProgressRenderers = {
    escape:(engine,progress,{readOnly=false}={})=>{
      const escaped=new Set(progress.escapedIds);
      const rows=(state.playerRoster||[]).map(id=>{const incapacitated=state.playerCasualtyIds.includes(id), operativeState=playerOperativeState(id), escapedHere=escaped.has(id)&&operativeState.offBoardReason==='escaped', unavailable=operativeState.inPlay===false&&!escapedHere;return `<div class="mission-objective-row"><span><strong>${escapeHtml(playerName(id))}</strong><small>${escapedHere?'Escaped · Off Board':unavailable?`Off Board${operativeState.offBoardReason?` · ${escapeHtml(operativeState.offBoardReason)}`:''}`:incapacitated?'Eliminated':'Still in the killzone'}</small></span>${readOnly||incapacitated||unavailable?'':`<button class="btn compact ${escapedHere?'secondary':'ghost'}" data-mission-escaped="${escapeHtml(id)}">${escapedHere?'Undo Escape':'Confirm Escape'}</button>`}</div>`;}).join('');
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
      const sites=engine.sites.map(site=>{const result=progress.sites[site.id]||'available';const status={available:'Available',cleared:'Cleared',transponder:'Transponder',removed:'Removed / resolved'}[result]||'Available';return `<div class="mission-objective-row"><span><strong>${escapeHtml(site.label)}</strong><small>${status}</small></span></div>`;}).join('');
      if(!progress.transponderFound)return `<p><strong>Status: SEARCHING</strong></p><p>Find the transponder and escape through Player A's killzone edge.</p><div class="mission-objective-list">${sites}</div><div class="summary-box"><strong>Search Sites Resolved: ${progress.searchSitesResolved||0} / 3</strong></div>`;
      const carrier=progress.carrierId?playerName(progress.carrierId):'On battlefield / no carrier';
      const controls=readOnly?'':`<div class="wizard-actions"><button class="btn primary" id="transponderEscape" ${progress.carrierId&&isPlayerOperativeInPlay(progress.carrierId)&&!state.playerCasualtyIds.includes(progress.carrierId)&&!progress.escaped?'':'disabled'}>Confirm Escape</button></div>`;
      return `<p><strong>Status: EXTRACTION</strong></p><p>Escape through Player A's killzone edge while carrying the transponder.</p><div class="mission-objective-list">${sites}</div><div class="summary-box"><strong>Transponder:</strong> Found<br><strong>Location:</strong> ${escapeHtml(engine.sites.find(site=>site.id===progress.transponderMarkerId)?.label||'Objective marker')}<br><strong>Carrier:</strong> ${escapeHtml(carrier)}${progress.escaped?' · Escaped':''}</div>${controls}`;
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

  async function performLocateItem(siteId,carrierId,stage=state.combatState?.stage){
    if(!siteId||!carrierId||!stage)return;
    const progress=state.missionState,existing=progress?.sites?.[siteId];
    if(existing&&existing!=='available'){state.missionActionContext=null;acknowledgeCurrentDiceRequest();return;}
    const transactionId=`${activePlayerActivation()?.activationId}:${activePlayerActivation()?.pendingAction?.actionSequence}:${siteId}`;
    if(progress.transactions?.[transactionId])return;
    state.missionActionContext={missionId:state.missionId,actionId:'searchTransponder',siteId,operativeId:carrierId,activationId:activePlayerActivation()?.activationId,transactionId};save();
    const available=missionEngine().sites.filter(site=>!progress.sites[site.id]||progress.sites[site.id]==='available');
    const automatic=available.length===1;
    const outcome=automatic?null:objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('searchTransponder',{...missionLifecycleContext(),activationId:activePlayerActivation()?.activationId,operativeId:carrierId,siteId})):null;
    if(!automatic&&objectiveEngine&&!outcome)return;
    const result=automatic?null:await missionDiceTotal(outcome,'searchRoll',{title:'LOCATE ITEM'});
    const found=automatic||TombWorldMissionEngine.resolveRemainingEntityRoll(result,available.length).found;
    if(progress.transactions?.[transactionId])return;
    if(!commitHumanPlayerAction(stage,{deferContinuation:true,deferPersistence:true}))return;
    progress.transactions={...(progress.transactions||{}),[transactionId]:{siteId,...(result===null?{}:{roll:result}),committed:true}};
    progress.sites[siteId]=found?'transponder':'cleared';
    progress.lastRoll={siteId,...(result===null?{}:{roll:result}),result:found?'transponder found':'false signal'};
    if(found){
      progress.transponderFound=true;progress.transponderMarkerId=siteId;progress.carrierId=carrierId;progress.transponderStatus='carried';progress.searchSitesResolved=missionEngine().sites.length;
      missionEngine().sites.forEach(site=>{if(site.id!==siteId&&(!progress.sites[site.id]||progress.sites[site.id]==='available'))progress.sites[site.id]='removed';});
    }else progress.searchSitesResolved=missionEngine().sites.filter(site=>progress.sites[site.id]==='cleared').length;
    const marker=missionEngine().sites.find(site=>site.id===siteId),history=objectiveEngine?.getMissionRuntime().history||[],entry=history.at(-1);
    const summary=found?`${playerName(carrierId)} found the transponder at ${marker.label}.`:`${playerName(carrierId)} searched ${marker.label}: false signal.`;
    if(entry&&!automatic){entry.type='transponder-search';entry.summary=summary;entry.title=summary;entry.transactionId=transactionId;}
    else if(automatic)objectiveEngine?.recordMissionHistory({id:transactionId,type:'transponder-search',title:summary,summary,operativeId:carrierId,turningPoint:state.turningPoint,transactionId},missionLifecycleContext());
    state.missionActionContext=null;save();acknowledgeCurrentDiceRequest();
    const removed=found?missionEngine().sites.filter(site=>site.id!==siteId&&progress.sites[site.id]==='removed').map(site=>site.label.replace(/Objective Marker /i,'')).join(' and '):'';
    const body=found?`<p><strong>${escapeHtml(marker.label)} contains the transponder.</strong></p><p>${escapeHtml(playerName(carrierId))} is carrying the transponder.</p>${removed?`<p>Remove Objective Markers ${escapeHtml(removed)} from the killzone.</p>`:''}`:`<p><strong>${escapeHtml(marker.label)} was a false signal.</strong></p><p>Remove ${escapeHtml(marker.label)} from the killzone.</p>`;
    const diceResult=result===null?'':`<div class="summary-box"><strong>D3: ${result}</strong></div>`;
    showModal(found?'TRANSPONDER FOUND':'ITEM NOT FOUND',`${body}${diceResult}<div class="wizard-actions"><button class="btn primary" id="continueLocateItem" data-dialog-focus>Continue</button></div>`);
    $('#continueLocateItem').onclick=()=>continueAfterCommittedHumanAction();
  }

  let transponderEscapePending=false;
  async function confirmTransponderEscape(){
    const progress=state.missionState,carrierId=progress?.carrierId;
    if(transponderEscapePending||missionEngine()?.type!=='transponder'||!progress?.transponderFound||!carrierId||progress.escaped||progress.completed||state.gameEnd||state.playerCasualtyIds.includes(carrierId)||!isPlayerOperativeInPlay(carrierId))return;
    const transactionId=`transponder-escape:${carrierId}`;
    if(progress.transactions?.[transactionId])return;
    transponderEscapePending=true;
    const button=$('#transponderEscape');if(button)button.disabled=true;
    const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('recordTransponderEscape',{...missionLifecycleContext(),activationId:transactionId,operativeId:carrierId})):null;
    if(objectiveEngine&&!outcome){transponderEscapePending=false;if(button?.isConnected)button.disabled=false;return;}
    progress.transactions={...(progress.transactions||{}),[transactionId]:{committed:true}};
    progress.escaped=true;progress.extractionConfirmed=true;progress.transponderStatus='escaped';progress.completed=true;progress.outcome='victory';
    const summary=`${playerName(carrierId)} escaped with the transponder.`;
    const entry=objectiveEngine?.getMissionRuntime().history?.at(-1);if(entry){entry.type='transponder-escape';entry.title=summary;entry.summary=summary;}
    save();completeMission('victory');transponderEscapePending=false;
  }

  function handleTransponderCarrierIncapacitation(){
    const progress=state.missionState,carrierId=progress?.carrierId;
    if(missionEngine()?.type!=='transponder'||!progress?.transponderFound||!carrierId||!state.playerCasualtyIds.includes(carrierId)||progress.escaped)return false;
    progress.carrierId=null;progress.transponderStatus='onBattlefield';
    const summary=`Transponder dropped when ${playerName(carrierId)} was incapacitated.`;
    objectiveEngine?.recordMissionHistory({id:`transponder-drop:${carrierId}:${state.turningPoint}:${state.activationNumber}`,type:'transponder-drop',title:summary,summary,turningPoint:state.turningPoint},missionLifecycleContext());
    log(`${mission().name}: ${summary}`);save();
    if(livingPlayerOperativeCount()>0)showToast(`TRANSPONDER DROPPED — ${playerName(carrierId)} was incapacitated. Update the marker on the tabletop.`);
    return true;
  }

  async function performAwakenRoom(roomId){
    if(!roomId)return;
    if(state.missionState?.awakenedRooms?.[roomId]){state.missionActionContext=null;acknowledgeCurrentDiceRequest();return;}
    const actionId=missionEngine().actions?.awakenRoom;
    state.missionActionContext={missionId:state.missionId,actionId,roomId};save();
    const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction(actionId,{...missionLifecycleContext(),roomId})):null;
    if(objectiveEngine&&!outcome)return;
    const awakenRoll=await missionDiceTotal(outcome,'awakenRoll',{title:'AWAKEN ROOM'});
    const count=Math.min(5,awakenRoll+threatGrade()),ids=[];
    for(let i=0;i<count&&activeNpos().length<MAX_NPOS;i++){
      const rawResult=availableGenerationResult();if(!rawResult)break;
      const request=replaceMissionRequestedNpo({...rawResult,source:'mission-05-awaken-room'});
      const result=resolveVariantNpoRequest(request,{transactionId:`mission:${state.missionId}:${roomId}:${i}:${request.type}`});
      const n=createNpo(result.type,`${result.type} ${roomId}`,{weaponId:result.weaponId,ready:true,dormant:false,deployed:false,order:'Conceal',replacementOptions:result.replacementOptions,replacementTransactionId:result.replacementTransactionId});
      n.missionRoom=roomId;state.roster.push(n);ids.push(n.id);
    }
    state.missionState.awakenedRooms[roomId]={count:ids.length,operativeIds:ids,placementConfirmed:false};
    state.missionActionContext=null;
    save();acknowledgeCurrentDiceRequest();
    updateMissionProgress(`${roomId} awakened; generated ${ids.length} ready NPO(s) with Conceal orders for tabletop placement.`);
  }

  async function performAuspexCalibration(){
    if(state.missionState?.auspexCalibrations?.[state.turningPoint]){state.missionActionContext=null;acknowledgeCurrentDiceRequest();return;}
    state.missionActionContext={missionId:state.missionId,actionId:'auspexCalibration',turningPoint:state.turningPoint};save();
    const outcome=objectiveEngine?await runMissionEvent(()=>objectiveEngine.executeMissionAction('auspexCalibration',missionLifecycleContext())):null;
    if(objectiveEngine&&!outcome)return;
    const directionRoll=await missionDiceTotal(outcome,'directionRoll',{title:'AUSPEX CALIBRATION - ESCAPE MARKER DIRECTION'});
    const distanceRoll=await missionDiceTotal(outcome,'distanceRoll',{title:'AUSPEX CALIBRATION - ESCAPE MARKER DISTANCE'}),distance=distanceRoll+3;
    const instruction=directionRoll===1?`Move the Escape marker ${distance} inches left.`:directionRoll===2?'Do not move the Escape marker.':`Move the Escape marker ${distance} inches right.`;
    state.missionState.auspexCalibrations[state.turningPoint]={directionRoll,distance,instruction};
    state.missionActionContext=null;log(`Auspex Calibration: ${instruction}`);save();acknowledgeCurrentDiceRequest();render();
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
    $('#transponderEscape')?.addEventListener('click',confirmTransponderEscape);
    $('#resolveMissionAction')?.addEventListener('click',confirmMissionAction);
    $$('[data-awaken-room]').forEach(button=>button.onclick=()=>performAwakenRoom(button.dataset.awakenRoom));
    $$('[data-confirm-room-placement]').forEach(button=>button.onclick=()=>{
      const awakening=state.missionState.awakenedRooms[button.dataset.confirmRoomPlacement];awakening.placementConfirmed=true;
      if(!state.variantState.crownworldFirstCrawlerConsumed){
        const crawler=state.roster.find(npo=>awakening.operativeIds.includes(npo.id)&&npo.type===TOMB_CRAWLER_TYPE);
        if(crawler){
          const pair=setupCrownworldCrawlerPair(crawler,`crownworld:mission:${state.missionId}:${button.dataset.confirmRoomPlacement}:${crawler.id}`);
          if(pair.blocked){awakening.placementConfirmed=false;showToast('The Royal Warden and Lychguard pair could not be set up within the 10-NPO limit.');save();render();return;}
          if(pair.replaced)awakening.operativeIds=awakening.operativeIds.flatMap(id=>id===crawler.id?pair.npos.map(npo=>npo.id):[id]);
        }
      }
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

  async function narrateVisibleGradeMilestone(){
    const milestone=state.gradeMilestone;
    if(!milestone||milestone.narrationSeen||!$('.grade-milestone')||!TombWorldNarration.isPlaybackEnabled())return false;
    const instanceId=milestone.instanceId;
    if(gradeNarrationInFlight.has(instanceId))return false;
    gradeNarrationInFlight.add(instanceId);
    try{
      const started=await TombWorldNarration.playGradeEscalation(milestone.grade,instanceId);
      const currentMilestone=state.gradeMilestone;
      if(started&&currentMilestone?.instanceId===instanceId){
        currentMilestone.narrationSeen=true;
        save();
      }else if(!started&&currentMilestone?.instanceId===instanceId){
        narrationGestureRecoveryRequired=true;
        armAudioGestureRecovery();
      }
      return started;
    }finally{
      gradeNarrationInFlight.delete(instanceId);
    }
  }

  function renderPlay(){
    const gradeDescription=state.gradeMilestone?gradeGameplayDescription(state.gradeMilestone.grade,{threat:state.gradeMilestone.threat,turningPoint:Math.max(2,state.turningPoint),suggestedInitiative:state.strategyData?.suggestedInitiative,restlessTombEnabled:state.restlessTombEnabled}):null;
    const milestone=gradeDescription?`<section class="grade-milestone" role="dialog" aria-labelledby="grade-milestone-heading" aria-describedby="grade-milestone-description"><div><small>THREAT ESCALATION</small><h2 id="grade-milestone-heading">Grade ${gradeDescription.grade}: ${escapeHtml(gradeDescription.name)}</h2><span>${escapeHtml(gradeDescription.threatRange)}</span><section id="grade-milestone-description" class="grade-gameplay-changes" aria-labelledby="grade-gameplay-heading"><h3 id="grade-gameplay-heading">GAMEPLAY CHANGES</h3><ul>${gradeDescription.effects.map(effect=>`<li>${escapeHtml(effect.text)}</li>`).join('')}</ul></section></div><button class="btn ghost compact" id="dismissGradeMilestone">Dismiss</button></section>`:'';
    app.innerHTML=hud()+milestone+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${state.phase!=='strategy'?activeEventEffectsHtml():''}${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
    bindPlay();
    requestAnimationFrame(narrateVisibleStrategyEvents);
    requestAnimationFrame(narrateVisibleGradeMilestone);
    if(gradeDescription)requestAnimationFrame(()=>$('#dismissGradeMilestone')?.focus({preventScroll:true}));
  }

  function activeEventEffectsHtml(){
    const active=state.eventState.active||[];
    if(!active.length)return '';
    const heading=`ACTIVE TOMB WORLD ${active.length===1?'EVENT':'EVENTS'}`;
    return `<section class="card active-events-panel"><details class="active-events-details"><summary class="active-events-summary" aria-label="${active.length===1?'Active Tomb World Event':'Active Tomb World Events'}, ${active.length} active"><span>${heading}</span><span class="active-events-count">${active.length} ACTIVE</span></summary><div class="active-events-content">${active.map(event=>`<div class="summary-box"><strong>${escapeHtml(presentSideTerminology(event.title))}</strong><br>${escapeHtml(presentSideTerminology(event.text))}</div>`).join('')}</div></details></section>`;
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
      return `<section class="next-card"><span class="phase">TURNING POINT ${state.turningPoint} COMPLETE</span><h2>Battle summary</h2><div class="turn-summary-grid"><div><small>Threat</small><strong>${state.tpStartThreat??state.threat} → ${state.threat}</strong><span>${threatChanged?'Changed this Turning Point':'No change'}</span></div><div><small>Grade</small><strong>${state.tpStartGrade??threatGrade()} → ${threatGrade()}</strong><span>${gradeChanged?'Grade increased':'Grade unchanged'}</span></div><div><small>${escapeHtml(opponentPluralLabel())} destroyed</small><strong>${npoLosses}</strong><span>This Turning Point</span></div><div><small>${escapeHtml(playerSideLabel())} casualties</small><strong>${playerLosses}</strong><span>This Turning Point</span></div></div><h3>Score and clean up</h3><p>Score mission objectives, resolve end-of-turn effects, and confirm all temporary markers have been cleared.</p>${missionProgressHtml()}<div class="checklist"><label class="check-row required-confirmation-row"><input id="endChecked" type="checkbox"><span><strong>End-of-turn steps complete</strong><small>Objectives scored, temporary effects resolved, and physical tokens cleaned up.</small></span></label></div><button class="btn primary big-action" id="finishTp" disabled>Finish Turning Point</button></section>`;
    }
    setNextActivation(state.nextSide || state.initiative || 'player');
    if(state.phase==='end'){save();return nextStepCard();}
    if(state.nextSide==='player' && playerOperativesRemaining()>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ${activationProgressLabel()}</span><h2>${escapeHtml(playerSideLabel())} Activation</h2><p>Activate one ${escapeHtml(playerSideLabel())} operative on the tabletop. After it completes, the Guide will alternate to a ${escapeHtml(opponentSingularLabel())} if one is ready.</p><button class="btn primary big-action" id="playerActivation">Activate an Operative</button></section>`;
    if(state.nextSide==='npo' && readyNpos().length>0)return `<section class="next-card npo-activation-card"><span class="phase">${escapeHtml(opponentSingularLabel().toUpperCase())} ACTIVATION · ${activationProgressLabel()}</span><h2 class="npo-activation-title">${escapeHtml(opponentSingularLabel())} Activation</h2><p class="npo-activation-meta">${isPvpMode()?`Choose a Ready ${escapeHtml(opponentSingularLabel())} to activate.`:`Identify the next ready ${escapeHtml(opponentSingularLabel())} using the Threat Principle.`}</p><button class="btn primary big-action" id="npoActivation">Activate ${escapeHtml(opponentSingularLabel())}</button></section>`;
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

  function soloCeaselessScuttlingPending(){return !isPvpMode()&&ceaselessScuttlingEligible();}

  function canLeaveStrategyActions(){return !missionStrategyPending()&&!soloCeaselessScuttlingPending();}

  function canLeaveStrategyEvents(){
    const d=state.strategyData||{};
    return !d.eventPending&&(d.events||[])[d.eventIndex||0]?.status!=='drawn'&&!strategyRequiredRedrawPending();
  }

  function strategyHasNoDownstreamWork(){
    const d=state.strategyData||{},reinforcements=state.reinforcementState||{};
    const presentation=strategyEventPresentation(d);
    const reinforcementProcessed=reinforcements.turningPoint===state.turningPoint
      &&state.strategyPipeline?.completed?.includes('reinforcement');
    return presentation.required===0
      &&!d.eventPending
      &&!presentation.events.some(event=>event.status==='drawn')
      &&!strategyRequiredRedrawPending()
      &&canLeaveStrategyEvents()
      &&reinforcementProcessed
      &&reinforcements.status==='complete'
      &&!(reinforcements.operativeIds||[]).length
      &&!(Number(reinforcements.blocked)||0)
      &&!(Number(reinforcements.blockedByCapacity)||0)
      &&!(Number(reinforcements.blockedByInventory)||0)
      &&!(Number(d.blocked)||0);
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
    const scuttlingPending=soloCeaselessScuttlingPending();
    const completeFromActions=strategyHasNoDownstreamWork();
    const scuttlingAvailable=ceaselessScuttlingAvailable();
    const scuttlingEligible=ceaselessScuttlingEligible();
    const scuttlingCard=state.turningPoint>1&&scuttlingAvailable&&(isPvpMode()||scuttlingEligible)
      ? `<section class="card reinforcement-card"><p class="eyebrow">STRATEGIC GAMBIT</p><h3>A Ceaseless Scuttling</h3><p>${scuttlingEligible?(isPvpMode()?'Fewer than three Macrocyte Warriors remain. You may reuse an incapacitated miniature to set up a new operative instance.':'Fewer than three Macrocyte Warriors remain. The tomb sets up another Macrocyte Warrior ready with a Conceal order wholly within the NPO drop zone.'):escapeHtml(ceaselessScuttlingUnavailableReason())}</p><button class="btn secondary" id="ceaselessScuttling" ${scuttlingEligible?'':'disabled'}>${isPvpMode()?'Use':'Resolve'} A Ceaseless Scuttling</button></section>`:'';
    const actionsHtml=`${missionStrategyPromptHtml()}${factionGuidanceHtml('gambits')}${scuttlingCard}`;
    const actionsBlocked=missionPending||scuttlingPending;
    const blockedReason=missionPending?'Resolve the mandatory mission Strategy Phase rule before continuing.':scuttlingPending?'Resolve A Ceaseless Scuttling before continuing.':'';
    const gambitChecklistItem=isPvpMode()?'Review optional Strategic Gambits.':'Resolve applicable Strategic Gambits.';
    return `${completeFromActions?'':strategyProgressHtml('actions')}<h2 id="strategy-step-heading">Resolve Strategy Phase Actions</h2><div class="strategy-phase-guide"><h3>Strategy Phase Checklist</h3><ol><li>Generate Command Points as required.</li><li>Play any Strategic Ploys.</li><li>Resolve abilities and mission rules.</li><li>${gambitChecklistItem}</li></ol></div>${actionsHtml||'<p class="strategy-empty-message">No additional guided Strategy Phase actions are required.</p>'}${strategyNavigationHtml({continueId:completeFromActions?'completeStrategyFromActions':'continueStrategyEvents',continueLabel:completeFromActions?'Strategy Phase Complete':'Continue to Tomb World Events',disabled:actionsBlocked,disabledReason:blockedReason})}`;
  }

  function strategyEventsStepHtml(d){
    const presentation=strategyEventPresentation(d);
    const displayedEvents=presentation.events.filter((event,index)=>event.status!=='drawn'||index===d.eventIndex);
    const activeEffects=state.eventState.active||[];
    const unmatched=activeEffects.filter(active=>!displayedEvents.some(event=>strategyEventActiveEffect(event,[active]))).map(event=>`<div class="summary-box"><strong>${escapeHtml(presentSideTerminology(event.title))}</strong><br>${escapeHtml(presentSideTerminology(event.text))}</div>`).join('');
    const requirement=strategyEventRequirementLabel(d,presentation), summary=strategyEventSummary(presentation);
    const hasEvents=presentation.required||presentation.cardsDrawn||unmatched;
    const content=hasEvents?`${requirement?`<p class="strategy-event-requirement">${escapeHtml(presentSideTerminology(requirement))}</p>`:''}<p class="strategy-event-summary" aria-label="${escapeHtml(presentSideTerminology(summary.accessible))}">${escapeHtml(presentSideTerminology(summary.visible))}</p>${displayedEvents.map(event=>strategyEventHtml(event,activeEffects)).join('')}${unmatched?`<h3 class="strategy-section-heading">Other Active Event Effects</h3>${unmatched}`:''}`:'<div class="summary-box"><strong>No Tomb World Event</strong><p>No Tomb World event is required during this Strategy Phase.</p></div>';
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
    const deployedSection=deployedNpos.length?`<div class="reinforcement-deployed"><h3>${deployedNpos.length} ${escapeHtml(deployedNpos.length===1?opponentSingularLabel():opponentPluralLabel())} deployed</h3><ul class="reinforcement-list">${deployedNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul></div>`:'';
    const pendingSection=pendingNpos.length?`<div class="reinforcement-pending"><h3>Deploy ${pendingNpos.length} ${escapeHtml(pendingNpos.length===1?opponentSingularLabel():opponentPluralLabel())}</h3><ul class="reinforcement-list">${pendingNpos.map(npo=>`<li>${escapeHtml(npoName(npo))}</li>`).join('')}</ul><p>Deploy ${pendingNpos.length===1?`this ${escapeHtml(opponentSingularLabel())}`:`these ${escapeHtml(opponentPluralLabel())}`} onto the battlefield using the Tomb World reinforcement rules.</p></div>`:'';
    const reinforcementCard=deployingNpos.length||blockedCount
      ? `<section class="card reinforcement-card" aria-live="polite"><p class="eyebrow">REINFORCEMENTS</p>${deployedSection}${pendingSection}${blockedCount?`<div class="reinforcement-blocked" role="status"><h3>${deployingNpos.length?`${blockedCount} additional reinforcement${blockedCount===1?'':'s'} could not be deployed`:'No reinforcements could be deployed'}</h3><p>${blockedReason}</p></div>`:''}</section>`
      : '<div class="summary-box strategy-empty-message">No reinforcements were generated this Turning Point.</div>';
    const placements=deployingNpos.map(npo=>`<label class="check-row"><input type="checkbox" data-reinforcement-placement="${escapeHtml(npo.id)}" aria-label="Confirm placement for ${escapeHtml(npoName(npo))}" ${npo.reinforcement?.placementConfirmed?'checked':''}><span><strong>${escapeHtml(npoName(npo))} · ${escapeHtml(npoWeapon(npoDefinition(npo.type),npo.weaponId)?.name||npo.weaponId)}</strong>${npo.replacementOptions?.length?`<span class="field"><span>Choose NPO</span><select aria-label="Choose replacement for ${escapeHtml(npoName(npo))}" data-reinforcement-replacement="${escapeHtml(npo.id)}">${npo.replacementOptions.map(type=>`<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join('')}</select></span>`:''}<small>Randomly determine an open hatchway, set up this operative with a Conceal order following the Tomb World reinforcement placement restrictions, then confirm.</small></span></label>`).join('');
    const showStatTooltips=!window.matchMedia('(max-width:600px)').matches;
    const tooltipAttrs=text=>showStatTooltips?` tabindex="0" data-tooltip="${text}"`:'';
    const infoDot=showStatTooltips?'<span class="info-dot">i</span>':'';
    const battlefield=`<section class="battlefield-state-section" aria-labelledby="battlefield-state-heading"><h3 id="battlefield-state-heading" class="strategy-section-heading">Current Battlefield State</h3><div class="stat-grid strategy-stat-grid"><div class="stat tooltip-stat"${tooltipAttrs('Threat rises from loud or aggressive actions. Higher Threat can increase the Grade, reinforcements, and Tomb World events.')}><small>THREAT LEVEL ${infoDot}</small><strong>${state.threat}</strong></div><div class="stat tooltip-stat"${tooltipAttrs('Grade 0–3 is derived from Threat and determines reinforcement pressure and some events.')}><small>GRADE LEVEL ${infoDot}</small><strong>${threatGrade()}</strong></div><div class="stat tooltip-stat"${tooltipAttrs(`The number of living ${opponentPluralLabel()} that are Ready and may still activate during this Turning Point.`)}><small>${escapeHtml(opponentPluralLabel())} Ready ${infoDot}</small><strong>${readyNpos().length}</strong></div></div></section>`;
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
    if(['initiative','event'].includes(state.strategyStage))return `<section class="next-card"><span class="phase">STRATEGY PHASE</span><h2>Dice resolution interrupted</h2><p>Continue from the last fully committed result. No committed dice will be rerolled.</p><button class="btn primary big-action" id="retryStrategyDice">Continue Strategy Phase</button></section>`;
    if(state.strategyStage!=='summary')return '';
    const step=strategyViewStep(d);
    return `<section class="next-card strategy-step">${step==='actions'?strategyActionsStepHtml(d):step==='events'?strategyEventsStepHtml(d):strategyReviewStepHtml(d)}</section>`;
  }

  function strategyEventHtml(event,activeEffects=state.eventState.active||[]){
    const title=event.title||event[0],description=event.text||event.description||event[1];
    if(event.type!=='tomb-world-event')return `<div class="summary-box"><strong>${escapeHtml(title)}</strong><br>${escapeHtml(description)}</div>`;
    const isRelocation=event.definitionId==='transdimensional-relocation';
    if(isRelocation&&event.status==='drawn')prepareTransdimensionalRelocation(event);
    const displayDescription=isRelocation&&['drawn','resolved'].includes(event.status)&&event.resolution?.playerOperativeIds?.length===2
      ? transdimensionalRelocationSelectionSummary()
      : description;
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
    const eventDetails=`${eventHeader}<div class="tomb-world-event-heading"><h3 class="tomb-world-event-title"${resolvedHeadingId}>${escapeHtml(presentSideTerminology(title))}</h3><span class="strategy-event-status" data-event-status="${escapeHtml(event.status)}"${activeEffect?` data-event-active="true" aria-label="${activeLabel}"`:''}>${statusLabel}</span></div><div class="tomb-world-event-effect"><div class="tomb-world-event-effect-label">Effect</div><p class="tomb-world-event-description">${escapeHtml(presentSideTerminology(displayDescription))}</p></div>`;
    if(event.status!=='drawn'){
      const cardStatusClass=event.status==='redrawn'?' tomb-world-event-card--redrawn':'';
      return `<div class="summary-box strategy-event tomb-world-event-card${cardStatusClass}" aria-live="polite">${eventDetails}<div class="event-resolution">${escapeHtml(presentSideTerminology(event.result||'Complete'))}</div></div>`;
    }
    if(isRelocation){
      const selected=event.resolution?.playerOperativeIds||[];
      if(selected.length!==2)return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite">${eventDetails}<div class="event-resolution">Another event card is being drawn because fewer than two ${escapeHtml(playerSideLabel())} operatives are on the battlefield.</div></div>`;
      const names=selected.map(playerName);
      const accessibleNames=names.join(' and ');
      return `<div class="summary-box strategy-event tomb-world-event-card" aria-live="polite" aria-label="Transdimensional Relocation. Operatives to swap: ${escapeHtml(accessibleNames)}.">${eventDetails}<div class="event-resolution"><h4 id="transdimensional-relocation-selection-heading">OPERATIVES TO SWAP</h4><ol>${names.map(name=>`<li>${escapeHtml(name)}</li>`).join('')}</ol><p>Remove both operatives from the killzone. Set each operative up in the other operative’s previous position.</p><p>Keep their wounds, order, Ready or Expended state, and all other statuses unchanged.</p></div><div class="event-controls"><button type="button" class="btn primary" id="resolveStrategyEvent" aria-label="Confirm positions swapped for ${escapeHtml(accessibleNames)}">Confirm Positions Swapped</button></div></div>`;
    }
    const labels={
      'awakened-warrior':'Confirm Necron Warrior Placement',
      'chittering-drone':'Confirm Scarab Placement',
      'flesh-hunger':'Confirm Flesh Hunger',
      'maze-reforms':'Confirm Terrain Changes'
    };
    const hasScarabChoices=event.execution.type==='chittering-drone'&&Array.isArray(event.eligibleNpoIds)&&event.eligibleNpoIds.length>1;
    const scarabGuide=event.execution.type==='chittering-drone'
      ? `<div class="event-resolution event-guide-action"><h4>GUIDE ACTION</h4><p>${hasScarabChoices?'Multiple wounded Canoptek Scarab Swarms are eligible. Choose one below. The Guide will automatically restore the selected swarm to full wounds.':`No wounded Canoptek Scarab Swarms are currently on the battlefield. Set up one Ready Canoptek Scarab Swarm with a Conceal order using the event card's placement instructions, then confirm below.`}</p></div>`:'';
    const scarabChoices=hasScarabChoices
      ? `<div class="field"><label for="eventNpoSelect">Wounded Scarab Swarm</label><select id="eventNpoSelect"><option value="">Select a Scarab Swarm...</option>${sortedNposForDisplay(event.eligibleNpoIds.map(id=>activeNpos().find(item=>item.id===id)).filter(Boolean)).map(n=>`<option value="${escapeHtml(n.id)}">${escapeHtml(npoName(n))} — ${n.wounds} of ${n.maxWounds} wounds</option>`).join('')}</select></div>`:'';
    const fleshChoices=event.execution.type==='flesh-hunger'&&event.eligibleNpoIds?.length&&isPvpMode()
      ? `<div class="field"><label for="eventNpoSelect">Flayed One</label><select id="eventNpoSelect">${event.eligibleNpoIds.map(id=>`<option value="${escapeHtml(id)}">${escapeHtml(npoName(activeNpos().find(npo=>npo.id===id)))}</option>`).join('')}</select></div><div class="field"><label for="eventFreeMovement">Free movement</label><select id="eventFreeMovement"><option>Charge</option><option>Reposition</option></select></div>`:'';
    const fleshGuide=event.execution.type==='flesh-hunger'?`<div class="event-resolution event-guide-action"><h4>GUIDE ACTION</h4><p>${event.eligibleNpoIds?.length?'Perform the selected free Charge or Reposition towards the closest Player operative. This costs 0 AP, starts no activation, and grants no attack.':`Random hatchway: ${escapeHtml(event.placementHatchway||'pending')}. Set up the Flayed One Ready with a Conceal order, wholly within NPO territory. Put the hatchway access point within its Control Range; if impossible, place it as close as possible and within Control Range of a Player operative if possible.`}</p></div>`:'';
    const awakenedOptions=event.execution.type==='awakened-warrior'&&isPvpMode()
      ? replaceEventGeneratedNpo({type:'Necron Warrior',source:'event'}).replacementOptions|| (isCrownworldTomb()?['Necron Warrior','Lychguard']:[])
      : [];
    const awakenedChoices=awakenedOptions.length
      ? `<div class="field"><label for="eventReplacementChoice">Choose NPO</label><select id="eventReplacementChoice">${awakenedOptions.map(type=>`<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join('')}</select></div>${isCrownworldTomb()?'<div class="field" id="eventLychguardLoadoutField" hidden><label for="eventLychguardLoadout">Lychguard weapon</label><select id="eventLychguardLoadout"><option value="hyperphase-sword">Hyperphase sword</option><option value="warscythe">Warscythe</option></select></div>':''}`:'';
    if(hasScarabChoices)labels['chittering-drone']='Restore Selected Scarab Swarm';
    const impossibleControl=event.execution.type==='maze-reforms'?'<button type="button" class="btn secondary" id="redrawStrategyEvent" aria-label="No valid terrain changes are possible; draw another Tomb World event card">No Valid Changes · Draw Again</button>':'';
    return `<div class="summary-box strategy-event tomb-world-event-card">${eventDetails}${scarabGuide}<div class="event-controls">${scarabChoices}${fleshGuide}${fleshChoices}${awakenedChoices}<button type="button" class="btn primary" id="resolveStrategyEvent" ${scarabChoices?'disabled':''}>${labels[event.definitionId]||labels[event.execution.type]||'Resolve Event'}</button>${impossibleControl}</div></div>`;
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
        <span>${escapeHtml(playerName(operativeId))}</span><span class="tracker-operative-status"><strong>${status}</strong></span>
      </button>`;
    }).join('');
    const npoRows=sortedNposForDisplay(trackerNpos()).map(n=>{
      const trackerStatus=npoTrackerStatus(n);
      return `<div class="tracker-operative npo ${trackerStatus.className}"><span>${escapeHtml(npoName(n))}</span><span class="tracker-operative-status"><strong>${trackerStatus.status}</strong></span></div>`;
    }).join('');
    return `<section class="card activation-tracker"><details class="activation-details">
      <summary><div><p class="eyebrow">ACTIVATION TRACKER</p><h3>${state.activationNumber} activations completed</h3></div></summary>
      <div class="activation-details-content">
      <div class="tracker-section">
        <small>${escapeHtml(selectedPlayerTeamName('Player'))} operatives</small>
        <p class="muted compact-copy">All selected operatives are listed, including eliminated operatives. Select a ${escapeHtml(playerSideLabel())} operative to mark it eliminated or restore it.</p>
        <div class="tracker-operative-grid">${playerRows||'<span class="muted">No player operatives selected</span>'}</div>
      </div>
      <div class="tracker-section">
        <small>${escapeHtml(opponentPluralLabel())}</small>
        <div class="tracker-operative-grid">${npoRows||`<span class="muted">No ${escapeHtml(opponentSingularLabel())} operatives generated</span>`}</div>
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
      <p>This status carries across Turning Points and is reflected in the activation tracker and ${escapeHtml(playerSideLabel())} Ready count.</p>
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
    $('#eventReplacementChoice')?.addEventListener('change',e=>{$('#eventLychguardLoadoutField')?.toggleAttribute('hidden',e.target.value!=='Lychguard');});
    $('#resolveStrategyEvent')?.addEventListener('click',event=>{
      const button=event.currentTarget;
      if(button.disabled)return;
      button.disabled=true;
      void resolveStrategyEvent(button).catch(error=>{console.error('[Strategy Event]',error);state.strategyStage='event';save();render();}).finally(()=>{if(button.isConnected&&state.strategyData?.eventPending)button.disabled=false;});
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
      else setTimeout(()=>{void redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.').catch(error=>{console.error('[Strategy Event Redraw]',error);state.strategyStage='event';save();render();});},0);
    }else focusedRelocationInstanceId=null;
    $('#redrawStrategyEvent')?.addEventListener('click',async event=>{
      const button=event.currentTarget;
      if(button.disabled)return;
      button.disabled=true;
      try{if(!await redrawCurrentEvent('No breach or open hatchway could be changed.'))button.disabled=false;}
      catch(error){console.error('[Strategy Event Redraw]',error);state.strategyStage='event';save();render();}
    });
    $('#continueStrategyEvents')?.addEventListener('click',()=>showStrategyViewStep('events','actions'));
    $('#completeStrategyFromActions')?.addEventListener('click',()=>{if(!strategyHasNoDownstreamWork()||!canCompleteStrategyPhase())return;beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player');});
    $('#backStrategyActions')?.addEventListener('click',()=>showStrategyViewStep('actions','events'));
    $('#continueStrategyReview')?.addEventListener('click',()=>showStrategyViewStep('review','events'));
    $('#backStrategyEvents')?.addEventListener('click',()=>showStrategyViewStep('events','review'));
    $('#continueStrategy')?.addEventListener('click',()=>{if(!canCompleteStrategyPhase())return;beginFirefight(state.strategyData?.suggestedInitiative==='npo'?'npo':'player');});
    $('#ceaselessScuttling')?.addEventListener('click',showCeaselessScuttling);
    $('#retryMissionReady')?.addEventListener('click',continueTurningPointStart);
    $('#retryStrategyDice')?.addEventListener('click',finishTurningPointStart);
    $('#playerActivation')?.addEventListener('click',()=>showPlayerActivation());
    $('#npoActivation')?.addEventListener('click',showNpoSelection);
    $('#missionHud')?.addEventListener('click',showMissionDetails);
    bindMissionProgressControls();
    $('#resolveAuspexCalibration')?.addEventListener('click',performAuspexCalibration);
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
    const definition=npoDefinition('Canoptek Macrocyte Warrior');
    const soloWeaponId=isPvpMode()?null:ceaselessScuttlingSoloWeaponId();
    const loadoutHtml=isPvpMode()
      ? `<div class="field"><label for="scuttlingLoadout">Loadout</label><select id="scuttlingLoadout">${definition.loadoutOptions.map(option=>`<option value="${escapeHtml(option.id)}">${escapeHtml(option.name)}</option>`).join('')}</select></div>`
      : `<div class="summary-box"><strong>New Canoptek Macrocyte Warrior</strong><br>${escapeHtml(definition.loadoutOptions.find(option=>option.id===soloWeaponId).name)}</div>`;
    const noLegalSetupAction=isPvpMode()?'':'<button class="btn secondary big-action" id="scuttlingNoLegalSetup">No Legal Setup Location</button>';
    showModal('A Ceaseless Scuttling',`<p>${isPvpMode()?'Select a supported loadout for the new operative instance, then ':''}Confirm a valid setup wholly within the NPO drop zone.</p>${loadoutHtml}<label class="check-row"><input id="scuttlingPlacement" type="checkbox"><span>Valid NPO drop-zone setup location confirmed</span></label>${noLegalSetupAction}<div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmScuttling" disabled>Confirm Setup</button></div>`);
    $('#scuttlingPlacement').onchange=()=>{$('#confirmScuttling').disabled=!$('#scuttlingPlacement').checked;};
    $('#scuttlingNoLegalSetup')?.addEventListener('click',()=>{
      state.strategyData.ceaselessScuttlingTurningPoint=state.turningPoint;
      log('A Ceaseless Scuttling could not set up a Macrocyte Warrior because no legal NPO drop-zone location was available.');
      save();closeModal();render();
    });
    $('#confirmScuttling').onclick=()=>{
      const warrior=createCeaselessScuttlingWarrior(isPvpMode()?$('#scuttlingLoadout').value:soloWeaponId);
      if(!warrior)return;
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
    await finishTurningPointStart();
  }

  async function continueTurningPointStart(){
    if(!await applyMissionReadyHooks())return;
    await finishTurningPointStart();
  }

  async function finishTurningPointStart(){
    try{
      if(state.strategyPipeline.current==='initiative'){
        state.phase='strategy';state.strategyStage='initiative';state.nextSide='player';state.activeNpoId=null;
        state.strategyData.initiativeMode='pending';save();
        await determineInitiative();
      }
      if(state.strategyPipeline.current==='event'){
        state.phase='strategy';state.strategyStage='event';save();
        if(Array.isArray(state.strategyData.events))await beginCurrentEvent();
        else await processEventStage();
      }
    }catch(error){
      console.error('[Strategy Dice]',error);
      save();render();
      return false;
    }
    if(!state.strategyData.eventPending)processReinforcementStage();
    const {grade,reinforcements}=state.strategyData;
    state.phase='strategy';state.strategyStage='summary';state.nextSide='player';state.activeNpoId=null;
    log(`Turning Point ${state.turningPoint} started. Grade ${grade}; ${state.strategyData.eventPending?'reinforcements await event resolution':`${reinforcements.length} reinforcement(s)`}.`);
    save();render();
    return true;
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
    completeStrategyStage('mission-ready-hooks','initiative');save();acknowledgeCurrentDiceRequest();
    return true;
  }

  async function determineInitiative(){
    await rollInitiative();
    completeStrategyStage('initiative','event');
  }

  async function processEventStage(){
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
    save();
    if(d.event){await beginCurrentEvent();return;}
    completeStrategyStage('event','reinforcement');
  }

  function eventRecord(card){
    const definition=eventDefinitions[card.definitionId];
    return {...card,type:'tomb-world-event',title:definition.title,text:definition.text,execution:{...definition.execution},duration:definition.duration,status:'drawn'};
  }

  function recycleUsedEvents(){
    const legalIds=new Set(eventDeckForVariant().map(card=>card.instanceId));
    state.eventState.available=(state.eventState.available||[]).filter(id=>legalIds.has(id));
    state.eventState.used=(state.eventState.used||[]).filter(id=>legalIds.has(id));
    for(const id of legalIds)if(!state.eventState.available.includes(id)&&!state.eventState.used.includes(id))state.eventState.available.push(id);
    const used=state.eventState.used||[];
    if(!used.length)return;
    state.eventState.available=[...new Set([...(state.eventState.available||[]),...used])];
    state.eventState.used=[];
  }

  function drawEvent(insertAt=null){
    if(!state.eventState.available.length)return null;
    const index=roll(state.eventState.available.length)-1;
    const instanceId=state.eventState.available.splice(index,1)[0];
    const card=eventDeckForVariant().find(candidate=>candidate.instanceId===instanceId);
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
    const variantDeck=eventDeckForVariant();
    const validPool=pool.filter(instanceId=>variantDeck.some(card=>card.instanceId===instanceId));
    if(!validPool.length)return null;
    const instanceId=validPool[roll(validPool.length)-1];
    const card=variantDeck.find(candidate=>candidate.instanceId===instanceId);
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

  function narrateAcceptedEvent(event){
    void TombWorldNarration.playEvent(event.definitionId,event.instanceId);
  }

  function narrateVisibleStrategyEvents(){
    const d=state.strategyData;
    if(state.phase!=='strategy'||state.strategyStage!=='summary'||strategyViewStep(d)!=='events'||!$('.strategy-event'))return;
    const events=Array.isArray(d?.events)?d.events:[];
    const acceptedCount=Math.min(events.length,(d.eventIndex||0)+(d.eventPending?1:0));
    events.slice(0,acceptedCount).filter(event=>event.status!=='redrawn').forEach(narrateAcceptedEvent);
  }

  async function beginCurrentEvent(){
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
        await redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.');
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
        const remaining=eligible.filter(id=>!transaction.selections.includes(id));
        while(remaining.length||transaction.pendingOperativeId){
          let operativeId=transaction.pendingOperativeId;
          if(!operativeId){const selectedIndex=roll(remaining.length)-1;operativeId=remaining.splice(selectedIndex,1)[0];}
          transaction.pendingOperativeId=operativeId;save();
          const requestKey=diceRequestKey('event',event.instanceId,'subjugation-glyphs',operativeId);
          if(state.pendingDice?.status==='committed'&&state.pendingDice.requestKey!==requestKey)acknowledgeCurrentDiceRequest();
          const [die]=await requestDiceResults({count:1,sides:6,title:'SUBJUGATION GLYPHS',instruction:'Roll 1D6 on the tabletop and enter the result.',rollerLabel:playerName(operativeId),requestKey,resumeKind:'event',resumeData:{eventInstanceId:event.instanceId,operativeId}});
          const baseApl=Number(playerDefinition(operativeId)?.apl||3),apl=effectivePlayerApl(operativeId,baseApl);
          transaction.selections.push(operativeId);transaction.rolls.push(die);delete transaction.pendingOperativeId;
          save();
          if(die>apl){
            const modifierId=`subjugation-glyphs:${event.instanceId}:${operativeId}`;
            if(!state.eventState.playerAplModifiers.some(item=>item.id===modifierId))state.eventState.playerAplModifiers.push({id:modifierId,sourceId:event.instanceId,targetId:operativeId,ruleId:'subjugation-glyphs',amount:-1,expires:null});
            transaction.affectedOperativeId=operativeId;
            break;
          }
        }
        transaction.committed=true;save();acknowledgeCurrentDiceRequest();
      }
      const tested=transaction.selections.map((id,index)=>`${playerName(id)} rolled ${transaction.rolls[index]}`).join('; ');
      await completeCurrentEvent(`${tested||'No eligible operatives.'}${transaction.affectedOperativeId?`; ${playerName(transaction.affectedOperativeId)} suffers -1 APL.`:'; no operative was affected.'}`);
      return;
    }
    if(type==='living-metal-flux'){
      const restored=[],wounded=sortedNposForDisplay(activeNpos().filter(npo=>npo.wounds<npo.maxWounds));
      const transaction=eventTransaction(`event:${event.instanceId}:${state.turningPoint}`,{definitionId:event.definitionId,selections:[],rolls:[]});
      const committed=[];
      for(const npo of wounded){
        const committedIndex=transaction.selections.indexOf(npo.id);
        let die=transaction.rolls[committedIndex];
        if(!Number.isInteger(die)){
          const requestKey=diceRequestKey('event',event.instanceId,'living-metal-flux',npo.id);
          if(state.pendingDice?.status==='committed'&&state.pendingDice.requestKey!==requestKey)acknowledgeCurrentDiceRequest();
          [die]=await requestDiceResults({count:1,sides:3,title:'LIVING METAL FLUX',instruction:'Roll 1D3. This model regains D3 + 2 wounds.',rollerLabel:npoName(npo),requestKey,resumeKind:'event',resumeData:{eventInstanceId:event.instanceId,npoId:npo.id}});
          transaction.selections.push(npo.id);transaction.rolls.push(die);
          save();
        }
        committed.push({npo,die});
      }
      committed.forEach(({npo,die})=>{
        const amount=die+2,before=npo.wounds;
        npo.wounds=Math.min(npo.maxWounds,npo.wounds+amount);
        restored.push({npo,die,result:`${npoName(npo)} rolled ${die}: ${before}→${npo.wounds}`});
      });
      const summary=sortedNposForDisplay(restored.map(entry=>entry.npo))
        .map(npo=>restored.find(entry=>entry.npo===npo).result)
        .join('; ');
      transaction.committed=true;save();acknowledgeCurrentDiceRequest();
      await completeCurrentEvent(summary||'No wounded NPOs.');
      return;
    }
    if(type==='stirrings'){
      if(state.threat===15){await redrawCurrentEvent('Threat was already 15.');return;}
      setThreat(1,event.title);
      await completeCurrentEvent(`Threat increased to ${state.threat}.`);
      return;
    }
    if(type==='activate'){
      if(event.definitionId==='enforcer-of-the-phaerons'&&!activeNpos().some(npo=>npo.type==='Royal Warden')){
        await redrawCurrentEvent('No living, deployed Royal Warden was in the killzone.');return;
      }
      if(!state.eventState.active.some(active=>active.instanceId===event.instanceId&&active.startedTurningPoint===state.turningPoint)){
        const definition=eventDefinitions[event.definitionId];
        state.eventState.active.push({...event,lifecycle:definition.lifecycle,handlerId:definition.handlerId,gameplayHooks:[...definition.gameplayHooks],automationType:definition.automationType,priority:definition.priority,startedTurningPoint:state.turningPoint,expiresAfterTurningPoint:state.turningPoint,status:'active'});
      }
      await completeCurrentEvent(eventDefinitions[event.definitionId]?.resultText||'Effect active until the end of this Turning Point.');
      return;
    }
    if(type==='chittering-drone'){
      const wounded=activeNpos().filter(npo=>npo.type==='Canoptek Scarab Swarm'&&npo.wounds<npo.maxWounds);
      if(wounded.length===1){const before=wounded[0].wounds;wounded[0].wounds=wounded[0].maxWounds;await completeCurrentEvent(`The Guide automatically restored ${npoName(wounded[0])} to full wounds (${before} → ${wounded[0].maxWounds}).`);return;}
      if(wounded.length>1){event.eligibleNpoIds=wounded.map(npo=>npo.id);d.eventPending=true;return;}
      if(activeNpos().length>=MAX_NPOS||!npoInventory()['Canoptek Scarab Swarm'].remaining){await redrawCurrentEvent('No Scarab Swarm could be set up.');return;}
    }
    if(type==='flesh-hunger'){
      const flayed=activeNpos().filter(npo=>npo.type==='Flayed One');
      if(flayed.length){event.eligibleNpoIds=flayed.map(npo=>npo.id);d.eventPending=true;return;}
      if(activeNpos().length>=MAX_NPOS){await redrawCurrentEvent('No Flayed One could be set up and none was available to move.');return;}
      event.placementHatchway=`Hatchway ${roll(6)}`;d.eventPending=true;return;
    }
    if(type==='maze-reforms'){
      const transaction=eventTransaction(`event:${event.instanceId}:${state.turningPoint}`,{definitionId:event.definitionId,rolls:[]});
      if(!Number.isInteger(transaction.rolls[0])){
        const requestKey=diceRequestKey('event',event.instanceId,'maze-reforms');
        const [die]=await requestDiceResults({count:1,sides:3,title:'THE MAZE REFORMS',instruction:'Roll 1D3 on the tabletop and enter the result.',requestKey,resumeKind:'event',resumeData:{eventInstanceId:event.instanceId}});
        transaction.rolls=[die];
        transaction.committed=true;save();acknowledgeDiceRequest(requestKey);
      }
      event.openHatchwayLimit=transaction.rolls[0];
      event.text=`Close one breach and up to ${event.openHatchwayLimit} open hatchway${event.openHatchwayLimit===1?'':'s'}. If this cannot be resolved, draw another event card.`;
    }
    if(type==='awakened-warrior'&&currentTombWorldVariant().id==='standard'&&(activeNpos().length>=MAX_NPOS||!npoInventory()['Necron Warrior'].remaining)){await redrawCurrentEvent('No Necron Warrior could be set up.');return;}
    if(type==='awakened-warrior'&&currentTombWorldVariant().id!=='standard'&&activeNpos().length>=MAX_NPOS){await redrawCurrentEvent('No eligible operative could be set up.');return;}
    d.eventPending=true;
  }

  async function completeCurrentEvent(result){
    const d=state.strategyData,event=currentEvent();
    if(!event)return;
    event.status='resolved';event.result=result;
    d.eventAction={eventId:event.instanceId,result};
    d.eventIndex=(d.eventIndex||0)+1;
    d.eventPending=false;
    const source=event.requiredBy==='restless-tomb'?'Restless Tomb minimum':'standard rules';
    log(`Turning Point ${state.turningPoint} · ${event.title} (${source}): ${result}`);
    save();
    await beginCurrentEvent();
  }

  async function redrawCurrentEvent(reason){
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
    save();
    await beginCurrentEvent();
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
        const request=tombWorldVariantHook('reinforcementGeneration',randomReinforcement());
        const rr=resolveVariantNpoRequest(request,{transactionId:`reinforcement:${state.turningPoint}:${i}:${request?.type||'none'}`});
        if(!rr){blocked++;state.reinforcementState.blockedByInventory++;continue;}
        const type=rr.type;
        let n=reserveNpos().find(candidate=>candidate.type===type&&!state.reinforcementState.operativeIds.includes(candidate.id)&&!state.reinforcementState.blockedOperativeIds.includes(candidate.id));
        if(n){
          n.reinforcement={turningPoint:state.turningPoint,placementConfirmed:false};
          n.battlefieldState='reserve';n.deployed=false;n.dormant=false;n.ready=false;
          n.replacementOptions=rr.replacementOptions||null;n.replacementTransactionId=rr.replacementTransactionId||null;
        }else{
          n=createNpo(type,`${type} R${state.turningPoint}-${i+1}`,{weaponId:rr.weaponId,deployed:false,reinforcement:{turningPoint:state.turningPoint,placementConfirmed:false},replacementOptions:rr.replacementOptions,replacementTransactionId:rr.replacementTransactionId});
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
    let npo=state.roster.find(item=>item.id===id&&state.reinforcementState.operativeIds.includes(item.id));
    if(!npo?.reinforcement)return;
    if(confirmed&&npo.replacementOptions?.length){
      const selected=$$('[data-reinforcement-replacement]').find(select=>select.dataset.reinforcementReplacement===npo.id)?.value;
      npo=commitPvpNpoReplacement(npo,selected);
      if(!npo){showToast('That replacement could not be added.');save();render();return;}
      id=npo.id;
    }
    if(confirmed&&npo.type===TOMB_CRAWLER_TYPE&&!state.variantState.crownworldFirstCrawlerConsumed){
      const pair=setupCrownworldCrawlerPair(npo,`crownworld:reinforcement:${state.turningPoint}:${npo.id}`);
      if(pair.blocked){state.reinforcementState.blocked++;state.reinforcementState.blockedByCapacity++;showToast('The Royal Warden and Lychguard pair could not be set up within the 10-NPO limit.');save();render();return;}
      if(pair.replaced){
        pair.npos.forEach(created=>{created.reinforcement={turningPoint:state.turningPoint,placementConfirmed:true};});
        state.reinforcementState.operativeIds=state.reinforcementState.operativeIds.flatMap(operativeId=>operativeId===id?pair.npos.map(created=>created.id):[operativeId]);
        const complete=state.reinforcementState.operativeIds.every(operativeId=>state.roster.find(item=>item.id===operativeId)?.reinforcement?.placementConfirmed);
        state.reinforcementState.status=complete?'complete':'placement';
        save();render();return;
      }
    }
    npo.reinforcement.placementConfirmed=Boolean(confirmed);
    npo.deployed=npo.reinforcement.placementConfirmed;
    npo.battlefieldState=npo.deployed?'deployed':'reserve';
    npo.dormant=npo.deployed&&state.threat===0;
    npo.ready=npo.deployed&&!npo.dormant;
    const complete=state.reinforcementState.operativeIds.every(operativeId=>state.roster.find(item=>item.id===operativeId)?.reinforcement?.placementConfirmed);
    state.reinforcementState.status=complete?'complete':'placement';
    save();render();
  }

  async function rollInitiative(){
    if(!state.strategyData)state.strategyData={};
    if(state.turningPoint===1||state.threat===0){
      state.strategyData.playerRoll=null;
      state.strategyData.npoRoll=null;
      state.strategyData.suggestedInitiative='player';
      state.strategyData.initiativeMode='automatic';
      state.strategyData.initiativeReason=state.turningPoint===1?'Turning Point 1':'Threat was 0 when initiative was determined';
      return;
    }
    const playerLabel=selectedPlayerTeamName();
    let p=state.strategyData.playerRoll,n=state.strategyData.npoRoll;
    if(!Number.isInteger(p)){
      const requestKey=`initiative:tp${state.turningPoint}:player`;
      [p]=await requestDiceResults({count:1,sides:6,title:'INITIATIVE',instruction:'Roll 1D6 and enter the result.',rollerLabel:playerLabel,requestKey,resumeKind:'strategy',resumeData:{turningPoint:state.turningPoint,side:'player'}});
      state.strategyData.playerRoll=p;save();
      acknowledgeDiceRequest(requestKey);
    }
    if(!Number.isInteger(n)){
      const requestKey=`initiative:tp${state.turningPoint}:necrons`;
      [n]=await requestDiceResults({count:1,sides:6,title:'INITIATIVE',instruction:'Roll 1D6 and enter the result.',rollerLabel:'Necrons',requestKey,resumeKind:'strategy',resumeData:{turningPoint:state.turningPoint,side:'necrons'}});
      state.strategyData.npoRoll=n;save();
      acknowledgeDiceRequest(requestKey);
    }
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

  async function resolveStrategyEvent(button=null){
    const event=currentEvent();
    if(state.phase!=='strategy'||state.strategyStage!=='summary'||!event||!state.strategyData.eventPending)return;
    let result='Tabletop effect confirmed.';
    if(event.execution.type==='transdimensional-relocation'){
      if(event.status!=='drawn'||event.resolution?.confirmed){if(button)button.disabled=false;return;}
      if(!validTransdimensionalRelocationSelection(event)){
        if(!prepareTransdimensionalRelocation(event))await redrawCurrentEvent('Transdimensional Relocation could not be resolved because fewer than two Player operatives were on the battlefield.');
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
      const before=n.wounds;
      n.wounds=n.maxWounds;
      result=`The Guide automatically restored ${npoName(n)} to full wounds (${before} → ${n.maxWounds}).`;
    }else if(event.execution.type==='flesh-hunger'&&event.eligibleNpoIds?.length){
      const operativeId=isPvpMode()?($('#eventNpoSelect')?.value||event.eligibleNpoIds[0]):event.eligibleNpoIds[0];
      const n=activeNpos().find(item=>item.id===operativeId&&event.eligibleNpoIds.includes(item.id));if(!n)return;
      const action=isPvpMode()?($('#eventFreeMovement')?.value||'Reposition'):'Charge';
      const transaction=eventTransaction(`event:${event.instanceId}:${state.turningPoint}:movement`,{npoId:n.id,action});
      if(!transaction.committed){transaction.committed=true;log(`Flesh Hunger: ${npoName(n)} performed a free ${action} towards the closest Player operative (0 AP; no activation or attack).`);}
      result=`${npoName(n)} performed a free ${action} towards the closest Player operative. No Fight or Shoot was granted.`;
    }else if(event.execution.type==='chittering-drone'||event.execution.type==='awakened-warrior'||event.execution.type==='flesh-hunger'){
      let request={type:event.execution.type==='chittering-drone'?'Canoptek Scarab Swarm':event.execution.type==='flesh-hunger'?'Flayed One':'Necron Warrior',source:'event'};
      if(event.execution.type==='awakened-warrior'){
        request=replaceEventGeneratedNpo(request);
        if(isCrownworldTomb())request={...request,replacementOptions:['Necron Warrior','Lychguard']};
        request=resolveVariantNpoRequest(request,{choice:$('#eventReplacementChoice')?.value||null,transactionId:`event:${event.instanceId}:${state.turningPoint}:replacement`});
      }
      const type=request.type;
      if(activeNpos().length>=MAX_NPOS){await redrawCurrentEvent(`${type} could not be set up.`);return;}
      const weaponId=type==='Lychguard'?(isPvpMode()?($('#eventLychguardLoadout')?.value||'hyperphase-sword'):(Math.random()<0.5?'hyperphase-sword':'warscythe')):undefined;
      const n=weaponId?createNpo(type,`${type} E${state.turningPoint}`,{order:'Conceal',weaponId}):createNpo(type,`${type} E${state.turningPoint}`,{order:'Conceal'});
      n.ready=true;n.dormant=false;
      if(!commitNpoRoster([...state.roster,n],'resolve that event')){await redrawCurrentEvent(`${type} could not be set up.`);return;}
      state.newIds.push(n.id);
      result=event.execution.type==='flesh-hunger'
        ? `${npoName(n)} was set up Ready with a Conceal order at ${event.placementHatchway}; place its access point within Control Range, wholly within NPO territory, as close as possible and within Control Range of a Player operative if possible.`
        : `${npoName(n)} was set up Ready with a Conceal order using the event card’s placement instructions.`;
    }
    if(event.execution.type==='maze-reforms')result='Breach and hatchway changes completed on the tabletop.';
    await completeCurrentEvent(result);
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
      activationId:missionActivationId('npo',n.id),side:'npo',operativeId:n.id,npoId:n.id,name:npoName(n),baseApl:definition.apl,effectiveApl:apl,
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
    if(isPvpMode()){
      showModal('Necron Activation',`<p>Choose a Ready Necron to activate.</p><div class="field"><label for="officialNpoSelection">Ready Necron</label><select id="officialNpoSelection" data-dialog-focus><option value="">Select a Ready Necron</option>${options}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmNpoSelection" disabled>Continue</button></div>`);
      $('#officialNpoSelection').onchange=()=>{$('#confirmNpoSelection').disabled=!$('#officialNpoSelection').value;};
      $('#confirmNpoSelection').onclick=()=>{
        const n=readyNpos().find(item=>item.id===$('#officialNpoSelection').value);
        if(n)beginNpoActivation(n);
        else{closeModal();render();showToast('That Necron is no longer Ready. Choose another Ready Necron.');}
      };
      return;
    }
    showModal(`Select ${opponentSingularLabel()} to Activate`,`<p>Use the Threat Principle in order. Select a ${escapeHtml(opponentSingularLabel())} that:</p><ol><li>has an ability, or is a threat, to Shoot or Fight a ${escapeHtml(playerSideLabel())} operative;</li><li>is not in cover;</li><li>is closest to a ${escapeHtml(playerSideLabel())} operative.</li></ol><p class="muted">If more than one ${escapeHtml(opponentSingularLabel())} is still tied, determine one at random on the tabletop.</p><div class="field"><label for="officialNpoSelection">Next ready ${escapeHtml(opponentSingularLabel())}</label><select id="officialNpoSelection" data-dialog-focus><option value="">Select matching ${escapeHtml(opponentSingularLabel())}</option>${options}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmNpoSelection" disabled>Continue</button></div>`);
    $('#officialNpoSelection').onchange=()=>{$('#confirmNpoSelection').disabled=!$('#officialNpoSelection').value;};
    $('#confirmNpoSelection').onclick=()=>{const n=candidates.find(item=>item.id===$('#officialNpoSelection').value);if(n)beginNpoActivation(n);};
  }

  function remainingPlayerOperatives(){
    const used=new Set(state.playerActivatedIds||[]);
    const casualties=new Set(state.playerCasualtyIds||[]);
    return inPlayPlayerOperativeIds().filter(id=>!used.has(id)&&!casualties.has(id));
  }

  const HUMAN_ACTION_GROUPS=[
    {id:'movement',label:'Movement'},
    {id:'combat',label:'Combat'},
    {id:'mission',label:'Mission / Battlefield'},
    {id:'special',label:'Special Actions'}
  ];

  function activePlayerActivation(){
    return state.lastActivation?.side==='player'&&!state.lastActivation.committed?state.lastActivation:null;
  }

  function beginPlayerActivation(operativeId){
    const operative=playerDefinition(operativeId);
    if(!operative||!remainingPlayerOperatives().includes(operativeId))return false;
    const baseApl=Number(operative.apl||3),apl=effectiveApl(operativeId,baseApl);
    state.lastActivation={
      activationId:missionActivationId('player',operativeId),side:'player',operativeId,playerOperativeId:operativeId,
      baseApl,effectiveApl:apl,startingAp:apl,remainingAp:apl,actionSequence:0,
      completedActionIds:[],resolvedActions:[],pendingAction:null,committed:false,completed:false
    };
    notifyMissionActivationStarted('player',operativeId);
    save();renderHumanPlayerActionPicker();
    return true;
  }

  function playerHumanActionCatalog(activation=activePlayerActivation()){
    const operativeId=activation?.operativeId,operative=playerDefinition(operativeId);
    if(!operative)return [];
    const actions=[
      {id:'move',name:'Reposition',group:'movement',cost:1},
      {id:'dash',name:'Dash',group:'movement',cost:1},
      {id:'charge',name:'Charge',group:'movement',cost:1},
      {id:'fallBack',name:'Fall Back',group:'movement',cost:2},
      {id:'shoot',name:'Shoot',group:'combat',cost:1},
      {id:'melee',name:'Fight',group:'combat',cost:1},
      {id:'damage',name:'Other Damage',group:'special',cost:1},
      {id:'hatch',name:'Operate Hatch',group:'mission',cost:1},
      {id:'breach',name:'Breach',group:'mission',cost:1}
    ];
    if(!['destroy-sarcophagus','recover-transponder'].includes(state.missionId))actions.push({id:'objective',name:'Mission Action',group:'mission',cost:1});
    const transponder=state.missionState;
    if(missionEngine()?.type==='transponder'&&!transponder?.transponderFound&&missionEngine().sites.some(site=>!transponder?.sites?.[site.id]||transponder.sites[site.id]==='available')){
      actions.push({id:'pickUpMarker',name:'Pick Up Marker',group:'mission',cost:Number(objectiveDefinition?.actions?.find(item=>item.id==='searchTransponder')?.apCost)||1});
    }
    if(canOfferBreachSarcophagus({missionBreachCommitted:(activation.completedActionIds||[]).includes('breachSarcophagus')},operativeId)){
      actions.push({id:'breachSarcophagus',name:'Breach Sarcophagus',group:'mission',cost:breachSarcophagusApCost(operativeId)});
    }
    return actions;
  }

  function playerHumanActionState(action,activation=activePlayerActivation()){
    const completed=new Set(activation?.completedActionIds||[]),remaining=Number(activation?.remainingAp||0);
    const discountedBreachCompleted=(activation?.resolvedActions||[]).some(record=>record.id==='breachSarcophagus'&&record.apCost===1);
    if(completed.has(action.id))return {status:'Used',disabled:true,reason:'Used'};
    if(action.cost>remaining)return {status:'Insufficient AP',disabled:true,reason:`Needs ${action.cost} AP`};
    if(action.id==='charge'&&['move','dash','fallBack'].some(id=>completed.has(id)))return {status:'Unavailable',disabled:true,reason:'Unavailable after movement'};
    if(['move','dash','fallBack'].includes(action.id)&&completed.has('charge'))return {status:'Unavailable',disabled:true,reason:'Unavailable after Charge'};
    if(action.id==='fallBack'&&completed.has('move'))return {status:'Unavailable',disabled:true,reason:'Unavailable after Reposition'};
    if(action.id==='move'&&completed.has('fallBack'))return {status:'Unavailable',disabled:true,reason:'Unavailable after Fall Back'};
    if(discountedBreachCompleted&&['shoot','charge'].includes(action.id))return {status:'Unavailable',disabled:true,reason:'Unavailable after Breach Sarcophagus'};
    if(action.id==='shoot'&&!playerAttackWeapons(activation.operativeId,'shoot').length)return {status:'Unavailable',disabled:true,reason:'No ranged weapon'};
    if(action.id==='melee'&&!playerAttackWeapons(activation.operativeId,'melee').length)return {status:'Unavailable',disabled:true,reason:'No melee weapon'};
    if(['shoot','melee'].includes(action.id)&&!hasValidPlayerCombatTargets({}))return {status:'Unavailable',disabled:true,reason:'No valid target'};
    if(action.id==='hatch'&&state.missionId==='demolition-protocol'&&!closedMissionFeatures('hatchway').length)return {status:'Unavailable',disabled:true,reason:'No closed hatchway'};
    if(action.id==='breach'&&state.missionId==='demolition-protocol'&&!closedMissionFeatures('breach-point').length)return {status:'Unavailable',disabled:true,reason:'No breach point'};
    if(action.id==='breachSarcophagus'&&action.cost===1&&(completed.has('shoot')||completed.has('charge')))return {status:'Unavailable',disabled:true,reason:'Unavailable after Shoot or Charge'};
    return {status:'Available',disabled:false,reason:'Available'};
  }

  function renderHumanActivationShell({title,name,wounds,maxWounds,baseApl,effectiveAp,remainingAp,startingAp,order,loadout,effects=[],completedActions=[],actions,onAction,onEnd}){
    const groups=HUMAN_ACTION_GROUPS.map(group=>{
      const items=actions.filter(action=>action.group===group.id);
      if(!items.length)return '';
      return `<section class="activation-group human-action-group" aria-labelledby="human-group-${group.id}"><div class="activation-group-title"><div><strong id="human-group-${group.id}">${escapeHtml(group.label.toUpperCase())}</strong></div></div><div class="human-npo-action-list">${items.map(action=>{
        const stateInfo=action.state;
        const status=stateInfo.status||(stateInfo.disabled?'Unavailable':'Available');
        const detail=stateInfo.reason&&stateInfo.reason!==status?`, ${stateInfo.reason}`:'';
        const accessible=`${action.name}, ${action.cost} AP, ${status}${detail}, ${remainingAp} AP remaining`;
        return `<button type="button" class="btn secondary human-npo-action" data-human-action="${escapeHtml(action.id)}" ${stateInfo.disabled?'disabled':''} aria-label="${escapeHtml(accessible)}"${stateInfo.disabled?` aria-disabled="true" aria-description="${escapeHtml(stateInfo.reason)}"`:''}><span><strong>${escapeHtml(action.name)}</strong><small>${action.cost} AP</small></span><small class="human-action-status">${escapeHtml(stateInfo.reason)}</small></button>`;
      }).join('')}</div></section>`;
    }).filter(Boolean).join('');
    const history=completedActions.length?`<section class="summary-box human-completed-actions"><strong>Completed Actions</strong><ul>${completedActions.map(action=>`<li>✓ ${escapeHtml(action.summary||action.name)}</li>`).join('')}</ul></section>`:'';
    showModal(title,`<div class="human-activation-shell"><h2>${escapeHtml(name)}</h2><div class="activation-profile-strip" role="status" aria-label="Activation profile"><span>Wounds: ${wounds}/${maxWounds}</span><span><strong>${remainingAp} / ${startingAp} AP remaining</strong></span>${loadout?`<span>${escapeHtml(loadout)}</span>`:''}${effects.map(effect=>`<span>${escapeHtml(effect)}</span>`).join('')}</div>${history}<div class="activation-groups">${groups}</div><div class="wizard-actions"><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="endHumanActivation">End Activation</button></div></div>`,undefined,'human-activation');
    $$('[data-human-action]',modalBody).forEach(button=>button.onclick=()=>onAction(button.dataset.humanAction));
    $('#endHumanActivation').onclick=onEnd;
  }

  function renderHumanPlayerActionPicker(){
    const activation=activePlayerActivation();
    if(!activation)return showPlayerActivation();
    if(activation.remainingAp<=0){void completeHumanPlayerActivation();return;}
    const operative=playerDefinition(activation.operativeId);
    const effects=[...(state.npoRuleState?.aplModifiers||[]),...(state.eventState?.playerAplModifiers||[])]
      .filter(item=>item.targetId===activation.operativeId)
      .map(item=>`${item.amount>0?'+':''}${item.amount} AP (${titleCaseRuleId(item.ruleId)})`);
    const loadout=(operative.weapons||[]).map(weapon=>weapon.name).filter(Boolean).join(' · ');
    const actions=playerHumanActionCatalog(activation).map(action=>({...action,state:playerHumanActionState(action,activation)}));
    renderHumanActivationShell({
      title:`${selectedPlayerTeamName().toUpperCase()} ACTIVATION`,name:playerName(activation.operativeId),
      wounds:playerCurrentWounds(activation.operativeId),maxWounds:operative.wounds,baseApl:activation.baseApl,
      effectiveAp:activation.effectiveApl,remainingAp:activation.remainingAp,startingAp:activation.startingAp,
      order:state.playerOperativeStates?.[activation.operativeId]?.order||'Tabletop',loadout,effects,
      completedActions:activation.resolvedActions||[],actions,onAction:selectHumanPlayerAction,
      onEnd:confirmEndHumanPlayerActivation
    });
    renderOperativeStatusPanel(activation.operativeId);
  }

  function playerSequentialStage(action){
    const activation=activePlayerActivation();
    return {
      playerOperativeId:activation.operativeId,baseApl:activation.baseApl,apl:activation.effectiveApl,
      sequential:true,humanActionId:action.id,humanActionName:action.name,humanActionCost:action.cost,
      [action.id]:true,...(action.id==='melee'?{melee:true}:{}),threatRolls:{}
    };
  }

  function cancelCurrentHumanPlayerAction(){
    const activation=activePlayerActivation();
    if(!activation)return;
    activation.pendingAction=null;state.combatState=null;state.missionActionContext=null;state.weaponRuleResolution=null;
    save();renderHumanPlayerActionPicker();
  }

  function selectHumanPlayerAction(actionId){
    const activation=activePlayerActivation();
    const action=playerHumanActionCatalog(activation).find(item=>item.id===actionId);
    if(!action||playerHumanActionState(action,activation).disabled)return;
    activation.pendingAction={activationId:activation.activationId,actionId:action.id,actionSequence:activation.actionSequence+1,cost:action.cost};
    const stage=playerSequentialStage(action);
    state.combatState={side:'player',stage};save();
    if(action.id==='shoot'||action.id==='melee'){
      showPendingPlayerAttackWizard(stage,action.id,result=>continuePlayerMultiTargetAttack(stage,action.id,result),cancelCurrentHumanPlayerAction);
      return;
    }
    if(action.id==='hatch'&&state.missionId==='demolition-protocol'){showActivationFeatureTargetSelection(stage,'operate-hatch');return;}
    if(action.id==='breach'&&state.missionId==='demolition-protocol'){showActivationFeatureTargetSelection(stage,'breach');return;}
    if(action.id==='breachSarcophagus'){beginBreachSarcophagus(stage);return;}
    if(action.id==='pickUpMarker'){
      const available=missionEngine().sites.filter(site=>!state.missionState.sites[site.id]||state.missionState.sites[site.id]==='available');
      if(!available.length){
        console.error('[Recover Transponder] Pick Up Marker cannot resolve because no unresolved markers remain. Saved mission state was preserved.');
        cancelCurrentHumanPlayerAction();showToast('Pick Up Marker could not be completed. Mission progress was preserved.');return;
      }
      if(available.length===1){void performLocateItem(available[0].id,activation.operativeId,stage);return;}
      const choices=available.map(site=>`<button type="button" class="btn secondary big-action" data-locate-site="${escapeHtml(site.id)}">${escapeHtml(site.label.toUpperCase())}</button>`).join('');
      showModal('LOCATE ITEM',`<p>Which objective marker is this operative searching?</p><div class="human-npo-action-list">${choices}</div><div class="wizard-actions"><button class="btn ghost" id="cancelLocateItem">Back</button></div>`);
      $('#cancelLocateItem').onclick=cancelCurrentHumanPlayerAction;
      $$('[data-locate-site]',modalBody).forEach(button=>button.onclick=()=>{button.disabled=true;void performLocateItem(button.dataset.locateSite,activation.operativeId,stage);});
      return;
    }
    const descriptions={move:'Confirm that Reposition has been completed on the tabletop.',dash:'Confirm that Dash has been completed on the tabletop.',charge:'Confirm that Charge has been completed on the tabletop.',fallBack:'Confirm that Fall Back has been completed on the tabletop.',damage:'Confirm that the damaging action and its effects are complete.',hatch:'Confirm that Operate Hatch is complete.',breach:'Confirm that Breach is complete.',objective:'Confirm that the mission action resolved successfully.'};
    showModal(action.name,`<p>${escapeHtml(descriptions[action.id]||`Confirm ${action.name} is complete.`)}</p><div class="wizard-actions"><button class="btn ghost" id="cancelHumanPlayerAction">Cancel</button><button class="btn primary" id="commitHumanPlayerAction">${['move','dash','charge','fallBack'].includes(action.id)?'Movement Complete':'Action Complete'}</button></div>`);
    $('#cancelHumanPlayerAction').onclick=cancelCurrentHumanPlayerAction;
    $('#commitHumanPlayerAction').onclick=()=>completePlayerActivation(stage);
  }

  function commitHumanPlayerAction(stage,{deferContinuation=false,deferPersistence=false}={}){
    const activation=activePlayerActivation(),pending=activation?.pendingAction;
    if(!activation||!pending||pending.activationId!==activation.activationId||pending.actionId!==stage.humanActionId)return false;
    if((activation.completedActionIds||[]).includes(pending.actionId))return false;
    const before=activation.remainingAp;
    if(pending.cost>before)return false;
    const attacks=[...pendingAttackResults(stage,'shoot'),...pendingAttackResults(stage,'melee')];
    const primary=attacks[0];
    const summary=primary?primary.attackType==='melee'?`${stage.humanActionName} · ${primary.targetName} · Dealt ${Number(primary.damageDealt??primary.damage??0)} · Suffered ${Number(primary.damageSuffered??0)}`:`${stage.humanActionName} · ${primary.targetName} · ${attacks.reduce((sum,item)=>sum+Number(item.damage||0),0)} damage`:stage.humanActionName;
    activation.remainingAp=before-pending.cost;
    activation.actionSequence=pending.actionSequence;
    activation.completedActionIds=[...(activation.completedActionIds||[]),pending.actionId];
    activation.resolvedActions=[...(activation.resolvedActions||[]),{sequence:pending.actionSequence,id:pending.actionId,name:stage.humanActionName,summary,apCost:pending.cost,apBefore:before,apRemaining:activation.remainingAp,attackSummaries:attacks.map(item=>item.attackType==='melee'?{targetId:item.targetId,targetName:item.targetName,before:item.before,after:item.after,damage:item.damage,attackType:item.attackType,damageDealt:item.attackerDamageDealt,damageSuffered:item.defenderDamageDealt,attackerBefore:item.attackerBefore,attackerAfter:item.attackerAfter,defenderBefore:item.defenderBefore,defenderAfter:item.defenderAfter,attackerIncapacitated:item.attackerIncapacitated,defenderIncapacitated:item.defenderIncapacitated,fightTransactionId:item.fightTransactionId}:{targetId:item.targetId,targetName:item.targetName,before:item.before,after:item.after,damage:item.damage,attackType:item.attackType})}];
    activation.pendingAction=null;state.combatState=null;state.missionActionContext=null;
    log(`${playerName(activation.operativeId)} completed ${summary}. ${activation.remainingAp} AP remaining.`);
    if(!deferPersistence){save();acknowledgeCurrentDiceRequest();}
    if(deferContinuation)return true;
    return continueAfterCommittedHumanAction();
  }

  function continueAfterCommittedHumanAction(){
    const activation=activePlayerActivation();
    if(!activation)return false;
    if(playerCurrentWounds(activation.operativeId)<=0||activation.remainingAp<=0){void completeHumanPlayerActivation();return true;}
    renderHumanPlayerActionPicker();
    return true;
  }

  function buildThreatCheckResult(type,roll,threatBefore,threatAfter){
    const breach=type==='breach';
    return {
      version:1,type,roll,threatBefore,threatAfter,
      baseThreat:breach?1:0,rollThreat:roll>=4?1:0,acknowledged:false,presentationSeen:false
    };
  }

  function renderThreatCheckResult(stage){
    const result=stage.threatCheckResult;
    if(!result||result.acknowledged)return false;
    const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
    const animate=!isPvpMode()&&!result.presentationSeen&&!reducedMotion;
    if(!result.presentationSeen){
      result.presentationSeen=true;
      state.combatState={side:'player',stage:{...stage}};
      save();
    }
    const breach=result.type==='breach';
    const title=breach?'Breach · Threat Check Result':'Operate Hatch · Threat Check Result';
    const outcome=breach
      ?result.rollThreat?'+1 ADDITIONAL THREAT':'NO ADDITIONAL THREAT'
      :result.rollThreat?'+1 THREAT':'NO THREAT INCREASE';
    const change=result.threatBefore===result.threatAfter
      ?`Threat remains ${result.threatAfter}`
      :`Threat: ${result.threatBefore} <span aria-hidden="true">→</span><span class="sr-only"> to </span> ${result.threatAfter}`;
    const maximum=result.threatAfter===15&&result.threatBefore===result.threatAfter&&(result.baseThreat+result.rollThreat)>0
      ?'<p class="threat-check-maximum">Threat is already at maximum.</p>':'';
    const details=`<strong class="threat-check-outcome">${outcome}</strong><dl class="threat-check-breakdown">${breach?`<div><dt>Opening the Breach</dt><dd>+${result.baseThreat}</dd></div>`:''}<div><dt>Threat Check</dt><dd>+${result.rollThreat}</dd></div></dl><p class="threat-check-change">${change}</p>${maximum}`;
    showModal(title,`<section class="threat-check-result" role="status" aria-label="Threat Check result"><div class="threat-check-roll"><small>ROLL</small><div class="dice-row compact ${animate?'animated-roll':'settled'}" id="threatCheckResultDie">${animate?rollingDieHtml():dieHtml({value:result.roll,ariaLabel:`Committed roll: ${result.roll}`})}</div></div><div id="threatCheckResultDetails" ${animate?'hidden':''}>${details}</div><div class="wizard-actions"><button class="btn primary" id="continueThreatCheckResult" data-dialog-focus ${animate?'disabled':''}>Continue</button></div></section>`,undefined,'threat-check-result');
    const button=$('#continueThreatCheckResult');
    if(animate){
      void TombWorldDiceSfx.play();
      setTimeout(()=>{
        if(!button?.isConnected)return;
        const die=$('#threatCheckResultDie');
        die.innerHTML=dieHtml({value:result.roll,ariaLabel:`Committed roll: ${result.roll}`});
        die.classList.replace('animated-roll','settled');
        $('#threatCheckResultDetails').hidden=false;
        button.disabled=false;
        button.focus({preventScroll:true});
      },DICE_ROLL_ANIMATION_MS);
    }
    button.onclick=()=>{
      const button=$('#continueThreatCheckResult');button.disabled=true;
      result.acknowledged=true;
      state.combatState={side:'player',stage:{...stage}};
      save();commitHumanPlayerAction(stage);
    };
    return true;
  }

  function confirmEndHumanPlayerActivation(){
    const activation=activePlayerActivation();if(!activation)return;
    const message=(activation.resolvedActions||[]).length
      ?`${activation.remainingAp} AP remain${activation.remainingAp===1?'s':''}.`
      :'This operative has not performed any actions.';
    showModal('End Activation?',`<p>${escapeHtml(message)}</p><div class="wizard-actions"><button class="btn ghost" id="continueHumanPlayerActivation">Continue Activation</button><button class="btn primary" id="confirmEndHumanPlayerActivation">End Activation</button></div>`);
    $('#continueHumanPlayerActivation').onclick=renderHumanPlayerActionPicker;
    $('#confirmEndHumanPlayerActivation').onclick=()=>completeHumanPlayerActivation();
  }

  async function completeHumanPlayerActivation(){
    const activation=state.lastActivation?.side==='player'?state.lastActivation:null;
    if(!activation)return;
    if(activation.committed){
      if(!activation.completionHookPending)return;
      closeModal();
      await executeMissionLifecycleHook('onPlayerActivationCompleted',{activationId:activation.activationId,operativeId:activation.operativeId});
      activation.completionHookPending=false;save();
      if(!checkGameEnd())render();
      return;
    }
    activation.committed=true;activation.completed=true;
    activation.completionHookPending=true;
    const operativeId=activation.operativeId,activationId=activation.activationId;
    if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
    state.playerReady=playerOperativesRemaining();state.playerActivated=state.playerActivatedIds.length;state.activationNumber++;
    const actions=[...(activation.resolvedActions||[])],summary=actions.map(item=>item.name).join(', ')||'No actions recorded';
    const attackSummaries=actions.flatMap(item=>item.attackSummaries||[]);
    state.activationHistory.unshift({side:'player',label:playerName(operativeId),summary,actions,attackSummary:attackSummaries.at(-1)||null,attackSummaries});
    expireActivationEffects(operativeId);advanceAfterActivation('player');
    log(`${playerName(operativeId)} completed activation: ${summary}.`);
    state.combatState=null;state.missionActionContext=null;save();closeModal();
    await executeMissionLifecycleHook('onPlayerActivationCompleted',{activationId,operativeId});
    activation.completionHookPending=false;save();
    if(!checkGameEnd())render();
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
    objective:1
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

function showPlayerActivation(){
    const active=activePlayerActivation();
    if(active){void resumeCheckpointedGameplayContext();return;}
    const candidates=remainingPlayerOperatives();
    if(!candidates.length){state.playerReady=0;setNextActivation('npo');save();render();return;}
    const options=candidates.map(id=>`<option value="${escapeHtml(id)}">${escapeHtml(playerName(id))}</option>`).join('');
    showModal(`${selectedPlayerTeamName().toUpperCase()} ACTIVATION`,`<p>Choose a Ready operative.</p><div class="field"><label for="humanPlayerSelection">Ready operative</label><select id="humanPlayerSelection" data-dialog-focus><option value="">Select a Ready operative</option>${options}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmHumanPlayerSelection" disabled>Continue</button></div>`);
    $('#humanPlayerSelection').onchange=()=>{$('#confirmHumanPlayerSelection').disabled=!$('#humanPlayerSelection').value;};
    $('#confirmHumanPlayerSelection').onclick=()=>beginPlayerActivation($('#humanPlayerSelection').value);
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
    return {dice:$('#automaticCombat'),results:$('#combatResults'),cancelButton:$(`#${cancelId}`),continueButton:$(`#${continueId}`)};
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
    if(rows.some(({row,dice})=>row?.classList.contains('animated-roll')&&dice.length))void TombWorldDiceSfx.play();
    const timer=setTimeout(()=>{
      rows.forEach(({row,dice})=>{
        if(!row)return;
        if(dice.length)row.innerHTML=dice.map(dieHtml).join('');
        row.classList.replace('animated-roll','settled');
      });
      onSettled();
    },DICE_ROLL_ANIMATION_MS);
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
        ()=>stage.sequential?cancelCurrentHumanPlayerAction():showPlayerActivation(stage)
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
        ()=>stage.sequential?cancelCurrentHumanPlayerAction():showPlayerActivation(stage)
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
    const targetLabel=isHatch?'Hatchway':'Breach point';
    const targetPlaceholder=isHatch?'Select hatchway…':'Select breach point…';
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
      $('#returnFromBreachTarget').onclick=()=>stage.sequential?cancelCurrentHumanPlayerAction():showPlayerActivation(stage);
      return;
    }
    showModal(`Select ${actionLabel} Target`,`<p>Choose the ${isHatch?'hatchway':'breach point'} this operative successfully opened. Mission progress and AP are committed when this action resolves.</p><div class="field"><label for="activationBreachTarget">${targetLabel}</label><select id="activationBreachTarget"><option value="">${targetPlaceholder}</option>${available.map(feature=>`<option value="${escapeHtml(feature.id)}" ${feature.id===pendingId?'selected':''}>${escapeHtml(feature.label)}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" id="cancelActivationBreach">Back</button><button class="btn primary" id="confirmActivationBreach" ${pendingId?'':'disabled'}>Confirm Target</button></div>`,undefined,'activation-breach-target');
    const select=$('#activationBreachTarget'),confirm=$('#confirmActivationBreach');
    select.onchange=()=>{confirm.disabled=!available.some(feature=>feature.id===select.value);};
    $('#cancelActivationBreach').onclick=()=>stage.sequential?cancelCurrentHumanPlayerAction():showPlayerActivation(stage);
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
          if(!Number.isInteger(transaction.roll)){
            if(!transaction.requesting){
              transaction.requesting=true;
              const requestKey=diceRequestKey('reanimation-protocols',transaction.id,n.id);
              void requestDiceResults({count:1,sides:6,title:'REANIMATION PROTOCOLS',rollerLabel:npoName(n),requestKey,resumeKind:'combat',resumeData:{transactionId:transaction.id,npoId:n.id},
                instruction:'Roll 1D6 for Reanimation Protocols and enter the result.'}).then(([value])=>{
                transaction.roll=value;delete transaction.requesting;save();
                acknowledgeDiceRequest(requestKey);
                if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);
              }).catch(error=>{delete transaction.requesting;console.error('[Reanimation Protocols] Dice request failed. No combat consequence was applied.',error);});
            }
            return true;
          }
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
      if(pending.attackType==='shoot'&&npoDefinition(n.type)?.id==='hexmark-destroyer'&&!pending.multiThreatResolved){
        void resolveMultiThreatEliminator(stage,pending,n);return true;
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
      if(checkGameEnd()&&!stage.sequential)return true;
    }
    return false;
  }

  function finalDiscardedFailedAttackDice(attackDice=[]){return attackDice.filter(die=>!die.retained&&die.kind==='miss').length;}
  function focusedHexmarkReactionProfile(hexmark,failedDice){
    const focused=npoAttackProfiles(hexmark,'shoot').map(canonicalAttackProfile).find(profile=>profile.profileId==='focused');
    return focused?{...focused,dice:Math.min(finalDiscardedFailedAttackDice(failedDice)+1,4)}:null;
  }
  async function resolveMultiThreatEliminator(stage,pending,hexmark){
    const transactionId=pending.transactionId||`${playerActionTransactionIdentity(stage,'shoot').activationId}:shoot:${hexmark.id}`;
    const reaction=stage3Trigger(`multi-threat-eliminator:${transactionId}`,{shootTransactionId:transactionId,withinEight:null,offered:false,decision:null,attackCount:null,profile:null,orderBefore:null,orderChanged:false,attackDice:null,defenseDice:null,damageCommitted:false});
    if(reaction.status==='complete'){pending.multiThreatResolved=true;if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);return;}
    if(reaction.withinEight===null){reaction.withinEight=await askYesNoRuleQuestion('Multi-Threat Eliminator',STAGE3_RULE_TEXT.multiThreatRange);save();}
    if(!reaction.withinEight){reaction.status='complete';pending.multiThreatResolved=true;save();if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);return;}
    if(!reaction.offered){reaction.offered=true;save();}
    if(reaction.decision===null){reaction.decision=isPvpMode()?await askPerformOrSkip('Multi-Threat Eliminator','The Hexmark can perform a free Shoot against the attacking operative.'):'perform';save();}
    if(reaction.decision==='skip'){reaction.status='complete';pending.multiThreatResolved=true;save();if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);return;}
    const profile=reaction.profile?{...reaction.profile}:focusedHexmarkReactionProfile(hexmark,pending.attackDice||[]);if(!profile)return;
    if(!reaction.profile){reaction.attackCount=profile.dice;reaction.profile={...profile};reaction.orderBefore=hexmark.order;reaction.orderChanged=true;hexmark.order='Engage';save();}
    else if(reaction.orderChanged&&hexmark.order!=='Engage'){hexmark.order='Engage';save();}
    const base=`multi-threat-eliminator:${transactionId}`;
    if(!reaction.attackDice){reaction.attackDice=await requestAttackDiceForProfile(profile,{rollerLabel:npoName(hexmark),requestKeyBase:base,attackerSide:'npo'});save();}
    if(!reaction.defenseDice){reaction.defenseDice=await requestDefenseDice(effectiveDefenseDiceCount(profile,reaction.attackDice,3),playerDefinition(stage.playerOperativeId)?.save||3,{rollerLabel:playerName(stage.playerOperativeId),requestKeyBase:base});save();acknowledgeDiceRequest(`${base}:defense`);}
    if(!reaction.damageCommitted){const result=resolveRetainedCombat(reaction.attackDice,reaction.defenseDice,profile),damage=result.damage+devastatingDamageForAttack(reaction.attackDice,profile);commitStage3PlayerDamage(stage.playerOperativeId,damage,{sourceNpo:hexmark,transactionId:`multi-threat-eliminator:${transactionId}`});reaction.damageCommitted=true;}
    reaction.status='complete';pending.multiThreatResolved=true;save();if(!applyPendingPlayerDamage(stage))finishPlayerAttackResolution(stage);
  }
  function askYesNoRuleQuestion(title,question){return new Promise(resolve=>{showModal(title,`<p>${escapeHtml(question)}</p><div class="wizard-actions"><button class="btn ghost" id="ruleAnswerNo">No</button><button class="btn primary" id="ruleAnswerYes">Yes</button></div>`);$('#ruleAnswerNo').onclick=()=>{closeModal();resolve(false);};$('#ruleAnswerYes').onclick=()=>{closeModal();resolve(true);};});}
  function askPerformOrSkip(title,message){return new Promise(resolve=>{showModal(title,`<p>${escapeHtml(message)}</p><div class="wizard-actions"><button class="btn ghost" id="skipRuleAction">Skip</button><button class="btn primary" id="performRuleAction">Perform Free Shoot</button></div>`);$('#skipRuleAction').onclick=()=>{closeModal();resolve('skip');};$('#performRuleAction').onclick=()=>{closeModal();resolve('perform');};});}
  function commitStage3PlayerDamage(operativeId,damage,{sourceNpo=null,transactionId=''}={}){
    if(!inPlayLivingPlayerOperativeIds().includes(operativeId))return false;
    const before=playerCurrentWounds(operativeId);
    state.playerWounds[operativeId]=Math.max(0,before-Math.max(0,Number(damage)||0));
    if(state.playerWounds[operativeId]<=0){
      if(!state.playerCasualtyIds.includes(operativeId))state.playerCasualtyIds.push(operativeId);
      if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
    }
    if(before>0&&state.playerWounds[operativeId]<=0&&sourceNpo)void resolveRewardsOfAnnihilation(sourceNpo,{id:operativeId,maxWounds:playerDefinition(operativeId)?.wounds},{transactionId});
    state.playerReady=playerOperativesRemaining();return true;
  }

  async function showAggressiveDefenseResolution(stage,pending,target,incapacitationId){
    const retaliation=eventTransaction(`aggressive-defence:${incapacitationId}`);
    if(!Number.isInteger(retaliation.roll)){
      try{
        const requestKey=diceRequestKey('aggressive-defence',retaliation.id,target.id);
        [retaliation.roll]=await requestDiceResults({count:1,sides:3,title:'AGGRESSIVE DEFENCE',rollerLabel:npoName(target),requestKey,resumeKind:'combat',resumeData:{transactionId:retaliation.id,targetId:target.id},
          instruction:'Roll 1D3 on the tabletop and enter the result.'});
      }catch(error){console.error('[Aggressive Defence] Dice request failed. No retaliation damage was applied.',error);return;}
    }
    pending.aggressiveDefenseRoll=retaliation.roll;
    pending.aggressiveDefenseDamage=aggressiveDefenseDamage(retaliation.roll);
    retaliation.committed=true;
    state.combatState={side:'player',stage:{...stage}};
    save();
    acknowledgeCurrentDiceRequest();
    missionDialogLocked=true;
    const animate=!isPvpMode();
    showModal('Aggressive Defence',`<p><strong>${escapeHtml(npoName(target))}</strong> was incapacitated by an enemy operative within 2 inches.</p><section class="combat-stage" aria-label="Aggressive Defence roll"><div class="dice-row ${animate?'animated-roll':'settled'}" id="aggressiveDefenseDie">${animate?rollingDieHtml():dieHtml({value:retaliation.roll,kind:'hit',retained:true})}</div><div id="aggressiveDefenseResult" aria-live="polite" ${animate?'hidden':''}><strong>D3 Roll: ${retaliation.roll}</strong><p>${pending.aggressiveDefenseDamage?'The attacking operative suffers 1 damage.':'The attacking operative suffers no damage.'}</p></div></section><div class="wizard-actions"><button class="btn primary" id="continueAggressiveDefense" ${animate?'disabled':''}>Continue</button></div>`);
    if(animate)void TombWorldDiceSfx.play();
    const button=$('#continueAggressiveDefense');
    const die=$('#aggressiveDefenseDie');
    if(animate)setTimeout(()=>{
      if(!button?.isConnected)return;
      die.innerHTML=dieHtml({value:retaliation.roll,kind:'hit',retained:true});
      die.classList.replace('animated-roll','settled');
      $('#aggressiveDefenseResult').innerHTML=`<strong>D3 Roll: ${retaliation.roll}</strong><p>${pending.aggressiveDefenseDamage?'The attacking operative suffers 1 damage.':'The attacking operative suffers no damage.'}</p>`;
      button.disabled=false;
    },DICE_ROLL_ANIMATION_MS);
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
    if(stage.sequential&&stage.threatCheckResult&&!stage.threatCheckResult.acknowledged){
      renderThreatCheckResult(stage);
      return true;
    }
    const requiredThreatChecks=[
      ...(stage.hatch&&state.missionId!=='scout-sub-crypt'?[{id:'operateHatch',title:'OPERATE HATCH - THREAT CHECK',instruction:'Roll 1D6. On 4+, Threat increases by 1.'}]:[]),
      ...(stage.breach?[{id:'breach',title:'BREACH - THREAT CHECK',instruction:'Roll 1D6. On 4+, Threat increases by an additional 1.'}]:[])
    ];
    stage.threatRolls=stage.threatRolls&&typeof stage.threatRolls==='object'?stage.threatRolls:{};
    if(stage.threatDiceResolving)return false;
    const missingThreatChecks=requiredThreatChecks.filter(check=>!Number.isInteger(stage.threatRolls[check.id]));
    if(missingThreatChecks.length){
      stage.threatDiceResolving=true;
      state.combatState={side:'player',stage:{...stage}};
      try{
        for(const check of missingThreatChecks){
          const requestKey=diceRequestKey('player-activation',activePlayerActivation()?.activationId||missionActivationId('player',operativeId),stage.humanActionId||'batch','threat',check.id);
          if(state.pendingDice?.status==='committed'&&state.pendingDice.requestKey!==requestKey)acknowledgeCurrentDiceRequest();
          const [die]=await requestDiceResults({count:1,sides:6,title:check.title,instruction:check.instruction,rollerLabel:playerName(operativeId),requestKey,resumeKind:'player-activation',resumeData:{activationId:missionActivationId('player',operativeId),operativeId,checkId:check.id}});
          stage.threatRolls[check.id]=die;
          state.combatState={side:'player',stage:{...stage}};save();
        }
      }catch(error){
        console.error('[Player Activation Threat Dice]',error);
        stage.threatDiceResolving=false;
        state.combatState={side:'player',stage:{...stage}};
        save();
        return false;
      }
      stage.threatDiceResolving=false;
      state.combatState={side:'player',stage:{...stage}};
      save();
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
    let inc=0;
    if(stage.shoot)inc++;
    if(stage.melee)inc++;
    if(stage.damage)inc++;
    if(stage.hatch&&state.missionId!=='scout-sub-crypt'){
      const r=stage.threatRolls.operateHatch;
      if(r>=4)inc++;
    }
    if(stage.breach){
      inc++;
      const r=stage.threatRolls.breach;
      if(r>=4)inc++;
    }
    const threatCommitKey=stage.sequential?`threat:${stage.humanActionId}:${activePlayerActivation()?.pendingAction?.actionSequence||0}`:'batch-threat';
    const threatAlreadyCommitted=stage.sequential&&(activePlayerActivation()?.committedEffectKeys||[]).includes(threatCommitKey);
    const threatBefore=state.threat;
    if(!threatAlreadyCommitted){
      if(inc)setThreat(inc,stage.sequential?`${stage.humanActionName} action`:'Player activation');
      if(stage.sequential){
        const activation=activePlayerActivation();
        activation.committedEffectKeys=[...(activation.committedEffectKeys||[]),threatCommitKey];
      }
    }
    if(stage.sequential){
      if((stage.hatch&&state.missionId!=='scout-sub-crypt')||stage.breach){
        const type=stage.breach?'breach':'operateHatch';
        const roll=stage.threatRolls[type];
        if(!stage.threatCheckResult){
          stage.threatCheckResult=buildThreatCheckResult(type,roll,threatBefore,state.threat);
        }
        state.combatState={side:'player',stage:{...stage}};
        save();
        if(!stage.threatCheckResult.acknowledged){renderThreatCheckResult(stage);return true;}
      }
      commitHumanPlayerAction(stage);
      return true;
    }
    state.combatState=null;
    state.missionActionContext=null;
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
    acknowledgeCurrentDiceRequest();
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

  function weaponRulesHtml(profile,{semanticHeading=false}={}){
    const summaries=weaponRuleSummaries(profile).map(summary=>`<li>${escapeHtml(summary.label)}</li>`).join('');
    const heading=semanticHeading?'<h3>Weapon Rules</h3>':'<strong>Weapon rules</strong>';
    return summaries?`<section class="weapon-rules">${heading}<ul>${summaries}</ul></section>`:'';
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
    if(isPvpMode())return '';
    const definition=npoDefinition(npo?.type);
    const weaponSentinel=(definition?.abilities||[]).find(ability=>ability.id==='weapon-sentinel');
    const rawGuidance=definition?.behavior?.weaponGuidance;
    const guidance=typeof rawGuidance==='string'
      ? {text:rawGuidance,...inferWeaponGuidanceContext(definition,rawGuidance)}
      : rawGuidance&&typeof rawGuidance==='object'
        ? {...(inferWeaponGuidanceContext(definition,rawGuidance.text)||{}),...rawGuidance}
        : null;
    const injuredReminder=npo&&npo.wounds<npo.maxWounds&&activeNpos().some(item=>npoDefinition(item.type)?.id==='royal-warden')?{text:STAGE3_RULE_TEXT.engrammatic,attackType}:null;
    const items=[guidance,weaponSentinel&&{text:`${weaponSentinel.name}: ${weaponSentinel.text}`,attackType:'shoot'},injuredReminder]
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

  function reuseCommittedDimensionalBanishment(combat){
    if(combat.dimensionalBanishmentResolved)return {...combat};
    if(Number.isInteger(combat.dimensionalBanishmentRoll)&&combat.dimensionalBanishmentRoll>0){
      return resolveDimensionalBanishment(combat,[]);
    }
    return {...combat};
  }

  async function requestDimensionalBanishment(combat,rollerLabel){
    if(combat.dimensionalBanishmentResolved)return {...combat};
    if(Number.isInteger(combat.dimensionalBanishmentRoll)&&combat.dimensionalBanishmentRoll>0)return resolveDimensionalBanishment(combat,[]);
    const triggered=combat.profile?.weaponId==='transdimensional-isolator'
      &&combatAbilityHandlers['dimensional-banishment']({criticalSuccesses:combat.critRemaining,damage:combat.damage,targetIncapacitated:combat.after<=0});
    const requestKey=diceRequestKey('combat',combat.transactionId||combat.targetId,combat.profile?.weaponId,combat.profile?.profileId,'dimensional-banishment');
    const dice=triggered?await requestDiceResults({count:2,sides:6,title:'DIMENSIONAL BANISHMENT',rollerLabel,requestKey,resumeKind:'combat',resumeData:{transactionId:combat.transactionId||'',targetId:combat.targetId||''},
      instruction:'Roll 2D6 on the tabletop and enter each result.'}):[];
    return resolveDimensionalBanishment(combat,dice);
  }

  function classifyCombatDice(values,threshold,critThreshold=6){
    return values.map(value=>({value,kind:value>=critThreshold?'crit':value>=threshold?'hit':'miss',retained:false}));
  }
  function rolledCombatDice(count,threshold,critThreshold=6){
    return classifyCombatDice(rollDice(Math.max(0,count),6),threshold,critThreshold);
  }
  function rolledAttackDiceForProfile(profile){
    const accurate=Math.min(Number(profile?.accurate||0),Math.max(0,Number(profile?.dice||0)));
    const retainedDice=retainSuccessfulDice([
      ...Array.from({length:accurate},()=>({value:Number(profile.hit||2),kind:'hit',retained:true,automatic:'Accurate 1'})),
      ...rolledCombatDice(Math.max(0,Number(profile.dice||0)-accurate),profile.hit,profile.critThreshold)
    ]);
    const severe=applySevereToAttackDice(retainedDice,profile);
    return applyRendingToAttackDice(severe.dice,profile).dice;
  }

  async function requestAttackDiceForProfile(profile,{rollerLabel='',requestKeyBase='',attackerSide='npo',container,onInitialRoll}={}){
    const total=Math.max(0,Number(profile?.dice||0));
    const accurate=Math.min(Number(profile?.accurate||0),total);
    const rolledCount=total-accurate;
    const requestKey=`${requestKeyBase||diceRequestKey('combat',profile.weaponId,profile.profileId)}:attack`;
    const values=rolledCount?await requestDiceResults({
      count:rolledCount,sides:6,title:'ATTACK ROLL',rollerLabel,
      instruction:`Roll ${rolledCount}D6 on the tabletop and enter each result.${accurate?` Accurate ${accurate} already retained ${accurate===1?'one normal success':`${accurate} normal successes`}.`:''}`,requestKey,resumeKind:'combat',resumeData:{phase:'attack'}
    }):[];
    const dice=retainSuccessfulDice([
      ...Array.from({length:accurate},()=>({value:Number(profile.hit||2),kind:'hit',retained:true,automatic:'Accurate 1'})),
      ...classifyCombatDice(values,profile.hit,profile.critThreshold)
    ]);
    if(onInitialRoll)onInitialRoll(dice);
    if(isPvpMode())acknowledgeDiceRequest(requestKey);
    const rerolled=await applyWeaponRuleRerolls(dice,profile,{attackerSide,container,rollerLabel,requestKeyBase,onCheckpoint:onInitialRoll});
    const severe=applySevereToAttackDice(retainSuccessfulDice(rerolled),profile);
    return applyRendingToAttackDice(severe.dice,profile).dice;
  }

  async function requestDefenseDice(count,threshold,{rollerLabel='',requestKeyBase=''}={}){
    if(count<=0)return [];
    const requestKey=`${requestKeyBase||diceRequestKey('combat')}:defense`;
    const values=await requestDiceResults({count,sides:6,title:'DEFENSE ROLL',rollerLabel,requestKey,resumeKind:'combat',resumeData:{phase:'defense'},
      instruction:`Roll ${count}D6 on the tabletop and enter each result.`});
    return retainSuccessfulDice(classifyCombatDice(values,Number(threshold)||3));
  }

  function retainSuccessfulDice(dice=[]){
    return dice.map(die=>({...die,retained:die.kind==='hit'||die.kind==='crit'}));
  }

  function applyRendingToAttackDice(dice,profile){
    const updatedDice=(dice||[]).map(die=>({...die}));
    if(!weaponHasRule(profile,'rending')||!updatedDice.some(die=>die.retained&&die.kind==='crit'))return {dice:updatedDice,applied:false,convertedIndex:-1};
    const convertedIndex=updatedDice.findIndex(die=>die.retained&&die.kind==='hit');
    if(convertedIndex<0)return {dice:updatedDice,applied:false,convertedIndex:-1};
    updatedDice[convertedIndex]={...updatedDice[convertedIndex],kind:'crit',originalKind:'hit',rendingConverted:true};
    return {dice:updatedDice,applied:true,convertedIndex};
  }

  function applyAttackSuccessConversions(dice,profile){
    const severe=applySevereToAttackDice(retainSuccessfulDice(dice),profile);
    return applyRendingToAttackDice(severe.dice,profile).dice;
  }

  function beneficialRerollChoice(dice,profile,ruleId){
    const candidates=(dice||[]).map((die,index)=>({die,index})).filter(item=>!item.die.automatic&&item.die.kind!=='crit');
    if(!candidates.length)return null;
    if(ruleId==='balanced'){
      const failed=candidates.filter(item=>item.die.kind==='miss').sort((a,b)=>a.die.value-b.die.value||a.index-b.index);
      return (failed[0]||null)?.index??null;
    }
    const failedCounts=new Map();
    candidates.filter(item=>item.die.kind==='miss').forEach(item=>failedCounts.set(item.die.value,(failedCounts.get(item.die.value)||0)+1));
    return [...failedCounts].sort((a,b)=>b[1]-a[1]||a[0]-b[0])[0]?.[0]??null;
  }

  function chooseHumanWeaponReroll(container,dice,ruleId){
    return new Promise(resolve=>{
      const label=ruleId==='balanced'?'Balanced':'Ceaseless';
      const choices=ruleId==='balanced'
        ? dice.map((die,index)=>({die,index})).filter(item=>!item.die.automatic).map(item=>({value:String(item.index),label:`Die ${item.index+1}: ${item.die.value}`}))
        : [...new Set(dice.filter(die=>!die.automatic).map(die=>die.value))].sort().map(value=>({value:String(value),label:`All ${value}s`}));
      container.innerHTML=`<section class="combat-stage weapon-reroll-choice"><small>${label.toUpperCase()} REROLL</small><div class="dice-row settled">${dice.map(dieHtml).join('')}</div><p>${label==='Balanced'?'Select exactly one attack die to reroll, or Skip.':'Select one rolled result value; every die showing it will be rerolled. Or Skip.'}</p><div class="wizard-actions">${choices.map(choice=>`<button class="btn secondary" type="button" data-reroll-choice="${choice.value}">${choice.label}</button>`).join('')}<button class="btn ghost" type="button" data-reroll-skip>Skip</button></div></section>`;
      $$('[data-reroll-choice]',container).forEach(button=>button.onclick=()=>resolve(button.dataset.rerollChoice));
      $('[data-reroll-skip]',container).onclick=()=>resolve(null);
    });
  }

  function markWeaponRerollResolved(dice,ruleId){
    return (dice||[]).map(die=>({...die,rerollRulesResolved:[...new Set([...(die.rerollRulesResolved||[]),ruleId])]}));
  }

  function weaponRuleRerollsComplete(dice,profile){
    const rules=['balanced','ceaseless'].filter(ruleId=>weaponHasRule(profile,ruleId));
    return rules.every(ruleId=>(dice||[]).every(die=>(die.rerollRulesResolved||[]).includes(ruleId)));
  }

  async function applyWeaponRuleRerolls(dice,profile,{attackerSide='npo',container,rollerLabel='',requestKeyBase='',onCheckpoint}={}){
    let updated=(dice||[]).map(die=>({...die}));
    const humanControlled=attackerSide==='player'||isPvpMode();
    for(const ruleId of ['balanced','ceaseless']){
      if(!weaponHasRule(profile,ruleId))continue;
      if(updated.every(die=>(die.rerollRulesResolved||[]).includes(ruleId)))continue;
      const requestKey=`${requestKeyBase||diceRequestKey('combat',profile.weaponId,profile.profileId)}:reroll:${ruleId}:1`;
      const resumedIndexes=state.pendingDice?.requestKey===requestKey&&state.pendingDice?.resumeData?.ruleId===ruleId
        ? state.pendingDice.resumeData.selectedIndexes : null;
      const choice=Array.isArray(resumedIndexes)?null:humanControlled?await chooseHumanWeaponReroll(container,updated,ruleId):beneficialRerollChoice(updated,profile,ruleId);
      if(!Array.isArray(resumedIndexes)&&(choice===null||choice===undefined)){
        updated=markWeaponRerollResolved(updated,ruleId);
        if(onCheckpoint)onCheckpoint(updated);
        continue;
      }
      const indexes=Array.isArray(resumedIndexes)
        ? resumedIndexes.filter(index=>Number.isInteger(index)&&updated[index]&&!updated[index].automatic)
        : ruleId==='balanced'
          ? [Number(choice)].filter(index=>Number.isInteger(index)&&updated[index]&&!updated[index].automatic)
          : updated.map((die,index)=>!die.automatic&&die.value===Number(choice)?index:-1).filter(index=>index>=0);
      if(!indexes.length){updated=markWeaponRerollResolved(updated,ruleId);if(onCheckpoint)onCheckpoint(updated);continue;}
      const replacements=await requestDiceResults({requestKey,resumeKind:'combat',resumeData:{phase:'attack-reroll',ruleId,weaponId:profile.weaponId,profileId:profile.profileId,selectedIndexes:indexes},count:indexes.length,sides:6,title:`${ruleId.toUpperCase()} REROLL`,rollerLabel,
        instruction:`Reroll ${indexes.length===1?`the selected die (${updated[indexes[0]].value})`:`all ${updated[indexes[0]].value}s (${indexes.length} dice)`} and enter ${indexes.length===1?'its result':'each result'}.`,
      });
      indexes.forEach((index,replacementIndex)=>{updated[index]={...updated[index],...classifyCombatDice([replacements[replacementIndex]],profile.hit,profile.critThreshold)[0],rerolledBy:ruleId};});
      updated=markWeaponRerollResolved(updated,ruleId);
      if(onCheckpoint)onCheckpoint(updated);
      if(isPvpMode())acknowledgeDiceRequest(requestKey);
    }
    return updated;
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
    const devastating=weaponRuleValue(profile,'devastating');
    const criticals=retainedDiceTotals(attackDice).critical;
    if(devastating>0&&criticals>0)messages.push(`Devastating ${devastating}: ${criticals*devastating} immediate damage from ${criticals} retained critical ${criticals===1?'success':'successes'}; those critical successes remain in the attack pool.`);
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
    showModal('Shock',`<p id="shockHelp">Did ${isPvpMode()?'the attacking Necron':'this NPO'} just strike with its first critical success?</p><p class="muted">Check the unresolved successes in this Fight sequence. Shock triggers only once.</p><div class="wizard-actions"><button class="btn ghost" id="shockBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn secondary" id="shockNo">No</button><button class="btn primary" id="shockYes">Yes</button></div>`);
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
    if(id==='dimensional-banishment')return {id,label:'Dimensional Banishment: After this attack, if the rule triggers and the target survives, the Guide rolls 2D6. If the total exceeds the target’s remaining wounds, it is incapacitated. Handled automatically.'};
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

  async function resolveHotTransaction(record){
    if(record.acknowledged)return record;
    if(!record.effectiveHit){
      console.warn('[Hot] Effective Hit stat is unavailable.',{attackerId:record.attackerId,weaponId:record.weaponId,profileId:record.profileId,storedHit:record.effectiveHit});
      return {...record,status:'error',damage:0,applied:true};
    }
    if(!Number.isInteger(record.roll)){
      const name=record.attackerSide==='player'?playerName(record.attackerId):npoName(state.roster.find(npo=>npo.id===record.attackerId));
      const requestKey=`${record.id}:roll`;
      const [value]=await requestDiceResults({count:1,sides:6,title:'HOT TEST',rollerLabel:name,requestKey,resumeKind:'hot',resumeData:{hotResolutionId:record.id},
        instruction:`Roll 1D6 for ${record.weaponName||'this weapon'} and enter the result.`});
      record={...record,roll:value};
      state.hotResolution=record;
      save();
      acknowledgeDiceRequest(requestKey);
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

  async function showHotResult(record,onContinue){
    try{record=await resolveHotTransaction(record);}
    catch(error){console.error('[Hot] Dice request failed. No Hot damage was applied.',error);return;}
    state.hotResolution=record;save();
    missionDialogLocked=true;
    if(record.status==='error'){
      showModal('Hot could not be resolved',`<p>The weapon's Hit stat could not be determined. The shooting attack was preserved and no Hot damage was applied.</p><div class="wizard-actions"><button class="btn primary" id="continueHot">Continue</button></div>`);
    }else{
      const name=record.attackerSide==='player'?playerName(record.attackerId):npoName(state.roster.find(npo=>npo.id===record.attackerId));
      const comparison=record.damage?`${record.roll} is lower than ${record.effectiveHit}.`:`The result is not lower than the weapon's Hit stat.`;
      const outcome=record.incapacitated?`${escapeHtml(name)} is incapacitated by Hot.`:record.damage?`${escapeHtml(name)} suffers ${record.damage} damage.<br>Wounds: ${record.woundsBefore} -&gt; ${record.woundsAfter}`:'No damage.';
      const reducedMotion=isPvpMode()||matchMedia('(prefers-reduced-motion: reduce)').matches;
      const die=reducedMotion?dieHtml({value:record.roll,ariaLabel:`Hot roll: ${record.roll}`}):rollingDieHtml();
      showModal('HOT',`<section class="combat-stage" aria-label="Hot result"><div class="dice-row ${reducedMotion?'settled':'animated-roll'}" id="hotRollDie">${die}</div><div id="hotRollResult" ${reducedMotion?'':'hidden'}><p><strong>Hot roll: ${record.roll}</strong><br>Hit stat: ${record.effectiveHit}+</p><p>${escapeHtml(comparison)}</p><strong>${outcome}</strong></div></section><div class="wizard-actions"><button class="btn primary" id="continueHot" ${reducedMotion?'':'disabled'}>Continue</button></div>`,undefined,`hot:${record.id}`);
      if(!reducedMotion){
        void TombWorldDiceSfx.play();
        setTimeout(()=>{
          const rollDie=$('#hotRollDie');
          if(!rollDie?.isConnected)return;
          rollDie.innerHTML=dieHtml({value:record.roll,ariaLabel:`Hot roll: ${record.roll}`});
          rollDie.classList.replace('animated-roll','settled');
          $('#hotRollResult').hidden=false;
          $('#continueHot').disabled=false;
        },DICE_ROLL_ANIMATION_MS);
      }
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
    void showHotResult(record,onContinue);
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
    const attackerLabel=attackerSide==='npo'?(isPvpMode()?'Necron':'NPO'):playerSideLabel();
    showModal('Attack profile unavailable',`<div class="modal-inner"><div class="summary-box"><strong>Attack profile unavailable</strong><p>The weapon selected for this multi-target attack could not be restored. Completed target results were preserved.</p></div><div class="wizard-actions"><button class="btn primary" id="returnFromMissingProfile">Return to ${escapeHtml(attackerLabel)} Activation</button></div></div>`);
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

  function showSecondaryTargetCheck({ruleId,distance,attackerSide,attackerId,activationId=null,actionId=null,primaryTargetId,targets,weaponId,weaponName,profileKey,profileName,weaponRules,onContinue,onBack}){
    const isBlast=ruleId==='blast';
    const eligible=(targets||[]).filter(target=>target.id!==attackerId&&target.id!==primaryTargetId&&target.inPlay!==false&&Number(target.wounds)>0);
    const question=isBlast
      ? `Which other operatives are visible to and within ${distance} inches of the primary target?`
      : `Are there other valid targets within ${distance} inches of the primary target?`;
    const help=isBlast
      ? `Blast attacks every other operative visible to and within ${distance} inches of the primary target, including friendly operatives.`
      : `Torrent attacks each selected valid enemy target within ${distance} inches of the primary target.`;
    const saved=state.weaponRuleResolution;
    const sameStep=saved?.ruleId===ruleId&&saved?.primaryTargetId===primaryTargetId&&saved?.profileKey===profileKey;
    showModal(ruleId[0].toUpperCase()+ruleId.slice(1),`<p id="secondaryTargetHelp">${escapeHtml(question)}</p><p class="muted">${escapeHtml(help)}</p><div class="checklist" aria-describedby="secondaryTargetHelp">${eligible.length?eligible.map(weaponRuleTargetOption).join(''):'<p class="muted">No other operatives are available.</p>'}</div><label class="check-row required-confirmation-row"><input id="tabletopCheckConfirmed" type="checkbox"><span>I have confirmed visibility and distance on the tabletop.</span></label><div class="wizard-actions"><button class="btn ghost" id="secondaryTargetsBack">Back</button><button class="btn ghost" data-close>Close Guide</button><button class="btn primary" id="confirmSecondaryTargets" disabled>Continue</button></div>`);
    $$('[data-weapon-rule-target]').forEach(input=>{input.checked=sameStep?(saved.secondaryTargetIds||[]).includes(input.value):false;});
    const confirmation=$('#tabletopCheckConfirmed');
    confirmation.checked=Boolean(sameStep&&saved.tabletopCheckConfirmed);
    const persistStep=()=>{
      const secondaryTargetIds=$$('[data-weapon-rule-target]:checked').map(input=>input.value).filter(id=>id!==primaryTargetId);
      const seekLightAnswer=state.weaponRuleResolution?.primaryTargetId===primaryTargetId?state.weaponRuleResolution.seekLightAnswer:null;
      const selectedTargets=[{id:primaryTargetId,targetSide:attackerSide==='player'?'npo':'player'},...eligible.filter(target=>secondaryTargetIds.includes(target.id))];
      const targetDescriptors=selectedTargets.map(target=>({targetId:target.id,targetSide:target.targetSide||(attackerSide==='player'?'npo':'player')}));
      const resolution=createWeaponRuleResolution({activationId:activationId||`${state.turningPoint}:${state.activationNumber}`,actionId:actionId||(attackerSide==='npo'?'npo-attack':'player-attack'),attackerSide,attackerId,weaponId,weaponName,profileKey,profileName,weaponRules,ruleId,primaryTargetId,secondaryTargetIds,targetDescriptors});
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
    const pending=attackerSide==='player'?'<p class="muted">These results remain pending until this combat action is committed.</p>':'';
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

  function attackRuleAppliedHtml(dice=[]){
    const messages=[];
    if(dice.some(die=>die.rendingConverted))messages.push('Rending applied: one normal success became a critical success.');
    const rerollRules=[...new Set(dice.map(die=>die.rerolledBy).filter(Boolean))];
    rerollRules.forEach(rule=>messages.push(`${rule[0].toUpperCase()+rule.slice(1)} reroll applied.`));
    return messages.map(message=>`<p class="severe-applied" role="status">${escapeHtml(message)}</p>`).join('');
  }

  function runAutomaticCombatRolls({container,profile,defenseSave,defenderWounds=0,attackerSide='npo',attackType='shoot',attackerLabel='',defenderLabel='',requestKeyBase='',rolledAttackDice=null,rolledDefenseDice=null,onAttackComplete,onComplete,onError}){
    // Restored pools still receive the same conversion represented previously by
    // applySevereToAttackDice(retainSuccessfulDice(rolledAttackDice),profile).dice;
    // Fresh pools remain: rolledAttackDice ? restored : await requestAttackDiceForProfile(profile, ...).
    // Solo attacks formerly entered through rolledAttackDiceForProfile(profile); the
    // Dice Provider path now supplies the same classified pool before shared rerolls.
    let timer=null;
    let cancelled=false;
    const run=async()=>{
      try{
        let attackDice;
        if(rolledAttackDice){
          if(isPvpMode()&&state.pendingDice?.requestKey===`${requestKeyBase}:attack`)acknowledgeDiceRequest(state.pendingDice.requestKey);
          const needsRerollResume=!weaponRuleRerollsComplete(rolledAttackDice,profile);
          const resumedDice=needsRerollResume
            ? await applyWeaponRuleRerolls(rolledAttackDice,profile,{attackerSide,container,rollerLabel:attackerLabel,requestKeyBase,onCheckpoint:onAttackComplete})
            : rolledAttackDice;
          attackDice=applyAttackSuccessConversions(resumedDice,profile);
        }else attackDice=await requestAttackDiceForProfile(profile,{rollerLabel:attackerLabel,requestKeyBase,attackerSide,container,onInitialRoll:onAttackComplete});
        if(cancelled||!container.isConnected)return;
        if(isPvpMode()&&!rolledAttackDice&&onAttackComplete){onAttackComplete(attackDice);acknowledgeDiceRequest(`${requestKeyBase}:attack`);}
        else if(onAttackComplete)onAttackComplete(attackDice);
        const animate=!isPvpMode()&&!rolledAttackDice;
        container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row ${animate?'animated-roll':'settled'}">${animate?attackDice.map(()=>rollingDieHtml()).join(''):attackDice.map(dieHtml).join('')}</div></section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row"><span class="muted">Rolling after the attack…</span></div></section>`;
        if(animate&&attackDice.length)void TombWorldDiceSfx.play();
        if(animate)await new Promise(resolve=>{timer=setTimeout(resolve,DICE_ROLL_ANIMATION_MS);});
        if(cancelled||!container.isConnected)return;
        const devastatingDamage=devastatingDamageForAttack(attackDice,profile);
        const devastatingIncapacitated=Number(defenderWounds)>0&&devastatingDamage>=Number(defenderWounds);
        const defenseCount=effectiveDefenseDiceCount(profile,attackDice,3);
        const defenseDice=devastatingIncapacitated?[]:rolledDefenseDice||await requestDefenseDice(defenseCount,defenseSave,{rollerLabel:defenderLabel,requestKeyBase});
        if(cancelled||!container.isConnected)return;
        const animateDefense=!isPvpMode()&&!rolledDefenseDice;
        const showDefenseAnimation=!devastatingIncapacitated&&animateDefense;
        const automaticMessages=automaticWeaponRuleMessages(profile,attackDice);
        const saturateMessage=attackType==='shoot'&&weaponHasRule(profile,'saturate')?'<p role="status">Saturate: cover saves cannot be retained.</p>':'';
        container.innerHTML=`<section class="combat-stage"><small>ATTACK DICE</small><div class="dice-row settled" data-combat-attack-dice>${attackDice.map(dieHtml).join('')}</div>${severeAppliedHtml(attackDice)}${attackRuleAppliedHtml(attackDice)}${automaticMessages.map(message=>`<p role="status">${escapeHtml(message)}</p>`).join('')}</section><section class="combat-stage"><small>DEFENSE DICE</small><div class="dice-row ${showDefenseAnimation?'animated-roll':'settled'}" data-combat-save-dice>${defenseDice.length?(showDefenseAnimation?defenseDice.map(()=>rollingDieHtml()).join(''):defenseDice.map(dieHtml).join('')):'<span class="muted">No defense dice rolled</span>'}</div>${saturateMessage}</section>`;
        attackDice.immediateEffects={devastatingDamage,devastatingIncapacitated};
        if(showDefenseAnimation){
          timer=settleCombatDice({attackDice,saveDice:defenseDice},()=>{timer=null;if(container.isConnected)onComplete(attackDice,defenseDice);},container);
        }else {onComplete(attackDice,defenseDice);if(isPvpMode()&&!rolledDefenseDice&&!devastatingIncapacitated&&defenseCount>0)acknowledgeDiceRequest(`${requestKeyBase}:defense`);}
      }catch(error){
        console.error('[Combat] Dice request failed. No combat result was committed.',error);
        if(onError)onError(error);
      }
    };
    void run();
    return ()=>{
      cancelled=true;
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

  function devastatingDamageForAttack(attackDice=[],profile={}){
    const value=weaponRuleValue(profile,'devastating');
    if(!value)return 0;
    return retainedDiceTotals(attackDice).critical*value;
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

  let activeFightContinuation=null;
  let fightResumePending=false;
  let fightCompletionInProgress=false;
  function fightDicePoolsComplete(fight){return Boolean(fight?.attacker?.attackDiceComplete&&fight?.defender?.attackDiceComplete);}
  function restoreFightContinuation(){
    if(activeFightContinuation)return activeFightContinuation;
    const playerStage=state.combatState?.side==='player'?state.combatState.stage:null;
    if(playerStage)activeFightContinuation=result=>continuePlayerMultiTargetAttack(playerStage,'melee',result);
    else if(state.lastActivation?.pendingAction?.id==='fight')activeFightContinuation=result=>{
      const pending=state.lastActivation?.pendingAction;
      if(pending)commitNpoAction({actionId:pending.id,actionName:pending.name,apCost:pending.apCost,result:`${result.targetName} · Dealt ${result.damageDealt} · Suffered ${result.damageSuffered}`,attackSummary:result,attackSummaries:[result],transitionMode:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE});
    };
    return activeFightContinuation;
  }
  async function resumePersistedFight(){
    const fight=state.fightState;
    if(!fight||fightResumePending)return false;
    const continuation=restoreFightContinuation();
    if(!continuation)return false;
    fightResumePending=true;
    try{
      if(fight.pendingStage3){void resumeStage3FightTrigger(fight);}
      else if(fightDicePoolsComplete(fight)){
        if(fight.history.length)renderFightResolution();
        else renderFightRoll(fight,{animate:false});
      }
      else await startSharedFight({id:fight.id,attacker:fight.attacker,defender:fight.defender,onComplete:continuation});
      return true;
    }finally{fightResumePending=false;}
  }
  function normalizeFightState(fight){
    if(!isRecord(fight)||fight.version!==1||typeof fight.id!=='string'||!fight.id)return null;
    const participants={};
    for(const role of ['attacker','defender']){
      const participant=fight[role];
      if(!isRecord(participant)||!['player','npo'].includes(participant.side)||typeof participant.id!=='string'||!participant.id||!isRecord(participant.profile))return null;
      participants[role]={...participant,attackDice:Array.isArray(participant.attackDice)?participant.attackDice.filter(isRecord).map(item=>({...item})):[],attackDiceComplete:Boolean(participant.attackDiceComplete)};
    }
    return {...fight,...participants,turn:['attacker','defender'].includes(fight.turn)?fight.turn:'attacker',resolutionIndex:Math.max(0,Number(fight.resolutionIndex||0)),successes:Object.fromEntries(['attacker','defender'].map(role=>[role,Array.isArray(fight.successes?.[role])?fight.successes[role].filter(isRecord).map(item=>({...item})):[]])),history:Array.isArray(fight.history)?fight.history.filter(isRecord).map(item=>({...item})):[],ruleTriggers:isRecord(fight.ruleTriggers)?{...fight.ruleTriggers}:{},completed:Boolean(fight.completed),resultAcknowledged:Boolean(fight.resultAcknowledged)};
  }
  function otherFightRole(role){return role==='attacker'?'defender':'attacker';}
  function unresolvedFightSuccesses(fight,role){return (fight?.successes?.[role]||[]).filter(success=>success.status==='unresolved');}
  function fightSuccessesFromDice(id,role,dice=[]){return dice.map((die,index)=>({id:`${id}:${role}:${index}:${die.kind}`,dieIndex:index,kind:die.kind==='crit'?'critical':'normal',status:die.retained?'unresolved':'discarded',value:die.value}));}
  function fightBlockTargets(fight,role,blocker){
    const opponent=fight[otherFightRole(role)];
    if(weaponHasRule(opponent.profile,'brutal')&&blocker.kind!=='critical')return [];
    return unresolvedFightSuccesses(fight,otherFightRole(role)).filter(target=>blocker.kind==='critical'||target.kind==='normal');
  }
  function canFightBlock(fight,role,blocker){return fightBlockTargets(fight,role,blocker).length>0;}
  function advanceFightTurn(fight){
    const other=otherFightRole(fight.turn);
    if(unresolvedFightSuccesses(fight,other).length)fight.turn=other;
    else if(!unresolvedFightSuccesses(fight,fight.turn).length)fight.completed=true;
  }
  function resolveFightShock(fight,role){
    const key=`shock:${role}`;
    if(!weaponHasRule(fight[role].profile,'shock')||fight.ruleTriggers[key])return null;
    const pool=unresolvedFightSuccesses(fight,otherFightRole(role));
    const discarded=pool.find(item=>item.kind==='normal')||pool.find(item=>item.kind==='critical')||null;
    fight.ruleTriggers[key]=true;if(discarded)discarded.status='discarded-by-shock';return discarded;
  }
  function setFightOperativeWounds(participant,wounds){
    if(participant.side==='player'){
      state.playerWounds[participant.id]=Math.max(0,wounds);
      if(wounds<=0&&!state.playerCasualtyIds.includes(participant.id))state.playerCasualtyIds.push(participant.id);
      state.playerReady=playerOperativesRemaining();return;
    }
    const npo=state.roster.find(item=>item.id===participant.id);if(!npo)return;
    npo.wounds=Math.max(0,wounds);if(npo.wounds<=0){npo.ready=false;npo.deployed=false;npo.battlefieldState='out-of-action';}
  }
  function stage3Trigger(id,defaults={}){
    state.npoRuleState.stage3Triggers=state.npoRuleState.stage3Triggers||{};
    return state.npoRuleState.stage3Triggers[id]||(state.npoRuleState.stage3Triggers[id]={id,status:'pending',...defaults});
  }
  function fightParticipantDefinitionId(participant){return npoDefinition(state.roster.find(item=>item.id===participant?.id)?.type)?.id||null;}
  function shieldBlockCapacity(participant){return fightParticipantDefinitionId(participant)==='lychguard'&&participant.profile?.weaponId==='hyperphase-sword'?2:1;}
  function qualifyingWhirlingStrike(fight,role,success){return success?.kind==='critical'&&fightParticipantDefinitionId(fight?.[role])==='skorpekh-destroyer'&&fight[role].profile?.weaponId==='skorpekh-hyperphase-weapons';}
  function qualifyingHorrifyingFlaying(fight,role,after){return after<=0&&fightParticipantDefinitionId(fight?.[role])==='flayed-one';}
  async function resolveWhirlingOnslaught(fight,historyEntry){
    fight.pendingStage3=true;save();
    const occurrence=stage3Trigger(`whirling:${fight.id}:${historyEntry.index}`,{fightId:fight.id,historyIndex:historyEntry.index,candidateIds:null,damageByTarget:{}});
    if(occurrence.status==='complete'){fight.pendingStage3=false;save();renderFightResolution();return;}
    const primaryId=fight[otherFightRole(historyEntry.role)].id;
    const eligible=inPlayLivingPlayerOperativeIds().filter(id=>id!==primaryId);
    if(!Array.isArray(occurrence.candidateIds)){
      occurrence.candidateIds=await chooseTabletopOperatives('Whirling Onslaught','Which other Player operatives are within this Skorpekh’s Control Range?',eligible,{humanChoosesAll:true});save();
    }
    for(const targetId of occurrence.candidateIds.filter(id=>inPlayLivingPlayerOperativeIds().includes(id))){
      if(occurrence.damageByTarget[targetId]!==undefined)continue;
      const requestKey=diceRequestKey('whirling-onslaught',fight.id,historyEntry.index,targetId);
      const [damage]=await requestDiceResults({count:1,sides:3,title:'WHIRLING ONSLAUGHT',instruction:'Roll D3 damage for this nearby operative.',rollerLabel:playerName(targetId),requestKey,resumeKind:'fight',resumeData:{fightId:fight.id}});
      const sourceNpo=state.roster.find(item=>item.id===fight[historyEntry.role].id);
      const before=playerCurrentWounds(targetId);
      occurrence.damageByTarget[targetId]=damage;commitStage3PlayerDamage(targetId,damage);
      if(before>0&&playerCurrentWounds(targetId)<=0&&sourceNpo)void resolveRewardsOfAnnihilation(sourceNpo,{id:targetId,maxWounds:playerDefinition(targetId)?.wounds},{transactionId:`whirling:${fight.id}:${historyEntry.index}:${targetId}`});
      save();
    }
    occurrence.status='complete';fight.pendingStage3=false;save();renderFightResolution();
  }
  async function resolveHorrifyingFlaying(fight,historyEntry){
    fight.pendingStage3=true;save();
    const occurrence=stage3Trigger(`horrifying-flaying:${fight.id}:${historyEntry.index}`,{fightId:fight.id,historyIndex:historyEntry.index,candidateIds:null,targetId:null,roll:null,applied:false});
    if(occurrence.status==='complete'){fight.pendingStage3=false;save();renderFightResolution();return;}
    const incapacitatedId=historyEntry.targetId,eligible=inPlayLivingPlayerOperativeIds().filter(id=>id!==incapacitatedId);
    if(!Array.isArray(occurrence.candidateIds)){occurrence.candidateIds=await chooseTabletopOperatives('Horrifying Flaying',STAGE3_RULE_TEXT.horrifyingCandidates,eligible,{humanChoosesAll:!isPvpMode(),allowNone:true});save();}
    if(!occurrence.candidateIds.length){occurrence.status='complete';fight.pendingStage3=false;save();renderFightResolution();return;}
    if(!occurrence.targetId){occurrence.targetId=isPvpMode()?occurrence.candidateIds[0]:choosePriorityPlayerTarget(occurrence.candidateIds);save();}
    if(occurrence.roll===null){const [roll]=await requestDiceResults({count:1,sides:6,title:'HORRIFYING FLAYING',instruction:'Roll D6. On 3+, the selected operative suffers -1 APL.',rollerLabel:playerName(occurrence.targetId),requestKey:diceRequestKey('horrifying-flaying',fight.id,historyEntry.index),resumeKind:'fight',resumeData:{fightId:fight.id}});occurrence.roll=roll;}
    if(occurrence.roll>=3&&!occurrence.applied)occurrence.applied=applyTemporaryAplModifier({sourceId:`${fight.id}:${historyEntry.index}`,targetId:occurrence.targetId,ruleId:'horrifying-flaying',amount:-1});
    occurrence.status='complete';fight.pendingStage3=false;save();renderFightResolution();
  }
  async function resumeStage3FightTrigger(fight){
    const trigger=Object.values(state.npoRuleState.stage3Triggers||{}).find(item=>item.fightId===fight.id&&item.status!=='complete');
    const historyEntry=fight.history.find(item=>item.index===trigger?.historyIndex);
    if(!trigger||!historyEntry){fight.pendingStage3=false;save();renderFightResolution();return;}
    if(trigger.id.startsWith('whirling:'))await resolveWhirlingOnslaught(fight,historyEntry);
    else if(trigger.id.startsWith('horrifying-flaying:'))await resolveHorrifyingFlaying(fight,historyEntry);
  }
  function commitFightStrike(fight,role,successId){
    if(!fight||fight.completed||fight.turn!==role)return false;
    const success=unresolvedFightSuccesses(fight,role).find(item=>item.id===successId);if(!success)return false;
    const actor=fight[role],target=fight[otherFightRole(role)],resolvingRemaining=!unresolvedFightSuccesses(fight,otherFightRole(role)).length,damage=success.kind==='critical'?actor.profile.crit:actor.profile.normal;
    success.status='struck';const before=target.wounds,after=Math.max(0,before-damage);target.wounds=after;setFightOperativeWounds(target,after);
    const shock=success.kind==='critical'?resolveFightShock(fight,role):null;
    const historyEntry={index:fight.resolutionIndex++,type:'strike',role,successId,successKind:success.kind,damage,before,after,targetSide:target.side,targetId:target.id,...(resolvingRemaining?{resolvingRemaining:true}:{}),...(shock?{shockDiscardedSuccessId:shock.id}:{})};fight.history.push(historyEntry);
    if(after<=0){fight.completed=true;fight.incapacitatedRole=otherFightRole(role);}else advanceFightTurn(fight);save();
    if(before>0&&after<=0&&actor.side==='npo'&&target.side==='player'){
      const sourceNpo=state.roster.find(item=>item.id===actor.id);
      if(sourceNpo)void resolveRewardsOfAnnihilation(sourceNpo,{id:target.id,maxWounds:target.maxWounds},{transactionId:`fight:${fight.id}:${historyEntry.index}`});
    }
    if(typeof qualifyingWhirlingStrike==='function'&&qualifyingWhirlingStrike(fight,role,success))void resolveWhirlingOnslaught(fight,historyEntry);
    if(typeof qualifyingHorrifyingFlaying==='function'&&qualifyingHorrifyingFlaying(fight,role,after)&&target.side==='player')void resolveHorrifyingFlaying(fight,historyEntry);
    return true;
  }
  function commitFightBlock(fight,role,blockerId,targetSuccessIds){
    if(!fight||fight.completed||fight.turn!==role)return false;
    const blocker=unresolvedFightSuccesses(fight,role).find(item=>item.id===blockerId),requested=[...new Set(Array.isArray(targetSuccessIds)?targetSuccessIds:[targetSuccessIds])];
    const legal=fightBlockTargets(fight,role,blocker||{}),targets=requested.map(id=>legal.find(item=>item.id===id)).filter(Boolean),capacity=Math.max(1,Number(fight.blockCapacity?.[role]||1));
    if(!blocker||!targets.length||targets.length>capacity||targets.length!==requested.length)return false;
    blocker.status='blocked';targets.forEach(target=>{target.status='blocked';});
    fight.history.push({index:fight.resolutionIndex++,type:'block',role,successId:blocker.id,successKind:blocker.kind,blockedSuccessIds:targets.map(item=>item.id),blockedKinds:targets.map(item=>item.kind)});
    advanceFightTurn(fight);save();return true;
  }
  function soloNpoFightDecision(fight,role){
    const actor=fight[role],opponent=fight[otherFightRole(role)],own=unresolvedFightSuccesses(fight,role),enemy=unresolvedFightSuccesses(fight,otherFightRole(role)),capacity=Math.max(1,Number(fight.blockCapacity?.[role]||1));
    const kill=[...own].sort((a,b)=>(a.kind==='critical')-(b.kind==='critical')).find(item=>(item.kind==='critical'?actor.profile.crit:actor.profile.normal)>=opponent.wounds);if(kill)return {type:'strike',successId:kill.id};
    if(capacity>1&&enemy.reduce((total,item)=>total+(item.kind==='critical'?opponent.profile.crit:opponent.profile.normal),0)>=actor.wounds){
      const shieldPlans=own.map(blocker=>({blocker,targets:fightBlockTargets(fight,role,blocker).sort((a,b)=>(b.kind==='critical'?opponent.profile.crit:opponent.profile.normal)-(a.kind==='critical'?opponent.profile.crit:opponent.profile.normal)).slice(0,capacity)}))
        .filter(plan=>plan.targets.length)
        .sort((a,b)=>b.targets.reduce((total,item)=>total+(item.kind==='critical'?opponent.profile.crit:opponent.profile.normal),0)-a.targets.reduce((total,item)=>total+(item.kind==='critical'?opponent.profile.crit:opponent.profile.normal),0));
      if(shieldPlans.length)return {type:'block',successId:shieldPlans[0].blocker.id,targetSuccessIds:shieldPlans[0].targets.map(item=>item.id)};
    }
    const lethal=enemy.find(item=>(item.kind==='critical'?opponent.profile.crit:opponent.profile.normal)>=actor.wounds);
    if(lethal){const blocker=own.find(item=>fightBlockTargets(fight,role,item).some(target=>target.id===lethal.id));if(blocker){const legal=fightBlockTargets(fight,role,blocker).sort((a,b)=>(b.kind==='critical')-(a.kind==='critical'));return {type:'block',successId:blocker.id,targetSuccessIds:legal.slice(0,capacity).map(item=>item.id)};}}
    const normal=own.find(item=>item.kind==='normal');return {type:'strike',successId:(normal||own[0]).id};
  }
  function fightPoolHtml(fight,role){
    const participant=fight[role],pool=unresolvedFightSuccesses(fight,role),normal=pool.filter(item=>item.kind==='normal').length,critical=pool.length-normal;
    const active=fight.turn===role;
    return `<section class="fight-pool ${active?'active':''}" aria-label="${active?'Acting now: ':''}${escapeHtml(participant.label)}">${active?'<span class="fight-active-label">ACTING NOW</span>':''}<small>${escapeHtml(participant.label)} · ${escapeHtml(participant.profile.name)}</small><strong>${participant.wounds}/${participant.maxWounds} wounds</strong><div class="fight-unresolved"><small>UNRESOLVED SUCCESSES</small><span>★ Critical × ${critical}</span><span>● Normal × ${normal}</span></div></section>`;
  }
  function fightDiePresentation(die,index){
    const result=die.retained?(die.kind==='crit'?'critical success':'normal success'):'failure';
    return {...die,ariaLabel:`Die ${index+1}: ${die.value}, ${result}${die.rerolledBy?`, rerolled by ${die.rerolledBy}`:''}`};
  }
  function fightRollSummary(dice=[]){
    const critical=dice.filter(die=>die.retained&&die.kind==='crit').length;
    const normal=dice.filter(die=>die.retained&&die.kind==='hit').length;
    if(!critical&&!normal)return '<strong>No retained successes</strong>';
    return `<strong>${critical?`${critical} Critical ${critical===1?'Success':'Successes'}`:''}${critical&&normal?'<br>':''}${normal?`${normal} Normal ${normal===1?'Success':'Successes'}`:''}</strong>`;
  }
  function fightRollParticipantHtml(fight,role,animate){
    const participant=fight[role],profile=participant.profile,dice=participant.attackDice.map(fightDiePresentation);
    return `<section class="combat-stage fight-roll-pool" aria-label="${escapeHtml(participant.label)} Fight roll"><small>${escapeHtml(participant.label)}</small><strong>${escapeHtml(profile.name)} · ${profile.dice} dice · ${profile.hit}+ · ${profile.normal}/${profile.crit}</strong><div class="dice-row ${animate?'animated-roll':'settled'}" data-fight-roll-dice="${role}">${dice.map(die=>animate?rollingDieHtml():dieHtml(die)).join('')}</div>${attackRuleAppliedHtml(dice)}${severeAppliedHtml(dice)}<div class="fight-roll-result"><small>RESULT</small>${fightRollSummary(dice)}</div></section>`;
  }
  function renderFightRoll(fight,{animate=false}={}){
    showModal('Fight Roll',`<div class="fight-roll"><p>The Fight dice are rolled. Review each participant’s retained results before resolving successes.</p>${fightRollParticipantHtml(fight,'attacker',animate)}${fightRollParticipantHtml(fight,'defender',animate)}<div class="wizard-actions"><button class="btn primary" id="continueFightResolution" ${animate?'disabled':''}>Resolve Strike or Block</button></div></div>`);
    const continueButton=$('#continueFightResolution');
    continueButton.onclick=renderFightResolution;
    if(animate)settleAnimatedDice(['attacker','defender'].map(role=>({row:$(`[data-fight-roll-dice="${role}"]`,modal),dice:fight[role].attackDice.map(fightDiePresentation)})),()=>{if(continueButton.isConnected)continueButton.disabled=false;});
  }
  function fightResolutionRecordHtml(fight,entry){
    const actor=fight[entry.role],target=fight[otherFightRole(entry.role)];
    const actorName=actor.side==='player'?'YOU':actor.label;
    const action=entry.type==='strike'?'STRUCK':'BLOCKED';
    const detail=entry.type==='strike'
      ? `<span>${titleCaseRuleId(entry.successKind)} Success · ${entry.damage} damage</span><span>${escapeHtml(target.label)}: ${entry.before} → ${entry.after} wounds</span>`
      : `<span>Used ${titleCaseRuleId(entry.successKind)} Success to block ${entry.blockedKinds.length>1?'enemy ':`1 ${escapeHtml(target.label)} `}${entry.blockedKinds.map(titleCaseRuleId).join(' and ')} ${entry.blockedKinds.length===1?'Success':'Successes'}.</span>`;
    return `<div class="fight-resolution-record"><strong>${escapeHtml(actorName)} ${action}</strong>${detail}</div>`;
  }
  function fightLastResolutionHtml(fight){
    const latest=fight.history.at(-1);if(!latest)return '';
    const previous=fight.history.at(-2),soloExchange=!isPvpMode()&&fight[latest.role]?.side==='npo'&&previous&&fight[previous.role]?.side==='player';
    const entries=soloExchange?[previous,latest]:[latest];
    return `<section class="fight-last-resolution" role="status" aria-label="Last exchange"><small>LAST EXCHANGE</small>${entries.map(entry=>fightResolutionRecordHtml(fight,entry)).join('')}</section>`;
  }
  function equivalentRemainingFightStrikes(fight,role){
    const own=unresolvedFightSuccesses(fight,role),enemy=unresolvedFightSuccesses(fight,otherFightRole(role));
    return own.length&&!enemy.length&&new Set(own.map(success=>success.kind)).size===1?own:null;
  }
  function showFightBlockSelection(fight,role,blockerId,initialTargetId){
    const blocker=unresolvedFightSuccesses(fight,role).find(item=>item.id===blockerId),legal=fightBlockTargets(fight,role,blocker),capacity=Math.max(1,Number(fight.blockCapacity?.[role]||1));
    showModal('Shield Block',`<p><strong>Shield:</strong> this Block can block up to two unresolved successes.</p><div class="checklist">${legal.map(target=>`<label class="check-row"><input type="checkbox" name="shieldBlockTarget" value="${escapeHtml(target.id)}" ${target.id===initialTargetId?'checked':''}><span>${titleCaseRuleId(target.kind)} success</span></label>`).join('')}</div><div class="wizard-actions"><button class="btn primary" id="commitShieldBlock">Block Selected Successes</button></div>`);
    const inputs=$$('[name="shieldBlockTarget"]',modal),button=$('#commitShieldBlock');
    inputs.forEach(input=>input.onchange=()=>{const selected=inputs.filter(item=>item.checked);if(selected.length>capacity)input.checked=false;button.disabled=!inputs.some(item=>item.checked);});
    button.onclick=()=>{const selected=inputs.filter(input=>input.checked).map(input=>input.value);if(commitFightBlock(fight,role,blockerId,selected))renderFightResolution();};
  }
  function semanticFightActions(fight,role){
    const participant=fight[role],own=unresolvedFightSuccesses(fight,role),capacity=Math.max(1,Number(fight.blockCapacity?.[role]||1)),strikes=[],blocks=[],strikeKeys=new Set(),blockKeys=new Set();
    own.forEach(success=>{
      const damage=success.kind==='critical'?participant.profile.crit:participant.profile.normal,key=`${success.kind}:${damage}`;
      if(!strikeKeys.has(key)){strikeKeys.add(key);strikes.push({success,damage});}
      fightBlockTargets(fight,role,success).forEach(target=>{
        const blockKey=capacity>1?`${success.kind}:shield`:`${success.kind}:${target.kind}`;
        if(!blockKeys.has(blockKey)){blockKeys.add(blockKey);blocks.push({blocker:success,target});}
      });
    });
    return {strikes,blocks};
  }
  function fightRoleDamage(fight,role){
    return fight.history.filter(entry=>entry.type==='strike'&&entry.role===role).reduce((total,entry)=>total+Math.max(0,Number(entry.before)-Number(entry.after)),0);
  }
  function fightResultExplanation(fight,result){
    const retained=role=>(fight[role].attackDice||[]).filter(die=>die.retained).length;
    const attackerRetained=retained('attacker'),defenderRetained=retained('defender');
    if(!attackerRetained&&!defenderRetained)return ['Neither operative retained a success.','No damage was dealt.'];
    const lines=[];
    if(!attackerRetained)lines.push(`${fight.attacker.label} retained no successes.`);
    if(!defenderRetained)lines.push(`${fight.defender.label} retained no successes.`);
    ['attacker','defender'].forEach(role=>{
      const blockedKinds=fight.history.filter(entry=>entry.type==='block'&&entry.role===role).flatMap(entry=>entry.blockedKinds||[]);
      if(!blockedKinds.length)return;
      const kinds=[...new Set(blockedKinds)],count=blockedKinds.length,target=fight[otherFightRole(role)].label;
      const detail=kinds.length===1?`${titleCaseRuleId(kinds[0])} ${count===1?'Success':'Successes'}`:`${count===1?'success':'successes'}`;
      lines.push(`${fight[role].label} blocked ${count} ${target} ${detail}.`);
    });
    if(result.attackerDamageDealt>0)lines.push(`${fight.attacker.label} dealt ${result.attackerDamageDealt} total Strike damage.`);
    if(result.defenderDamageDealt>0)lines.push(`${fight.defender.label} dealt ${result.defenderDamageDealt} total Strike damage.`);
    if(result.attackerDamageDealt<=0&&result.defenderDamageDealt<=0)lines.push('No damage was dealt.');
    return lines;
  }
  function buildFightResult(fight){
    const attackerDamageDealt=fightRoleDamage(fight,'attacker'),defenderDamageDealt=fightRoleDamage(fight,'defender');
    const participant=role=>({id:fight[role].id,name:fight[role].label,side:fight[role].side,before:fight[role].initialWounds,after:fight[role].wounds,incapacitated:fight[role].wounds<=0,damageDealt:role==='attacker'?attackerDamageDealt:defenderDamageDealt});
    const result={resultVersion:2,transactionId:fight.id,attackType:'melee',attackerName:fight.attacker.label,defenderName:fight.defender.label,targetId:fight.defender.id,targetName:fight.defender.label,side:fight.defender.side,weaponName:fight.attacker.profile.name,profile:fight.attacker.profile,before:fight.defender.initialWounds,after:fight.defender.wounds,damage:attackerDamageDealt,damageDealt:attackerDamageDealt,damageSuffered:defenderDamageDealt,attackerDamageDealt,defenderDamageDealt,attackerBefore:fight.attacker.initialWounds,attackerAfter:fight.attacker.wounds,defenderBefore:fight.defender.initialWounds,defenderAfter:fight.defender.wounds,attackerIncapacitated:fight.attacker.wounds<=0,defenderIncapacitated:fight.defender.wounds<=0,participants:{attacker:participant('attacker'),defender:participant('defender')},committed:true,fightHistory:fight.history.map(item=>({...item})),fightTransactionId:fight.id};
    result.explanation=fightResultExplanation(fight,result);return result;
  }
  function fightResultParticipantHtml(participant,role){
    return `<section class="fight-result-card" aria-label="${escapeHtml(participant.name)}, ${role} participant"><h3>${escapeHtml(participant.name)}</h3><dl><div><dt>Damage Dealt</dt><dd>${participant.damageDealt}</dd></div><div><dt>Wounds</dt><dd>${participant.before} <span aria-hidden="true">→</span><span class="sr-only">to</span> ${participant.after}</dd></div></dl>${participant.incapacitated?'<strong class="fight-eliminated">ELIMINATED</strong>':''}</section>`;
  }
  function acknowledgeFightResult(fight){
    fight.resultAcknowledged=true;save();
    const continuation=activeFightContinuation||restoreFightContinuation();
    if(!continuation)return;
    fightCompletionInProgress=true;activeFightContinuation=null;
    try{continuation(fight.result);state.fightState=null;save();}
    finally{fightCompletionInProgress=false;}
  }
  function renderFightResult(fight){
    const result=fight.result;
    showModal('Fight Result',`<div class="fight-result" role="status" aria-label="Fight finished"><p class="fight-finished">FIGHT FINISHED</p><div class="fight-result-participants">${fightResultParticipantHtml(result.participants.attacker,'attacker')}${fightResultParticipantHtml(result.participants.defender,'defender')}</div><div class="fight-result-explanation"><h3>SUMMARY</h3>${result.explanation.map(line=>`<p>${escapeHtml(line)}</p>`).join('')}</div><div class="wizard-actions"><button class="btn primary" id="continueFightResult" data-dialog-focus>Continue</button></div></div>`,undefined,'fight-result');
    $('#continueFightResult').onclick=()=>{const button=$('#continueFightResult');button.disabled=true;acknowledgeFightResult(fight);};
  }
  function finishFight(fight){
    if(fightCompletionInProgress)return;
    const completeResult=fight.result?.resultVersion===2&&fight.result?.participants?.attacker&&fight.result?.participants?.defender&&Array.isArray(fight.result?.explanation);
    if(!fight.resultCommitted||!completeResult){fight.result=buildFightResult(fight);fight.resultCommitted=true;fight.resultAcknowledged=false;if(!fight.resultLogged){log(`${fight.attacker.label} fought ${fight.defender.label}: dealt ${fight.result.attackerDamageDealt} damage, suffered ${fight.result.defenderDamageDealt}.`);fight.resultLogged=true;}save();}
    if(fight.resultAcknowledged){acknowledgeFightResult(fight);return;}
    renderFightResult(fight);
  }
  function renderFightResolution(){
    const fight=state.fightState;if(!fight||fight.pendingStage3)return;if(fight.completed){finishFight(fight);return;}
    if(!unresolvedFightSuccesses(fight,fight.turn).length){
      const other=otherFightRole(fight.turn);
      if(unresolvedFightSuccesses(fight,other).length)fight.turn=other;else fight.completed=true;
      save();renderFightResolution();return;
    }
    const role=fight.turn,participant=fight[role],human=participant.side==='player'||isPvpMode();
    const automaticStrikes=equivalentRemainingFightStrikes(fight,role);
    if(human&&automaticStrikes){commitFightStrike(fight,role,automaticStrikes[0].id);renderFightResolution();return;}
    if(!human){const choice=soloNpoFightDecision(fight,role);if(choice.type==='block')commitFightBlock(fight,role,choice.successId,choice.targetSuccessIds);else commitFightStrike(fight,role,choice.successId);renderFightResolution();return;}
    const actions=semanticFightActions(fight,role);
    const strikes=actions.strikes.map(({success,damage})=>`<button class="btn secondary fight-action" data-fight-strike="${escapeHtml(success.id)}" aria-label="Strike with ${success.kind} success, deal ${damage} damage"><strong>${titleCaseRuleId(success.kind)} Success</strong><span>Deal ${damage} damage</span></button>`).join('');
    const capacity=Math.max(1,Number(fight.blockCapacity?.[role]||1));
    const blocks=actions.blocks.map(({blocker,target})=>`<button class="btn secondary fight-action" data-fight-blocker="${escapeHtml(blocker.id)}" data-fight-block-target="${escapeHtml(target.id)}" aria-label="Block enemy ${target.kind} success using ${blocker.kind} success"><strong>${titleCaseRuleId(blocker.kind)} Success</strong><span>${capacity>1?'Block up to 2 legal enemy successes':`Block 1 enemy ${titleCaseRuleId(target.kind)}`}</span></button>`).join('');
    const intro=isPvpMode()?'Starting with the attacker, players alternate resolving one success as a Strike or Block.':'You and the NPO alternate resolving one success. You choose for your operative. The Guide automatically resolves the NPO’s response.';
    showModal('Fight Resolution',`<div class="fight-sequence"><p>${intro}</p><div class="fight-pools">${fightPoolHtml(fight,'attacker')}${fightPoolHtml(fight,'defender')}</div>${fightLastResolutionHtml(fight)}<section class="fight-turn" aria-label="Acting now: ${escapeHtml(participant.label)}"><h3 class="fight-turn-heading">${escapeHtml(participant.label)}'s Turn</h3><p>Choose how ${escapeHtml(participant.label)} uses one of its unresolved successes.</p>${capacity>1?'<p><strong>Shield:</strong> this Block can block up to two unresolved successes.</p>':''}<section class="fight-action-group" aria-labelledby="fightStrikeHeading"><h4 id="fightStrikeHeading">STRIKE</h4><div class="fight-actions">${strikes}</div></section>${blocks?`<section class="fight-action-group" aria-labelledby="fightBlockHeading"><h4 id="fightBlockHeading">${capacity>1?'BLOCK · SHIELD':'BLOCK'}</h4><div class="fight-actions">${blocks}</div></section>`:''}</section><p class="muted">Choose one success to resolve. Damage and Blocks commit immediately.</p></div>`);
    $$('[data-fight-strike]',modal).forEach(button=>button.onclick=()=>{commitFightStrike(fight,role,button.dataset.fightStrike);renderFightResolution();});
    $$('[data-fight-blocker]',modal).forEach(button=>button.onclick=()=>{if(capacity>1)showFightBlockSelection(fight,role,button.dataset.fightBlocker,button.dataset.fightBlockTarget);else{commitFightBlock(fight,role,button.dataset.fightBlocker,[button.dataset.fightBlockTarget]);renderFightResolution();}});
  }
  async function rollFightParticipant(fight,role){
    const participant=fight[role];if(participant.attackDiceComplete)return;
    if(participant.attackDice?.length){
      const rerolled=weaponRuleRerollsComplete(participant.attackDice,participant.profile)
        ? participant.attackDice
        : await applyWeaponRuleRerolls(participant.attackDice,participant.profile,{attackerSide:participant.side,container:modalBody,rollerLabel:participant.label,requestKeyBase:`fight:${fight.id}:${role}`,onCheckpoint:dice=>{participant.attackDice=dice.map(item=>({...item}));save();}});
      participant.attackDice=applyAttackSuccessConversions(rerolled,participant.profile);
    }else participant.attackDice=await requestAttackDiceForProfile(participant.profile,{rollerLabel:participant.label,requestKeyBase:`fight:${fight.id}:${role}`,attackerSide:participant.side,container:modalBody,onInitialRoll:dice=>{participant.attackDice=dice.map(item=>({...item}));participant.attackDiceComplete=false;save();}});
    participant.attackDice=participant.attackDice.map(item=>({...item}));participant.attackDiceComplete=true;fight.successes[role]=fightSuccessesFromDice(fight.id,role,participant.attackDice);
    const target=fight[otherFightRole(role)];const stun=applyStunForAttack({profile:participant.profile,attackDice:participant.attackDice,sourceAttackId:`${fight.id}:${role}`,targetId:target.id,targetName:target.label,targetSide:target.side});if(stun.message)fight.messages=[...(fight.messages||[]),stun.message];save();
  }
  async function startSharedFight({id,attacker,defender,onComplete}){
    activeFightContinuation=onComplete;let fight=state.fightState?.id===id?state.fightState:null;
    if(!fight){fight={version:1,id,attacker:{...attacker},defender:{...defender},successes:{attacker:[],defender:[]},turn:'attacker',resolutionIndex:0,history:[],ruleTriggers:{},blockCapacity:{attacker:shieldBlockCapacity(attacker),defender:shieldBlockCapacity(defender)},completed:false,resultCommitted:false};state.fightState=fight;save();}
    for(const role of ['attacker','defender']){
      const participant=fight[role],current=participant.side==='player'?playerCurrentWounds(participant.id):state.roster.find(item=>item.id===participant.id)?.wounds;
      if(Number.isFinite(current)&&fight.history.length===0)participant.wounds=current;
    }
    const restored=fightDicePoolsComplete(fight);
    try{await rollFightParticipant(fight,'attacker');await rollFightParticipant(fight,'defender');acknowledgeCurrentDiceRequest();renderFightRoll(fight,{animate:!isPvpMode()&&!restored});}catch(error){console.error('[Fight] Dice request failed. The Fight remains resumable.',error);}
  }

  function fightParticipantState({side,id,label,profile,wounds,maxWounds}){
    return {side,id,label,profile:{...profile},initialWounds:Number(wounds),wounds:Number(wounds),maxWounds:Number(maxWounds)};
  }
  function choosePlayerRetaliationWeapon(operativeId,onSelected,onCancel){
    const weapons=playerAttackWeapons(operativeId,'melee');
    if(!weapons.length){showToast(`${playerName(operativeId)} has no melee weapon available to retaliate.`);onCancel();return;}
    if(weapons.length===1){onSelected(playerWeaponProfile(weapons[0],{operativeId,attackType:'melee',weaponIndex:0}));return;}
    showModal('Select Retaliation Weapon',`<p>${escapeHtml(playerName(operativeId))} must select a melee weapon for this Fight.</p><div class="field"><label for="retaliationWeapon">Melee weapon</label><select id="retaliationWeapon"><option value="">Select a weapon…</option>${weapons.map((weapon,index)=>`<option value="${index}">${escapeHtml(weapon.name)}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" id="cancelRetaliationWeapon">Back</button><button class="btn primary" id="confirmRetaliationWeapon" disabled>Roll Fight Dice</button></div>`);
    const select=$('#retaliationWeapon'),confirm=$('#confirmRetaliationWeapon');select.onchange=()=>{confirm.disabled=select.value==='';};
    $('#cancelRetaliationWeapon').onclick=onCancel;confirm.onclick=()=>{const index=Number(select.value);onSelected(playerWeaponProfile(weapons[index],{operativeId,attackType:'melee',weaponIndex:index}));};
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

  function playerActionTransactionIdentity(stage,attackType){
    const activation=activePlayerActivation(),pending=activation?.pendingAction;
    if(stage?.sequential&&activation&&pending){
      return {activationId:activation.activationId,actionId:`${stage.humanActionId||attackType}:${pending.actionSequence}`};
    }
    return {activationId:`${state.turningPoint}:${state.activationNumber}`,actionId:attackType};
  }

  function showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel,preferredTargetId=''){
    const targetSideLabel=isPvpMode()?'Necron':'NPO';
    const targets=sortedNposForDisplay(activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0));
    if(!targets.length){
      showToast(`No active ${targetSideLabel} is available as a target.`);
      if(stage.sequential)onCancel();
      else showPlayerActivation(normalizeImpossiblePlayerCombat(stage));
      return;
    }

    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    if(!weapons.length){
      showToast(`${playerName(stage.playerOperativeId)} has no ${attackType==='shoot'?'ranged':'melee'} weapon in its roster profile.`);
      if(stage.sequential)onCancel();
      else showPlayerActivation(stage);
      return;
    }

    const draft=stage[`${attackType}CombatDraft`];
    if(draft){
      showPlayerCombatResolution(stage,attackType,draft.targetId,draft.weaponIndex,onResolved,onCancel,draft.rolling
        ? {animate:false,committedAttackDice:draft.attackDice,committedDefenseDice:draft.saveDice}
        : {result:draft,animate:false});
      return;
    }

    const singleTarget=targets.length===1?targets[0]:null;
    const targetControl=singleTarget
      ? `<div class="field"><label>Target ${targetSideLabel}</label><div class="readonly-select">${escapeHtml(npoName(singleTarget))} · Wounds ${projectedNpoWounds(singleTarget.id,stage)}/${singleTarget.maxWounds} · Save ${singleTarget.save}+</div><input type="hidden" id="combatTarget" value="${singleTarget.id}"></div>`
      : `<div class="field"><label for="combatTarget">Target ${targetSideLabel}</label><select id="combatTarget"><option value="">Select a target ${targetSideLabel}...</option>${targets.map(n=>`<option value="${n.id}"${n.id===preferredTargetId?' selected':''}>${escapeHtml(npoName(n))} · Wounds ${projectedNpoWounds(n.id,stage)}/${n.maxWounds} · Save ${n.save}+</option>`).join('')}</select></div>`;
    const weaponFieldClass='field weapon-field';
    const weaponControl=weapons.length===1
      ? `<div class="${weaponFieldClass}"><label>Weapon</label><div class="readonly-select">${escapeHtml(weapons[0].name)}</div><input type="hidden" id="playerWeaponSelect" value="0"></div>`
      : `<div class="${weaponFieldClass}"><label>Weapon</label><select id="playerWeaponSelect"><option value="">Select a weapon...</option>${weapons.map((weapon,index)=>`<option value="${index}">${escapeHtml(weapon.name)}</option>`).join('')}</select></div>`;
    const meleeWeaponSummarySizers=attackType==='melee'
      ? weapons.map(weapon=>`<div class="melee-weapon-summary-sizer" aria-hidden="true">${weapon.attacks} dice · ${weapon.hit}+ · ${escapeHtml(weapon.damage)}</div>`).join('')
      : '';
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
      <div class="summary-box weapon-details${attackType==='melee'?' melee-weapon-summary melee-weapon-summary-pending':''}" id="playerWeaponSummary" aria-hidden="true"${attackType==='shoot'?' hidden':''}><div id="playerWeaponSummaryContent"></div>${meleeWeaponSummarySizers}</div>
      <div id="aggressiveDefenseFields"></div>
      <div class="wizard-actions"><button class="btn ghost" id="cancelPendingAttack">Cancel</button><button class="btn primary" id="openCombatResolution">Continue</button></div>`);

    const targetSelect=$('#combatTarget');
    const weaponSelect=$('#playerWeaponSelect');
    const renderChoices=()=>{
      const target=activeNpos().find(n=>n.id===targetSelect.value);
      const weapon=weaponSelect.value===''?null:weapons[Number(weaponSelect.value)];
      const weaponSummary=$('#playerWeaponSummary');
      const weaponIndex=weapon?weapons.indexOf(weapon):-1;
      const profile=weapon?playerWeaponProfile(weapon,{operativeId:stage.playerOperativeId,attackType,weaponIndex}):null;
      $('#playerWeaponSummaryContent').innerHTML=weapon
        ? `<div class="weapon-profile-stats">${weapon.attacks} dice · ${weapon.hit}+ · ${escapeHtml(weapon.damage)}</div>${weaponRulesHtml(profile,{semanticHeading:true})}`
        : '';
      if(attackType==='melee'){
        weaponSummary.classList.toggle('melee-weapon-summary-pending',!weapon);
      }else weaponSummary.hidden=!weapon;
      weaponSummary.setAttribute('aria-hidden',String(!weapon));
      $('#aggressiveDefenseFields').innerHTML=aggressiveDefenseFields(target);
      if(npoDefinition(target?.type)?.id==='skorpekh-destroyer'&&target.order==='Conceal')$('#aggressiveDefenseFields').insertAdjacentHTML('beforeend','<p class="muted"><strong>Hulking:</strong> while Concealed, this Skorpekh cannot use Light terrain to prevent it from being selected as a target.</p>');
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
      const guardianProtocolCheck=async()=>{
        if(attackType!=='shoot'||npoDefinition(target.type)?.id!=='royal-warden'||!activeNpos().some(item=>npoDefinition(item.type)?.id==='lychguard'&&item.order==='Engage'))return false;
        const identity=playerActionTransactionIdentity(stage,attackType),decision=stage3Trigger(`guardian-protocol:${identity.activationId}:${identity.actionId}:${target.id}`,{activationId:identity.activationId,actionId:identity.actionId,targetId:target.id,withinControlRange:null});
        if(decision.withinControlRange===null){decision.withinControlRange=await askYesNoRuleQuestion('Guardian Protocol',STAGE3_RULE_TEXT.guardianRange);decision.status='complete';save();}
        const protectedTarget=decision.withinControlRange;
        if(!protectedTarget)return false;
        showModal('Guardian Protocol',`<p>${STAGE3_RULE_TEXT.guardianPrevented}</p><div class="wizard-actions"><button class="btn primary" id="returnToShootTarget">Select Another Target</button></div>`);
        $('#returnToShootTarget').onclick=back;return true;
      };
      const ruleId=weaponHasRule(profile,'blast')?'blast':weaponHasRule(profile,'torrent')?'torrent':null;
      const actionIdentity=playerActionTransactionIdentity(stage,attackType);
      const resolutionKey=`player:${actionIdentity.activationId}:${actionIdentity.actionId}:${stage.playerOperativeId}:${target.id}:${profile.weaponId}`;
      const selectSecondaryTargets=()=>{
        if(!ruleId){proceed();return;}
        const playerTargets=(state.playerRoster||[]).map(id=>({id,targetSide:'player',label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id),wounds:playerCurrentWounds(id),inPlay:state.playerOperativeStates?.[id]?.inPlay!==false}));
        const npoTargets=activeNpos().map(npo=>({id:npo.id,targetSide:'npo',label:npoName(npo),wounds:npo.wounds,inPlay:npo.battlefieldState==='deployed'}));
        showSecondaryTargetCheck({ruleId,distance:weaponRuleValue(profile,ruleId),attackerSide:'player',attackerId:stage.playerOperativeId,activationId:actionIdentity.activationId,actionId:actionIdentity.actionId,primaryTargetId:target.id,targets:ruleId==='blast'?[...playerTargets,...npoTargets]:npoTargets,weaponId:profile.weaponId,weaponName:profile.weaponName,profileKey:profile.profileId,profileName:profile.profileName,weaponRules:profile.rules,onContinue:proceed,onBack:back});return;
      };
      void guardianProtocolCheck().then(blocked=>{if(blocked)return;if(weaponHasRule(profile,'seek-light')&&target.order==='Conceal'){showSeekLightCheck({target,resolutionKey,onContinue:selectSecondaryTargets,onBack:back});return;}selectSecondaryTargets();});
    };
    renderChoices();
    const singleProfile=weapons.length===1?playerWeaponProfile(weapons[0],{operativeId:stage.playerOperativeId,attackType,weaponIndex:0}):null;
    const requiresStage3TargetCheck=attackType==='shoot'&&(npoDefinition(singleTarget?.type)?.id==='royal-warden'&&activeNpos().some(item=>npoDefinition(item.type)?.id==='lychguard'&&item.order==='Engage')||npoDefinition(singleTarget?.type)?.id==='skorpekh-destroyer'&&singleTarget.order==='Conceal');
    const requiresTabletopCheck=requiresStage3TargetCheck||singleProfile&&['seek-light','blast','torrent'].some(ruleId=>weaponHasRule(singleProfile,ruleId));
    if(!isPvpMode()&&singleTarget&&weapons.length===1&&singleTarget.type!=='Canoptek Macrocyte Warrior'&&!darkDistance&&!requiresTabletopCheck)showPlayerCombatResolution(stage,attackType,singleTarget.id,0,onResolved,onCancel);
  }

  function showPlayerCombatResolution(stage,attackType,targetId,weaponIndex,onResolved,onCancel,{result=null,animate=true,moreThanEight=false,deferRoll=false,committedAttackDice=null,committedDefenseDice=null}={}){
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
      showMultiTargetProfileRecovery('player',()=>{state.weaponRuleResolution=null;state.combatState={side:'player',stage:{...stage,[`${attackType}CombatDraft`]:null}};save();if(stage.sequential)cancelCurrentHumanPlayerAction();else showPlayerActivation(stage);});
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
    if(attackType==='melee'){
      const retaliationProfile=canonicalAttackProfile(npoAttackProfiles(target,'melee')[0]);
      if(!retaliationProfile?.dice){showToast(`${targetName} has no melee weapon available to retaliate.`);showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);return;}
      const actionIdentity=playerActionTransactionIdentity(stage,attackType);
      const transactionId=`fight:${actionIdentity.activationId}:${actionIdentity.actionId}:player:${stage.playerOperativeId}:npo:${target.id}:${profile.weaponId}:${retaliationProfile.weaponId}`;
      const attacker=fightParticipantState({side:'player',id:stage.playerOperativeId,label:playerName(stage.playerOperativeId),profile,wounds:playerCurrentWounds(stage.playerOperativeId),maxWounds:playerDefinition(stage.playerOperativeId)?.wounds});
      const defender=fightParticipantState({side:'npo',id:target.id,label:targetName,profile:retaliationProfile,wounds:target.wounds,maxWounds:target.maxWounds});
      void startSharedFight({id:transactionId,attacker,defender,onComplete:onResolved});
      return;
    }
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
      if(sequence){if(stage.sequential)cancelCurrentHumanPlayerAction();else showPlayerActivation(stage);}
      else showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel);
    };
    if(committedAttackDice)screen.cancelButton.disabled=true;

    if(result){
      displayPendingPlayerCombat(stage,attackType,result,onResolved,onCancel,false);
      return;
    }

    const actionIdentity=playerActionTransactionIdentity(stage,attackType);
    const transactionId=`attack:${actionIdentity.activationId}:${actionIdentity.actionId}:${stage.playerOperativeId}:${targetId}`;
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
      runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,defenderWounds:targetSide==='player'?playerCurrentWounds(target.id):projectedNpoWounds(target.id,stage),attackerSide:'player',attackType,attackerLabel:playerName(stage.playerOperativeId),defenderLabel:targetName,requestKeyBase:`combat:${transactionId}`,
        rolledAttackDice:committedAttackDice,rolledDefenseDice:committedDefenseDice,
        onAttackComplete:attackDice=>{
          diceDraft.attackDice=attackDice.map(die=>({...die}));
          stage[`${attackType}CombatDraft`]={rolling:true,attackType,targetId,targetName,weaponIndex,profile,attackDice:diceDraft.attackDice};
          state.combatState={side:'player',stage:{...stage}};
          screen.cancelButton.disabled=true;
          save();
        },onComplete:(attackDice,defenseDice)=>{
        const immediateEffects=attackDice.immediateEffects||{};
        diceDraft.attackDice=attackDice;
        diceDraft.defenseDice=defenseDice;
        Object.assign(diceDraft,immediateEffects);
        stage[`${attackType}CombatDraft`]={rolling:true,attackType,targetId,targetName,weaponIndex,profile,
          attackDice:attackDice.map(die=>({...die})),saveDice:defenseDice.map(die=>({...die})),...immediateEffects};
        state.combatState={side:'player',stage:{...stage}};
        save();
        void previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,{targetId,weaponIndex,targetSide}).catch(error=>{rollStarted=false;console.error('[Combat] Combat-triggered dice request failed. No combat result was committed.',error);});
      },onError:()=>{rollStarted=false;}});
    };
    if(!deferRoll)startRoll();
    return {...screen,startRoll};
  }

  async function previewPendingPlayerAttack(stage,attackType,onResolved,onCancel,diceDraft,selection={}){
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
    const resolution=diceDraft.devastatingIncapacitated?{normal:0,critical:0,damage:0}:resolveRetainedCombat(diceDraft.attackDice,diceDraft.defenseDice,profile);
    const devastatingDamage=Number(diceDraft.devastatingDamage??devastatingDamageForAttack(diceDraft.attackDice,profile));
    const result={
      ...recordedCombat({attackerName:playerName(stage.playerOperativeId),defenderName:targetName,attackType,attackerSide:'player',defenderSide:targetSide,profile:{...profile,rules:weapon.rules||[]},before,
        normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage+devastatingDamage}),
      targetId:n.id,targetName,side:targetSide,weaponName:weapon.name,weaponIndex,
      severeApplied:diceDraft.attackDice.some(die=>die.severeConverted),devastatingDamage,devastatingApplied:true,devastatingIncapacitated:Boolean(diceDraft.devastatingIncapacitated)
    };
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
    const savedCountertemporal=transaction.countertemporalRolls||[];
    const qualifyingIndexes=packets.map((packet,index)=>Number(packet.damage)>=3&&!Number.isInteger(savedCountertemporal[index])?index:-1).filter(index=>index>=0);
    const countertemporalRequestKey=diceRequestKey('combat',result.transactionId,'countertemporal-shifting',qualifyingIndexes.join('-'));
    const countertemporalValues=qualifyingIndexes.length&&tombWorldEventActive('countertemporal-shifting')
      ? await requestDiceResults({count:qualifyingIndexes.length,sides:6,title:'COUNTERTEMPORAL SHIFTING',rollerLabel:targetName,requestKey:countertemporalRequestKey,resumeKind:'combat',resumeData:{transactionId:result.transactionId,packetIndexes:qualifyingIndexes},
        instruction:`Roll ${qualifyingIndexes.length}D6 for Countertemporal Shifting and enter each result.`})
      : [];
    const suppliedRolls=[...savedCountertemporal];
    qualifyingIndexes.forEach((packetIndex,index)=>{suppliedRolls[packetIndex]=countertemporalValues[index];});
    let countertemporalIndex=0;
    result.damagePackets=EventEffects.resolveCountertemporalPackets(state,packets,{turningPoint:state.turningPoint,attackerSide:'player',defenderSide:'npo',attackType,savedRolls:suppliedRolls,rollD6:()=>countertemporalValues[countertemporalIndex++]});
    transaction.countertemporalRolls=result.damagePackets.map(packet=>Number.isInteger(packet.countertemporalRoll)?packet.countertemporalRoll:null);
    if(countertemporalValues.length){save();acknowledgeDiceRequest(countertemporalRequestKey);}
    result.eventMessages=[...(diceDraft.rerolls.messages||[])];
    if(result.damagePackets.some(packet=>Number.isInteger(packet.countertemporalRoll)))result.eventMessages.push('Countertemporal Shifting: Resolved one D6 for each qualifying attack die.');
    result.damage=result.damagePackets.reduce((total,packet)=>total+packet.finalDamage,0);
    result.after=Math.max(0,result.before-result.damage);
    result.aggressiveDefenseDamage=0;
    const resolvedResult=await requestDimensionalBanishment(result,playerName(stage.playerOperativeId));
    const stun=applyStunForAttack({profile,attackDice:diceDraft.attackDice,sourceAttackId:diceDraft.transactionId,targetId:n.id,targetName,targetSide});
    if(stun.message)resolvedResult.eventMessages.push(stun.message);
    stage[`${attackType}CombatDraft`]=resolvedResult;
    state.combatState={side:'player',stage:{...stage}};
    save();
    acknowledgeCurrentDiceRequest();
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
    const behavior=npoBehavior(n);
    if(behavior?.focus==='warden')return activeNpos().some(item=>npoDefinition(item.type)?.id==='royal-warden')?'warden':'fight';
    if(behavior?.focus)return behavior.focus;
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
    const shootCanFollow=remainingAp>=2&&!(activation?.completedActionIds||[]).includes('shoot');
    const fightCanFollow=remainingAp>=2&&!(activation?.completedActionIds||[]).includes('fight');
    if(id==='reposition'){
      const distance=formatMovementDistance(npoRepositionDistance(n));
      if(focus==='shoot'&&shootCanFollow&&!declined.has('reposition-enable-shoot'))return {id:'reposition-enable-shoot',purpose:'enable-shoot',followUpActionId:'shoot',guaranteesFollowUp:true,question:distance?`Can this NPO Reposition up to ${distance} and finish where it can Shoot?`:'Can this NPO Reposition to a position where it can Shoot?',help:'Select Yes only if it can finish the Reposition with a Player operative it can Shoot.'};
      if(focus==='shoot')return {id:'reposition-general-position',purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false,question:distance?`Can this NPO Reposition up to ${distance} to improve its position for the next activation or the mission?`:'Can this NPO Reposition to improve its position for the next activation or the mission?',help:'Select Yes if it can move closer to a future shooting position, gain useful cover, or help complete or defend the mission.'};
      if(focus==='fight'&&fightCanFollow)return {id:'reposition-enable-fight',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:false,question:distance?`Can this NPO Reposition up to ${distance} closer to its target?`:'Can this NPO Reposition closer to its target?',help:'Select Yes if it can move closer to the nearest Player operative, using cover when possible.'};
      if(focus==='fight')return {question:distance?`Can this NPO Reposition up to ${distance} closer to its target?`:'Can this NPO Reposition closer to its target?',help:'Select Yes if it can move closer to the nearest Player operative, using cover when possible.'};
      if(focus==='warden')return {id:'reposition-toward-royal-warden',purpose:'toward-royal-warden',question:STAGE3_RULE_TEXT.lychguardMovement,help:'Move toward the dynasty leader, using cover when possible. If none is in the killzone, move toward the closest Player operative.'};
      if(focus==='support')return {question:distance?`Can this NPO Reposition up to ${distance} to use a support action or help the mission?`:'Can this NPO Reposition to use a support action or help the mission?',help:'Select Yes if moving would help it use a higher-priority action or improve its mission position.'};
      return {question:distance?`Can this NPO Reposition up to ${distance} to help complete or defend the mission?`:'Can this NPO Reposition to help complete or defend the mission?',help:'Select Yes only if it can reach a clearly better mission position.'};
    }
    if(activation?.movementIntent?.movementActionCommitted&&activation.movementIntent.actionId==='dash')return {...activation.movementIntent,question:'Can this NPO use Dash to complete its Reposition movement intent?',help:npoMovementInstruction(n,action)};
    if(remainingAp===1&&npoBehavior(n)?.orderRule){
      if(focus==='warden')return {id:'dash-toward-royal-warden',purpose:'toward-royal-warden',question:STAGE3_RULE_TEXT.lychguardMovement,help:'Move toward the dynasty leader, using cover when possible. If none is in the killzone, move toward the closest Player operative.'};
      if(focus==='fight')return {id:'dash-toward-enemy',purpose:'enable-fight',question:'Can a 3-inch Dash move this NPO closer to its target?',help:'Select Yes if the Dash moves it closer to the nearest Player operative, using cover when possible.'};
      if(focus==='shoot')return {id:'dash-shooting-position',purpose:'general-position',question:'Can a 3-inch Dash improve this NPO’s shooting or mission position?',help:'Move toward a valid unobscured Shoot target if possible; otherwise improve its mission position.'};
    }
    if(remainingAp===1)return {id:'dash-final-position',purpose:'final-position',followUpActionId:null,guaranteesFollowUp:false,endsActivation:true,question:'Can this NPO use its last AP to Dash to a better position?',help:'Select Yes if the Dash improves cover, mission position, or its setup for the next Turning Point. The activation will end after the Dash.'};
    if(focus==='shoot'&&shootCanFollow&&!declined.has('dash-enable-shoot'))return {id:'dash-enable-shoot',purpose:'enable-shoot',followUpActionId:'shoot',guaranteesFollowUp:true,question:'Can a 3-inch Dash move this NPO to a position where it can Shoot?',help:'Select Yes only if it can finish the Dash with a Player operative it can Shoot.'};
    if(focus==='shoot')return {id:'dash-general-position',purpose:'general-position',followUpActionId:null,guaranteesFollowUp:false,question:'Can a 3-inch Dash improve this NPO’s position?',help:'Select Yes if it improves cover, moves it toward the mission, or sets up a better position for a later activation.'};
    if(focus==='fight'&&fightCanFollow)return {id:'dash-enable-fight',purpose:'enable-fight',followUpActionId:'fight',guaranteesFollowUp:false,question:'Can a 3-inch Dash move this NPO closer to its target?',help:'Select Yes if the Dash moves it closer to the nearest Player operative, using cover when possible.'};
    if(focus==='fight')return {question:'Can a 3-inch Dash move this NPO closer to its target?',help:'Select Yes if the Dash moves it closer to the nearest Player operative, using cover when possible.'};
    if(focus==='warden')return {id:'dash-toward-royal-warden',purpose:'toward-royal-warden',question:STAGE3_RULE_TEXT.lychguardMovement,help:'Move toward the dynasty leader, using cover when possible. If none is in the killzone, move toward the closest Player operative.'};
    if(focus==='support')return {question:'Can a 3-inch Dash help this NPO use a support action?',help:'Select Yes if the Dash helps it reach an ally, enemy, or mission position needed for a higher-priority action.'};
    return {question:'Can a 3-inch Dash put this NPO in a better position?',help:'Select Yes if the Dash moves it toward a clear shot or a better mission position.'};
  }
  function npoMovementInstruction(n,action){
    const name=npoActionId(action)==='dash'?'Dash':'Reposition';
    const distance=name==='Dash'?'3 inches':formatMovementDistance(npoRepositionDistance(n)),focus=npoMovementFocus(n,action);
    if(name==='Reposition'&&state.lastActivation?.movementIntent?.purpose==='enable-shoot')return distance?`Move this NPO up to ${distance} and finish where it can Shoot.`:'Move this NPO and finish where it can Shoot.';
    if(name==='Reposition'&&state.lastActivation?.movementIntent?.purpose==='general-position')return distance?`Move this NPO up to ${distance} to improve its cover, mission position, or setup for a later activation.`:'Move this NPO to improve its cover, mission position, or setup for a later activation.';
    if(focus==='warden')return distance?`${name==='Dash'?'Dash':'Move'} this bodyguard up to ${distance} toward the dynasty leader, using cover when possible. If none is present, move toward the closest Player operative.`:'Move this bodyguard toward the dynasty leader, or the closest Player operative if none is present.';
    if(focus==='fight')return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward the selected Player operative, using cover when possible.`:`Move this NPO toward the selected Player operative, using cover when possible.`;
    if(focus==='shoot')return name==='Dash'?`Dash this NPO up to 3 inches toward a clear shot or a better mission position.`:distance?`Move this NPO up to ${distance} to get a clear shot. If that is not possible, move it to help the mission.`:'Move this NPO to get a clear shot. If that is not possible, move it to help the mission.';
    if(focus==='support')return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward an ally, enemy, or mission position needed for its next support action.`:`Move this NPO toward an ally, enemy, or mission position needed for its next support action.`;
    return distance?`${name==='Dash'?'Dash':'Move'} this NPO up to ${distance} toward the mission objective or a position that helps defend it.`:`Move this NPO toward the mission objective or a position that helps defend it.`;
  }
  function npoActionCost(n,actionId){
    const profileAction=(npoDefinition(n?.type)?.actions||[]).find(action=>action.id===actionId);
    if(profileAction&&Number.isFinite(Number(profileAction.ap)))return Math.max(0,Number(profileAction.ap));
    if(actionId==='operate-hatch'&&npoBehavior(n)?.orderRule&&npoBehavior(n)?.operatesHatches)return 1;
    return Object.prototype.hasOwnProperty.call(NPO_CORE_ACTION_COSTS,actionId)?NPO_CORE_ACTION_COSTS[actionId]:null;
  }
  function npoActionChangesContext(actionId){
    return ['reposition','dash','charge','fall-back'].includes(actionId);
  }
  function conciseNpoActionName(action){
    if(NPO_CORE_ACTION_COSTS[action.id]===undefined)return action.name;
    const fight=action.id==='fight'?action.attackSummary||action.attackSummaries?.at(-1):null;
    if(fight)return `Fight · ${fight.targetName} · Dealt ${Number(fight.damageDealt??fight.damage??0)} · Suffered ${Number(fight.damageSuffered??0)}`;
    return action.id==='fall-back'?'Fall Back':action.id[0].toUpperCase()+action.id.slice(1);
  }
  function legalNpoActions(n,context={}){
    return filterLegalNpoActions(n,npoBehavior(n)?.actions||[],context);
  }
  function supportedHumanNpoActions(n){
    const definition=npoDefinition(n?.type);
    if(!definition)return [];
    return [
      'Reposition','Dash','Charge','Fall Back',
      ...(definition.rangedWeapons||[]).length?['Shoot']:[],
      ...(definition.meleeWeapons||[]).length?['Fight']:[],
      ...(definition.behavior?.orderRule&&definition.behavior?.operatesHatches?['Operate Hatch']:[]),
      ...(definition.actions||[]).map(action=>action.name)
    ];
  }
  function eligibleNpoSpecialActionTargets(n,action){
    if(action.target?.side==='enemy'){
      const ids=isPvpMode()?inPlayLivingPlayerOperativeIds():remainingPlayerOperatives();
      return ids.map(id=>({id,name:playerName(id),side:'enemy'})).filter(target=>!isPvpMode()||action.id!=='cranial-overload'
        ||!state.npoRuleState.aplModifiers.some(item=>item.sourceId===n.id&&item.targetId===target.id&&item.ruleId==='cranial-overload'));
    }
    return sortedNposForDisplay(activeNpos().filter(target=>(action.target?.excludeSelf!==true||target.id!==n.id)
      &&(!action.target?.keywordsAll||action.target.keywordsAll.every(keyword=>npoDefinition(target.type)?.keywords.includes(keyword)))
      &&(action.id!=='nanoscarab-beam'||target.wounds<target.maxWounds&&!state.npoRuleState.reanimatedTargetIds.includes(target.id))
      &&(!isPvpMode()||action.id!=='overcharge'||!state.npoRuleState.aplModifiers.some(item=>item.sourceId===n.id&&item.targetId===target.id&&item.ruleId==='overcharge'))
      &&(!isPvpMode()||action.id!=='molecular-breach'||!state.npoRuleState.pendingMovementEffects.some(effect=>effect.targetId===target.id&&effect.ruleId==='molecular-breach'))));
  }
  function legalHumanNpoActions(n,context={}){
    return filterLegalNpoActions(n,supportedHumanNpoActions(n),context).filter(actionName=>{
      const action=npoSpecialAction(n,actionName);
      if(!action||action.id==='geomantic-disturbance')return true;
      return eligibleNpoSpecialActionTargets(n,action).length>0;
    });
  }
  function filterLegalNpoActions(n,actionCatalog,context={}){
    const definition=npoDefinition(n?.type);
    if(!definition||n.wounds<=0||!n.ready)return [];
    const activation=state.lastActivation?.npoId===n.id?state.lastActivation:null;
    const remainingAp=Number.isFinite(context.remainingAp)?context.remainingAp:Number(activation?.remainingAp??effectiveApl(n.id,definition.apl));
    const completed=new Set(context.completedActionIds||activation?.completedActionIds||[]);
    return actionCatalog.filter(actionName=>{
      const id=npoActionId(actionName),profileAction=(definition.actions||[]).find(action=>action.id===id),cost=npoActionCost(n,id);
      if(cost===null||cost>remainingAp||completed.has(id))return false;
      if(['shoot','fight','charge'].includes(id)&&!inPlayLivingPlayerOperativeIds().length)return false;
      if(id==='shoot'&&!(definition.rangedWeapons||[]).length)return false;
      if(id==='fight'&&!(definition.meleeWeapons||[]).length)return false;
      if(id==='charge'&&['reposition','dash','fall-back'].some(done=>completed.has(done)))return false;
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
      'flayed-one':['Fight','Charge','Reposition','Dash'],
      'skorpekh-destroyer':['Fight','Charge','Reposition','Dash'],
      'hexmark-destroyer':['Fall Back','Shoot','Reposition','Dash','Fight'],
      'royal-warden':['Fall Back','Shoot','Reposition','Dash','Fight'],
      'lychguard':['Fight','Charge','Reposition','Dash'],
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

  function renderCompletedNpoQuestions(history){
    return history.map(item=>`<div class="npo-question-complete npo-question-history"><span>${escapeHtml(item.question||item.action)}</span><strong>${item.type==='selected'?'Selected':item.answer?'Yes':'No'}</strong></div>`).join('');
  }

  function renderActiveNpoQuestion(q){
    return `<section class="npo-question-active npo-question-card--active npo-active-question" aria-live="polite" aria-atomic="true" aria-labelledby="activeNpoQuestion" aria-describedby="activeNpoQuestionHelp">
      <h3 id="activeNpoQuestion">${escapeHtml(q.title)}</h3><p id="activeNpoQuestionHelp">${escapeHtml(q.help)}</p>
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

  function humanNpoDecision(n,actionName){
    const id=npoActionId(actionName),distance=id==='dash'?3:id==='charge'?npoDefinition(n.type).move+2:npoDefinition(n.type).move;
    const movementInstructions={
      reposition:`Move ${npoName(n)} up to ${distance} inches following the normal Reposition rules.`,
      dash:`Move ${npoName(n)} up to 3 inches following the normal Dash rules.`,
      charge:`Charge with ${npoName(n)} following the normal Charge rules, then confirm the move was completed legally.`,
      'fall-back':`Fall Back with ${npoName(n)} following the normal tabletop requirements, finishing outside enemy control range.`
    };
    return {action:actionName,target:[],stance:'Engage',threat:['shoot','fight'].includes(id)?1:0,reason:movementInstructions[id]||`Resolve ${actionName}.`,path:[actionName]};
  }

  function renderHumanNpoActionPicker(n){
    const activation=state.lastActivation,legal=new Set(legalHumanNpoActions(n,activation.currentContext||{}).map(npoActionId));
    const completed=new Set(activation.completedActionIds||[]),definition=npoDefinition(n.type);
    const catalog=supportedHumanNpoActions(n).map(name=>{
      const id=npoActionId(name),cost=npoActionCost(n,id),available=legal.has(id),used=completed.has(id);
      const reason=used?'Used':available?'Available':cost>activation.remainingAp?`Needs ${cost} AP`:'Unavailable';
      return {name,id,cost,group:['reposition','dash','charge','fall-back'].includes(id)?'movement':['shoot','fight'].includes(id)?'combat':'special',state:{status:used?'Used':available?'Available':cost>activation.remainingAp?'Insufficient AP':'Unavailable',disabled:!available,reason}};
    });
    const modifiers=(state.npoRuleState.aplModifiers||[]).filter(item=>item.targetId===n.id).map(item=>`${item.amount>0?'+':''}${item.amount} AP (${titleCaseRuleId(item.ruleId)})`);
    if((state.npoRuleState.pendingMovementEffects||[]).some(item=>item.targetId===n.id&&item.ruleId==='molecular-breach'))modifiers.push('Next movement uses Molecular Breach');
    if(n.wounds<n.maxWounds&&activeNpos().some(item=>npoDefinition(item.type)?.id==='royal-warden'))modifiers.push(STAGE3_RULE_TEXT.engrammatic);
    renderHumanActivationShell({title:'NECRON ACTIVATION',name:npoName(n),wounds:n.wounds,maxWounds:n.maxWounds,
      baseApl:definition.apl,effectiveAp:activation.effectiveApl,remainingAp:activation.remainingAp,startingAp:activation.startingAp,
      order:n.order,loadout:definition.loadoutOptions?.find(option=>option.id===n.weaponId)?.name||npoWeapon(definition,n.weaponId)?.name||'',effects:modifiers,
      completedActions:(activation.resolvedActions||[]).map(action=>({...action,summary:conciseNpoActionName(action)})),actions:catalog,
      onAction:actionId=>selectHumanNpoAction(n,actionId),onEnd:()=>confirmEndHumanNpoActivation(n)});
    renderOperativeStatusPanel();
  }

  function selectHumanNpoAction(n,actionId){
    const actionName=supportedHumanNpoActions(n).find(name=>npoActionId(name)===actionId);
    if(!actionName||!legalHumanNpoActions(n,state.lastActivation.currentContext||{}).some(name=>npoActionId(name)===actionId)){showToast('That action is no longer legal.');renderHumanNpoActionPicker(n);return;}
    const decision=humanNpoDecision(n,actionName),cost=npoActionCost(n,actionId);
    state.npoAttackTargetId=null;
    state.lastActivation={...state.lastActivation,...decision,answers:{action:actionName},questionHistory:[],pendingFollowUpAction:null,movementIntent:null,pendingAction:{id:actionId,name:actionName,apCost:cost,decisionPass:state.lastActivation.decisionPass},committed:false};
    save();resolveNpoAction(n,state.lastActivation.pendingAction);
  }

  function confirmEndHumanNpoActivation(n){
    const activation=state.lastActivation,remaining=activation.remainingAp;
    if(remaining<=0){completeNpoActivation();return;}
    const message=(activation.resolvedActions||[]).length
      ?`${remaining} AP remain${remaining===1?'s':''}.`
      :'This operative has not performed any actions.';
    showModal('End Activation?',`<p>${escapeHtml(message)}</p><div class="wizard-actions"><button class="btn ghost" id="continueHumanNpoActivation">Continue Activation</button><button class="btn primary" id="confirmEndHumanNpoActivation">End Activation</button></div>`);
    $('#continueHumanNpoActivation').onclick=()=>renderHumanNpoActionPicker(n);
    $('#confirmEndHumanNpoActivation').onclick=()=>completeNpoActivation();
  }


  function renderNpoActivationHeader(n){
    const definition=npoDefinition(n.type),modifiers=(state.npoRuleState.aplModifiers||[]).filter(item=>item.targetId===n.id);
    const pendingBreach=(state.npoRuleState.pendingMovementEffects||[]).some(item=>item.targetId===n.id&&item.ruleId==='molecular-breach');
    const loadout=definition.loadoutOptions?.find(option=>option.id===n.weaponId)?.name||npoWeapon(definition,n.weaponId)?.name;
    const engrammatic=n.wounds<n.maxWounds&&activeNpos().some(item=>npoDefinition(item.type)?.id==='royal-warden')?`<p class="muted">${escapeHtml(STAGE3_RULE_TEXT.engrammatic)}</p>`:'';
    return `<h2 id="activeNpoQuestionHeading">${escapeHtml(opponentSingularLabel())} Activation: ${escapeHtml(npoName(n))}</h2>${engrammatic}<div class="activation-profile-strip" role="status" aria-live="polite" aria-label="Activation profile"><span>Wounds: ${n.wounds}/${n.maxWounds}</span><span>AP remaining: ${state.lastActivation.remainingAp}/${state.lastActivation.startingAp}</span>${loadout?`<span>${escapeHtml(loadout)}</span>`:''}${modifiers.map(item=>`<span>${item.amount>0?'+':''}${item.amount} AP this activation (${escapeHtml(titleCaseRuleId(item.ruleId))})</span>`).join('')}${pendingBreach?'<span>Next movement uses Molecular Breach</span>':''}</div>${renderNpoActionProgress()}`;
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
        }else if(q.actionId==='charge'&&state.lastActivation.remainingAp>=2&&!(state.lastActivation.completedActionIds||[]).includes('fight')){
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
    const rule=npoBehavior(n)?.orderRule;
    const stance=rule==='engage-if-fight-or-charge'?(['Fight','Charge'].includes(action.split(' ')[0])?'Engage':'Conceal')
      :rule==='engage-if-shoot-or-fight'?(['Shoot','Fight'].includes(action.split(' ')[0])?'Engage':'Conceal')
      :rule==='engage-if-fight-charge-or-warden'?(['Fight','Charge'].includes(action.split(' ')[0])||state.lastActivation?.movementIntent?.purpose==='toward-royal-warden'&&activeNpos().some(item=>npoDefinition(item.type)?.id==='royal-warden'&&item.order==='Engage')?'Engage':'Conceal'):'Engage';
    if(rule)n.order=stance;
    return {action,target,stance,threat:attack?1:0,reason,path:[action]};
  }

  function continueNpoActivation(){
    if(isPvpMode()){
      continueHumanNecronActivation();
      return;
    }
    continueSoloNpoActivation();
  }

  function continueHumanNecronActivation(){
    const activation=state.lastActivation,n=state.roster.find(item=>item.id===activation?.npoId);
    if(!activation||activation.committed)return;
    if(!n){
      state.activeNpoId=null;state.lastActivation=null;save();closeModal();render();return;
    }
    if(n.wounds<=0){completeNpoActivation();return;}
    if(n.battlefieldState!=='deployed'||n.dormant||!n.ready){
      state.activeNpoId=null;state.lastActivation=null;save();closeModal();render();return;
    }
    if(activation.awaitingActionResult){renderNpoActionResult(n,activation.awaitingActionResult,Boolean(activation.awaitingActionResult.endsActivation));return;}
    if(activation.pendingAction){resolveNpoAction(n,activation.pendingAction);return;}
    if(activation.remainingAp<=0){completeNpoActivation();return;}
    renderHumanNpoActionPicker(n);
  }

  function continueSoloNpoActivation(){
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
    const continuedMovementIntent=changesPosition&&actionId==='reposition'&&activation.remainingAp>0&&npoBehavior(n)?.orderRule&&!activation.pendingFollowUpAction&&activation.movementIntent
      ? {...activation.movementIntent,id:`dash-complete-${activation.movementIntent.id}`,actionId:'dash',completesMovementIntentId:activation.movementIntent.id,movementActionCommitted:true}
      : null;
    if(changesPosition)activation.currentContext={inEnemyControlRange:null,hasValidShootTarget:null,hasValidFightTarget:null};
    if(changesPosition&&activation.pendingFollowUpAction?.movementActionId===actionId)activation.pendingFollowUpAction={...activation.pendingFollowUpAction,movementCommitted:true,decisionPass:activation.decisionPass};
    else if(changesPosition)activation.movementIntent=continuedMovementIntent;
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
    return (paragraphs[action.id]||[action.description]).map(text=>`<p>${escapeHtml(isPvpMode()?text.replaceAll('Player operative',`${playerSideLabel()} operative`).replaceAll('NPO','Necron'):text)}</p>`).join('');
  }
  function resolveNpoSpecialAction(n,decision,answers,questionHistory){
    const action=npoSpecialAction(n,decision.action);
    if(!action){completeNpoActivation();return;}
    const friendlies=action.target?.side==='enemy'?[]:eligibleNpoSpecialActionTargets(n,action);
    const friendlyOptions=friendlies.map(target=>`<option value="${escapeHtml(target.id)}">${escapeHtml(npoName(target))}</option>`).join('');
    const enemyOptions=(action.target?.side==='enemy'?eligibleNpoSpecialActionTargets(n,action):[]).map(target=>`<option value="${escapeHtml(target.id)}">${escapeHtml(playerTargetLabel(target.id))}</option>`).join('');
    const targetOptions=action.target?.side==='enemy'?enemyOptions:friendlyOptions;
    const targetLabel=action.target?.side==='enemy'?(isPvpMode()?`${playerSideLabel()} operative`:'Player operative'):(isPvpMode()?`Friendly ${opponentSingularLabel()}`:'Friendly NPO');
    if(action.id==='geomantic-disturbance'){
      const affected=[...sortedNposForDisplay(activeNpos()),...inPlayLivingPlayerOperativeIds().map(id=>({id:`player:${id}`,label:playerTargetLabel(id),ariaLabel:playerTargetAriaLabel(id)}))];
      showModal(action.name,`<p>Choose a visible terrain point within 8 inches, then select every operative within 2 inches of it.</p><div class="checklist">${affected.map(target=>`<label class="check-row"><input type="checkbox" data-disturbance-target="${escapeHtml(target.id)}"${target.ariaLabel?` aria-label="${escapeHtml(target.ariaLabel)}"`:''}><span>${escapeHtml(target.label||npoName(target))}</span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="cancelSpecialAction">Cancel</button><button class="btn primary" id="confirmSpecialAction">Roll Damage</button></div>`);
      $('#cancelSpecialAction').onclick=()=>{if(isPvpMode()){state.lastActivation.pendingAction=null;save();renderHumanNpoActionPicker(n);}else resolveNpoAction(n,state.lastActivation.pendingAction);};
      $('#confirmSpecialAction').onclick=async()=>{
        const button=$('#confirmSpecialAction');
        if(!canCommitNpoAction(action.id,npoActionCost(n,action.id)))return;
        button.disabled=true;
        const selected=$$('[data-disturbance-target]:checked').map(input=>input.dataset.disturbanceTarget);
        if(state.lastActivation?.pendingAction){state.lastActivation.pendingAction.selectedTargets=[...selected];save();}
        const restoredResolution=state.lastActivation?.pendingAction?.resolvedResult;
        if(restoredResolution){finishNpoSpecialAction(n,action,restoredResolution,decision,answers,questionHistory);return;}
        const targets=selected.map(id=>id.startsWith('player:')?livePlayerOperative(id.slice(7)):state.roster.find(item=>item.id===id)).filter(Boolean);
        let committedRolls;
        try{
          const pendingAction=state.lastActivation?.pendingAction;
          const savedRolls=pendingAction?.diceResults&&typeof pendingAction.diceResults==='object'?pendingAction.diceResults:{};
          committedRolls=[];
          for(const target of targets){
            const targetId=selected[targets.indexOf(target)],label=targetId.startsWith('player:')?playerName(target.id):npoName(target);
            let dice=savedRolls[targetId];
            if(!Array.isArray(dice)||dice.length!==2||dice.some(value=>!Number.isInteger(value)||value<1||value>6)){
              const requestKey=diceRequestKey('npo-activation',n.id,'geomantic-disturbance',targetId);
              if(state.pendingDice?.status==='committed'&&state.pendingDice.requestKey!==requestKey)acknowledgeCurrentDiceRequest();
              dice=await requestDiceResults({count:2,sides:6,title:'GEOMANTIC DISTURBANCE',instruction:'Roll 2D6 for this operative and enter both results.',rollerLabel:label,requestKey,resumeKind:'npo-special-action',resumeData:{npoId:n.id,actionId:action.id,targetId}});
              savedRolls[targetId]=dice;
              if(pendingAction)pendingAction.diceResults=savedRolls;
              save();
            }
            committedRolls.push(dice);
          }
        }catch(error){
          console.error('[Geomantic Disturbance Dice]',error);
          button.disabled=false;
          return;
        }
        const results=resolveGeomanticDisturbance(targets,operative=>committedRolls[targets.indexOf(operative)]);
        results.forEach(result=>{
          const targetId=selected[results.indexOf(result)],target=targets[results.indexOf(result)],before=target.wounds;
          if(targetId.startsWith('player:'))state.playerWounds[target.id]=Math.max(0,before-result.damage);
          else {target.wounds=Math.max(0,before-result.damage);if(!target.wounds){target.ready=false;target.deployed=false;target.battlefieldState='out-of-action';}}
          log(`${npoName(n)} used Geomantic Disturbance on ${targetId.startsWith('player:')?playerName(target.id):npoName(target)}: ${result.dice.join('+')}=${result.total}; ${result.damage} damage.`);
        });
        const resolvedResult={targets:selected,results};
        if(state.lastActivation?.pendingAction)state.lastActivation.pendingAction.resolvedResult=resolvedResult;
        save();acknowledgeCurrentDiceRequest();
        finishNpoSpecialAction(n,action,resolvedResult,decision,answers,questionHistory);
      };
      return;
    }
    const confirmation=action.id==='molecular-breach'?`I confirmed that this ${opponentSingularLabel()} can be placed as instructed.`:'I confirmed that this target is visible and within range.';
    const buttonLabels={'canoptek-control':'Use Canoptek Control','molecular-breach':'Apply Molecular Breach',overcharge:'Use Overcharge','cranial-overload':'Use Cranial Overload','nanoscarab-beam':'Roll Healing'};
    showModal(action.name,`${npoSpecialActionDescription(action)}<div class="field"><label for="specialActionTarget">${targetLabel}</label><select id="specialActionTarget"><option value="">Select operative…</option>${targetOptions}</select></div>${action.id==='canoptek-control'?'<div class="field"><label for="freeActionChoice">Choose the free 1 AP action</label><select id="freeActionChoice"><option>Reposition</option><option>Dash</option><option>Charge</option><option>Shoot</option><option>Fight</option><option>Mission action</option></select></div>':''}<label class="check-row" for="specialRangeConfirmed"><input id="specialRangeConfirmed" type="checkbox"><span>${escapeHtml(confirmation)}</span></label><div class="wizard-actions"><button class="btn ghost" id="cancelSpecialAction">Cancel</button><button class="btn primary" id="confirmSpecialAction" disabled>${escapeHtml(buttonLabels[action.id]||`Use ${action.name}`)}</button></div>`);
    const update=()=>{$('#confirmSpecialAction').disabled=!$('#specialActionTarget').value||!$('#specialRangeConfirmed').checked;};
    $('#specialActionTarget').onchange=update;$('#specialRangeConfirmed').onchange=update;
    $('#cancelSpecialAction').onclick=()=>{if(isPvpMode()){state.lastActivation.pendingAction=null;save();renderHumanNpoActionPicker(n);}else resolveNpoAction(n,state.lastActivation.pendingAction);};
    $('#confirmSpecialAction').onclick=async()=>{
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
      if(action.id==='nanoscarab-beam'){
        try{
          const pendingAction=state.lastActivation?.pendingAction;
          if(pendingAction){pendingAction.targetId=targetId;save();}
          if(pendingAction?.resolvedResult)result=pendingAction.resolvedResult;
          else{
            const requestKey=diceRequestKey('npo-activation',n.id,'nanoscarab-beam',targetId);
            const dice=await requestDiceResults({count:3,sides:3,title:'NANOSCARAB BEAM',instruction:'Roll 3D3 on the tabletop and enter each result.',rollerLabel:npoName(target),requestKey,resumeKind:'npo-special-action',resumeData:{npoId:n.id,actionId:action.id,targetId}});
            result=useNanoscarabBeam(target,dice);
            if(result){pendingAction.diceResults={healing:[...dice]};pendingAction.resolvedResult=result;save();acknowledgeDiceRequest(requestKey);}
          }
        }catch(error){
          console.error('[Nanoscarab Beam Dice]',error);
          button.disabled=false;
          return;
        }
      }
      if(!result){button.disabled=false;showToast('That action is no longer legal.');return;}
      if(result?.applied===false){
        button.disabled=false;
        showToast(`${action.name} could not be applied. No AP was spent.`);
        if(isPvpMode()){state.lastActivation.pendingAction=null;save();renderHumanNpoActionPicker(n);}
        return;
      }
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
    if(isPvpMode()){
      state.lastActivation.pendingAction=null;
      save();renderHumanNpoActionPicker(n);
      return;
    }
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
    if(isPvpMode()){
      state.lastActivation={...state.lastActivation,pendingAction:null,targetConfirmed:false,attackRequired:false,attackResolved:false,combatDraft:null};
      state.npoAttackTargetId=null;state.npoAttackSummary=null;
      save();renderHumanNpoActionPicker(n);
      return;
    }
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
    modalBody.innerHTML=`<div class="modal-inner">${renderNpoActivationHeader(n)}<div class="ai-wizard"><div class="npo-question-flow"><section class="npo-question-active npo-question-card--active npo-movement-confirmation" aria-labelledby="${headingId}" aria-describedby="${instructionId}"><h3 id="${headingId}">${escapeHtml(displayAction)}</h3><p id="${instructionId}">${escapeHtml(decision.reason)}</p><p class="npo-movement-cost">Costs ${pendingAction.apCost} AP (${state.lastActivation.remainingAp} AP to ${state.lastActivation.remainingAp-pendingAction.apCost} AP)</p><div class="ai-choice-grid"><button class="ai-choice yes npo-movement-confirm" id="confirmNpoMovement"><strong>Confirm ${escapeHtml(displayAction)} Complete</strong></button></div></section></div>${renderNpoGuideFooter()}</div></div>`;
    if(!modal.open)modal.showModal();
    modal.setAttribute('aria-labelledby','activeNpoQuestionHeading');
    modal.setAttribute('tabindex','-1');
    $('[data-close]',modal).onclick=closeModal;
    $('#aiBack').onclick=()=>backFromNpoMovementConfirmation(n);
    requestAnimationFrame(()=>focusInitialDialogControl(modal));
  }

  function resolveNpoAction(n,pendingAction){
    if(!pendingAction||state.lastActivation?.pendingAction?.id!==pendingAction.id)return;
    if(!isPvpMode()&&normalizeUnknownAttackMovement(state.lastActivation)){
      save();runNpoPrompt(n,0,{},state.lastActivation.questionHistory||[]);return;
    }
    const decision=isPvpMode()?humanNpoDecision(n,pendingAction.name):chooseNpoDecision(n,{action:pendingAction.name});
    if(npoSpecialAction(n,pendingAction.name)){resolveNpoSpecialAction(n,decision,state.lastActivation.answers||{},state.lastActivation.questionHistory||[]);return;}
    if(npoActionChangesContext(pendingAction.id)){
      renderNpoMovementConfirmation(n,pendingAction,decision);
      $('#confirmNpoMovement').onclick=()=>{const button=$('#confirmNpoMovement');if(!canCommitNpoAction(pendingAction.id,pendingAction.apCost))return;button.disabled=true;const effect=consumeMolecularBreach(n.id,pendingAction.id==='fall-back'?'Fall Back':pendingAction.name.split(' ')[0]);const finalApDash=pendingAction.id==='dash'&&state.lastActivation.remainingAp===pendingAction.apCost&&!state.lastActivation.pendingFollowUpAction&&!isPvpMode();commitNpoAction({actionId:pendingAction.id,actionName:pendingAction.name,apCost:pendingAction.apCost,result:effect||decision.reason,changesPosition:true,endsActivation:finalApDash,transitionMode:finalApDash?NPO_ACTION_TRANSITIONS.COMPLETE_ACTIVATION:NPO_ACTION_TRANSITIONS.AUTO_CONTINUE});};
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
    modalBody.innerHTML=`<div class="modal-inner"><h2>Target could not be confirmed</h2><div class="summary-box">The attack state was not preserved. No AP, dice, or damage were committed.</div><div class="wizard-actions"><button class="btn primary" id="recoverNpoActivation">Return to ${escapeHtml(opponentSingularLabel())} Activation</button></div></div>`;
    if(!modal.open)modal.showModal();
    $('#recoverNpoActivation').onclick=()=>{
      const current=state.lastActivation;
      state.npoAttackTargetId=null;state.npoAttackSummary=null;state.weaponRuleResolution=null;
      state.lastActivation={...current,pendingAction:null,targetConfirmed:false,attackRequired:false,attackResolved:false,combatDraft:null};
      save();isPvpMode()?renderHumanNpoActionPicker(n):runNpoPrompt(n,0,current?.answers||{},current?.questionHistory||[]);
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
      showToast(`That ${playerSideLabel()} operative is no longer an eligible target. Select another target.`);
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
    if(!isPvpMode()&&!targetConfirmed&&eligibleTargetIds.length===1)state.npoAttackTargetId=eligibleTargetIds[0];
    state.lastActivation={...state.lastActivation,name:npoName(n),...decision,dice,answers,questionHistory,attackResolved,attackRequired,targetConfirmed};save();
    if(attackRequired&&targetConfirmed&&!attackResolved){
      openNpoCombat(n,decision,dice,answers);
      return;
    }
    const targetOptions=eligibleTargetIds.map(id=>`<option value="${escapeHtml(id)}" ${state.npoAttackTargetId===id?'selected':''}>${escapeHtml(playerTargetLabel(id))}</option>`).join('');
    const targetName=state.npoAttackTargetId?playerTargetLabel(state.npoAttackTargetId):'';
    const targetField=targetConfirmed||(!isPvpMode()&&eligibleTargetIds.length===1)
      ? `<input id="npoPriorityTarget" value="${escapeHtml(targetName)}" readonly>`
      : `<select id="npoPriorityTarget" ${attackResolved?'disabled':''}><option value="" ${state.npoAttackTargetId?'':'selected'}>${isPvpMode()?'Choose an eligible target.':'Select the first operative that matches the priority above.'}</option>${targetOptions}</select>`;
    const targetPriority=!isPvpMode()&&decision.target.length?`<p>Choose the target in this order:</p><ol>${decision.target.map(item=>`<li>${escapeHtml(item)}</li>`).join('')}</ol><p>Randomize only if still tied.</p>`:'';
    const attackSummary=attackResolved&&state.npoAttackSummary?{
      ...state.npoAttackSummary,
      side:'player',
      attackType:state.npoAttackSummary.attackType||(decision.action.includes('Fight')?'melee':'shoot')
    }:null;
    const eliminationAction=newlyEliminated(attackSummary)?` Eliminated ${escapeHtml(attackSummary.targetName)}.`:'';
    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <div class="ai-result-title"><div><h2>${escapeHtml(npoName(n))}</h2><p>${escapeHtml(n.type)}</p></div></div>
      ${attackRequired&&questionHistory.length?`<div class="npo-question-flow">${renderCompletedNpoQuestions(questionHistory.filter(item=>item.type!=='selected'))}</div>`:''}
      <div class="npo-result-card"><div><small>${isPvpMode()?'SELECTED ACTION':'NEXT ACTION'}</small><strong>${escapeHtml(decision.action)}</strong><p>${escapeHtml(decision.reason)}</p><div class="npo-target-priority">${isPvpMode()?'':`<small>TARGET PRIORITY</small>`}${targetPriority}${attackRequired?`<div class="field target-selection"><label for="npoPriorityTarget">Select Target</label>${targetField}</div>`:''}</div></div></div>
      ${attackRequired&&!targetConfirmed&&(isPvpMode()||eligibleTargetIds.length>1)?`<button class="btn secondary big-action" id="confirmNpoTarget" ${state.npoAttackTargetId?'':'disabled'}>Confirm Target</button>`:''}
      ${attackRequired&&!targetConfirmed&&!isPvpMode()&&eligibleTargetIds.length===1?`<button class="btn secondary big-action" id="resolveNpoTarget">Resolve Combat</button>`:''}
      ${attackSummary?`${renderEliminationSummary(attackSummary)}<section class="card npo-attack-summary">
        <p class="eyebrow">${escapeHtml(opponentSingularLabel().toUpperCase())} ATTACK SUMMARY</p>
        ${renderAttackSummary(attackSummary)}
        <div class="combat-stage"><small>${escapeHtml(playerSideLabel().toUpperCase())} SAVE ROLL</small><div class="dice-row settled">${attackSummary.saveDice.length?attackSummary.saveDice.map(dieHtml).join(''):'<span class="muted">No save dice rolled</span>'}</div></div>
        <div class="damage-summary">
          <div><small>Unsaved normal hits</small><strong>${attackSummary.normalRemaining}</strong></div>
          <div><small>Unsaved critical hits</small><strong>${attackSummary.critRemaining}</strong></div>
        </div>
      </section><div class="summary-box"><strong>Actions:</strong> ${attackSummary.attackType==='shoot'?'Shooting':'Melee'} attack resolved.${eliminationAction}</div>`:''}
      ${!attackRequired?`<div class="wizard-actions">${isPvpMode()&&npoActionId(decision.action)==='operate-hatch'?'<button class="btn ghost" id="cancelNpoUtilityAction">Back</button>':''}<button class="btn primary" id="completeNpo">Confirm ${escapeHtml(decision.action)} Complete</button></div>`:''}
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
    $('#cancelNpoUtilityAction')?.addEventListener('click',()=>backFromNpoAttackSelection(n));

    $('#completeNpo')?.addEventListener('click',()=>{
      const pending=state.lastActivation?.pendingAction;
      if(pending)commitNpoAction({actionId:pending.id,actionName:pending.name,apCost:pending.apCost,result:decision.reason});
    });
  }

  async function completeNpoActivation(){
    const activation=state.lastActivation;
    if(activation?.committed){
      if(!activation.completionHookPending)return;
      closeModal();
      await executeMissionLifecycleHook('onNpoActivationCompleted',{activationId:activation.activationId,operativeId:activation.npoId});
      activation.completionHookPending=false;save();
      if(!checkGameEnd())render();
      return;
    }
    const n=state.roster.find(item=>item.id===activation?.npoId);
    if(!n)return;
    state.lastActivation.committed=true;state.lastActivation.completed=true;state.lastActivation.completionHookPending=true;
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
    state.lastActivation.completionHookPending=false;save();
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
    const newlyIncapacitated=summary.after<=0&&!casualties.has(target.id);
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
    if(newlyIncapacitated)void resolveRewardsOfAnnihilation(n,target,summary);
  }

  function resolveRewardsOfAnnihilation(n,target,summary={}){
    if(!tombWorldEventActive('rewards-of-annihilation')||!['Skorpekh Destroyer','Hexmark Destroyer'].includes(n.type))return false;
    const casualtyWounds=Number(target.maxWounds||playerDefinition(target.id)?.wounds||0),diceCount=casualtyWounds>=12?2:1;
    const identity=summary.transactionId||`${state.turningPoint}:${state.activationNumber}:${n.id}:${target.id}:${state.eventState.rewardsTriggers.length}`;
    const transaction=eventTransaction(`rewards:${identity}:${target.id}`,{definitionId:'rewards-of-annihilation',sourceTransactionId:identity,attackerId:n.id,casualtyId:target.id,casualtyWounds,diceCount,rolls:[],restored:0});
    if(transaction.committed)return false;
    if(!state.eventState.rewardsTriggers.includes(transaction.id))state.eventState.rewardsTriggers.push(transaction.id);
    save();void processRewardsOfAnnihilationQueue();return true;
  }
  async function processRewardsOfAnnihilationQueue(){
    if(rewardsQueueInProgress)return false;
    rewardsQueueInProgress=true;
    try{
      for(const transactionId of state.eventState.rewardsTriggers){
        const transaction=state.eventState.transactions?.[transactionId];
        if(!transaction||transaction.committed)continue;
        const n=state.roster.find(item=>item.id===transaction.attackerId&&item.wounds>0);if(!n)continue;
        transaction.requesting=true;save();
        const requestKey=diceRequestKey('rewards-of-annihilation',transaction.id,n.id,transaction.casualtyId);
        const rolls=await requestDiceResults({count:transaction.diceCount,sides:3,title:'REWARDS OF ANNIHILATION',instruction:`Roll ${transaction.diceCount===2?'2D3':'D3'} to restore the Destroyer’s lost wounds.`,rollerLabel:npoName(n),requestKey,resumeKind:'rewards',resumeData:{transactionId:transaction.id,npoId:n.id,casualtyId:transaction.casualtyId}});
        const before=n.wounds,total=rolls.reduce((sum,value)=>sum+value,0);n.wounds=Math.min(n.maxWounds,n.wounds+total);
        Object.assign(transaction,{rolls:[...rolls],result:total,restored:n.wounds-before,committed:true});delete transaction.requesting;
        log(`Rewards of Annihilation: ${npoName(n)} incapacitated ${playerName(transaction.casualtyId)}, rolled ${rolls.join('+')} and restored ${transaction.restored} wound${transaction.restored===1?'':'s'}.`);
        save();acknowledgeDiceRequest(requestKey);
      }
      render();return true;
    }catch(error){console.error('[Rewards of Annihilation] Dice request failed; healing was not committed.',error);return false;}
    finally{rewardsQueueInProgress=false;}
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
    if(!target){showToast(`Select the targeted ${playerSideLabel()} operative first.`);if(onCancel)onCancel();return;}
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
      showModal('Unable to Resolve Combat',`<div class="modal-inner"><div class="summary-box"><strong>This ${escapeHtml(opponentSingularLabel())} has no weapon it can use for this ${weaponType} attack.</strong></div><div class="wizard-actions"><button class="btn ghost" id="cancelNpoAttack">Back</button></div></div>`);
      $('#cancelNpoAttack').onclick=()=>{if(onCancel)onCancel();};
      return;
    }
    if(attackType==='melee'){
      const baseAttackerProfile=canonicalAttackProfile(availableProfiles[0]);
      const begin=async defenderProfile=>{
        const attackerProfile=await effectiveEnforcerNpoWeaponProfile(n,baseAttackerProfile,'melee');
        const transactionId=`fight:${state.lastActivation?.activationId||missionActivationId('npo',n.id)}:${state.lastActivation?.pendingAction?.decisionPass||1}:npo:${n.id}:player:${target.id}:${attackerProfile.weaponId}:${defenderProfile.weaponId}`;
        const attacker=fightParticipantState({side:'npo',id:n.id,label:npoName(n),profile:attackerProfile,wounds:n.wounds,maxWounds:n.maxWounds});
        const defender=fightParticipantState({side:'player',id:target.id,label:targetName,profile:defenderProfile,wounds:playerCurrentWounds(target.id),maxWounds:target.maxWounds||playerDefinition(target.id)?.wounds});
        void startSharedFight({id:transactionId,attacker,defender,onComplete:summary=>onDone?.(summary,[summary])});
      };
      choosePlayerRetaliationWeapon(target.id,begin,()=>onCancel?.());
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
      ? `<label class="check-row compact-check" for="sameRoomAsC1"><input type="checkbox" id="sameRoomAsC1"><span><strong>Is this ${isPvpMode()?'Necron':'NPO'} in the same room as the sarcophagus?</strong><small>This matters only while My Will Be Done is active.</small></span></label>`
      : '';
    const enforcer=tombWorldEventActive('enforcer-of-the-phaerons')&&activeNpos().some(operative=>operative.type==='Royal Warden')&&!initialProfile?.rules?.some(rule=>/^Ceaseless$/i.test(String(rule)))&&!sameCombat&&!rollingCombat;
    const enforcerQuestion=enforcer&&n.type!=='Royal Warden'
      ? `<label class="check-row compact-check" for="sameRoomAsRoyalWarden"><input type="checkbox" id="sameRoomAsRoyalWarden"><span><strong>Is ${escapeHtml(npoName(n))} in the same room as a Royal Warden?</strong><small>This matters only while Enforcer of the Phaerons is active.</small></span></label>`:'';
    const guidance=npoCombatGuidanceHtml(n,{attackType,profile:initialProfile});
    const screen=showSharedCombatResolutionScreen({
      title:'Resolve Combat',attackerName:npoName(n),defenderName:targetName,attackType,
      weaponName:initialProfile?.name||'—',attackLabel:initialProfile?combatAttackLabel(initialProfile):'—',defenseLabel:`3 dice · ${target.save||3}+`,
      cancelId:'cancelNpoAttack',continueId:'completeNpoCombat',extraHtml:`<div id="npoCombatGuidance">${guidance}</div>${profileControl}${willBeDone}${enforcerQuestion}`,
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
    if(rollingCombat)screen.cancelButton.disabled=true;

    let combatTimer=null;
    let resolutionCommitted=false;
    const commitCombat=(combat)=>{
      const pending=state.lastActivation?.pendingAction;
      if(resolutionCommitted||!pending||!canCommitNpoAction(pending.id,pending.apCost))return;
      resolutionCommitted=true;
      const complete=$('#completeNpoCombat');
      complete.disabled=true;
      const resolvedCombat=reuseCommittedDimensionalBanishment(combat);
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
    const displayCombat=async(combat,animate=false)=>{
      let resolvedCombat;
      try{resolvedCombat=await requestDimensionalBanishment(combat,npoName(n));}
      catch(error){console.error('[Dimensional Banishment] Dice request failed. No combat result was committed.',error);return;}
      const banishmentAnimating=resolvedCombat.dimensionalBanishmentTriggered&&!resolvedCombat.dimensionalBanishmentAnimationShown;
      if(resolvedCombat!==combat){
        state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
        save();
        acknowledgeCurrentDiceRequest();
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
    const finishAutomaticCombat=async(profile,rolledAttackDice,rolledDefenseDice,immediateEffects={})=>{
      const resolution=immediateEffects.devastatingIncapacitated?{normal:0,critical:0,damage:0}:resolveRetainedCombat(rolledAttackDice,rolledDefenseDice,profile);
      const devastatingDamage=Number(immediateEffects.devastatingDamage??devastatingDamageForAttack(rolledAttackDice,profile));
      const combat={
        ...recordedCombat({attackerName:npoName(n),defenderName:targetName,attackType,attackerSide:'npo',defenderSide:targetSide,profile,before:target.wounds||10,
          normalSuccesses:resolution.normal,criticalSuccesses:resolution.critical,damage:resolution.damage+devastatingDamage}),
        attackDice:rolledAttackDice,saveDice:rolledDefenseDice,
        retainedSaves:retainedDiceTotals(rolledDefenseDice).normal+retainedDiceTotals(rolledDefenseDice).critical,
        recordedOutcome:false,targetId:target.id,targetName:targetName,
        severeApplied:rolledAttackDice.some(die=>die.severeConverted),devastatingDamage,devastatingApplied:true,devastatingIncapacitated:Boolean(immediateEffects.devastatingIncapacitated)
      };
      combat.eventMessages=[];
      let resolvedCombat;
      try{resolvedCombat=await requestDimensionalBanishment(combat,npoName(n));}
      catch(error){console.error('[Dimensional Banishment] Dice request failed. No combat result was committed.',error);rollStarted=false;return;}
      const stun=applyStunForAttack({profile,attackDice:rolledAttackDice,sourceAttackId:`attack:${state.turningPoint}:${state.activationNumber}:npo:${n.id}:${target.id}`,targetId:target.id,targetName:targetName,targetSide});
      if(stun.message)resolvedCombat.eventMessages.push(stun.message);
      state.lastActivation={...state.lastActivation,combatDraft:resolvedCombat};
      save();
      acknowledgeCurrentDiceRequest();
      void displayCombat(resolvedCombat,false);
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
      if(transaction.definitionAnswers.sameRoomAsRoyalWarden===undefined)transaction.definitionAnswers.sameRoomAsRoyalWarden=n.type==='Royal Warden'||Boolean($('#sameRoomAsRoyalWarden')?.checked);
      const profile=effectiveWeaponProfile(baseProfile,{attackerSide:'npo',attackType,sameRoomAsC1:transaction.definitionAnswers.sameRoomAsC1,sameRoomAsRoyalWarden:transaction.definitionAnswers.sameRoomAsRoyalWarden});
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
      const restoredAttackDice=restoredRoll?.attackDice||null;
      const restoredDefenseDice=restoredRoll?.saveDice||null;
      combatTimer=runAutomaticCombatRolls({container:screen.dice,profile,defenseSave:target.save,defenderWounds:target.wounds,attackerSide:'npo',attackType,
        attackerLabel:npoName(n),defenderLabel:targetName,requestKeyBase:`combat:attack:${state.turningPoint}:${state.activationNumber}:${attackType}:npo:${n.id}:${target.id}:${profile.weaponId}:${profile.profileId}`,
        rolledAttackDice:restoredAttackDice,rolledDefenseDice:restoredDefenseDice,
        onAttackComplete:completedAttackDice=>{
          state.lastActivation={...state.lastActivation,dice:attackDice.map(d=>({...d})),targetConfirmed:true,combatDraft:{
            rolling:true,attackType,targetId:target.id,targetName:targetName,profile,attackDice:completedAttackDice.map(die=>({...die})),
            severeApplied:completedAttackDice.some(die=>die.severeConverted)
          }};
          screen.cancelButton.disabled=true;
          save();
        },
        onComplete:(completedAttackDice,completedDefenseDice)=>{
        const immediateEffects=completedAttackDice.immediateEffects||{};
        state.lastActivation={...state.lastActivation,dice:attackDice.map(d=>({...d})),targetConfirmed:true,combatDraft:{
          rolling:true,attackType,targetId:target.id,targetName:targetName,profile,attackDice:completedAttackDice,saveDice:completedDefenseDice,
          severeApplied:completedAttackDice.some(die=>die.severeConverted),...immediateEffects
        }};
        save();
        combatTimer=null;
        void finishAutomaticCombat(profile,completedAttackDice,completedDefenseDice,immediateEffects);
      },onError:()=>{rollStarted=false;}});
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
    if(sameCombat)void displayCombat(saved,animateCombat);
    else if(rollingCombat)startAutomaticCombat(saved);
    else if(availableProfiles.length===1&&willBeDone){
      screen.continueButton.disabled=false;
      screen.continueButton.textContent='Roll Attack';
      screen.continueButton.onclick=()=>startAutomaticCombat();
    }
    else if(isPvpMode()&&!resumeGuided&&(availableProfiles.length===1||locked)){
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
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(presentSideTerminology(rule.name))}</strong>${rule.timing?`<small>${escapeHtml(presentSideTerminology(rule.timing))}</small>`:''}<p>${escapeHtml(presentSideTerminology(rule.summary))}</p></div>`).join('');
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${escapeHtml(presentSideTerminology(m.brief))}</p></div></div>
      <section class="card"><h3>Objective</h3><p>${escapeHtml(presentSideTerminology(m.objective))}</p><div class="stat-grid"><div class="stat"><small>Starting ${escapeHtml(opponentPluralLabel())}</small><strong>${missionSetup(m)}</strong></div><div class="stat"><small>TP1 Initiative</small><strong>${escapeHtml(missionFirstInitiative(m)==='npo'?opponentPluralLabel():playerSideLabel())}</strong></div><div class="stat"><small>Objective</small><strong>${escapeHtml(presentSideTerminology(m.missionEngine?.progressLabel||missionTracker(m)))}</strong></div></div><p><strong>${escapeHtml(opponentSingularLabel())} deployment:</strong> ${escapeHtml(presentSideTerminology(m.startingNpos?.deployment||'Use the mission rules.'))}</p></section>
      ${boardSvg(m.id)}
      <section class="card"><h3>Battle settings</h3><p><strong>Restless Tomb:</strong> ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p>${isPvpMode()?'':`<p><strong>Deadly Encounters:</strong> ${deadlyEncountersStatusLabel()} (Official Expansion - White Dwarf 521)</p>`}</section>
      <section class="card"><h3>Mission rules</h3><div class="mission-rules">${rules}</div></section>
      <section class="card"><h3>Victory</h3><p><strong>Win:</strong> ${escapeHtml(presentSideTerminology(m.victory?.win||'See mission rules.'))}</p><p><strong>Lose:</strong> ${escapeHtml(presentSideTerminology(m.victory?.lose||'See mission rules.'))}</p></section>${missionProgressHtml()}`;
  }
  function renderRoster(){const available=Object.values(npoInventory()).reduce((sum,item)=>sum+item.remaining,0);app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">${escapeHtml(opponentSingularLabel().toUpperCase())} ROSTER</p><h2>${activeNpos().length} active ${escapeHtml(opponentPluralLabel())}</h2><p>${available} of ${MAX_PHYSICAL_NPOS} physical models remain available. Activation status is tracked automatically.</p></div><button class="btn secondary" id="addNpo" ${available?'':'disabled'}>Add ${escapeHtml(opponentSingularLabel())}</button></div><div class="player-roster-grid npo-roster-grid">${state.roster.length?sortedNposForDisplay(state.roster).map(n=>npoRosterCard(n,n.battlefieldState==='deployed'||n.wounds<=0)).join(''):`<div class="card empty">No ${escapeHtml(opponentPluralLabel())} are currently on the battlefield.</div>`}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));$$('[data-npo-loadout]').forEach(select=>select.onchange=()=>changeNpoLoadout(select.dataset.npoLoadout,select.value));}
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
    const teamName=selectedPlayerTeamName(isPvpMode()?'Kill Team':'Player');
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">${escapeHtml(playerSideLabel().toUpperCase())} ROSTER</p><h2>${escapeHtml(teamName)}</h2><p>${inPlayPlayerOperativeIds().filter(id=>!casualties.has(id)).length} active on the battlefield of ${(state.playerRoster||[]).length} selected operatives.</p></div></div>${factionGuidanceHtml()}<div class="roster-grid player-full-roster-grid">${cards||'<div class="card empty">No Player operatives were selected for this game.</div>'}</div>`;
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
      ${loadout}${npoProfileDetailsHtml(n,definition)}<div class="npo-card-actions">${controls?`<div class="wound-controls"><button class="btn ghost" data-wound="${n.id}" ${!hasProfile||n.wounds<=0?'disabled':''}>− Wound</button><button class="btn ghost" data-heal="${n.id}" ${!hasProfile||n.wounds>=n.maxWounds?'disabled':''}>+ Heal</button></div>`:''}<div class="quick-actions"><button class="btn danger" data-delete="${n.id}" ${state.turningPoint>0?'disabled':''}>Remove ${escapeHtml(opponentSingularLabel())}</button></div></div>
    </article>`;
  }
  function operativeCard(n,controls){return npoRosterCard(n,controls);}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(presentSideTerminology(j.text))}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Instructions & quick reference</h2><p>${isPvpMode()?'Review player responsibilities and common gameplay terms.':`Review the ${escapeHtml(opponentSingularLabel())} decision process and common gameplay terms.`} This reference does not change the current game.</p></div></div>${guideInstructionsHtml(false)}<section class="card help-list">
    <details><summary>Tombs Beyond Counting</summary><p>The Guide supports the official White Dwarf 517 expansion through three mutually exclusive Tomb World variants: Flayer Curse Infected Tomb, Destroyer Cult Tomb, and Crownworld of the Dynasty Tomb. A selected variant can substitute additional Necron NPOs, add its corresponding Tomb World event, and apply variant-specific rules. Select the variant before NPO deployment. The manual Add NPO tool remains limited to the Standard inventory; expansion operatives enter play only through their rules-driven replacement flows. Consult the official publication for authoritative wording.</p></details>
    ${isPvpMode()?'':'<details><summary>Deadly Encounters: Tomb Worlds</summary><p>This is the official optional expansion from White Dwarf 521, February 2026. The Guide implements only its PvE solo method. Player operatives reveal persistent features; NPOs never reveal them, although revealed features can affect NPOs. Rooms and eligible markers use separate D33 tables, and every feature rule is unique across the battle. Deadly Encounters is independent from Restless Tomb. Consult the official publication for authoritative wording.</p></details>'}
    <details><summary>What does ${escapeHtml(playerSideLabel())} mean?</summary><p>${isPvpMode()?'The operatives from the selected player-controlled Kill Team.':'Your solo player-controlled Kill Team operatives.'}</p></details>
    <details><summary>What is a ${escapeHtml(opponentSingularLabel())}?</summary><p>${isPvpMode()?'A Necron operative controlled by the second player. The Guide validates choices and tracks the battle, but does not choose its actions or targets.':'A non-player operative controlled by the Guide’s decision tree.'}</p></details>
    <details><summary>What is Threat Level?</summary><p>A 0–15 alert meter that rises from loud or destructive actions. Higher Threat produces higher grades, more reinforcements, and eventually Tomb World events.</p></details>
    <details><summary>What is Threat Grade?</summary><p>Grade 0 at Threat 0, Grade 1 at 1–5, Grade 2 at 6–10, and Grade 3 at 11–15. Reinforcements normally equal the current grade after Turning Point 1.</p></details>
    <details><summary>How does alternating activation work?</summary><p>The side with initiative activates first. The Guide then alternates ${escapeHtml(playerSideLabel())} and ${escapeHtml(opponentSingularLabel())} activations whenever both sides still have ready operatives. If one side runs out, the other finishes its remaining activations.</p></details>
    <details><summary>What happens during the Strategy Phase?</summary><p>The Guide readies operatives, applies mission Ready rules, determines initiative, then processes Tomb World events and reinforcements.</p></details>
    <details><summary>How are saves and damage handled?</summary><p>${isPvpMode()?'Roll physical dice and enter each result when prompted.':'The Guide rolls gameplay dice automatically.'} Resolve retained successes with the current Core rules. The Guide shows the canonical profile and records the resulting damage; the resulting damage is committed with the completed combat action.</p></details>
  </section>`;}


  function boardSvg(id){
    const currentMission=mission();
    const missionNumber=String(currentMission.number).padStart(2,'0');
    const imagePath=`Assets/Maps/mission-${missionNumber}.png?v=${APP_VERSION}`;
    return `<figure class="official-map-card">
      <div class="official-map-heading">
        <div><span>MISSION MAP</span><strong>${escapeHtml(currentMission.number)} · ${escapeHtml(currentMission.name)}</strong></div>
        <small>Battle Guide schematic</small>
      </div>
      <img class="official-map-image" src="${imagePath}" alt="Battle Guide board layout for ${escapeHtml(currentMission.name)}" loading="eager">
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
    showModal(`Add ${opponentSingularLabel()}`,`<div class="field"><label>${escapeHtml(opponentSingularLabel())} type</label><select id="newNpoType">${types.map(type=>`<option value="${escapeHtml(type)}" ${inventory[type].remaining?'':'disabled'}>${escapeHtml(type)} — ${inventory[type].remaining} remaining</option>`).join('')}</select></div><div id="newNpoLoadout"></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add ${escapeHtml(opponentSingularLabel())}</button></div>`);
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

  async function animateMissionDice(operation,context={}){
    const supplied=context.missionDice;
    const requestKey=diceRequestKey('mission',state.missionId,context.activationId||context.operativeId||state.missionActionContext?.operativeId,context.siteId||context.roomId||state.missionActionContext?.siteId||state.missionActionContext?.roomId,operation.id);
    const previousPending=state.pendingDice;
    if(previousPending?.status==='committed'&&previousPending.requestKey!==requestKey&&state.missionRuntime?.pendingDiceResults?.[previousPending.requestKey]){
      acknowledgeDiceRequest(previousPending.requestKey);
    }
    const saved=state.missionRuntime?.pendingDiceResults?.[requestKey];
    const candidate=Array.isArray(supplied)?supplied:saved;
    const suppliedDice=Array.isArray(candidate)&&candidate.length===operation.dice.count
      &&candidate.every(value=>Number.isInteger(value)&&value>=1&&value<=operation.dice.sides)?candidate.slice():null;
    const dice=suppliedDice||await requestDiceResults({
      count:operation.dice.count,
      sides:operation.dice.sides,
      title:operation.label||'MISSION ROLL',
      instruction:`Roll ${operation.dice.count}D${operation.dice.sides} on the tabletop and enter each result.`,requestKey,resumeKind:'mission',resumeData:{missionId:state.missionId,operationId:operation.id,activationId:context.activationId||'',operativeId:context.operativeId||state.missionActionContext?.operativeId||'',siteId:context.siteId||state.missionActionContext?.siteId||'',roomId:context.roomId||state.missionActionContext?.roomId||''}
    });
    const result={dice,total:dice.reduce((sum,value)=>sum+value,0)};
    if(isPvpMode()){
      state.missionRuntime=state.missionRuntime||{};
      state.missionRuntime.pendingDiceResults={...(state.missionRuntime.pendingDiceResults||{}),[requestKey]:[...dice]};
      save();
    }
    if(isPvpMode())return result;
    return new Promise((resolve,reject)=>{
      let settled=false;
      showModal(operation.label||'Mission Roll',`<div class="dice-row animated-roll" id="missionDiceRoll">${dice.map(()=>rollingDieHtml()).join('')}</div><p>Rolling ${operation.dice.count}D${operation.dice.sides}…</p>`,()=>{if(!settled)reject(new TombWorldMissionEngine.MissionEngineError('DICE_CANCELLED','Mission dice roll was cancelled.'));});
      if(dice.length)void TombWorldDiceSfx.play();
      missionDialogLocked=true;
      setTimeout(()=>{
        if(!modal.open)return;
        settled=true;
        $('#missionDiceRoll').className='dice-row settled';
        $('#missionDiceRoll').innerHTML=dice.map(value=>dieHtml({value})).join('');
        modalBody.querySelector('p').textContent=`Dice: ${dice.join(' + ')} · Total: ${dice.reduce((sum,value)=>sum+value,0)}`;
        setTimeout(()=>{missionDialogLocked=false;closeModal();resolve(result);},450);
      },DICE_ROLL_ANIMATION_MS);
    });
  }

  function requestMissionNumber(operation){
    if(operation.id==='controllingPlayerOperatives'&&state.missionReadyContext?.turningPoint===state.turningPoint){
      return Promise.resolve(state.missionReadyContext.sarcophagusControllers);
    }
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
        if(operation.id==='controllingPlayerOperatives'){
          state.missionReadyContext={turningPoint:state.turningPoint,sarcophagusControllers:value};save();
        }
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
    if(['mission-feature-opened','mission-feature-corrected','transponder-search','transponder-carrier','transponder-drop','transponder-escape'].includes(entry.type))return entry.summary||entry.title;
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
    return `<div class="mission-details"><h3>${escapeHtml(selected?.name||'Selected Mission')}</h3><section><h4>Objective</h4><p>${escapeHtml(presentSideTerminology(selected?.objective||'Review the mission rules and track progress on the tabletop.'))}</p></section><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p>${isPvpMode()?'':`<p>Deadly Encounters: ${deadlyEncountersStatusLabel()} (Official Expansion - White Dwarf 521)</p>`}</section><p class="muted">Automated mission progress is not available for this mission.</p></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
  }

  function missionDetailsContent(){
    if(!objectiveEngine)return missionDetailsContentFallback();
    const model=objectiveEngine.getMissionDetailsModel();
    const objective=model.objectives[0];
    const history=model.history.slice(0,objectiveDefinition.presentation.historyDisplayCount||5);
    if(missionEngine()?.type==='transponder'){
      const activity=history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(missionHistoryText(entry))}</span>${entry.turningPoint?`<small>Turning Point ${entry.turningPoint}</small>`:''}</li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>';
      return `<div class="mission-details"><h3>RECOVER TRANSPONDER</h3>${missionProgressRenderers.transponder(missionEngine(),state.missionState||freshMissionState())}<section><h4>Recent Activity</h4>${activity}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
    }
    if(!objective)return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p>${isPvpMode()?'':`<p>Deadly Encounters: ${deadlyEncountersStatusLabel()} (Official Expansion - White Dwarf 521)</p>`}</section><section><h4>Objective</h4><p>${escapeHtml(presentSideTerminology(model.objectiveSummary))}</p></section><section><h4>Recent Activity</h4>${history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(presentSideTerminology(missionHistoryText(entry)))}</span></li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>'}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
    const completedDuring=objective.completedTurningPoint?`<section><h4>Completed during</h4><p>Turning Point ${objective.completedTurningPoint}</p></section>`:'';
    const activity=history.length?`<ul class="mission-history">${history.map(entry=>`<li><span>${escapeHtml(presentSideTerminology(missionHistoryText(entry)))}</span>${entry.turningPoint?`<small>Turning Point ${entry.turningPoint}</small>`:''}</li>`).join('')}</ul>`:'<p class="muted mission-history-empty">No mission activity yet.</p>';
    return `<div class="mission-details"><h3>${escapeHtml(model.name)}</h3><section><h4>Battle settings</h4><p>Restless Tomb: ${state.restlessTombEnabled?'On':'Off'} (House Rule)</p>${isPvpMode()?'':`<p>Deadly Encounters: ${deadlyEncountersStatusLabel()} (Official Expansion - White Dwarf 521)</p>`}</section>${objective.completed?'<p class="mission-complete-status">✓ Objective Complete</p>':`<section><h4>Objective</h4><p>${escapeHtml(presentSideTerminology(model.objectiveSummary))}</p></section>`}${completedDuring}<section><h4>${objective.completed?'Final Progress':'Progress'}</h4><p class="mission-progress">${objective.value} / ${objective.target}</p></section><section><h4>Recent Activity</h4>${activity}</section></div><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`;
  }

  function showMissionDetails(){
    let completed=false;
    let content;
    try{completed=Boolean(objectiveEngine?.getMissionHudModel().completed);content=missionDetailsContent();}
    catch(error){console.warn('[MissionEngine] Mission details unavailable.',error);content=missionDetailsContentFallback();}
    showModal(completed?'MISSION STATUS':'MISSION DETAILS',content);
    bindMissionProgressControls();
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
    if(stage.sequential){cancelCurrentHumanPlayerAction();return;}
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
    if(!canOfferBreachSarcophagus(stage,operativeId)){if(stage.sequential)cancelCurrentHumanPlayerAction();return;}
    if(remainingAp<apCost){showToast('Not enough AP to Breach the sarcophagus.');if(stage.sequential)cancelCurrentHumanPlayerAction();return;}
    if(apCost===1&&(stage.shoot||stage.charge)){showToast('The Breach reduction cannot be combined with Shoot or Charge in this activation.');if(stage.sequential)cancelCurrentHumanPlayerAction();return;}
    state.combatState={side:'player',stage:{...stage}};
    state.missionActionContext={missionId:'04',actionId:'breachSarcophagus',side:'player',operativeId,activationId,apCost,remainingAp,step:'control-range',controlRangeConfirmed:null,enemyControlRangeConfirmed:null,committed:false,diceRolled:false,dice:[],previousTotal:null,newTotal:null,victoryCommitted:false};
    save();renderBreachSarcophagusStep(stage);
  }

  function renderBreachSarcophagusStep(stage){
    const context=state.missionActionContext;
    if(!context||context.missionId!=='04'||context.actionId!=='breachSarcophagus')return stage.sequential?cancelCurrentHumanPlayerAction():showPlayerActivation(stage);
    if(context.operativeId!==stage.playerOperativeId||context.activationId!==missionActivationId('player',stage.playerOperativeId)){
      state.missionActionContext=null;save();showToast('The active operative changed. Breach was not performed.');if(stage.sequential)cancelCurrentHumanPlayerAction();else showPlayerActivation(stage);return;
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
      try{
        const requestKey=diceRequestKey('mission','04',context.activationId,'breach-sarcophagus',context.operativeId);
        context.dice=await requestDiceResults({count:2,sides:6,title:'BREACH SARCOPHAGUS',instruction:'Roll 2D6 on the tabletop and enter each result.',rollerLabel:playerName(context.operativeId),requestKey,resumeKind:'breach-sarcophagus',resumeData:{missionId:'04',activationId:context.activationId,operativeId:context.operativeId}});
        context.committed=true;context.diceRolled=true;context.step='result';
        stage.missionBreachCommitted=true;stage.missionBreachCost=context.apCost;
        state.combatState={side:'player',stage:{...stage}};save();acknowledgeDiceRequest(requestKey);
      }catch(error){
        if(button)button.disabled=false;
        console.error('[Breach Sarcophagus Dice]',error);
        return;
      }
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
    $('#breachResultContinue').onclick=async()=>{
      if(won){
        if(stage.sequential){commitHumanPlayerAction(stage);await completeHumanPlayerActivation();}
        void finalizeMissionCompletion('victory',context.previousPhase||'firefight');
      }
      else if(stage.sequential){completePlayerActivation(stage);}
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
    if(isPvpMode())return;
    const de=state.deadlyEncountersState,locations=Object.entries(de.operativeLocations).filter(([,roomId])=>roomId);
    showModal('Deadly Encounters: Tomb Worlds',`<p><strong>Status:</strong> ${deadlyEncountersStatusLabel()} · <span class="rule-classification official">Official Expansion - White Dwarf 521</span></p>${deadlyEncountersActive()?`<section class="deadly-section"><h3>Rooms</h3>${deadlyEntityList(de.rooms,'No rooms registered.')}</section><section class="deadly-section"><h3>Eligible markers</h3>${deadlyEntityList(de.objectives,'No markers registered.')}${Object.keys(de.objectives).length>3?'<p class="nonblocking-note">More than three markers are registered. Three is an official recommendation, not a limit.</p>':''}</section><section class="deadly-section"><h3>Operative room locations</h3>${locations.length?`<ul>${locations.map(([operativeId,roomId])=>`<li>${escapeHtml(deadlyOperativeOptions().find(item=>item.id===operativeId)?.label||operativeId)} — ${escapeHtml(de.rooms[roomId]?.label||'Outside registered rooms')}</li>`).join('')}</ul>`:'<p class="muted">No battlefield room locations recorded.</p>'}</section><section class="deadly-section"><h3>Active and pending effects</h3><p>${de.temporaryEffects.length?`${de.temporaryEffects.length} temporary effect(s) active.`:'No temporary effects.'}</p><p>${de.pendingResolution?'A mandatory resolution is pending.':'No resolution pending.'}</p></section><div class="game-menu-grid"><button class="btn primary" id="recordDeadlyEncounter">Record Deadly Encounter</button><button class="btn secondary" id="registerDeadlyRoom">Register Room</button><button class="btn secondary" id="registerDeadlyObjective">Register Marker</button><button class="btn secondary" id="updateDeadlyLocation">Update Room Location</button><button class="btn secondary" id="updateDeadlyCarrier">Update Carried Marker</button><button class="btn ghost" id="correctDeadlyRecord">Correct Location or Encounter</button></div>`:'<p>Deadly Encounters is disabled for this battle. No feature prompts or effects apply.</p>'}<p class="source-note">Concise play aid based on White Dwarf 521, February 2026. Consult the official publication for authoritative wording.</p><div class="wizard-actions"><button class="btn primary" data-close>Close</button></div>`);
    if(!deadlyEncountersActive())return;
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
    $('#confirmDeadlyDiscovery').onclick=()=>{const triggerType=$('#deadlyTrigger').value,entityId=$('#deadlyEntity').value,operativeId=$('#deadlyOperative').value;if(!entityId||!operativeId){showToast('Select an unresolved record and Player operative.');return;}const room=['opened','entered'].includes(triggerType),actionId=`manual-${Date.now().toString(36)}`,context={missionId:state.missionId,turningPoint:state.turningPoint,activationId:`tp${state.turningPoint}-a${state.activationNumber}`,actionId,actionType:'manual-record',actingSide:'player',operativeId,triggerType,...(room?{roomId:entityId,entityType:'room',entityId}:{objectiveId:entityId,entityType:'objective',entityId})};const result=DeadlyEncounters.discover(state.deadlyEncountersState,true,context);state.deadlyEncountersState=result.state;result.attempts?.forEach(attempt=>log(`Deadly Encounters D33 ${attempt.result}: ${attempt.status}${attempt.reason?` — ${attempt.reason}`:''}`));const names=deadlyFeatureNames(result.featureIds);log(`Deadly Encounters: ${room?'room':'marker'} ${result.entity?.label||entityId} revealed ${names.join(' and ')||result.message}.`);save();if(result.entity&&!result.duplicate&&result.featureIds.length){try{void TombWorldNarration.playDeadlyEncounter(result.featureIds,DeadlyEncounters.transactionId(context));}catch{/* Narration is optional and must never affect discovery. */}}showDeadlyResult(result,room,triggerType);};
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
        ${inGame?`${deadlyEncountersActive()?'<button class="btn secondary" id="menuDeadlyEncounters">Deadly Encounters</button>':''}
        <button class="btn secondary" data-game-view="mission">Mission & Map</button>
        <button class="btn secondary" data-game-view="roster">${escapeHtml(opponentSingularLabel())} Roster</button>
        <button class="btn secondary" data-game-view="player-roster">${escapeHtml(playerSideLabel())} Roster</button>
        <button class="btn secondary" data-game-view="journal">Battle Journal</button>`:''}
        ${canOpenHelp()?'<button class="btn secondary" id="menuHelp" type="button">Help</button>':''}
        <button class="btn secondary" id="menuAbout" type="button">About</button>
        <div class="ambient-toggle-row">
          <span id="narrationLabel">Narration</span>
          <button class="ambient-toggle" id="narrationToggle" type="button" role="switch" aria-labelledby="narrationLabel" aria-checked="${TombWorldNarration.isPreferenceEnabled()}">
            <span class="ambient-toggle-state">${TombWorldNarration.isPreferenceEnabled()?'On':'Off'}</span><span class="ambient-toggle-track" aria-hidden="true"><span></span></span>
          </button>
        </div>
        <div class="ambient-toggle-row">
          <span id="ambientNoiseLabel">Ambient Noise</span>
          <button class="ambient-toggle" id="ambientNoiseToggle" type="button" role="switch" aria-labelledby="ambientNoiseLabel" aria-checked="${ambientEnabled}">
            <span class="ambient-toggle-state">${ambientEnabled?'On':'Off'}</span><span class="ambient-toggle-track" aria-hidden="true"><span></span></span>
          </button>
        </div>
        <div class="ambient-toggle-row">
          <span id="diceRollLabel">Dice Roll</span>
          <button class="ambient-toggle" id="diceRollToggle" type="button" role="switch" aria-labelledby="diceRollLabel" aria-checked="${TombWorldDiceSfx.isPreferenceEnabled()}">
            <span class="ambient-toggle-state">${TombWorldDiceSfx.isPreferenceEnabled()?'On':'Off'}</span><span class="ambient-toggle-track" aria-hidden="true"><span></span></span>
          </button>
        </div>
        ${supportsInAppVolumeControl()?`<div class="game-volume-row">
          <label for="gameVolume">Volume</label>
          <div class="game-volume-control">
            <svg class="game-volume-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 9v6h4l5 4V5L8 9H4z"></path><path d="M16 9 L21 15 M21 9 L16 15"></path></svg>
            <input id="gameVolume" type="range" min="0" max="100" step="1" value="${TombWorldNarration.isMasterEnabled()?Math.round(preferredGameVolume*100):0}" aria-valuetext="${TombWorldNarration.isMasterEnabled()?`${Math.round(preferredGameVolume*100)} percent`:'Muted'}" style="--volume-percent:${TombWorldNarration.isMasterEnabled()?Math.round(preferredGameVolume*100):0}%">
            <svg class="game-volume-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 9v6h4l5 4V5L8 9H4z"></path><path d="M16 8.5c1.3 1.8 1.3 5.2 0 7M19 6c2.7 3.2 2.7 8.8 0 12"></path></svg>
          </div>
        </div>`:''}
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
    if(inGame&&deadlyEncountersActive())$('#menuDeadlyEncounters').onclick=showDeadlyEncountersPanel;
    if(canOpenHelp())$('#menuHelp').onclick=openHelpFromGameMenu;
    $('#narrationToggle').onclick=()=>{
      TombWorldNarration.setPreferenceEnabled(!TombWorldNarration.isPreferenceEnabled());
      syncNarrationControls();
    };
    $('#ambientNoiseToggle').onclick=()=>{
      ambientEnabled=!ambientEnabled;
      localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY,String(ambientEnabled));
      syncNarrationControls();
    };
    $('#diceRollToggle').onclick=()=>{
      TombWorldDiceSfx.setPreferenceEnabled(!TombWorldDiceSfx.isPreferenceEnabled());
      syncNarrationControls();
    };
    const gameVolume=$('#gameVolume');
    if(gameVolume)gameVolume.oninput=event=>{
      const percentage=Number(event.currentTarget.value);
      if(percentage===0){
        if(TombWorldNarration.isMasterEnabled())void setGameAudioEnabled(false);
        else syncNarrationControls();
        return;
      }
      preferredGameVolume=percentage/100;
      TombWorldNarration.setVolumeMultiplier(preferredGameVolume);
      TombWorldAmbient.setVolumeMultiplier(preferredGameVolume);
      TombWorldDiceSfx.setVolumeMultiplier(preferredGameVolume);
      writePreferredGameVolume();
      if(!TombWorldNarration.isMasterEnabled())void setGameAudioEnabled(true);
      else syncNarrationControls();
    };
    $('#menuAbout').onclick=showAbout;
    $('#menuExportSave').onclick=exportSave;
    $('#menuImportSave').onclick=()=>importInput.click();
    $('#menuNewGame').onclick=confirmNewGame;
  }

  function showAbout(){
    showModal('About',`<div class="about-intro">
        <p class="about-app-name">Tomb World Battle Guide</p>
        <p class="screen-version">Version ${APP_VERSION}</p>
        <p><strong>Created by J.R. Benning</strong></p>
        <p>Tomb World Battle Guide is a free, unofficial, fan-created companion for managing solo and two-player tabletop play. It is not a replacement for the official rules, publications, miniatures, terrain, cards, or other materials required to play.</p>
      </div>
      <div class="about-content">
        <section><h3>Project Status</h3><p>This project is provided without charge and is not operated for commercial gain.</p></section>
        <section><h3>Games Workshop Notice</h3><p>Tomb World Battle Guide is an unofficial fan-created project. It is not affiliated with, endorsed by, sponsored by, licensed by, or approved by Games Workshop Limited or any of its affiliates.</p><p>Games Workshop, Warhammer, Warhammer 40,000, Kill Team, Necron, Tomb World, and all associated names, logos, characters, factions, settings, artwork, and distinctive likenesses are trademarks, copyrights, or other intellectual property of Games Workshop Limited and/or its licensors.</p><p>All such intellectual property remains the property of its respective owners. No challenge to any ownership, trademark, copyright, or other proprietary right is intended.</p></section>
        <section><h3>Official Rules and Materials</h3><p>This application is intended only as an organizational and gameplay aid for players who own or otherwise have lawful access to the required official products and rules.</p><p>It does not grant access to, replace, or authorize reproduction of any Games Workshop rulebook, publication, data card, mission pack, image, artwork, model, terrain component, or other official material.</p><p>Players are responsible for consulting the current official rules, errata, balance updates, and publications. If this application conflicts with an official Games Workshop source, the official source controls.</p><p>No part of this application should be interpreted as legal permission to copy, distribute, publish, or commercially exploit Games Workshop intellectual property.</p></section>
        <section><h3>Project Content</h3><p>Original application code, interface design, and original project content are created by J.R. Benning except where otherwise stated.</p><p>Third-party names and references are used solely to identify the games, products, rules, and fictional elements with which this unofficial companion is intended to be used.</p><p>Any third-party material remains subject to the rights and terms of its respective owner.</p></section>
        <section><h3>Software Disclaimer</h3><p>This application is provided &quot;as is&quot; and &quot;as available,&quot; without warranties of any kind, express or implied, including warranties of accuracy, completeness, reliability, merchantability, fitness for a particular purpose, availability, compatibility, or non-infringement.</p><p>Use of this application is at the user’s own risk. The author does not guarantee that the application is error-free, that its interpretation of any rule is correct, or that saved data will always remain available or compatible.</p><p>To the fullest extent permitted by applicable law, the author will not be liable for any direct, indirect, incidental, consequential, special, exemplary, or other damages arising from use of, inability to use, or reliance on this application.</p><p>Nothing in this notice excludes or limits liability where doing so would be prohibited by applicable law.</p></section>
        <section><h3>User Responsibility</h3><p>Users are responsible for verifying gameplay decisions against the official rules and for ensuring that their use of this application and any related materials complies with applicable laws and the terms imposed by the relevant rights holders.</p></section>
        <section><h3>Privacy</h3><p>Tomb World Battle Guide does not intentionally collect or transmit personal information. Game state and preferences are stored locally in the user’s browser unless the user explicitly exports or shares them.</p><p class="muted">The app is hosted on GitHub Pages, whose server request logs are governed by GitHub’s own practices. The app uses no analytics, advertising, tracking, cookies, external fonts, or third-party APIs.</p></section>
        <section><h3>Contact</h3><p>Questions, corrections, attribution concerns, or rights-holder requests may be submitted through the project’s GitHub repository.</p><p>The author intends to address good-faith attribution, ownership, or rights-holder concerns promptly.</p><a class="btn secondary external-link" href="https://github.com/ImTheKeyMaster/TombWorldSoloGuide" target="_blank" rel="noopener noreferrer">Open Project Repository <span aria-hidden="true">↗</span><span class="sr-only"> (opens in a new tab)</span></a></section>
      </div>
      <div class="wizard-actions about-footer"><button class="btn primary" id="aboutBack" type="button">Back</button></div>`);
    $('#aboutBack').onclick=()=>{
      showGameMenu();
      requestAnimationFrame(()=>$('#menuAbout')?.focus({preventScroll:true}));
    };
  }

  function startNewGameSetup(){
    discardActiveManualDiceRequest();
    TombWorldNarration.stop();
    TombWorldAmbient.reset();
    TombWorldDiceSfx.stop();
    clearPendingBoardSetupMissionIntro();
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
  function exportSave(){
    if(objectiveEngine){
      const pendingDiceResults=state.missionRuntime?.pendingDiceResults;
      state.missionRuntime=objectiveEngine.getMissionRuntime();
      if(pendingDiceResults)state.missionRuntime.pendingDiceResults=pendingDiceResults;
    }
    const blob=new Blob([JSON.stringify(createPersistedSave(state),null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-battle-guide-save.json';a.click();URL.revokeObjectURL(a.href);
  }
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
    try{
      discardActiveManualDiceRequest();
      state=normalizeState(candidate);state.screen=report.requiresRegeneration?'setup':'game';await loadObjectiveMission();ensureGameBackgroundSelection();if(!save())throw new Error('Browser storage rejected the migrated save.');
      render();
      if(state.pendingDice)await resumePendingDiceWorkflow();
      else await resumeCheckpointedGameplayContext();
      return true;
    }
    catch(error){
      state=previous;await loadObjectiveMission();render();
      if(state.pendingDice)await resumePendingDiceWorkflow();
      else await resumeCheckpointedGameplayContext();
      console.warn('[Persistence] Migrated import was not committed.',error);showToast('The imported save could not be committed; the current game is unchanged.');return false;
    }
  }
  function showRegenerationNotice(migration,source){
    const causes=[...migration.report.unsupportedRetiredTypes,...migration.report.invalidPhysicalLimits,...migration.report.errors];
    showModal('Current battle cannot be resumed',`<p>The current battle uses retired or invalid NPO data and cannot be resumed safely.</p>${causes.length?`<p><strong>Cause:</strong> ${causes.map(escapeHtml).join('; ')}</p>`:''}<p>The battle will return to setup and a new legal NPO roster must be generated. The selected mission, player team and roster choices, completed battle history, settings, and preferences will be preserved where possible.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmLegacyReset">Return to Setup</button></div>`);
    $('#confirmLegacyReset').onclick=async()=>{
      const reset=resetActiveBattle(migration.state);closeModal();
      if(await commitImported(reset,{...migration.report,requiresRegeneration:true}))showToast(source==='import'?'Imported battle could not be resumed. Your setup choices were preserved.':'Previous battle could not be resumed. Your setup choices were preserved.');
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
    }catch(error){console.warn('[Persistence] Imported save could not be migrated; browser progress was left unchanged.',error);showToast(error.message?.includes('newer than supported')?'That save was created by a newer unsupported version.':'That file is not a valid Tomb World Battle Guide save.');}
    finally{importInput.value='';}
  });

  function bindCommon(){
    const versionBadge=$('.version');
    if(versionBadge) versionBadge.textContent=`v${APP_VERSION}`;
    gameMenuBtn.onclick=showGameMenu;
    syncNarrationControls();
    void TombWorldNarration.init();
  }

  function renderStartupRecovery(error){
    console.error('[Startup] Application restoration could not continue.',error);
    app.innerHTML=`<section class="card startup-recovery" role="alert"><p class="eyebrow">RECOVERY</p><h2>Your saved game could not be loaded</h2><p>Your stored save has been preserved. Retry loading, or export a backup before troubleshooting.</p><div class="wizard-actions"><button class="btn primary" id="retryStartup">Retry Loading</button><button class="btn ghost" id="exportStoredSave">Export Save</button></div></section>`;
    $('#retryStartup').onclick=()=>window.location.reload();
    $('#exportStoredSave').onclick=()=>{
      const stored=localStorage.getItem(STORAGE_KEY);
      if(!stored){showToast('No stored save is available to export.');return;}
      const blob=new Blob([stored],{type:'application/json'}),link=document.createElement('a');
      link.href=URL.createObjectURL(blob);link.download='tomb-world-battle-guide-recovery-save.json';link.click();URL.revokeObjectURL(link.href);
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
      if(state.pendingDice)await resumePendingDiceWorkflow();
      else await resumeCheckpointedGameplayContext();
      if(pendingStoredMigration)showRegenerationNotice(pendingStoredMigration,'storage');
      else if(!storedMigrationNoticeShown&&hasMeaningfulMigrationChanges(loadedSave?.report)){
        if(save()){storedMigrationNoticeShown=true;showMigrationNotice(loadedSave.report);}
      }
    })
    .catch(error=>{
      renderStartupRecovery(error);
    });
})();
