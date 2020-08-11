from flask import jsonify, g, Flask
import config
from flask_cors import CORS
import logging


def create_app(config_file=config.Config):
    app = Flask(__name__)
    logging.basicConfig(filename='flask.log', level=logging.DEBUG)
    app.config.from_object(config_file)
    CORS(app)

    from data.model import db
    db.init_app(app)

    from .auth import auth_blueprint
    from .group import group_blueprint
    from .record import record_blueprint
    from .send_email import email_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(group_blueprint)
    app.register_blueprint(record_blueprint)
    app.register_blueprint(email_blueprint)

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    @app.errorhandler(400)
    def page_not_found(e):
        return jsonify(msg=str(e)), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify(msg=str(e)), 404

    return app

