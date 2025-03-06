import json
import logging
import sys
import os
import socket

from sage.all import Zmod
# Change the port to match the challenge you're solving
PORT = 40130

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
print(json_recv())