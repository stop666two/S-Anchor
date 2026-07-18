const fs = require('fs');
let h = fs.readFileSync('D:/administrator/Documents/project/S-Anchor/frontend/index.html', 'utf8');

// Replace the mode function to restructure columns
const oldMode = `function m(md){st.m=md;var b=document.querySelectorAll('.b');for(var i=0;i<b.length;i++)b[i].className='b'+(i===md?' a':'');var pp=$('pp');if(pp){var ch=pp.children;for(var i=2;i<ch.length;i++)ch[i].style.display=md===0?'':'none'}if(md===0&&st.cd)rw();else{$('cv').style.display='none';$('pn').style.display='flex'}lg(tk('extract'))}`;

const newMode = `function m(md){st.m=md;var b=document.querySelectorAll('.b');for(var i=0;i<b.length;i++)b[i].className='b'+(i===md?' a':'');var ec=$('ec'),er=$('er');if(ec)ec.style.display=md===0?'':'none';if(er)er.style.display=md===0?'':'none';var xr=$('xr'),xp=$('xp');if(xr)xr.style.display=md===0?'none':'';if(xp)xp.style.display=md===0?'':'none';if(md===0){if(st.cd)rw()}else{$('cv').style.display='none';$('pn').style.display='flex'}lg(t(md?'extract':'embed'))}`;

h = h.replace(oldMode, newMode);

// Update the grid to support dual-mode columns
// The current grid: <div class=mc> has 3 children divs
// We need to wrap right-column embed/extract content differently

// Find the params panel and add extract result panel alongside it
const ppEnd = `</div></div></div>` + "\n" + `<div class=cv`;
// Insert extract panel before the comparison section
const extractPanel = `</div></div></div>` + "\n" +
`<div class=pt id=xr style=display:none><div class=ph data-i=xr>EXTRACTED</div><div id=xl style=flex:1;overflow-y:auto;padding:4px>No results yet</div><button class=bx id=be2 data-i=xc style=margin-top:4px>EXTRACT</button></div>` + "\n" +
`<div class=cv`;

h = h.replace(ppEnd, extractPanel);

// Also add extracted result label to i18n
h = h.replace("L.en={on:", "L.en={xr:'EXTRACTED',embed:'EMBED',extract:'EXTRACT',on:");
h = h.replace("L.zh={on:", "L.zh={xr:'\\u63d0\\u53d6\\u7ed3\\u679c',embed:'\\u5d4c\\u5165',extract:'\\u63d0\\u53d6',on:");
h = h.replace("L.ru={on:", "L.ru={xr:'\\u0420\\u0435\\u0437\\u0443\\u043b\\u044c\\u0442\\u0430\\u0442',embed:'EMBED',extract:'EXTRACT',on:");

// Modify dx() to populate the extract result panel
const oldDx = `async function dx(){var b64=await d2b(st.cd.du);var r=await fetch('http://127.0.0.1:8080/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_b64:b64,delta:st.de,level:st.lv,sync_enabled:!!st.sy,bch_enabled:!!st.bc})});if(!r.ok){var e=await r.json();throw new Error(e.error||'HTTP '+r.status)}var d=await r.json();var parts=d.watermark_text.split('|');lg(tk('ext')+' '+parts.length+' items:','o');parts.forEach(function(p,i){lg('  ['+(i+1)+'] '+p.substring(0,60))});showExtract(parts)}`;

const newDx = `async function dx(){var b64=await d2b(st.cd.du);var r=await fetch('http://127.0.0.1:8080/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image_b64:b64,delta:st.de,level:st.lv,sync_enabled:!!st.sy,bch_enabled:!!st.bc})});if(!r.ok){var e=await r.json();throw new Error(e.error||'HTTP '+r.status)}var d=await r.json();var parts=d.watermark_text.split('|');lg(tk('ext')+' '+parts.length+' items:','o');parts.forEach(function(p,i){lg('  ['+(i+1)+'] '+p.substring(0,60))});showExtract(parts);var xl=$('xl');if(xl){xl.innerHTML='';parts.forEach(function(p,i){var r=document.createElement('div');r.style.cssText='border-bottom:1px solid var(--d);padding:6px 4px;font-size:12px';var n=document.createElement('div');n.style.cssText='color:var(--g);font-size:10px;text-transform:uppercase';n.textContent='#'+(i+1);r.appendChild(n);var t=document.createElement('div');t.style.cssText='color:var(--f0)';t.textContent=p.substring(0,40);r.appendChild(t);xl.appendChild(r)})}}`;

h = h.replace(oldDx, newDx);

// Modify showExtract to also update the extract panel while keeping canvas overlay
// (showExtract already renders on canvas, we just added the panel above)

// Add embed/extract labels as data-i attributes
h = h.replace('onclick=m(0) data-i=em>EMBED</button>', 'onclick=m(0)>EMBED</button>');
h = h.replace('onclick=m(1) data-i=ex>EXTRACT</button>', 'onclick=m(1)>EXTRACT</button>');

fs.writeFileSync('D:/administrator/Documents/project/S-Anchor/frontend/index.html', h, 'utf8');

// Verify
const h2 = fs.readFileSync('D:/administrator/Documents/project/S-Anchor/frontend/index.html', 'utf8');
const m = h2.match(/<script>([\s\S]*?)<\/script>/);
try { new Function(m[1]); console.log('JS OK'); }
catch(e) { console.log('JS FAIL: ' + e.message.substring(0, 80)); }
