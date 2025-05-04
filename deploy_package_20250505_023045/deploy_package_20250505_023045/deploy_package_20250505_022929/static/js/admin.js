/**
 * Admin Panel JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Toggle sidebar on mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-toggled');
            document.querySelector('.admin-sidebar').classList.toggle('toggled');
        });
    }

    // Close any open menu accordions when window is resized
    window.addEventListener('resize', function() {
        const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        if (vw < 768) {
            document.querySelectorAll('.admin-sidebar .collapse').forEach(function(collapse) {
                collapse.classList.remove('show');
            });
        }
    });

    // Prevent the content wrapper from scrolling when the fixed side navigation hovered over
    document.querySelector('.admin-sidebar').addEventListener('mousewheel', function(e) {
        if (this.classList.contains('fixed-sidebar')) {
            e.preventDefault();
        }
    });

    // Enable data tables if present
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            responsive: true
        });
    }

    // Enable date pickers if present
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.datepicker', {
            enableTime: false,
            dateFormat: 'Y-m-d'
        });
    }

    // Enable select2 if present
    if (typeof $.fn.select2 !== 'undefined') {
        $('.select2').select2({
            theme: 'bootstrap4'
        });
    }

    // Enable CKEditor if present
    if (typeof ClassicEditor !== 'undefined') {
        document.querySelectorAll('.ckeditor').forEach(function(element) {
            ClassicEditor.create(element).catch(error => {
                console.error(error);
            });
        });
    }

    // Handle form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Handle file input display
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0].name;
            const label = this.nextElementSibling;
            label.textContent = fileName;
        });
    });

    // Handle confirmation dialogs
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});
