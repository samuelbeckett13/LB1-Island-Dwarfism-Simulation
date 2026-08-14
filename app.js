(() => {
  "use strict";

  function initSimulator() {
    const $ = (s) => document.querySelector(s);
    const required = [
      "#baseline","#family","#scale","#brainExp","#igf","#iodine","#overlap","#retention","#multi",
      "#femur","#icv","#crural","#hfi","#ffi","#distance","#distanceBig","#grid","#marks"
    ];

    const missing = required.filter(s => !$(s));
    const statusDot = $("#statusDot");
    const statusText = $("#statusText");

    if (missing.length) {
      if (statusDot) statusDot.classList.add("error");
      if (statusText) statusText.textContent = "Simulator error: page assets are out of sync.";
      console.error("LB1 simulator missing elements:", missing);
      return;
    }

    const C = {
      baseline: $("#baseline"), family: $("#family"), scale: $("#scale"),
      brainExp: $("#brainExp"), igf: $("#igf"), iodine: $("#iodine"),
      overlap: $("#overlap"), retention: $("#retention"), multi: $("#multi")
    };

    const REF = {femur:434, icv:1341, crural:83.5, hfi:71.5, ffi:54.2};
    const SD  = {femur:24,  icv:100,  crural:2.3, hfi:2.3, ffi:2.5};
    const LB1 = {femur:280, icv:430,  crural:83.9, hfi:87.8, ffi:70};

    function clamp(x, lo=0, hi=.95) { return Math.min(hi, Math.max(lo, x)); }

    function calc() {
      const scale = Number(C.scale.value)/100;
      const exp = Number(C.brainExp.value)/100;
      const igf = Number(C.igf.value)/100;
      const iod = Number(C.iodine.value)/100;
      const ov = Number(C.overlap.value)/100;
      const ret = Number(C.retention.value)/100;
      const multiTransmission = Number(C.multi.value)/100;
      const b = C.baseline.value;
      const f = C.family.value;

      let baseFem = REF.femur;
      let baseICV = REF.icv;

      if (b !== "modern") baseFem = REF.femur * scale;
      if (b === "flores") baseICV = REF.icv * Math.pow(scale, exp);
      if (b === "bodyOnly") baseICV = REF.icv;

      const transmissionNormalized = Math.max(0, Math.min(1, (multiTransmission - 0.10) / 0.19));
      const susceptibility = (f === "full") ? (1 + .145 * transmissionNormalized) : 1;
      let boneLoss = 0;
      let brainLoss = 0;

      if (["igf","igfIodine","full"].includes(f)) {
        const igfBone = clamp(igf * .82 * ov * Math.max(.60, ret) * susceptibility);
        const igfBrain = clamp(igf * .50 * ov * Math.max(.45, ret) * susceptibility);
        boneLoss = 1 - (1-boneLoss)*(1-igfBone);
        brainLoss = 1 - (1-brainLoss)*(1-igfBrain);
      }

      if (["iodine","igfIodine","full"].includes(f)) {
        const iodineBone = clamp(iod * .20 * ov * (.10 + .60*ret) * susceptibility);
        const iodineBrain = clamp(iod * .72 * ov * (.60 + .40*ret) * susceptibility);
        boneLoss = 1 - (1-boneLoss)*(1-iodineBone);
        brainLoss = 1 - (1-brainLoss)*(1-iodineBrain);
      }

      if (f === "none") {
        boneLoss = 0;
        brainLoss = 0;
      }

      boneLoss = clamp(boneLoss);
      brainLoss = clamp(brainLoss);

      const femur = baseFem * (1-boneLoss);
      const icv = baseICV * (1-brainLoss);

      const tibLoss = clamp(boneLoss*.98);
      const humLoss = clamp(boneLoss*.74*(1-.04*iod));
      const footLoss = clamp(boneLoss*.60*(1-.04*iod));

      const baseTibia = baseFem*(REF.crural/100);
      const baseHum = baseFem*(REF.hfi/100);
      const baseFoot = baseFem*(REF.ffi/100);

      const tibia = baseTibia*(1-tibLoss);
      const humerus = baseHum*(1-humLoss);
      const foot = baseFoot*(1-footLoss);

      const crural = 100*tibia/femur;
      const hfi = 100*humerus/femur;
      const ffi = 100*foot/femur;

      const z = {
        femur:(femur-LB1.femur)/SD.femur,
        icv:(icv-LB1.icv)/SD.icv,
        crural:(crural-LB1.crural)/SD.crural,
        hfi:(hfi-LB1.hfi)/SD.hfi,
        ffi:(ffi-LB1.ffi)/SD.ffi
      };

      const score = Object.values(z).reduce((sum,v)=>sum+v*v,0);
      return {baseFem,baseICV,femur,icv,crural,hfi,ffi,boneLoss,brainLoss,score,z};
    }

    function draw(x) {
      const grid = $("#grid");
      const marks = $("#marks");
      const L=68,R=725,T=28,B=365,x0=180,x1=460,y0=250,y1=1450;
      const sx=v=>L+(v-x0)/(x1-x0)*(R-L);
      const sy=v=>B-(v-y0)/(y1-y0)*(B-T);
      let g="";

      [200,250,300,350,400,450].forEach(v=>{
        const X=sx(v);
        g += `<line x1="${X}" y1="${T}" x2="${X}" y2="${B}" stroke="#83b8d1" stroke-opacity=".15"/>`;
        g += `<text x="${X}" y="394" fill="#6f8997" font-size="11" text-anchor="middle">${v}</text>`;
      });

      [400,600,800,1000,1200,1400].forEach(v=>{
        const Y=sy(v);
        g += `<line x1="${L}" y1="${Y}" x2="${R}" y2="${Y}" stroke="#83b8d1" stroke-opacity=".15"/>`;
        g += `<text x="53" y="${Y+4}" fill="#6f8997" font-size="11" text-anchor="end">${v}</text>`;
      });

      g += `<text x="397" y="420" fill="#8aa6b5" font-size="12" text-anchor="middle">Femur length (mm)</text>`;
      g += `<text x="17" y="196" fill="#8aa6b5" font-size="12" text-anchor="middle" transform="rotate(-90 17 196)">Endocranial volume (cc)</text>`;
      grid.innerHTML = g;

      const pts = [
        [REF.femur,REF.icv,"#748b97",8,"Reference"],
        [LB1.femur,LB1.icv,"#f49b4b",10,"LB1"],
        [x.femur,x.icv,"#70d0ff",11,"Current model"]
      ];

      marks.innerHTML = pts.map(p =>
        `<circle cx="${sx(p[0])}" cy="${sy(p[1])}" r="${p[3]+6}" fill="${p[2]}" opacity=".08"/>` +
        `<circle cx="${sx(p[0])}" cy="${sy(p[1])}" r="${p[3]}" fill="${p[2]}" stroke="white" stroke-opacity=".55"/>` +
        `<text x="${sx(p[0])+14}" y="${sy(p[1])-13}" fill="${p[2]}" font-size="11">${p[4]}</text>`
      ).join("");
    }

    function traitBar(barSel,textSel,z,val,target,digits=1) {
      const bar = $(barSel);
      const text = $(textSel);
      if (bar) bar.style.width = Math.min(100,Math.abs(z)/4*100) + "%";
      if (text) text.textContent = `${Number(val).toFixed(digits)} · target ${target}`;
    }

    function setText(sel, value) {
      const el = $(sel);
      if (el) el.textContent = value;
    }

    function update() {
      const x = calc();

      setText("#scaleOut",(Number(C.scale.value)/100).toFixed(2)+"×");
      setText("#expOut",(Number(C.brainExp.value)/100).toFixed(2));
      setText("#igfOut",C.igf.value+"%");
      setText("#iodineOut",C.iodine.value+"%");
      setText("#overlapOut",C.overlap.value+"%");
      setText("#retentionOut",C.retention.value+"%");
      setText("#multiOut",(Number(C.multi.value)/100).toFixed(2));

      setText("#femur",x.femur.toFixed(1));
      setText("#icv",x.icv.toFixed(0));
      setText("#crural",x.crural.toFixed(1));
      setText("#hfi",x.hfi.toFixed(1));
      setText("#ffi",x.ffi.toFixed(1));
      setText("#distance",x.score.toFixed(2));
      setText("#distanceBig",x.score.toFixed(2));

      setText("#baselineFemur",x.baseFem.toFixed(1)+" mm");
      setText("#baselineICV",x.baseICV.toFixed(0)+" cc");
      setText("#femurLoss",(x.boneLoss*100).toFixed(1)+"%");
      setText("#brainLoss",(x.brainLoss*100).toFixed(1)+"%");

      const fit = x.score<5 ? "Very close" : x.score<10 ? "Close region" : x.score<20 ? "Moderate fit" : "Large mismatch";
      setText("#fitLabel",fit);

      traitBar("#barFemur","#traitFemur",x.z.femur,x.femur,LB1.femur,1);
      traitBar("#barICV","#traitICV",x.z.icv,x.icv,LB1.icv,0);
      traitBar("#barCrural","#traitCrural",x.z.crural,x.crural,LB1.crural,1);
      traitBar("#barHFI","#traitHFI",x.z.hfi,x.hfi,LB1.hfi,1);
      traitBar("#barFFI","#traitFFI",x.z.ffi,x.ffi,LB1.ffi,1);

      const b = C.baseline.value;
      const f = C.family.value;
      const familyText = f==="full" ? "full IGF + iodine + literature-anchored intergenerational architecture"
        : f==="igfIodine" ? "IGF + iodine without multigenerational modifier"
        : f==="igf" ? "IGF only"
        : f==="iodine" ? "iodine–thyroid only"
        : "no developmental insult";

      setText("#modelNote",
        `${b==="modern" ? "Modern benchmark" : "Flores baseline"}; ${familyText}. ` +
        `Browser outputs are explanatory; thesis inference comes from the frozen Python Monte Carlo model.`
      );

      draw(x);
    }

    Object.values(C).forEach(el => {
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });

    const presets = {
      "#pFull": () => {
        C.baseline.value="flores"; C.family.value="full"; C.scale.value=74; C.brainExp.value=190;
        C.igf.value=70; C.iodine.value=72; C.overlap.value=68; C.retention.value=82; C.multi.value=18;
      },
      "#pIodine": () => {
        C.baseline.value="flores"; C.family.value="igfIodine"; C.scale.value=75; C.brainExp.value=200;
        C.igf.value=70; C.iodine.value=82; C.overlap.value=74; C.retention.value=86; C.multi.value=10;
      },
      "#pBaseline": () => {
        C.baseline.value="flores"; C.family.value="none"; C.scale.value=72; C.brainExp.value=190;
        C.igf.value=0; C.iodine.value=0; C.overlap.value=0; C.retention.value=0; C.multi.value=10;
      }
    };

    Object.entries(presets).forEach(([sel,fn]) => {
      const btn = $(sel);
      if (btn) btn.addEventListener("click", e => {
        e.preventDefault();
        fn();
        update();
      });
    });

    update();
    if (statusDot) statusDot.classList.add("ready");
    if (statusText) statusText.textContent = "Version 14 definitive simulator ready — controls update live.";
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSimulator);
  } else {
    initSimulator();
  }
})();