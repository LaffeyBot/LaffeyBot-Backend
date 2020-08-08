from flask import jsonify, g, Flask
import config
from flask_cors import CORS
import logging

import atexit


def create_app(config_file=config.Config):
    from app.view.view import view
    from app.upload.upload import upload
    from app.auth.auth import auth_blueprint
    from app.ex_extension import extension
    # from app.connect_database import Connect

    app = Flask(__name__)
    logging.basicConfig(filename='flask.log', level=logging.DEBUG)
    app.config.from_object(config_file)
    app.register_blueprint(view)
    app.register_blueprint(upload)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(extension)
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

