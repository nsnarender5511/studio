import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Import config, extensions, blueprints
from .config import config # Import flattened config object
from .models import db
from .logging_setup import setup_logging
from .api.history_api import history_bp
from .api.jobs_api import jobs_bp
# Import container and settings instance
from .container import Container

# Initialize SQLAlchemy instance, but don't bind it to the app yet
# db = SQLAlchemy() # Already imported from models

# Setup logging as early as possible
setup_logging()

logger = logging.getLogger(__name__)

def create_app():
    # Create and wire the DI container
    container = Container()
    # Provide the already loaded config instance from config.py
    container.config.override(config)
    # List all modules where @inject or Provide[...] will be used within Flask context
    container.wire(modules=[
        __name__, # Current module
        ".api.jobs_api",
        ".api.history_api",
        "src.tasks.documentation_task", # In case API calls task methods directly with DI
        "src.adk.services.memory_service", # Added this
        # Add other API or service modules using injection here
    ])
    logger.info("Dependency Injector container wired for Flask app.")

    # Use flattened config instance path
    app = Flask(__name__, instance_relative_config=True, instance_path=config.INSTANCE_FOLDER_PATH)

    logger.info(f"Initializing Flask app with instance path: {app.instance_path}")
    # Use flattened config DB URI
    logger.info(f"Database DSN from config: {config.SQLALCHEMY_DATABASE_URI}")

    # Load Flask configuration from config object
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=config.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Add other Flask specific configs if needed
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev') # Example secret key
    )

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Attach container to app context if needed elsewhere
    # app.container = container

    # Import and register blueprints
    # Use relative imports for blueprints within the 'app' package
    from .api.jobs_api import jobs_bp
    from .api.history_api import history_bp
    # Import other blueprints...

    app.register_blueprint(jobs_bp)
    app.register_blueprint(history_bp)
    # Register other blueprints...
    logger.info("Flask blueprints registered.")

    # Create database tables if they don't exist
    with app.app_context():
        logger.info("Creating database tables if they don't exist...")
        try:
            # Ensure required directories exist before DB creation / first use
            dirs_to_create = [
                config.INSTANCE_FOLDER_PATH,
                config.CLONE_BASE_DIR,
                config.OUTPUT_BASE_DIR
            ]
            for dir_path in dirs_to_create:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created application directory: {dir_path}")

            # Reflect existing tables to prevent recreation issues if needed
            # db.reflect()
            # Create only tables that don't exist
            db.create_all()
            logger.info("Database tables checked/created.")
        except Exception as e:
            logger.error(f"Error during database table creation: {e}", exc_info=True)

    @app.route('/ping')
    def ping():
        return "pong"

    return app

# Optional: Add main block for direct execution (e.g., using flask run or python -m src.app)
# if __name__ == "__main__":
#    app_instance = create_app()
#    # Use flattened config host/port
#    app_instance.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
