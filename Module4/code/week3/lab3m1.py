import json
import logging
import sys
import os
import socket

from math import e, gcd
from sage.all import PolynomialRing, ZZ, Sequence, Zmod
from Crypto.Hash import SHA256
# Change the port to match the challenge you're solving
PORT = 40310

# Pro tip: for debugging, set the level to logging.DEBUG if you want
# to read all the messages back and forth from the server
# log_level = logging.DEBUG
log_level = logging.INFO
logging.basicConfig(stream=sys.stdout, level=log_level)

s = socket.socket()

# Set the environmental variable REMOTE to True in order to connect to the server
#
# To do so, run on the terminal:
# REMOTE=True sage solve.py
#
# When we grade, we will automatically set this for you
if "REMOTE" in os.environ:
    s.connect(("isl.aclabs.ethz.ch", PORT))
else:
    s.connect(("localhost", PORT))

fd = s.makefile("rw")

def json_recv():
    """Receive a serialized json object from the server and deserialize it"""

    line = fd.readline()
    logging.debug(f"Recv: {line}")
    return json.loads(line)

def json_send(obj):
    """Convert the object to json and send to the server"""

    request = json.dumps(obj)
    logging.debug(f"Send: {request}")
    fd.write(request + "\n")
    fd.flush()

def xor(a: bytes, b: bytes) -> bytes:
    if len(a) < len(b):
        a += bytes([0] * (len(b) - len(a)))

    if len(b) < len(a):
        b += bytes([0] * (len(a) - len(b)))

    return bytes(x ^ y for x, y in zip(a, b))

def check(G):
    coefficients = G.coefficients()[::-1]
    for i, coef in enumerate(coefficients):
        assert (coef % X**i) == 0

# WRITE YOUR SOLUTION HERE
identifier = "identifier"
first_bit = 512
key_bit = int(first_bit / 2)
obj = {"command": "gen_key", "bit_length": first_bit, "identifier": identifier}
json_send(obj)
print(json_recv())

second_bit = 2048
p_bit = int(second_bit / 2)
obj = {"command": "gen_key", "bit_length": second_bit, "identifier": identifier}
json_send(obj)
print(json_recv())


obj = {"command": "get_pubkey", "identifier": identifier}
json_send(obj)
resp_dict = json_recv()
n = resp_dict['n']
e = resp_dict['e']
bits = resp_dict['bits']
obj = {"command": "export_p", "identifier": identifier}
json_send(obj)
resp_dict = json_recv()
obfuscated_p = resp_dict['obfuscated_p']
obfuscated_p = bytes.fromhex(obfuscated_p)
#here bytes means bytes stream
obfuscated_keystream = bytes([0] * (p_bit - key_bit))
assert len(obfuscated_p) == p_bit
p_LSB_bits = xor(obfuscated_p[key_bit:], obfuscated_keystream)
p_LSB_int = int(p_LSB_bits.decode(), 2)

N  = n
X = 2**256

R = PolynomialRing(Zmod(N), 1, 'x')
x = R.gen()
F = p_LSB_int + (2**768) * x
F = F / F.coefficient(x)
coefficients = F.coefficients()

R = PolynomialRing(ZZ, 1, 'x')
x = R.gen()
S = Sequence([], R)
coef = int(coefficients[1])
S.append(N)
S.append(X*x + coef)
S.append(X**2*x ** 2 + coef * X * x)
S.append(X**3*x ** 3 + coef * X ** 2 * x**2)

matrix, monomials = S.coefficient_matrix(sparse=False)
n_cols = matrix.ncols()
matrix = matrix.matrix_from_columns([n_cols - 1 - i for i in range(n_cols)])

reduced_matrix = matrix.LLL()

coefficients = reduced_matrix[0]
R = PolynomialRing(ZZ, 1, 'x')
x = R.gen()
P = 0
for i, coef in enumerate(coefficients):
    P += (coef / X**i) * x**i
root = P.roots()[0][0]
F = p_LSB_int + (2**768) * root
p = int(gcd(n, F))
# print(p)
# print(n)
assert n % p == 0
q = n // p
# print(q)
assert n % q == 0
phi = (p - 1) * (q - 1)
Zphi = Zmod(phi)
d = 1 / Zphi(e)
h = int.from_bytes(SHA256.new(b"gimme the flag").digest())
s = Zmod(n)(h) ** d
obj = {"command": "solve", "identifier": identifier, "signature": int(s)}
json_send(obj)
print(json_recv())