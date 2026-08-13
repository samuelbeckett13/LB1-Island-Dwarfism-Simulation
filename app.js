const $=s=>document.querySelector(s);
const C={baseline:$('#baseline'),family:$('#family'),scale:$('#scale'),brainExp:$('#brainExp'),igf:$('#igf'),iodine:$('#iodine'),overlap:$('#overlap'),retention:$('#retention'),multi:$('#multi')};
const REF={femur:434,icv:1341,crural:83.5,hfi:71.5,ffi:54.2};
const SD={femur:24,icv:100,crural:2.3,hfi:2.3,ffi:2.5};
const LB1={femur:280,icv:430,crural:83.9,hfi:87.8,ffi:70};

function calc(){
 let scale=+C.scale.value/100,exp=+C.brainExp.value/100,igf=+C.igf.value/100,iod=+C.iodine.value/100,ov=+C.overlap.value/100,ret=+C.retention.value/100,multi=+C.multi.value/100;
 let b=C.baseline.value,f=C.family.value;
 let baseFem=REF.femur,baseICV=REF.icv;
 if(b!=='modern') baseFem=REF.femur*scale;
 if(b==='flores') baseICV=REF.icv*Math.pow(scale,exp);
 if(b==='bodyOnly') baseICV=REF.icv;

 let sus=(f==='full')?1+0.5*multi:1;
 let boneLoss=0,brainLoss=0;
 if(f==='igf'||f==='igfIodine'||f==='full'){
   boneLoss=1-(1-boneLoss)*(1-Math.min(.95,igf*.82*ov*Math.max(.60,ret)*sus));
   brainLoss=1-(1-brainLoss)*(1-Math.min(.95,igf*.50*ov*Math.max(.45,ret)*sus));
 }
 if(f==='iodine'||f==='igfIodine'||f==='full'){
   let iBone=Math.min(.95,iod*.20*ov*(.10+.60*ret)*sus);
   let iBrain=Math.min(.95,iod*.72*ov*(.60+.40*ret)*sus);
   boneLoss=1-(1-boneLoss)*(1-iBone);
   brainLoss=1-(1-brainLoss)*(1-iBrain);
 }
 if(f==='none'){boneLoss=0;brainLoss=0}

 boneLoss=Math.min(.95,Math.max(0,boneLoss));brainLoss=Math.min(.95,Math.max(0,brainLoss));
 let femur=baseFem*(1-boneLoss),icv=baseICV*(1-brainLoss);

 // explanatory segment response mirroring V13 architecture
 let tibLoss=Math.min(.95,boneLoss*.98);
 let humLoss=Math.min(.95,boneLoss*.74*(1-.04*iod));
 let footLoss=Math.min(.95,boneLoss*.60*(1-.04*iod));
 let baseTibia=baseFem*(REF.crural/100);
 let baseHum=baseFem*(REF.hfi/100);
 let baseFoot=baseFem*(REF.ffi/100);
 let tib=baseTibia*(1-tibLoss),hum=baseHum*(1-humLoss),foot=baseFoot*(1-footLoss);
 let crural=100*tib/femur,hfi=100*hum/femur,ffi=100*foot/femur;

 let z={
  femur:(femur-LB1.femur)/SD.femur,
  icv:(icv-LB1.icv)/SD.icv,
  crural:(crural-LB1.crural)/SD.crural,
  hfi:(hfi-LB1.hfi)/SD.hfi,
  ffi:(ffi-LB1.ffi)/SD.ffi
 };
 let score=z.femur*z.femur+z.icv*z.icv+z.crural*z.crural+z.hfi*z.hfi+z.ffi*z.ffi;
 return {baseFem,baseICV,femur,icv,crural,hfi,ffi,boneLoss,brainLoss,score,z};
}
function draw(x){
 const grid=$('#grid'),marks=$('#marks');let L=68,R=725,T=28,B=365,x0=180,x1=460,y0=250,y1=1450,sx=v=>L+(v-x0)/(x1-x0)*(R-L),sy=v=>B-(v-y0)/(y1-y0)*(B-T),g='';
 [200,250,300,350,400,450].forEach(v=>{let X=sx(v);g+=`<line x1="${X}" y1="${T}" x2="${X}" y2="${B}" stroke="#83b8d1" stroke-opacity=".15"/><text x="${X}" y="394" fill="#6f8997" font-size="11" text-anchor="middle">${v}</text>`});
 [400,600,800,1000,1200,1400].forEach(v=>{let Y=sy(v);g+=`<line x1="${L}" y1="${Y}" x2="${R}" y2="${Y}" stroke="#83b8d1" stroke-opacity=".15"/><text x="53" y="${Y+4}" fill="#6f8997" font-size="11" text-anchor="end">${v}</text>`});
 g+=`<text x="397" y="420" fill="#8aa6b5" font-size="12" text-anchor="middle">Femur length (mm)</text><text x="17" y="196" fill="#8aa6b5" font-size="12" text-anchor="middle" transform="rotate(-90 17 196)">Endocranial volume (cc)</text>`;
 grid.innerHTML=g;
 let pts=[[REF.femur,REF.icv,'#748b97',8,'Reference'],[LB1.femur,LB1.icv,'#f49b4b',10,'LB1'],[x.femur,x.icv,'#70d0ff',11,'Current model']];
 marks.innerHTML=pts.map(p=>`<circle cx="${sx(p[0])}" cy="${sy(p[1])}" r="${p[3]+6}" fill="${p[2]}" opacity=".08"/><circle cx="${sx(p[0])}" cy="${sy(p[1])}" r="${p[3]}" fill="${p[2]}" stroke="white" stroke-opacity=".55"/><text x="${sx(p[0])+14}" y="${sy(p[1])-13}" fill="${p[2]}" font-size="11">${p[4]}</text>`).join('');
}
function traitBar(idBar,idText,z,val,target,digits=1){
 let pct=Math.min(100,Math.abs(z)/4*100);$(idBar).style.width=pct+'%';$(idText).textContent=`${Number(val).toFixed(digits)} · target ${target}`;
}
function update(){
 let x=calc();
 $('#scaleOut').textContent=(+C.scale.value/100).toFixed(2)+'×';$('#expOut').textContent=(+C.brainExp.value/100).toFixed(2);$('#igfOut').textContent=C.igf.value+'%';$('#iodineOut').textContent=C.iodine.value+'%';$('#overlapOut').textContent=C.overlap.value+'%';$('#retentionOut').textContent=C.retention.value+'%';$('#multiOut').textContent=C.multi.value+'%';
 $('#femur').textContent=x.femur.toFixed(1);$('#icv').textContent=x.icv.toFixed(0);$('#crural').textContent=x.crural.toFixed(1);$('#hfi').textContent=x.hfi.toFixed(1);$('#ffi').textContent=x.ffi.toFixed(1);$('#distance').textContent=x.score.toFixed(2);$('#distanceBig').textContent=x.score.toFixed(2);
 $('#baselineFemur').textContent=x.baseFem.toFixed(1)+' mm';$('#baselineICV').textContent=x.baseICV.toFixed(0)+' cc';$('#femurLoss').textContent=(x.boneLoss*100).toFixed(1)+'%';$('#brainLoss').textContent=(x.brainLoss*100).toFixed(1)+'%';
 let fit=x.score<5?'Very close':x.score<10?'Close region':x.score<20?'Moderate fit':'Large mismatch';$('#fitLabel').textContent=fit;
 traitBar('#barFemur','#traitFemur',x.z.femur,x.femur,LB1.femur,1);traitBar('#barICV','#traitICV',x.z.icv,x.icv,LB1.icv,0);traitBar('#barCrural','#traitCrural',x.z.crural,x.crural,LB1.crural,1);traitBar('#barHFI','#traitHFI',x.z.hfi,x.hfi,LB1.hfi,1);traitBar('#barFFI','#traitFFI',x.z.ffi,x.ffi,LB1.ffi,1);
 let f=C.family.value,b=C.baseline.value;$('#modelNote').textContent=`${b==='modern'?'Modern benchmark':'Flores baseline'}; ${f==='full'?'full IGF + iodine + multigenerational architecture':f==='igfIodine'?'IGF + iodine without multigenerational modifier':f==='igf'?'IGF only':f==='iodine'?'iodine–thyroid only':'no developmental insult'}. Browser outputs are explanatory, not thesis-run Monte Carlo results.`;
 draw(x);
}
Object.values(C).forEach(e=>e.addEventListener('input',update));
$('#pFull').onclick=()=>{C.baseline.value='flores';C.family.value='full';C.scale.value=74;C.brainExp.value=190;C.igf.value=70;C.iodine.value=72;C.overlap.value=68;C.retention.value=82;C.multi.value=18;update()};
$('#pIodine').onclick=()=>{C.baseline.value='flores';C.family.value='igfIodine';C.scale.value=75;C.brainExp.value=200;C.igf.value=70;C.iodine.value=82;C.overlap.value=74;C.retention.value=86;C.multi.value=0;update()};
$('#pBaseline').onclick=()=>{C.baseline.value='flores';C.family.value='none';C.scale.value=72;C.brainExp.value=190;C.igf.value=0;C.iodine.value=0;C.overlap.value=0;C.retention.value=0;C.multi.value=0;update()};
update();