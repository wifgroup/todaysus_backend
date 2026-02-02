from flask import Blueprint, Response, send_from_directory
from datetime import datetime, timedelta
from db.mongo import mongo
from dateutil import parser

from dateutil import parser

def normalize_datetime(value):
    """
    Returns a datetime object safely
    """
    if isinstance(value, str):
        return parser.parse(value)
    if isinstance(value, datetime):
        return value
    return None


def article_pub_datetime(article):
    """
    Google News–safe publication datetime
    """
    return (
        normalize_datetime(article.get("published_at"))
        or normalize_datetime(article.get("updated_at"))
        or normalize_datetime(article.get("created_at"))
        or datetime.utcnow()
    )


def safe_date(value):
    if isinstance(value, str):
        value = parser.parse(value)
    if isinstance(value, datetime):
        return value.date()
    return datetime.utcnow().date()


sitemap_bp = Blueprint("sitemap", __name__)

BASE_URL = "https://www.todaysus.com"
static_pages = [
    "about",
    "contact",
    "editorial-policy",
    "ethics",
    "corrections",
    "privacy-policy",
    "terms-of-use"
]

@sitemap_bp.route("/sitemap.xml", methods=["GET"])
def sitemap():
    urls = []
    # BASE_URL = "https://www.todaysus.com"

    # ---------- Home ----------
    urls.append({
        "loc": f"{BASE_URL}/",
        "lastmod": datetime.utcnow().date(),
        "changefreq": "daily",
        "priority": "1.0"
    })
    
    # ---------- Static Pages ----------
    for page in static_pages:
        urls.append({
            "loc": f"{BASE_URL}/{page}",
            "lastmod": datetime.utcnow().date(),
            "changefreq": "monthly",
            "priority": "0.5"
        })
        
    # ---------- Static Pages ----------
    authors = mongo.db.authors.find(
        {
            
            "is_active": True
        }
    )
    
    for author in authors:
        urls.append({
            "loc": f"{BASE_URL}/authors/{author['slug']}",
            "lastmod": (
                author.get("updated_at")
                or author.get("created_at")
                or datetime.utcnow()
            ).date(),
            "changefreq": "monthly",
            "priority": "0.6"
        })

    # ---------- Categories ----------
    category_slugs = set()

    articles = mongo.db.articles.find(
        {
            "status": "published",
            "is_deleted": False
        }
    )

    articles_list = list(articles)

    for article in articles_list:
        category = article.get("category", {})
        slug = category.get("slug")

        if slug:
            category_slugs.add(slug)

    for slug in category_slugs:
        urls.append({
            "loc": f"{BASE_URL}/{slug}",
            "lastmod": datetime.utcnow().date(),
            "changefreq": "daily",
            "priority": "0.8"
        })

        # ---------- TRENDING TOPICS ----------

    trending_topics = mongo.db.articles.aggregate([
        {
            "$match": {
                "status": "published",
                "is_deleted": False,
                "topics": {"$exists": True, "$ne": []}
            }
        },
        {"$unwind": "$topics"},
        {
            "$group": {
                "_id": "$topics.slug",
                "article_count": {"$sum": 1},
                "last_published": {"$max": "$published_at"}
            }
        },
        {"$sort": {"article_count": -1}},   # most articles first
        {"$limit": 25}                       # ONLY TOP 25 TOPICS
    ])

    for topic in trending_topics:
        if not topic["_id"]:
            continue

        urls.append({
            "loc": f"{BASE_URL}/topics/{topic['_id']}",
            "lastmod": 
                safe_date(topic.get("last_published"))
                ,
            "changefreq": "daily",
            "priority": "0.7"
        })

    
    # ---------- Articles ----------
    for article in articles_list:
        slug = article.get("slug")
        category = article.get("category", {}).get("slug")

        if not slug or not category:
            continue

        urls.append({
            "loc": f"{BASE_URL}/{category}/{slug}",
            "lastmod": (
                article.get("updated_at")
                or article.get("published_at")
                or datetime.utcnow()
            ).date(),
            "changefreq": "weekly",
            "priority": "0.8"
        })

    # ---------- Build XML ----------
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        xml.append("<url>")
        xml.append(f"<loc>{url['loc']}</loc>")
        xml.append(f"<lastmod>{url['lastmod']}</lastmod>")
        xml.append(f"<changefreq>{url['changefreq']}</changefreq>")
        xml.append(f"<priority>{url['priority']}</priority>")
        xml.append("</url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")



@sitemap_bp.route("/news-sitemap.xml", methods=["GET"])
def news_sitemap():

    articles = mongo.db.articles.find(
        {
            "status": "published",
            "is_deleted": False,
            "updated_at": {
                "$gte": datetime.utcnow() - timedelta(days=7)
            }
        }
    ).sort("updated_at", -1).limit(100)

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
    )

    for article in articles:
        category = article.get("category", {}).get("slug")
        slug = article.get("slug")

        if not category or not slug:
            continue

        pub_date = article_pub_datetime(article)

        xml.append("<url>")
        xml.append(f"<loc>{BASE_URL}/{category}/{slug}</loc>")
        xml.append("<news:news>")
        xml.append("<news:publication>")
        xml.append("<news:name>Todays US</news:name>")
        xml.append("<news:language>en</news:language>")
        xml.append("</news:publication>")
        xml.append(
            f"<news:publication_date>{pub_date.isoformat()}</news:publication_date>"
        )
        xml.append(f"<news:title>{article['title']}</news:title>")
        xml.append("</news:news>")
        xml.append("</url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")

@sitemap_bp.route("/robots.txt")
def robots_txt():
    return send_from_directory("static", "robots.txt", mimetype="text/plain")
