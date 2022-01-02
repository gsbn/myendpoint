import math
from Cryptodome.Cipher import AES # pip install pycryptodomex

def ProcessRawData(rawData, ble_keys):
    ble_dict = {}

    try:
        bleheader = rawData[0:3].hex()
        msglen = ord(rawData[3:4])
        msgtype = rawData[4:5].hex()
    except Exception:
        bleheader = ""
        msglen = ""
        msgtype = ""

    if bleheader == "020106" and msgtype == "16":

        #print(' BLEHeader: ', bleheader)
        #print(' MsgLength: ', msglen)
        #print(' MsgType: ', msgtype)

        #print(' RawData: ', rawData[7:].hex())
        #print(' RawData: ', rawData.hex())
        #print(' RawData Len: ', len(rawData[7:]))
        #print(' RawData Len: ', len(rawData))

        mft = int.from_bytes(rawData[5:7], byteorder='little')
        if mft == 0xfe95:
            #print(' Manfacturer: Xiaomi 0xfe95')
            mydata = rawData[7:]

            # extract frame control bits
            frctrl = mydata[0] + (mydata[1] << 8) # (22616)
            frctrl_mesh = (frctrl >> 7) & 1  # mesh device (0)
            frctrl_version = frctrl >> 12  # version (5)
            frctrl_auth_mode = (frctrl >> 10) & 3 # (2) Standard certification
            frctrl_solicited = (frctrl >> 9) & 1 # (0)
            frctrl_registered = (frctrl >> 8) & 1 # (0)
            frctrl_object_include = (frctrl >> 6) & 1 # (1)
            frctrl_capability_include = (frctrl >> 5) & 1 # (0)
            frctrl_mac_include = (frctrl >> 4) & 1  # check for MAC address in data (1)
            frctrl_is_encrypted = (frctrl >> 3) & 1  # check for encryption being used (1)
            frctrl_request_timing = frctrl & 1  # old version (0)

            # 0x03D6: "CGH1"
            #device_id = mydata[2] + (mydata[3] << 8)
            device_id = int.from_bytes(mydata[2:4], byteorder='little')

            if frctrl_is_encrypted == 1 and device_id == 0x03D6: # 0x03D6: "CGH1 - Door Sensor"

                packet_id = mydata[4]

                # extract mac address and reverse it
                mac = mydata[5:11][::-1]
                
                # get security key from json
                #key = bytes.fromhex("9c480e19bb03e7a262c2f1f92ec5de0d")
                key = bytes.fromhex(ble_keys.get(mac.hex()))

                i = (9 + 6) # Default offset
                doorstatus = -1
                batt = -1
                volt = -1
                payload = decrypt_mibeacon(rawData[3:], i, mac, key)
                if payload:
                    decrypted = payload.hex()
                    payload_start = 0
                    payload_length = len(payload)
                    while payload_length >= payload_start + 3:
                        obj_typecode = payload[payload_start] + (payload[payload_start + 1] << 8)
                        obj_length = payload[payload_start + 2]
                        next_start = payload_start + 3 + obj_length
                        if payload_length < next_start:
                            print("Invalid payload data length, payload:", payload.hex())
                            break
                        object = payload[payload_start + 3:next_start]
                        if obj_length != 0:
                            if obj_typecode == 0x1019:
                                # Door sensor
                                doorstatus = object[0]
                            elif obj_typecode == 0x100a:
                                # Battery
                                batt = object[0]
                                volt = 2.2 + (3.1 - 2.2) * (batt / 100)

                        payload_start = next_start
                else:
                    decrypted = "NONE"

                ble_dict.update({
                    #"debug": 1,
                    "mft_id": '{:04x}'.format(mft),
                    "device": "xiaomi",
                    "version": frctrl_version,
                    "device_id": '{:04x}'.format(device_id),
                    "packet_id": '{:02x}'.format(packet_id),
                    "decrypted": decrypted,
                    "doorstatus": doorstatus,
                    "battery": batt,
                    "voltage": round(volt, 3),
                    "mac": mac.hex()
                })

    elif bleheader == "020106" and msgtype == "ff":

        mft = int.from_bytes(rawData[5:7], byteorder='little')
        if mft == 0x0499:
            #print(' Manfacturer: RuuviTag 0x0499')
            mydata = rawData[7:]
            formatver = ord(mydata[0:1])
            #print('    FormatVer:', ord(mydata[0:1]), mydata[0:1].hex())
            temp = int.from_bytes(mydata[1:3], byteorder='big', signed=True) * 0.005
            #print('     Temp:', temp, mydata[1:3].hex())
            humid = int.from_bytes(mydata[3:5], byteorder='big') * 0.0025
            #print('    Humid:', humid, mydata[3:5].hex())
            press = (int.from_bytes(mydata[5:7], byteorder='big') + 50000) / 100
            #print('    Press:', press, mydata[5:7].hex())
            accx = int.from_bytes(mydata[7:9], byteorder='big', signed=True)
            #print('     AccX:', accx, mydata[7:9].hex())
            accy = int.from_bytes(mydata[9:11], byteorder='big', signed=True)
            #print('     AccY:', accy, mydata[9:11].hex())
            accz = int.from_bytes(mydata[11:13], byteorder='big', signed=True)
            #print('     AccZ:', accz, mydata[11:13].hex())
            powerbit = bin(int.from_bytes(mydata[13:15], byteorder='big'))[2:]
            power = int(powerbit[0:11], 2) + 1600
            voltage = power / 1000
            if voltage >= 3.00:
                batt = 100
            elif voltage >= 2.60:
                batt = 60 + (voltage - 2.60) * 100
            elif voltage >= 2.50:
                batt = 40 + (voltage - 2.50) * 200
            elif voltage >= 2.45:
                batt = 20 + (voltage - 2.45) * 400
            else:
                batt = 0
            batt = round(batt, 1)
            tx = (int(powerbit[11:], 2)*2)-40
            #print('     Batt:', power, powerbit, mydata[13:15].hex())
            #print('  TXPower:', tx, powerbit, mydata[13:15].hex())
            movct = int.from_bytes(mydata[15:16], byteorder='big')
            #print('    MovCt:', movct, mydata[15:16].hex())
            seq = int.from_bytes(mydata[16:18], byteorder='big')
            #print('      Seq:', seq, mydata[16:18].hex())
            mac = mydata[18:24].hex()
            #print('      MAC:', mydata[18:24].hex())
            # JSON Data
            ble_dict.update({
                "mft_id": '{:04x}'.format(mft),
                "device": "ruuvitag",
                "data_format": formatver,
                "humidity": float("{:.2f}".format(humid)),
                "temperature": float("{:.2f}".format(temp)),
                "pressure": press,
                "acceleration": math.sqrt(accx ** 2 + accy ** 2 + accz ** 2),
                "acceleration_x": accx,
                "acceleration_y": accy,
                "acceleration_z": accz,
                "tx_power": tx,
                "battery_voltage": voltage,
                "battery_percent": batt,
                "movement_counter": movct,
                "measurement_sequence_number": seq,
                "mac": mac
            })
        

        elif mft == 0x0583:
            #print(' Manfacturer: PuckJS 0x0583')
            mydata = rawData[7:]
            #per = int.from_bytes(mydata[2:3], byteorder='big')
            #print('     Per:', per, mydata[2:3].hex())
            batt = int.from_bytes(mydata[3:4], byteorder='big')
            batt2 = ((batt/255)*(3.6-2.0))+2.0
            #print('    Batt:', batt2, batt, mydata[3:4].hex())
            temp = int.from_bytes(mydata[4:5], byteorder='big')
            temp2 = (temp*0.5) - 40
            #print('    Temp:', temp2,  temp, mydata[4:5].hex())
            light = int.from_bytes(mydata[5:6], byteorder='big')
            light2 = light / 255
            #print('   Light:', light2, light, mydata[5:6].hex())
            #cap = int.from_bytes(mydata[6:7], byteorder='big')
            #cap2 = (cap/255)*262144
            #print('     Cap:', cap2, cap, mydata[6:7].hex())
            magx = int.from_bytes(mydata[7:9], byteorder='big', signed=True)
            magy = int.from_bytes(mydata[9:11], byteorder='big', signed=True)
            magz = int.from_bytes(mydata[11:13], byteorder='big', signed=True)
            #print('     Mag:', magx, magy, magz, mydata[7:13].hex())
            ble_dict.update({
                "debug": 1,
                "mft_id": '{:04x}'.format(mft),
                "device": "puckjs"
            })
        elif mft == 0x004c:
            #print(' Manfacturer: Apple 0x004C')
            ble_dict.update({
                "debug": 1,
                "mft_id": '{:04x}'.format(mft),
                "device": "apple"
            })
        #else:
            #print(' Manfacturer: ', '0x' + hex(mft)[2:].zfill(4), rawData[5:7], rawData[5:7].hex())

    return ble_dict


def decrypt_mibeacon(data, i, xiaomi_mac, key):
    # check for minimum length of encrypted advertisement
    if len(data) < i + 9:
        print("Invalid data length (for decryption), adv: ", data.hex())
    # try to find encryption key for current device
    try:
        if len(key) != 16:
            print("Encryption key should be 16 bytes (32 characters) long")
            return None
    except KeyError:
        # no encryption key found
        print("No encryption key found for device with MAC ", xiaomi_mac)
        return None

    nonce = b"".join([xiaomi_mac[::-1], data[6:9], data[-7:-4]])
    aad = b"\x11"
    token = data[-4:]
    cipherpayload = data[i:-7]
    cipher = AES.new(key, AES.MODE_CCM, nonce=nonce, mac_len=4)
    cipher.update(aad)

    try:
        decrypted_payload = cipher.decrypt_and_verify(cipherpayload, token)
    except ValueError as error:
        print("Decryption failed: ", error)
        print("token: ", token.hex())
        print("nonce: ", nonce.hex())
        print("cipherpayload: ", cipherpayload.hex())
        return None
    if decrypted_payload is None:
        print("Decryption failed for %s, decrypted payload is None", xiaomi_mac)
        return None
    return decrypted_payload