from base64 import b64decode
from json import loads
from os import path, environ

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


def apply_environment():
    # The following string represents a dictionary of {key: value} pairs for os.environ
    # 1. JSON serialized,
    # 2. encrypted to the SSH public key of www.boarddirector.co
    # 3. base64 encoded
    encrypted_env = """F6DG35NQ8iP3HEsllBee6f3HdpnWQWSYnDjUlb3wqVT/y0jJs4rDnje39rc6b9gv9NXfRHVIuf9D7Sf24vJFB3MutV5YMWiwWVq/ZvVE9waQmuFO89RxyL2PVEN9ZJthegUZn6oTpEL9RyC3T6gQoggZOwf46XuDkZ6WFg1EJyb0Xk9pxQsQ+Xb+4WIpP52Dexvt8ydEi+CqSOoWgwDHgbfDyPNsC1ZKVdFF6VMzVIR8X3xfxjaRoV66dbhol8w50SzQo6HrBDT79qCAkcXFXzxvE1l6N7Yl2anQf6itic8pF+S+ScylhpOemva9dfuvCj6YfTvGb3imBXomdeGSzw=="""
    home_dir = environ.get("HOME", "/home/ubuntu")

    with open(path.join(home_dir, ".ssh", "id_rsa"), "rb") as key_file:
        private_key = RSA.importKey(key_file.read())
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_env = loads(cipher.decrypt(b64decode(encrypted_env)))
    for (k, v) in decrypted_env.items():
        environ.setdefault(k, v)
