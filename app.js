
const $=s=>document.querySelector(s);

const C={
  family:$('#modelFamily'), severity:$('#severity'), start:$('#start'),
  duration:$('#duration'), bone:$('#bone'), brain:$('#brain'), persist:$('#persist')
};

const REF={femur:397.47,icv:1387};
const LB1={femur:280,icv:430};

function compute(){
  const fam=C.family.value;
  let severity=+C.severity.value/100;
  let bone=+C.bone.value/100;
  let brain=+C.brain.value/100;
  let persist=+C.persist.value/100;
  const start=+C.start.value;
  const duration=+C.duration.value;

  let note='';
  if(fam==='igf'){
    bone=Math.max(.55,bone);
    brain=Math.max(.25*bone,Math.min(.75*bone,brain));
    persist=Math.max(.45,persist);
    note='Persistent IGF analogue: skeletal effects are constrained to exceed cranial effects.';
  }else if(fam==='fgr'){
    bone=Math.max(.35,Math.min(.85,bone));
    brain=Math.max(.05,Math.min(.40,brain));
    persist=Math.min(.45,persist);
    note='Transient FGR analogue: relative cranial sparing and stronger postnatal catch-up are enforced.';
  }else if(fam==='gc'){
    severity=Math.min(.08,severity);
    bone=.01;brain=.012;persist=.20;
    note='Glucocorticoid analogue: only modest human-observed growth effects are allowed.';
  }else{
    note='Uniform scaling applies the same proportional reduction to both selected endpoints.';
  }

  let femur,icv;

  if(fam==='uniform'){
    femur=REF.femur*(1-severity);
    icv=REF.icv*(1-severity);
  }else{
    const timing=Math.max(.16,Math.min(.72,(duration/16)*(.72-Math.abs(start-25)/70)));
    const boneLoss=Math.min(.95,severity*bone*(timing+persist*(1-timing)));
    const brainLoss=Math.min(.95,severity*brain*(timing+persist*(1-timing)));
    femur=REF.femur*(1-boneLoss);
    icv=REF.icv*(1-brainLoss);
  }

  const distance=((femur-LB1.femur)/27.46)**2 + ((icv-LB1.icv)/77)**2;
  return {fam,femur,icv,distance,start,duration,note};
}

function drawPlot(x){
  const svg=$('#phenotypePlot');
  const grid=$('#gridLines');
  const marks=$('#plotMarks');
  grid.innerHTML=''; marks.innerHTML='';

  const L=68,R=725,T=28,B=365;
  const xmin=150,xmax=430,ymin=300,ymax=1500;

  function sx(v){return L+(v-xmin)/(xmax-xmin)*(R-L)}
  function sy(v){return B-(v-ymin)/(ymax-ymin)*(B-T)}
  function line(x1,y1,x2,y2,stroke,op=.18,dash=''){
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-opacity="${op}" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
  }

  let gh='';
  [200,250,300,350,400].forEach(v=>{
    const xx=sx(v);
    gh+=line(xx,T,xx,B,'#83b8d1');
    gh+=`<text x="${xx}" y="394" fill="#6f8997" font-size="11" text-anchor="middle">${v}</text>`;
  });
  [400,600,800,1000,1200,1400].forEach(v=>{
    const yy=sy(v);
    gh+=line(L,yy,R,yy,'#83b8d1');
    gh+=`<text x="53" y="${yy+4}" fill="#6f8997" font-size="11" text-anchor="end">${v}</text>`;
  });
  gh+=`<text x="${(L+R)/2}" y="420" fill="#8aa6b5" font-size="12" text-anchor="middle">Femur length (mm)</text>`;
  gh+=`<text x="17" y="${(T+B)/2}" fill="#8aa6b5" font-size="12" text-anchor="middle" transform="rotate(-90 17 ${(T+B)/2})">Endocranial volume (cc)</text>`;
  grid.innerHTML=gh;

  const points=[
    {x:REF.femur,y:REF.icv,c:'#718995',r:8,label:'Reference'},
    {x:LB1.femur,y:LB1.icv,c:'#f49b4b',r:10,label:'LB1'},
    {x:x.femur,y:x.icv,c:'#70d0ff',r:11,label:'Current model'}
  ];

  marks.innerHTML=points.map(p=>`
    <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="${p.r+6}" fill="${p.c}" opacity=".08"/>
    <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="${p.r}" fill="${p.c}" stroke="#fff" stroke-opacity=".55" stroke-width="1.2"/>
    <text x="${sx(p.x)+14}" y="${sy(p.y)-13}" fill="${p.c}" font-size="11">${p.label}</text>
  `).join('');
}

function update(){
  const x=compute();

  $('#severityOut').textContent=C.severity.value+'%';
  $('#startOut').textContent=C.start.value+' weeks';
  $('#durationOut').textContent=C.duration.value+' weeks';
  $('#boneOut').textContent=C.bone.value+'%';
  $('#brainOut').textContent=C.brain.value+'%';
  $('#persistOut').textContent=C.persist.value+'%';

  $('#constraintText').textContent=x.note;

  $('#femurValue').textContent=x.femur.toFixed(1);
  $('#icvValue').textContent=x.icv.toFixed(0);
  $('#distanceValue').textContent=x.distance.toFixed(2);
  $('#distanceBig').textContent=x.distance.toFixed(2);

  $('#femurBar').style.width=Math.min(100,x.femur/REF.femur*100)+'%';
  $('#icvBar').style.width=Math.min(100,x.icv/REF.icv*100)+'%';

  const end=Math.min(40,x.start+x.duration);
  $('#windowLabel').textContent=x.start+' → '+end+' weeks';
  $('#window').style.left=(x.start/40*100)+'%';
  $('#window').style.width=((end-x.start)/40*100)+'%';

  let fit,interp;
  if(x.distance<2){fit='Very close';interp='This parameter set approaches the selected LB1 target closely.'}
  else if(x.distance<20){fit='Relatively close';interp='The current scenario approaches the selected target but retains measurable mismatch.'}
  else if(x.distance<70){fit='Moderate mismatch';interp='The current scenario reproduces part of the phenotype but not both endpoints simultaneously.'}
  else{fit='Large mismatch';interp='The current scenario remains far from the selected LB1 phenotype.'}

  $('#fitText').textContent=fit;
  $('#interpretation').textContent=interp;

  drawPlot(x);
}

Object.values(C).forEach(el=>el.addEventListener('input',update));

$('#defaultPreset').addEventListener('click',()=>{
  C.family.value='igf';C.severity.value=62;C.start.value=22;C.duration.value=8;C.bone.value=85;C.brain.value=45;C.persist.value=74;update();
});
$('#mildPreset').addEventListener('click',()=>{
  C.family.value='fgr';C.severity.value=28;C.start.value=25;C.duration.value=5;C.bone.value=48;C.brain.value=20;C.persist.value=24;update();
});
$('#highPreset').addEventListener('click',()=>{
  C.family.value='igf';C.severity.value=82;C.start.value=20;C.duration.value=12;C.bone.value=94;C.brain.value=70;C.persist.value=90;update();
});

update();
