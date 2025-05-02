/**
 * Main JavaScript File for Remote Hive
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Bootstrap tooltips initialization
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Flash message auto-dismiss after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Smooth scrolling for internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add animation to hero section elements
    const heroElements = document.querySelectorAll('.hero-section h1, .hero-section p, .search-box');
    heroElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('animate-fadeInUp');
        }, index * 200);
    });
    
    // Sticky navigation on scroll
    const navbar = document.querySelector('nav.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('shadow-sm');
            } else {
                navbar.classList.remove('shadow-sm');
            }
        });
    }
    
    // Search form validation
    const searchForms = document.querySelectorAll('form[action*="search"]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const queryInput = this.querySelector('input[name="query"]');
            if (queryInput && queryInput.value.trim() === '') {
                e.preventDefault();
                queryInput.classList.add('is-invalid');
                
                // Create error message if it doesn't exist
                let errorMsg = this.querySelector('.search-error-message');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'invalid-feedback search-error-message';
                    errorMsg.textContent = 'Please enter a search term.';
                    queryInput.parentNode.appendChild(errorMsg);
                }
                
                // Remove invalid class when user starts typing
                queryInput.addEventListener('input', function() {
                    if (this.value.trim() !== '') {
                        this.classList.remove('is-invalid');
                    }
                });
            }
        });
    });
    
    // Job filtering functionality
    const filterCheckboxes = document.querySelectorAll('.filter-checkbox');
    if (filterCheckboxes.length > 0) {
        filterCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', applyFilters);
        });
        
        function applyFilters() {
            const jobCards = document.querySelectorAll('.job-card');
            if (jobCards.length === 0) return;
            
            // Get selected filters
            const selectedExperience = Array.from(document.querySelectorAll('input[id^="exp"]:checked')).map(el => el.value);
            const selectedJobTypes = Array.from(document.querySelectorAll('input[id^="type"]:checked')).map(el => el.value);
            const selectedSalaryRanges = Array.from(document.querySelectorAll('input[id^="sal"]:checked')).map(el => el.value);
            const remoteOnly = document.getElementById('remoteFilter')?.checked || false;
            
            // If no filters are selected, show all jobs
            if (selectedExperience.length === 0 && selectedJobTypes.length === 0 && 
                selectedSalaryRanges.length === 0 && !remoteOnly) {
                jobCards.forEach(card => {
                    card.style.display = '';
                });
                return;
            }
            
            // Otherwise, filter jobs
            jobCards.forEach(card => {
                const jobType = card.querySelector('.badge').textContent;
                const isRemote = card.textContent.includes('Remote');
                const experienceText = card.querySelector('.job-details').textContent;
                const salaryText = card.querySelector('.job-details').textContent;
                
                // Check if job matches all selected filters
                const matchesJobType = selectedJobTypes.length === 0 || selectedJobTypes.includes(jobType);
                const matchesRemote = !remoteOnly || isRemote;
                
                // Simple check for experience (would be more sophisticated in a real app)
                const matchesExperience = selectedExperience.length === 0 || 
                    selectedExperience.some(exp => experienceText.includes(exp));
                
                // Simple check for salary range (would be more sophisticated in a real app)
                const matchesSalary = selectedSalaryRanges.length === 0 ||
                    selectedSalaryRanges.some(range => salaryText.includes(range));
                
                if (matchesJobType && matchesRemote && matchesExperience && matchesSalary) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    }
    
    // Company rating stars hover effect
    const ratingStars = document.querySelectorAll('.rating-select .form-select');
    ratingStars.forEach(select => {
        select.addEventListener('change', function() {
            const stars = this.closest('.rating-select').querySelectorAll('.star');
            const rating = parseInt(this.value);
            
            stars.forEach((star, index) => {
                if (index < rating) {
                    star.classList.add('filled');
                } else {
                    star.classList.remove('filled');
                }
            });
        });
    });
    
    // Save job functionality (frontend only, would connect to backend in a real app)
    const saveButtons = document.querySelectorAll('.save-job-btn');
    saveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            const icon = this.querySelector('i');
            
            if (icon.classList.contains('far')) {
                icon.classList.replace('far', 'fas');
                this.textContent = ' Saved';
                this.prepend(icon);
                this.classList.add('btn-secondary');
                this.classList.remove('btn-outline-secondary');
            } else {
                icon.classList.replace('fas', 'far');
                this.textContent = ' Save';
                this.prepend(icon);
                this.classList.remove('btn-secondary');
                this.classList.add('btn-outline-secondary');
            }
            
            // This would make an AJAX call to the server in a real application
            console.log('Toggle saved state for job ID:', jobId);
        });
    });
    
    // Mobile menu improvements
    const mobileNav = document.querySelector('.navbar-collapse');
    if (mobileNav) {
        document.addEventListener('click', function(e) {
            // Close mobile menu when clicking outside
            if (mobileNav.classList.contains('show') && 
                !mobileNav.contains(e.target) && 
                !e.target.classList.contains('navbar-toggler')) {
                const bsCollapse = new bootstrap.Collapse(mobileNav);
                bsCollapse.hide();
            }
        });
    }
    
    // File input display filename
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const fileNameDisplay = document.createElement('div');
                fileNameDisplay.className = 'selected-file mt-2 small text-muted';
                fileNameDisplay.textContent = `Selected file: ${fileName}`;
                
                // Remove any existing filename display
                const existingDisplay = this.parentNode.querySelector('.selected-file');
                if (existingDisplay) {
                    existingDisplay.remove();
                }
                
                this.parentNode.appendChild(fileNameDisplay);
            }
        });
    });

    // Trigger search on Enter key press in search input
    const searchInputs = document.querySelectorAll('input[name="query"]');
    searchInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const form = this.closest('form');
                if (form) {
                    form.submit();
                }
            }
        });
    });
});
