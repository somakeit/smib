from http.webserver import Webserver
from lib.ulogging import uLogger
from lib.module_config import ModuleConfig
from json import dumps
import uasyncio
from lib.updater import UpdateCore

class WebApp:

    def __init__(self, module_config: ModuleConfig, hid: object) -> None:
        """
        A web app that provides a web interface to the smibhid device
        leveraging the tinyweb webserver.
        Pass the module_config object to the constructor to allow the webapp to
        access the necessary modules.
        """
        self.log = uLogger("Web app")
        self.log.info("Init webserver")
        self.app = Webserver()
        self.hid = hid
        self.wifi = module_config.get_wifi()
        self.display = module_config.get_display()
        self.sensors = module_config.get_sensors()
        self.update_core = UpdateCore()
        self.port = 80
        self.running = False
        self.create_style_css()
        self.create_update_js()
        self.create_homepage()
        self.create_update()
        self.create_api()

    def startup(self):
        network_access = uasyncio.run(self.wifi.check_network_access())

        if network_access:
            self.log.info("Starting web server")
            self.app.run(host='0.0.0.0', port=self.port, loop_forever=False)
            self.log.info(f"Web server started: {self.wifi.get_ip()}:{self.port}")
            self.running = True
        else:
            self.log.error("No network access - web server not started")
    
    def create_style_css(self):
        @self.app.route('/css/style.css')
        async def index(request, response):
            await response.send_file('/http/www/css/style.css', content_type='text/css')

    def create_update_js(self):
        @self.app.route('/js/update.js')
        async def index(request, response):
            await response.send_file('/http/www/js/update.js', content_type='application/javascript')
    
    def create_homepage(self) -> None:
        @self.app.route('/')
        async def index(request, response):
            await response.send_file('/http/www/index.html')

    def create_update(self) -> None:
        @self.app.route('/update')
        async def index(request, response):
            await response.send_file('/http/www/update.html')

    def create_api(self) -> None:
        @self.app.route('/api')
        async def api(request, response):
            await response.send_file('/http/www/api.html')
        
        self.app.add_resource(WLANMAC, '/api/wlan/mac', wifi = self.wifi, logger = self.log)
        self.app.add_resource(Version, '/api/version', hid = self.hid, logger = self.log)
        
        self.app.add_resource(FirmwareFiles, '/api/firmware_files', update_core = self.update_core, logger = self.log)
        self.app.add_resource(Reset, '/api/reset', update_core = self.update_core, logger = self.log)
        
        self.app.add_resource(Modules, '/api/sensors/modules', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Sensors, '/api/sensors/modules/<module>', sensors = self.sensors, logger = self.log)
        #self.app.add_resource(Readings, '/api/sensors/modules/<module>/readings/latest', sensors = self.sensors, logger = self.log) #TODO: Fix tinyweb to allow for multiple parameters https://github.com/belyalov/tinyweb/pull/51
        self.app.add_resource(Readings, '/api/sensors/readings/latest', module = "", sensors = self.sensors, logger = self.log)
    
class WLANMAC():

    def get(self, data, wifi, logger: uLogger) -> str:
        logger.info("API request - wlan/mac")
        html = dumps(wifi.get_mac())
        logger.info(f"Return value: {html}")
        return html
    
class Version():

    def get(self, data, hid, logger: uLogger) -> str:
        logger.info("API request - version")
        html = dumps(hid.version)
        logger.info(f"Return value: {html}")
        return html

class FirmwareFiles():

    def get(self, data, update_core: UpdateCore, logger: uLogger) -> str:
        logger.info("API request - GET Firmware files")
        html = dumps(update_core.process_update_file())
        logger.info(f"Return value: {html}")
        return html
    
    def post(self, data, update_core: UpdateCore, logger: uLogger) -> str:
        logger.info("API request - POST Firmware files")
        logger.info(f"Data: {data}")
        if data["action"] == "add":
            logger.info("Adding update - data: {data}")
            html = update_core.stage_update_url(data["url"])
        elif data["action"] == "remove":
            logger.info("Removing update - data: {data}")
            html = update_core.unstage_update_url(data["url"])
        else:
            html = f"Invalid request: {data["action"]}"
        return dumps(html)
    
class Reset():

    def post(self, data, update_core: UpdateCore, logger: uLogger) -> None:
        logger.info("API request - reset")
        update_core.reset()
        return
    
class Modules():

    def get(self, data, sensors, logger: uLogger) -> str:
        logger.info("API request - sensors/modules")
        html = dumps(sensors.get_modules())
        logger.info(f"Return value: {html}")
        return html

class Sensors():

    def get(self, data, module: str, sensors, logger: uLogger) -> str:
        logger.info(f"API request - sensors/{module}")
        sensor_list = sensors.get_sensors(module)
        logger.info(f"Available sensors: {sensor_list}")
        html = dumps(sensor_list)
        logger.info(f"Return value: {html}")
        return html

class Readings():

    def get(self, data, module: str, sensors, logger: uLogger) -> str:
        logger.info(f"API request - sensors/readings - Module: {module}")
        html = dumps(sensors.get_readings(module))
        logger.info(f"Return value: {html}")
        return html
