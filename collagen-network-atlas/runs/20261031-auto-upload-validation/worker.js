'use strict';
importScripts('model.js');
onmessage=e=>{try{const {family,seed,params,mode}=e.data,net=CollagenAtlas.build(family,seed,params),r=CollagenAtlas.simulate(net,mode),stats=CollagenAtlas.graphMetrics(net);postMessage({net,...r,stats});}catch(error){postMessage({error:String(error)});}};
