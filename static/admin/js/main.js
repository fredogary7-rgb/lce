// ========== LCE ADMIN JS ==========
(function () {
  'use strict';

  // --- SIDEBAR TOGGLE ---
  const sidebar = document.getElementById('adminSidebar');
  const main = document.getElementById('adminMain');
  const sidebarCollapse = document.getElementById('sidebarCollapse');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarToggleMobile = document.getElementById('sidebarToggleMobile');

  // Create overlay for mobile
  let overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  overlay.id = 'sidebarOverlay';
  document.body.appendChild(overlay);

  function openSidebar() {
    if (sidebar) sidebar.classList.add('show');
    if (overlay) overlay.classList.add('show');
  }
  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('show');
    if (overlay) overlay.classList.remove('show');
  }
  function toggleSidebar() {
    if (sidebar) {
      if (sidebar.classList.contains('show')) closeSidebar();
      else openSidebar();
    }
  }
  function toggleDesktop() {
    // Desktop collapse (hide text, keep icons)
    if (sidebar && main) {
      sidebar.classList.toggle('collapsed');
      main.classList.toggle('expanded');
      localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
    }
  }

  if (sidebarCollapse) sidebarCollapse.addEventListener('click', toggleDesktop);
  if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
  if (sidebarToggleMobile) sidebarToggleMobile.addEventListener('click', toggleSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Restore desktop state
  if (localStorage.getItem('sidebar-collapsed') === 'true' && window.innerWidth >= 992) {
    if (sidebar) sidebar.classList.add('collapsed');
    if (main) main.classList.add('expanded');
  }

  // Close on escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) closeSidebar();
  });

  // Resize handler
  window.addEventListener('resize', function() {
    if (window.innerWidth >= 992) {
      closeSidebar();
      // Restore desktop collapse
      if (localStorage.getItem('sidebar-collapsed') === 'true') {
        sidebar.classList.add('collapsed');
        main.classList.add('expanded');
      }
    }
  });

  // --- DARK MODE TOGGLE ---
  const darkBtn = document.getElementById('darkModeToggle');
  const html = document.documentElement;

  function setTheme(theme) {
    html.setAttribute('data-bs-theme', theme);
    localStorage.setItem('admin-theme', theme);
    if (darkBtn) {
      const icon = darkBtn.querySelector('i');
      if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars';
      }
    }
  }

  const savedTheme = localStorage.getItem('admin-theme') || 'light';
  setTheme(savedTheme);

  if (darkBtn) {
    darkBtn.addEventListener('click', function() {
      const current = html.getAttribute('data-bs-theme');
      setTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // --- CONFIRMATION DIALOGS ---
  // Improve confirm with Bootstrap modal? Keep native for now

  // --- AUTO-HIDE ALERTS ---
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      const closeBtn = alert.querySelector('.btn-close');
      if (closeBtn) closeBtn.click();
    }, 5000);
  });

  // --- COUNTER ANIMATION FOR STATS ---
  const statValues = document.querySelectorAll('.stat-value');
  statValues.forEach(function(el) {
    const target = parseInt(el.textContent || '0', 10);
    if (isNaN(target) || target === 0) return;
    let current = 0;
    const duration = 800;
    const step = Math.max(1, Math.ceil(target / (duration / 16)));
    const timer = setInterval(function() {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = current;
      }
    }, 16);
  });

  // --- IMAGE PREVIEW (optional, for file inputs) ---
  document.addEventListener('change', function(e) {
    const input = e.target;
    if (input && input.type === 'file' && input.accept && input.accept.includes('image')) {
      const file = input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(ev) {
        // Try to find preview element nearby
        const previewId = input.id.replace('Image', '') + 'Preview';
        const preview = document.getElementById(previewId) || document.getElementById('imgPreview');
        if (preview) {
          preview.classList.remove('d-none');
          const img = preview.querySelector('img');
          if (img) img.src = ev.target.result;
        }
      };
      reader.readAsDataURL(file);
    }
  });

})();