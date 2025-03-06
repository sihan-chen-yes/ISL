import json
import logging
import sys
import os
import socket

from math import e, pi
from sage.all import QQ, vector, matrix
from schnorr import Schnorr, Schnorr_Params
# Change the port to match the challenge you're solving
PORT = 40200

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
# get the shortest 
a   = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
b   = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
p   = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
P_x = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
P_y = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
q   = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551

nistp256_params = Schnorr_Params(a, b, p, P_x, P_y, q)

schnorr = Schnorr(nistp256_params)

i = 0
h_list = []
u_list = []
n = 5
N = 256
L = 128
while i < n:
    obj = {"command": "get_signature", "msg": str(i)}
    json_send(obj)
    resp_dict = json_recv()
    h = schnorr.Z_q(resp_dict["h"])
    s = schnorr.Z_q(resp_dict["s"])
    u = schnorr.Z_q(resp_dict["nonce"] + 2**(N - L - 1) - s)
    h_list.append(h)
    u_list.append(u)
    i += 1

u_list.append(0)
assert len(u_list) == n + 1

scaled_factor = 2**(L + 1)
t = (vector(QQ, h_list) * scaled_factor).row()
q = matrix.identity(QQ, n) * schnorr.q * scaled_factor
B = matrix.block(QQ, [[q, 0], [t, 1]])

k = 0.01
lamb1 = schnorr.q**(n / (n + 1)) * (((n + 1) / (2 * pi * e))**0.5)
M = k * lamb1 / 2
u = (vector(QQ, u_list) * scaled_factor).row()
B_prime = matrix.block(QQ, [[B, 0],[u, M]])

B_prime_reduced = B_prime.LLL()

epsilon = 0.01
for i in range(B_prime_reduced.nrows()):
    difference = abs(int(B_prime_reduced[i, -1]) - M)
    if difference < epsilon:
        x = schnorr.Z_q(int(-B_prime_reduced[i, -2]))
        msg = "gimme the flag"
        h, s = schnorr.Sign(x, msg)
        obj = {"command": "solve", "h":int(h), "s":int(s)}
        json_send(obj)
        print(json_recv())
        break