/* Temporary Tomb UI v2 prototype. Loaded after app.js so it can replace only the experimental operative picker. */
(()=>{
  const ASSET_ROOT='Assets/Images/TombUI/v2/';
  const READY_FRAME=ASSET_ROOT+'card-ready.svg';
  const SELECTED_FRAME=ASSET_ROOT+'card-selected.svg';
  const PORTRAIT_SPRITE=ASSET_ROOT+'portrait-sprite.webp';

  const deathwatchPortraitClass={
    sergeant:'leader',
    aegis:'rifleman',
    marksman:'rifleman',
    disruptor:'rifleman',
    gunner:'rifleman',
    blademaster:'melee',
    demolisher:'melee',
    headtaker:'melee',
    breacher:'heavy',
    bombard:'heavy',
    'horde-slayer':'heavy'
  };

  function v2ThreatBars(value){
    const threat=Math.max(0,Number(value)||0);
    const filled=Math.min(5,Math.ceil(threat/3));
    return Array.from({length:5},(_,i)=>`<i class="${i<filled?'on':''}"></i>`).join('');
  }

  function v2TurningPointDots(value){
    const point=Math.max(0,Math.min(4,Number(value)||0));
    return Array.from({length:4},(_,i)=>`<i class="${i<point?'on':''}"></i>`).join('');
  }

  function v2Portrait(id){
    if(selectedPlayerTeamName().toLowerCase()!=='deathwatch'){
      return `<span class="tomb-v2-monogram">${escapeHtml(playerName(id).slice(0,2).toUpperCase())}</span>`;
    }
    const portrait=deathwatchPortraitClass[id]||'rifleman';
    return `<span class="tomb-v2-portrait portrait-${portrait}" style="--tomb-v2-sprite:url('${PORTRAIT_SPRITE}')" aria-hidden="true"></span>`;
  }

  showTombPlayerOperativeSelection=function(candidates){
    const firstApl=candidates.length?(playerDefinition(candidates[0])?.apl??livePlayerOperative(candidates[0])?.apl??'—'):'—';
    const cards=candidates.map((id,index)=>{
      const operative=livePlayerOperative(id)||playerDefinition(id)||{};
      return `<button class="tomb-v2-card" type="button" role="radio" aria-checked="false" data-tomb-player-operative="${escapeHtml(id)}" ${index===0?'data-dialog-focus':''}>
        <img class="tomb-v2-card-frame" src="${READY_FRAME}" alt="" aria-hidden="true">
        <span class="tomb-v2-card-grid">
          <span class="tomb-v2-portrait-zone">${v2Portrait(id)}</span>
          <span class="tomb-v2-copy">
            <strong>${escapeHtml(playerName(id))}</strong>
            <small>${escapeHtml(operative.role||'Operative')}</small>
            <span class="tomb-v2-status"><i></i><b>READY</b></span>
          </span>
          <span class="tomb-v2-radio" aria-hidden="true"></span>
        </span>
      </button>`;
    }).join('');

    showModal('OPERATIVE ACTION',`<section class="tomb-v2-shell">
      <header class="tomb-v2-brand">
        <div class="tomb-v2-brand-copy"><strong>TOMB WORLD SOLO</strong><span>OPERATIVE ACTION</span></div>
      </header>
      <div class="tomb-v2-hud" aria-label="Battle status">
        <div class="tomb-v2-hud-cell threat"><span>THREAT LEVEL</span><div class="tomb-v2-bars">${v2ThreatBars(state.threat)}</div><strong>${escapeHtml(String(state.threat??0))}</strong></div>
        <div class="tomb-v2-hud-cell tp"><span>TURNING POINT</span><div class="tomb-v2-dots">${v2TurningPointDots(state.turningPoint)}</div><strong>${escapeHtml(String(state.turningPoint??0))}</strong></div>
        <div class="tomb-v2-hud-cell apl"><span>APL</span><div class="tomb-v2-apl-icon">≋</div><strong id="tombV2Apl">${escapeHtml(String(firstApl))}</strong></div>
      </div>
      <div class="tomb-v2-section-title"><span>✠</span><strong>SELECT OPERATIVE</strong></div>
      <div class="tomb-v2-operative-grid" role="radiogroup" aria-label="Ready operatives">${cards}</div>
      <div class="tomb-v2-preview">
        <img src="Assets/Images/TombUI/action-preview.webp" alt="" aria-hidden="true">
        <div class="tomb-v2-preview-copy"><span>ACTION PREVIEW</span><strong>OPERATIVE READY</strong><small id="tombV2PreviewText">Choose an operative to continue.</small></div>
      </div>
      <div class="tomb-v2-actions">
        <button class="tomb-graphic-button primary" type="button" id="confirmTombPlayerSelection" disabled><img src="Assets/Images/TombUI/button-primary.webp" alt="" aria-hidden="true"><span>Confirm Selection »</span></button>
        <button class="tomb-graphic-button secondary" type="button" data-close><img src="Assets/Images/TombUI/button-secondary.webp" alt="" aria-hidden="true"><span>Cancel</span></button>
      </div>
    </section>`);

    modal.classList.add('tomb-operative-picker-modal');
    let selectedId='';
    const confirm=$('#confirmTombPlayerSelection');
    const preview=$('#tombV2PreviewText');
    const apl=$('#tombV2Apl');

    $$('[data-tomb-player-operative]',modal).forEach(button=>button.onclick=()=>{
      selectedId=button.dataset.tombPlayerOperative;
      $$('[data-tomb-player-operative]',modal).forEach(card=>{
        const selected=card.dataset.tombPlayerOperative===selectedId;
        card.classList.toggle('selected',selected);
        card.setAttribute('aria-checked',String(selected));
        const frame=$('.tomb-v2-card-frame',card);
        if(frame)frame.src=selected?SELECTED_FRAME:READY_FRAME;
        const status=$('.tomb-v2-status b',card);
        if(status)status.textContent=selected?'SELECTED':'READY';
      });
      const definition=playerDefinition(selectedId)||livePlayerOperative(selectedId)||{};
      if(apl)apl.textContent=String(definition.apl??'—');
      if(preview)preview.textContent=`${playerName(selectedId)} selected. Confirm to begin activation.`;
      confirm.disabled=false;
    });

    confirm.onclick=()=>{if(selectedId)beginPlayerActivation(selectedId);};
  };
})();