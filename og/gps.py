import adafruit_gps
import busio
import board
import asyncio
from time import monotonic
import binascii

class OGGPS:
    def __init__(self, tx=board.GP8, rx=board.GP9, baudrate=9600, timeout=5):
        self.uart = busio.UART(tx, rx, baudrate=baudrate, timeout=timeout)
        self.gps = adafruit_gps.GPS(self.uart)
        self.locationData = {
            'time': '',
            'latitude': '',
            'longitude': '',
            'fix': 0,
            'sats': 0,
            'hpos': 0,
            'altitude': 0,
            'altitudeUnit': 0,
            'height': 0,
            'heightUnit': 0,
            'dgpsUpdate': 0,
            'dgpsID': 0,
            'checksum': '',
            'speed': '',
            'date' : ''
        }

    def convertToDegree(self, rawDegrees, direction):
        rawAsFloat = float(rawDegrees)
        firstdigits = int(rawAsFloat/100)
        nexttwodigits = rawAsFloat - float(firstdigits*100)
        converted = float(firstdigits + nexttwodigits/60.0)
        if direction in ['W','S']:
            converted = -converted
        converted = '{0:.6f}'.format(converted)
        return str(converted)

    def messageParser(self, sentenceString):
        message = sentenceString.split(',')
        checkSum = message[-1].split('*')
        message[-1] = checkSum[0]
        message.append(checkSum[1])
        return message

    def getData(self, debug=False):
        fetchingData = True
        message = ''
        distinctMessages = []
        while fetchingData:
            try:
                sentence = self.gps.readline()
                if sentence:
                    sentenceString = str(sentence, 'ascii').strip()
                    message = self.messageParser(sentenceString)
                    if message[0][-3:] not in distinctMessages:
                        distinctMessages.append(message[0][-3:])
                    if debug:
                        if 'GSA' in message[0]:
                            print('MODE 1: {}, MODE 2: {}'.format(message[1], message[2]))
                        if 'GSV' in message[0]:
                            print('Message: {}/{} - In view: {}'.format(message[2], message[1], message[3]))
                            for sat in range(int(message[3])/int(message[1])):
                                satOffset = 4 * sat
                                idIndex = 4 + satOffset
                                strIndex = 7 + satOffset
                                if len(message) > (strIndex):
                                    print('S: {} - {}dbHz'.format(message[idIndex], message[strIndex]))
                    if 'RMC' in message[0]:
                            self.locationData['date'] = message[9]
                            if message[2] is 'A':
                                self.locationData['speed'] = '{0:.1f}'.format(float(message[7]) * 1.852)
                    if 'GGA' in message[0]:
                        self.locationData['time'] = message[1]
                        if  int(message[6]) > 0:
                            self.locationData['latitude'] = self.convertToDegree(message[2], message[3])
                            self.locationData['longitude'] = self.convertToDegree(message[4], message[5])
                            self.locationData['fix'] = int(message[6])
                            self.locationData['sats'] = message[7]
                            self.locationData['hpos'] = message[8]
                            self.locationData['altitude'] = message[9]
                            self.locationData['altitudeUnit'] = message[10]
                            self.locationData['height'] = message[11]
                            self.locationData['heightUnit'] = message[12]
                            #self.locationData['dgpsUpdate'] = binascii.unhexlify(message[13])
                            #self.locationData['dgpsID'] = message[14]
                            self.locationData['checksum'] = message[15]
                    if len(distinctMessages) > 5 :
                        fetchingData = False
                        if debug:
                            print('--------------------')
                            for index,val in self.locationData.items():
                                print('{}:{}'.format(index,val))
                            print('+++++++++++++++++++++')
            except Exception as e:
                print(e)
            

    async def update(self, debug=False, track=None):
        initialFixing = True
        while True:
            track.location = self.locationData
            if (track.gpsStart + track.updateInterval) < monotonic() and not initialFixing:
                track.gpsStart = monotonic()
                self.getData(debug)
                track.fixStatus = 2
                track.gpsText = 'Don\'t call it a warning, this is a war.'
                track.display = True
            if self.locationData['fix'] > 0 and initialFixing:
                self.getData(debug)
                track.fixStatus = 1
                initialFixing = False
                track.gpsText = 'This is the moment you\'ve been waiting for.'
                track.display = True
            elif initialFixing and self.locationData['fix'] < 1:
                self.getData(debug)
                track.fixStatus = 0
                track.gpsText = 'We cannot save you, enjoy the ride.'
                track.display = True
            await asyncio.sleep(0)

