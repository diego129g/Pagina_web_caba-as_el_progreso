document.addEventListener('DOMContentLoaded', () => {
    const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || getCookie('csrftoken');

    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (const c of cookies) {
            const [key, val] = c.trim().split('=');
            if (key === name) return decodeURIComponent(val);
        }
        return '';
    }

    function enviarAjax(url, data) {
        const formData = data instanceof FormData ? data : new URLSearchParams(data);
        return fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            body: formData,
        }).then(r => r.json());
    }

    function crearNodoComentario(c) {
        const div = document.createElement('div');
        div.className = 'comentario' + (c.es_respuesta ? ' comentario--respuesta' : '');
        div.dataset.id = c.id;

        const inicial = c.nombre.charAt(0).toUpperCase();
        div.innerHTML = `
            <div class="comentario__header">
                <div class="comentario__avatar${c.es_respuesta ? ' comentario__avatar--sm' : ''}">${inicial}</div>
                <div class="comentario__meta">
                    <span class="comentario__nombre">${c.nombre}</span>
                    <span class="comentario__fecha">${c.creado_at}</span>
                </div>
                ${c.puede_eliminar ? `<button class="comentario__btn-eliminar" data-id="${c.id}" title="Eliminar comentario">✕</button>` : ''}
            </div>
            <p class="comentario__texto">${c.texto}</p>
            ${!c.es_respuesta ? `
            <div class="comentario__acciones">
                <button class="comentario__btn-responder" data-id="${c.id}">Responder</button>
            </div>
            <div class="comentario-form-respuesta" id="respuesta-form-${c.id}" style="display:none;">
                <input type="text" class="comentario-form__input" placeholder="Tu nombre" maxlength="100">
                <input type="email" class="comentario-form__input" placeholder="Tu correo electrónico">
                <textarea class="comentario-form__textarea" placeholder="Escribe tu respuesta..." maxlength="1000" rows="3"></textarea>
                <div class="comentario-form__acciones">
                    <button class="btn btn--primary btn--sm comentario__btn-enviar-respuesta" data-parent="${c.id}">Enviar respuesta</button>
                    <button class="btn btn--outline btn--sm comentario__btn-cancelar-respuesta" data-parent="${c.id}">Cancelar</button>
                </div>
            </div>` : ''}
        `;
        return div;
    }

    function insertarComentario(nodo, parentId) {
        const lista = document.getElementById('comentarios-lista');
        const vacios = document.getElementById('comentarios-vacios');
        if (vacios) vacios.remove();

        if (nodo.classList.contains('comentario--respuesta') && parentId) {
            const padreNodo = lista.querySelector(`.comentario[data-id="${parentId}"]`);
            if (padreNodo) {
                padreNodo.appendChild(nodo);
                return;
            }
            lista.appendChild(nodo);
        } else {
            lista.prepend(nodo);
        }
    }

    // ── Nuevo comentario ──
    document.getElementById('comentario-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type=submit]');
        btn.disabled = true;

        const data = new FormData(form);
        try {
            const res = await enviarAjax(form.dataset.url || window.location.href, data);
            if (res.ok) {
                const nodo = crearNodoComentario(res.comentario);
                insertarComentario(nodo);
                form.reset();
            } else {
                alert('Error al publicar. Revisa los datos e intenta de nuevo.');
            }
        } catch {
            alert('Error de conexión. Intenta de nuevo.');
        }
        btn.disabled = false;
    });

    // ── Event delegation para acciones ──
    document.getElementById('comentarios-lista')?.addEventListener('click', async (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;

        // Responder
        if (btn.classList.contains('comentario__btn-responder')) {
            const id = btn.dataset.id;
            const form = document.getElementById(`respuesta-form-${id}`);
            if (form) {
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
            }
            return;
        }

        // Cancelar respuesta
        if (btn.classList.contains('comentario__btn-cancelar-respuesta')) {
            const id = btn.dataset.parent;
            const form = document.getElementById(`respuesta-form-${id}`);
            if (form) {
                form.style.display = 'none';
                form.querySelectorAll('input, textarea').forEach(el => el.value = '');
            }
            return;
        }

        // Enviar respuesta
        if (btn.classList.contains('comentario__btn-enviar-respuesta')) {
            const parentId = btn.dataset.parent;
            const form = document.getElementById(`respuesta-form-${parentId}`);
            if (!form) return;

            const inputs = form.querySelectorAll('input, textarea');
            const nombre = inputs[0].value.trim();
            const correo = inputs[1].value.trim();
            const texto = inputs[2].value.trim();

            if (!nombre || !correo || !texto) {
                alert('Por favor completa todos los campos.');
                return;
            }

            btn.disabled = true;
            const data = new FormData();
            data.append('nombre', nombre);
            data.append('correo', correo);
            data.append('texto', texto);

            try {
                const res = await enviarAjax(`/experiencias/comentario/${parentId}/responder/`, data);
                if (res.ok) {
                    const nodo = crearNodoComentario(res.comentario);
                    insertarComentario(nodo, parentId);
                    form.style.display = 'none';
                    form.querySelectorAll('input, textarea').forEach(el => el.value = '');
                } else {
                    alert('Error al responder. Intenta de nuevo.');
                }
            } catch {
                alert('Error de conexión. Intenta de nuevo.');
            }
            btn.disabled = false;
            return;
        }

        // Eliminar
        if (btn.classList.contains('comentario__btn-eliminar')) {
            if (!confirm('¿Estás seguro de que quieres eliminar este comentario?')) return;

            const id = btn.dataset.id;
            try {
                const res = await enviarAjax(`/experiencias/comentario/${id}/eliminar/`, {});
                if (res.ok) {
                    const nodo = document.querySelector(`.comentario[data-id="${id}"]`);
                    if (nodo) {
                        // Si es un comentario raíz, eliminar también sus respuestas visibles
                        if (!nodo.classList.contains('comentario--respuesta')) {
                            nodo.querySelectorAll('.comentario--respuesta').forEach(r => r.remove());
                        }
                        nodo.remove();
                    }
                    // Si no quedan comentarios, mostrar mensaje
                    const lista = document.getElementById('comentarios-lista');
                    if (lista && !lista.querySelector('.comentario')) {
                        const p = document.createElement('p');
                        p.className = 'comentarios-vacios';
                        p.id = 'comentarios-vacios';
                        p.textContent = 'Sé el primero en dejar tu comentario sobre tu experiencia en Cabañas El Progreso.';
                        lista.appendChild(p);
                    }
                } else {
                    alert(res.error || 'No se pudo eliminar el comentario.');
                }
            } catch {
                alert('Error de conexión. Intenta de nuevo.');
            }
        }
    });
});
