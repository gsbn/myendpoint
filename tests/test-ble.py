import sys
import os
import json

# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
  
# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)
  
# adding the parent directory to the sys.path.
sys.path.append(parent)

import bluelibrary

# Ruuvitag
test_ruuvitag = "0201061bff9904051364459ec51a0004007803e082f6060038cb0b8df98717"
# 020106 # Header
# 1b # Msg Length
# ff # Msg Type
# 9904 # Mft code
# 051364459ec51a0004007803e082f6060038 # Data - from data[4]
# cb0b8df98717 # MAC

# Qingping door sensor
# Mi Bind Key: 9c480e19bb03e7a262c2f1f92ec5de0d
test_qingping = "020106191695fe5858d603cada3a40342d58034f18910100007039c686"
# 020106 # Header
# 19 # Msg Length
# 16 # Msg Type
# 95fe # UUID Service 0xFE95 is a Xiaomi
# 5858 # Frame control Bits
# d603 # Device ID # 0x03D6: "CGH1"
# b1 # Packet ID
# da3a40342d58 # MAC Reversed
# ea74d73f00000041226fed

# "020106191695fe5858d603b1da3a40342d58ea74d73f00000041226fed"
# "020106191695fe5858d603b0da3a40342d58488e7fcc000000e90b1e93"
# "020106191695fe5858d603b4da3a40342d582e081fd600000046df7b78"
# "0201060f1695fe3058d603ffda3a40342d58081c0951696e6770696e6720446f6f722f57696e646f772053656e736f72"
# "020106191695fe5858d603cada3a40342d58034f18910100007039c686"

test_data = test_qingping

ble_keys = {}
ble_dict = bluelibrary.ProcessRawData(bytes.fromhex(test_data),ble_keys)

if "device" in ble_dict:
    json_data = json.dumps(ble_dict, indent = 4)
    print(json_data)
else:
    print("No data")
