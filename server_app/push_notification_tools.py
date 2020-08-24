from config import Config
import hmac
import base64
from datetime import datetime
from hashlib import sha256
import requests


def generate_cert(json: dict):
    # json_string = str(json)
    # combined = (time_stamp + str(Config.TPN_ACCESS_ID) + json_string).encode()
    # token = hmac.new(combined, Config.TPN_SECRET_KEY.encode(), digestmod=sha256).hexdigest()
    key: str = str(Config.TPN_ACCESS_ID) + ':' + Config.TPN_SECRET_KEY
    return base64.b64encode(key.encode())


def generate_header(json: dict) -> dict:
    # timestamp = str(int(datetime.timestamp(datetime.now())))
    # header = {'Sign': generate_cert(time_stamp=timestamp, json=json),
    #           'TimeStamp': timestamp,
    #           'AccessId': str(Config.TPN_ACCESS_ID)}
    header = {'Authorization': 'Basic ' + generate_cert(json).decode()}
    return header


def account_with_token(platform: str, account: str, token: str, operator_type: int):
    base_url = 'https://api.tpns.tencent.com/v3/device/account/batchoperate'
    data = {
        "operator_type": operator_type,
        "platform": platform,
        "token_accounts": [{
            "token": token,
            "account_list": [
                {
                    "account": account
                }
            ]
        }]}
    print(data)
    r = requests.post(base_url, json=data, headers=generate_header(data))
    return r.json()


def push_ios(account_list: list, title: str, subtitle: str, content: str):
    environment = 'dev'
    base_url = 'https://api.tpns.tencent.com/v3/push/app'
    data = {
        "audience_type": "account_list",
        "environment": environment,
        "account_list": account_list,
        "message_type": "notify",
        "message": {
            "title": title,
            "content": content,
            "ios": {
                "aps": {
                    "alert": {
                        "subtitle": subtitle
                    },
                    "badge_type": -2

                }
            }
        }
    }
    print("-------------------------")
    print(data)
    r = requests.post(base_url, json=data, headers=generate_header(data))
    return r.json()


if __name__ == '__main__':
    print(generate_cert(str(int(datetime.timestamp(datetime.now()))), dict()))
