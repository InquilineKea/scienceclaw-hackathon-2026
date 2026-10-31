'use strict';
// Original bounded checks: annotations must agree with the unchanged solver.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const M=require('./model.js'),G=require('./load-guide.js'),D=require('./data/results.json');
const sandbox={};vm.runInNewContext(fs.readFileSync(__dirname+'/data/replays.js','utf8'),sandbox);
const R=sandbox.ATLAS_REPLAYS;let coordinateChecks=0,fabricChecks=0;
for(const mode of Object.keys(G.modes)){
 const net=R['aligned:'+mode].net,b=M.boundary(net,mode,.1);
 for(const marker of G.markers(net,mode))for(const [axis,held,drive]of [[0,marker.holdX,marker.driveX],[1,marker.holdY,marker.driveY]]){
  const id=2*marker.node+axis;assert.equal(held||drive!==0,b.fixed.has(id),mode+' coordinate '+id);
  if(held)assert.equal(b.deriv.get(id),0);
  if(drive)assert.equal(Math.sign(b.deriv.get(id)),drive);
  coordinateChecks++;
 }
 assert.equal(G.markers(net,mode).filter(m=>m.bodyX).length,['pulse','free'].includes(mode)?net.N:0);
}
for(const family of M.families){const net=R[family+':tension'].net,a=G.fabric(net),row=D.rows.find(r=>r.group==='topology'&&r.seed===17&&r.family===family&&r.mode==='tension');assert.ok(Math.abs(a.anisotropy-row.anisotropy)<1e-6);assert.ok(Math.abs(a.alignmentX-row.alignmentX)<1e-6);fabricChecks++;}
console.log(JSON.stringify({boundary_coordinate_checks:coordinateChecks,loading_modes:8,fabric_comparisons:fabricChecks,status:'passed'}));
