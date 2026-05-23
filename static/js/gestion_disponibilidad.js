/* gestion_disponibilidad.js — Calendario de disponibilidad para el panel de gestión */
document.addEventListener('DOMContentLoaded', function () {
  var select    = document.getElementById('cabana-select');
  var container = document.getElementById('calendario-container');

  if (!select || !container) return;

  var apiUrl = container.getAttribute('data-url');
  if (!apiUrl) return;

  var hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  var mesActual = hoy.getMonth();
  var anioActual = hoy.getFullYear();
  var cache = {};

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
    container.innerHTML = '<div class="calendario-loading">Cargando disponibilidad…</div>';
  }

  function mostrarError(msg) {
    container.innerHTML = '<div class="calendario-error" style="text-align:center;padding:20px;color:#c0392b;background:#fde8e8;border-radius:10px;font-size:0.85rem;">❌ ' + (msg || 'No se pudo cargar.') + '</div>';
  }

  function fetchDisponibilidad(cabanaId, mes, anio, cb) {
    var key = cabanaId + '-' + mes + '-' + anio;
    if (cache[key]) { cb(cache[key]); return; }

    var url = apiUrl + '?cabana_id=' + cabanaId + '&month=' + (mes + 1) + '&year=' + anio;

    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.timeout = 10000;
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var data = JSON.parse(xhr.responseText);
          var ocupados = data.dias_ocupados || [];
          cache[key] = ocupados;
          cb(ocupados);
        } catch (e) {
          mostrarError('Respuesta inválida.');
        }
      } else {
        mostrarError('Error (' + xhr.status + ').');
      }
    };
    xhr.onerror = function () { mostrarError('Error de conexión.'); };
    xhr.ontimeout = function () { mostrarError('Tiempo agotado.'); };
    xhr.send();
  }

  function renderCalendario(cabanaId, mes, anio, ocupados) {
    var ocupSet = {};
    ocupados.forEach(function (f) { ocupSet[f] = true; });

    var primero  = new Date(anio, mes, 1);
    var ultimo   = new Date(anio, mes + 1, 0);
    var diasMes  = ultimo.getDate();
    var inicioWD = primero.getDay();

    var html = '';

    /* Header */
    html += '<div class="calendario-header">';
    html += '<button class="calendario-header__btn" data-mes="prev">‹</button>';
    html += '<span class="calendario-header__mes">' + meses[mes] + ' ' + anio + '</span>';
    html += '<button class="calendario-header__btn" data-mes="next">›</button>';
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

    /* Eventos navegación */
    var prev = container.querySelector('[data-mes="prev"]');
    var next = container.querySelector('[data-mes="next"]');
    if (prev) {
      prev.addEventListener('click', function () {
        mesActual = mes === 0 ? 11 : mes - 1;
        anioActual = mes === 0 ? anio - 1 : anio;
        render(cabanaId);
      });
    }
    if (next) {
      next.addEventListener('click', function () {
        mesActual = mes === 11 ? 0 : mes + 1;
        anioActual = mes === 11 ? anio + 1 : anio;
        render(cabanaId);
      });
    }
  }

  function render(cabanaId) {
    mostrarLoading();
    fetchDisponibilidad(cabanaId, mesActual, anioActual, function (ocupados) {
      renderCalendario(cabanaId, mesActual, anioActual, ocupados);
    });
  }

  /* Iniciar con la primera cabaña */
  render(select.value);

  /* Cambiar al seleccionar otra cabaña */
  select.addEventListener('change', function () {
    cache = {};
    mesActual = hoy.getMonth();
    anioActual = hoy.getFullYear();
    render(this.value);
  });
});
