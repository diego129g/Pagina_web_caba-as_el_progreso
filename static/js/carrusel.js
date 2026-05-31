(function () {
  'use strict';

  var carrusel = document.querySelector('.carrusel');
  if (!carrusel) return;

  var slides = carrusel.querySelector('.carrusel__slides');
  var total  = parseInt(carrusel.dataset.total, 10);
  if (total < 2) return;

  var prevBtn = carrusel.querySelector('.carrusel__btn--prev');
  var nextBtn = carrusel.querySelector('.carrusel__btn--next');
  var dots    = carrusel.querySelectorAll('.carrusel__dot');
  var current = 0;

  function goTo(index) {
    if (index < 0) index = total - 1;
    if (index >= total) index = 0;
    current = index;
    slides.style.transform = 'translateX(-' + (current * 100) + '%)';
    for (var i = 0; i < dots.length; i++) {
      dots[i].classList.toggle('carrusel__dot--active', i === current);
    }
  }

  function next() { goTo(current + 1); }
  function prev() { goTo(current - 1); }

  if (prevBtn) {
    prevBtn.addEventListener('click', function (e) {
      e.preventDefault();
      prev();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', function (e) {
      e.preventDefault();
      next();
    });
  }

  for (var j = 0; j < dots.length; j++) {
    (function (idx) {
      dots[idx].addEventListener('click', function (e) {
        e.preventDefault();
        goTo(idx);
      });
    })(j);
  }

  // ── Swipe táctil ──
  var xStart = 0;
  var xDelta = 0;

  carrusel.addEventListener('touchstart', function (e) {
    xStart = e.changedTouches[0].screenX;
  }, { passive: true });

  carrusel.addEventListener('touchend', function (e) {
    xDelta = e.changedTouches[0].screenX - xStart;
    if (Math.abs(xDelta) > 50) {
      if (xDelta < 0) next();
      else prev();
    }
  }, { passive: true });

  goTo(0);
})();
