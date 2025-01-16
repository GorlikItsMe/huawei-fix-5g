from time import sleep
from huawei_lte_api.Connection import Connection
from huawei_lte_api.Client import Client
from huawei_lte_api.enums.net import NetworkModeEnum
from dotenv import dotenv_values
config = dotenv_values(".env")


class Config():
    router_ip = config.get('ROUTER_IP', '192.168.8.1')
    username = config.get('ROUTER_USERNAME', 'admin')
    password = config.get('ROUTER_PASSWORD', 'admin')


connection_string = f'http://{Config.username}:{Config.password}@{Config.router_ip}/'

with Connection(connection_string) as connection:
    client = Client(connection)

    is4g = client.monitoring.status()["SignalIconNr"] == "0"

    print(f"4G: {is4g}")
    if is4g:
        print("its 4G. Lets try fix that!")

        data = client.net.net_mode()
        print(data)
        print("switch to 4G only")
        client.net.set_net_mode(
            lteband=data['LTEBand'],
            networkband=data['NetworkBand'],
            networkmode=NetworkModeEnum.MODE_4G_ONLY
        )
        print("wait 10sek for network to switch...")
        sleep(10)
        data = client.net.net_mode()
        print(data)
        print("set back to auto (5G)")
        client.net.set_net_mode(
            lteband=data['LTEBand'],
            networkband=data['NetworkBand'],
            networkmode=NetworkModeEnum.MODE_AUTO
        )
    else:
        print("You are already on 5G")
