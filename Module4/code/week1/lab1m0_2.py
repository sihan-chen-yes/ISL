import json
import logging
import sys
import os
import socket

from ecdsa2 import ECDSA2, ECDSA2_Params, Point
from sage.all import Zmod
# Change the port to match the challenge you're solving
PORT = 40102

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
a   = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
b   = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
p   = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
P_x = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
P_y = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
q   = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551

nistp256_params = ECDSA2_Params(a, b, p, P_x, P_y, q)

ecdsa2 = ECDSA2(nistp256_params)

obj = {"command": "get_pubkey"}
json_send(obj)
resp_dict = json_recv()
pubkey = Point(ecdsa2.curve, resp_dict['x'], resp_dict['y'])
i = 0
while i < 128:
    obj = {"command": "get_signature"}
    json_send(obj)
    resp_dict = json_recv()
    msg = resp_dict['msg']
    r = ecdsa2.Z_q(resp_dict['r'])
    s = ecdsa2.Z_q(resp_dict['s'])
    res = ecdsa2.Verify(pubkey, msg, r, s)
    b = 1 if res else 0
    obj = {"command": "solve", "b": b}
    json_send(obj)
    print(json_recv())
    i += 1
obj = {"command": "flag"}
json_send(obj)
print(json_recv())