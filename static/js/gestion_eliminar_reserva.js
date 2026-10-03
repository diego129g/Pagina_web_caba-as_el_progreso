/* gestion_eliminar_reserva.js — Confirmación para eliminar reservas desde el listado del panel de gestión */
document.addEventListener('DOMContentLoaded', function () {
  var dialogo = document.getElementById('dialogo-eliminar');
  var form    = document.getElementById('form-eliminar');

  if (!dialogo || !form) return;

  document.querySelectorAll('.js-eliminar-reserva').forEach(function(boton) {
    boton.addEventListener('click', function() {
      form.action = boton.dataset.url;
      dialogo.querySelector('[data-campo="id"]').textContent     = '#' + boton.dataset.id;
      dialogo.querySelector('[data-campo="cliente"]').textContent = boton.dataset.cliente;
      dialogo.querySelector('[data-campo="cabana"]').textContent  = boton.dataset.cabana;
      dialogo.querySelector('[data-campo="fechas"]').textContent  = boton.dataset.fechas;
      dialogo.showModal();
    });
  });

  dialogo.querySelector('[data-cerrar]').addEventListener('click', function() {
    dialogo.close();
  });

  // Cerrar al hacer clic fuera del cuadro
  dialogo.addEventListener('click', function(e) {
    if (e.target === dialogo) dialogo.close();
  });

  // Evitar doble envío
  form.addEventListener('submit', function() {
    form.querySelector('button[type="submit"]').disabled = true;
  });
});
