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
      <div class="iu-daily"><b>${new Intl.DateTimeFormat('ko-KR',{dateStyle:'long',weekday:'short'}).format(new Date())}의 나도 여기 있어요.</b><div class="body">괜찮아. 아직 확정된 사실보다 내 마음이 붙인 해석이 더 클 수도 있어. 오늘은 그것을 알아차린 것만으로 충분해.</div></div>`;
  }

  let aiHistory=[];
  function evidenceHTML(x){
    if(!x.evidence?.length)return '';
    const items=x.evidence.map(e=>`<a class="iu-source" href="${esc(e.url||'#')}" target="_blank" rel="noopener"><b>${esc(e.year)} · ${esc(e.publisher||'')}<em>${esc(e.tier||'')}</em></b><span>${esc(e.source||'')}</span><span>“${esc(e.quote||'')}”</span></a>`).join('');
    return `<details class="iu-evidence"><summary>이번 답변의 근거 ${x.evidenceUsed||x.evidence.length}개 보기 · IU Brain 총 ${x.brainTotal||'?'}개</summary>${items}</details>`;
  }
  function renderChat(){
    const box=document.querySelector('#iuChat'); if(!box)return;
    if(!aiHistory.length){box.innerHTML='<div class="empty">지금 마음을 적으면 관련 IU Brain 자료를 먼저 찾고, 그 자료를 겹쳐 본 답이 나타나요.</div>';return}
    box.innerHTML=aiHistory.map(x=>`<div class="iu-bubble ${x.role==='user'?'user':'ai'}"><b>${x.role==='user'?'나':'IU Brain · 공개발언 기반 사고모델'}</b><div class="body">${esc(x.text)}</div>${x.role==='ai'?evidenceHTML(x):''}</div>`).join('');
  }
  function context(){
    if(!document.querySelector('#iuUseContext')?.checked)return null;
    try{
      const entries=JSON.parse(localStorage.getItem('mySea.entries.v3')||'[]').slice(0,5).map(e=>({date:e.createdAt,emotion:e.emotion,intensity:e.intensity,fact:e.fact,meaning:e.meaning||e.interpretation,patterns:e.patterns,observer:e.observer,boundary:e.boundary,selfMsg:e.selfMsg||e.selfMessage,proof:e.proof}));
      const boundary=JSON.parse(localStorage.getItem('mySea.boundary.v3')||'null');
      return {recent_entries:entries,boundary_plan:boundary};
    }catch{return null}
  }
  async function loadBrainStatus(){
    const meta=document.querySelector('#iuBrainMeta'), wrap=document.querySelector('#iuKeyWrap'), forget=document.querySelector('#iuForgetWrap'); if(!meta)return;
    const appPw=sessionStorage.getItem('mySea.appPassword')||'';
    try{
      const r=await fetch('/api/iu-brain/status',{headers:{'X-App-Password':appPw}}); const d=await r.json(); if(!r.ok)throw new Error();
      meta.innerHTML=`<span class="iu-badge">검증 관찰치 ${d.observations}개</span><span class="iu-badge">${(d.years||[])[0]||'?'}–${(d.years||[]).slice(-1)[0]||'?'} 시간축</span><span class="iu-badge">${d.server_key_configured?'서버 AI 키 연결됨':'브라우저 키 필요'}</span>`;
      if(d.server_key_configured){if(wrap)wrap.style.display='none';if(forget)forget.style.display='none'}
    }catch{meta.innerHTML='<span class="iu-badge">IU Brain 상태 확인 대기</span>'}
  }
  async function askIU(){
    const q=document.querySelector('#iuQuestion')?.value.trim(); if(!q){alert('지금 마음을 한 문장이라도 적어줘요.');return}
    const key=document.querySelector('#iuKey')?.value.trim()||sessionStorage.getItem('mySea.aiKey')||''; if(key)sessionStorage.setItem('mySea.aiKey',key);
    const appPw=sessionStorage.getItem('mySea.appPassword')||'';
    const btn=document.querySelector('#iuAsk'), status=document.querySelector('#iuStatus');
    btn.disabled=true; btn.textContent='관련 기억을 찾는 중…'; status.textContent='IU Brain에서 지금 고민과 가까운 공개발언을 찾고, 서로 다른 시기의 관점을 겹쳐 보고 있어요.';
    aiHistory.push({role:'user',text:q}); renderChat();
    try{
      const headers={'Content-Type':'application/json','X-App-Password':appPw}; if(key)headers['X-AI-Key']=key;
      const r=await fetch('/api/iu-advice',{method:'POST',headers,body:JSON.stringify({message:q,context:context(),model:document.querySelector('#iuModel').value})});
      const d=await r.json(); if(!r.ok)throw new Error(d.detail||('HTTP '+r.status));
      aiHistory.push({role:'ai',text:d.text||'답변을 불러오지 못했어요.',evidence:d.evidence||[],evidenceUsed:d.evidence_used,brainTotal:d.brain_total});
      document.querySelector('#iuQuestion').value=''; status.textContent=`답변 완료 · 관련 근거 ${d.evidence_used||0}개 / 전체 Brain ${d.brain_total||0}개 · ${d.model||''}`;
    }catch(e){const m='AI 호출에 실패했어요. '+e.message; aiHistory.push({role:'ai',text:m}); status.textContent=m}
    finally{btn.disabled=false;btn.textContent='IU Brain으로 바라보기';renderChat()}
  }

  function addAIPage(){
    if(document.querySelector('#ai'))return;
    const app=document.querySelector('.app'); const nav=document.querySelector('.nav'); if(!app||!nav)return;
    const page=document.createElement('section'); page.className='page'; page.id='ai';
    page.innerHTML=`<div class="grid"><div class="card"><h3>아이유의 말</h3><p class="small">아이유 본인의 답변을 재현하는 기능이 아니라, 실제 공개 인터뷰를 연도별로 검증해 만든 <b>IU Brain</b>에서 관련 사고자료를 검색해 적용하는 AI예요.</p>
      <div class="iu-note"><b>IU Brain 방식</b><br>고민에서 핵심 주제를 찾기 → 관련 공개발언 검색 → 10대·20대·30대의 공통점과 변화를 비교 → 최근 나의 바다 기록과 연결 → 지금 적용 가능한 관점 만들기.</div><div class="iu-brain-meta" id="iuBrainMeta"><span class="iu-badge">Brain 불러오는 중…</span></div>
      <div class="field" id="iuKeyWrap"><label>OpenAI API Key · 서버 키가 없을 때만</label><input id="iuKey" type="password" placeholder="sk-... · DB에는 저장하지 않고 브라우저 세션에서만 사용"></div>
      <div class="iu-ai-row"><div class="field"><label>조언 모델</label><select id="iuModel"><option value="gpt-5.6-luna" selected>GPT-5.6 Luna · 저비용 기본</option><option value="gpt-5.6-terra">GPT-5.6 Terra · 더 깊게</option><option value="gpt-5.6-sol">GPT-5.6 Sol · 가장 깊게</option></select></div><div class="field" id="iuForgetWrap"><label>&nbsp;</label><button class="secondary" style="width:100%" id="iuForget">브라우저 API 키 지우기</button></div></div>
      <label class="iu-check"><input id="iuUseContext" type="checkbox" checked> 최근 마음 기록 5개와 현재 경계 선언도 함께 참고하기</label>
      <div class="field"><label>지금 무슨 일이 있었어?</label><textarea id="iuQuestion" placeholder="예: 경계를 세웠더니 그 사람이 떠났어. 머리로는 이해하는데 자꾸 악마화하게 돼. 지금 이 마음을 어떻게 보면 좋을까?"></textarea></div>
      <div class="chips"><button class="chip" data-iu-preset="사람 때문에 상처받았는데 사람을 미워하는 사람으로 변하고 싶지는 않아. 이 마음을 어떻게 받아들이면 좋을까?">사람 때문에 힘들 때</button><button class="chip" data-iu-preset="내가 경계를 세웠더니 상대가 떠났어. 내가 너무한 건지 자꾸 흔들려.">경계 후 떠났을 때</button><button class="chip" data-iu-preset="지금 내가 상대를 완전히 나쁜 사람으로 악마화하고 있어. 이 감정을 억누르지 않으면서 한 발 떨어져 보고 싶어.">악마화 알아차림</button></div>
      <button class="primary" id="iuAsk" style="margin-top:14px">IU Brain으로 바라보기</button><div class="iu-status" id="iuStatus"></div></div>
      <div class="card"><h3>지금의 나에게 건네는 말</h3><p class="small">답변 아래의 <b>근거 보기</b>를 열면 이번 조언에 실제로 연결된 연도·매체·공개발언을 확인할 수 있어요.</p><div id="iuChat"></div></div></div>`;
    app.insertBefore(page,nav);
    const b=document.createElement('button'); b.dataset.p='ai'; b.innerHTML='✦<br>아이유'; nav.insertBefore(b,nav.lastElementChild);
    b.addEventListener('click',()=>{document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));page.classList.add('active');document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));b.classList.add('active');window.scrollTo({top:0,behavior:'smooth'})});
    document.querySelector('#iuKey').value=sessionStorage.getItem('mySea.aiKey')||'';
    document.querySelector('#iuAsk').onclick=askIU;
    document.querySelector('#iuForget').onclick=()=>{sessionStorage.removeItem('mySea.aiKey');document.querySelector('#iuKey').value='';alert('브라우저 API 키를 지웠어요.')};
    document.querySelectorAll('[data-iu-preset]').forEach(x=>x.onclick=()=>{document.querySelector('#iuQuestion').value=x.dataset.iuPreset;document.querySelector('#iuQuestion').focus()});
    renderChat(); loadBrainStatus();
  }

  function run(){injectStyle();restoreWriteLayout();addAIPage()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(run,0));else setTimeout(run,0);
})();