import asyncio
import socketpool
import wifi
from time import monotonic
import json
import os
import microcontroller
from adafruit_httpserver.mime_type import MIMEType
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.server import HTTPServer
### OG Modules
from og.gps import OGGPS
from og.leds import OGLEDS
from og.sd import OGSD

def print_directory(path='/sd'):
    files = []
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " by"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        
        fileData = {
            'filename': prettyprintname,
            'size': sizestr
        }
        files.append(fileData)
    return files

class TrackStatus:
    def __init__(self, status='Please, remain calm, the end has arrived.'):
        self.gpsText = status
        self.fixStatus = 0
        self.display = True
        self.startTime = monotonic()
        self.gpsStart = monotonic()
        self.updateInterval = 30
        self.location = {}
        self.updating = False


leds = OGLEDS()
atHome = False
server = None

leds.writeText('.init.', 0xDC143C)

try:
    from secrets import secrets
    leds.writeText('--secret--', 0xFF0000)
except ImportError:
    leds.writeText('--secret error--', 0xFF0000)
    pass

try:
    leds.writeText('==net==', 0xFFFF00)
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    pool = socketpool.SocketPool(wifi.radio)
    server = HTTPServer(pool)
    leds.setBrightness(0.1)
    leds.writeText(str(wifi.radio.ipv4_address), 0xFFFF00)
    atHome = True
    
except Exception as e:
    print(e)
    server = None
    leds.writeText('It\'s the Parasite Eve.', 0xDC143C)
    pass

if atHome:
    try:
        server.start(str(wifi.radio.ipv4_address))
        print("Listening on http://%s:80" % wifi.radio.ipv4_address)
        gpsData = OGGPS()

        @server.route("/")
        def base(request):
            with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
                response.send_file("/html/index.html")

        @server.route("/log")
        def getLog(request):
            params = request.query_params
            fileDownload = '{}.jsonl'.format(params['file'])
            with HTTPResponse(request) as response:
                response.send_file(filename=fileDownload, root_path='/sd')

        @server.route("/log/clear")
        def clear(request):
            with open('/sd/log.jsonl', 'w'):
                pass
            return HTTPResponse(content_type="text/html", body='file cleared')

        @server.route("/gps")
        def gps(request):
            gpsData.getData()
            currentGPS = json.dumps(gpsData.locationData)
            return HTTPResponse(content_type="application/json", body=currentGPS)

        @server.route("/temp")
        def temp(request):
            tempData = {
                'temp': microcontroller.cpu.temperature
            }
            tempDataJSON = json.dumps(tempData)
            return HTTPResponse(content_type="application/json", body=tempDataJSON)

        @server.route("/logs")
        def logList(request):
            logs = print_directory()
            logsJSON = json.dumps(logs)
            with HTTPResponse(request, content_type=MIMEType.TYPE_JSON) as response:
               response.send(logsJSON)
            
    
    except Exception as e:
        print(e)
        microcontroller.reset()
        server = False

async def updatelog(track):
    sd = OGSD(track)
    sd.writeSD(True)
    while True:
        if (track.startTime + track.updateInterval) < monotonic():
            sd.writeSD(True)
            track.startTime = monotonic()
        await asyncio.sleep(0)


async def main(leds, server):
    trackStatus = TrackStatus()
    gpsData = OGGPS()
    sd_task = asyncio.create_task(updatelog(trackStatus))
    gps_task = asyncio.create_task(gpsData.update(debug=True, track=trackStatus))
    led_task = asyncio.create_task(leds.updateStatus(trackStatus))
    gatherTask =  asyncio.gather(
            gps_task,
            sd_task,
            led_task
        )

    await gatherTask
        
if server and atHome:
    while True:
        server.poll()
else:
    asyncio.run(main(leds, server))
