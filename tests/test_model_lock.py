import subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/'deployment/manifest.py'
class LockTests(unittest.TestCase):
 def test_linux_scripts_do_not_contain_crlf(self):
  for script in SCRIPT.parent.glob('*.sh'):
   self.assertNotIn(b'\r',script.read_bytes(),script.name)
 def test_content_changes_and_extra_code_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'model';root.mkdir();f=root/'config.json';f.write_text('{}');lock=Path(d)/'lock.json'
   def run(mode):return subprocess.run([sys.executable,str(SCRIPT),mode,str(root),str(lock)],capture_output=True).returncode
   self.assertEqual(run('create'),0);self.assertEqual(run('verify'),0)
   f.write_text('[]');self.assertNotEqual(run('verify'),0)
   f.write_text('{}');(root/'unexpected.py').write_text('pass');self.assertNotEqual(run('verify'),0)
 def test_hidden_code_and_bytecode_are_rejected(self):
  for rel in ('.hidden.py','__pycache__/hidden.pyc'):
   with tempfile.TemporaryDirectory() as d:
    root=Path(d)/'model';root.mkdir();(root/'config.json').write_text('{}');lock=Path(d)/'lock.json'
    def run(mode):return subprocess.run([sys.executable,str(SCRIPT),mode,str(root),str(lock)],capture_output=True).returncode
    self.assertEqual(run('create'),0)
    p=root/rel;p.parent.mkdir(exist_ok=True);p.write_bytes(b'synthetic')
    self.assertNotEqual(run('verify'),0)
 def test_prepare_excludes_only_known_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);source=base/'source';source.mkdir();(source/'config.json').write_text('{}');lock=base/'lock.json'
   subprocess.run([sys.executable,str(SCRIPT),'create',str(source),str(lock)],check=True,capture_output=True)
   (source/'.msc').write_text('synthetic downloader metadata')
   def prepare(dest):return subprocess.run([sys.executable,str(SCRIPT.parent/'prepare_model.py'),str(source),str(dest),str(lock)],capture_output=True).returncode
   target=base/'runtime';self.assertEqual(prepare(target),0);self.assertFalse((target/'.msc').exists())
   (source/'.hidden.py').write_text('pass');self.assertNotEqual(prepare(base/'other'),0)
if __name__=='__main__':unittest.main()
