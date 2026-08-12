"""Local-only Tomb World narration production server."""
from __future__ import annotations
import hashlib, json, os, subprocess, tempfile, webbrowser
from pathlib import Path
from urllib.parse import quote
import requests
from dotenv import dotenv_values
from flask import Flask, jsonify, request, send_from_directory
from mutagen.mp3 import MP3

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
SCRIPTS=ROOT/'Narration'/'scripts'; SETTINGS=ROOT/'Narration'/'producer-settings.json'
AUDIO=ROOT/'Assets'/'Audio'/'Narration'; MANIFEST=AUDIO/'narration-manifest.json'
API='https://api.elevenlabs.io/v1'; ALLOWED={SCRIPTS.resolve(),AUDIO.resolve(),SETTINGS.resolve()}
app=Flask(__name__,static_folder='static',static_url_path='')

def normalize(text): return text.replace('\r\n','\n').replace('\r','\n').strip()
def digest(value): return hashlib.sha256(value if isinstance(value,bytes) else value.encode('utf-8')).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def settings_hash(s):
 data={k:s.get(k) for k in ('voiceId','modelId','outputFormat','voiceSettings')}; return digest(canonical(data)) if all(data[k] is not None for k in data) else None
def generation_hash(sh,sth): return digest(f'{sh}:{sth}') if sh and sth else None
def key(): return (dotenv_values(HERE/'.env').get('ELEVENLABS_API_KEY') or '').strip()
def headers(): return {'xi-api-key':key()}
def safe(path,root):
 p=(root/path).resolve()
 if p!=root.resolve() and root.resolve() not in p.parents: raise ValueError('The requested path is not allowed.')
 return p
def atomic_json(path,data):
 safe(path.relative_to(ROOT),ROOT)
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.producer-',suffix='.tmp')
 try:
  with os.fdopen(fd,'w',encoding='utf8') as f: json.dump(data,f,indent=2,ensure_ascii=False); f.write('\n')
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)
def library():
 result=[]
 for path in sorted(SCRIPTS.glob('*.json')):
  data=json.loads(path.read_text(encoding='utf8'))
  for record in data['scripts']:
   actual=digest(normalize(record['script'])); record=dict(record,fileSource=path.name,characterCount=len(normalize(record['script'])))
   record['reviewRequired']=actual!=record.get('scriptHash'); result.append(record)
 return result
def friendly(response):
 if response.status_code in (401,403): return 'ElevenLabs rejected the API key. Open the API Key file, verify the key, save it, and try Recheck API Key.'
 return 'ElevenLabs could not complete the request. Check your connection and try again.'
def get_json(url):
 if not key(): raise ValueError('Add an ElevenLabs API key, save the file, and choose Recheck API Key.')
 r=requests.get(url,headers=headers(),timeout=20)
 if not r.ok: raise ValueError(friendly(r))
 return r.json()
@app.get('/')
def index(): return app.send_static_file('index.html')
@app.get('/api/status')
def status(): return jsonify(apiKeyConfigured=bool(key()),settings=json.loads(SETTINGS.read_text()),scripts=library())
@app.post('/api/recheck')
def recheck(): return jsonify(apiKeyConfigured=bool(key()))
@app.post('/api/open-key-file')
def open_key_file():
 env=HERE/'.env'
 if not env.exists(): env.write_text((HERE/'.env.example').read_text())
 if os.name=='nt': subprocess.Popen(['notepad.exe',str(env)])
 return jsonify(opened=os.name=='nt',message='The API Key file is ready. Save it, then choose Recheck API Key.')
@app.post('/api/open-output-folder')
def open_output():
 AUDIO.mkdir(parents=True,exist_ok=True)
 if os.name=='nt': subprocess.Popen(['explorer.exe',str(AUDIO)])
 return jsonify(opened=os.name=='nt')
@app.get('/api/connection')
def connection():
 try: return jsonify(ok=True,subscription=get_json(API+'/user/subscription'))
 except ValueError as e: return jsonify(ok=False,error=str(e)),400
@app.get('/api/metadata')
def metadata():
 try:
  voices=get_json(API+'/voices').get('voices',[]); models=get_json(API+'/models')
  models=[m for m in models if m.get('can_do_text_to_speech',True)]
  return jsonify(voices=voices,models=models)
 except ValueError as e: return jsonify(error=str(e)),400
@app.get('/api/voices/<voice_id>/settings')
def voice_settings(voice_id):
 try: return jsonify(get_json(API+'/voices/'+quote(voice_id,safe='')+'/settings'))
 except ValueError as e: return jsonify(error=str(e)),400
@app.post('/api/settings')
def save_settings():
 data=request.get_json(force=True)
 if any('key' in k.lower() for k in data): return jsonify(error='API keys cannot be saved in Producer settings.'),400
 data['schemaVersion']=1; atomic_json(SETTINGS,data); return jsonify(ok=True)
def plan(ids,settings):
 sth=settings_hash(settings); rows=[]
 for rec in library():
  if rec['id'] not in ids: continue
  gh=generation_hash(rec['scriptHash'],sth); output=safe(Path(rec['outputFile']),AUDIO)
  approved=rec['status'] in ('approved','generated') and not rec['reviewRequired']; up=False
  if approved and gh==rec.get('generationHash') and output.exists() and rec.get('audioHash'): up=digest(output.read_bytes())==rec['audioHash']
  reason='Up to date.' if up else ('Script approval is required.' if not approved else ('Generation settings are incomplete.' if not sth else 'Would generate.'))
  rows.append({**{k:rec.get(k) for k in ('id','status','characterCount','outputFile','scriptHash')},'settingsHash':sth,'generationHash':gh,'blocked':not approved or not sth,'wouldGenerate':approved and bool(sth) and not up,'wouldSkip':up,'reason':reason})
 return rows
@app.post('/api/dry-run')
def dry_run():
 body=request.get_json(force=True); rows=plan(set(body.get('ids',[])),body.get('settings',{}))
 return jsonify(items=rows,totals={'selected':len(rows),'approved':sum(not r['blocked'] for r in rows),'blocked':sum(r['blocked'] for r in rows),'wouldGenerate':sum(r['wouldGenerate'] for r in rows),'wouldSkip':sum(r['wouldSkip'] for r in rows),'totalCharacters':sum(r['characterCount'] for r in rows)})
@app.post('/api/scripts/<path:script_id>/approve')
def approve(script_id):
 for path in SCRIPTS.glob('*.json'):
  data=json.loads(path.read_text(encoding='utf8'))
  for rec in data['scripts']:
   if rec['id']==script_id:
    rec['script']=normalize(rec['script']); rec['scriptHash']=digest(rec['script']); rec['status']='approved'
    for k in ('settingsHash','generationHash','audioHash'): rec[k]=None
    atomic_json(path,data); return jsonify(ok=True,scriptHash=rec['scriptHash'])
 return jsonify(error='Narration script not found.'),404
def validate_audio(path):
 if path.stat().st_size<128 or path.read_bytes()[:3] not in (b'ID3',) and path.read_bytes()[:2] not in (b'\xff\xfb',b'\xff\xf3',b'\xff\xf2'): raise ValueError('ElevenLabs returned audio that was not a valid MP3.')
 duration=MP3(path).info.length
 if duration<=0: raise ValueError('The generated MP3 has no playable duration.')
 return round(duration*1000)
@app.post('/api/generate')
def generate():
 body=request.get_json(force=True)
 if body.get('confirmation') is not True: return jsonify(error='Generation requires explicit credit confirmation.'),400
 if body.get('force') and body.get('forceConfirmation') is not True: return jsonify(error='Force Regenerate requires explicit confirmation.'),400
 if not key(): return jsonify(error='Configure the API key before generating.'),400
 settings=body.get('settings',{}); results=[]
 for row in plan(set(body.get('ids',[])),settings):
  if row['blocked']: results.append({'id':row['id'],'status':'blocked','message':row['reason']}); continue
  if row['wouldSkip'] and not body.get('force'): results.append({'id':row['id'],'status':'skipped'}); continue
  rec=next(x for x in library() if x['id']==row['id']); dest=safe(Path(rec['outputFile']),AUDIO); dest.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(dir=dest.parent,prefix='.narration-',suffix='.tmp'); os.close(fd); tmp=Path(tmp)
  try:
   payload={'text':normalize(rec['script']),'model_id':settings['modelId'],'voice_settings':settings['voiceSettings']}
   response=requests.post(f"{API}/text-to-speech/{quote(settings['voiceId'],safe='')}",params={'output_format':settings['outputFormat']},headers={**headers(),'Accept':'audio/mpeg','Content-Type':'application/json'},json=payload,timeout=120)
   if not response.ok: raise ValueError(friendly(response))
   tmp.write_bytes(response.content); duration=validate_audio(tmp); ah=digest(response.content); os.replace(tmp,dest)
   manifest=json.loads(MANIFEST.read_text()); entry=manifest['entries'][rec['id']]; entry.update(file=rec['outputFile'],available=True,scriptHash=rec['scriptHash'],settingsHash=row['settingsHash'],generationHash=row['generationHash'],audioHash=ah,durationMs=duration); atomic_json(MANIFEST,manifest)
   source=SCRIPTS/rec['fileSource']; data=json.loads(source.read_text())
   target=next(x for x in data['scripts'] if x['id']==rec['id']); target.update(status='generated',settingsHash=row['settingsHash'],generationHash=row['generationHash'],audioHash=ah,voiceId=settings['voiceId'],modelId=settings['modelId']); atomic_json(source,data)
   results.append({'id':rec['id'],'status':'generated','durationMs':duration})
  except (ValueError,requests.RequestException) as e: results.append({'id':rec['id'],'status':'failed','message':str(e)})
  finally:
   if tmp.exists(): tmp.unlink()
 return jsonify(results=results)
@app.get('/audio/<path:name>')
def audio(name):
 path=safe(Path(name),AUDIO); return send_from_directory(path.parent,path.name)
if __name__=='__main__':
 webbrowser.open('http://127.0.0.1:8765'); app.run(host='127.0.0.1',port=8765,debug=False)
