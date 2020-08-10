from flask import jsonify, g, Flask
import config
from flask_cors import CORS
import logging


def create_app(config_file=config.Config):
    from .auth.auth import auth_blueprint
    from .group.group import group_blueprint
    from .record.record import record_blueprint
    from .send_email.send_email import email_blueprint
    # from app.connect_database import Connect

    app = Flask(__name__)
    logging.basicConfig(filename='flask.log', level=logging.DEBUG)
    app.config.from_object(config_file)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(group_blueprint)
    app.register_blueprint(record_blueprint)
    app.register_blueprint(email_blueprint)
    CORS(app)

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

