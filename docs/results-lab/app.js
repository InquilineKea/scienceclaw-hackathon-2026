/* Codex integration of Argon's complete Results Lab HTML/CSS. Saved data only. */
'use strict';
(async()=>{
const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const fmt=x=>typeof x==='number'?(Number.isFinite(x)?Number(x.toPrecision(6)).toString():'unavailable'):String(x??'unavailable');
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
function node(tag,a={},text){const e=document.createElementNS(NS,tag);Object.entries(a).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;return e}
function options(id,values,label=fmt){const s=$(id),prev=s.value;s.replaceChildren(...values.map(v=>{const o=el('option',label(v));o.value=v;return o}));if(values.map(String).includes(prev))s.value=prev}
function table(id,rows,keys){$(id).replaceChildren(...rows.map(r=>{const tr=el('tr');keys.forEach(k=>tr.append(el('td',fmt(r[k]))));return tr}))}
function detail(id,r){const d=$(id);d.replaceChildren();Object.entries(r).forEach(([k,v])=>{const a=el('div',undefined,'kv-item');a.append(el('strong',k+': '),el('span',fmt(v)));d.append(a)})}
function limitations(id,rows){$(id).replaceChildren(...rows.map(x=>el('li',x)))}
function source(id,url,label){const a=el('a',label);a.href=url;$(id).append(a)}
const colors=['#166d66','#a1472b','#6f42a0','#326aa7','#8b6c13','#a23768','#434e5a'];
function chart(id,series,{xLabel,yLabel,log=false,select=()=>{},selected=-1,zero=false,connect=true}={}){
 const svg=$(id);svg.replaceChildren();const vb=svg.viewBox.baseVal,W=vb.width,H=vb.height,L=72,T=20,R=22,B=58;
 const all=series.flatMap(s=>s.points).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)&&(!log||p.x>0));if(!all.length){svg.append(node('text',{x:20,y:35},'No saved finite points for this selection'));return}
 const xx=p=>log?Math.log10(p.x):p.x;let xmin=Math.min(...all.map(xx)),xmax=Math.max(...all.map(xx)),ymin=Math.min(...all.flatMap(p=>Number.isFinite(p.sd)?[p.y-p.sd,p.y+p.sd]:[p.y]),...(zero?[0]:[])),ymax=Math.max(...all.flatMap(p=>Number.isFinite(p.sd)?[p.y-p.sd,p.y+p.sd]:[p.y]),...(zero?[0]:[]));
 if(xmin===xmax){xmin-=.5;xmax+=.5}if(ymin===ymax){ymin-=.5;ymax+=.5}const yp=(ymax-ymin)*.07;ymin-=yp;ymax+=yp;
 const X=x=>L+(x-xmin)/(xmax-xmin)*(W-L-R),Y=y=>H-B-(y-ymin)/(ymax-ymin)*(H-T-B);
 for(let i=0;i<=4;i++){const x=xmin+i*(xmax-xmin)/4,y=ymin+i*(ymax-ymin)/4;svg.append(node('line',{x1:L,x2:W-R,y1:Y(y),y2:Y(y),stroke:'#d9e0e4'}),node('text',{x:L-8,y:Y(y)+4,'text-anchor':'end','font-size':11,fill:'#334155'},fmt(y)),node('text',{x:X(x),y:H-B+20,'text-anchor':'middle','font-size':11,fill:'#334155'},fmt(log?10**x:x)))}
 svg.append(node('line',{x1:L,x2:W-R,y1:H-B,y2:H-B,stroke:'#64748b'}),node('text',{x:(L+W-R)/2,y:H-12,'text-anchor':'middle','font-size':12},xLabel),node('text',{x:14,y:(H-B)/2,transform:`rotate(-90 14 ${(H-B)/2})`,'text-anchor':'middle','font-size':12},yLabel));
 if(zero&&ymin<0&&ymax>0)svg.append(node('line',{x1:L,x2:W-R,y1:Y(0),y2:Y(0),stroke:'#64748b','stroke-dasharray':'3 4'}));
 for(const s of series){let path='';for(const p of s.points){if(!Number.isFinite(p.y)||!Number.isFinite(p.x)||(log&&p.x<=0)){path='';continue}path+=(path?' L':'M')+X(xx(p))+' '+Y(p.y)}if(connect&&path)svg.append(node('path',{d:path,fill:'none',stroke:s.color,'stroke-width':1.7,'stroke-dasharray':s.dash?'6 4':'none'}));
  for(const p of s.points){if(!Number.isFinite(p.y)||!Number.isFinite(p.x)||(log&&p.x<=0))continue;
   if(Number.isFinite(p.sd))svg.append(node('line',{x1:X(xx(p)),x2:X(xx(p)),y1:Y(p.y-p.sd),y2:Y(p.y+p.sd),stroke:s.color,'stroke-opacity':.35}));
   const c=node('circle',{cx:X(xx(p)),cy:Y(p.y),r:p.id===selected?6:3.2,fill:s.color,stroke:p.id===selected?'#111827':'white','stroke-width':p.id===selected?2:1,tabindex:0,role:'button','aria-label':`${s.label}: x ${fmt(p.x)}, y ${fmt(p.y)}; select saved record ${p.id}`});c.append(node('title',{},`${s.label}: ${fmt(p.x)}, ${fmt(p.y)}`));c.addEventListener('click',()=>select(p.id));c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(p.id)}});svg.append(c)
  }
 }
}
try{
const load=async f=>{const r=await fetch(f);if(!r.ok)throw Error('Could not load '+f);return r.json()};const [o,r]=await Promise.all([load('organoid.json'),load('rheology.json')]);
limitations('organoid-limitations-list',o.limitations);limitations('rheology-limitations-list',r.limitations);
source('organoid-provenance','https://humanavianaisymbiosis.wordpress.com/2026/10/31/organoid-gene-expression-collagen-network-156-gel-simulation/','Full synthetic model report');source('rheology-provenance',r.source_url,'Original saved workbook');
for(const name of ['organoid','rheology'])$('tab-btn-'+name).onclick=()=>{for(const n of ['organoid','rheology']){$('panel-'+n).hidden=n!==name;$('tab-btn-'+n).setAttribute('aria-selected',String(n===name));$('tab-btn-'+n).classList.toggle('active',n===name)}};
options('org-day-select',[0,1,2,3,4,5,6,7]);$('org-day-select').value='7';options('org-gel-select',o.gels.map(g=>g.gel));
const genes=['CYR61','CTGF','ANKRD1','AMOTL2','ACTA2','LOX','MMP14','LY6A','LGR5','KRT20','MKI67'];options('org-readout-select',['R_um',...genes.flatMap(g=>['mean','tip','inter'].map(t=>g+'_'+t))],v=>v==='R_um'?'Radius (µm)':v+' (dimensionless)');
table('org-matched-tbody',o.matched_day7_aggregate,['readout','n_pairs','median_rel_diff','p90_rel_diff','max_rel_diff']);
function organoid(){const day=+$('org-day-select').value,y=$('org-readout-select').value,gel=+$('org-gel-select').value,by=$('org-color-select').value,g=o.gels.find(g=>g.gel===gel),slice=o.trajectories.filter(t=>t.day===day).map(t=>({...o.gels.find(g=>g.gel===t.gel),...t})),cats=[...new Set(slice.map(t=>t[by]))].sort(),label=y==='R_um'?'Radius (µm)':y+' (dimensionless)';
 $('org-legend').replaceChildren(...cats.map((c,i)=>el('span',String(c),'legend-item result-color-'+(i%colors.length))));const choose=id=>{$('org-gel-select').value=id;organoid()};
 chart('org-scatter-svg',cats.map((c,i)=>({label:c,color:colors[i%colors.length],points:slice.filter(t=>t[by]===c).map(t=>({x:t.E_lin_Pa,y:t[y],id:t.gel}))})),{xLabel:'Saved linear stiffness E_lin (Pa)',yLabel:label,connect:false,selected:gel,select:choose});
 $('org-scatter-subtitle').textContent=`Day ${day} · ${slice.length} saved synthetic gels · select a point or gel. Colors: ${by}.`;
 $('org-slice-readout-th').textContent=label;table('org-slice-tbody',slice,['gel','collagen','mode','chem','dose','E_lin_Pa',y]);
 const trajectory=o.trajectories.filter(t=>t.gel===gel).sort((a,b)=>a.day-b.day);chart('org-traj-svg',[{label,color:colors[0],points:trajectory.map(t=>({x:t.day,y:t[y],id:t.day}))}],{xLabel:'Saved day',yLabel:label,selected:day,select:id=>{$('org-day-select').value=id;organoid()}});
 detail('org-gel-params',{...g,...trajectory.find(t=>t.day===day)});$('org-traj-col-readout').textContent=label;table('org-traj-tbody',trajectory,['day','R_um','Wnt','eps_mean',y]);$('org-traj-subtitle').textContent=`Gel ${gel}: one saved trajectory; no replicate confidence interval.`;
}
for(const id of ['org-day-select','org-gel-select','org-readout-select','org-color-select'])$(id).onchange=organoid;
options('rheo-curve-select',[...new Set(r.predictions.map(t=>t.curve))]);options('rheo-conc-select',[...new Set(r.frequency_curves.map(t=>t.concentration_mg_ml))]);options('rheo-model-select',[...new Set(r.predictions.map(t=>t.model))]);
let point=0;
function rheology(){const mode=$('rheo-view-select').value,model=$('rheo-model-select').value,curve=+$('rheo-curve-select').value,conc=+$('rheo-conc-select').value,full=mode==='full_fit_mean';$('rheo-curve-group').hidden=full;$('rheo-conc-group').hidden=!full;
 const data=(full?r.frequency_curves.filter(t=>t.model===model&&t.concentration_mg_ml===conc).map(t=>({...t,observed_Gp_Pa:t.observed_mean_Gp_Pa,observed_Gpp_Pa:t.observed_mean_Gpp_Pa,predicted_Gp_Pa:t.fitted_Gp_Pa,predicted_Gpp_Pa:t.fitted_Gpp_Pa})):r.predictions.filter(t=>t.mode===mode&&t.model===model&&t.curve===curve)).sort((a,b)=>a.omega_rad_s-b.omega_rad_s);
 point=Math.max(0,Math.min(point,data.length-1));options('rheo-point-select',data.map((_,i)=>i),i=>`${i+1}: ω=${fmt(data[i].omega_rad_s)} rad/s`);$('rheo-point-select').value=point;
 const choose=id=>{point=id;rheology()},base={xLabel:'Angular frequency ω (rad/s, log axis)',yLabel:'Signed modulus (Pa)',log:true,zero:true,selected:point,select:choose};
 const series=[['observed_Gp_Pa','#166d66','Observed G′',false,'observed_sd_Gp_Pa'],['predicted_Gp_Pa','#56a69c','Predicted/fit G′',true],['observed_Gpp_Pa','#a1472b','Observed G″',false,'observed_sd_Gpp_Pa'],['predicted_Gpp_Pa','#db8a62','Predicted/fit G″',true]].map(([key,color,label,dash,sd])=>({color,label,dash,points:data.map((t,i)=>({x:t.omega_rad_s,y:t[key],id:i,sd:full&&sd?t[sd]:undefined}))}));chart('rheo-main-svg',series,base);
 chart('rheo-res-svg',[['Gp','#166d66'],['Gpp','#a1472b']].map(([k,color])=>({color,label:'Δ'+k,points:data.map((t,i)=>({x:t.omega_rad_s,y:t['predicted_'+k+'_Pa']-t['observed_'+k+'_Pa'],id:i}))})),{...base,yLabel:'Predicted − observed (Pa)'});
 const mapped=data.map(t=>({...t,frequency_hz:t.omega_rad_s/(2*Math.PI),resGp:t.predicted_Gp_Pa-t.observed_Gp_Pa,resGpp:t.predicted_Gpp_Pa-t.observed_Gpp_Pa}));table('rheo-sweep-tbody',mapped,['omega_rad_s','frequency_hz','band','observed_Gp_Pa','predicted_Gp_Pa','resGp','observed_Gpp_Pa','predicted_Gpp_Pa','resGpp']);detail('rheo-point-detail',mapped[point]||{status:'No saved points'});
 table('rheo-score-tbody',full?[]:r.scores.filter(t=>t.mode===mode&&t.model===model&&t.curve===curve),['band','points','complex_NRMSE','complex_RMSE_Pa','Gp_NRMSE','Gpp_NRMSE','scale_Pa']);$('rheo-score-subtitle').textContent=full?'Full fit view: held-out scores are not applicable to this view.':'Saved matching held-out scores; no refitting.';table('rheo-boot-tbody',r.bootstrap_parameters.filter(t=>t.model===model),['model','parameter','full_fit','q025','median','q975']);$('rheo-main-subtitle').textContent=`${mode} · ${model} · ${data.length} saved frequencies. ${full?'Mean ± between-replicate SD; not a predictive interval.':'Observed values and saved held-out predictions; residuals are not uncertainty.'} Linear signed y preserves zeros and negatives.`;
}
for(const id of ['rheo-view-select','rheo-model-select','rheo-curve-select','rheo-conc-select'])$(id).onchange=()=>{point=0;rheology()};$('rheo-point-select').onchange=()=>{point=+$('rheo-point-select').value;rheology()};
organoid();rheology();$('status-banner').textContent=`Loaded ${o.gels.length} synthetic gels / ${o.trajectories.length} trajectory rows, ${r.measurements.length} measured rheology rows / ${r.predictions.length} held-out predictions. No new simulation or fitting.`;
}catch(e){$('status-banner').textContent='Saved results could not be rendered: '+e.message;console.error(e)}
})();
