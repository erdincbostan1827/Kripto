from __future__ import annotations

import argparse
import base64
import os
import struct
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC=b"CTPBK1\n"
CHUNK=1024*1024


def load_key(path:str)->bytes:
    raw=Path(path).read_text(encoding='utf-8').strip().encode('ascii')
    try: key=base64.urlsafe_b64decode(raw)
    except Exception as exc: raise ValueError('invalid backup encryption key encoding') from exc
    if len(key)!=32: raise ValueError('backup encryption key must decode to 32 bytes')
    return key


def encrypt_stream(source,target,key:bytes)->None:
    aes=AESGCM(key); target.write(MAGIC)
    while True:
        block=source.read(CHUNK)
        if not block: break
        nonce=os.urandom(12); encrypted=aes.encrypt(nonce,block,MAGIC)
        target.write(struct.pack('>I',len(encrypted))); target.write(nonce); target.write(encrypted)
    target.write(struct.pack('>I',0))


def decrypt_stream(source,target,key:bytes)->None:
    if source.read(len(MAGIC))!=MAGIC: raise ValueError('invalid backup header')
    aes=AESGCM(key)
    while True:
        size_raw=source.read(4)
        if len(size_raw)!=4: raise ValueError('truncated backup length')
        size=struct.unpack('>I',size_raw)[0]
        if size==0: break
        nonce=source.read(12); encrypted=source.read(size)
        if len(nonce)!=12 or len(encrypted)!=size: raise ValueError('truncated encrypted backup')
        target.write(aes.decrypt(nonce,encrypted,MAGIC))


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['encrypt','decrypt'])
    parser.add_argument('--key-file',required=True)
    args=parser.parse_args()
    key=load_key(args.key_file)
    source=sys.stdin.buffer; target=sys.stdout.buffer
    if args.action=='encrypt': encrypt_stream(source,target,key)
    else: decrypt_stream(source,target,key)

if __name__=='__main__': main()
