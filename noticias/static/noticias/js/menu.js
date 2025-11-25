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

  // === DROPDOWNS DO MENU ===
  document.querySelectorAll('#menu .dropdown .drop-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const li = btn.closest('.dropdown');
      const isOpen = li.classList.contains('open');

      // fecha todos antes de abrir o clicado
      document.querySelectorAll('#menu .dropdown').forEach(d => d.classList.remove('open'));

      if (!isOpen) {
        li.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
      } else {
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  });

  // === ESCONDER / MOSTRAR BARRA UOL NO SCROLL ===
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

  // === BLOCO AO VIVO EXPANSÍVEL ===
  const liveDropdown = document.querySelector('#menu .dropdown.live');
  if (liveDropdown) {
    const liveBtn = liveDropdown.querySelector('.drop-btn');
    const submenu = liveDropdown.querySelector('.submenu');

    // altura quando fechado
    const closedHeight = liveBtn.offsetHeight || 56;

    function openLive() {
      const totalHeight = closedHeight + submenu.scrollHeight + 16;
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

    // atualiza ao redimensionar a tela
    window.addEventListener('resize', () => {
      if (liveDropdown.classList.contains('is-open')) openLive();
      else closeLive();
    });

    // inicia fechado
    closeLive();
  }

})();
// === CARROSSEL MOBILE — NOSSOS PRODUTOS ===
(function () {
  const carrossel = document.querySelector(".produtos-logos");
  const dots = document.querySelectorAll(".carousel-dots .dot");

  // só funciona se existir (somente mobile)
  if (!carrossel || dots.length === 0) return;

  let page = 0; // página inicial

  function getPageWidth() {
    return carrossel.clientWidth; // largura da viewport do carrossel
  }

  // Atualiza a bolinha ativa
  function updateDots() {
    dots.forEach(dot => dot.classList.remove("active"));
    dots[page].classList.add("active");
  }

  // Clicar nas bolinhas → deslizar carrossel
  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      page = parseInt(dot.dataset.index);
      carrossel.scrollTo({
        left: getPageWidth() * page,
        behavior: "smooth"
      });
      updateDots();
    });
  });

  // Scroll manual → mudar bolinhas automaticamente
  carrossel.addEventListener("scroll", () => {
    const width = getPageWidth();
    const newPage = Math.round(carrossel.scrollLeft / width);

    if (newPage !== page) {
      page = newPage;
      updateDots();
    }
  });
})();
