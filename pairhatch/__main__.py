"""Local operator and actor CLI. No automatic service installation."""
import argparse,json,os,pathlib,sys,time,uuid
from .store import Store,Refused
from .engine import Broker,load_config

def parser():
 p=argparse.ArgumentParser(description='Pairhatch V10: bounded local peer consultation')
 p.add_argument('--config',required=True);p.add_argument('--actor')
 sub=p.add_subparsers(dest='command',required=True)
 g=sub.add_parser('grant',help='Operator only: explicitly authorize pair/topic and finite budget')
 g.add_argument('--id',required=True);g.add_argument('--participants',nargs=2,required=True);g.add_argument('--topic',required=True)
 g.add_argument('--minutes',type=float,default=10);g.add_argument('--max-messages',type=int,default=6);g.add_argument('--max-consultations',type=int,default=1)
 g.add_argument('--confirm',required=True,help='Exact phrase: ALLOW <first> <second>')
 a=sub.add_parser('ask');a.add_argument('--grant',required=True);a.add_argument('--to',required=True)
 a.add_argument('--consultation',required=True);a.add_argument('--message-id',required=True)
 a.add_argument('--text',help='Otherwise reads bounded text from stdin')
 r=sub.add_parser('reply');r.add_argument('--consultation',required=True);r.add_argument('--in-reply-to',required=True)
 r.add_argument('--message-id',required=True);r.add_argument('--text');r.add_argument('--final',action='store_true')
 s=sub.add_parser('status');s.add_argument('--consultation')
 i=sub.add_parser('inbox',help='Read a bounded page of admitted messages for this actor')
 i.add_argument('--limit',type=int,default=100);i.add_argument('--offset',type=int,default=0)
 sub.add_parser('pause');sub.add_parser('resume')
 c=sub.add_parser('cancel');c.add_argument('--consultation',required=True)
 v=sub.add_parser('revoke');v.add_argument('--grant',required=True)
 sub.add_parser('serve',help='Run optional stdio tool interface; does not register it')
 sub.add_parser('doctor',help='Config/destination preflight; may initialize database and bind peers; no live sends')
 return p

def main(argv=None):
 args=parser().parse_args(argv);store=None;exit_code=0
 try:
  config,peers=load_config(args.config)
  # Paths are trusted operator settings; preserving symlinks lets Store reject them.
  db=config.get('database')
  if not isinstance(db,str) or not pathlib.Path(db).is_absolute():raise Refused('Absolute private database path required')
  store=Store(db)
  store.bind_peers(peers)
  if args.command=='grant':
   if any(p not in peers for p in args.participants):raise Refused('Grant participant not enrolled')
   if args.confirm!='ALLOW '+' '.join(args.participants):raise Refused('Exact operator confirmation phrase required')
   if not 0<args.minutes<=1440:raise Refused('Grant lifetime must be at most one day')
   result=store.create_grant(args.id,args.participants,args.topic,time.time()+args.minutes*60,args.max_messages,args.max_consultations)
  elif args.command in ('pause','resume'):
   getattr(store,args.command)();result=store.status()
  elif args.command=='revoke':store.revoke_grant(args.grant);result=store.status()
  elif args.command=='status' and not args.consultation:result=store.status()
  else:
   if not args.actor:raise Refused('Explicit configured actor required')
   broker=Broker(store,peers,args.actor)
   if args.command=='serve':
    from .mcp import serve
    serve(broker);return 0
   if args.command in ('ask','reply'):
    text=args.text if args.text is not None else sys.stdin.read(8193)
    if args.command=='ask':result=broker.ask(args.grant,args.to,text,args.consultation,args.message_id)
    else:result=broker.reply(args.consultation,args.in_reply_to,text,args.final,args.message_id)
   elif args.command=='status':result=broker.inspect(args.consultation)
   elif args.command=='inbox':result=broker.inbox(args.limit,args.offset)
   elif args.command=='cancel':result=broker.cancel(args.consultation)
   elif args.command=='doctor':
    result={'actor':args.actor,'origin_evidence':'configured local client claim; not cryptographically authenticated','peers':[]}
    for peer in peers.values():
     try:broker.adapters[peer['kind']].preflight(peer);result['peers'].append({'id':peer['id'],'preflight':'passed','note':'Not a live delivery test'})
     except Exception as exc:result['peers'].append({'id':peer['id'],'preflight':'failed','reason':str(exc)})
    if any(peer['preflight']=='failed' for peer in result['peers']):exit_code=1
   else:raise Refused('Unsupported command')
  print(json.dumps(result,ensure_ascii=False,indent=2));return exit_code
 except Exception as exc:print(json.dumps({'error':str(exc),'note':'No automatic retry; inspect recorded delivery state'}),file=sys.stderr);return 1
 finally:
  if store:store.close()
if __name__=='__main__':sys.exit(main())

