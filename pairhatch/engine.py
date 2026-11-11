"""Shared CLI/MCP orchestration. Grant administration is deliberately separate."""
import json,re,uuid
from .store import Refused
from .transports import MockTransport,CodexQueue,ClaudeSocket,PreflightRejected,UncertainDelivery,render,secure_read_json,uuid_ok

def diagnostic(exc):
    return "".join(c if c in "\n\t" or (ord(c)>=32 and not 127<=ord(c)<=159) else "?" for c in str(exc))[:2000] or type(exc).__name__

def load_config(path):
    config=secure_read_json(path)
    if config.get('version')!=10 or not isinstance(config.get('peers'),list):raise Refused('V10 peer configuration required')
    peers={}
    for peer in config['peers']:
        if not isinstance(peer,dict) or not re.fullmatch(r'[a-z0-9_-]{1,64}',peer.get('id','')):raise Refused('Invalid peer id')
        if peer['id'] in peers:raise Refused('Duplicate peer identity')
        if peer.get('kind') not in ('mock','codex_queue','claude_socket'):raise Refused('Unsupported transport')
        if peer['kind'] != 'mock' and config.get('experimental_native_transports') is not True:
            raise Refused('Native transports require explicit experimental_native_transports: true')
        label=peer.get('label','')
        if not isinstance(label,str) or not label.strip() or len(label)>80 or any(ord(c)<32 for c in label):raise Refused('Invalid peer label')
        peers[peer['id']]=peer
    if len(peers)<2:raise Refused('At least two enrolled peers required')
    return config,peers

class Broker:
    def __init__(self,store,peers,actor,adapters=None):
        if actor not in peers:raise Refused('Actor is not enrolled')
        store.bind_peers(peers)
        self.store=store;self.peers=peers;self.actor=actor
        self.adapters=adapters or {'mock':MockTransport(),'codex_queue':CodexQueue(),'claude_socket':ClaudeSocket()}
    def _own(self,consultation_id):
        c=self.store.get_consultation(consultation_id)
        pair=json.loads(c['pair']) if isinstance(c['pair'],str) else c['pair']
        if self.actor not in pair:raise Refused('Actor is not a participant')
        return c
    def dispatch(self,message):
        # Replayed calls report the recorded outcome instead of sending again.
        if message['state']!='queued':return message
        peer=self.peers[message['recipient']];adapter=self.adapters[peer['kind']]
        # Claim first: permission/grant/time accounting is atomic before any I/O.
        message=self.store.claim(message['message_id'])
        try:
            adapter.preflight(peer)
            envelope=dict(message,approved_scope=self.store.get_grant(self.store.get_consultation(message['consultation_id'])['grant_id'])['topic'])
            receipt=adapter.send(peer,render(envelope,self.peers),message['message_id'])
            if receipt.outcome!='accepted':raise UncertainDelivery('Unexpected transport receipt')
        except PreflightRejected as exc:return self.store.settle(message['message_id'],'rejected',diagnostic(exc))
        except Exception as exc:return self.store.settle(message['message_id'],'unknown',diagnostic(exc))
        return self.store.settle(message['message_id'],'accepted',receipt.detail)
    def ask(self,grant_id,recipient,text,consultation_id=None,message_id=None):
        if recipient not in self.peers or recipient==self.actor:raise Refused('Exact other enrolled peer required')
        cid=str(uuid.uuid4()) if consultation_id is None else consultation_id;mid=str(uuid.uuid4()) if message_id is None else message_id
        if self.peers[recipient]['kind']!='mock' and not uuid_ok(mid):raise Refused('Native message ID must be a canonical UUID')
        message=self.store.open_question(grant_id,cid,mid,self.actor,recipient,text)
        return self.dispatch(message)
    def reply(self,consultation_id,in_reply_to,text,final=False,message_id=None):
        self._own(consultation_id)
        previous=self.store.get_message(in_reply_to)
        if previous['consultation_id']!=consultation_id or previous['recipient']!=self.actor:raise Refused('Reply is not addressed to actor')
        mid=str(uuid.uuid4()) if message_id is None else message_id
        if self.peers[previous['sender']]['kind']!='mock' and not uuid_ok(mid):raise Refused('Native message ID must be a canonical UUID')
        message=self.store.enqueue(consultation_id,mid,self.actor,previous['sender'],text,'final' if final else 'answer',in_reply_to)
        return self.dispatch(message)
    def inspect(self,consultation_id):
        self._own(consultation_id)
        return {'consultation':self.store.get_consultation(consultation_id),'messages':self.store.list_messages(consultation_id),
                'delivery_note':'accepted means transport admission, not model receipt; only a correlated peer reply proves a response'}
    def inbox(self,limit=100,offset=0):
        return self.store.inbox(self.actor,limit,offset)
    def cancel(self,consultation_id):
        self._own(consultation_id);self.store.cancel(consultation_id)
        return {'state':self.store.get_consultation(consultation_id)['state'],'note':'Cannot recall a message already claimed, written or queued'}

