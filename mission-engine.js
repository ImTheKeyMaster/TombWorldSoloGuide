(function(global){
  'use strict';

  const DEFINITION_SCHEMA_VERSION=1;
  const RUNTIME_SCHEMA_VERSION=1;
  const HISTORY_LIMIT=50;
  const OPERATION_TYPES=new Set(['setCounter','addCounter','subtractCounter','setFlag','clearFlag','completeObjective','appendHistory','requestDiceRoll','requestNumericInput','showDialog']);
  const HOOK_NAMES=new Set(['onMissionInitialized','onStrategyPhaseReadyStep','onPlayerActivationStarted','onPlayerActivationCompleted','onNpoActivationStarted','onNpoActivationCompleted','onTurningPointEnded','onBattleEnded']);
  const CONDITION_OPERATORS=new Set(['==','!=','>','>=','<','<=','in','notIn','truthy','falsy']);
  const EXPRESSION_OPERATIONS=new Set(['add','subtract','multiply','min','max']);

  class MissionEngineError extends Error{
    constructor(code,message,details={}){super(message);this.name='MissionEngineError';this.code=code;this.details=details;}
  }

  const isRecord=value=>Boolean(value)&&typeof value==='object'&&!Array.isArray(value);
  const clone=value=>JSON.parse(JSON.stringify(value));
  const now=context=>typeof context?.now==='function'?context.now():new Date().toISOString();
  const fail=(code,path,reason,value)=>{throw new MissionEngineError(code,`${path}: ${reason}`,{path,reason,value});};
  const requireString=(value,path)=>{if(typeof value!=='string'||!value.trim())fail('INVALID_DEFINITION',path,'must be a non-empty string',value);};
  const requireFinite=(value,path)=>{if(typeof value!=='number'||!Number.isFinite(value))fail('INVALID_DEFINITION',path,'must be a finite number',value);};

  function validateCondition(condition,path='condition'){
    if(!isRecord(condition))fail('INVALID_CONDITION',path,'must be an object',condition);
    const groups=['all','any','not'].filter(key=>Object.prototype.hasOwnProperty.call(condition,key));
    if(groups.length){
      if(groups.length!==1||Object.keys(condition).length!==1)fail('INVALID_CONDITION',path,'must contain exactly one condition group',condition);
      if(groups[0]==='not')return validateCondition(condition.not,`${path}.not`);
      if(!Array.isArray(condition[groups[0]])||!condition[groups[0]].length)fail('INVALID_CONDITION',`${path}.${groups[0]}`,'must be a non-empty array',condition[groups[0]]);
      condition[groups[0]].forEach((item,index)=>validateCondition(item,`${path}.${groups[0]}[${index}]`));
      return;
    }
    requireString(condition.path,`${path}.path`);
    requireString(condition.operator,`${path}.operator`);
    if(!CONDITION_OPERATORS.has(condition.operator))fail('UNSUPPORTED_CONDITION_OPERATOR',`${path}.operator`,`unsupported operator "${condition.operator}"`,condition.operator);
    if(!['truthy','falsy'].includes(condition.operator)&&!Object.prototype.hasOwnProperty.call(condition,'value'))fail('INVALID_CONDITION',`${path}.value`,'is required',undefined);
  }

  function validateExpression(expression,path='expression'){
    if(typeof expression==='number'){if(!Number.isFinite(expression))fail('INVALID_EXPRESSION',path,'must be finite',expression);return;}
    if(isRecord(expression)&&typeof expression.path==='string'&&Object.keys(expression).length===1)return;
    if(!isRecord(expression)||!EXPRESSION_OPERATIONS.has(expression.operation))fail('INVALID_EXPRESSION',path,'has an unsupported expression operation',expression?.operation);
    if(!Array.isArray(expression.arguments)||!expression.arguments.length)fail('INVALID_EXPRESSION',`${path}.arguments`,'must be a non-empty array',expression.arguments);
    expression.arguments.forEach((argument,index)=>validateExpression(argument,`${path}.arguments[${index}]`));
  }

  function validateOperation(operation,path,objectiveIds){
    if(!isRecord(operation))fail('INVALID_DEFINITION',path,'must be an object',operation);
    requireString(operation.type,`${path}.type`);
    if(!OPERATION_TYPES.has(operation.type))fail('UNSUPPORTED_OPERATION',`${path}.type`,`unsupported operation "${operation.type}"`,operation.type);
    if(['setCounter','addCounter','subtractCounter','completeObjective'].includes(operation.type)){
      requireString(operation.objectiveId,`${path}.objectiveId`);
      if(!objectiveIds.has(operation.objectiveId))fail('INVALID_DEFINITION',`${path}.objectiveId`,'references an unknown objective',operation.objectiveId);
    }
    if(['setCounter','addCounter','subtractCounter'].includes(operation.type)){
      const sources=['value','valueFrom','valueExpression'].filter(key=>Object.prototype.hasOwnProperty.call(operation,key));
      if(sources.length!==1)fail('INVALID_DEFINITION',path,'counter operation requires exactly one value source',operation);
      if(sources[0]==='value')requireFinite(operation.value,`${path}.value`);
      if(sources[0]==='valueFrom')requireString(operation.valueFrom,`${path}.valueFrom`);
      if(sources[0]==='valueExpression')validateExpression(operation.valueExpression,`${path}.valueExpression`);
    }
    if(['setFlag','clearFlag'].includes(operation.type))requireString(operation.flag,`${path}.flag`);
    if(['requestDiceRoll','requestNumericInput'].includes(operation.type))requireString(operation.id,`${path}.id`);
    if(operation.type==='requestDiceRoll'){
      if(!isRecord(operation.dice))fail('INVALID_DEFINITION',`${path}.dice`,'must be an object',operation.dice);
      if(!Number.isInteger(operation.dice.count)||operation.dice.count<1)fail('INVALID_DEFINITION',`${path}.dice.count`,'must be a positive integer',operation.dice.count);
      if(operation.dice.sides!==6)fail('INVALID_DEFINITION',`${path}.dice.sides`,'only D6 dice are supported',operation.dice.sides);
    }
    if(operation.type==='requestNumericInput'){
      if(Object.prototype.hasOwnProperty.call(operation,'minimum'))requireFinite(operation.minimum,`${path}.minimum`);
      if(Object.prototype.hasOwnProperty.call(operation,'maximum'))requireFinite(operation.maximum,`${path}.maximum`);
      if(operation.minimum>operation.maximum)fail('INVALID_DEFINITION',path,'numeric input bounds are inconsistent',operation);
    }
  }

  function validateMissionDefinition(input,sourcePath='mission definition'){
    if(!isRecord(input))fail('INVALID_DEFINITION',sourcePath,'must contain a JSON object',input);
    const definition=clone(input);
    ['schemaVersion','id','slug','name','briefing','objectiveSummary','objectives','actions','hooks','completion','hud','dialogs','presentation'].forEach(field=>{
      if(!Object.prototype.hasOwnProperty.call(definition,field))fail('INVALID_DEFINITION',`${sourcePath}.${field}`,'is required',undefined);
    });
    ['id','slug','name','briefing','objectiveSummary'].forEach(field=>requireString(definition[field],`${sourcePath}.${field}`));
    if(definition.schemaVersion!==DEFINITION_SCHEMA_VERSION)fail('UNSUPPORTED_SCHEMA_VERSION',`${sourcePath}.schemaVersion`,`must equal ${DEFINITION_SCHEMA_VERSION}`,definition.schemaVersion);
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(definition.slug))fail('INVALID_DEFINITION',`${sourcePath}.slug`,'must be a lowercase hyphenated identifier',definition.slug);
    if(!Array.isArray(definition.objectives))fail('INVALID_DEFINITION',`${sourcePath}.objectives`,'must be an array',definition.objectives);
    const objectiveIds=new Set();
    definition.objectives.forEach((objective,index)=>{
      const path=`${sourcePath}.objectives[${index}]`;
      if(!isRecord(objective))fail('INVALID_DEFINITION',path,'must be an object',objective);
      requireString(objective.id,`${path}.id`);requireString(objective.type,`${path}.type`);requireString(objective.label,`${path}.label`);
      if(objectiveIds.has(objective.id))fail('DUPLICATE_OBJECTIVE_ID',`${path}.id`,'must be unique',objective.id);objectiveIds.add(objective.id);
      if(!['counter','boolean'].includes(objective.type))fail('INVALID_DEFINITION',`${path}.type`,'must be counter or boolean',objective.type);
      if(objective.type==='counter'){
        ['initial','minimum','maximum','target'].forEach(field=>requireFinite(objective[field],`${path}.${field}`));
        if(objective.minimum>objective.maximum||objective.initial<objective.minimum||objective.initial>objective.maximum||objective.target<objective.minimum||objective.target>objective.maximum)fail('INVALID_DEFINITION',path,'counter bounds are inconsistent',objective);
        validateCondition({path:'value',...(objective.completion||{})},`${path}.completion`);
      }else if(typeof objective.initial!=='boolean')fail('INVALID_DEFINITION',`${path}.initial`,'must be boolean',objective.initial);
    });
    if(!Array.isArray(definition.actions))fail('INVALID_DEFINITION',`${sourcePath}.actions`,'must be an array',definition.actions);
    const actionIds=new Set();
    definition.actions.forEach((action,index)=>{
      const path=`${sourcePath}.actions[${index}]`;requireString(action?.id,`${path}.id`);requireString(action?.label,`${path}.label`);
      if(actionIds.has(action.id))fail('DUPLICATE_ACTION_ID',`${path}.id`,'must be unique',action.id);actionIds.add(action.id);
      if(action.availability)validateCondition(action.availability,`${path}.availability`);
      if(!Array.isArray(action.operations))fail('INVALID_DEFINITION',`${path}.operations`,'must be an array',action.operations);
      action.operations.forEach((operation,operationIndex)=>validateOperation(operation,`${path}.operations[${operationIndex}]`,objectiveIds));
    });
    if(!isRecord(definition.hooks))fail('INVALID_DEFINITION',`${sourcePath}.hooks`,'must be an object',definition.hooks);
    Object.entries(definition.hooks).forEach(([hookName,events])=>{
      if(!HOOK_NAMES.has(hookName))fail('UNKNOWN_HOOK',`${sourcePath}.hooks.${hookName}`,'is not a supported hook',hookName);
      if(!Array.isArray(events))fail('INVALID_DEFINITION',`${sourcePath}.hooks.${hookName}`,'must be an array',events);
      events.forEach((event,index)=>{
        const path=`${sourcePath}.hooks.${hookName}[${index}]`;requireString(event?.id,`${path}.id`);
        if(event.availability)validateCondition(event.availability,`${path}.availability`);
        if(!Array.isArray(event.operations))fail('INVALID_DEFINITION',`${path}.operations`,'must be an array',event.operations);
        event.operations.forEach((operation,operationIndex)=>validateOperation(operation,`${path}.operations[${operationIndex}]`,objectiveIds));
      });
    });
    definition.completion=isRecord(definition.completion)?definition.completion:{};
    if(!Object.prototype.hasOwnProperty.call(definition.completion,'endsBattle'))definition.completion.endsBattle=false;
    if(typeof definition.completion.endsBattle!=='boolean')fail('INVALID_DEFINITION',`${sourcePath}.completion.endsBattle`,'must be boolean',definition.completion.endsBattle);
    definition.hud=isRecord(definition.hud)?definition.hud:{};definition.dialogs=isRecord(definition.dialogs)?definition.dialogs:{};definition.presentation=isRecord(definition.presentation)?definition.presentation:{};
    return definition;
  }

  async function createMissionRegistry(entries,fetchJson){
    if(!Array.isArray(entries))throw new MissionEngineError('INVALID_REGISTRY','Mission definition registry must be an array.');
    const loaded=[];const ids=new Set();
    for(const entry of entries){
      const path=typeof entry==='string'?entry:entry?.file;
      requireString(path,'mission definition path');
      let data;
      try{data=await fetchJson(path);}catch(error){throw new MissionEngineError('DEFINITION_LOAD_FAILED',`Unable to load ${path}: ${error.message}`,{path,cause:error});}
      const definition=validateMissionDefinition(data,path);
      if(ids.has(definition.id))throw new MissionEngineError('DUPLICATE_MISSION_ID',`Duplicate mission definition ID "${definition.id}".`,{path,missionId:definition.id});
      ids.add(definition.id);loaded.push({path,definition});
    }
    return {entries:loaded,resolve(missionId){return loaded.find(item=>item.definition.id===missionId||item.definition.slug===missionId)||null;}};
  }

  async function loadMissionDefinition(missionId,options={}){
    const fetchImpl=options.fetch||global.fetch;
    if(typeof fetchImpl!=='function')throw new MissionEngineError('FETCH_UNAVAILABLE','Mission definitions require the Fetch API.');
    const base=options.basePath||'Missions/';
    const fetchJson=async path=>{
      const response=await fetchImpl(path,{cache:'no-store'});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      try{return await response.json();}catch(error){throw new MissionEngineError('MALFORMED_JSON',`${path} contains malformed JSON.`,{path,cause:error});}
    };
    const manifest=options.manifest||await fetchJson(`${base}manifest.json`);
    const entries=options.entries||manifest.definitions;
    if(!Array.isArray(entries))throw new MissionEngineError('INVALID_REGISTRY','Missions/manifest.json has no definitions registry.');
    const registry=await createMissionRegistry(entries.map(entry=>typeof entry==='string'?`${base}${entry}`:`${base}${entry.file}`),fetchJson);
    const resolved=registry.resolve(missionId);
    if(!resolved)throw new MissionEngineError('UNKNOWN_MISSION_ID',`No mission definition is registered for "${missionId}".`,{missionId});
    return resolved.definition;
  }

  function safePath(root,path){
    if(typeof path!=='string'||!path||path.split('.').some(part=>!part||['__proto__','prototype','constructor'].includes(part)))throw new MissionEngineError('UNSAFE_PATH',`Unsafe mission context path "${path}".`,{path});
    let value=root;for(const part of path.split('.')){if(!isRecord(value)&&!Array.isArray(value))return undefined;value=value[part];}return value;
  }
  function evaluateCondition(condition,context){
    validateCondition(condition);
    if(condition.all)return condition.all.every(item=>evaluateCondition(item,context));
    if(condition.any)return condition.any.some(item=>evaluateCondition(item,context));
    if(condition.not)return !evaluateCondition(condition.not,context);
    const actual=safePath(context,condition.path),expected=condition.value;
    switch(condition.operator){case '==':return actual===expected;case '!=':return actual!==expected;case '>':return actual>expected;case '>=':return actual>=expected;case '<':return actual<expected;case '<=':return actual<=expected;case 'in':return Array.isArray(expected)&&expected.includes(actual);case 'notIn':return Array.isArray(expected)&&!expected.includes(actual);case 'truthy':return Boolean(actual);case 'falsy':return !actual;default:return false;}
  }
  function evaluateExpression(expression,context){
    validateExpression(expression);
    if(typeof expression==='number')return expression;
    if(expression.path)return safePath(context,expression.path);
    const values=expression.arguments.map(argument=>evaluateExpression(argument,context));
    if(values.some(value=>typeof value!=='number'||!Number.isFinite(value)))throw new MissionEngineError('INVALID_EXPRESSION_VALUE','Mission expression operands must resolve to finite numbers.');
    switch(expression.operation){case 'add':return values.reduce((sum,value)=>sum+value,0);case 'subtract':return values.slice(1).reduce((result,value)=>result-value,values[0]);case 'multiply':return values.reduce((result,value)=>result*value,1);case 'min':return Math.min(...values);case 'max':return Math.max(...values);default:return 0;}
  }

  function createMissionEngine(services={}){
    let definition=null,runtime=null;
    const objectiveDefinition=id=>definition?.objectives.find(objective=>objective.id===id)||null;
    const requireRuntime=()=>{if(!runtime||!definition)throw new MissionEngineError('MISSION_NOT_INITIALIZED','Mission runtime has not been initialized.');};
    const contextFor=context=>({mission:runtime,gameplay:isRecord(context?.gameplay)?context.gameplay:{},results:isRecord(context?.results)?context.results:{},inputs:isRecord(context?.inputs)?context.inputs:{}});
    const evaluateCompletion=(objective,state,context={})=>objective.type==='boolean'?Boolean(state.value):evaluateCondition({path:'value',...(objective.completion||{operator:'>=',value:objective.target})},{value:state.value,gameplay:context.gameplay||{}});
    function initializeMissionRuntime(nextDefinition,context={}){
      definition=validateMissionDefinition(nextDefinition);
      const timestamp=now(context);runtime={schemaVersion:RUNTIME_SCHEMA_VERSION,missionId:definition.id,initialized:true,objectives:{},flags:{},eventExecutions:{},history:[],lastUpdatedAt:timestamp};
      definition.objectives.forEach(objective=>{runtime.objectives[objective.id]={value:objective.initial,completed:false,completedAt:null};runtime.objectives[objective.id].completed=evaluateCompletion(objective,runtime.objectives[objective.id],context);if(runtime.objectives[objective.id].completed)runtime.objectives[objective.id].completedAt=timestamp;});
      return runtime;
    }
    function setObjectiveValue(objectiveId,value,metadata={}){
      requireRuntime();const objective=objectiveDefinition(objectiveId),state=runtime.objectives[objectiveId];
      if(!objective||!state)throw new MissionEngineError('UNKNOWN_OBJECTIVE',`Unknown mission objective "${objectiveId}".`);
      if(objective.lockOnComplete&&state.completed)return state.value;
      if(objective.type==='counter'&&(typeof value!=='number'||!Number.isFinite(value)))throw new MissionEngineError('INVALID_COUNTER_VALUE',`Counter "${objectiveId}" requires a finite number.`);
      if(objective.type==='boolean'&&typeof value!=='boolean')throw new MissionEngineError('INVALID_OBJECTIVE_VALUE',`Boolean objective "${objectiveId}" requires a boolean.`);
      state.value=objective.type==='counter'?Math.max(objective.minimum,Math.min(objective.maximum,value)):value;
      const completed=evaluateCompletion(objective,state,metadata);if(completed&&!state.completed){state.completed=true;state.completedAt=now(metadata);}runtime.lastUpdatedAt=now(metadata);return state.value;
    }
    function adjustObjectiveValue(objectiveId,delta,metadata={}){if(typeof delta!=='number'||!Number.isFinite(delta))throw new MissionEngineError('INVALID_COUNTER_VALUE','Counter adjustment requires a finite number.');return setObjectiveValue(objectiveId,getObjectiveValue(objectiveId)+delta,metadata);}
    function getObjectiveValue(objectiveId){requireRuntime();if(!runtime.objectives[objectiveId])throw new MissionEngineError('UNKNOWN_OBJECTIVE',`Unknown mission objective "${objectiveId}".`);return runtime.objectives[objectiveId].value;}
    function recordMissionHistory(entry,context={}){requireRuntime();const timestamp=now(context);runtime.history.push({id:entry.id||`mission-${Date.now()}-${runtime.history.length}`,timestamp,...clone(entry)});runtime.history=runtime.history.slice(-HISTORY_LIMIT);runtime.lastUpdatedAt=timestamp;return runtime.history.at(-1);}
    const operationValue=(operation,eventContext)=>Object.prototype.hasOwnProperty.call(operation,'value')?operation.value:operation.valueFrom?safePath(eventContext,operation.valueFrom):evaluateExpression(operation.valueExpression,eventContext);
    async function executeEvent(event,context={}){
      requireRuntime();event.operations.forEach((operation,index)=>validateOperation(operation,`event.operations[${index}]`,new Set(definition.objectives.map(objective=>objective.id))));
      if(event.availability&&!evaluateCondition(event.availability,contextFor(context)))return {status:'unavailable'};
      const scope=event.oncePer||'unlimited',scopeValue=scope==='game'?'game':scope==='turningPoint'?context.turningPoint:scope==='activation'?context.activationId:null;
      if(!['unlimited','manual'].includes(scope)&&scopeValue==null)throw new MissionEngineError('MISSING_IDEMPOTENCY_CONTEXT',`Event "${event.id}" requires ${scope} context.`);
      const executionKey=!['unlimited','manual'].includes(scope)?`${event.executionKey||event.id}:${scope}:${scopeValue}`:null;
      if(executionKey&&runtime.eventExecutions[executionKey])return {status:'already-executed',executionKey};
      const snapshot=clone(runtime),eventContext=contextFor(context),pendingHistory=[];
      try{
        for(const operation of event.operations){
          switch(operation.type){
            case 'setCounter':setObjectiveValue(operation.objectiveId,operationValue(operation,eventContext),context);break;
            case 'addCounter':adjustObjectiveValue(operation.objectiveId,operationValue(operation,eventContext),context);break;
            case 'subtractCounter':adjustObjectiveValue(operation.objectiveId,-operationValue(operation,eventContext),context);break;
            case 'setFlag':runtime.flags[operation.flag]=Object.prototype.hasOwnProperty.call(operation,'value')?clone(operation.value):true;break;
            case 'clearFlag':delete runtime.flags[operation.flag];break;
            case 'completeObjective':{const objective=runtime.objectives[operation.objectiveId];objective.completed=true;objective.completedAt=now(context);break;}
            case 'appendHistory':pendingHistory.push(operation.entry||{title:event.label||event.id,summary:operation.summary||''});break;
            case 'requestDiceRoll':{
              if(typeof services.requestDiceRoll!=='function')throw new MissionEngineError('SERVICE_UNAVAILABLE','Dice roll service is unavailable.');
              const result=await services.requestDiceRoll(clone(operation),context);
              if(!isRecord(result)||typeof result.total!=='number'||!Number.isFinite(result.total)||!Array.isArray(result.dice)||result.dice.length!==operation.dice.count)throw new MissionEngineError('INVALID_DICE_RESULT','Dice service returned an invalid result.');
              eventContext.results[operation.id]=clone(result);break;
            }
            case 'requestNumericInput':{
              if(typeof services.requestNumericInput!=='function')throw new MissionEngineError('SERVICE_UNAVAILABLE','Numeric input service is unavailable.');
              const value=await services.requestNumericInput(clone(operation),context);
              if(typeof value!=='number'||!Number.isFinite(value)||(operation.integer&&!Number.isInteger(value))||(Number.isFinite(operation.minimum)&&value<operation.minimum)||(Number.isFinite(operation.maximum)&&value>operation.maximum))throw new MissionEngineError('INVALID_NUMERIC_INPUT','Numeric input service returned an invalid value.');
              eventContext.inputs[operation.id]=value;break;
            }
            case 'showDialog':{if(typeof services.showDialog!=='function')throw new MissionEngineError('SERVICE_UNAVAILABLE','Dialog service is unavailable.');await services.showDialog(clone(operation),context);break;}
          }
        }
        if(executionKey)runtime.eventExecutions[executionKey]={completed:true,completedAt:now(context)};
        const history=pendingHistory.length?pendingHistory:[{eventId:event.id,title:event.label||event.id,summary:event.history?.summary||`${event.label||event.id} completed.`}];
        history.forEach(entry=>recordMissionHistory({...entry,eventId:entry.eventId||event.id,turningPoint:context.turningPoint??null,phase:context.phase||null},context));
        return {status:'completed',executionKey,results:eventContext.results,inputs:eventContext.inputs};
      }catch(error){runtime=snapshot;throw error;}
    }
    async function executeMissionAction(actionId,context={}){requireRuntime();const action=definition.actions.find(item=>item.id===actionId);if(!action)throw new MissionEngineError('UNKNOWN_ACTION',`Unknown mission action "${actionId}".`);return executeEvent(action,context);}
    async function executeMissionHook(hookName,context={}){requireRuntime();if(!HOOK_NAMES.has(hookName))throw new MissionEngineError('UNKNOWN_HOOK',`Unknown mission hook "${hookName}".`);const outcomes=[];for(const event of definition.hooks[hookName]||[])outcomes.push(await executeEvent(event,context));return outcomes;}
    function evaluateMissionConditions(trigger,context={}){requireRuntime();return trigger?evaluateCondition(trigger,contextFor(context)):true;}
    function evaluateObjectiveCompletion(context={}){requireRuntime();definition.objectives.forEach(objective=>setObjectiveValue(objective.id,runtime.objectives[objective.id].value,context));return Object.fromEntries(Object.entries(runtime.objectives).map(([id,state])=>[id,state.completed]));}
    function getMissionHudModel(){requireRuntime();const objective=definition.objectives[0],state=objective?runtime.objectives[objective.id]:null;return {missionId:definition.id,name:definition.name,label:definition.hud.label||'MISSION',objectiveId:objective?.id||null,value:state?.value??null,target:objective?.target??null,completed:Boolean(state?.completed),visible:definition.presentation.showHud!==false};}
    function getMissionDetailsModel(){requireRuntime();return {missionId:definition.id,name:definition.name,briefing:definition.briefing,objectiveSummary:definition.objectiveSummary,objectives:definition.objectives.map(objective=>({...clone(objective),...clone(runtime.objectives[objective.id])})),history:clone(runtime.history).reverse(),completion:clone(definition.completion)};}
    return {initializeMissionRuntime,getMissionRuntime:()=>runtime,getMissionDefinition:()=>definition,getObjectiveValue,setObjectiveValue,adjustObjectiveValue,evaluateMissionConditions,executeMissionAction,executeMissionHook,evaluateObjectiveCompletion,recordMissionHistory,getMissionHudModel,getMissionDetailsModel};
  }

  global.TombWorldMissionEngine={MissionEngineError,validateMissionDefinition,createMissionRegistry,loadMissionDefinition,evaluateCondition,evaluateExpression,createMissionEngine,constants:{DEFINITION_SCHEMA_VERSION,RUNTIME_SCHEMA_VERSION,HISTORY_LIMIT}};
})(typeof window!=='undefined'?window:globalThis);
