import threading
from flask import Flask, redirect, abort, Response

# Global variable to hold the reference to the Discord bot's module database
global_module_database = {}

app = Flask(__name__)

@app.route('/')
def home():
    """A simple route to confirm the server is running."""
    names = sorted(global_module_database.keys())
    if not names:
        return "Keep-alive server is running. Module database is empty."
        
    html_list = "<ul>" + "".join([f'<li><a href="/{name}">{name}</a></li>' for name in names]) + "</ul>"
    
    return Response(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Module Redirect Server</title>
            <style>
                body {{ font-family: sans-serif; margin: 40px; background-color: #f4f4f9; }}
                h1 {{ color: #333; }}
                code {{ background-color: #eee; padding: 2px 4px; border-radius: 4px; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 6px; background-color: #fff; }}
                a {{ text-decoration: none; color: #007bff; font-weight: bold; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
        <h1>Module Redirect Server Running</h1>
        <p>Access a module by visiting <code>https://[site.com]/[name]</code></p>
        <h2>Available Modules:</h2>
        {html_list}
        </body>
        </html>
        """,
        mimetype='text/html'
    )

@app.route('/<name>')
def redirect_to_url(name):
    """
    Looks up the 'name' in the database and redirects the user to the associated URL.
    """
    url = global_module_database.get(name)
    
    if url:
        return redirect(url, code=302)
    else:
        return abort(404, description=f"Module '{name}' not found in the database.")


def run():
    """Starts the Flask server."""
    app.run(host='0.0.0.0', port=8080)

def keep_alive(db_reference):
    """
    Initializes and starts the Flask server in a separate thread,
    and accepts the database dictionary reference.
    """
    global global_module_database
    global_module_database = db_reference
    
    t = threading.Thread(target=run)
    t.start()
    print("Keep-alive server started on port 8080.")
