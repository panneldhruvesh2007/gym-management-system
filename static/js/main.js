/* ══════════════════════════════════════
   POWERFIT GYM - MAIN JS
   ══════════════════════════════════════ */

// ── Flash Message Auto-dismiss ──
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => { alert.style.opacity = '0'; setTimeout(() => alert.remove(), 500); }, 4000);
  alert.addEventListener('click', () => alert.remove());
});

// ── Sidebar Toggle (Mobile) ──
const sidebar = document.querySelector('.sidebar');
const overlay = document.querySelector('.sidebar-overlay');
const hamburger = document.querySelector('.hamburger');

if (hamburger) {
  hamburger.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
    overlay?.classList.toggle('active');
  });
}
if (overlay) {
  overlay.addEventListener('click', () => {
    sidebar?.classList.remove('open');
    overlay.classList.remove('active');
  });
}

// ── Dropdowns ──
document.querySelectorAll('.dropdown').forEach(dd => {
  const trigger = dd.querySelector('[data-dropdown-trigger]');
  trigger?.addEventListener('click', (e) => {
    e.stopPropagation();
    dd.classList.toggle('open');
  });
});
document.addEventListener('click', () => {
  document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
});

// ── Modal System ──
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) { modal.classList.add('active'); document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) { modal.classList.remove('active'); document.body.style.overflow = ''; }
}
// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) { overlay.classList.remove('active'); document.body.style.overflow = ''; }
  });
});

// ── Animated Counter ──
function animateCounter(el) {
  const target = parseInt(el.dataset.target || el.textContent.replace(/[^0-9]/g, ''));
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const duration = 1200;
  const start = performance.now();
  
  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(eased * target);
    el.textContent = prefix + current.toLocaleString('en-IN') + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// Run counters when visible
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-value[data-target]').forEach(el => counterObserver.observe(el));

// ── Plan Price Auto-fill ──
const planSelect = document.getElementById('plan_id');
const amountInput = document.getElementById('amount');
const expiryInput = document.getElementById('expiry_date');
const joinDateInput = document.getElementById('join_date');

if (planSelect) {
  planSelect.addEventListener('change', async function() {
    const planId = this.value;
    if (!planId) return;
    try {
      const res = await fetch(`/api/plan/${planId}`);
      const plan = await res.json();
      if (amountInput) amountInput.value = plan.price;
      updateExpiry();
      updateNetAmount();
    } catch(e) {}
  });
}

function updateExpiry() {
  if (!joinDateInput || !planSelect || !expiryInput) return;
  const join = new Date(joinDateInput.value);
  if (isNaN(join)) return;
  const planOption = planSelect.options[planSelect.selectedIndex];
  const months = parseInt(planOption?.dataset?.months || 1);
  join.setMonth(join.getMonth() + months);
  expiryInput.value = join.toISOString().split('T')[0];
}

if (joinDateInput) joinDateInput.addEventListener('change', updateExpiry);

function updateNetAmount() {
  const amount = parseFloat(document.getElementById('amount')?.value || 0);
  const discount = parseFloat(document.getElementById('discount')?.value || 0);
  const netEl = document.getElementById('net_amount');
  if (netEl) netEl.value = (amount - discount).toFixed(2);
}

document.getElementById('discount')?.addEventListener('input', updateNetAmount);
document.getElementById('amount')?.addEventListener('input', updateNetAmount);

// ── Photo Preview ──
document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
  input.addEventListener('change', function() {
    const preview = document.getElementById(this.dataset.preview);
    if (preview && this.files[0]) {
      const reader = new FileReader();
      reader.onload = e => {
        preview.src = e.target.result;
        preview.style.display = 'block';
      };
      reader.readAsDataURL(this.files[0]);
    }
  });
});

// ── Delete Confirmation ──
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', function(e) {
    if (!confirm(this.dataset.confirm || 'Are you sure?')) e.preventDefault();
  });
});

// ── Data Table Search (client-side) ──
const inlineSearch = document.getElementById('inline-search');
if (inlineSearch) {
  inlineSearch.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    document.querySelectorAll('.data-table tbody tr').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
  });
}

// ── Theme Persistence ──
const savedTheme = localStorage.getItem('gym_theme');
if (savedTheme === 'light') document.body.classList.add('light-theme');

function toggleTheme() {
  document.body.classList.toggle('light-theme');
  const isLight = document.body.classList.contains('light-theme');
  localStorage.setItem('gym_theme', isLight ? 'light' : 'dark');
  const btn = document.querySelector('.theme-toggle');
  if (btn) btn.innerHTML = isLight ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
}

// ── Responsive Table: Add data-label ──
document.querySelectorAll('.data-table').forEach(table => {
  const headers = [...table.querySelectorAll('thead th')].map(th => th.textContent.trim());
  table.querySelectorAll('tbody tr').forEach(row => {
    [...row.querySelectorAll('td')].forEach((cell, i) => {
      if (headers[i]) cell.setAttribute('data-label', headers[i]);
    });
  });
});

// ── Tooltip Init ──
document.querySelectorAll('[data-tooltip]').forEach(el => {
  el.style.position = 'relative';
  el.addEventListener('mouseenter', function() {
    const tip = document.createElement('div');
    tip.className = 'tooltip';
    tip.textContent = this.dataset.tooltip;
    tip.style.cssText = `position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);background:#1a1a2e;color:#f0f0ff;padding:5px 10px;border-radius:6px;font-size:12px;white-space:nowrap;z-index:9999;pointer-events:none;`;
    this.appendChild(tip);
  });
  el.addEventListener('mouseleave', function() {
    this.querySelector('.tooltip')?.remove();
  });
});

// ── Print Invoice ──
function printInvoice() {
  window.print();
}

// ── Export CSV ──
function exportTableCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return;
  let csv = '';
  table.querySelectorAll('tr').forEach(row => {
    const cells = [...row.querySelectorAll('td, th')].map(c => `"${c.textContent.trim().replace(/"/g, '""')}"`);
    csv += cells.join(',') + '\n';
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename || 'export.csv';
  a.click();
}

/* ════════════════════════════════════════
   UPGRADES: Cookie, WhatsApp, Back-to-top,
   Form validation, Double-submit prevention
   ════════════════════════════════════════ */

// ── Safe storage ──────────────────────────────────────────────────────────
const safeStore = {
  get(k, fallback = null) {
    try { const v = localStorage.getItem(k); return v !== null ? JSON.parse(v) : fallback; }
    catch { return fallback; }
  },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  remove(k) { try { localStorage.removeItem(k); } catch {} }
};

// ── Cookie Banner ─────────────────────────────────────────────────────────
(function initCookieBanner() {
  if (safeStore.get('cookie_consent')) return;
  const banner = document.getElementById('cookie-banner');
  if (banner) setTimeout(() => banner.classList.add('show'), 900);
})();

function acceptCookies() {
  safeStore.set('cookie_consent', 'accepted');
  const b = document.getElementById('cookie-banner');
  if (b) b.classList.remove('show');
}
function declineCookies() {
  safeStore.set('cookie_consent', 'declined');
  const b = document.getElementById('cookie-banner');
  if (b) b.classList.remove('show');
}

// ── Back to Top ───────────────────────────────────────────────────────────
(function initBackToTop() {
  const btn = document.getElementById('back-to-top');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('show', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
})();

// ── Scroll reveal ─────────────────────────────────────────────────────────
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
  els.forEach(el => obs.observe(el));
})();

// ── Double-submit prevention ──────────────────────────────────────────────
document.querySelectorAll('form:not([data-no-prevent])').forEach(form => {
  form.addEventListener('submit', function() {
    const btn = this.querySelector('[type="submit"]');
    if (!btn || btn.disabled) return;
    setTimeout(() => {
      btn.disabled = true;
      const orig = btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span> Processing...';
      // Re-enable after 8s as safety fallback
      setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 8000);
    }, 0);
  });
});

// ── Input sanitization (prevent script injection) ─────────────────────────
function sanitizeInput(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ── Form field validation helpers ─────────────────────────────────────────
function showFieldError(inputEl, msg) {
  inputEl.classList.add('is-invalid');
  inputEl.classList.remove('is-valid');
  let err = inputEl.parentElement.querySelector('.field-error');
  if (!err) {
    err = document.createElement('span');
    err.className = 'field-error';
    inputEl.parentElement.appendChild(err);
  }
  err.textContent = msg;
  err.classList.add('show');
}
function clearFieldError(inputEl) {
  inputEl.classList.remove('is-invalid');
  inputEl.classList.add('is-valid');
  const err = inputEl.parentElement.querySelector('.field-error');
  if (err) err.classList.remove('show');
}

// Live validation on blur
document.querySelectorAll('input[required], textarea[required]').forEach(input => {
  input.addEventListener('blur', function() {
    if (!this.value.trim()) {
      showFieldError(this, 'This field is required.');
    } else {
      clearFieldError(this);
    }
  });
  input.addEventListener('input', function() {
    if (this.value.trim()) clearFieldError(this);
  });
});

// Email validation
document.querySelectorAll('input[type="email"]').forEach(input => {
  input.addEventListener('blur', function() {
    const v = this.value.trim();
    if (v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      showFieldError(this, 'Please enter a valid email address.');
    } else if (v) {
      clearFieldError(this);
    }
  });
});

// Phone validation
document.querySelectorAll('input[type="tel"]').forEach(input => {
  input.addEventListener('blur', function() {
    const v = this.value.trim();
    if (v && !/^[+\d\s\-()]{7,15}$/.test(v)) {
      showFieldError(this, 'Please enter a valid phone number.');
    } else if (v) {
      clearFieldError(this);
    }
  });
});

// ── Inject cookie banner + WhatsApp + back-to-top into page ──────────────
(function injectFloatingUI() {
  // Cookie banner (only if not already in template)
  if (!document.getElementById('cookie-banner')) {
    const banner = document.createElement('div');
    banner.id = 'cookie-banner';
    banner.className = 'cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Cookie consent');
    banner.innerHTML = `
      <div class="cookie-inner">
        <p>🍪 We use cookies to improve your experience. <a href="#">Learn more</a></p>
        <div class="cookie-actions">
          <button class="btn-cookie-accept" onclick="acceptCookies()">Accept</button>
          <button class="btn-cookie-decline" onclick="declineCookies()">Decline</button>
        </div>
      </div>`;
    document.body.appendChild(banner);
    if (!safeStore.get('cookie_consent')) {
      setTimeout(() => banner.classList.add('show'), 900);
    }
  }

  // Back to top button
  if (!document.getElementById('back-to-top')) {
    const btn = document.createElement('button');
    btn.id = 'back-to-top';
    btn.className = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    document.body.appendChild(btn);
    window.addEventListener('scroll', () => btn.classList.toggle('show', window.scrollY > 400), { passive: true });
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  // WhatsApp float (only on non-admin pages)
  const isAdminPage = window.location.pathname.startsWith('/admin') || window.location.pathname.startsWith('/member');
  if (!isAdminPage && !document.querySelector('.whatsapp-float')) {
    const wa = document.createElement('a');
    wa.href = 'https://wa.me/919876543210?text=Hi%20PowerFit!%20I%27m%20interested%20in%20joining.';
    wa.className = 'whatsapp-float';
    wa.target = '_blank';
    wa.rel = 'noopener';
    wa.setAttribute('aria-label', 'Chat on WhatsApp');
    wa.innerHTML = '<i class="fab fa-whatsapp"></i>';
    document.body.appendChild(wa);
  }
})();

// ── Year auto-update ──────────────────────────────────────────────────────
document.querySelectorAll('.current-year').forEach(el => {
  el.textContent = new Date().getFullYear();
});
