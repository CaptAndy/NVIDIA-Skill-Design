"""Run inside the exact serving image, with /model mounted read-only."""
import hashlib,json,random,string
from pathlib import Path
from transformers import AutoTokenizer
original=AutoTokenizer.from_pretrained('/model',trust_remote_code=True)
preserved=AutoTokenizer.from_pretrained('/model',trust_remote_code=True,fix_mistral_regex=False)
converted=AutoTokenizer.from_pretrained('/model',trust_remote_code=True,fix_mistral_regex=True)
samples=['我想查办件进度。','材料.pdf 2MB 已受理','你好\n下一步','Hello WORLD 123456','ABCDef 中文 mixedCASE','\n \t\r\n','é 中文，标点！？','test@example.invalid']
r=random.Random(20260925);alphabet=string.ascii_letters+string.digits+' 中文办理受理提交。！？\n\t'
samples += [''.join(r.choice(alphabet) for _ in range(r.randint(1,200))) for _ in range(1000)]
result={'model_type':json.loads(Path('/model/config.json').read_text()).get('model_type'),'samples':len(samples),'original_vs_false_differences':sum(original.encode(x)!=preserved.encode(x) for x in samples),'original_vs_true_differences':sum(original.encode(x)!=converted.encode(x) for x in samples),'source_tokenizer_sha256':hashlib.sha256(Path('/model/tokenizer.json').read_bytes()).hexdigest()}
print(json.dumps(result,indent=2))
if result['original_vs_false_differences']:raise SystemExit(1)
