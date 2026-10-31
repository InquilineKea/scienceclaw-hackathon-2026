/* Original analysis of the unchanged crosslink solver. No changed physics. */
(function(root){
'use strict';
function beforeEvent(curve,predicate){
  const i=curve.findIndex(predicate);
  if(i<0)return {observed:false,lastIntactStrain:curve.at(-1).q,onsetStrain:null,work:null,storedEnergy:null};
  const a=curve[Math.max(0,i-1)],b=curve[i];
  return {observed:true,lastIntactStrain:a.q,onsetStrain:b.q,work:a.work,storedEnergy:a.energy};
}
function summarize(result){
  const c=result.curve,m=result.metrics;
  const any=beforeEvent(c,r=>r.damage>0||r.linkDamage>0),collagen=beforeEvent(c,r=>r.damage>0);
  const peak=c.reduce((a,b)=>b.force>a.force?b:a,c[0]);
  return {...m,firstDamageObserved:any.observed,firstDamageStrain:any.onsetStrain,lastIntactStrain:any.lastIntactStrain,workBeforeDamage:any.work,energyBeforeDamage:any.storedEnergy,
    collagenDamageObserved:collagen.observed,firstCollagenDamageStrain:collagen.onsetStrain,workBeforeCollagenDamage:collagen.work,
    strainAtPeak:peak.q,workToPeak:peak.work,largestCollagenDamageIncrement:Math.max(0,...c.map((r,i)=>r.damage-(i?c[i-1].damage:0)))};
}
function compareResolution(coarse,fine){
  const relative=(a,b)=>Number.isFinite(a)&&Number.isFinite(b)?Math.abs(b-a)/Math.max(Math.abs(a),Math.abs(b),1e-12):null;
  const d={stiffness:relative(coarse.stiffness,fine.stiffness),work:relative(coarse.work,fine.work),failureStrain:relative(coarse.failureStrain,fine.failureStrain),workBeforeDamage:relative(coarse.workBeforeDamage,fine.workBeforeDamage),workBeforeCollagenDamage:relative(coarse.workBeforeCollagenDamage,fine.workBeforeCollagenDamage)};
  const flag=k=>!coarse.valid||!fine.valid||d[k]===null||d[k]>=.05;
  return {relativeChanges:d,stiffnessUnresolved:!coarse.stiffnessValid||!fine.stiffnessValid||flag('stiffness'),workUnresolved:coarse.censored||fine.censored||coarse.criterion!==fine.criterion||flag('work'),failureStrainUnresolved:coarse.censored||fine.censored||coarse.criterion!==fine.criterion||flag('failureStrain'),workBeforeDamageUnresolved:flag('workBeforeDamage'),workBeforeCollagenDamageUnresolved:flag('workBeforeCollagenDamage')};
}
const api={version:'crosslink-density-v1',beforeEvent,summarize,compareResolution};root.AtlasDensity=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
