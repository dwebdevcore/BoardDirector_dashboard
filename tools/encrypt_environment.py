# -*- coding: utf-8 -*-
import base64
import json

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


def encrypt_boarddirector_env():
    plaintext = json.dumps(
        {'DOMAIN':                  'www.boarddirector.co',
         'AWS_STORAGE_BUCKET_NAME': '{{ get from server }}',
         'AWS_ACCESS_KEY_ID':       '{{ get from server }}',
         'AWS_SECRET_ACCESS_KEY':   '{{ get from server }}'}
    )
    bd_pubkey_str = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDVSooBQENaBcsZJUWVYMlS/31tDEJ2hrh0O8Qm1hZjo6KQkuL70qBGPThdkRTqe03rBtPCX8jPkRVG8l2gGYJ10TFiHXTmIUiiizCBOjov2m7otL1G+kbGxYOX8rlSmiQOuUqkGEOqJ429OiZpZYeA+EUQepuowG4xcoLlwTQvMMpd+E0iF+7vkHdxD+5e1kgnn6nLNGLjh1JA/vi0BXIQDPRlG87rxjDXEf1L43SM7RCeKHWoU4pTQwCWuqWNDI28u01DD8xnJKUkamkGyMo2b32pIiGPWG+rpnOhKH6Y8rqsgU8i7ms4cjUO498kMDKa92sHqaZ/CYQYMLQOSpcp ubuntu@ip-172-31-13-87"""
    bd_public_key = RSA.importKey(bd_pubkey_str)
    cipher = PKCS1_OAEP.new(bd_public_key)
    ct = cipher.encrypt(plaintext)
    print base64.b64encode(ct)


if __name__ == "__main__":
    encrypt_boarddirector_env()
