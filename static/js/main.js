document.addEventListener('DOMContentLoaded', function () {

    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(el => new bootstrap.Tooltip(el));

    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 6000);

    window.confirmar = function (mensaje) {
        return confirm(mensaje || '¿Estás seguro?');
    };

    document.querySelectorAll('.fila-link').forEach(function (fila) {
        fila.addEventListener('click', function () {
            window.location = this.dataset.href;
        });
    });

    document.querySelectorAll('.table-clickable tbody tr').forEach(function (row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function () {
            const link = this.querySelector('a[href]');
            if (link) window.location = link.getAttribute('href');
        });
    });

});
