import socket
import json
import math
from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate

def send_hs_command(address, port, sdata):
    data = b""

    #print("TCP Opening Socket")
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect((address, port))
        tcp_sock.send(bytes(sdata + "\r\n", "ascii"))
        data = tcp_sock.recv(2048)
    except socket.error:
        print("TCP Socket closed")
    finally:
        tcp_sock.close()
    return data

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        try:
            bleheader = dev.rawData[0:3].hex()
            msglen = ord(dev.rawData[3:4])
            msgtype = dev.rawData[4:5].hex()
        except Exception:
            bleheader = ""
            msglen = ""
            msgtype = ""

        if bleheader == "020106" and msgtype == "ff":
            
            #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi)
            #print(' BLEHeader: ', bleheader)
            #print(' MsgLength: ', msglen)
            #print(' MsgType: ', msgtype)

            mft = int.from_bytes(dev.rawData[5:7], byteorder='little')
            if mft == 0x0499:
                print(' Manfacturer: RuuviTag 0x0499')
                mydata = dev.rawData[7:]
                formatver = ord(mydata[0:1])
                print('    FormatVer:', ord(mydata[0:1]), mydata[0:1].hex())
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
                tx = (int(powerbit[11:], 2)*2)-40
                #print('     Batt:', power, powerbit, mydata[13:15].hex())
                #print('  TXPower:', tx, powerbit, mydata[13:15].hex())
                movct = int.from_bytes(mydata[15:16], byteorder='big')
                #print('    MovCt:', movct, mydata[15:16].hex())
                seq = int.from_bytes(mydata[16:18], byteorder='big')
                #print('      Seq:', seq, mydata[16:18].hex())
                mac = mydata[18:24].hex()
                #print('      MAC:', mydata[18:24].hex())
                # JSON Format
                ble_dict = {"data_format": formatver,
                    "humidity": float("{:.2f}".format(humid)),
                    "temperature": float("{:.2f}".format(temp)),
                    "pressure": press,
                    "acceleration": math.sqrt(accx * accx + accy * accy + accz * accz),
                    "acceleration_x": accx,
                    "acceleration_y": accy,
                    "acceleration_z": accz,
                    "tx_power": tx,
                    "battery": power,
                    "movement_counter": movct,
                    "measurement_sequence_number": seq,
                    "mac": mac
                }
                json_data = json.dumps(ble_dict, indent = 4)
                #print(json_data)
                send_hs_command("10.2.0.23", 1888, json_data)                

            elif mft == 0x0583:
                print(' Manfacturer: PuckJS 0x0583')
                mydata = dev.rawData[7:]
                #per = int.from_bytes(mydata[2:3], byteorder='big')
                #print('     Per:', per, mydata[2:3].hex())
                batt = int.from_bytes(mydata[3:4], byteorder='big')
                batt2 = ((batt/255)*(3.6-2.0))+2.0
                print('    Batt:', batt2, batt, mydata[3:4].hex())
                temp = int.from_bytes(mydata[4:5], byteorder='big')
                temp2 = (temp*0.5) - 40
                print('    Temp:', temp2,  temp, mydata[4:5].hex())
                light = int.from_bytes(mydata[5:6], byteorder='big')
                light2 = light / 255
                print('   Light:', light2, light, mydata[5:6].hex())
                #cap = int.from_bytes(mydata[6:7], byteorder='big')
                #cap2 = (cap/255)*262144
                #print('     Cap:', cap2, cap, mydata[6:7].hex())
                magx = int.from_bytes(mydata[7:9], byteorder='big', signed=True)
                magy = int.from_bytes(mydata[9:11], byteorder='big', signed=True)
                magz = int.from_bytes(mydata[11:13], byteorder='big', signed=True)
                print('     Mag:', magx, magy, magz, mydata[7:13].hex())
            elif mft == 0x004c:
                print(' Manfacturer: Apple 0x004c')
            else:
                print(' Manfacturer: ', '0x' + hex(mft)[2:].zfill(4), dev.rawData[5:7], dev.rawData[5:7].hex())

            #print(' RawData: ', dev.rawData[7:].hex())
            #print(' RawData Len: ', len(dev.rawData[7:]))
        #else:
            #print(' RawData: ', dev.rawData.hex())
            #print(' RawData Len: ', len(dev.rawData[5:]))

scanner = Scanner().withDelegate(ScanDelegate())
scanner.start()

while True:
    scanner.process()
