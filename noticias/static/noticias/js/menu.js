(function () {
  const menu = document.getElementById('menu');
  const toggleBtn = document.getElementById('menu-toggle');
  const closeBtn = document.getElementById('menu-close');
  const overlay = document.getElementById('menu-overlay');
  if (!menu || !toggleBtn || !overlay) return;

  function openMenu() {
    menu.classList.add('is-open');
    menu.setAttribute('aria-hidden', 'false');
    toggleBtn.setAttribute('aria-expanded', 'true');
    overlay.hidden = false;
    document.body.classList.add('no-scroll');
  }

  function closeMenu() {
    menu.classList.remove('is-open');
    menu.setAttribute('aria-hidden', 'true');
    toggleBtn.setAttribute('aria-expanded', 'false');
    overlay.hidden = true;
    document.body.classList.remove('no-scroll');
  }

  toggleBtn.addEventListener('click', openMenu);
  closeBtn?.addEventListener('click', closeMenu);
  overlay.addEventListener('click', closeMenu);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeMenu();
  });

  function closeAllExcept(exceptLi) {
    document.querySelectorAll('#menu .dropdown').forEach(li => {
      if (li !== exceptLi) {
        li.classList.remove('open');
        li.querySelector('.drop-btn')?.setAttribute('aria-expanded', 'false');
      }
    });
  }

  document.querySelectorAll('#menu .dropdown .drop-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const li = btn.closest('.dropdown');
      const isOpen = li.classList.contains('open');
      if (isOpen) {
        li.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      } else {
        closeAllExcept(li);
        li.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
})();
