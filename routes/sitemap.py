from flask import Blueprint, Response, send_from_directory
from datetime import datetime, timedelta
from db.mongo import mongo

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
    
    for page in static_pages:
        urls.append({
            "loc": f"{BASE_URL}/{page}",
            "lastmod": datetime.utcnow().date(),
            "changefreq": "monthly",
            "priority": "0.5"
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
            "priority": "0.7"
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
    # BASE_URL = "https://www.todaysus.com"

    articles = mongo.db.articles.find(
        {
            "status": "published",
            "is_deleted": False,
            "published_at": {
                "$gte": datetime.utcnow() - timedelta(days=7)
            }
        }
    ).sort("published_at", -1).limit(100)

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
               'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">')

    for article in articles:
        category = article.get("category", {}).get("slug")
        slug = article.get("slug")

        if not category or not slug:
            continue

        xml.append("<url>")
        xml.append(f"<loc>{BASE_URL}/{category}/{slug}</loc>")
        xml.append("<news:news>")
        xml.append("<news:publication>")
        xml.append("<news:name>Todays US</news:name>")
        xml.append("<news:language>en</news:language>")
        xml.append("</news:publication>")
        xml.append(f"<news:publication_date>{article['published_at'].isoformat()}</news:publication_date>")
        xml.append(f"<news:title>{article['title']}</news:title>")
        xml.append("</news:news>")
        xml.append("</url>")

    xml.append("</urlset>")

    return Response("\n".join(xml), mimetype="application/xml")

@sitemap_bp.route("/robots.txt")
def robots_txt():
    return send_from_directory("static", "robots.txt", mimetype="text/plain")
