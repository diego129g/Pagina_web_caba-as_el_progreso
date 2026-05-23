/* cabana_detalles.js */
console.log('[cabana_detalles] JS loaded');

document.addEventListener('DOMContentLoaded', function () {
  console.log('[cabana_detalles] DOMContentLoaded');

  var sidebarToggle = document.getElementById('sidebar-toggle');
  var sidebarList = document.getElementById('sidebar-list');

  /* ── Toggle sidebar en móvil ── */
  if (sidebarToggle && sidebarList) {
    sidebarToggle.addEventListener('click', function () {
      var isOpen = sidebarList.classList.contains('open');
      sidebarList.classList.toggle('open');
      sidebarToggle.classList.toggle('open');
      sidebarToggle.setAttribute('aria-expanded', !isOpen);
    });

    sidebarList.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth < 900) {
          sidebarList.classList.remove('open');
          sidebarToggle.classList.remove('open');
          sidebarToggle.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }

  /* ── Resaltar link activo al hacer scroll ── */
  (function () {
    var sidebarLinks = document.querySelectorAll('.detalle-sidebar__link');
    if (sidebarLinks.length > 1 && 'IntersectionObserver' in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.id;
            sidebarLinks.forEach(function (link) {
              link.classList.toggle('active', link.getAttribute('href') === '#' + id);
            });
          }
        });
      }, { rootMargin: '-40% 0px -55% 0px' });
      document.querySelectorAll('[data-observe]').forEach(function (el) {
        observer.observe(el);
      });
    }
  })();

  /* ── Animación escalonada al hacer scroll ── */
  (function () {
    var animItems = document.querySelectorAll('.tarifa-card, .extra-card');
    if (animItems.length && 'IntersectionObserver' in window) {
      var animObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            animObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      animItems.forEach(function (el, i) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        el.style.transitionDelay = i * 0.06 + 's';
        animObserver.observe(el);
      });
    }
  })();

  /* ════════════════════════════════════════════
     CALENDARIO DE DISPONIBILIDAD
     ════════════════════════════════════════════ */
  (function () {
    console.log('[calendario] iniciando…');

    var container = document.getElementById('calendario-container');
    console.log('[calendario] container:', container);
    if (!container) {
      console.warn('[calendario] #calendario-container NO encontrado');
      return;
    }

    var cabanaId  = container.getAttribute('data-cabana-id');
    var apiUrl    = container.getAttribute('data-url');
    console.log('[calendario] cabanaId:', cabanaId, 'apiUrl:', apiUrl);
    if (!cabanaId || !apiUrl) {
      console.warn('[calendario] faltan data-cabana-id o data-url');
      return;
    }

    var hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    var mesActual = hoy.getMonth();
    var anioActual = hoy.getFullYear();
    var cache = {};
    var ocupadosGlobal = [];

    var meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                 'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    var diasSem = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];

    function fmtFecha(d) {
      var y = d.getFullYear();
      var m = String(d.getMonth() + 1).padStart(2, '0');
      var dd = String(d.getDate()).padStart(2, '0');
      return y + '-' + m + '-' + dd;
    }

    function mostrarLoading() {
      container.innerHTML =
        '<div class="calendario-loading">Cargando disponibilidad…</div>';
    }

    function mostrarError(msg) {
      container.innerHTML =
        '<div class="calendario-error">❌ ' + (msg || 'No se pudo cargar.') + '</div>';
    }

    function fetchDisponibilidad(mes, anio, cb) {
      var key = mes + '-' + anio;
      if (cache[key]) { cb(cache[key]); return; }

      var url = apiUrl + '?cabana_id=' + cabanaId + '&month=' + (mes + 1) + '&year=' + anio;
      console.log('[calendario] XHR GET', url);

      var xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.timeout = 10000;

      xhr.onload = function () {
        console.log('[calendario] XHR status:', xhr.status, xhr.responseText.substring(0, 120));
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            var data = JSON.parse(xhr.responseText);
            var ocupados = data.dias_ocupados || [];
            console.log('[calendario] días ocupados:', ocupados.length);
            cache[key] = ocupados;
            cb(ocupados);
          } catch (e) {
            console.error('[calendario] JSON parse error:', e);
            mostrarError('Respuesta inválida del servidor.');
          }
        } else {
          mostrarError('Error del servidor (' + xhr.status + ').');
        }
      };

      xhr.onerror = function () {
        console.error('[calendario] XHR error');
        mostrarError('Error de conexión.');
      };

      xhr.ontimeout = function () {
        console.error('[calendario] XHR timeout');
        mostrarError('Tiempo de espera agotado.');
      };

      xhr.send();
    }

    function renderCalendario(mes, anio, ocupados) {
      console.log('[calendario] renderizando', meses[mes], anio);
      ocupadosGlobal = ocupados;

      var ocupSet = {};
      ocupados.forEach(function (f) { ocupSet[f] = true; });

      var primero  = new Date(anio, mes, 1);
      var ultimo   = new Date(anio, mes + 1, 0);
      var diasMes  = ultimo.getDate();
      var inicioWD = primero.getDay();

      var html = '';

      /* Header */
      html += '<div class="calendario-header">';
      html += '<button class="calendario-header__btn" data-mes="prev" aria-label="Mes anterior">‹</button>';
      html += '<span class="calendario-header__mes">' + meses[mes] + ' ' + anio + '</span>';
      html += '<button class="calendario-header__btn" data-mes="next" aria-label="Mes siguiente">›</button>';
      html += '</div>';

      /* Grid */
      html += '<div class="calendario-grid">';

      for (var i = 0; i < 7; i++) {
        html += '<div class="calendario-grid__dia-nombre">' + diasSem[i] + '</div>';
      }

      for (var j = 0; j < inicioWD; j++) {
        html += '<div class="calendario-grid__dia calendario-grid__dia--otro-mes"></div>';
      }

      for (var d = 1; d <= diasMes; d++) {
        var fecha = new Date(anio, mes, d);
        var fStr = fmtFecha(fecha);
        var clases = ['calendario-grid__dia'];

        if (fecha < hoy) {
          clases.push('calendario-grid__dia--pasado');
        } else if (ocupSet[fStr]) {
          clases.push('calendario-grid__dia--ocupado');
        } else {
          clases.push('calendario-grid__dia--disponible');
        }

        if (fecha.toDateString() === hoy.toDateString()) {
          clases.push('calendario-grid__dia--hoy');
        }

        html += '<div class="' + clases.join(' ') + '" data-fecha="' + fStr + '">' + d + '</div>';
      }

      var total = inicioWD + diasMes;
      var resto = total % 7;
      if (resto > 0) {
        for (var k = 0; k < 7 - resto; k++) {
          html += '<div class="calendario-grid__dia calendario-grid__dia--otro-mes"></div>';
        }
      }

      html += '</div>';

      /* Leyenda */
      html += '<div class="calendario-leyenda">';
      html += '<span class="calendario-leyenda__item"><span class="calendario-leyenda__color calendario-leyenda__color--disponible"></span> Disponible</span>';
      html += '<span class="calendario-leyenda__item"><span class="calendario-leyenda__color calendario-leyenda__color--ocupado"></span> Ocupado</span>';
      html += '<span class="calendario-leyenda__item"><span class="calendario-leyenda__color calendario-leyenda__color--hoy"></span> Hoy</span>';
      html += '</div>';

      container.innerHTML = html;
      console.log('[calendario] renderizado OK');

      /* Eventos navegación */
      var prev = container.querySelector('[data-mes="prev"]');
      var next = container.querySelector('[data-mes="next"]');
      if (prev) {
        prev.addEventListener('click', function (e) {
          e.preventDefault();
          mesActual = mes === 0 ? 11 : mes - 1;
          anioActual = mes === 0 ? anio - 1 : anio;
          render();
        });
      }
      if (next) {
        next.addEventListener('click', function (e) {
          e.preventDefault();
          mesActual = mes === 11 ? 0 : mes + 1;
          anioActual = mes === 11 ? anio + 1 : anio;
          render();
        });
      }
    }

    function render() {
      mostrarLoading();
      fetchDisponibilidad(mesActual, anioActual, function (ocupados) {
        renderCalendario(mesActual, anioActual, ocupados);
      });
    }

    render();
  })();
});
