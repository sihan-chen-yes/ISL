import json
import logging
import sys
import os
import socket

from sage.all import PolynomialRing, ZZ, Sequence, Zmod
# Change the port to match the challenge you're solving
PORT = 40300

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

# WRITE YOUR SOLUTION HERE
obj = {"command": "get_pubkey"}
json_send(obj)
resp_dict = json_recv()
N = resp_dict['n']
e = resp_dict['e']

obj = {"command": "get_ciphertext"}
json_send(obj)
resp_dict = json_recv()
ciphertext = resp_dict['ciphertext']
ciphertext_int = int.from_bytes(bytes.fromhex(ciphertext))

N_BIT_LENGTH = 1024

padded_ptxt = b'\x00'*(1 + 2 * 8)
to_add = N_BIT_LENGTH // 8 - len(padded_ptxt)
padded_ptxt += bytes([to_add] * to_add)
ptxt_int = int.from_bytes(padded_ptxt)

#simple copper
M = N
d = 3
X = int(M**(2 / (d * (d + 1))) / (2**0.5 * (d + 1)**(1 / d)))
f0 = -ciphertext_int

R = PolynomialRing(Zmod(M), 1, 'x')
x = R.gen()
F = (ptxt_int + (x * 2**(to_add * 8)))**3 + f0
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
msg_enc = int(root).to_bytes(N_BIT_LENGTH // 8)[-16:]
msg = msg_enc.decode()
obj = {"command": "solve", "message": msg}
json_send(obj)
print(json_recv())