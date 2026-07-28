(function(root){
  'use strict';

  const SAVE_VERSION = 3;
  const NON_PERSISTED_FIELDS = new Set(['temporaryUiState','cachedHtml','domReferences','migrationReport']);
  const OBSOLETE_NPO_PORTRAIT_FIELDS = new Set(['portrait','portraitUrl','portraitPath','image','imageUrl','imagePath','thumbnail']);
  const OBSOLETE_MATRIX_FIELDS = new Set([
    'obeliskNodeMatrix','obeliskMatrix','nodeMatrix','obeliskNode','obeliskNodes',
    'nodeMarker','nodeMarkers','withinMatrix','insideMatrix','matrixBonus','matrixActive',
    'matrixRange','matrixTargeting','matrixControl','matrixPowered','matrixEnhanced',
    'matrixDerivedApl','matrixWeaponModifiers','matrixActionTargets','matrixMovementHistory',
    'pendingMatrixQuestion','matrixUiStep'
  ]);
  // This is the only superseded type name present in repository history.
  const LEGACY_TYPE_ALIASES = Object.freeze({
    'canoptek macrocyte':'Canoptek Macrocyte Warrior'
  });
  // Repository history contains no other named retired catalog entry. Unknown legacy
  // identities are still reported explicitly and can never be guessed into this set.
  const RETIRED_NPO_TYPES = Object.freeze([]);
  const isRecord = value => Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  const clone = value => JSON.parse(JSON.stringify(value));
  const integer = (value,fallback=0) => Number.isFinite(Number(value))?Math.max(0,Math.round(Number(value))):fallback;
  const records = value => Array.isArray(value)?value.filter(isRecord):[];
  const strings = value => Array.isArray(value)?[...new Set(value.filter(item=>typeof item==='string'&&item))]:[];
  const normalizedName = value => String(value||'').trim().replace(/\s+/g,' ').toLocaleLowerCase('en');

  function currentSaveVersion(){return SAVE_VERSION;}
  function migrate0to1(save){return {...save,saveVersion:1};}

  const matrixRule = value => typeof value==='string'&&/(?:obelisk|matrix|node-control)/i.test(value);
  function withoutFields(value,fields,reportKey,report){
    if(!isRecord(value))return value;
    const result={};
    Object.entries(value).forEach(([field,item])=>{
      if(fields.has(field)){if(report)report[reportKey]++;return;}
      result[field]=item;
    });
    return result;
  }
  function stripObsoleteMatrixState(save,report){
    const cleaned=withoutFields(save,OBSOLETE_MATRIX_FIELDS,'matrixFieldsRemoved',report);
    cleaned.roster=records(cleaned.roster).map(item=>withoutFields(item,OBSOLETE_MATRIX_FIELDS,'matrixFieldsRemoved',report));
    if(isRecord(cleaned.npoRuleState)){
      const ruleState=withoutFields(cleaned.npoRuleState,OBSOLETE_MATRIX_FIELDS,'matrixFieldsRemoved',report);
      ruleState.aplModifiers=records(ruleState.aplModifiers).filter(modifier=>{
        const keep=!matrixRule(modifier.ruleId)&&!matrixRule(modifier.id);
        if(!keep&&report)report.temporaryEffectsRemoved++;
        return keep;
      });
      ruleState.pendingMovementEffects=records(ruleState.pendingMovementEffects).filter(effect=>{
        const keep=!matrixRule(effect.ruleId)&&!matrixRule(effect.id);
        if(!keep&&report)report.temporaryEffectsRemoved++;
        return keep;
      });
      ruleState.oncePerTurningPoint=isRecord(ruleState.oncePerTurningPoint)
        ? Object.fromEntries(Object.entries(ruleState.oncePerTurningPoint).filter(([ruleId])=>!matrixRule(ruleId))) : {};
      cleaned.npoRuleState=ruleState;
    }
    return cleaned;
  }
  function migrate1to2(save,report){return {...stripObsoleteMatrixState(save,report),saveVersion:2};}
  function migrate2to3(save){return {...save,saveVersion:3};}
  const migrations = {0:migrate0to1,1:migrate1to2,2:migrate2to3};

  function migrationReport(sourceVersion){
    return {sourceVersion,targetVersion:SAVE_VERSION,outcome:'current',aliasesApplied:[],instanceIdsCreated:[],instanceIdsRepaired:[],loadoutsNormalized:[],woundsClamped:[],portraitFieldsRemoved:0,matrixFieldsRemoved:0,unsupportedRetiredTypes:[],invalidPhysicalLimits:[],temporaryEffectsRemoved:0,pendingStateCleared:[],requiresRegeneration:false,completedHistoryPreserved:true,warnings:[],errors:[]};
  }
  function canonicalCatalog(catalog){
    if(!isRecord(catalog)||!Object.keys(catalog).length)throw new TypeError('The authoritative NPO catalog is required.');
    return catalog;
  }
  function resolveLegacyNpoType(legacy,catalog){
    catalog=canonicalCatalog(catalog);
    const stableId=normalizedName(legacy?.typeId||legacy?.npoTypeId);
    if(stableId){
      const match=Object.values(catalog).find(entry=>normalizedName(entry.id)===stableId);
      if(match)return {supported:true,type:match.type,matchedBy:'id'};
    }
    const rawType=legacy?.type;
    if(typeof rawType==='string'&&catalog[rawType])return {supported:true,type:rawType,matchedBy:'type'};
    const candidate=normalizedName(rawType||legacy?.name);
    const canonical=Object.values(catalog).find(entry=>normalizedName(entry.type)===candidate||normalizedName(entry.name)===candidate);
    if(canonical)return {supported:true,type:canonical.type,matchedBy:'name'};
    const alias=LEGACY_TYPE_ALIASES[candidate];
    if(alias&&catalog[alias])return {supported:true,type:alias,matchedBy:'alias',alias:candidate};
    return {supported:false,type:null,legacyType:String(rawType||legacy?.name||'Unknown NPO')};
  }
  function deterministicId(type,index){
    return `legacy-${normalizedName(type).replace(/[^a-z0-9]+/g,'-')}-${index+1}`;
  }
  function legacyLoadout(npo,definition){
    const candidate=normalizedName(npo.weaponId||npo.loadoutId||npo.loadout||npo.weapon||npo.weaponName);
    if(!definition.loadoutOptions)return definition.defaultWeaponId;
    const option=definition.loadoutOptions.find(item=>normalizedName(item.id)===candidate||normalizedName(item.name)===candidate||normalizedName(item.name).startsWith(candidate));
    return option?.id||definition.defaultWeaponId;
  }
  function normalizeActiveRoster(save,catalog,report){
    const seenIds=new Map(), roster=records(save.roster);
    const normalized=roster.map((original,index)=>{
      let npo=withoutFields(withoutFields(original,OBSOLETE_NPO_PORTRAIT_FIELDS,'portraitFieldsRemoved',report),OBSOLETE_MATRIX_FIELDS,'matrixFieldsRemoved',report);
      const resolution=resolveLegacyNpoType(npo,catalog);
      if(!resolution.supported){report.unsupportedRetiredTypes.push(resolution.legacyType);report.requiresRegeneration=true;return npo;}
      const definition=catalog[resolution.type];
      if(resolution.type!==npo.type||npo.name!==definition.name){report.aliasesApplied.push({from:String(npo.type||npo.name||''),to:resolution.type});npo.type=resolution.type;}
      npo.name=definition.name;
      if(typeof npo.id!=='string'||!npo.id){npo.id=deterministicId(npo.type,index);report.instanceIdsCreated.push(npo.id);}
      if(seenIds.has(npo.id)){
        const previous=seenIds.get(npo.id);
        if(previous.type!==npo.type||previous.weaponId&&npo.weaponId&&previous.weaponId!==npo.weaponId){report.requiresRegeneration=true;report.errors.push(`Conflicting NPO instance ID ${npo.id}.`);}
        else {report.requiresRegeneration=true;report.errors.push(`Duplicate roster record for NPO instance ${npo.id}.`);}
      }else seenIds.set(npo.id,npo);
      const weaponId=legacyLoadout(npo,definition);
      if(npo.weaponId!==weaponId){report.loadoutsNormalized.push({id:npo.id,from:npo.weaponId||null,to:weaponId});npo.weaponId=weaponId;}
      const maximum=definition.wounds;
      const numeric=Number(npo.wounds);
      const wounds=Number.isFinite(numeric)?Math.min(maximum,Math.max(0,numeric)):maximum;
      if(Number.isFinite(numeric)&&wounds!==numeric)report.woundsClamped.push({id:npo.id,from:numeric,to:wounds});
      npo.wounds=wounds;npo.maxWounds=maximum;npo.move=definition.move;npo.apl=definition.apl;npo.save=definition.save;npo.baseSize=definition.baseSize;
      return npo;
    });
    const used={};
    normalized.forEach(npo=>{
      const definition=catalog[npo.type];if(!definition)return;
      if(definition.physicalQuantity<=1){npo.displayNumber=null;return;}
      const numbers=used[npo.type]||(used[npo.type]=new Set());
      if(Number.isInteger(npo.displayNumber)&&npo.displayNumber>0&&!numbers.has(npo.displayNumber)){numbers.add(npo.displayNumber);return;}
      let number=1;while(numbers.has(number))number++;npo.displayNumber=number;numbers.add(number);
    });
    return normalized;
  }
  function validateAllocation(roster,catalog,report){
    const ids=new Set(),counts={};
    roster.forEach(npo=>{
      if(!catalog[npo.type])return;
      if(ids.has(npo.id))return;ids.add(npo.id);counts[npo.type]=(counts[npo.type]||0)+1;
    });
    Object.entries(counts).forEach(([type,count])=>{
      const definition=catalog[type];
      const living=roster.filter(npo=>npo.type===type&&npo.wounds>0).length;
      const scuttling=type==='Canoptek Macrocyte Warrior'
        && living<=definition.physicalQuantity
        && count-definition.physicalQuantity<=roster.filter(npo=>npo.type===type&&npo.createdBy==='a-ceaseless-scuttling').length;
      if(count>definition.physicalQuantity&&!scuttling)report.invalidPhysicalLimits.push(`${type}: ${count} of ${definition.physicalQuantity}`);
    });
    const isolators=roster.filter(npo=>npo.type==='Canoptek Tomb Crawler'&&npo.weaponId==='transdimensional-isolator').length;
    if(isolators>1)report.invalidPhysicalLimits.push('Canoptek Tomb Crawler: more than one transdimensional isolator');
    if(report.invalidPhysicalLimits.length)report.requiresRegeneration=true;
  }
  function normalizeRuleState(save,roster,report){
    if(!isRecord(save.npoRuleState))return;
    const ids=new Set(roster.filter(npo=>npo.id&&npo.wounds>=0).map(npo=>npo.id));
    const unique=(items,key)=>{
      const seen=new Set();return records(items).filter(item=>{
        const references=['sourceId','targetId'].filter(field=>item[field]);
        const valid=references.every(field=>ids.has(item[field]));
        const signature=JSON.stringify(key(item));
        const keep=valid&&!matrixRule(item.ruleId)&&!seen.has(signature);
        if(!keep)report.temporaryEffectsRemoved++;
        if(keep)seen.add(signature);return keep;
      });
    };
    save.npoRuleState.aplModifiers=unique(save.npoRuleState.aplModifiers,item=>[item.sourceId,item.targetId,item.ruleId,item.amount,item.expires]);
    save.npoRuleState.pendingMovementEffects=unique(save.npoRuleState.pendingMovementEffects,item=>[item.sourceId,item.targetId,item.ruleId,item.expires]);
  }
  function clearUnsafePendingState(save,roster,report){
    const ids=new Set(roster.map(npo=>npo.id));
    const unsafe=(value)=>isRecord(value)&&['npoId','targetId','sourceId','operativeId'].some(field=>value[field]&&!ids.has(value[field]));
    ['lastActivation','npoAttackSummary','combatState'].forEach(field=>{
      if(unsafe(save[field])){save[field]=null;report.pendingStateCleared.push(field);}
    });
    if(report.pendingStateCleared.length){save.activeNpoId=null;save.npoAttackTargetId=null;}
  }
  function resetActiveBattle(save){
    const completedJournal=save.completed||save.gameEnd?records(save.journal):[];
    return {...save,screen:'setup',tab:'play',setupStep:0,setupChecks:{},restlessTombEnabled:false,deadlyEncountersEnabled:false,deadlyEncountersState:null,roster:[],playerRosterInitializedForTeamId:'',turningPoint:0,threat:0,tracker:0,phase:'setup',initiative:'player',nextSide:'player',playerDeployed:false,playerActivatedIds:[],playerCasualtyIds:[],playerWounds:{},playerOperativeStates:{},playerReady:0,activeNpoId:null,lastActivation:null,npoAttackTargetId:null,npoAttackSummary:null,combatState:null,journal:completedJournal,activationHistory:[],activationNumber:0,totalActivationsThisTP:0,playerActivated:0,npoActivated:0,reinforcementState:{turningPoint:0,status:'idle',operativeIds:[],blockedOperativeIds:[],blocked:0},strategyStage:null,strategyData:null,strategyPipeline:null,missionState:null,missionRuntime:null,missionReadyContext:{sarcophagusControllers:0},npoRuleState:{aplModifiers:[],pendingMovementEffects:[],oncePerTurningPoint:{},reanimatedTargetIds:[],incapacitationTriggers:[]},startingNpoGeneration:null,eventState:{},gameEnd:null,completed:false};
  }

  function normalizeSave(save){
    save=stripObsoleteMatrixState(save);
    const normalized={...save};
    normalized.restlessTombEnabled=save.restlessTombEnabled===true;
    normalized.deadlyEncountersEnabled=save.deadlyEncountersEnabled===true;
    normalized.deadlyEncountersState=isRecord(save.deadlyEncountersState)?clone(save.deadlyEncountersState):null;
    normalized.roster=records(save.roster);normalized.playerRoster=strings(save.playerRoster);
    const importedPlayerStates=isRecord(save.playerOperativeStates)?save.playerOperativeStates:{};
    normalized.playerOperativeStates=Object.fromEntries(normalized.playerRoster.map(id=>{const value=isRecord(importedPlayerStates[id])?importedPlayerStates[id]:{};return [id,{...value,inPlay:value.inPlay!==false,...(typeof value.offBoardReason==='string'&&value.offBoardReason?{offBoardReason:value.offBoardReason}:{})}];}));
    normalized.journal=records(save.journal);normalized.activationHistory=Array.isArray(save.activationHistory)?save.activationHistory:[];
    normalized.playerActivatedIds=strings(save.playerActivatedIds).filter(id=>normalized.playerRoster.includes(id));normalized.playerCasualtyIds=strings(save.playerCasualtyIds).filter(id=>normalized.playerRoster.includes(id));
    normalized.playerWounds=isRecord(save.playerWounds)?{...save.playerWounds}:{};normalized.setupChecks=isRecord(save.setupChecks)?{...save.setupChecks}:{};normalized.missionState=isRecord(save.missionState)?{...save.missionState}:{};normalized.missionRuntime=isRecord(save.missionRuntime)?{...save.missionRuntime}:null;normalized.strategyData=isRecord(save.strategyData)?{...save.strategyData}:null;normalized.eventState=isRecord(save.eventState)?{...save.eventState}:{};normalized.reinforcementState=isRecord(save.reinforcementState)?{...save.reinforcementState}:{};
    ['setupStep','playerCount','playerReady','turningPoint','threat','tracker','activationNumber','totalActivationsThisTP','playerActivated','npoActivated','tpStartThreat','tpStartGrade','tpStartDestroyedNpos','tpStartPlayerCasualties'].forEach(field=>{normalized[field]=integer(save[field]);});
    const rosterIds=new Set(normalized.roster.map(item=>item.id).filter(id=>typeof id==='string'&&id));normalized.newIds=strings(save.newIds).filter(id=>rosterIds.has(id));normalized.reinforcementState.operativeIds=strings(normalized.reinforcementState.operativeIds).filter(id=>rosterIds.has(id));normalized.reinforcementState.blockedOperativeIds=strings(normalized.reinforcementState.blockedOperativeIds).filter(id=>rosterIds.has(id)&&!normalized.reinforcementState.operativeIds.includes(id));
    return normalized;
  }
  function migrateSaveDetailed(input,catalog){
    if(!isRecord(input))throw new TypeError('Saved game must be an object.');
    catalog=canonicalCatalog(catalog);let migrated=clone(input);let version=migrated.saveVersion===undefined?0:migrated.saveVersion;
    if(!Number.isInteger(version)||version<0)throw new TypeError('Saved game has an invalid saveVersion.');
    if(version>SAVE_VERSION)throw new Error(`Save schema ${version} is newer than supported schema ${SAVE_VERSION}.`);
    const report=migrationReport(version);
    while(version<SAVE_VERSION){
      const migration=migrations[version];if(typeof migration!=='function')throw new Error(`No migration is available from save schema ${version}.`);
      migrated=migration(migrated,report);
      if(!Number.isInteger(migrated.saveVersion)||migrated.saveVersion<=version)throw new Error(`Migration from save schema ${version} did not advance the version.`);
      version=migrated.saveVersion;
    }
    migrated=stripObsoleteMatrixState(migrated,report);migrated.roster=normalizeActiveRoster(migrated,catalog,report);validateAllocation(migrated.roster,catalog,report);normalizeRuleState(migrated,migrated.roster,report);clearUnsafePendingState(migrated,migrated.roster,report);
    report.unsupportedRetiredTypes=[...new Set(report.unsupportedRetiredTypes)];
    report.outcome=report.requiresRegeneration?'regeneration-required':(report.aliasesApplied.length||report.instanceIdsCreated.length||report.loadoutsNormalized.length||report.woundsClamped.length||report.portraitFieldsRemoved||report.matrixFieldsRemoved||report.temporaryEffectsRemoved||report.pendingStateCleared.length?'migrated':'current');
    return {state:normalizeSave(migrated),report};
  }
  function migrateSave(save,catalog){
    if(catalog)return migrateSaveDetailed(save,catalog).state;
    if(!isRecord(save))throw new TypeError('Saved game must be an object.');
    let migrated=clone(save),version=migrated.saveVersion===undefined?0:migrated.saveVersion;
    if(!Number.isInteger(version)||version<0)throw new TypeError('Saved game has an invalid saveVersion.');
    if(version>SAVE_VERSION)throw new Error(`Save schema ${version} is newer than supported schema ${SAVE_VERSION}.`);
    while(version<SAVE_VERSION){
      const migration=migrations[version];if(!migration)throw new Error(`No migration is available from save schema ${version}.`);
      migrated=migration(migrated);
      if(!Number.isInteger(migrated.saveVersion)||migrated.saveVersion<=version)throw new Error(`Migration from save schema ${version} did not advance the version.`);
      version=migrated.saveVersion;
    }
    return normalizeSave(migrated);
  }
  function createPersistedSave(state){
    if(!isRecord(state))throw new TypeError('Game state must be an object.');
    const gameplayState=Object.fromEntries(Object.entries(state).filter(([field])=>!NON_PERSISTED_FIELDS.has(field)));
    const cleaned=stripObsoleteMatrixState(clone(gameplayState));
    cleaned.roster=records(cleaned.roster).map(item=>withoutFields(item,OBSOLETE_NPO_PORTRAIT_FIELDS));
    return {...cleaned,saveVersion:SAVE_VERSION};
  }

  const api={currentSaveVersion,migrateSave,migrateSaveDetailed,createPersistedSave,resetActiveBattle,resolveLegacyNpoType,LEGACY_TYPE_ALIASES,RETIRED_NPO_TYPES,migrations};
  root.TombWorldPersistence=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
