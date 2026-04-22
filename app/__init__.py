from flask import Flask, redirect, url_for
from config import Config
from app.extensions import db, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth import bp as auth_bp
    from app.incidents import bp as incidents_bp
    from app.dashboard import bp as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(dashboard_bp)

    @app.route('/')
    def index():
        return redirect(url_for('incidents.list'))

    with app.app_context():
        db.create_all()

    return app
