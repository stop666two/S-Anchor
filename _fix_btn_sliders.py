"""Fix ADD button auto-select and slider interaction."""
with open(r'D:\administrator\Documents\project\S-Anchor\frontend\app.js', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 1: awt() - after adding, auto-select the LAST added watermark
old_awt = "uw();cc();lg('+'+lines.length+' ['+tp+']');rw()"
new_awt = "uw();sel=wid;var ws=$('ws');if(ws)ws.value=sel;cc();lg('+'+lines.length+' ['+tp+']');rw()"
if old_awt in c:
    c = c.replace(old_awt, new_awt)
    print('1. awt() now auto-selects last watermark')
else:
    print(f'1. awt() pattern not found')

# Fix 2: When selecting "--" (no selection), show aggregate info
# Change: show total watermark text instead of st.txt
old_ws_idle = "if(id<0){if(st.txt)$('wt').value=st.txt;rw();return}"
new_ws_idle = "if(id<0){rw();return}"
if old_ws_idle in c:
    c = c.replace(old_ws_idle, new_ws_idle)
    print('2. ws() idle selection simplified')
else:
    print(f'2. ws() idle pattern not found')

# Fix 3: When content text changes AND watermarks exist but none selected,
# update the FIRST watermark's text (useful fallback)
old_wt = "$('wt').oninput=function(){var v=this.value;if(sel>=0){wm.forEach(function(w){if(w.id===sel)w.txt=v})}else{st.txt=v}rw();cc()}"
new_wt = "$('wt').oninput=function(){var v=this.value;if(sel>=0){wm.forEach(function(w){if(w.id===sel)w.txt=v})}rw();cc()}"
if old_wt in c:
    c = c.replace(old_wt, new_wt)
    print('3. wt oninput simplified (removed st.txt)')
else:
    print(f'3. wt oninput pattern not found')

# Fix 4: X/Y/Opacity sliders should only apply when watermark selected, not to st.*
# These sliders set st.px, st.py etc which are unused. Remove else branches.
for slider, field in [('rx', 'px'), ('ry', 'py'), ('rr', 'rt'), ('rs', 'fs'), ('ro', 'op')]:
    old = f"$('{slider}').oninput=function(){{var v=+this.value;sf('v{s[0]}',v+'%');if(sel>=0){{wm.forEach(function(w){{if(w.id===sel)w.{field}=v}})}}else{{st.{field}=v}}rw()}}"
    new = f"$('{slider}').oninput=function(){{var v=+this.value;sf('v{s[0]}',v);if(sel>=0){{wm.forEach(function(w){{if(w.id===sel)w.{field}=v}})}}rw()}}"
    
    # Try both with and without % suffix
    if field in ('px', 'py', 'op'):
        old_pct = f"$('{slider}').oninput=function(){{var v=+this.value;sf('v{s[0]}',v+'%');if(sel>=0){{wm.forEach(function(w){{if(w.id===sel)w.{field}=v}})}}else{{st.{field}=v}}rw()}}"
        new_pct = f"$('{slider}').oninput=function(){{var v=+this.value;sf('v{s[0]}',v+'%');if(sel>=0){{wm.forEach(function(w){{if(w.id===sel)w.{field}=v}})}}rw()}}"
        if old_pct in c:
            c = c.replace(old_pct, new_pct)
            print(f'4. {slider} ({field}) fixed')
        elif old in c:
            c = c.replace(old, new)
            print(f'4. {slider} ({field}) fixed (no %)')
        else:
            # Check what's actually there
            idx = c.find(f"$('{slider}').oninput")
            if idx >= 0:
                end = c.find('}', c.find('}', idx) + 1) + 1
                snippet = c[idx:end]
                print(f'4. {slider}: found pattern: {snippet[:80]}...')
    else:
        if old in c:
            c = c.replace(old, new)
            print(f'4. {slider} ({field}) fixed')
        else:
            idx = c.find(f"$('{slider}').oninput")
            if idx >= 0:
                end = c.find('}', c.find('}', idx) + 1) + 1
                snippet = c[idx:end]
                print(f'4. {slider}: found pattern: {snippet[:80]}...')

with open(r'D:\administrator\Documents\project\S-Anchor\frontend\app.js', 'w', encoding='utf-8') as f:
    f.write(c)

# Verify
opens = c.count('{')
closes = c.count('}')
print(f'Braces: {opens}/{closes} {"OK" if opens==closes else "MISMATCH"}')
print('Done')
