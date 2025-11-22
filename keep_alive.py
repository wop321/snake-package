import threading
from flask import Flask
f = open("database.txt")
app = Flask(__name__)

@app.route('/')
def home():
    """A simple route to keep the service alive."""
    return f.read()

def run():
    """Starts the Flask server."""
    # Run on 0.0.0.0 and 8080 for broad compatibility
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Initializes and starts the Flask server in a separate thread."""
    t = threading.Thread(target=run)
    t.start()
    print("Keep-alive server started on port 8080.")

if __name__ == '__main__':
    keep_alive()
