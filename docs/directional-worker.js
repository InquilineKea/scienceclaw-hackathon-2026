'use strict';
importScripts('model.js','directional.js');
onmessage=({data})=>{try{const net=CollagenAtlas.build(data.family,data.seed??17,data.params||{});postMessage({net,...AtlasDirectional.simulate(net,data.angle)});}catch(e){postMessage({error:String(e.message||e)});}};
