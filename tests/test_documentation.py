"""Keep the documented synthetic conversation executable without live hosts."""
import json
from pathlib import Path
import re
import tempfile
import time
import unittest

from pairhatch.engine import Broker
from pairhatch.mcp import handle, TOOLS
from pairhatch.store import Store

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_cookbook_covers_all_tools_and_runs_mock_exchange(self):
        document = (ROOT / 'docs/MCP_COOKBOOK.md').read_text()
        requests = [json.loads(block) for block in re.findall(r'```json\n(.*?)\n```', document, re.S)]
        self.assertEqual({r['params']['name'] for r in requests}, {t['name'] for t in TOOLS})
        peers = {p: {'id': p, 'label': p, 'kind': 'mock'} for p in ('peer-a', 'peer-b')}
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(str(Path(tmp).resolve() / 'broker.sqlite'))
            try:
                store.create_grant('approved-synthetic-check', ['peer-a', 'peer-b'],
                                   'Synthetic question and answer only', time.time()+600, 2, 1)
                actors = ('peer-a', 'peer-b', 'peer-b', 'peer-a', 'peer-a')
                payloads = []
                for request, actor in zip(requests, actors):
                    result = handle(Broker(store, peers, actor), request)
                    self.assertFalse(result['isError'], result)
                    payloads.append(json.loads(result['content'][0]['text']))
                self.assertEqual(payloads[0]['state'], 'accepted')
                self.assertEqual(payloads[0]['sequence'], 1)
                self.assertEqual(len(payloads[1]), 1)
                self.assertEqual(payloads[2]['kind'], 'final')
                self.assertEqual(payloads[3]['consultation']['state'], 'completed')
                self.assertEqual(payloads[3]['consultation']['messages_used'], 2)
                self.assertEqual(len(payloads[3]['messages']), 2)
                self.assertEqual(payloads[4]['state'], 'completed')
            finally:
                store.close()

    def test_agent_entrypoint_links_resolve(self):
        for filename in ('AGENTS.md', 'docs/MCP_COOKBOOK.md', 'docs/TROUBLESHOOTING.md'):
            path = ROOT / filename
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in link:
                    self.assertTrue((path.parent / link.split('#')[0]).is_file(), (filename, link))
