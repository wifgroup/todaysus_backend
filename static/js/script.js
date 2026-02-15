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
  // Mobile nav toggle (Animated)
  const menuToggle = document.getElementById("menuToggle");
  const mobileNav = document.getElementById("mobileNav");

  if (menuToggle && mobileNav) {
    menuToggle.addEventListener("click", () => {
      const isOpen = mobileNav.classList.contains("open");

      // Toggle animation classes
      menuToggle.classList.toggle("active");
      mobileNav.classList.toggle("open");

      // Accessibility
      menuToggle.setAttribute("aria-expanded", String(!isOpen));
    });

    // Close menu when clicking a link (better UX)
    mobileNav.querySelectorAll("a").forEach(link => {
      link.addEventListener("click", () => {
        menuToggle.classList.remove("active");
        mobileNav.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      });
    });

    // Close menu on outside click (premium UX)
    document.addEventListener("click", (e) => {
      if (
        mobileNav.classList.contains("open") &&
        !mobileNav.contains(e.target) &&
        !menuToggle.contains(e.target)
      ) {
        menuToggle.classList.remove("active");
        mobileNav.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      }
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

// Search overlay toggle
const searchToggle = document.getElementById('searchToggle');
const searchToggleDesktop = document.getElementById('searchToggleDesktop');
const searchOverlay = document.getElementById('searchOverlay');
const searchClose = document.getElementById('searchClose');
const searchInput = searchOverlay?.querySelector('input[type=search]');

function openSearch() {
  searchOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
  setTimeout(() => searchInput?.focus(), 300);
}

function closeSearch() {
  searchOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

if (searchOverlay) {
  // Open from mobile search icon
  searchToggle?.addEventListener('click', openSearch);

  // Open from desktop search icon
  searchToggleDesktop?.addEventListener('click', openSearch);

  // Close search overlay
  searchClose?.addEventListener('click', closeSearch);

  // Close on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && searchOverlay.classList.contains('active')) {
      closeSearch();
    }
  });

  // Close on overlay click (outside form)
  searchOverlay.addEventListener('click', (e) => {
    if (e.target === searchOverlay) {
      closeSearch();
    }
  });
}

/* ===========================
   Back to Top + Scroll Progress
=========================== */
(function () {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  const ring = btn.querySelector('.progress-ring-fill');
  const circumference = 2 * Math.PI * 20; // r=20

  function updateProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? scrollTop / docHeight : 0;

    // Update ring
    const offset = circumference - (progress * circumference);
    ring.style.strokeDashoffset = offset;

    // Show/hide button (show after 300px scroll)
    if (scrollTop > 300) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }

  // Scroll to top on click
  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Listen for scroll
  window.addEventListener('scroll', updateProgress, { passive: true });

  // Initial check
  updateProgress();
})();

/* ===========================
   Share Popup Logic
=========================== */
(function () {
  const popup = document.getElementById('sharePopup');
  if (!popup) return;

  const closeBtn = document.getElementById('sharePopupClose');
  const triggers = document.querySelectorAll('[data-share]');
  const pageUrl = encodeURIComponent(window.location.href);
  const pageTitle = encodeURIComponent(document.title);

  // Set share links
  const whatsapp = document.getElementById('shareWhatsApp');
  const xBtn = document.getElementById('shareX');
  const linkedin = document.getElementById('shareLinkedIn');
  const facebook = document.getElementById('shareFacebook');
  const email = document.getElementById('shareEmail');
  const copyBtn = document.getElementById('shareCopyLink');

  if (whatsapp) whatsapp.href = 'https://wa.me/?text=' + pageTitle + '%20' + pageUrl;
  if (xBtn) xBtn.href = 'https://twitter.com/intent/tweet?text=' + pageTitle + '&url=' + pageUrl;
  if (linkedin) linkedin.href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + pageUrl;
  if (facebook) facebook.href = 'https://www.facebook.com/sharer/sharer.php?u=' + pageUrl;
  if (email) email.href = 'mailto:?subject=' + pageTitle + '&body=' + pageUrl;

  // Open popup
  triggers.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      popup.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  });

  // Close popup
  function closePopup() {
    popup.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (closeBtn) closeBtn.addEventListener('click', closePopup);

  popup.addEventListener('click', function (e) {
    if (e.target === popup) closePopup();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && popup.classList.contains('active')) closePopup();
  });

  // Copy link
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      navigator.clipboard.writeText(window.location.href).then(function () {
        copyBtn.classList.add('copied');
        copyBtn.querySelector('span:last-child').textContent = 'Copied!';
        setTimeout(function () {
          copyBtn.classList.remove('copied');
          copyBtn.querySelector('span:last-child').textContent = 'Copy link';
        }, 2000);
      });
    });
  }
})();

/* ===========================
   Smooth Scroll to #subscribe
=========================== */
(function () {
  document.querySelectorAll('a[href="#subscribe"], .nav-cta[href="#subscribe"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var target = document.getElementById('subscribe');
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Focus the email input
        var input = target.querySelector('input[type="email"]');
        if (input) {
          setTimeout(function () { input.focus(); }, 600);
        }
      }
    });
  });
})();
