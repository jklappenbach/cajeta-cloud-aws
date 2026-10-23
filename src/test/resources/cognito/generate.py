import json, base64, os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
out = "fixtures"; os.makedirs(out, exist_ok=True)
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def i2b(n): return n.to_bytes((n.bit_length()+7)//8, "big")
# Fixed keys from a deterministic source are not possible with cryptography's RSA;
# generated once, the fixtures are committed and never regenerated.
keys = {k: rsa.generate_private_key(public_exponent=65537, key_size=2048)
        for k in ["access-kid-1", "id-kid-1", "rotated-kid-2"]}
def jwk(kid):
    pn = keys[kid].public_key().public_numbers()
    return {"alg": "RS256", "e": b64(i2b(pn.e)), "kid": kid, "kty": "RSA", "n": b64(i2b(pn.n)), "use": "sig"}
REGION, POOL, CLIENT = "us-east-1", "us-east-1_ExAmPlE12", "3n4b5urk1ft4fl3mg5e62d9ado"
ISS = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL}"
SUB = "4f3c2a10-9b7e-4d6a-8c21-0e5f7a9b3d14"
IAT = 1767225600; EXP = IAT + 3600
def sign(kid, payload, alg="RS256"):
    h = b64(json.dumps({"kid": kid, "alg": alg}, separators=(",", ":")).encode())
    p = b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = keys[kid].sign(f"{h}.{p}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{h}.{p}.{b64(sig)}"
def access(**over):
    c = {"sub": SUB, "cognito:groups": ["admins", "editors"], "iss": ISS, "version": 2,
         "client_id": CLIENT, "origin_jti": "0b1c2d3e-aaaa-bbbb-cccc-000000000001",
         "event_id": "5e6f7a8b-aaaa-bbbb-cccc-000000000002", "token_use": "access",
         "scope": "aws.cognito.signin.user.admin", "auth_time": IAT, "exp": EXP, "iat": IAT,
         "jti": "9a8b7c6d-aaaa-bbbb-cccc-000000000003", "username": "ada"}
    c.update(over); return c
def idt(**over):
    c = {"sub": SUB, "cognito:groups": ["admins", "editors"], "email_verified": True, "iss": ISS,
         "cognito:username": "ada", "origin_jti": "0b1c2d3e-aaaa-bbbb-cccc-000000000001",
         "aud": CLIENT, "event_id": "5e6f7a8b-aaaa-bbbb-cccc-000000000002", "token_use": "id",
         "auth_time": IAT, "exp": EXP, "iat": IAT, "jti": "9a8b7c6d-aaaa-bbbb-cccc-000000000004",
         "email": "ada@example.com", "custom:team": "engines"}
    c.update(over); return c
files = {
  "jwks.json": json.dumps({"keys": [jwk("access-kid-1"), jwk("id-kid-1")]}),
  "jwks-rotated.json": json.dumps({"keys": [jwk("access-kid-1"), jwk("id-kid-1"), jwk("rotated-kid-2")]}),
  "access.jwt": sign("access-kid-1", access()),
  "id.jwt": sign("id-kid-1", idt()),
  "access-wrong-issuer.jwt": sign("access-kid-1", access(iss=f"https://cognito-idp.{REGION}.amazonaws.com/us-east-1_OtHeRpOoL")),
  "access-wrong-client.jwt": sign("access-kid-1", access(client_id="someotherclientid000000000")),
  "id-wrong-audience.jwt": sign("id-kid-1", idt(aud="someotherclientid000000000")),
  "access-rotated-key.jwt": sign("rotated-kid-2", access()),
}
# a signature that does not verify: the payload altered after signing
t = files["access.jwt"].split(".")
forged = access(username="mallory")
files["access-forged.jwt"] = ".".join([t[0], b64(json.dumps(forged, separators=(",", ":")).encode()), t[2]])
for name, text in files.items():
    open(f"{out}/{name}", "w").write(text)
print(json.dumps({"region": REGION, "pool": POOL, "client": CLIENT, "iss": ISS, "sub": SUB, "iat": IAT, "exp": EXP}))
