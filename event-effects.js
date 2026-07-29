(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.TombWorldEventEffects=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const HANDLERS={
    'dark-of-the-tomb':{
      attackRerolls(context){
        if(context.attackerSide!=='player'||context.attackType!=='shoot'||context.moreThanEight!==true)return context;
        return {...context,attackDice:false,messages:[...(context.messages||[]),'Dark of the Tomb: Attack dice cannot be rerolled at this distance.']};
      }
    },
    'my-will-be-done':{
      effectiveWeapon(context){
        if(context.attackerSide!=='npo'||context.sameRoomAsC1!==true)return context;
        const profile={...context.profile,rules:[...(context.profile?.rules||[])]};
        if(!profile.rules.some(rule=>/^Accurate\s+1$/i.test(String(rule))))profile.rules.push('Accurate 1');
        profile.accurate=Math.max(1,Number(profile.accurate||0));
        return {...context,profile,messages:[...(context.messages||[]),'My Will Be Done: This NPO has Accurate 1.']};
      }
    },
    'countertemporal-shifting':{
      damagePackets(context){
        if(context.attackerSide!=='player'||context.defenderSide!=='npo'||!['shoot','melee'].includes(context.attackType))return context;
        const rollD6=context.rollD6||(()=>Math.floor(Math.random()*6)+1);
        const packets=(context.packets||[]).map((packet,index)=>{
          const originalDamage=Math.max(0,Number(packet.originalDamage??packet.damage)||0);
          if(originalDamage<3)return {...packet,originalDamage,finalDamage:originalDamage};
          const saved=context.savedRolls?.[index];
          const roll=Number.isInteger(saved)?saved:rollD6();
          return {...packet,originalDamage,countertemporalRoll:roll,finalDamage:Math.max(0,originalDamage-(roll>=5?1:0))};
        });
        return {...context,packets,messages:[...(context.messages||[]),'Countertemporal Shifting: Resolve one D6 for each qualifying attack die.']};
      }
    },
    'reanimation-protocols':{
      incapacitationCandidates(context){
        const consumed=context.eventAttempts?.[`${context.turningPoint}:${context.npoId}`];
        if(consumed)return context;
        return {...context,candidates:[...(context.candidates||[]),{sourceId:'tomb-world-event:reanimation-protocols',priority:10}]};
      }
    }
  };

  function activeRecords(state,turningPoint){
    return (state?.eventState?.active||[]).filter(record=>record&&record.definitionId&&record.startedTurningPoint===turningPoint&&record.expiresAfterTurningPoint>=turningPoint);
  }

  function applyActiveTombWorldEventHooks(state,hookName,context={}){
    return activeRecords(state,Number(context.turningPoint??state?.turningPoint)).sort((a,b)=>Number(a.priority||0)-Number(b.priority||0)).reduce((current,record)=>{
      const handler=HANDLERS[record.definitionId]?.[hookName];
      return handler?handler({...current,eventInstanceId:record.instanceId}):current;
    },context);
  }

  function damagePackets(normal,critical,profile){
    return [
      ...Array.from({length:Math.max(0,Number(normal)||0)},(_,index)=>({id:`normal-${index}`,kind:'normal',originalDamage:Number(profile?.normal||0),finalDamage:Number(profile?.normal||0)})),
      ...Array.from({length:Math.max(0,Number(critical)||0)},(_,index)=>({id:`critical-${index}`,kind:'critical',originalDamage:Number(profile?.crit||0),finalDamage:Number(profile?.crit||0)}))
    ];
  }

  function effectivePlayerApl(state,operativeId,baseApl){
    const modifier=(state?.eventState?.playerAplModifiers||[]).filter(item=>item.targetId===operativeId).reduce((sum,item)=>sum+Number(item.amount||0),0);
    return Math.max(1,Number(baseApl||0)+modifier);
  }

  function effectiveNpoApl(state,operativeId,baseApl){
    const modifier=(state?.npoRuleState?.aplModifiers||[]).filter(item=>item.targetId===operativeId).reduce((sum,item)=>sum+Number(item.amount||0),0);
    return Math.max(1,Number(baseApl||0)+modifier);
  }

  function effectiveWeaponProfile(state,profile,context={}){
    const result=applyActiveTombWorldEventHooks(state,'effectiveWeapon',{...context,profile:{...profile,rules:[...(profile?.rules||[])]}});
    return result.messages?.length?{...result.profile,eventMessages:[...result.messages]}:result.profile;
  }

  function effectiveAttackRerolls(state,context={}){
    return applyActiveTombWorldEventHooks(state,'attackRerolls',{attackDice:true,defenceDice:true,...context});
  }

  function resolveCountertemporalPackets(state,packets,context={}){
    return applyActiveTombWorldEventHooks(state,'damagePackets',{...context,packets}).packets;
  }

  function resolveNpoIncapacitation(state,context={}){
    return applyActiveTombWorldEventHooks(state,'incapacitationCandidates',{...context,candidates:[...(context.candidates||[])]});
  }

  return {HANDLERS,activeRecords,applyActiveTombWorldEventHooks,damagePackets,effectivePlayerApl,effectiveNpoApl,effectiveWeaponProfile,effectiveAttackRerolls,resolveCountertemporalPackets,resolveNpoIncapacitation};
});
