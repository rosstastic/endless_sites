/* endless_sites — Business Template JS
   No dependencies. ES2020. */

(function () {
  'use strict';

  // ── Mobile nav ──────────────────────────────────────────
  const toggle = document.getElementById('nav-toggle');
  const links  = document.getElementById('nav-links');
  const nav    = document.querySelector('.nav');

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open);
    });

    // Close nav when a link is clicked
    links.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        links.classList.remove('open');
        toggle.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ── Nav scroll shadow ────────────────────────────────────
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ── Highlight today's row in hours table ─────────────────
  const DAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
  const todayName = DAYS[new Date().getDay()];
  document.querySelectorAll('.hours__table tr').forEach(row => {
    const cell = row.querySelector('td');
    if (cell && cell.textContent.trim().toLowerCase() === todayName) {
      row.classList.add('today');
    }
  });

  // ── Open Now badge ───────────────────────────────────────
  const badge = document.getElementById('open-now-badge');
  if (badge && typeof HOURS_DATA !== 'undefined') {
    try {
      const now  = new Date();
      const day  = DAYS[now.getDay()];
      const raw  = HOURS_DATA[day];

      if (raw && raw.toLowerCase() !== 'closed') {
        // Parse "11:00 AM – 9:00 PM" style strings
        const parseTime = str => {
          const m = str.trim().match(/(\d+):(\d+)\s*(AM|PM)/i);
          if (!m) return null;
          let h = parseInt(m[1], 10);
          const min = parseInt(m[2], 10);
          const ampm = m[3].toUpperCase();
          if (ampm === 'PM' && h !== 12) h += 12;
          if (ampm === 'AM' && h === 12) h = 0;
          return h * 60 + min;
        };

        const parts  = raw.split(/[–—-]/);
        const open   = parseTime(parts[0]);
        const close  = parseTime(parts[1]);
        const nowMin = now.getHours() * 60 + now.getMinutes();

        if (open !== null && close !== null) {
          const isOpen = nowMin >= open && nowMin < close;
          badge.textContent = isOpen ? '● Open Now' : '● Closed Now';
          badge.classList.toggle('closed', !isOpen);
          badge.removeAttribute('hidden');
        }
      } else if (raw && raw.toLowerCase() === 'closed') {
        badge.textContent = '● Closed Today';
        badge.classList.add('closed');
        badge.removeAttribute('hidden');
      }
    } catch (_) { /* silently ignore parse errors */ }
  }

  // ── Lazy image loading ───────────────────────────────────
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          const img = e.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
          obs.unobserve(img);
        }
      });
    }, { rootMargin: '200px' });

    document.querySelectorAll('img[data-src]').forEach(img => io.observe(img));
  } else {
    // Fallback: load immediately
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
    });
  }

  // ── Smooth scroll offset for fixed nav ───────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const offset = 72; // nav height
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

})();
