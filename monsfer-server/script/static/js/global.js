// Global utility functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    document.querySelector('.container-fluid').prepend(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

// Initialize DataTables
function initDataTable(tableId, options = {}) {
    const defaultOptions = {
        responsive: true,
        language: {
            search: "Search:",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)"
        }
    };
    return $(`#${tableId}`).DataTable({...defaultOptions, ...options});
}

// Format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Handle form submissions
function handleFormSubmit(formId, successCallback) {
    $(`#${formId}`).on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        $.ajax({
            url: $(this).attr('action'),
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                showAlert(response.message || 'Operation successful');
                if (successCallback) successCallback(response);
            },
            error: function(xhr) {
                showAlert(xhr.responseJSON?.message || 'An error occurred', 'danger');
            }
        });
    });
}

// Initialize tooltips
function initTooltips() {
    $('[data-toggle="tooltip"]').tooltip();
}

// Initialize popovers
function initPopovers() {
    $('[data-toggle="popover"]').popover();
}

// Handle modal forms
function handleModalForm(modalId, formId, successCallback) {
    $(`#${modalId}`).on('hidden.bs.modal', function() {
        $(`#${formId}`)[0].reset();
    });
    
    handleFormSubmit(formId, function(response) {
        $(`#${modalId}`).modal('hide');
        if (successCallback) successCallback(response);
    });
}

// Initialize all common features
$(document).ready(function() {
    initTooltips();
    initPopovers();
    
    // Handle CSRF token for AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", $('meta[name="csrf-token"]').attr('content'));
            }
        }
    });
}); 