# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'main.login'  # Note the 'main.' prefix

    # Register blueprints
    from .admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        from . import models
        db.create_all()

        # Create default admin if not exists
        from .models import User
        admin = User.query.filter_by(email='admin@gmail.com').first()
        if not admin:
            admin = User(
                username='admin',
                full_name='Administrator',
                email='admin@gmail.com',
                role='Admin'
            )
            admin.set_password('admin')  # Set default password
            db.session.add(admin)
            db.session.commit()

        # Load sample users from JSON file
        import json
        try:
            with open('sample_users.json') as f:
                users = json.load(f)
                for user_data in users:
                    existing_user = User.query.filter_by(email=user_data['email']).first()
                    if not existing_user:
                        user = User(
                            student_number=user_data['student_number'],
                            username=user_data['username'],
                            full_name=user_data['full_name'],
                            email=user_data['email'],
                            role='User'
                        )
                        user.set_password(user_data['password'])
                        db.session.add(user)
                db.session.commit()
        except FileNotFoundError:
            print("sample_users.json file not found. Please ensure it exists in the project root directory.")

    return app
