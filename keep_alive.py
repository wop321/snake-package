import threading
from flask import Flask, redirect, abort, Response

# Global variable to hold the reference to the Discord bot's live module database.
# This dictionary is updated by the main bot file after loading from Firestore.
global_module_database = {}

app = Flask(__name__)

@app.route('/')
def home():
    """
    The main route. It generates an HTML page listing all available shortcuts
    from the in-memory database dictionary (synced from Firestore).
    This serves as the public, viewable database.
    """
    names = sorted(global_module_database.keys())
    
    if not names:
        return Response(
            """
            <!DOCTYPE html>
            <html><head><title>Project Redirect Server</title></head>
            <body><h1>No Projects Found</h1><p>The server is running, but the database is empty. Add projects using the Discord bot's /add command!</p></body>
            </html>
            """,
            mimetype='text/html'
        )

    # Generate an HTML list of all available shortcuts
    html_list = "<ul>" + "".join([
        f'<li><a href="/{name}" class="font-mono bg-blue-100 text-blue-800 p-2 rounded-lg hover:bg-blue-200">{name}</a></li>' 
        for name in names
    ]) + "</ul>"
    
    # Use Tailwind CSS classes for a simple, mobile-friendly design
    return Response(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Project Redirect Server</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ font-family: 'Inter', sans-serif; }}
            </style>
        </head>
        <body class="bg-gray-50 min-h-screen flex flex-col items-center p-4">
            <div class="max-w-xl w-full bg-white shadow-xl rounded-2xl p-6 md:p-10 mt-10">
                <h1 class="text-3xl font-extrabold text-gray-900 mb-2">Project Shortcut Database</h1>
                <p class="text-gray-600 mb-6">
                    This is a live, persistent list of all projects saved via the Discord bot. 
                    Click a shortcut name to get the direct <code>pip install</code> command.
                </p>
                
                <h2 class="text-xl font-semibold text-gray-800 mb-4 border-b pb-2">Available Shortcuts ({len(names)})</h2>
                
                <div class="space-y-3">
                    {html_list}
                </div>

                <div class="mt-8 pt-4 border-t text-sm text-gray-500">
                    <p>To use, type the following into your terminal, replacing [site.com] with this server's URL:</p>
                    <p class="font-mono bg-gray-100 p-2 rounded-lg mt-2 text-gray-700">
                        pip install <a href="#" class="underline">https://[site.com]/[shortcut-name]</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """,
        mimetype='text/html'
    )

@app.route('/<name>')
def redirect_to_url(name):
    """
    Looks up the 'name' (shortcut) in the database and redirects the user
    to the associated Git install command URL.
    """
    url = global_module_database.get(name)
    
    if url:
        # Flask redirects to the VALUE of the URL, which is the full 
        # "pip install git+https://..." string.
        # This allows the user's terminal to process the pip install command correctly.
        return redirect(url, code=302)
    else:
        return abort(404, description=f"Module '{name}' not found in the persistent database.")


def run():
    """Starts the Flask server."""
    # Ensure debug is off for deployment
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), debug=False) 

def keep_alive(db_reference):
    """
    Initializes and starts the Flask server in a separate thread,
    and accepts the database dictionary reference.
    """
    global global_module_database
    global_module_database = db_reference
    
    # We must import os here for os.environ.get('PORT')
    import os
    
    t = threading.Thread(target=run)
    t.start()
    print("Keep-alive server started.")
