'use strict';
(()=>{
const F=TopologyFigure,D=ATLAS_DENSITY_DATA,M=TOPOLOGY_MAPS,$=id=>document.getElementById(id);
const metrics=[['stiffness','Stiffness'],['work','Work to failure criterion'],['failureStrain','Failure strain'],['workBeforeDamage','Work before first damage']];
function render(){
 const family=$('topFamily').value,count=+$('topCount').value,angle=+$('topAngle').value;
 $('topCountValue').textContent=`${count} / 36 nodes`; $('topAngleValue').textContent=angle+'°';
 $('topologyCards').innerHTML=['distributed','clustered'].map(pattern=>{
  const rows=metrics.map(([key,label])=>{const v=F.stats(D,family,pattern,count,angle,key);return `<tr><th scope="row">${label}</th><td>${v.mean===null?'Unavailable':v.mean.toFixed(2)+'×'}${v.resolved?'':' †'}<small>${v.min===null?'':'Range '+v.min.toFixed(2)+'–'+v.max.toFixed(2)+'×'}</small></td></tr>`}).join('');
  return `<article class="topology-card"><h3>${pattern==='distributed'?'Distributed local sites':'Central cluster'}</h3><svg viewBox="0 0 360 340" role="img" aria-label="${F.names[family]} with ${count} ${pattern} connectors; seed 17"><rect width="360" height="340" fill="white"/>${F.network(M[family],pattern,count,30,20,285)}</svg><table><caption>Mean of three paired seed ratios</caption><tbody>${rows}</tbody></table></article>`;
 }).join('');
 $('topologyStatus').textContent=`${F.names[family]} · ${count} added connectors · ${angle}° loading · saved 960-step results, checked against 480 steps. No new simulation is running.`;
}
for(const id of ['topFamily','topCount','topAngle'])$(id).addEventListener('input',render);render();
$('downloadPng').addEventListener('click',async()=>{
 const button=$('downloadPng');button.disabled=true;$('downloadStatus').textContent='Rendering the checked four-panel overview…';
 let source;
 try{source=URL.createObjectURL(new Blob([F.overview(D,M)],{type:'image/svg+xml'}));const img=new Image();await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=source});const canvas=document.createElement('canvas');canvas.width=3200;canvas.height=2240;canvas.getContext('2d').drawImage(img,0,0,3200,2240);const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('PNG encoding failed');let a=$('downloadReady');if(!a){a=document.createElement('a');a.id='downloadReady';document.querySelector('.downloads').append(a);}a.href=canvas.toDataURL('image/png');a.download='collagen-aging-topology-overview.png';a.textContent='Save PNG (3200 × 2240)';a.click();$('downloadStatus').textContent='PNG ready. Use the Save PNG link if the download did not start. Values match the vector overview and saved figure data.';}catch(e){$('downloadStatus').textContent='PNG export failed. The vector SVG and figure data remain available.';}finally{if(source)URL.revokeObjectURL(source);button.disabled=false;}
});
})();
