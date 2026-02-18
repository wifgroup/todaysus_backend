from flask import Blueprint, jsonify, render_template, abort, request
from datetime import datetime
from dateutil import parser
from db.mongo import mongo
from models.page_model import create_page
from utils.helper import normalize_articles, render_static_page
from werkzeug.exceptions import HTTPException
from flask import send_from_directory

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/sw.js")
def service_worker():
    return send_from_directory(
        directory="static",
        path="js/sw.js",
        mimetype="application/javascript"
    )

@pages_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template(
        "404.html",
        current_year=datetime.utcnow().year
    ), 404


@pages_bp.app_errorhandler(Exception)
def handle_all_errors(e):
    # If it's a known HTTP error (404, 403, etc.), let Flask handle it
    if isinstance(e, HTTPException):
        return e

    # Otherwise treat it as 500
    return render_template(
        "500.html",
        current_year=datetime.utcnow().year
    ), 500

 
@pages_bp.route("/<category_slug>/<article_slug>")
def article_page(category_slug, article_slug):

    # ---------------- MAIN ARTICLE ---------------- #
    article = mongo.db.articles.find_one_and_update(
        {
            "slug": article_slug,
            "category.slug": category_slug,
            "status": "published",
            "is_deleted": False
        },
        {
            "$inc": {"view_count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )

    if not article:
        abort(404)

    # Convert string dates → datetime
    if isinstance(article.get("published_at"), str):
        article["published_at"] = parser.parse(article["published_at"])

    if isinstance(article.get("updated_at"), str):
        article["updated_at"] = parser.parse(article["updated_at"])

    article["_id"] = str(article["_id"])

    canonical_url = f"https://todaysus.com/{category_slug}/{article_slug}"

    # ---------------- MOST RELEVANT ---------------- #
    topic_slugs = [t["slug"] for t in article.get("topics", [])]

    relevant_articles = list(
        mongo.db.articles.find(
            {
                "_id": {"$ne": article["_id"]},
                "status": "published",
                "is_deleted": False,
                "category.slug": category_slug,
                "topics.slug": {"$in": topic_slugs}
            }
        )
        .sort([
            ("view_count", -1),
            ("published_at", -1)
        ])
        .limit(5)
    )

    # ---------------- MOST RECENT ---------------- #
    recent_articles = list(
        mongo.db.articles.find(
            {
                "status": "published",
                "is_deleted": False
            }
        )
        .sort("published_at", -1)
        .limit(5)
    )

    # Convert IDs
    for a in relevant_articles + recent_articles:
        a["_id"] = str(a["_id"])

    # ---------------- MORE COVERAGE ---------------- #
    more_coverage = list(
        mongo.db.articles.find(
            {
                "_id": {"$ne": article["_id"]},
                "status": "published",
                "is_deleted": False,
                "category.slug": category_slug
            }
        )
        .sort("published_at", -1)
        .limit(6)
    )

    for m in more_coverage:
        m["_id"] = str(m["_id"])

    # ---------------- AUTHOR ---------------- #
    author = None

    if article.get("author") and article["author"].get("slug"):
        author = mongo.db.authors.find_one(
            {
                "slug": article["author"]["slug"],
                "is_active": True
            }
        )

        if author:
            author["_id"] = str(author["_id"])

    
    # ---------------- ADS FLAG ---------------- #
    show_ads = False  # 🔴 Enable later when ads are ready

    # ---------------- RENDER PAGE ---------------- #
    return render_template(
        "article.html",
        article=article,
        author=author,
        canonical_url=canonical_url,
        current_year=datetime.utcnow().year,

        # Sidebar
        relevant_articles=relevant_articles,
        recent_articles=recent_articles,

        # More coverage
        more_coverage=more_coverage,

        # Ads
        show_ads=show_ads
    )


@pages_bp.route("/<category_slug>")
def category_page(category_slug):
    page = int(request.args.get("page", 1))
    limit = 10
    skip = (page - 1) * limit

    # ---------------- CATEGORY ---------------- #
    category = mongo.db.categories.find_one(
        {"slug": category_slug, "is_active": True}
    )
    if not category:
        abort(404)

    # ---------------- LEAD STORY ---------------- #
    lead_article = mongo.db.articles.find_one(
        {
            "status": "published",
            "is_deleted": False,
            "category.slug": category_slug,
            "is_featured": True
        },
        sort=[("published_at", -1)]
    )

    # ---------------- STORY STREAM ---------------- #
    query = {
        "status": "published",
        "is_deleted": False,
        "category.slug": category_slug
    }

    most_read_query = query.copy()

    # Exclude lead story from stream to prevent duplication
    if lead_article:
        query["_id"] = {"$ne": lead_article["_id"]}
    # {
    #     "status": "published",
    #     "is_deleted": False,
    #     # "category.slug": category_slug
    # }

    stream_articles = list(
        mongo.db.articles
        .find(query)
        .sort("published_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total_articles = mongo.db.articles.count_documents(query)
    has_more = total_articles > (page * limit)

    # ---------------- MOST READ ---------------- #
    most_read = list(
        mongo.db.articles.find(most_read_query)
        .sort("view_count", -1)
        .limit(5)
    )

    # ---------------- TOPICS ---------------- #
    topic_map = {}
    for a in stream_articles:
        for t in a.get("topics", []):
            topic_map[t["slug"]] = t["name"]

    topics = [{"slug": k, "name": v} for k, v in topic_map.items()]

    # ---------------- DATE FIX ---------------- #
    def fix_dates(items):
        for a in items:
            # published_at
            if isinstance(a.get("published_at"), str):
                a["published_at"] = parser.parse(a["published_at"])

            # created_at (IMPORTANT)
            if isinstance(a.get("created_at"), str):
                a["created_at"] = parser.parse(a["created_at"])

            # fallback (CRITICAL)
            if not a.get("published_at"):
                a["published_at"] = a.get("created_at")

            a["_id"] = str(a["_id"])


    fix_dates(stream_articles)
    fix_dates(most_read)
    if lead_article:
        fix_dates([lead_article])

    return render_template(
        "category.html",
        category=category,
        lead_article=lead_article,
        stream_articles=stream_articles,
        most_read=most_read,
        topics=topics,
        current_year=datetime.utcnow().year,
        page=page,
        has_more=has_more
    )

@pages_bp.route("/topics/<topic_slug>")
def topic_page(topic_slug):
    page = int(request.args.get("page", 1))
    limit = 10
    skip = (page - 1) * limit

    # ---------------- TOPIC ---------------- #
    topic = mongo.db.topics.find_one(
        {"slug": topic_slug, "is_active": True}
    )

    if not topic:
        abort(404)

    # ---------------- QUERY ---------------- #
    query = {
        "status": "published",
        "is_deleted": False,
        "topics.slug": topic_slug
    }

    # ---------------- LEAD STORY ---------------- #
    lead_article = mongo.db.articles.find_one(
        query,
        sort=[("published_at", -1)]
    )

    # ---------------- STORY STREAM ---------------- #
    stream_articles = list(
        mongo.db.articles
        .find(query)
        .sort("published_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total_articles = mongo.db.articles.count_documents(query)
    has_more = total_articles > (page * limit)

    # ---------------- MOST READ ---------------- #
    most_read = list(
        mongo.db.articles
        .find(query)
        .sort("view_count", -1)
        .limit(5)
    )

    # ---------------- DATE FIX ---------------- #
    def fix_dates(items):
        for a in items:
            # published_at
            if isinstance(a.get("published_at"), str):
                a["published_at"] = parser.parse(a["published_at"])

            # created_at (CRITICAL FIX)
            if isinstance(a.get("created_at"), str):
                a["created_at"] = parser.parse(a["created_at"])

            # fallback safety
            if not a.get("published_at"):
                a["published_at"] = a.get("created_at")

            a["_id"] = str(a["_id"])


    fix_dates(stream_articles)
    fix_dates(most_read)
    if lead_article:
        fix_dates([lead_article])

    return render_template(
        "topic.html",
        topic=topic,
        lead_article=lead_article,
        stream_articles=stream_articles,
        most_read=most_read,
        page=page,
        has_more=has_more,
        current_year=datetime.utcnow().year
    )


@pages_bp.route("/about")
def about_page():

    page = mongo.db.pages.find_one(
        {"slug": "about", "is_active": True}
    )

    if not page:
        abort(404)

    # -------- COVERAGE (dynamic like home) -------- #
    categories = list(
        mongo.db.categories.find(
            {"is_active": True}
        ).sort("order", 1)
    )

    for c in categories:
        c["_id"] = str(c["_id"])

    return render_template(
        "about.html",
        page=page,
        categories=categories,
        current_year=datetime.utcnow().year
    )

@pages_bp.route("/api/v1/admin/pages", methods=["POST"])
def create_page_api():
    data = request.json
    page = create_page(data)
    mongo.db.pages.insert_one(page)
    return jsonify({"message": "Page created"}), 201


@pages_bp.route("/contact")
def contact_page():
    return render_template(
        "contact.html",
        seo_title="Contact Today’s US",
        seo_description="Contact the Today’s US newsroom for editorial inquiries, corrections, or general questions.",
        canonical_url="https://todaysus.com/contact",
        current_year=datetime.utcnow().year
    )


@pages_bp.route("/editorial-policy")
def editorial_policy_page():
    return render_static_page("editorial-policy", "editorial-policy.html")


@pages_bp.route("/corrections")
def corrections_page():
    return render_static_page("corrections", "corrections.html")


@pages_bp.route("/ethics")
def ethics_page():
    return render_static_page("ethics", "ethics.html")


# @pages_bp.route("/privacy-policy")
# def privacy_policy_page():
#     return render_static_page("privacy-policy", "page.html")


# @pages_bp.route("/terms-of-use")
# def terms_page():
#     return render_static_page("terms-of-use", "page.html")
@pages_bp.route("/privacy-policy")
def privacy_policy_page():
    page = mongo.db.pages.find_one(
        {"slug": "privacy-policy", "is_active": True}
    )
    if not page:
        abort(404)

    return render_template(
        "legal_page.html",
        page=page,
        current_year=datetime.utcnow().year
    )


@pages_bp.route("/terms-of-use")
def terms_of_use_page():
    page = mongo.db.pages.find_one(
        {"slug": "terms-of-use", "is_active": True}
    )
    if not page:
        abort(404)

    return render_template(
        "legal_page.html",
        page=page,
        current_year=datetime.utcnow().year
    )

@pages_bp.route("/authors/<slug>")
def author_page(slug):

    author = mongo.db.authors.find_one({
        "slug": slug,
        "is_active": True,
        "is_public": True
    })

    if not author:
        abort(404)

    author["_id"] = str(author["_id"])

    # Latest articles by this author
    articles = list(
        mongo.db.articles.find(
            {
                "status": "published",
                "is_deleted": False,
                "author.slug": slug
            }
        )
        .sort("published_at", -1)
        .limit(10)
    )

    normalize_articles(articles)

    return render_template(
        "author.html",
        author=author,
        articles=articles,
        current_year=datetime.utcnow().year
    )


@pages_bp.route("/")
def home_page():

    base_query = {
        "status": "published",
        "is_deleted": False
    }

    # ---------------- TODAY'S BRIEFING ---------------- #
    today_briefing = list(
        mongo.db.articles.find(base_query)
        .sort("published_at", -1)
        .limit(3)
    )
    normalize_articles(today_briefing)

    # ---------------- PRIMARY FEATURE ---------------- #
    primary_feature = mongo.db.articles.find_one(
        {**base_query, "is_featured": True},
        sort=[("published_at", -1)]
    )
    if primary_feature:
        normalize_articles([primary_feature])

    # ---------------- SECONDARY FEATURES ---------------- #
    secondary_features = list(
        mongo.db.articles.find(
            {**base_query, "is_featured": False}
        )
        .sort("published_at", -1)
        .limit(2)
    )
    normalize_articles(secondary_features)

    # ---------------- LATEST BY CATEGORY ---------------- #
    def latest_by_category(slug):
        items = list(
            mongo.db.articles.find(
                {**base_query, "category.slug": slug}
            )
            .sort("published_at", -1)
            .limit(3)
        )
        normalize_articles(items)
        return items

    latest_politics = latest_by_category("politics")
    latest_business = latest_by_category("business")
    # latest_technology = latest_by_category("technology")
    latest_news = latest_by_category("news")

    # ---------------- MOST READ ---------------- #
    most_read = list(
        mongo.db.articles.find(base_query)
        .sort("view_count", -1)
        .limit(5)
    )
    normalize_articles(most_read)

    # ---------------- EDITOR'S PICK ---------------- #
    editors_pick = mongo.db.articles.find_one(
        {**base_query, "is_featured": True},
        sort=[("view_count", -1)]
    )
    if editors_pick:
        normalize_articles([editors_pick])

    # ---------------- EDITORIAL GRID ---------------- #
    big_story = mongo.db.articles.find_one(
        base_query,
        sort=[("updated_at", -1)]
    )
    if big_story:
        normalize_articles([big_story])

    editors_focus = [
        "Why context matters more than speed in political coverage",
        "How we distinguish analysis from opinion",
        "What readers should watch as policies take shape"
    ]

    watching = [
        "Federal policy developments",
        "Economic indicators",
        "Technology regulation"
    ]

    explainers = [
        "How U.S. elections work",
        "What inflation data actually shows",
        "How AI policy is formed"
    ]

    # ---------------- COVERAGE AREAS ---------------- #
    coverage_areas = list(
        mongo.db.categories.find(
            {"is_active": True}
        ).sort("order", 1)
    )

    for c in coverage_areas:
        c["_id"] = str(c["_id"])

    # ---------------- TRUST / STANDARDS ---------------- #
    trust_points = [
        "Verification first",
        "Transparent corrections",
        "Clear labeling (News / Analysis / Opinion)"
    ]

    
    latest_article = mongo.db.articles.find_one(
        {"status": "published"},
        sort=[("updated_at", -1)]
    )


    # ---------------- RENDER ---------------- #
    return render_template(
        "index.html",

        # Hero / Briefing
        today_briefing=today_briefing,

        # Featured
        primary_feature=primary_feature,
        secondary_features=secondary_features,

        # Latest by category
        latest_politics=latest_politics,
        latest_business=latest_business,
        latest_news=latest_news,

        # Most read
        most_read=most_read,
        editors_pick=editors_pick,

        # Editorial grid
        big_story=big_story,
        editors_focus=editors_focus,
        watching=watching,
        explainers=explainers,

        # Coverage + trust
        coverage_areas=coverage_areas,
        trust_points=trust_points,

        latest_updated_at = latest_article["updated_at"],
        current_year=datetime.utcnow().year
    )



@pages_bp.route("/search")
def search_page():

    query = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    limit = 10
    skip = (page - 1) * limit

    results = []
    total = 0

    if query:
        mongo_query = {
            "$text": {"$search": query},
            "status": "published",
            "is_deleted": False
        }

        cursor = (
            mongo.db.articles
            .find(mongo_query, {"score": {"$meta": "textScore"}})
            .sort([("score", {"$meta": "textScore"})])
            .skip(skip)
            .limit(limit)
        )

        results = list(cursor)
        total = mongo.db.articles.count_documents(mongo_query)

        normalize_articles(results)

    has_more = total > (page * limit)

    return render_template(
        "search.html",
        query=query,
        results=results,
        total=total,
        page=page,
        has_more=has_more,
        current_year=datetime.utcnow().year,
        canonical_url=f"https://todaysus.com/search?q={query}"
    )
