/* ===========================
FILE: script.js
Animations + UX + Page Cache
=========================== */

// Register Service Worker (client-side cache)
(function () {
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", async () => {
    try {
      await navigator.serviceWorker.register("/sw.js");
      // console.log("SW registered");
    } catch (e) {
      // console.log("SW failed", e);
    }
  });
})();


(function () {

  

  /* ===========================
     EXISTING UX / UI LOGIC
  =========================== */

  // Footer year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Mobile nav toggle
  const menuBtn = document.getElementById("menuBtn");
  const mobileNav = document.getElementById("mobileNav");

  if (menuBtn && mobileNav) {
    menuBtn.addEventListener("click", () => {
      const expanded = menuBtn.getAttribute("aria-expanded") === "true";
      menuBtn.setAttribute("aria-expanded", String(!expanded));
      mobileNav.hidden = expanded;
    });
  }

  // Theme toggle
  const themeToggle = document.getElementById("themeToggle");
  const root = document.documentElement;

  const savedTheme = localStorage.getItem("todaysus_theme");
  if (savedTheme === "dark") root.classList.add("theme-dark");

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      root.classList.toggle("theme-dark");
      const isDark = root.classList.contains("theme-dark");
      localStorage.setItem("todaysus_theme", isDark ? "dark" : "light");
    });
  }

  // Reveal on scroll
  const revealEls = document.querySelectorAll(".reveal");
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!prefersReduced && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  // Subscribe form
  const form = document.getElementById("subscribeForm");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = form.querySelector("input[name='email']").value;
      const note = form.querySelector(".form-note");

      note.textContent = "Submitting...";
      note.style.color = "#555";

      try {
        const res = await fetch("/api/v1/subscribe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, source: "homepage" })
        });

        const data = await res.json();
        note.textContent = data.message || "Done!";
        note.style.color = "green";
        form.reset();
      } catch {
        note.textContent = "Something went wrong. Try again.";
        note.style.color = "red";
      }
    });
  }

})();

/* ===========================
   Auto-update U.S. date
=========================== */
(function updateUSDate() {
  const timeEl = document.getElementById("currentDate");
  if (!timeEl) return;

  const now = new Date();
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "America/New_York"
  };

  timeEl.textContent = new Intl.DateTimeFormat("en-US", options).format(now);
})();
