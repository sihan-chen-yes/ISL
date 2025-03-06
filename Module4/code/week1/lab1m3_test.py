import json
import logging
import re
import sys
import os
import socket
import time
from tkinter import NO
from matplotlib import testing

from sympy import O
from ecdsa2 import ECDSA2, ECDSA2_Params, Point, bits_to_int, hash_message_to_bits
from sage.all import Zmod, Integer, ceil
# Change the port to match the challenge you're solving
PORT = 40130

# Pro tip: for debugging, set the level to logging.DEBUG if you want
# to read all the messages back and forth from the server
# log_level = logging.DEBUG
log_level = logging.INFO
logging.basicConfig(stream=sys.stdout, level=log_level)

fd = None 

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
def test():
# get the shortest 
    #TODO num
    num = 2000
    i = 0
    obj = {"command": "get_signature"}
    res = {}
    while i < num:
        json_send(obj)
        resp_dict = json_recv()
        msg = resp_dict["msg"]
        t = resp_dict["time"]
        res[t] = msg
        i += 1
    sorted_times = sorted(res.keys())[:20]
    msgs = []
    for t in sorted_times:
        msgs.append(res[t])
    assert len(msgs) == 20
    obj = {"command": "solve", "messages":msgs}
    json_send(obj)
    obj = json_recv()
    return 1 if "flag" in obj.keys() else 0

test_time = 500
success = 0
i = 0
for i in range(test_time):
    s = socket.socket()

    if "REMOTE" in os.environ:
        s.connect(("isl.aclabs.ethz.ch", PORT))
    else:
        s.connect(("localhost", PORT))

    fd = s.makefile("rw")
    success += test()
    print(f'testing for the {i + 1} round, now the successrate is {success / (i + 1)}')
print(f'final success rate is {success / test_time}')