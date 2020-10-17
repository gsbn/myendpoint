from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        bleheader = dev.rawData[0:3].hex()
        msglen = ord(dev.rawData[3:4])
        msgtype = dev.rawData[4:5].hex()

        if bleheader == "020106" and msgtype == "ff":
            print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi)
            print(' BLEHeader: ', bleheader)
            print(' MsgLength: ', msglen)
            print(' MsgType: ', msgtype)

            mft = int.from_bytes(dev.rawData[5:7], byteorder='little')
            if mft == 0x0499:
                print(' Manfacturer: RuuviTag 0x0499')
                mydata = dev.rawData[7:]
                print('    FormatVer:', ord(mydata[0:1]), mydata[0:1].hex())
                temp = int.from_bytes(mydata[1:3], byteorder='big', signed=True) * 0.005
                print('     Temp:', temp, mydata[1:3].hex())
                humid = int.from_bytes(mydata[3:5], byteorder='big') * 0.0025
                print('    Humid:', humid, mydata[3:5].hex())
                press = int.from_bytes(mydata[5:7], byteorder='big') + 50000
                print('    Press:', press, mydata[5:7].hex())
                accx = int.from_bytes(mydata[7:9], byteorder='big', signed=True)
                print('     AccX:', accx, mydata[7:9].hex())
                accy = int.from_bytes(mydata[9:11], byteorder='big', signed=True)
                print('     AccY:', accy, mydata[9:11].hex())
                accz = int.from_bytes(mydata[11:13], byteorder='big', signed=True)
                print('     AccZ:', accz, mydata[11:13].hex())
                powerbit = bin(int.from_bytes(mydata[13:15], byteorder='big'))[2:]
                power = int(powerbit[0:11], 2) + 1600
                tx = (int(powerbit[11:], 2)*2)-40
                print('     Batt:', power, powerbit, mydata[13:15].hex())
                print('  TXPower:', tx, powerbit, mydata[13:15].hex())
                movct = int.from_bytes(mydata[15:16], byteorder='big')
                print('    MovCt:', movct, mydata[15:16].hex())
                seq = int.from_bytes(mydata[16:18], byteorder='big')
                print('      Seq:', seq, mydata[16:18].hex())
                print('      MAC:', mydata[18:24].hex())
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

            print(' RawData: ', dev.rawData[7:].hex())
            print(' RawData Len: ', len(dev.rawData[7:]))
        #else:
            #print(' RawData: ', dev.rawData.hex())
            #print(' RawData Len: ', len(dev.rawData[5:]))
        scanner.clear()
        scanner.start()

scanner = Scanner().withDelegate(ScanDelegate())
scanner.start()

while True:
    scanner.process()
