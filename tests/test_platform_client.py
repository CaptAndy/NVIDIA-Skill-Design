import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

path=Path(__file__).resolve().parents[1]/'screen-assistance/scripts/invoke_model.py'
spec=importlib.util.spec_from_file_location('client',path)
client=importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)

class ClientTests(unittest.TestCase):
    def test_step_plan_path(self):
        r=client.build_request('step-plan','synthetic',base='https://example.org',key='fake-test-key')
        self.assertEqual(r.full_url,'https://api.stepfun.com/step_plan/v1/chat/completions')
        self.assertNotIn('fake-test-key',r.data.decode())
    def test_no_cloud_images(self):
        with self.assertRaises(ValueError):client.build_request('step-plan','x',image='not-read.png',key='fake')
    def test_restrict_spark_to_tunnel(self):
        for url in ['http://remote.example/v1','https://127.0.0.1/v1','http://user:secret@localhost/v1','http://localhost/v1?token=abc']:
            with self.assertRaises(ValueError):client.build_request('spark','x',base=url)
    def test_only_image_formats(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.png';p.write_bytes(b'not an image')
            with self.assertRaises(ValueError):client.build_request('spark','x',image=p)
    def test_refuse_incomplete_output(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self, limit):return json.dumps({'choices':[{'finish_reason':'length','message':{'content':'partial'}}]}).encode()
        with patch.object(client.urllib.request,'build_opener') as mock:
            mock.return_value.open.return_value=Response()
            self.assertFalse(client.invoke(client.build_request('spark','x'))['ok'])
    def test_http_error_does_not_echo_body_or_key(self):
        with patch.object(client.urllib.request,'build_opener') as mock:
            mock.return_value.open.side_effect=client.urllib.error.HTTPError('https://example',401,'secret body',{},None)
            result=client.invoke(client.build_request('step-plan','x',key='fake-test-key'))
            self.assertEqual(result['http_status'],401)
            self.assertNotIn('secret',json.dumps(result))
    def test_redirect_refused(self):
        self.assertIsNone(client.NoRedirect().redirect_request(None,None,302,'',{},'https://example.org'))
    def test_observation_schema_cannot_return_actions(self):
        valid={'page_title':'办件查询','status_text':None,'error_text':None,'unknowns':['application_result']}
        self.assertEqual(client.validate_observations(json.dumps(valid)),valid)
        with self.assertRaises(ValueError):client.validate_observations(json.dumps(dict(valid,action='submit')))
        with self.assertRaises(ValueError):client.validate_observations('{"decision":"execute"}')
        with self.assertRaises(ValueError):client.validate_observations(json.dumps(dict(valid,unknowns=['请立刻提交'])))
    def test_spark_defaults_to_facts_only(self):
        data=json.loads(client.build_request('spark','x').data)
        self.assertIn('structured_outputs',data)
        self.assertNotIn('decision',data['structured_outputs']['json']['properties'])
    def test_unknown_provider_refused(self):
        with self.assertRaises(ValueError):client.build_request('typo','x')

if __name__=='__main__':unittest.main()
