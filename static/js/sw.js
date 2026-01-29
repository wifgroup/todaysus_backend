// static/sw.js
// Client-side page caching with TTL by URL type

const CACHE_NAME = "todaysus-pages-v1";

const TTL = {
  article: 5 * 60 * 60 * 1000,   // 5 hours
  category: 5 * 60 * 60 * 1000,  // 5 hours
  home: 15 * 60 * 1000,          // 15 minutes
  static: 3 * 24 * 60 * 60 * 1000 // 3 days
};

function getPageType(url) {
  const path = new URL(url).pathname;

  if (path === "/") return "home";

  if (
    path === "/about" ||
    path === "/privacy-policy" ||
    path === "/terms-of-use" ||
    path === "/editorial-policy" ||
    path === "/corrections" ||
    path === "/ethics" ||
    path === "/contact"
  ) return "static";

  if (path.startsWith("/topics/")) return "category";

  const parts = path.split("/").filter(Boolean);

  // /category/article-slug
  if (parts.length === 2) return "article";

  // /category
  if (parts.length === 1) return "category";

  return null;
}

function withFetchedAt(response) {
  // Add a timestamp header so we can calculate TTL
  const headers = new Headers(response.headers);
  headers.set("x-sw-fetched-at", String(Date.now()));
  return response.blob().then((body) => new Response(body, {
    status: response.status,
    statusText: response.statusText,
    headers
  }));
}

function isFresh(cachedResponse, ttlMs) {
  const fetchedAt = Number(cachedResponse.headers.get("x-sw-fetched-at") || 0);
  if (!fetchedAt) return false;
  return (Date.now() - fetchedAt) < ttlMs;
}

self.addEventListener("install", (event) => {
  // Activate immediately
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Only handle GET
  if (req.method !== "GET") return;

  // Only cache full page navigations (HTML documents)
  if (req.mode !== "navigate") return;

  const type = getPageType(req.url);
  if (!type) return;

  const ttlMs = TTL[type];

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(req);

    // 1) If cached and fresh -> return cached
    if (cached && isFresh(cached, ttlMs)) {
      return cached;
    }

    // 2) Otherwise try network
    try {
      const network = await fetch(req);
      // Only cache successful HTML responses
      const contentType = network.headers.get("content-type") || "";
      if (network.ok && contentType.includes("text/html")) {
        const stamped = await withFetchedAt(network.clone());
        await cache.put(req, stamped.clone());
        return stamped;
      }
      return network;
    } catch (e) {
      // 3) Offline fallback -> return cached even if stale
      if (cached) return cached;
      // last fallback
      return new Response("Offline", { status: 503, headers: { "content-type": "text/plain" } });
    }
  })());
});
