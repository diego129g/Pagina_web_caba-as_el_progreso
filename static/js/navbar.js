/* navbar.js — Menú hamburguesa */
document.addEventListener('DOMContentLoaded', function () {
  const hamburger = document.getElementById('navbar-hamburger');
  const mobileMenu = document.getElementById('navbar-mobile-menu');

  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', function () {
    const isOpen = mobileMenu.classList.contains('open');
    hamburger.classList.toggle('active');
    mobileMenu.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', !isOpen);
    document.body.style.overflow = isOpen ? '' : 'hidden';
  });

  // Cerrar al hacer click en un link
  mobileMenu.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      hamburger.classList.remove('active');
      mobileMenu.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  // Cerrar al hacer scroll
  window.addEventListener('scroll', function () {
    if (mobileMenu.classList.contains('open')) {
      hamburger.classList.remove('active');
      mobileMenu.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  }, { passive: true });
});