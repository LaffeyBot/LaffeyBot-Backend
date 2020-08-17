from config import Config
import hmac
import base64
from datetime import datetime
from hashlib import sha256
import requests


def generate_cert(time_stamp: str, json: dict):
    json_string = str(json)
    combined = (time_stamp + str(Config.TPN_ACCESS_ID) + json_string).encode('utf-8')
    token = hmac.new(combined, Config.TPN_SECRET_KEY.encode('utf-8'), digestmod=sha256).hexdigest()
    return base64.b64encode(token.encode('utf8'))


def link_account_with_token(platform: str, account: str, token: str):
    base_url = 'https://api.tpns.tencent.com/v3/device/account/batchoperate'
    data = {
        "operator_type": 1,
        "platform": platform,
        "token_accounts": [{
            "token": token,
            "account_list": [
                {
                    "account": account
                }
            ]
        }]}
    r = requests.post(base_url, json=data)
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

    r = requests.post(base_url, json=data)
    return r.json()


if __name__ == '__main__':
    print(generate_cert(str(int(datetime.timestamp(datetime.now()))), dict()))
