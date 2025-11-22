import threading
from flask import Flask, redirect, abort, Response # Imported Response, redirect, abort

# Global variable to hold the reference to the Discord bot's module database
global_module_database = {}

app = Flask(__name__)

@app.route('/')
def home():
    """A simple route to confirm the server is running."""
    # List all available names for easy reference
    names = sorted(global_module_database.keys())
    if not names:
        return "Keep-alive server is running. Module database is empty."
        
    html_list = "<ul>" + "".join([f'<li><a href="/{name}">{name}</a></li>' for name in names]) + "</ul>"
    
    return Response(
        f"""
        <h1>Module Redirect Server Running</h1>
        <p>Access a module by visiting <code>https://[site.com]/[name]</code></p>
        <h2>Available Modules:</h2>
        {html_list}
        """,
        mimetype='text/html'
    )

@app.route('/<name>')
def redirect_to_url(name):
    """
    Looks up the 'name' in the database and redirects the user to the associated URL.
    Example: Accessing /python redirects to the stored Python link.
    """
    url = global_module_database.get(name)
    
    if url:
        # Redirects the user's browser to the stored URL
        return redirect(url, code=302)
    else:
        # Returns a 404 error if the module is not found
        return abort(404, description=f"Module '{name}' not found in the database.")


def run():
    """Starts the Flask server."""
    # Run on 0.0.0.0 and 8080 for broad compatibility
    app.run(host='0.0.0.0', port=8080)

def keep_alive(db_reference):
    """Initializes and starts the Flask server in a separate thread."""
    global global_module_database
    # Store the reference to the dictionary
    global_module_database = db_reference
    
    t = threading.Thread(target=run)
    t.start()
    print("Keep-alive server started on port 8080.")
