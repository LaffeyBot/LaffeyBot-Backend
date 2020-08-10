from server_app import create_app

app = create_app()

from data.model import *
db.create_all()
