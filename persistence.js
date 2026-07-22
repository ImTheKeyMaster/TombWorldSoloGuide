(function(root){
  'use strict';

  const SAVE_VERSION = 1;
  const isRecord = value => Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  const clone = value => JSON.parse(JSON.stringify(value));
  const integer = (value,fallback=0) => Number.isFinite(Number(value))?Math.max(0,Math.round(Number(value))):fallback;
  const records = value => Array.isArray(value)?value.filter(isRecord):[];
  const strings = value => Array.isArray(value)?[...new Set(value.filter(item=>typeof item==='string'&&item))]:[];

  function currentSaveVersion(){return SAVE_VERSION;}

  function migrate0to1(save){
    return {...save,saveVersion:1};
  }

  const migrations = {0:migrate0to1};

  function normalizeSave(save){
    const normalized={...save};
    normalized.roster=records(save.roster);
    normalized.playerRoster=strings(save.playerRoster);
    normalized.journal=records(save.journal);
    normalized.activationHistory=Array.isArray(save.activationHistory)?save.activationHistory:[];
    normalized.playerActivatedIds=strings(save.playerActivatedIds).filter(id=>normalized.playerRoster.includes(id));
    normalized.playerCasualtyIds=strings(save.playerCasualtyIds).filter(id=>normalized.playerRoster.includes(id));
    normalized.playerWounds=isRecord(save.playerWounds)?{...save.playerWounds}:{};
    normalized.setupChecks=isRecord(save.setupChecks)?{...save.setupChecks}:{};
    normalized.missionState=isRecord(save.missionState)?{...save.missionState}:{};
    normalized.missionRuntime=isRecord(save.missionRuntime)?{...save.missionRuntime}:null;
    normalized.strategyData=isRecord(save.strategyData)?{...save.strategyData}:null;
    normalized.eventState=isRecord(save.eventState)?{...save.eventState}:{};
    normalized.reinforcementState=isRecord(save.reinforcementState)?{...save.reinforcementState}:{};
    [
      'setupStep','playerCount','playerReady','turningPoint','threat','tracker',
      'activationNumber','totalActivationsThisTP','playerActivated','npoActivated',
      'tpStartThreat','tpStartGrade','tpStartDestroyedNpos','tpStartPlayerCasualties'
    ].forEach(field=>{normalized[field]=integer(save[field]);});

    const rosterIds=new Set(normalized.roster.map(item=>item.id).filter(id=>typeof id==='string'&&id));
    normalized.newIds=strings(save.newIds).filter(id=>rosterIds.has(id));
    normalized.reinforcementState.operativeIds=strings(normalized.reinforcementState.operativeIds).filter(id=>rosterIds.has(id));
    normalized.reinforcementState.blockedOperativeIds=strings(normalized.reinforcementState.blockedOperativeIds)
      .filter(id=>rosterIds.has(id)&&!normalized.reinforcementState.operativeIds.includes(id));
    return normalized;
  }

  function migrateSave(save){
    if(!isRecord(save))throw new TypeError('Saved game must be an object.');
    let migrated=clone(save);
    let version=migrated.saveVersion===undefined?0:migrated.saveVersion;
    if(!Number.isInteger(version)||version<0)throw new TypeError('Saved game has an invalid saveVersion.');
    if(version>currentSaveVersion()){
      console.warn(`[Persistence] Save schema ${version} is newer than supported schema ${currentSaveVersion()}; preserving unknown fields.`);
      return normalizeSave(migrated);
    }
    while(version<currentSaveVersion()){
      const migration=migrations[version];
      if(typeof migration!=='function')throw new Error(`No migration is available from save schema ${version}.`);
      migrated=migration(migrated);
      const nextVersion=migrated.saveVersion;
      if(!Number.isInteger(nextVersion)||nextVersion<=version)throw new Error(`Migration from save schema ${version} did not advance the version.`);
      version=nextVersion;
    }
    return normalizeSave(migrated);
  }

  function createPersistedSave(state){
    if(!isRecord(state))throw new TypeError('Game state must be an object.');
    return {...clone(state),saveVersion:currentSaveVersion()};
  }

  const api={currentSaveVersion,migrateSave,createPersistedSave,migrations};
  root.TombWorldPersistence=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
