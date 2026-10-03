/* gestion_reserva_form.js — Formulario de crear/editar reserva del panel de gestión */
document.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('.form-gestion');
  if (!form) return;

  // ── Búsqueda de cliente por documento (solo al crear) ──
  // Al editar no se busca: bloquearía los campos y no dejaría corregir al cliente.
  var docInput = document.querySelector('input[name="documento"]');
  if (form.dataset.modo === 'crear' && docInput) {
    var buscarClienteUrl = form.dataset.buscarClienteUrl;
    var nombreInput      = document.querySelector('input[name="nombre"]');
    var telefonoInput    = document.querySelector('input[name="telefono"]');

    function buscarCliente(documento) {
      if (!documento || documento.length < 3) return;

      fetch(buscarClienteUrl + '?documento=' + encodeURIComponent(documento))
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.encontrado) {
            var c = data.cliente;
            nombreInput.value   = c.nombre;
            telefonoInput.value = c.telefono;
            [nombreInput, telefonoInput].forEach(function(el) {
              el.setAttribute('readonly', 'readonly');
              el.style.backgroundColor = '#E6F1FB';
            });
          } else {
            [nombreInput, telefonoInput].forEach(function(el) {
              el.removeAttribute('readonly');
              el.style.backgroundColor = '';
            });
          }
        })
        .catch(function() {});
    }

    docInput.addEventListener('blur', function() {
      buscarCliente(docInput.value.trim());
    });

    docInput.addEventListener('change', function() {
      buscarCliente(docInput.value.trim());
    });
  }

  // ── Plan personalizado y precio del plan ──
  var planCheckbox    = document.getElementById('plan_personalizado');
  var planFields      = document.getElementById('plan_personalizado_fields');
  var tarifaSelect    = document.getElementById('tarifa_select');
  var precioPlanInput = document.getElementById('precio_plan');

  // Copia el precio de la tarifa al precio del plan (solo si NO es plan personalizado)
  function autoFillPrecioPlan() {
    if (!tarifaSelect || !precioPlanInput) return;
    if (planCheckbox && planCheckbox.checked) return;
    var selected = tarifaSelect.options[tarifaSelect.selectedIndex];
    if (selected && selected.dataset.precio) {
      precioPlanInput.value = selected.dataset.precio;
    }
  }

  if (planCheckbox && planFields) {
    planCheckbox.addEventListener('change', function() {
      planFields.style.display = this.checked ? 'flex' : 'none';
      // Al quitar el plan personalizado, el precio vuelve al de la tarifa
      if (!this.checked) autoFillPrecioPlan();
    });
  }

  if (tarifaSelect) {
    tarifaSelect.addEventListener('change', autoFillPrecioPlan);
  }

  // Al cargar solo se completa si está vacío: así no se pisa el precio
  // guardado de una reserva que se está editando.
  if (precioPlanInput && !precioPlanInput.value) {
    autoFillPrecioPlan();
  }

  // ── Fechas: los planes de día de sol permiten entrada y salida el mismo día
  var fechaInicioInput = document.querySelector('input[name="fecha_inicio"]');
  var fechaFinInput    = document.querySelector('input[name="fecha_fin"]');

  function sumarDias(fechaStr, dias) {
    var partes = fechaStr.split('-');
    var d = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    d.setDate(d.getDate() + dias);
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + mm + '-' + dd;
  }

  function actualizarMinFechaFin() {
    if (!fechaInicioInput.value) {
      fechaFinInput.removeAttribute('min');
      return;
    }
    var selected = tarifaSelect.options[tarifaSelect.selectedIndex];
    var diaDeSol = selected && selected.dataset.diaSol === '1';
    fechaFinInput.min = sumarDias(fechaInicioInput.value, diaDeSol ? 0 : 1);
  }

  if (fechaInicioInput && fechaFinInput && tarifaSelect) {
    fechaInicioInput.addEventListener('change', actualizarMinFechaFin);
    tarifaSelect.addEventListener('change', actualizarMinFechaFin);
    actualizarMinFechaFin();
  }
});
