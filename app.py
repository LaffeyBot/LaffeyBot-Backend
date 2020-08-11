from server_app import create_app
from config import Config
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from data.model import db

app = create_app(Config)
Migrate(app,db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
if __name__ == '__main__':
    manager.run()
