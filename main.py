from time import sleep
from huawei_lte_api.Connection import Connection
from huawei_lte_api.Client import Client
from huawei_lte_api.enums.net import NetworkModeEnum
from dotenv import dotenv_values
from utils import Config, send_discord_notification
config = dotenv_values(".env")


if __name__ == "__main__":
    connection_string = f'http://{Config.username}:{Config.password}@{Config.router_ip}/'

    try:
        with Connection(connection_string) as connection:
            client = Client(connection)

            is4g = client.monitoring.status()["SignalIconNr"] == "0"

            print(f"4G: {is4g}")
            if is4g:
                print("its 4G. Lets try fix that!")
                send_discord_notification(
                    "5G Connection Issue Detected: Attempting to fix...")

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
                print("Now it should work. I will check it...")
                sleep(10)
                is4g = client.monitoring.status()["SignalIconNr"] == "0"
                if is4g:
                    send_discord_notification("Done but it didnt help. You are still on 4G.")
                else:
                    send_discord_notification("Done. Now it should work.")
            else:
                print("You are already on 5G")
    except Exception as e:
        send_discord_notification("Crashed")
        raise e
