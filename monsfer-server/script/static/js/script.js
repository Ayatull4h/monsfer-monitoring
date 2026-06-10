// Theme toggle function
function toggleTheme() {
    const html = document.documentElement;
    const themeButton = document.querySelector('.theme-toggle i');
    
    if (html.getAttribute('data-bs-theme') === 'dark') {
        html.setAttribute('data-bs-theme', 'light');
        themeButton.classList.remove('bi-sun-fill');
        themeButton.classList.add('bi-moon-fill');
        document.cookie = "theme=light; path=/; max-age=31536000"; // Save for 1 year
    } else {
        html.setAttribute('data-bs-theme', 'dark');
        themeButton.classList.remove('bi-moon-fill');
        themeButton.classList.add('bi-sun-fill');
        document.cookie = "theme=dark; path=/; max-age=31536000"; // Save for 1 year
    }
}

// Function to get cookie value
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Set initial theme based on cookie
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = getCookie('theme');
    const html = document.documentElement;
    const themeButton = document.querySelector('.theme-toggle i');
    
    if (savedTheme === 'dark') {
        html.setAttribute('data-bs-theme', 'dark');
        themeButton.classList.remove('bi-moon-fill');
        themeButton.classList.add('bi-sun-fill');
    } else {
        html.setAttribute('data-bs-theme', 'light');
        themeButton.classList.remove('bi-sun-fill');
        themeButton.classList.add('bi-moon-fill');
    }
});

// Admin settings update function
function updateAdminSettings() {
    const formData = {
        username: document.getElementById('admin_username').value,
        password: document.getElementById('admin_password').value,
        fullname: document.getElementById('admin_fullname').value
    };

    fetch('/api/admin/settings', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating admin settings');
    });
}

// UPT Operations
function submitAddUpt() {
    const formData = {
        id_upt: document.getElementById('id_upt').value,
        fullname: document.getElementById('fullname').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
    };

    fetch('/api/upts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding the UPT');
    });
}

function editUpt(id_upt, fullname, username, password) {
    document.getElementById('edit_id_upt').value = id_upt;
    document.getElementById('edit_fullname').value = fullname;
    document.getElementById('edit_username').value = username;
    document.getElementById('edit_password').value = password;
    new bootstrap.Modal(document.getElementById('editUptModal')).show();
}

function submitEditUpt() {
    const id_upt = document.getElementById('edit_id_upt').value;
    const formData = {
        fullname: document.getElementById('edit_fullname').value,
        username: document.getElementById('edit_username').value,
        password: document.getElementById('edit_password').value
    };

    fetch(`/api/upts/${id_upt}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the UPT');
    });
}

function deleteUpt(id_upt) {
    if (confirm('Are you sure you want to delete this UPT?')) {
        fetch(`/api/upts/${id_upt}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the UPT');
        });
    }
}

// Site Operations
function showAddSiteModal(id_upt) {
    document.getElementById('site_upt_id').value = id_upt;
    new bootstrap.Modal(document.getElementById('addSiteModal')).show();
}

function submitAddSite() {
    const id_upt = document.getElementById('site_upt_id').value;
    const formData = {
        id_perangkat: document.getElementById('id_perangkat').value,
        site_name: document.getElementById('site_name').value,
        token: document.getElementById('token').value
    };

    fetch(`/api/upts/${id_upt}/sites`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding the site');
    });
}

function editSite(id_upt, id_perangkat, site_name, token) {
    document.getElementById('edit_site_upt_id').value = id_upt;
    document.getElementById('edit_id_perangkat').value = id_perangkat;
    document.getElementById('edit_site_name').value = site_name;
    document.getElementById('edit_token').value = token;
    new bootstrap.Modal(document.getElementById('editSiteModal')).show();
}

function submitEditSite() {
    const id_upt = document.getElementById('edit_site_upt_id').value;
    const id_perangkat = document.getElementById('edit_id_perangkat').value;
    const formData = {
        site_name: document.getElementById('edit_site_name').value,
        token: document.getElementById('edit_token').value
    };

    fetch(`/api/upts/${id_upt}/sites/${id_perangkat}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the site');
    });
}

function deleteSite(id_upt, id_perangkat) {
    if (confirm('Are you sure you want to delete this site?')) {
        fetch(`/api/upts/${id_upt}/sites/${id_perangkat}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the site');
        });
    }
}

// Token toggle function
function toggleToken(button) {
    const tokenText = button.parentElement.querySelector('.token-text');
    const icon = button.querySelector('i');
    
    if (tokenText.style.display === 'none') {
        tokenText.style.display = 'inline';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        tokenText.style.display = 'none';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}

// Save folders function
function saveFolders() {
    const toast = document.getElementById('verifyToast');
    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header');
    const toastIcon = toast.querySelector('.bi');
    
    // Show loading state
    toastHeader.classList.remove('bg-success', 'bg-danger', 'text-white');
    toastIcon.classList.remove('bi-check-circle', 'bi-exclamation-circle');
    toastIcon.classList.add('bi-arrow-repeat', 'spinner-border', 'spinner-border-sm');
    toastBody.innerHTML = '<div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm me-2" role="status"></div>Verifying and updating database...</div>';
    
    const bsToast = new bootstrap.Toast(toast, {
        delay: 5000  // Show for 5 seconds
    });
    bsToast.show();

    fetch('/api/verify-database', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading state
        toastIcon.classList.remove('bi-arrow-repeat', 'spinner-border', 'spinner-border-sm');
        
        if (data.error) {
            toastHeader.classList.remove('bg-success');
            toastHeader.classList.add('bg-danger', 'text-white');
            toastIcon.classList.add('bi-exclamation-circle');
            toastBody.textContent = data.error;
        } else {
            toastHeader.classList.remove('bg-danger');
            toastHeader.classList.add('bg-success', 'text-white');
            toastIcon.classList.add('bi-check-circle');
            
            let message = 'Database verification complete.';
            if (data.updated_sites && data.updated_sites.length > 0) {
                message += `<br><br>Updated ${data.updated_sites.length} site IDs to 3 digits:`;
                message += `<div class="small mt-2">${data.updated_sites.map(site => 
                    `<div>${site.old_id} → ${site.new_id}</div>`
                ).join('')}</div>`;
            }
            
            if (data.created_folders && data.created_folders.length > 0) {
                message += `<br><br>Created ${data.created_folders.length} new folders:`;
                message += `<div class="small mt-2">${data.created_folders.map(folder => 
                    `<div>${folder}</div>`
                ).join('')}</div>`;
            }
            
            toastBody.innerHTML = message;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Remove loading state
        toastIcon.classList.remove('bi-arrow-repeat', 'spinner-border', 'spinner-border-sm');
        
        toastHeader.classList.remove('bg-success');
        toastHeader.classList.add('bg-danger', 'text-white');
        toastIcon.classList.add('bi-exclamation-circle');
        toastBody.textContent = 'An error occurred while verifying the database';
    });
}

function checkFolders() {
    fetch('/api/verify-folders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const folderStatus = document.getElementById('folderStatus');
        folderStatus.innerHTML = '';
        
        if (data.message) {
            const lines = data.message.split('\n');
            lines.forEach(line => {
                if (line.trim()) {
                    const item = document.createElement('div');
                    item.className = 'list-group-item';
                    item.innerHTML = `<i class="bi bi-folder me-2"></i>${line}`;
                    folderStatus.appendChild(item);
                }
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function checkErrors() {
    fetch('/api/system/errors', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const errorList = document.getElementById('errorList');
        errorList.innerHTML = '';
        
        if (data.errors && data.errors.length > 0) {
            data.errors.forEach(error => {
                const item = document.createElement('div');
                item.className = 'list-group-item list-group-item-warning';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-exclamation-triangle-fill me-2 text-warning"></i>
                            <strong class="text-warning">${error.type}</strong>
                        </div>
                        <small class="text-muted">${error.timestamp}</small>
                    </div>
                    <p class="mb-0 mt-2 text-warning">${error.message}</p>
                `;
                errorList.appendChild(item);
            });
        } else {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-success';
            item.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Tidak ada peringatan sistem';
            errorList.appendChild(item);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const errorList = document.getElementById('errorList');
        errorList.innerHTML = `
            <div class="list-group-item list-group-item-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Gagal memuat peringatan sistem
            </div>
        `;
    });
}

function checkOrphaned() {
    fetch('/api/system/orphaned', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const orphanedList = document.getElementById('orphanedList');
        orphanedList.innerHTML = '';
        
        if (data.orphaned && data.orphaned.length > 0) {
            data.orphaned.forEach(folder => {
                const item = document.createElement('div');
                item.className = 'list-group-item list-group-item-warning';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-folder-x me-2"></i>
                            <strong>${folder.path}</strong>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="deleteOrphaned('${folder.path}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                `;
                orphanedList.appendChild(item);
            });
        } else {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.innerHTML = '<i class="bi bi-check-circle me-2"></i>No orphaned folders found';
            orphanedList.appendChild(item);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function deleteOrphaned(path) {
    if (confirm(`Are you sure you want to delete ${path}?`)) {
        fetch('/api/system/orphaned', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                checkOrphaned();
            } else {
                alert('Failed to delete folder');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete folder');
        });
    }
}

// Add event listener for system info modal
document.getElementById('systemInfoModal').addEventListener('show.bs.modal', function () {
    // Load initial data when modal opens
    checkFolders();
});

// Add these functions to your existing script
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (window.innerWidth <= 768) {
        // Mobile view
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
        
        if (sidebar.classList.contains('show')) {
            sidebarToggle.style.display = 'none';
        } else {
            sidebarToggle.style.display = 'inline-flex';
        }
    } else {
        // Desktop view
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (window.innerWidth <= 768 && 
        !sidebar.contains(event.target) && 
        !sidebarToggle.contains(event.target) &&
        sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        sidebarToggle.style.display = 'inline-flex';
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (window.innerWidth > 768) {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        sidebarToggle.style.display = 'inline-flex';
        if (!sidebar.classList.contains('collapsed')) {
            mainContent.classList.remove('expanded');
        }
    }
});

// Add this to your existing script
document.getElementById('uptSearch').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const uptCards = document.querySelectorAll('.upt-card');
    
    uptCards.forEach(card => {
        const title = card.querySelector('.card-title').textContent.toLowerCase();
        const id = card.querySelector('.text-muted').textContent.toLowerCase();
        const username = card.querySelector('.card-text').textContent.toLowerCase();
        const siteNames = Array.from(card.querySelectorAll('.list-group-item strong')).map(el => el.textContent.toLowerCase());
        
        if (title.includes(searchTerm) || 
            id.includes(searchTerm) || 
            username.includes(searchTerm) ||
            siteNames.some(site => site.includes(searchTerm))) {
            card.closest('.col').style.display = '';
        } else {
            card.closest('.col').style.display = 'none';
        }
    });
});

// Content switching function
function showContent(contentId) {
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show the selected content
    document.getElementById(contentId + 'Content').style.display = 'block';
    
    // Update active state in sidebar
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Close sidebar on mobile after selection
    if (window.innerWidth <= 768) {
        toggleSidebar();
    }
}