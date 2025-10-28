// Simple JavaScript for enhanced interactivity

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to elements
    const elements = document.querySelectorAll('.feature-card, .login-card, .admin-section');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('fade-in');
        }, index * 100);
    });

    // Enhanced form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], select[required]');
            let isValid = true;

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'error');
            }
        });
    });

    // Password strength indicator (optional enhancement)
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            const strength = calculatePasswordStrength(this.value);
            updatePasswordStrengthIndicator(this, strength);
        });
    });
});

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
}

function updatePasswordStrengthIndicator(input, strength) {
    let existingIndicator = input.parentNode.querySelector('.password-strength');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    if (input.value.length > 0) {
        const indicator = document.createElement('div');
        indicator.className = 'password-strength mt-1';
        
        let strengthText = '';
        let strengthClass = '';
        
        switch (strength) {
            case 0-1:
                strengthText = 'Very Weak';
                strengthClass = 'text-danger';
                break;
            case 2:
                strengthText = 'Weak';
                strengthClass = 'text-warning';
                break;
            case 3:
                strengthText = 'Medium';
                strengthClass = 'text-info';
                break;
            case 4:
                strengthText = 'Strong';
                strengthClass = 'text-success';
                break;
            case 5:
                strengthText = 'Very Strong';
                strengthClass = 'text-success fw-bold';
                break;
        }
        
        indicator.innerHTML = `<small class="${strengthClass}">Password Strength: ${strengthText}</small>`;
        input.parentNode.appendChild(indicator);
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Enhanced table interactions
function initializeTableInteractions() {
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('click', function(e) {
            if (!e.target.closest('button')) {
                // Add selection highlight
                tableRows.forEach(r => r.classList.remove('table-active'));
                this.classList.add('table-active');
            }
        });
    });
}

// Initialize table interactions when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTableInteractions);

// Form auto-save functionality (for admin forms)
function initializeAutoSave() {
    const forms = document.querySelectorAll('form');
    forms.forEach((form, formIndex) => {
        // Only auto-save forms that have an explicit id to avoid clobbering
        // values across multiple identical unnamed forms (e.g. enroll forms).
        if (!form.id) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                // Save to localStorage with form ID and input name
                const formId = form.id;
                const key = `${formId}-${this.name}`;
                if (this.type !== 'password') {
                    localStorage.setItem(key, this.value);
                }
            });
        });
    });
}

// Load saved form data
function loadAutoSavedData() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Only load saved data for forms that have an explicit id
        if (!form.id) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type !== 'password') {
                const formId = form.id;
                const key = `${formId}-${input.name}`;
                const savedValue = localStorage.getItem(key);
                if (savedValue) {
                    input.value = savedValue;
                }
            }
        });
    });
}

// Clear auto-saved data on successful form submission
function clearAutoSavedData(formId) {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(`${formId}-`)) {
            localStorage.removeItem(key);
        }
    });
}

// Initialize auto-save functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAutoSave();
    loadAutoSavedData();
});