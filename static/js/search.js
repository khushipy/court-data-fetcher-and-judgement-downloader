// Search Form Handling
document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const form = document.getElementById('multiStepForm');
    const steps = document.querySelectorAll('.step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('searchProgress');
    const stateSelect = document.getElementById('state');
    const courtTypeSelect = document.getElementById('courtType');
    const districtSelect = document.getElementById('district');
    const caseTypeSelect = document.getElementById('caseType');
    const captchaImage = document.getElementById('captchaImage');
    const refreshCaptchaBtn = document.getElementById('refreshCaptcha');
    
    let currentStep = 1;
    let captchaText = '';
    
    // Initialize the form
    function initForm() {
        updateProgressBar();
        updateButtons();
        loadDistricts();
        loadCaseTypes();
        initCaptcha();
        
        // Event listeners
        prevBtn.addEventListener('click', prevStep);
        nextBtn.addEventListener('click', nextStep);
        form.addEventListener('submit', handleSubmit);
        stateSelect.addEventListener('change', loadDistricts);
        refreshCaptchaBtn.addEventListener('click', initCaptcha);
    }
    
    // Update progress bar
    function updateProgressBar() {
        const progress = (currentStep / steps.length) * 100;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        
        // Update step indicators
        document.querySelectorAll('.step-indicator').forEach((indicator, index) => {
            if (index + 1 < currentStep) {
                indicator.classList.add('completed');
                indicator.classList.remove('active');
            } else if (index + 1 === currentStep) {
                indicator.classList.add('active');
                indicator.classList.remove('completed');
            } else {
                indicator.classList.remove('active', 'completed');
            }
        });
    }
    
    // Update navigation buttons
    function updateButtons() {
        // Show/hide previous button
        if (currentStep === 1) {
            prevBtn.style.display = 'none';
        } else {
            prevBtn.style.display = 'block';
        }
        
        // Update next/submit button
        if (currentStep === steps.length) {
            nextBtn.classList.add('d-none');
            submitBtn.classList.remove('d-none');
        } else {
            nextBtn.classList.remove('d-none');
            submitBtn.classList.add('d-none');
        }
    }
    
    // Go to next step
    function nextStep() {
        if (validateStep(currentStep)) {
            // Hide current step
            document.getElementById(`step${currentStep}`).classList.add('d-none');
            
            // Show next step
            currentStep++;
            document.getElementById(`step${currentStep}`).classList.remove('d-none');
            
            // Update UI
            updateProgressBar();
            updateButtons();
            
            // Load data for next step if needed
            if (currentStep === 5) {
                initCaptcha();
            }
        }
    }
    
    // Go to previous step
    function prevStep() {
        // Hide current step
        document.getElementById(`step${currentStep}`).classList.add('d-none');
        
        // Show previous step
        currentStep--;
        document.getElementById(`step${currentStep}`).classList.remove('d-none');
        
        // Update UI
        updateProgressBar();
        updateButtons();
    }
    
    // Validate current step
    function validateStep(step) {
        let isValid = true;
        const currentStepElement = document.getElementById(`step${step}`);
        
        // Get all required fields in current step
        const requiredFields = currentStepElement.querySelectorAll('[required]');
        
        // Check each required field
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                
                // Additional validation for specific fields
                if (field.id === 'year') {
                    const year = parseInt(field.value);
                    if (year < 1900 || year > new Date().getFullYear() + 1) {
                        field.classList.add('is-invalid');
                        field.nextElementSibling.textContent = 'Please enter a valid year';
                        isValid = false;
                    }
                }
            }
        });
        
        return isValid;
    }
    
    // Load districts based on selected state
    async function loadDistricts() {
        const state = stateSelect.value;
        if (!state) return;
        
        districtSelect.disabled = true;
        districtSelect.innerHTML = '<option value="" selected disabled>Loading districts...</option>';
        
        try {
            const response = await fetch(`/api/districts/${state}`);
            const data = await response.json();
            
            if (data.success && data.districts.length > 0) {
                districtSelect.innerHTML = '<option value="" selected disabled>Select District</option>';
                data.districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district.toLowerCase().replace(/\s+/g, '_');
                    option.textContent = district;
                    districtSelect.appendChild(option);
                });
                districtSelect.disabled = false;
            } else {
                districtSelect.innerHTML = '<option value="" selected disabled>No districts found</option>';
            }
        } catch (error) {
            console.error('Error loading districts:', error);
            showError('Failed to load districts. Please try again.');
            districtSelect.innerHTML = '<option value="" selected disabled>Error loading districts</option>';
        }
    }
    
    // Load case types
    async function loadCaseTypes() {
        caseTypeSelect.disabled = true;
        caseTypeSelect.innerHTML = '<option value="" selected disabled>Loading case types...</option>';
        
        try {
            const response = await fetch('/api/case-types');
            const data = await response.json();
            
            if (data.success && data.case_types.length > 0) {
                caseTypeSelect.innerHTML = '<option value="" selected disabled>Select Case Type</option>';
                data.case_types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type.toLowerCase().replace(/\s+/g, '_');
                    option.textContent = type;
                    caseTypeSelect.appendChild(option);
                });
                caseTypeSelect.disabled = false;
            } else {
                caseTypeSelect.innerHTML = '<option value="" selected disabled>No case types found</option>';
            }
        } catch (error) {
            console.error('Error loading case types:', error);
            showError('Failed to load case types. Please try again.');
            caseTypeSelect.innerHTML = '<option value="" selected disabled>Error loading case types</option>';
        }
    }
    
    // Initialize CAPTCHA
    async function initCaptcha() {
        try {
            const response = await fetch('/api/init');
            const data = await response.json();
            
            if (data.success) {
                captchaImage.src = data.captcha_image;
                captchaText = data.captcha_text;
            } else {
                showError('Failed to load CAPTCHA. Please refresh the page.');
            }
        } catch (error) {
            console.error('Error initializing CAPTCHA:', error);
            showError('Failed to load CAPTCHA. Please try again.');
        }
    }
    
    // Handle form submission
    async function handleSubmit(e) {
        e.preventDefault();
        
        // Validate CAPTCHA
        const captchaInput = document.getElementById('captcha');
        if (captchaInput.value.toLowerCase() !== captchaText.toLowerCase()) {
            captchaInput.classList.add('is-invalid');
            captchaInput.nextElementSibling.textContent = 'Invalid CAPTCHA. Please try again.';
            initCaptcha(); // Refresh CAPTCHA
            return;
        }
        
        // Show loading state
        const submitBtnText = document.getElementById('submitBtnText');
        const submitBtnSpinner = document.getElementById('submitBtnSpinner');
        submitBtn.disabled = true;
        submitBtnText.textContent = 'Searching...';
        submitBtnSpinner.classList.remove('d-none');
        
        try {
            // Prepare search data
            const searchData = {
                state: stateSelect.value,
                court_type: courtTypeSelect.value,
                district: districtSelect.value,
                case_type: caseTypeSelect.value,
                case_number: document.getElementById('caseNumber').value,
                year: document.getElementById('year').value,
                captcha: captchaInput.value
            };
            
            // Send search request
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show search results in modal
                displaySearchResults(data);
                const searchResultsModal = new bootstrap.Modal(document.getElementById('searchResultsModal'));
                searchResultsModal.show();
            } else {
                showError(data.error || 'Failed to perform search. Please try again.');
                // Reset to first step if there's an error
                currentStep = 1;
                updateProgressBar();
                updateButtons();
                document.querySelectorAll('.step').forEach((step, index) => {
                    step.classList.toggle('d-none', index !== 0);
                });
            }
        } catch (error) {
            console.error('Search error:', error);
            showError('An error occurred while processing your request. Please try again.');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtnText.textContent = 'Search';
            submitBtnSpinner.classList.add('d-none');
        }
    }
    
    // Display search results in modal
    function displaySearchResults(data) {
        const resultsContainer = document.getElementById('searchResultsBody');
        
        if (!data.case) {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning">
                    No results found for the given search criteria.
                </div>
            `;
            return;
        }
        
        const caseData = data.case;
        const parties = data.parties || [];
        const orders = data.orders || [];
        
        // Format the results HTML
        let html = `
            <div class="card mb-4">
                <div class="card-header bg-light">
                    <h5 class="mb-0">Case Details</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>CNR Number:</strong> ${caseData.cnr_number || 'N/A'}</p>
                            <p><strong>Filing Number:</strong> ${caseData.filing_number || 'N/A'}</p>
                            <p><strong>Registration Number:</strong> ${caseData.registration_number || 'N/A'}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Filing Date:</strong> ${formatDate(caseData.filing_date)}</p>
                            <p><strong>Registration Date:</strong> ${formatDate(caseData.registration_date)}</p>
                            <p><strong>Status:</strong> <span class="badge bg-${caseData.is_disposed ? 'danger' : 'success'}">
                                ${caseData.case_status || (caseData.is_disposed ? 'Disposed' : 'Pending')}
                            </span></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header bg-light">
                            <h5 class="mb-0">Parties</h5>
                        </div>
                        <div class="card-body">
                            ${parties.length > 0 ? 
                                parties.map(party => `
                                    <div class="mb-3">
                                        <h6>${party.party_type || 'Party'}</h6>
                                        <p class="mb-1">${party.name || 'N/A'}</p>
                                        <small class="text-muted">${party.advocate_name ? 'Advocate: ' + party.advocate_name : ''}</small>
                                    </div>
                                `).join('') : 
                                '<p class="text-muted">No party information available.</p>'
                            }
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header bg-light d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">Orders & Judgments</h5>
                            ${data.pdf_url ? `
                                <a href="${data.pdf_url}" class="btn btn-sm btn-outline-primary" download>
                                    <i class="bi bi-download"></i> Download PDF
                                </a>
                            ` : ''}
                        </div>
                        <div class="card-body">
                            ${orders.length > 0 ? 
                                orders.map(order => `
                                    <div class="mb-3 border-bottom pb-2">
                                        <div class="d-flex justify-content-between">
                                            <h6>${order.order_type || 'Order'}</h6>
                                            <small class="text-muted">${formatDate(order.order_date)}</small>
                                        </div>
                                        <p class="mb-1">${order.description || 'No description available.'}</p>
                                        ${order.pdf_url ? `
                                            <a href="${order.pdf_url}" class="btn btn-sm btn-outline-secondary" target="_blank">
                                                <i class="bi bi-file-earmark-pdf"></i> View PDF
                                            </a>
                                        ` : ''}
                                    </div>
                                `).join('') : 
                                '<p class="text-muted">No orders or judgments available.</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
            
            ${data.raw_path ? `
                <div class="text-center mt-3">
                    <a href="${data.raw_path}" class="btn btn-sm btn-outline-secondary" target="_blank">
                        <i class="bi bi-code-square"></i> View Raw Data
                    </a>
                </div>
            ` : ''}
        `;
        
        resultsContainer.innerHTML = html;
    }
    
    // Helper function to format dates
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-IN', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
        } catch (e) {
            return dateString;
        }
    }
    
    // Show error message
    function showError(message) {
        // You can implement a toast or alert here
        alert(message);
    }
    
    // Initialize the form when DOM is loaded
    initForm();
});
