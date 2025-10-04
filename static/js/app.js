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
        return 'Invalid date';
    }
}

// Helper function to get status badge class
function getStatusBadgeClass(status) {
    if (!status) return 'bg-secondary';
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('disposed')) return 'bg-danger';
    if (statusLower.includes('pending')) return 'bg-warning text-dark';
    if (statusLower.includes('admit') || statusLower.includes('allowed')) return 'bg-success';
    if (statusLower.includes('dismiss') || statusLower.includes('reject')) return 'bg-dark';
    return 'bg-info';
}

// Function to display search results
function displayResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    No cases found matching your search criteria.
                </div>
            </div>
        `;
        return;
    }
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>CNR Number</th>
                        <th>Case Number</th>
                        <th>Filing Date</th>
                        <th>Status</th>
                        <th>Next Hearing</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    results.forEach((result) => {
        tableHtml += `
            <tr>
                <td>${result.cnr_number || 'N/A'}</td>
                <td>${result.case_number || 'N/A'}</td>
                <td>${formatDate(result.filing_date) || 'N/A'}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(result.status)}">
                        ${result.status || 'N/A'}
                    </span>
                </td>
                <td>${formatDate(result.next_hearing_date) || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-details" 
                            data-case-id="${result.id || ''}">
                        <i class="bi bi-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    resultsContainer.innerHTML = tableHtml;
}

// Function to view case details
function viewCaseDetails(caseId) {
    const modal = new bootstrap.Modal(document.getElementById('caseDetailsModal'));
    const modalBody = document.querySelector('#caseDetailsModal .modal-body');
    
    // Show loading state
    modalBody.innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading case details...</p>
        </div>
    `;
    
    // Show the modal
    modal.show();
    
    // Fetch case details
    fetch(`/api/cases/${caseId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch case details');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Format parties
            let partiesHtml = '';
            if (data.parties && data.parties.length > 0) {
                partiesHtml = `
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Party Type</th>
                                    <th>Name</th>
                                    <th>Advocate</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.parties.map(party => `
                                    <tr>
                                        <td>${party.type || 'N/A'}</td>
                                        <td>${party.name || 'N/A'}</td>
                                        <td>${party.advocate || 'N/A'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>`;
            } else {
                partiesHtml = '<p>No party information available</p>';
            }
            
            // Format orders/judgments
            let ordersHtml = '';
            if (data.orders && data.orders.length > 0) {
                ordersHtml = `
                    <div class="list-group mt-3">
                        ${data.orders.map(order => `
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">${order.type || 'Order'}</h6>
                                    <small>${formatDate(order.date) || 'N/A'}</small>
                                </div>
                                <p class="mb-1">${order.text || 'No details available'}</p>
                                ${order.pdf_url ? `
                                    <a href="${order.pdf_url}" 
                                       class="btn btn-sm btn-outline-primary mt-2"
                                       target="_blank" rel="noopener noreferrer">
                                        <i class="bi bi-download"></i> Download
                                    </a>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>`;
            }
            
            // Format and display case details
            modalBody.innerHTML = `
                <div class="case-details">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h5>Case Information</h5>
                            <table class="table table-sm table-borderless">
                                <tr>
                                    <th>CNR Number:</th>
                                    <td>${data.cnr_number || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Filing Number:</th>
                                    <td>${data.filing_number || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Status:</th>
                                    <td>
                                        <span class="badge ${getStatusBadgeClass(data.status)}">
                                            ${data.status || 'N/A'}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h5>Dates</h5>
                            <table class="table table-sm table-borderless">
                                <tr>
                                    <th>Filing Date:</th>
                                    <td>${formatDate(data.filing_date) || 'N/A'}</td>
                                </tr>
                                <tr>
                                    <th>Next Hearing:</th>
                                    <td>${formatDate(data.next_hearing_date) || 'Not scheduled'}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <h5>Parties</h5>
                        ${partiesHtml}
                    </div>
                    
                    ${ordersHtml ? `
                        <div>
                            <h5>Orders/Judgments</h5>
                            ${ordersHtml}
                        </div>
                    ` : ''}
                </div>
            `;
        })
        .catch(error => {
            console.error('Error fetching case details:', error);
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${error.message || 'Failed to load case details. Please try again.'}
                </div>
            `;
        });
}

// Function to fetch and display cause list
async function fetchCauseList() {
    const date = new Date().toISOString().split('T')[0]; // Today's date in YYYY-MM-DD
    const courtType = document.getElementById('courtType').value;
    const causeListContainer = document.getElementById('causeListContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Show loading state
    causeListContainer.innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading cause list...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/causes?date=${date}&court_type=${courtType}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch cause list');
        }
        
        // Display cause list
        displayCauseList(data.cases || []);
        
    } catch (error) {
        console.error('Error fetching cause list:', error);
        errorContainer.textContent = error.message || 'Failed to load cause list';
        errorContainer.classList.remove('d-none');
        causeListContainer.innerHTML = '';
    }
}

// Function to display cause list
function displayCauseList(cases) {
    const causeListContainer = document.getElementById('causeListContainer');
    
    if (!cases || cases.length === 0) {
        causeListContainer.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle-fill me-2"></i>
                No cases listed for today.
            </div>
        `;
        return;
    }
    
    const tableHtml = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Case Number</th>
                        <th>Petitioner</th>
                        <th>Respondent</th>
                        <th>Purpose</th>
                        <th>Time</th>
                        <th>Court Room</th>
                        <th>Judge</th>
                    </tr>
                </thead>
                <tbody>
                    ${cases.map(caseItem => `
                        <tr>
                            <td>${caseItem.case_number || 'N/A'}</td>
                            <td>${caseItem.petitioner || 'N/A'}</td>
                            <td>${caseItem.respondent || 'N/A'}</td>
                            <td>${caseItem.purpose || 'N/A'}</td>
                            <td>${caseItem.time || 'N/A'}</td>
                            <td>${caseItem.court_room || 'N/A'}</td>
                            <td>${caseItem.judge || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    causeListContainer.innerHTML = tableHtml;
}

// Initialize the application
function init() {
    // Handle search form submission
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const searchBtn = document.getElementById('searchBtn');
            const resultsContainer = document.getElementById('searchResults');
            const errorContainer = document.getElementById('errorContainer');
            
            // Show loading state
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...';
            
            // Clear previous results and errors
            resultsContainer.innerHTML = '';
            errorContainer.classList.add('d-none');
            
            try {
                const formData = {
                    case_type: document.getElementById('caseType').value,
                    case_number: document.getElementById('caseNumber').value,
                    year: document.getElementById('year').value,
                    court_type: document.getElementById('courtType').value
                };
                
                // Make API call
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch case details');
                }
                
                // Display results
                if (data.case) {
                    displayCaseDetails(data.case);
                } else if (data.results && data.results.length > 0) {
                    displayResults(data.results);
                } else {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-info">
                            No results found for your search criteria.
                        </div>
                    `;
                }
                
            } catch (error) {
                console.error('Search error:', error);
                errorContainer.textContent = error.message || 'An error occurred while processing your request.';
                errorContainer.classList.remove('d-none');
            } finally {
                // Reset button state
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="bi bi-search me-2"></i> Search';
            }
        });
    }
    
    // Handle view details buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.view-details')) {
            const caseId = e.target.closest('.view-details').dataset.caseId;
            if (caseId) {
                viewCaseDetails(caseId);
            }
        }
    });
    
    // Handle tab switching
    const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabLinks.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            if (e.target.getAttribute('href') === '#causeList') {
                fetchCauseList();
            }
        });
    });
    
    // Load cause list by default if on the cause list tab
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab && activeTab.getAttribute('href') === '#causeList') {
        fetchCauseList();
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', init);
