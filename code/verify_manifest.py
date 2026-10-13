"""Verify every file listed in the package's SHA-256 manifest."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=json.loads((ROOT/'MANIFEST_SHA256.json').read_text());errors=[]
    for item in manifest['files']:
        p=ROOT/item['path']
        if not p.is_file():errors.append(item['path']+': missing');continue
        if p.stat().st_size!=item['bytes']or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:errors.append(item['path']+': mismatch')
    print(json.dumps({'checked_files':len(manifest['files']),'errors':errors,'status':'PASS'if not errors else'FAIL'},indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
