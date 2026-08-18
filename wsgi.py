"""WSGI entry point for Gunicorn.

Gunicorn needs a module-level app object. This file creates and exports it.
"""

from web_app import create_app

app = create_app("development")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
