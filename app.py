from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, abort, redirect, request
from config import Config
from db.mongo import mongo
from routes.article_routes import article_bp
from routes.pages import pages_bp

from routes.category_routes import category_bp
from routes.topic_routes import topic_bp
from routes.subscriber_routes import subscriber_bp
from routes.contact_api import contact_bp
from routes.sitemap import sitemap_bp
from routes.admin_authors import admin_authors_bp
from routes.admin_routes import admin_bp



app = Flask(__name__)
app.config.from_object(Config)

mongo.init_app(app)

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "0"

    response.headers["Permissions-Policy"] = (
        "geolocation=(), camera=(), microphone=()"
    )

    return response

@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )
    return response

@app.before_request
def force_https():
    if not request.is_secure and not app.debug:
        return redirect(request.url.replace("http://", "https://"), code=301)


@app.before_request
def admin_read_only():
    if request.path.startswith("/api/v1/admin"):
        if request.method != "GET":
            abort(404)

app.register_blueprint(article_bp)

# Page routes (HTML)
app.register_blueprint(pages_bp)

app.register_blueprint(category_bp)

app.register_blueprint(topic_bp)


app.register_blueprint(contact_bp)

app.register_blueprint(subscriber_bp)

app.register_blueprint(sitemap_bp)

app.register_blueprint(admin_authors_bp)

app.register_blueprint(admin_bp)


if __name__ == "__main__":
    app.run(debug=True)
