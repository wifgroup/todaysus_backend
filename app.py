from flask import Flask
from config import Config
from db.mongo import mongo
from routes.article_routes import article_bp
from routes.pages import pages_bp

from routes.category_routes import category_bp
from routes.topic_routes import topic_bp
from routes.subscriber_routes import subscriber_bp


app = Flask(__name__)
app.config.from_object(Config)

mongo.init_app(app)
app.register_blueprint(article_bp)

# Page routes (HTML)
app.register_blueprint(pages_bp)

app.register_blueprint(category_bp)

app.register_blueprint(topic_bp)



app.register_blueprint(subscriber_bp)


if __name__ == "__main__":
    app.run(debug=True)
