import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from dotenv import dotenv_values
from utils import Config, is_number
from huawei_lte_api.Connection import Connection
from huawei_lte_api.Client import Client
import huawei_lte_api

PORT = 8888

metric_thread_running = True


class MyMetrics:

    def __init__(self):
        self.info = None
        self.is4g = None
        self.monitoring_status = None
        self.traffic_statistics = None
        self.connected_hosts = []
        self.signal = None
        self._login()

    def _login(self):
        dotenv_values(".env")
        connection_string = f'http://{Config.username}:{Config.password}@{Config.router_ip}/'
        connection = Connection(connection_string)
        self.client = Client(connection)

    def update_metrics(self, try_relogin=True):
        try:
            # Get data from router
            # and save it to self
            t_start = time.time()
            self.info = self.client.device.information()
            self.monitoring_status = self.client.monitoring.status()
            self.is4g = self.monitoring_status["SignalIconNr"] == "0"
            self.traffic_statistics = self.client.monitoring.traffic_statistics()
            self.connected_hosts = self.client.lan.host_info()['Hosts']['Host']

            # _signal = self.client.device.signal()
            # self.signal = {
            #     'rsrq': _signal['rsrq'], # dB
            #     'rsrp': _signal['rsrp'], # dBm
            #     'sinr': _signal['sinr'], # dB
            # }
            t_end = time.time()
            duration = int((t_end - t_start)* 100)
            print(f"Got all information in {duration}ms")

        except huawei_lte_api.exceptions.ResponseErrorLoginRequiredException as err:
            if try_relogin:
                print("relogin...")
                self._login()
                return self.update_metrics(try_relogin=False)
            raise err

    def to_metrics_string(self):
        message = ""

        def dict_2_metric(_dict: dict):
            x = ",".join([f'{key}="{_dict[key]}"' for key in _dict])
            return "{" + x + "}"

        if self.info is not None:
            message += \
                "# HELP router_info A metric with a constant '1' value labeled by router informations\n" \
                "# TYPE router_info gauge\n" \
                f"router_info{dict_2_metric(self.info)} 1\n"

        if self.is4g is not None:
            message += \
                "# HELP router_is_4g '1' if 4G connection is established\n" \
                "# TYPE router_is_4g gauge\n" \
                f"router_is_4g {1 if self.is4g else 0}\n"
                
        dicts_to_show = [
            # (dict, prefix_)
            (self.traffic_statistics, 'traffic_statistics_'),
            (self.monitoring_status, 'monitoring_status_'),
        ]
        for (_dict, key_prefix) in dicts_to_show:
            if _dict is not None:
                for key in _dict:
                    _key = f"{key_prefix}{key.lower()}"
                    value = _dict[key]
                    if is_number(value):
                        message += \
                            f"# HELP {_key}\n" \
                            f"# TYPE {_key} gauge\n" \
                            f"{_key} {value}\n"


        for host in self.connected_hosts:
            # find values (numbers)
            value_names = [key for key in host if is_number(host[key])]
            # cache params
            _fake_json = dict_2_metric(host)
            # create gauge for each value (and add all props)
            for value_name in value_names:
                _key = f'router_devices_{value_name.lower()}'
                value = host[value_name]
                message += \
                    f"# HELP {_key}\n" \
                    f"# TYPE {_key} gauge\n" \
                    f"{_key}{_fake_json} {value}\n"
                    

        return message

my_metric = MyMetrics()

class MyHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler. Doesn't parse the request URL: Always responds with
    the test metrics in the form Prometheus expects them. E.g:

    # HELP python_operations_counter Number of Operations Performed.
    # TYPE python_operations_counter counter
    python_operations_counter 999.0
    ...
    """
    # noinspection PyPep8Naming
    def do_GET(self):
        global my_metric, lock
        lock.acquire()
        message = my_metric.to_metrics_string()
        lock.release()
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))


def generate_metric():
    """
    Function to run in a thread and update the values that are exposed as
    metrics by the 'MyHandler' class
    """
    global my_metric, lock, metric_thread_running

    print("Metric thread started")
    while metric_thread_running:
        lock.acquire()
        try:
            my_metric.update_metrics()
        except:
            pass
        lock.release()
        time.sleep(10)
    print("Metric thread stopped")


# Create a lock to synchronize access to the metric values for the generate_metric function, which
# runs in a thread, and the HTTP response handler
lock = Lock()

# Start up a thread to update the metric values
Thread(target=generate_metric).start()

# Create the HTTP server
httpd = HTTPServer(("", PORT), MyHandler)

try:
    # Start the HTTP server. Control will return when the server is stopped, e.g.
    # by the user pressing CTRL-C, or stopping the app in PyCharm
    print("Running server...")
    httpd.serve_forever()
except:
    print("Server stopped")
    httpd.server_close()
finally:
    # stop the metric update thread
    metric_thread_running = False
