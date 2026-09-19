const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = value => value == null ? 'Unavailable' : `${(value * 100).toFixed(2)}%`;
const cents = value => `${(value * 100).toFixed(2)}¢`;
let events = null, loading = false, generation = 0;
async function api(path, body) {
  const response = await fetch(path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  return data;
}
function status(message, warning=false) { $('status').textContent=message; $('status').className=warning?'warning':'muted'; }
function eventInputs(){return {kalshi:$('kalshi-event').value,polymarket:$('polymarket-event').value};}
function invalidate(){generation++; $('dashboard').hidden=true;}
$('search-form').addEventListener('submit', async e => {
  e.preventDefault(); const button=e.submitter; button.disabled=true; $('search-status').textContent='Searching both platforms…'; $('search-results').replaceChildren();
  try {
    const data=await api('/api/search?q='+encodeURIComponent($('query').value));
    for(const platform of ['Kalshi','Polymarket']){
      const box=document.createElement('div'), title=document.createElement('h2');title.textContent=platform;box.append(title);
      const matches=data.events.filter(x=>x.platform===platform);
      if(!matches.length){const empty=document.createElement('p');empty.textContent='No matching events returned.';box.append(empty);}
      for(const event of matches){const button=document.createElement('button');button.className='result';button.innerHTML=`${esc(event.title)}<small>${esc(event.id)}</small>`;button.onclick=()=>{$(platform==='Kalshi'?'kalshi-event':'polymarket-event').value=event.id;invalidate();$('outcomes').hidden=true;status(`${platform} event selected. Select the other event, then load outcomes.`);};box.append(button);}
      $('search-results').append(box);
    }
    $('search-status').textContent=[data.coverage,...data.errors].join(' ');
  }catch(error){$('search-status').textContent=error.message;}finally{button.disabled=false;}
});
$('events-form').addEventListener('submit',e=>{e.preventDefault();loadEvents();});
$('example').onclick=()=>{$('kalshi-event').value='KXFEDDECISION-26OCT';$('polymarket-event').value='fed-decision-in-october-20260617190323537';loadEvents();};
for(const id of ['kalshi-event','polymarket-event']) $(id).addEventListener('input',()=>{invalidate();$('outcomes').hidden=true;});
async function loadEvents(){
  if(loading)return;loading=true;invalidate();const version=generation;$('outcomes').hidden=true;$('candidates').replaceChildren();status('Loading event contracts…');
  try{
    const data=await api('/api/events',eventInputs());if(version!==generation)return;events=data;
    if(!data.kalshi||!data.polymarket) throw new Error(data.errors.join(' '));
    for(const side of ['kalshi','polymarket']) $(side+'-market').innerHTML=data[side].markets.map(m=>`<option value="${esc(m.id)}">${esc(m.outcome)}${m.active?'':' (inactive)'}</option>`).join('');
    if(!data.kalshi.markets.length||!data.polymarket.markets.length)throw new Error('One event has no supported binary YES/NO contracts.');
    $('outcomes').hidden=false;
    for(const candidate of data.candidates.slice(0,8)){
      const k=data.kalshi.markets.find(m=>m.id===candidate.kalshi_id),p=data.polymarket.markets.find(m=>m.id===candidate.polymarket_id);
      const button=document.createElement('button');button.textContent=`${k.outcome} ↔ ${p.outcome}`;button.title=candidate.reason;
      button.onclick=()=>{$('kalshi-market').value=k.id;$('polymarket-market').value=p.id;refresh();};$('candidates').append(button);
    }
    if(data.candidates.length){$('kalshi-market').value=data.candidates[0].kalshi_id;$('polymarket-market').value=data.candidates[0].polymarket_id;}
    status(data.candidates.length?'Suggested pairs are unverified. Review settlement terms below.':'No strong text match. Select outcomes manually.',true);
  }catch(error){status(error.message,true);}finally{loading=false;}
  if(version===generation&&!$('outcomes').hidden)await refresh();
}
$('compare').onclick=refresh;
for(const id of ['kalshi-market','polymarket-market','days','allowance'])$(id).addEventListener('change',()=>{invalidate();});
async function refresh(){
  if(loading||$('outcomes').hidden)return;
  const allowance=Number($('allowance').value);
  if(!Number.isFinite(allowance)||allowance<0||allowance>100){status('Enter an allowance between 0 and 100 cents.',true);return;}
  loading=true;invalidate();const version=generation;$('compare').disabled=true;status('Retrieving quotes and history…');
  try{
    const data=await api('/api/compare',{...eventInputs(),kalshi_market:$('kalshi-market').value,polymarket_market:$('polymarket-market').value,days:Number($('days').value),allowance:allowance/100});
    if(version!==generation)return;
    render(data);$('dashboard').hidden=false;
    const errors=[...data.errors,...data.kalshi.warnings,...data.polymarket.warnings];
    status(errors.length?errors.join(' '):'Comparison refreshed. Settlement equivalence remains unverified.',true);
  }catch(error){status(error.message,true);}finally{loading=false;$('compare').disabled=false;}
}
setInterval(()=>{if($('auto').checked&&!document.hidden)refresh();},30000);
function render(data){
  const k=data.kalshi,p=data.polymarket;
  $('freshness').textContent='Retrieved '+new Date(data.fetched_at).toLocaleString();
  $('metrics').innerHTML=[k,p].map(m=>`<div class="metric"><span class="${m.platform==='Kalshi'?'kalshi':'poly'}">${esc(m.platform)} · YES</span><strong>${pct(m.probability)}</strong><div>${esc(m.outcome)}</div><p class="muted">${esc(m.probability_basis)}<br>${m.active?'Open':'Inactive'} · ${m.quote_time?'Book timestamp '+esc(new Date(m.quote_time).toLocaleString()):'Exchange quote timestamp unavailable'}</p></div>`).join('')+`<div class="metric"><span>PROBABILITY GAP</span><strong>${data.gap_pp==null?'—':Math.abs(data.gap_pp).toFixed(2)+' pp'}</strong><div>${data.gap_pp==null?'Missing price':data.gap_pp===0?'Same indicated probability':(data.gap_pp>0?'Kalshi':'Polymarket')+' priced higher'}</div><p class="muted">Absolute difference in indicated YES prices. This is not a tradable profit estimate.</p></div>`;
  $('rules').innerHTML=[k,p].map(m=>`<div><h3>${esc(m.platform)}</h3><a href="${esc(m.url)}" target="_blank" rel="noopener noreferrer">${esc(m.title)} ↗</a><p class="muted">Close / end: ${esc(m.close_time?new Date(m.close_time).toLocaleString():'Unspecified')}</p><div class="rules-text">${esc(m.rules||'No rules returned by source.')}</div></div>`).join('');
  if(!data.trades.length){$('trade').innerHTML='<p>Both buy quotes are not available for an active pair. No trade estimate can be calculated.</p>';}
  else{
    const t=data.trades[0];
    $('trade').innerHTML=`<p class="muted">Lowest quoted cost of the two opposing-side combinations</p><div class="trade-legs"><div>Buy YES on <strong>${esc(t.yes_platform)}</strong><br>${cents(t.yes_price)}</div><span>+</span><div>Buy NO on <strong>${esc(t.no_platform)}</strong><br>${cents(t.no_price)}</div></div><table><tbody><tr><td>Cost per pair</td><td>${cents(t.cost)}</td></tr><tr><td>Gross conditional edge</td><td>${cents(t.gross_edge)}</td></tr><tr><td>After your allowance</td><td>${cents(t.adjusted_edge)} / pair</td></tr><tr><td>Top-of-book pair capacity</td><td>${t.max_pairs_at_top==null?'Unverified — one side lacks size data':t.max_pairs_at_top.toFixed(2)}</td></tr></tbody></table><p class="warning">${esc(t.status)}. ${t.adjusted_edge>0?'Positive conditional price edge; review terms and execution.':'No positive edge after the selected allowance.'}</p>`;
  }
  chart(data.history);
}
function chart(history){
  const series=Object.entries(history).map(([name,points])=>({name,points:points.map(p=>({t:typeof p.t==='number'?p.t:new Date(p.t).getTime()/1000,p:p.p})).filter(p=>Number.isFinite(p.t)&&Number.isFinite(p.p)).sort((a,b)=>a.t-b.t)}));
  const points=series.flatMap(s=>s.points);
  $('history-table').innerHTML=points.length?'<table><thead><tr><th>Source</th><th>Time (UTC)</th><th>YES price</th></tr></thead><tbody>'+series.flatMap(s=>s.points.map(p=>`<tr><td>${esc(s.name)}</td><td>${esc(new Date(p.t*1000).toISOString())}</td><td>${pct(p.p)}</td></tr>`)).join('')+'</tbody></table>':'No historical observations available.';
  if(!points.length){$('chart').innerHTML='<p class="warning">No history returned for this range. Current quotes may still be available.</p>';return;}
  const lo=Math.min(...points.map(p=>p.t)),hi=Math.max(...points.map(p=>p.t));const x=t=>60+((t-lo)/Math.max(1,hi-lo))*980,y=p=>270-p*240;
  let svg='<svg viewBox="0 0 1080 325" role="img" aria-label="YES prices over time on a zero to one hundred percent scale">';
  for(const p of [0,.25,.5,.75,1])svg+=`<line x1="60" y1="${y(p)}" x2="1040" y2="${y(p)}" stroke="#27313c"/><text x="6" y="${y(p)+4}" fill="#94a2b3" font-size="12">${p*100}%</text>`;
  for(const s of series){const color=s.name==='Kalshi'?'#a5efbd':'#8baaff';let last=null;const gaps=s.points.slice(1).map((p,i)=>p.t-s.points[i].t).sort((a,b)=>a-b);const maxGap=(gaps[Math.floor(gaps.length/2)]||3600)*3;
    let path='';for(const p of s.points){path+=`${last===null||p.t-last>maxGap?'M':'L'}${x(p.t).toFixed(1)},${y(p.p).toFixed(1)} `;last=p.t;}
    svg+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="2.5"/>`;
    for(const p of s.points)svg+=`<circle cx="${x(p.t)}" cy="${y(p.p)}" r="2" fill="${color}"><title>${esc(s.name)} · ${esc(new Date(p.t*1000).toLocaleString())} · ${pct(p.p)}</title></circle>`;
  }
  svg+=`<text x="60" y="305" fill="#94a2b3" font-size="12">${esc(new Date(lo*1000).toLocaleString())}</text><text x="1040" y="305" text-anchor="end" fill="#94a2b3" font-size="12">${esc(new Date(hi*1000).toLocaleString())}</text></svg>`;
  const missing=series.filter(s=>!s.points.length).map(s=>s.name);
  $('chart').innerHTML=svg+(missing.length?`<p class="warning">No ${esc(missing.join(', '))} history returned for this range.</p>`:'');
}
