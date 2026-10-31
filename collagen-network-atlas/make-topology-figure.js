'use strict';
// Original publisher: snapshots geometry and summarizes existing data; no scientific solves.
const fs=require('node:fs'),path=require('node:path'),A=require('./aging.js'),F=require('./topology-figure.js');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'data/density.json'),'utf8')),maps={};
for(const family of Object.keys(F.names)){
 const a=A.build(family,17,{count:24,pattern:'distributed'}),b=A.build(family,17,{count:24,pattern:'clustered'});
 maps[family]={X:a.X,edges:a.edges.map(({i,j})=>({i,j})),links:{distributed:a.links.map(({i,j})=>({i,j})),clustered:b.links.map(({i,j})=>({i,j}))}};
}
fs.writeFileSync(path.join(__dirname,'data/topology-maps.js'),'globalThis.TOPOLOGY_MAPS='+JSON.stringify(maps)+';\n');
fs.writeFileSync(path.join(__dirname,'figures/topology-aging-overview.svg'),F.overview(data,maps));
const checks=[];
for(const family of ['isotropic','modular'])for(const pattern of ['distributed','clustered'])for(const metric of ['stiffness','work','failureStrain']){const v=F.stats(data,family,pattern,24,0,metric);if(!v.resolved)throw Error('Figure must not present an unresolved result without marking');checks.push({family,pattern,metric,...v});}
fs.writeFileSync(path.join(__dirname,'figures/topology-aging-values.json'),JSON.stringify({sourceSnapshot:'f6d5714bfb8a6354b63d17fe6fbc4ab4a10f2fdb',count:24,angle:0,mapSeed:17,metricSeeds:[17,29,43],checks},null,2)+'\n');
console.log(JSON.stringify({networks:Object.keys(maps).length,figureChecks:checks.length,solverRuns:0}));
