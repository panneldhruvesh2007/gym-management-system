'use strict';

// ── Safe storage wrapper ──────────────────────────────────────────────────
const store = {
  get(key, fallback = null) {
    try { const v = localStorage.getItem(key); return v !== null ? JSON.parse(v) : fallback; }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
  },
  remove(key) {
    try { localStorage.removeItem(key); } catch {}
  }
};

// ── Cookie Banner ─────────────────────────────────────────────────────────
(function initCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  if (!banner) return;
  if (!store.get('cookie_consent')) {
    setTimeout(() => banner.classList.add('show'), 800);
  }
})();

function acceptCookies() {
  store.set('cookie_consent', 'accepted');
  hideCookieBanner();
}
function declineCookies() {
  store.set('cookie_consent', 'declined');
  hideCookieBanner();
}
function hideCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  if (banner) { banner.classList.remove('show'); }
}

// ── Theme ─────────────────────────────────────────────────────────────────
(function initTheme() {
  const saved = store.get('theme', 'dark');
  document.body.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const icon = document.getElementById('theme-icon');
  if (!icon) return;
  icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const current = document.body.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', next);
    store.set('theme', next);
    updateThemeIcon(next);
  });
}

// ── Navbar scroll ─────────────────────────────────────────────────────────
const navbar = document.getElementById('navbar');
let lastScroll = 0;

function onScroll() {
  const y = window.scrollY;
  if (navbar) {
    navbar.classList.toggle('scrolled', y > 50);
  }
  // Back to top
  const btt = document.getElementById('back-to-top');
  if (btt) btt.classList.toggle('show', y > 400);
  // Active nav link
  updateActiveNav();
  lastScroll = y;
}

window.addEventListener('scroll', onScroll, { passive: true });

// ── Mobile menu ───────────────────────────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('nav-links');

if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    hamburger.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });

  // Close on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!navbar.contains(e.target) && navLinks.classList.contains('open')) {
      navLinks.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
}

// ── Active nav link on scroll ─────────────────────────────────────────────
function updateActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const links    = document.querySelectorAll('.nav-link');
  let current = '';
  sections.forEach(sec => {
    if (window.scrollY >= sec.offsetTop - 120) current = sec.id;
  });
  links.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === '#' + current);
  });
}

// ── Back to top ───────────────────────────────────────────────────────────
const btt = document.getElementById('back-to-top');
if (btt) {
  btt.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ── Counter animation ─────────────────────────────────────────────────────
function animateCounter(el, target, duration = 1800) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = Math.floor(start).toLocaleString();
    if (start >= target) clearInterval(timer);
  }, 16);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;
      const target = parseInt(el.dataset.target, 10);
      if (!isNaN(target)) animateCounter(el, target);
      counterObserver.unobserve(el);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('[data-target]').forEach(el => counterObserver.observe(el));

// ── AOS (scroll reveal) ───────────────────────────────────────────────────
const aosObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const delay = entry.target.dataset.aosDelay || 0;
      setTimeout(() => entry.target.classList.add('visible'), parseInt(delay));
      aosObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('[data-aos]').forEach(el => {
  el.classList.add('aos');
  aosObserver.observe(el);
});

// ── Contact form validation ───────────────────────────────────────────────
const form = document.getElementById('contact-form');

function sanitizeInput(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function showError(fieldId, msg) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(fieldId + '-error');
  if (field) field.classList.add('error');
  if (error) error.textContent = msg;
}

function clearError(fieldId) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(fieldId + '-error');
  if (field) field.classList.remove('error');
  if (error) error.textContent = '';
}

function validateForm() {
  let valid = true;
  const name    = document.getElementById('name');
  const phone   = document.getElementById('phone');
  const email   = document.getElementById('email');
  const message = document.getElementById('message');

  ['name','phone','email','message'].forEach(clearError);

  if (!name || name.value.trim().length < 2) {
    showError('name', 'Please enter your full name (min 2 characters).'); valid = false;
  }
  if (!phone || !/^[+\d\s\-()]{7,15}$/.test(phone.value.trim())) {
    showError('phone', 'Please enter a valid phone number.'); valid = false;
  }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
    showError('email', 'Please enter a valid email address.'); valid = false;
  }
  if (!message || message.value.trim().length < 10) {
    showError('message', 'Message must be at least 10 characters.'); valid = false;
  }
  return valid;
}

// Live validation
['name','phone','email','message'].forEach(id => {
  const el = document.getElementById(id);
  if (el) el.addEventListener('input', () => clearError(id));
});

if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    const btn  = document.getElementById('submit-btn');
    const text = document.getElementById('submit-text');
    const icon = document.getElementById('submit-icon');
    const success = document.getElementById('form-success');

    btn.disabled = true;
    if (text) text.textContent = 'Sending...';
    if (icon) icon.className = 'fas fa-spinner fa-spin';

    // Simulate API call
    setTimeout(() => {
      btn.disabled = false;
      if (text) text.textContent = 'Send Message';
      if (icon) icon.className = 'fas fa-paper-plane';
      if (success) {
        success.textContent = '✅ Message sent! We\'ll get back to you within 24 hours.';
        success.classList.add('show');
        setTimeout(() => success.classList.remove('show'), 5000);
      }
      form.reset();
    }, 1500);
  });
}

// ── Year ──────────────────────────────────────────────────────────────────
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();
