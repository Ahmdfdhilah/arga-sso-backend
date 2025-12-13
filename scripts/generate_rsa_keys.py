#!/usr/bin/env python3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    keys_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    private_key_path = os.path.join(keys_dir, "jwt_private.pem")
    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    print(f"Private key saved to: {private_key_path}")
    
    public_key_path = os.path.join(keys_dir, "jwt_public.pem")
    with open(public_key_path, "wb") as f:
        f.write(public_pem)
    print(f"Public key saved to: {public_key_path}")
    
    print("\n=== PRIVATE KEY (for SSO .env - JWT_PRIVATE_KEY) ===")
    print(private_pem.decode().replace('\n', '\\n'))
    
    print("\n=== PUBLIC KEY (for HRIS .env - JWT_PUBLIC_KEY) ===")
    print(public_pem.decode().replace('\n', '\\n'))

if __name__ == "__main__":
    generate_rsa_keys()
