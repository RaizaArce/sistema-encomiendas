document.addEventListener('DOMContentLoaded', function () {

    // ── Inicializar tooltips de Bootstrap ──────────────────────────
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(el => new bootstrap.Tooltip(el));

    // ── Auto-cerrar alertas flash despues de 5 segundos ────────────
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);

    // ── Confirmacion antes de eliminar ────────────────────────────
    window.confirmar = function (mensaje) {
        return confirm(mensaje || '¿Estas seguro?');
    };

    // ── Resaltar fila al hacer clic ───────────────────────────────
    document.querySelectorAll('.fila-link').forEach(function (fila) {
        fila.addEventListener('click', function () {
            window.location = this.dataset.href;
        });
    });

});
