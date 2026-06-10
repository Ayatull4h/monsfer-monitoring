from app import app
from config.config_loader import config

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)
