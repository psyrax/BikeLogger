import busio
import board
import sdcardio
import storage
import wifi
import binascii
import json
import os

spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
sd = sdcardio.SDCard(spi, board.GP13)
vfs = storage.VfsFat(sd)
storage.mount(vfs, '/sd')


class OGSD:
    def __init__(self, status):
        currentNumber = 0
        for file in os.listdir('/sd'):
            if '.jsonl' in file:
                currentNumber = currentNumber+1
        currentFile = "/sd/log{}.jsonl".format(currentNumber)
        self.currentFile = currentFile

        with open(currentFile, "w") as f:
            f.write("")
        self.status = status

    def scanNet(self):
        networks = []
        for network in wifi.radio.start_scanning_networks():
            netAuth = 'UNKNOWN'
            macAddress = binascii.hexlify(network.bssid).decode()
            macAddress = ':'.join(macAddress[i:i+2] for i in range(0,12,2)).upper()
            try:
                netAuth = '{}-{}'.format(str(network.authmode[0]).split('.')[-1], str(network.authmode[1]).split('.')[-1])
            except Exception as e:
                print('Auth Fail 1: {}'.format(e))
                try:
                    netAuth = '{}'.format(str(network.authmode[0]).split('.')[-1])
                except Exception as e:
                    print('Auth Fail 2: {}'.format(e))
            networkDeets = {
                'SSID': str(network.ssid, 'utf-8'),
                'BBID': macAddress,
                'CHAN': network.channel,
                'AUTH': netAuth
            }
            networks.append(networkDeets)
        wifi.radio.stop_scanning_networks()
        res = [i for n, i in enumerate(networks) if i not in networks[n + 1:]]
        return res



    def writeSD(self, debug=False):
        apJson = self.scanNet()
        newData = {
            'location' : self.status.location,
            'networks': apJson
        }
        if debug:
            print('**********************')
            for index,val in newData.items():
                print('{}:{}'.format(index,val))
        with open(self.currentFile, "a") as f:
            f.write("\r\n{}\r\n".format(json.dumps(newData)))
