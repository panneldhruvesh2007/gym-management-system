// =============================================
// FITPRO GYM MANAGEMENT - MAIN JS
// =============================================

document.addEventListener('DOMContentLoaded', function() {
  initSidebar();
  initAlerts();
  initAnimations();
  initDateTime();
  initTheme();
  initModals();
  initDropdowns();
  initSearch();
  initCounters();
  initCharts();
  initMobileMenu();
});

// =============================================
// SIDEBAR
// =============================================
function initSidebar() {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const topbar = document.getElementById('topbar');

  if (!toggleBtn || !sidebar) return;

  const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (collapsed) {
    sidebar.classList.add('collapsed');
    mainContent?.classList.add('sidebar-collapsed');
    topbar?.classList.add('sidebar-collapsed');
  }

  toggleBtn.addEventListener('click', function() {
    const isCollapsed = sidebar.classList.toggle('collapsed');
    mainContent?.classList.toggle('sidebar-collapsed', isCollapsed);
    topbar?.classList.toggle('sidebar-collapsed', isCollapsed);
    localStorage.setItem('sidebarCollapsed', isCollapsed);
  });

  // Tooltip for collapsed nav items
  document.querySelectorAll('.nav-link').forEach(link => {
    const text = link.querySelector('.nav-text')?.textContent;
    if (text) link.setAttribute('title', text);
  });
}

// Sidebar collapsed styles
const sidebarStyle = document.createElement('style');
sidebarStyle.textContent = `
  .sidebar.collapsed { width: var(--sidebar-collapsed); }
  .sidebar.collapsed .nav-text,
  .sidebar.collapsed .nav-section-label,
  .sidebar.collapsed .sidebar-logo-text,
  .sidebar.collapsed .user-info,
  .sidebar.collapsed .nav-badge { display: none; }
  .sidebar.collapsed .sidebar-logo { justify-content: center; padding: 20px 0; }
  .sidebar.collapsed .nav-link { justify-content: center; padding: 11px 0; }
  .sidebar.collapsed .user-card { justify-content: center; padding: 10px 0; }
  .topbar.sidebar-collapsed { left: var(--sidebar-collapsed); }
  .main-content.sidebar-collapsed { margin-left: var(--sidebar-collapsed); }
  @media (max-width: 768px) {
    .sidebar.collapsed { transform: translateX(-100%); width: var(--sidebar-width); }
    .topbar { left: 0 !important; }
    .main-content { margin-left: 0 !important; }
    .sidebar.mobile-open { transform: translateX(0) !important; }
  }
`;
document.head.appendChild(sidebarStyle);

// =============================================
// MOBILE MENU
// =============================================
function initMobileMenu() {
  if (window.innerWidth > 768) return;
  
  const sidebar = document.getElementById('sidebar');
  const overlay = document.createElement('div');
  overlay.id = 'mobileOverlay';
  overlay.style.cssText = `
    display:none; position:fixed; inset:0; background:rgba(0,0,0,0.7);
    z-index:999; backdrop-filter:blur(4px);
  `;
  document.body.appendChild(overlay);

  const mobileToggle = document.getElementById('sidebarToggle');
  mobileToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('mobile-open');
    overlay.style.display = sidebar?.classList.contains('mobile-open') ? 'block' : 'none';
  });

  overlay.addEventListener('click', () => {
    sidebar?.classList.remove('mobile-open');
    overlay.style.display = 'none';
  });
}

// =============================================
// ALERTS / NOTIFICATIONS
// =============================================
function initAlerts() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert, i) => {
    alert.style.animationDelay = `${i * 0.1}s`;
    
    const closeBtn = alert.querySelector('.alert-close');
    closeBtn?.addEventListener('click', () => dismissAlert(alert));

    // Auto-dismiss after 5s
    setTimeout(() => dismissAlert(alert), 5000 + i * 200);
  });
}

function dismissAlert(alert) {
  alert.style.transition = 'all 0.4s ease';
  alert.style.transform = 'translateX(110%)';
  alert.style.opacity = '0';
  setTimeout(() => alert.remove(), 400);
}

function showNotification(message, type = 'info') {
  const container = document.getElementById('alertsContainer') || createAlertsContainer();
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.innerHTML = `
    <span>${icons[type] || 'ℹ️'}</span>
    <span>${message}</span>
    <button class="alert-close" onclick="this.closest('.alert').remove()">×</button>
  `;
  container.appendChild(alert);
  setTimeout(() => dismissAlert(alert), 5000);
  return alert;
}

function createAlertsContainer() {
  const c = document.createElement('div');
  c.id = 'alertsContainer';
  c.className = 'alerts-container';
  document.body.appendChild(c);
  return c;
}

// =============================================
// ANIMATIONS
// =============================================
function initAnimations() {
  // Intersection Observer for scroll animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card, .stat-card, .trainer-card, .plan-card').forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

// =============================================
// COUNTER ANIMATIONS
// =============================================
function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
  const target = parseFloat(el.dataset.count);
  const duration = 1200;
  const isDecimal = el.dataset.decimal === 'true';
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const start = performance.now();

  function update(time) {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = target * eased;
    
    if (isDecimal) {
      el.textContent = prefix + current.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
    } else {
      el.textContent = prefix + Math.floor(current).toLocaleString() + suffix;
    }
    
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = prefix + (isDecimal ? target.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : target.toLocaleString()) + suffix;
  }
  
  requestAnimationFrame(update);
}

// =============================================
// CHARTS
// =============================================
function initCharts() {
  // Revenue Chart
  const revenueEl = document.getElementById('revenueChart');
  if (revenueEl && window.Chart) {
    const data = JSON.parse(revenueEl.dataset.chart || '{}');
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    new Chart(revenueEl, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Revenue',
          data: values,
          backgroundColor: (ctx) => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(255,107,43,0.8)');
            gradient.addColorStop(1, 'rgba(255,107,43,0.1)');
            return gradient;
          },
          borderColor: '#FF6B2B',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10,10,20,0.9)',
            borderColor: 'rgba(255,107,43,0.3)',
            borderWidth: 1,
            padding: 14,
            titleColor: '#F0F0F8',
            bodyColor: '#9090B0',
            callbacks: {
              label: ctx => `Revenue: ₹${ctx.raw.toLocaleString()}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
            ticks: { color: '#9090B0', font: { size: 12 } }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
            ticks: {
              color: '#9090B0', font: { size: 12 },
              callback: v => '₹' + v.toLocaleString()
            },
            beginAtZero: true
          }
        },
        animation: {
          duration: 1200,
          easing: 'easeInOutCubic'
        }
      }
    });
  }

  // Payment Mode Donut Chart
  const modeEl = document.getElementById('paymentModeChart');
  if (modeEl && window.Chart) {
    const data = JSON.parse(modeEl.dataset.chart || '{}');
    const colors = ['#FF6B2B', '#FFD700', '#4FC3F7', '#00E676'];
    
    new Chart(modeEl, {
      type: 'doughnut',
      data: {
        labels: Object.keys(data).map(k => k.toUpperCase()),
        datasets: [{
          data: Object.values(data),
          backgroundColor: colors,
          borderColor: 'transparent',
          borderWidth: 0,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '72%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#9090B0',
              padding: 16,
              font: { size: 12 },
              boxWidth: 12,
              boxHeight: 12
            }
          },
          tooltip: {
            backgroundColor: 'rgba(10,10,20,0.9)',
            borderColor: 'rgba(255,107,43,0.3)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: ctx => ` ₹${ctx.raw.toLocaleString()}`
            }
          }
        },
        animation: { animateScale: true, duration: 1200 }
      }
    });
  }

  // Member Growth Line Chart
  const growthEl = document.getElementById('memberGrowthChart');
  if (growthEl && window.Chart) {
    const data = JSON.parse(growthEl.dataset.chart || '{}');
    
    new Chart(growthEl, {
      type: 'line',
      data: {
        labels: Object.keys(data),
        datasets: [{
          label: 'New Members',
          data: Object.values(data),
          borderColor: '#4FC3F7',
          backgroundColor: (ctx) => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, 'rgba(79,195,247,0.3)');
            gradient.addColorStop(1, 'rgba(79,195,247,0)');
            return gradient;
          },
          borderWidth: 2.5,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#4FC3F7',
          pointBorderColor: '#0a0a0f',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10,10,20,0.9)',
            borderColor: 'rgba(79,195,247,0.3)',
            borderWidth: 1,
            padding: 14,
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#9090B0', font: { size: 12 } }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#9090B0', font: { size: 12 } },
            beginAtZero: true
          }
        }
      }
    });
  }
}

// =============================================
// DATETIME
// =============================================
function initDateTime() {
  const el = document.getElementById('currentDateTime');
  if (!el) return;

  function update() {
    const now = new Date();
    el.textContent = now.toLocaleString('en-IN', {
      weekday: 'short', day: '2-digit', month: 'short',
      year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }
  update();
  setInterval(update, 1000);
}

// =============================================
// THEME
// =============================================
function initTheme() {
  const theme = document.documentElement.dataset.theme || localStorage.getItem('theme') || 'dark';
  document.documentElement.dataset.theme = theme;
  
  const toggles = document.querySelectorAll('[data-theme-toggle]');
  toggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
      const current = document.documentElement.dataset.theme;
      const newTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = newTheme;
      localStorage.setItem('theme', newTheme);
      toggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    });
    toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
  });
}

// =============================================
// MODALS
// =============================================
function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modal = document.getElementById(trigger.dataset.modalTarget);
      openModal(modal);
    });
  });

  document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      closeModal(modal);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal(overlay);
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.show').forEach(m => closeModal(m));
    }
  });
}

function openModal(modal) {
  if (!modal) return;
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('show');
  document.body.style.overflow = '';
}

// Delete confirmation modal
function confirmDelete(formId, name) {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.querySelector('.delete-name').textContent = name;
    modal.querySelector('.confirm-delete-btn').onclick = () => {
      document.getElementById(formId)?.submit();
    };
    openModal(modal);
  } else {
    if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      document.getElementById(formId)?.submit();
    }
  }
}

// =============================================
// DROPDOWNS
// =============================================
function initDropdowns() {
  document.querySelectorAll('[data-dropdown]').forEach(trigger => {
    const target = document.getElementById(trigger.dataset.dropdown);
    if (!target) return;

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = target.classList.toggle('open');
      if (isOpen) {
        positionDropdown(trigger, target);
      }
    });
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.open').forEach(d => d.classList.remove('open'));
  });
}

function positionDropdown(trigger, dropdown) {
  const rect = trigger.getBoundingClientRect();
  dropdown.style.top = `${rect.bottom + window.scrollY + 8}px`;
  dropdown.style.right = `${window.innerWidth - rect.right}px`;
}

// =============================================
// SEARCH
// =============================================
function initSearch() {
  // Live member search in forms
  const memberSearchInput = document.getElementById('memberSearch');
  if (memberSearchInput) {
    let timeout;
    memberSearchInput.addEventListener('input', function() {
      clearTimeout(timeout);
      timeout = setTimeout(() => searchMembers(this.value), 300);
    });
  }
}

async function searchMembers(query) {
  if (query.length < 2) {
    document.getElementById('memberSearchResults')?.classList.remove('show');
    return;
  }

  try {
    const res = await fetch(`/api/search_members?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    
    const resultsEl = document.getElementById('memberSearchResults');
    if (!resultsEl) return;

    if (data.length === 0) {
      resultsEl.innerHTML = '<div class="search-result-item empty">No members found</div>';
    } else {
      resultsEl.innerHTML = data.map(m => `
        <div class="search-result-item" onclick="selectMember(${m.id}, '${m.full_name}', '${m.member_id}')">
          <span class="font-mono text-primary">${m.member_id}</span> — ${m.full_name}
          <span class="text-muted">${m.phone}</span>
        </div>
      `).join('');
    }
    resultsEl.classList.add('show');
  } catch(err) {
    console.error('Search error:', err);
  }
}

function selectMember(id, name, mid) {
  document.getElementById('memberIdInput').value = id;
  document.getElementById('memberSearch').value = `${mid} - ${name}`;
  document.getElementById('memberSearchResults')?.classList.remove('show');
}

// =============================================
// FORM HELPERS
// =============================================
async function getPlanPrice(planId) {
  if (!planId) return;
  try {
    const res = await fetch(`/api/get_plan_price/${planId}`);
    const data = await res.json();
    const amountInput = document.getElementById('amountInput');
    if (amountInput && data.price > 0) {
      amountInput.value = data.price.toFixed(2);
    }
  } catch(err) {
    console.error('Error fetching plan price:', err);
  }
}

// Auto-calculate expiry date
function calcExpiryDate() {
  const joinDateEl = document.getElementById('joinDate');
  const planEl = document.getElementById('planSelect');
  const expiryEl = document.getElementById('expiryDate');
  
  if (!joinDateEl || !planEl || !expiryEl) return;
  
  const joinDate = new Date(joinDateEl.value);
  const planOption = planEl.selectedOptions[0];
  const months = parseInt(planOption?.dataset.months || 0);
  
  if (joinDate && months) {
    const expiry = new Date(joinDate);
    expiry.setMonth(expiry.getMonth() + months);
    expiryEl.value = expiry.toISOString().split('T')[0];
  }
}

// =============================================
// TABLE UTILITIES
// =============================================
function filterTable(inputId, tableId) {
  const filter = document.getElementById(inputId).value.toLowerCase();
  const rows = document.querySelectorAll(`#${tableId} tbody tr`);
  let visible = 0;
  
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const show = text.includes(filter);
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  const countEl = document.getElementById('tableCount');
  if (countEl) countEl.textContent = visible;
}

// =============================================
// PRINT INVOICE
// =============================================
function printInvoice() {
  window.print();
}

// =============================================
// EXPORT
// =============================================
function exportTableCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = Array.from(table.querySelectorAll('tr'));
  const csv = rows.map(row => 
    Array.from(row.querySelectorAll('th, td'))
      .map(cell => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
      .join(',')
  ).join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filename || 'export'}_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  
  showNotification('Data exported successfully!', 'success');
}

// =============================================
// PHOTO PREVIEW
// =============================================
function initPhotoPreview() {
  document.querySelectorAll('.photo-upload input[type="file"]').forEach(input => {
    input.addEventListener('change', function() {
      const file = this.files[0];
      if (!file) return;
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = this.closest('.photo-upload').querySelector('.photo-preview');
        if (preview) {
          preview.src = e.target.result;
          preview.style.display = 'block';
        }
        
        const icon = this.closest('.photo-upload').querySelector('.upload-icon');
        if (icon) icon.style.display = 'none';
        
        const text = this.closest('.photo-upload').querySelector('.upload-text');
        if (text) text.textContent = file.name;
      };
      reader.readAsDataURL(file);
    });
  });
}

document.addEventListener('DOMContentLoaded', initPhotoPreview);

// =============================================
// TABS
// =============================================
function initTabsManual(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const tabId = this.dataset.tab;
      
      container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      this.classList.add('active');
      document.getElementById(tabId)?.classList.add('active');
    });
  });
}

// =============================================
// SETTINGS: THEME
// =============================================
function setThemeMode(mode) {
  document.documentElement.dataset.theme = mode;
  localStorage.setItem('theme', mode);
  
  document.querySelectorAll('.theme-opt').forEach(opt => {
    opt.classList.toggle('active', opt.dataset.mode === mode);
  });
}

// =============================================
// LOADING STATES
// =============================================
function setLoading(btn, loading) {
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Loading...';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText;
    btn.disabled = false;
  }
}

// Form submission loading
document.querySelectorAll('form[data-loading]').forEach(form => {
  form.addEventListener('submit', function() {
    const btn = this.querySelector('[type="submit"]');
    if (btn) setLoading(btn, true);
  });
});

// =============================================
// SEARCH BAR DROPDOWN STYLES
// =============================================
const searchStyle = document.createElement('style');
searchStyle.textContent = `
  .search-results-dropdown {
    position: absolute;
    top: 100%; left: 0; right: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-card);
    max-height: 240px;
    overflow-y: auto;
    z-index: 100;
    display: none;
  }
  .search-results-dropdown.show { display: block; }
  .search-result-item {
    padding: 10px 14px;
    cursor: pointer;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
    display: flex;
    gap: 10px;
    align-items: center;
    transition: background 0.15s;
    color: var(--text-secondary);
  }
  .search-result-item:hover { background: var(--bg-glass); }
  .search-result-item.empty { cursor: default; justify-content: center; color: var(--text-muted); }

  .dropdown-menu {
    position: fixed;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-card);
    min-width: 180px;
    z-index: 2000;
    display: none;
    overflow: hidden;
  }
  .dropdown-menu.open { display: block; animation: fadeIn 0.2s ease; }
  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    font-size: 14px;
    color: var(--text-secondary);
    text-decoration: none;
    cursor: pointer;
    transition: background 0.15s;
    border: none;
    background: none;
    width: 100%;
    font-family: var(--font-body);
  }
  .dropdown-item:hover { background: var(--bg-glass); color: var(--text-primary); }
  .dropdown-item.danger:hover { color: var(--danger); }
  .dropdown-divider { border: none; border-top: 1px solid var(--border); margin: 4px 0; }

  .theme-switcher { display: flex; gap: 8px; margin-top: 12px; }
  .theme-opt {
    flex: 1; padding: 10px; border-radius: var(--radius-sm); cursor: pointer;
    border: 2px solid var(--border); background: var(--bg-glass);
    color: var(--text-secondary); font-size: 13px; font-weight: 500; text-align: center;
    transition: var(--transition-fast); font-family: var(--font-body);
  }
  .theme-opt.active { border-color: var(--primary); color: var(--primary); background: var(--primary-glow); }
  .theme-opt:hover { border-color: var(--border-hover); color: var(--text-primary); }
`;
document.head.appendChild(searchStyle);
