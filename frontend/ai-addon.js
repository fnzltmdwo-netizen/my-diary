(()=>{
  function esc(s=''){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
  function injectStyle(){
    const st=document.createElement('style');
    st.textContent=`
      .nav{grid-template-columns:repeat(8,1fr)!important;width:min(860px,calc(100% - 18px))!important}
      .iu-question{border:1px solid var(--line);border-radius:17px;background:rgba(129,110,183,.055);padding:14px;margin-top:10px}
      .iu-question b{display:block;font-size:12.5px;margin-bottom:5px}.iu-question span{font-size:12px;line-height:1.55;color:var(--muted)}
      .iu-daily{border:1px solid var(--line);border-radius:18px;padding:15px;margin-top:20px;background:linear-gradient(135deg,rgba(129,110,183,.07),rgba(128,174,189,.07))}
      .iu-note{border:1px solid var(--line);border-radius:18px;padding:14px;background:linear-gradient(135deg,rgba(129,110,183,.09),rgba(128,174,189,.09));font-size:12px;line-height:1.65}
      .iu-brain-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.iu-badge{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:10.5px;color:var(--muted);background:var(--solid)}
      .iu-ai-row{display:grid;grid-template-columns:1fr 190px;gap:10px}.iu-check{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px;margin:12px 0}.iu-check input{width:auto}
      .iu-bubble{border:1px solid var(--line);border-radius:18px;padding:14px;margin-top:10px;background:var(--solid)}.iu-bubble.user{background:rgba(129,110,183,.065)}.iu-bubble.ai{background:rgba(128,174,189,.075)}
      .iu-bubble .body{white-space:pre-wrap;line-height:1.72}.iu-status{font-size:11px;color:var(--muted);margin-top:9px}
      .iu-evidence{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px}.iu-evidence summary{cursor:pointer;color:var(--muted);font-size:11px;font-weight:700}.iu-source{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:13px;padding:9px 10px;margin-top:7px;background:rgba(255,255,255,.25)}.iu-source:hover{transform:translateY(-1px)}.iu-source b{font-size:11px}.iu-source span{display:block;font-size:10.5px;color:var(--muted);line-height:1.45;margin-top:3px}.iu-source em{font-style:normal;font-size:9px;border:1px solid var(--line);padding:2px 5px;border-radius:999px;margin-left:5px;color:var(--muted)}
      @media(max-width:780px){.iu-ai-row{grid-template-columns:1fr}.nav{width:calc(100% - 18px)!important}.nav button{font-size:8.5px!important}}
    `;
    document.head.appendChild(st);
  }

  function restoreWriteLayout(){
    const write=document.querySelector('#write'); if(!write)return;
    const grid=write.querySelector('.grid'); if(!grid)return;
    const cards=[...grid.children].filter(x=>x.classList?.contains('card')); if(cards.length<2)return;
    const left=cards[0], right=cards[1];
    const h=left.querySelector('h3'); if(h)h.textContent='오늘의 마음 기록';
    const sub=left.querySelector('.small,.sub'); if(sub)sub.textContent='감정을 없애려 하지 않고, 감정과 나 사이에 공간을 만듭니다.';
    const patterns=document.querySelector('#patterns');
    if(patterns && !left.contains(patterns)){
      const wrap=document.createElement('div'); wrap.className='field'; wrap.innerHTML='<label>내가 알아차린 패턴</label>'; wrap.appendChild(patterns);
      const meaning=document.querySelector('#meaning')?.closest('.field'); if(meaning)meaning.insertAdjacentElement('afterend',wrap); else left.appendChild(wrap);
    }
    right.innerHTML=`<h3>오늘의 다섯 질문</h3><p class="small">정답을 만들기보다 내 마음이 어디에 있는지 확인합니다.</p>
      <div class="iu-question"><b>1. 실제 사실은?</b><span>상대 행동과 내가 붙인 의미를 분리해보기.</span></div>
      <div class="iu-question"><b>2. 내 마음은 무엇을 하고 있나?</b><span>악마화·비교·자기비난을 없애기 전에 먼저 이름 붙이기.</span></div>
      <div class="iu-question"><b>3. 이해와 허용은 같은가?</b><span>이해해도 거리를 둘 수 있고, 용서해도 다시 믿지 않을 수 있어요.</span></div>
      <div class="iu-question"><b>4. 지금의 감정이 미래의 예언인가?</b><span>현재의 느낌은 현재의 상태이지 미래에 대한 판결이 아닙니다.</span></div>
      <div class="iu-question"><b>5. 오늘의 나를 버리지 않으려면?</b><span>완벽한 해결 대신 오늘 가능한 한 행동을 고릅니다.</span></div>
      <div class="iu-daily"><b>${new Intl.DateTimeFormat('ko-KR',{year:'numeric',month:'long',day:'numeric',weekday:'short'}).format(new Date())}의 나도 여기 있어요.</b><div class="body">괜찮아. 아직 확정된 사실보다 내 마음이 붙인 해석이 더 클 수도 있어. 오늘은 그것을 알아차린 것만으로 충분해.</div></div>`;
  }

  let aiHistory=[];
  try{aiHistory=JSON.parse(sessionStorage.getItem('mySea.aiChat.v51')||'[]').slice(-12)}catch{}
  function saveHistory(){sessionStorage.setItem('mySea.aiChat.v51',JSON.stringify(aiHistory.slice(-12)))}
  function evidenceHTML(x){
    const principles=(x.principles||[]).map(p=>`<div class="iu-source"><b>${esc(p.id)} · ${esc(p.category||'원칙')}</b><span>${esc(p.scenario||'')}</span></div>`).join('');
    if(!x.evidence?.length&&!principles)return '';
    const items=x.evidence.map(e=>`<a class="iu-source" href="${esc(e.url||'#')}" target="_blank" rel="noopener"><b>${esc(e.year)} · ${esc(e.publisher||'')}<em>${esc(e.tier||'')}</em></b><span>${esc(e.source||'')}</span><span>“${esc(e.quote||'')}”</span></a>`).join('');
    return `<details class="iu-evidence"><summary>연결 근거 보기 · 공개 관찰 ${x.evidenceUsed||0}개 · 적용 원칙 ${x.principlesUsed||0}개</summary>${principles}${items}</details>`;
  }
  function renderChat(){
    const box=document.querySelector('#iuChat'); if(!box)return;
    if(!aiHistory.length){box.innerHTML='<div class="empty">지금 마음을 적으면 관련 IU Brain 자료를 먼저 찾고, 그 자료를 겹쳐 본 답이 나타나요.</div>';return}
    box.innerHTML=aiHistory.map(x=>`<div class="iu-bubble ${x.role==='user'?'user':'ai'}"><b>${x.role==='user'?'나':'나의 바다 원칙 코치'}</b><div class="body">${esc(x.text)}</div>${x.role==='ai'?evidenceHTML(x):''}</div>`).join('');
  }
  function context(){
    if(!document.querySelector('#iuUseContext')?.checked)return null;
    try{
      const appState=(typeof state==='object'&&state)||{};
      const entries=(appState.entries||[]).slice(0,5).map(e=>({date:e.createdAt,emotion:e.emotion,intensity:e.intensity,fact:e.fact,meaning:e.meaning||e.interpretation,patterns:e.patterns,observer:e.observer,boundary:e.boundary,selfMsg:e.selfMsg||e.selfMessage,proof:e.proof}));
      const draft={emotion:typeof emotion==='string'?emotion:'',intensity:document.querySelector('#intensity')?.value||'',fact:document.querySelector('#fact')?.value||'',meaning:document.querySelector('#meaning')?.value||'',observer:document.querySelector('#observer')?.value||'',boundary:document.querySelector('#boundary')?.value||'',selfMsg:document.querySelector('#selfmsg')?.value||''};
      return {current_diary:draft,recent_entries:entries,boundary_plan:appState.boundary||null};
    }catch{return null}
  }
  async function loadBrainStatus(){
    const meta=document.querySelector('#iuBrainMeta'); if(!meta)return;
    const appPw=sessionStorage.getItem('mySeaPw')||'';
    try{
      const r=await fetch('/api/iu-brain/status',{headers:{'X-App-Password':appPw}}); const d=await r.json(); if(!r.ok)throw new Error();
      meta.innerHTML=`<span class="iu-badge">검증 관찰치 ${d.observations}개</span><span class="iu-badge">개인 장면 원칙 ${d.principles||0}개</span><span class="iu-badge">${(d.years||[])[0]||'?'}–${(d.years||[]).slice(-1)[0]||'?'} 시간축</span><span class="iu-badge">${d.server_key_configured?'AI 연결됨':'로컬 원칙 모드'}</span>`;
    }catch{meta.innerHTML='<span class="iu-badge">IU Brain 상태 확인 대기</span>'}
  }
  async function askIU(){
    const q=document.querySelector('#iuQuestion')?.value.trim(); if(!q){alert('지금 마음을 한 문장이라도 적어줘요.');return}
    const appPw=sessionStorage.getItem('mySeaPw')||'';
    const btn=document.querySelector('#iuAsk'), status=document.querySelector('#iuStatus');
    btn.disabled=true; btn.textContent='관련 기억을 찾는 중…'; status.textContent='IU Brain에서 지금 고민과 가까운 공개발언을 찾고, 서로 다른 시기의 관점을 겹쳐 보고 있어요.';
    aiHistory.push({role:'user',text:q}); saveHistory(); renderChat();
    try{
      const headers={'Content-Type':'application/json','X-App-Password':appPw};
      const r=await fetch('/api/iu-advice',{method:'POST',headers,body:JSON.stringify({message:q,context:context(),model:document.querySelector('#iuModel').value,mode:document.querySelector('#iuMode').value})});
      const d=await r.json(); if(!r.ok)throw new Error(d.detail||('HTTP '+r.status));
      aiHistory.push({role:'ai',text:d.text||'답변을 불러오지 못했어요.',evidence:d.evidence||[],evidenceUsed:d.evidence_used,brainTotal:d.brain_total,principles:d.principles||[],principlesUsed:d.principles_used||0});
      saveHistory(); document.querySelector('#iuQuestion').value=''; status.textContent=`답변 완료 · 공개 근거 ${d.evidence_used||0}개 · 적용 원칙 ${d.principles_used||0}개 · ${d.model||''}`;
    }catch(e){const m='원칙 코치를 불러오지 못했어. '+e.message; aiHistory.push({role:'ai',text:m});saveHistory();status.textContent=m}
    finally{btn.disabled=false;btn.textContent='원칙 코치로 바라보기';renderChat()}
  }

  function addAIPage(){
    if(document.querySelector('#ai'))return;
    const app=document.querySelector('.app'); const nav=document.querySelector('.nav'); if(!app||!nav)return;
    const page=document.createElement('section'); page.className='page'; page.id='ai';
    page.innerHTML=`<div class="grid"><div class="card"><h3>나의 바다 원칙 코치</h3><p class="small">아이유 본인을 재현하거나 사적 마음을 진단하는 기능이 아니에요. 검증한 공개자료의 대처 원칙과 승재의 반복 장면 원칙 DB를 현재 사실에 맞춰 적용합니다.</p>
      <div class="iu-note"><b>판독 순서</b><br>현재 사실 → 마음이 붙인 해석 → 행동의 단기 효과와 장기 비용 → 상대 책임과 내 통제 범위 → 오늘 가능한 한 걸음.</div><div class="iu-brain-meta" id="iuBrainMeta"><span class="iu-badge">자료 불러오는 중…</span></div>
      <div class="iu-ai-row"><div class="field"><label>답변 방식</label><select id="iuMode"><option value="counseling" selected>상담형</option><option value="diary">일기 분석형</option><option value="short">짧게</option><option value="casual">일상 대화형</option></select></div><div class="field"><label>조언 모델</label><select id="iuModel"><option value="gpt-5.6-luna" selected>GPT-5.6 Luna · 저비용 기본</option><option value="gpt-5.6-terra">GPT-5.6 Terra · 더 깊게</option><option value="gpt-5.6-sol">GPT-5.6 Sol · 가장 깊게</option></select></div></div>
      <label class="iu-check"><input id="iuUseContext" type="checkbox" checked> 최근 마음 기록 5개와 현재 경계 선언도 함께 참고하기</label>
      <div class="field"><label>지금 무슨 일이 있었어?</label><textarea id="iuQuestion" placeholder="예: 경계를 세웠더니 그 사람이 떠났어. 머리로는 이해하는데 자꾸 악마화하게 돼. 지금 이 마음을 어떻게 보면 좋을까?"></textarea></div>
      <div class="chips"><button class="chip" data-iu-preset="답장이 없어서 나를 피하는 것 같고 불안해.">답장 불안</button><button class="chip" data-iu-preset="내가 경계를 세웠더니 상대가 떠났어. 내가 너무한 건지 자꾸 흔들려.">경계 후 죄책감</button><button class="chip" data-iu-preset="상대가 잘 지내는 모습을 보고 또 나쁜 사람이라고 생각하고 있어.">악마화 알아차림</button><button class="chip" data-iu-preset="빚과 카드 문제 때문에 미래가 끝난 것처럼 느껴져. 지금 뭘 먼저 해야 할까?">돈·빚 불안</button></div>
      <button class="primary" id="iuAsk" style="margin-top:14px">원칙 코치로 바라보기</button><div class="iu-status" id="iuStatus"></div></div>
      <div class="card"><h3>지금의 나에게 건네는 말</h3><p class="small">답변 아래의 <b>근거 보기</b>를 열면 이번 조언에 실제로 연결된 연도·매체·공개발언을 확인할 수 있어요.</p><div id="iuChat"></div></div></div>`;
    app.appendChild(page);
    const b=document.createElement('button'); b.dataset.p='ai'; b.innerHTML='✦<br>아이유'; nav.insertBefore(b,nav.lastElementChild);
    b.addEventListener('click',()=>{document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));page.classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));b.classList.add('active');window.scrollTo({top:0,behavior:'smooth'})});
    document.querySelector('#iuAsk').onclick=askIU;
    document.querySelectorAll('[data-iu-preset]').forEach(x=>x.onclick=()=>{document.querySelector('#iuQuestion').value=x.dataset.iuPreset;document.querySelector('#iuQuestion').focus()});
    renderChat(); loadBrainStatus();
  }

  function run(){injectStyle();restoreWriteLayout();addAIPage()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(run,0));else setTimeout(run,0);
})();
