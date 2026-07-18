const fs = require('fs');
let j = fs.readFileSync('D:/administrator/Documents/project/S-Anchor/frontend/app.js', 'utf8');

// 1. Replace awt() with multi-line parsing version
// The key: use String.fromCharCode(10) instead of \n to avoid escaping issues
const oldAwt = "function awt(){var id=++wid;wm.push({id:id,ty:'t',txt:'WM'+id,px:(id*7+13)%60,py:(id*9+17)%60,rt:0,fs:40,op:85,fn:st.fn,cl:st.cl});uw();$('ws').value=id;ws();$('wt').value='WM'+id;lg('+TEXT #'+id)}";
const newAwt = "function awt(){var lines=$('wt').value.split(String.fromCharCode(10)).filter(function(l){return l.trim()});if(!lines.length)lines=['WM'];lines.forEach(function(line,i){var id=++wid;wm.push({id:id,ty:'t',txt:line.trim(),px:(id*7+13)%60,py:(id*9+15)%60,rt:0,fs:36,op:85,fn:st.fn,cl:st.cl})});uw();lg('+'+lines.length+' WMs');rw()}";
j = j.replace(oldAwt, newAwt);

// 2. Remove awi() function
const awiStart = j.indexOf('function awi()');
const awiEnd = j.indexOf('function', awiStart + 10);
if (awiStart > 0) {
  const end = awiEnd > 0 ? awiEnd : j.indexOf('function wd()', awiStart);
  j = j.substring(0, awiStart) + j.substring(end);
}

// 3. Update de() - remove image-specific encoding
j = j.replace("w.ty==='i'?'[IMG:'+w.txt+']':w.txt", "w.txt");

// 4. Remove image drawing from rw()
const oldDraw = "if(w.ty==='i'&&w.img){ctx.save();ctx.translate(ox+st.cd.w*s*w.px/100,oy+st.cd.h*s*w.py/100);ctx.rotate(w.rt*Math.PI/180);ctx.globalAlpha=w.op/100;var ws=Math.min(120/st.cd.w,120/st.cd.h)*s;ctx.drawImage(w.img.el,-w.img.el.width*ws/2,-w.img.el.height*ws/2,w.img.el.width*ws,w.img.el.height*ws);ctx.restore()}else{dw(w.px,w.py,w.rt,w.fs,w.op,w.txt,w.id)}";
j = j.replace(oldDraw, "dw(w.px,w.py,w.rt,w.fs,w.op,w.txt,w.id)");

// 5. Update dx() results population to remove IMG detection
j = j.replace("(p.indexOf('[IMG:')===0?' [IMG]':' [TEXT]')", "' TEXT'");

fs.writeFileSync('D:/administrator/Documents/project/S-Anchor/frontend/app.js', j, 'utf8');
console.log('JS patched');

try { new Function(j); console.log('JS OK'); }
catch(e) { console.log('JS FAIL: ' + e.message.substring(0, 80)); }

// Update HTML
let h = fs.readFileSync('D:/administrator/Documents/project/S-Anchor/frontend/index.html', 'utf8');
h = h.replace(
  '<div class=mm style=margin-bottom:4px><button class="tb sm" onclick=awt() style=flex:1>+ TEXT</button><button class="tb sm" onclick=awi() style=flex:1>+ IMG</button></div>',
  '<button class="tb sm" onclick=awt() style=margin-bottom:4px>+ ADD</button>'
);
h = h.replace(
  '<input class=wi id=wt value="S-ANCHOR" style=margin-bottom:4px>',
  '<textarea class=wi id=wt style="margin-bottom:4px;min-height:50px;resize:vertical;padding:6px;background:var(--b2);color:var(--f0);border:1px solid var(--d);font-family:inherit;font-size:12px;outline:none;width:100%">Line1\nLine2\nLine3</textarea>'
);
fs.writeFileSync('D:/administrator/Documents/project/S-Anchor/frontend/index.html', h, 'utf8');
console.log('HTML patched');
