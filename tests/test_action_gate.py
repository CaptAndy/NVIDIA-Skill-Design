import importlib.util,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'integration/action_gate.py'
s=importlib.util.spec_from_file_location('action_gate',p);g=importlib.util.module_from_spec(s);sys.modules[s.name]=g;s.loader.exec_module(g)

class GateTests(unittest.TestCase):
 def setUp(self):self.obs=g.Observation('page1','revision1','scopeA')
 def run_gate(self,kind='navigate',effect='read',confirmation=None,**kw):
  return g.check(g.Action(kind,'办件进度',True,effect),self.obs,kw.pop('current',self.obs),confirmation,**kw)
 def test_navigation_needs_no_extra_confirmation(self):self.assertTrue(self.run_gate()['allowed'])
 def test_refresh_invalidates_target(self):self.assertEqual(self.run_gate(current=g.Observation('page1','revision2','scopeA'))['next'],'observe')
 def test_other_tab_invalidates_target(self):self.assertFalse(self.run_gate(current=g.Observation('page2','revision1','scopeA'))['allowed'])
 def test_unknown_effect_is_not_local(self):self.assertFalse(self.run_gate(kind='fill',effect='unknown')['allowed'])
 def test_upload_requires_confirmation_even_if_mislabelled_read(self):self.assertEqual(self.run_gate(kind='upload')['next'],'confirm')
 def test_matching_confirmation_consumed(self):self.assertTrue(self.run_gate('upload','external',g.Confirmation('upload','scopeA',True))['consume_confirmation'])
 def test_changed_file_invalidates_confirmation(self):self.assertFalse(self.run_gate('upload','external',g.Confirmation('upload','scopeB',True))['allowed'])
 def test_confirmation_is_action_specific(self):self.assertFalse(self.run_gate('submit','external',g.Confirmation('upload','scopeA',True))['allowed'])
 def test_confirmation_cannot_be_replayed(self):self.assertFalse(self.run_gate('submit','external',g.Confirmation('submit','scopeA',True,used=True))['allowed'])
 def test_timeout_never_retries_submit(self):self.assertEqual(self.run_gate('submit','external',g.Confirmation('submit','scopeA',True),outcome_unknown=True)['next'],'observe')
 def test_pause_overrides_authorization(self):self.assertEqual(self.run_gate(paused=True)['next'],'stop')
 def test_payment_remains_with_user(self):self.assertEqual(self.run_gate('payment','external',g.Confirmation('payment','scopeA',True))['next'],'handoff')
 def test_duplicate_and_hidden_buttons(self):
  for kw in ({'target_unique':False},{'target_visible':False}):self.assertEqual(self.run_gate(**kw)['next'],'observe')
 def test_no_identical_third_retry(self):self.assertEqual(self.run_gate(unchanged_failures=2)['next'],'stop')

if __name__=='__main__':unittest.main()
