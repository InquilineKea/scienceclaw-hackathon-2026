(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('h100-data').textContent);
  const el = id => document.getElementById('h100-' + id);
  const colors = {uniform:'#85d5c2', clustered:'#f3a467', muted:'#a5b9cb', line:'#35475d', text:'#e3edfa'};
  const fmt = (value, retention, signed=false) => {
    const n = retention ? value * 100 : value;
    return (signed && n > 0 ? '+' : '') + (Math.abs(n) < 1e-12 ? '0' : n.toFixed(retention ? 2 : 5)).replace('-', '−');
  };
  const text = (x,y,s,extra='') => `<text x="${x}" y="${y}" fill="${colors.muted}" font-family="system-ui,sans-serif" font-size="16" ${extra}>${s}</text>`;
  const line = (x1,y1,x2,y2,color=colors.line,extra='') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" ${extra}/>`;
  function plotPairs(row, retention) {
    const pairs = row.pairs.filter(p => p.included);
    const max = retention ? 1.05 : Math.max(...pairs.flatMap(p=>[p.uniform.value,p.clustered.value])) * 1.15;
    const top=42,bottom=300,xu=180,xc=395;
    const y = value => bottom - value / max * (bottom-top);
    let svg=`<svg viewBox="0 0 520 370" role="img" aria-labelledby="h100-pairs-title"><title id="h100-pairs-title">${row.valid_pairs} included pairs: uniform mean ${fmt(row.uniform_mean,retention)}${retention?' percent':''}; clustered mean ${fmt(row.clustered_mean,retention)}${retention?' percent':''}</title>`;
    svg+=text(68,23,retention?'Stress retained (%)':'RMS segment strain (dimensionless)');
    for(let i=0;i<=4;i++){
      const value=(retention?1:max)*i/4,yy=y(value);
      svg+=line(80,yy,480,yy)+text(68,yy+5,retention?String(Math.round(value*100)):value.toFixed(4),'text-anchor="end"');
    }
    for(const p of pairs){
      const jitter=((p.seed%7)-3)*3;
      svg+=line(xu+jitter,y(p.uniform.value),xc+jitter,y(p.clustered.value),'#7a8b9e','opacity=".4"');
      for(const [arch,x] of [['uniform',xu+jitter],['clustered',xc+jitter]]) svg+=`<circle cx="${x}" cy="${y(p[arch].value)}" r="4.5" fill="${colors[arch]}" stroke="#101926" stroke-width=".7"><title>Seed ${p.seed}: ${arch} ${fmt(p[arch].value,retention)}${retention?'%':''}</title></circle>`;
    }
    for(const [arch,x] of [['uniform',xu],['clustered',xc]]){
      const yy=y(row[arch+'_mean']);
      svg+=line(x-30,yy,x+30,yy,colors[arch],'stroke-width="4"');
      svg+=text(x,330,arch==='uniform'?'Uniform':'Clustered','text-anchor="middle"');
    }
    svg+='</svg>';
    el('pairs-plot').innerHTML=svg;
  }
  function plotContrast(row,retention){
    const extent=Math.max(Math.abs(row.bootstrap_low),Math.abs(row.bootstrap_high),Math.abs(row.paired_mean_difference),retention?.005:.0002)*1.35;
    const x=v=>280+v/extent*190;
    let svg=`<svg viewBox="0 0 520 260" role="img" aria-labelledby="h100-contrast-title"><title id="h100-contrast-title">Clustered minus uniform: ${fmt(row.paired_mean_difference,retention,true)}, 95 percent paired bootstrap interval ${fmt(row.bootstrap_low,retention,true)} to ${fmt(row.bootstrap_high,retention,true)} ${retention?'percentage points':'strain units'}</title>`;
    svg+=text(20,30,retention?'Difference in percentage points':'Difference in RMS strain');
    svg+=line(90,165,470,165)+line(x(0),55,x(0),184,'#d3e4f3','stroke-dasharray="5 5"');
    for(let i=-2;i<=2;i++){
      const value=extent*i/2,xx=x(value);
      svg+=line(xx,160,xx,170)+text(xx,192,fmt(value,retention,true),'text-anchor="middle" font-size="14"');
    }
    const lo=x(row.bootstrap_low),hi=x(row.bootstrap_high),mid=x(row.paired_mean_difference);
    svg+=line(lo,112,hi,112,colors.text,'stroke-width="4"');
    svg+=line(lo,101,lo,123,colors.text,'stroke-width="2"')+line(hi,101,hi,123,colors.text,'stroke-width="2"');
    svg+=`<circle cx="${mid}" cy="112" r="7" fill="${colors.text}"/>`;
    svg+=text(90,229,'Lower in clustered','text-anchor="start" font-size="14"')+text(470,229,'Higher in clustered','text-anchor="end" font-size="14"');
    el('contrast-plot').innerHTML=svg+'</svg>';
  }
  function render(){
    const [r,beta]=el('mechanism').value.split('|').map(Number);
    const row=data.records.find(d=>d.nodes===Number(el('size').value)&&d.kappa===Number(el('kappa').value)&&d.r===r&&d.beta===beta&&d.metric===el('metric').value);
    if(!row)throw new Error('No archived comparison for this selection');
    const retention=row.metric==='stress_retention',unit=retention?'%':'',diffUnit=retention?' pp':'';
    el('uniform').textContent=fmt(row.uniform_mean,retention)+unit;
    el('clustered').textContent=fmt(row.clustered_mean,retention)+unit;
    el('difference').textContent=fmt(row.paired_mean_difference,retention,true)+diffUnit;
    el('interval').textContent=`95% interval: ${fmt(row.bootstrap_low,retention,true)} to ${fmt(row.bootstrap_high,retention,true)}${diffUnit}`;
    el('count').textContent=`${row.valid_pairs} / ${row.attempted_pairs}`;
    el('excluded').textContent=`${row.attempted_pairs-row.valid_pairs} pairs excluded`;
    const spansZero=row.bootstrap_low<=0&&row.bootstrap_high>=0;
    let reading=spansZero?'The interval includes zero: the direction of this difference is uncertain.':`The interval is entirely ${row.bootstrap_high<0?'below':'above'} zero: ${retention?'retention':'RMS strain'} is ${row.bootstrap_high<0?'lower':'higher'} in the clustered networks for this comparison.`;
    if(retention&&r===1) reading='Elastic control: both architectures retain 100% of stress, with a zero paired difference.';
    el('reading').textContent=reading;
    el('pair-rule').textContent=retention?'Pairs require both complete hold trajectories to pass the numerical convergence flag.':'Pairs require both initial states to pass the convergence flag; later hold failures do not exclude an accepted initial-state value.';
    plotPairs(row,retention);plotContrast(row,retention);
    for(const arch of ['uniform','clustered']){
      el(arch+'-network').src=`h100/network-${row.nodes}-${arch}.svg`;
      el(arch+'-network').alt=`Saved ${arch} network topology, seed 0, ${row.nodes.toLocaleString()} nodes`;
    }
    el('topology-note').textContent=`Saved seed-0 topologies, shown undeformed: ${row.nodes.toLocaleString()} nodes and ${row.nodes===576?'1,036':'4,147'} retained segments per network. The examples illustrate connectivity, not the selected outcome. Periodic edges crossing the displayed cell boundary are omitted from the drawing.`;
    el('seed-table').replaceChildren();
    for(const p of row.pairs){
      const tr=document.createElement('tr');if(!p.included)tr.className='excluded';
      const failed=['uniform','clustered'].filter(a=>!p[a]?.valid);
      const difference=p.uniform?.value!=null&&p.clustered?.value!=null?fmt(p.clustered.value-p.uniform.value,retention,true)+diffUnit:'—';
      const cells=[p.seed,...['uniform','clustered'].map(a=>p[a]?.value==null?'—':fmt(p[a].value,retention)+unit),difference,p.included?'Included':`Excluded: ${failed.join(' and ')} convergence`];
      for(const value of cells){const td=document.createElement('td');td.textContent=value;tr.append(td);}
      el('seed-table').append(tr);
    }
  }
  for(const id of ['size','kappa','mechanism','metric']) el(id).addEventListener('change',render);
  render();
})();
