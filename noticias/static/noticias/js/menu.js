(function () {
  const menu = document.getElementById('menu');
  const toggleBtn = document.getElementById('menu-toggle');
  const closeBtn = document.getElementById('menu-close');
  const overlay = document.getElementById('menu-overlay');
  if (!menu || !toggleBtn || !overlay) return;

  // === ABRIR / FECHAR MENU ===
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

  // === DROPDOWNS ===
  document.querySelectorAll('#menu .dropdown .drop-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const li = btn.closest('.dropdown');
      const isOpen = li.classList.contains('open');
      document.querySelectorAll('#menu .dropdown').forEach(d => d.classList.remove('open'));
      if (!isOpen) {
        li.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      } else {
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  });

  // === ESCONDER / MOSTRAR BARRA UOL AO ROLAR ===
  let lastScrollTop = 0;
  const uolBar = document.querySelector('.uol-bar');

  window.addEventListener('scroll', () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    if (scrollTop > lastScrollTop && scrollTop > 80) {
      uolBar.style.transform = 'translateY(-100%)';
    } else {
      uolBar.style.transform = 'translateY(0)';
    }
    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
  });
    // === BLOCO AO VIVO (cápsula expansível) ===
  const liveDropdown = document.querySelector('#menu .dropdown.live');
  if (liveDropdown) {
    const liveBtn = liveDropdown.querySelector('.drop-btn');
    const submenu = liveDropdown.querySelector('.submenu');

    // define altura inicial (fechado)
    const closedHeight = liveBtn.offsetHeight || 56;

    function openLive() {
      const totalHeight = closedHeight + submenu.scrollHeight + 16; // 16px de respiro
      liveDropdown.classList.add('is-open');
      liveDropdown.style.maxHeight = `${totalHeight}px`;
      liveBtn.setAttribute('aria-expanded', 'true');
    }

    function closeLive() {
      liveDropdown.classList.remove('is-open');
      liveDropdown.style.maxHeight = `${closedHeight}px`;
      liveBtn.setAttribute('aria-expanded', 'false');
    }

    liveBtn.addEventListener('click', () => {
      const isOpen = liveDropdown.classList.contains('is-open');
      if (isOpen) closeLive();
      else openLive();
    });

    // garante altura correta ao redimensionar
    window.addEventListener('resize', () => {
      if (liveDropdown.classList.contains('is-open')) openLive();
      else closeLive();
    });

    // inicia fechado
    closeLive();
  }

})();

// === CARROSSEL DE PRODUTOS (MOBILE APENAS) ===
document.addEventListener('DOMContentLoaded', () => {
  const produtosSection = document.querySelector('.produtos');
  if (!produtosSection) return;

  const produtosLogos = produtosSection.querySelector('.produtos-logos');
  const dots = produtosSection.querySelectorAll('.dot');
  const items = produtosSection.querySelectorAll('.produto-item');
  if (!produtosLogos || dots.length === 0 || items.length === 0) return;

  // só ativa o carrossel no mobile
  if (window.innerWidth > 768) {
    produtosLogos.style.transform = 'translateX(0)';
    return;
  }

  let currentIndex = 0;
  const totalItems = items.length; // 7 produtos
  const visiblePerPage = 4;
  const maxIndex = Math.ceil(totalItems / visiblePerPage) - 1; // 7/4 = 1.75 => 1 (0 e 1)

  function goTo(index) {
    if (index < 0) index = 0;
    if (index > maxIndex) index = maxIndex;
    currentIndex = index;

    dots.forEach(d => d.classList.remove('active'));
    dots[currentIndex].classList.add('active');

    const shiftPercent = (100 / totalItems) * (visiblePerPage * index);
    produtosLogos.style.transform = `translateX(-${shiftPercent}%)`;
  }

  // === CLIQUE NAS BOLINHAS ===
  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      const index = parseInt(dot.dataset.index);
      goTo(index);
    });
  });

  // === CONTROLE POR TOQUE (SWIPE) ===
  let startX = 0;
  let moveX = 0;

  produtosLogos.addEventListener('touchstart', e => {
    startX = e.touches[0].clientX;
  });

  produtosLogos.addEventListener('touchmove', e => {
    moveX = e.touches[0].clientX - startX;
  });

  produtosLogos.addEventListener('touchend', () => {
    if (Math.abs(moveX) > 50) {
      if (moveX < 0 && currentIndex < maxIndex) goTo(currentIndex + 1);
      else if (moveX > 0 && currentIndex > 0) goTo(currentIndex - 1);
    }
    moveX = 0;
  });

  goTo(0);
});
