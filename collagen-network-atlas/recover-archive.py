"""Recover the public data/source ZIP from the supplement HTML; no network or execution."""
import base64
import hashlib
import io
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path


class Codes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.active=False;self.parts=[];self.blocks=[]
    def handle_starttag(self,tag,attrs):
        if tag=='code':self.active=True;self.parts=[]
    def handle_data(self,data):
        if self.active:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='code' and self.active:self.blocks.append(''.join(self.parts));self.active=False
def recover(html):
    parser=Codes();parser.feed(html)
    for block in parser.blocks:
        m=re.fullmatch(r'FRACTURE_ATLAS_ARCHIVE_SHA256: ([0-9a-f]{64})\s+BASE64_BEGIN\s+(.+?)\s+BASE64_END\s*',block,re.DOTALL)
        if m:
            payload=base64.b64decode(re.sub(r'\s','',m[2]),validate=True)
            assert hashlib.sha256(payload).hexdigest()==m[1],'Archive checksum mismatch'
            with zipfile.ZipFile(io.BytesIO(payload)) as z:assert z.testzip() is None
            return payload,m[1]
    raise ValueError('No complete archive code block found; save the public supplement HTML first.')
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python3 -I recover-archive.py supplement.html')
    payload,digest=recover(Path(sys.argv[1]).read_text())
    output=Path('fracture-atlas-recovered.zip')
    with output.open('xb') as f:f.write(payload)
    print('Wrote',output,'bytes',len(payload),'SHA256',digest)
