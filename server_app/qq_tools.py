import requests
from config import Config


async def send_message_to_qq(message: str, id_: int, type_: str, header: dict):
    url = Config.QQ_BOT_URL + '/send_message'
    json = dict(message=message, id=id_, type=type_)
    r = requests.post(url=url, json=json, headers=header)
    requests.map(r)
    print(r.content)
    print(r.text)
