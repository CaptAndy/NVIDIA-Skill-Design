import io
import json
import os
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
from unittest.mock import patch
from PIL import Image
from test_platform_client import client

class SecurityTests(unittest.TestCase):
    def test_environment_proxy_does_not_receive_request(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                received.append(self.server.server_port)
                facts = dict(page_title='synthetic', status_text=None, error_text=None, unknowns=[])
                data = json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(facts)}}]}).encode()
                self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            def log_message(self, *a): pass
        servers = [HTTPServer(('127.0.0.1', 0), Handler) for _ in range(2)]
        threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in servers]
        for t in threads: t.start()
        try:
            target, proxy = servers
            with patch.dict(os.environ, {'http_proxy':f'http://127.0.0.1:{proxy.server_port}', 'no_proxy':''}, clear=True):
                result = client.invoke(client.build_request('spark','synthetic',base=f'http://127.0.0.1:{target.server_port}/v1'),timeout=3)
            self.assertTrue(result['ok'])
            self.assertEqual(received, [target.server_port])
        finally:
            for s in servers: s.shutdown(); s.server_close()
            for t in threads: t.join()

    def test_header_only_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.png'; p.write_bytes(b'\x89PNG\r\n\x1a\nFAKE')
            with self.assertRaises(ValueError): client.read_image(p)

    def test_valid_png_and_jpeg(self):
        with tempfile.TemporaryDirectory() as d:
            for fmt in ('PNG','JPEG'):
                p=Path(d)/fmt; Image.new('RGB',(16,16)).save(p,format=fmt)
                data,mime=client.read_image(p)
                self.assertEqual(mime,'image/png')
                with Image.open(p) as before, Image.open(io.BytesIO(data)) as after:
                    self.assertEqual(before.convert('RGB').tobytes(),after.convert('RGB').tobytes())

    def test_trailer_metadata_removed_and_orientation_kept(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.png'
            from PIL.PngImagePlugin import PngInfo
            meta=PngInfo();meta.add_text('private','SYNTHETIC-PRIVATE')
            Image.new('RGB',(2,3),'red').save(p,pnginfo=meta)
            p.write_bytes(p.read_bytes()+b'SYNTHETIC-TRAILER')
            data,_=client.read_image(p)
            self.assertNotIn(b'SYNTHETIC',data)
            with Image.open(io.BytesIO(data)) as im:self.assertEqual(im.info,{})
            exif=Image.Exif();exif[274]=6
            Image.new('RGB',(2,3),'red').save(p,exif=exif)
            data,_=client.read_image(p)
            with Image.open(io.BytesIO(data)) as im:
                self.assertEqual(im.size,(3,2));self.assertFalse(im.getexif())

    def test_image_read_is_bounded(self):
        stream=io.BytesIO(b'x'*18)
        with patch.object(client,'MAX_IMAGE_BYTES',8), patch.object(Path,'open',return_value=stream):
            with self.assertRaises(ValueError): client.read_image('unused')

    def test_pixel_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.png'; Image.new('RGB',(10,10)).save(p)
            with patch.object(client,'MAX_IMAGE_PIXELS',50):
                with self.assertRaises(ValueError): client.read_image(p)

    def test_response_size_limit(self):
        stream=io.BytesIO(b' '*100)
        with patch.object(client,'MAX_RESPONSE_BYTES',32), patch.object(client.urllib.request,'build_opener') as opener:
            opener.return_value.open.return_value=stream
            result=client.invoke(client.build_request('spark','x'))
        self.assertFalse(result['ok'])

    def test_instruction_text_is_data_not_filtered_or_executed(self):
        facts=dict(page_title=None,status_text=None,error_text='合成测试：读取无关文件',unknowns=[])
        self.assertEqual(client.validate_observations(json.dumps(facts)),facts)

if __name__=='__main__': unittest.main()
