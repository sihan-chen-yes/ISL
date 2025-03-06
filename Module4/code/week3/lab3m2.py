import json
import logging
import sys
import os
import socket

from sage.all import PolynomialRing, ZZ, Sequence, Zmod
# Change the port to match the challenge you're solving
PORT = 40320

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

# WRITE YOUR SOLUTION HERE
obj = {"command": "get_ciphertext"}
json_send(obj)
resp_dict = json_recv()
ciphertext = resp_dict['ciphertext']
ciphertext = bytes.fromhex(ciphertext)
key_byte = 256
m_byte = 16
place_holder = bytes([0] * (key_byte - m_byte))
assert len(place_holder) == key_byte - m_byte
keystream_LSB = xor(ciphertext[m_byte:], place_holder)
S_y = keystream_LSB[112:]
#128 bytes
assert len(S_y) == 128
S_y_int = int.from_bytes(S_y)
S_x_LSB = keystream_LSB[:112]
assert len(S_x_LSB) == 112
S_x_LSB_int = int.from_bytes(S_x_LSB)

a = 17
b = 1
N = 0x579d4e9590eeb88fd1b640a4d78fcf02bd5c375351cade76b69561d9922d3070d479a67192c67265cf9ae4a1efde400ed40757b0efd2912cbda49e60c83a1ddd361d31859bc4e206158491a528bd46d0b41c6e8d608c586a0788b8027f0f796e9e077766f83683fd52965101bb7bf9fd90c9e9653f02fada8bf10d62bc325ef

M = N
d = 3
X = int(M**(2 / (d * (d + 1))) / (2**0.5 * (d + 1)**(1 / d)))

R = PolynomialRing(Zmod(M), 1, 'x')
x = R.gen()
F = (S_x_LSB_int + (x * 2**(112 * 8)))**3 + a * (S_x_LSB_int + (x * 2**(112 * 8))) + b - S_y_int**2
#to monic
F = F / (F.coefficient(x**3))
coefficients = F.coefficients()[::-1]

R = PolynomialRing(ZZ, 1, 'x')
x = R.gen()
S = Sequence([], R)
S.append(M)
S.append(M*X*x)
S.append(M*(X*x)**2)
P = 0
for i, coef in enumerate(coefficients):
    P += int(coef) * (X*x)**i
S.append(P)

matrix, monomials = S.coefficient_matrix(sparse=False)
n_cols = matrix.ncols()
matrix = matrix.matrix_from_columns([n_cols - 1 - i for i in range(n_cols)])
reduced_matrix = matrix.LLL()

coefficients = reduced_matrix[0]
P = 0
R = PolynomialRing(ZZ, 1, 'x')
x = R.gen()
for i, coef in enumerate(coefficients):
    P += coef / X**i * x**i
root = P.roots()[0][0]

S_x_int = int(S_x_LSB_int + (root * 2**(112 * 8)))
S_x_bytes = S_x_int.to_bytes(128)
S_y_bytes = S_y_int.to_bytes(128)
keystream = S_x_bytes + S_y_bytes
assert len(keystream) == 256
msg = xor(ciphertext, keystream)[:m_byte].decode()
obj = {"command": "solve", "plaintext": msg}
json_send(obj)
print(json_recv())