from flask import Flask
from routes import api, app

if __name__ == '__main__':
    app.run(debug=True)