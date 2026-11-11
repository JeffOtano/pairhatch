import json,pathlib,subprocess,sys,tempfile,unittest,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
class CLITests(unittest.TestCase):
 def test_two_process_roundtrip_and_restart(self):
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d).resolve();config=d/'config.json'
   config.write_text(json.dumps({'version':10,'database':str(d/'broker.sqlite'),'peers':[{'id':x,'label':x,'kind':'mock'} for x in ('codex','claude')]}))
   def call(actor,*args):
    result=subprocess.run([sys.executable,str(ROOT/'run.py'),'--config',str(config),'--actor',actor,*args],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)
   call('codex','grant','--id','g','--participants','codex','claude','--topic','Synthetic median review','--max-messages','2','--confirm','ALLOW codex claude')
   mid=str(uuid.uuid4());reply=str(uuid.uuid4())
   call('claude','ask','--grant','g','--to','codex','--consultation','c','--message-id',mid,'--text','What should median([]) do?')
   self.assertEqual(call('codex','inbox')[0]['message_id'],mid)
   self.assertEqual(call('codex','inbox','--limit','1','--offset','1'),[])
   call('codex','reply','--consultation','c','--in-reply-to',mid,'--message-id',reply,'--text','Raise ValueError.','--final')
   s=call('claude','status','--consultation','c');self.assertEqual(s['consultation']['state'],'completed');self.assertEqual(len(s['messages']),2)
   call('codex','reply','--consultation','c','--in-reply-to',mid,'--message-id',reply,'--text','Raise ValueError.','--final')
   self.assertEqual(len(call('claude','status','--consultation','c')['messages']),2)
 def test_stdio_protocol_process(self):
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d).resolve();config=d/'config.json';config.write_text(json.dumps({'version':10,'database':str(d/'db'),'peers':[{'id':x,'label':x,'kind':'mock'} for x in ('codex','claude')]}))
   requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},{'jsonrpc':'2.0','id':2,'method':'tools/list'}]
   p=subprocess.run([sys.executable,str(ROOT/'run.py'),'--config',str(config),'--actor','codex','serve'],input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True,timeout=5)
   self.assertEqual(p.returncode,0,p.stderr);rows=[json.loads(l) for l in p.stdout.splitlines()];self.assertEqual(len(rows),2);self.assertEqual(len(rows[1]['result']['tools']),5)

