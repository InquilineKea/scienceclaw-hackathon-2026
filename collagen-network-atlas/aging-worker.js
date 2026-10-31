'use strict';
importScripts('model.js','directional.js','aging.js');
onmessage=({data})=>{try{
 const {family,seed,angle,parameters}=data,reference=AtlasAging.build(family,seed,{...parameters,count:0}),modified=AtlasAging.build(family,seed,parameters);
 const pair=[{net:reference,...AtlasAging.simulate(reference,angle)},{net:modified,...AtlasAging.simulate(modified,angle)}];postMessage({type:'pair',pair});
 if(data.sweep){const rows=[];for(let a=0;a<180;a+=15){rows.push({angle:a,...AtlasAging.simulate(modified,a,{frames:false}).metrics});postMessage({type:'progress',done:rows.length,total:12});}postMessage({type:'sweep',rows});}
 postMessage({type:'done'});
}catch(e){postMessage({type:'error',error:String(e.message||e)});}};
