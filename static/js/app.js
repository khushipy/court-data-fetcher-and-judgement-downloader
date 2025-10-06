(function() {
    const form = document.getElementById('searchForm');
    const loading = document.getElementById('loadingIndicator');
    const resultsWrapper = document.getElementById('resultsTableWrapper');
    const resultsBody = document.querySelector('#resultsTable tbody');
    const noResults = document.getElementById('noResults');
    const errorContainer = document.getElementById('errorContainer');
  
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorContainer.classList.add('d-none');
      loading.style.display = 'inline-block';
      resultsBody.innerHTML = '';
      resultsWrapper.style.display = 'none';
      noResults.style.display = 'none';
  
      const payload = {
        court_type: form.court_type.value,
        state: form.state.value,
        case_type: form.case_type.value,
        case_number: form.case_number.value,
        year: form.year.value
      };
  
      try {
        const res = await fetch('/api/search', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
  
        const data = await res.json();
        loading.style.display = 'none';
  
        if (!res.ok || !data.success) {
          errorContainer.textContent = data.error || 'No data returned';
          errorContainer.classList.remove('d-none');
          noResults.style.display = '';
          return;
        }
  
        const caseObj = data.case;
        if (!caseObj) { noResults.style.display = ''; return; }
  
        resultsWrapper.style.display = '';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${caseObj.case_number || payload.case_number}</td>
          <td>${caseObj.case_type || payload.case_type}</td>
          <td>${caseObj.status || 'Unknown'}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="displayCaseDetails('${data.search_id}')">Details</button>
          </td>`;
        resultsBody.appendChild(tr);
  
      } catch (err) {
        loading.style.display = 'none';
        console.error(err);
        errorContainer.textContent = 'Network error';
        errorContainer.classList.remove('d-none');
        noResults.style.display = '';
      }
    });
  
    window.displayCaseDetails = async function(searchId) {
      try {
        const res = await fetch(`/api/search/${searchId}`);
        const data = await res.json();
        if (!res.ok || !data.success) { alert('Unable to fetch details'); return; }
  
        const caseData = data.case || {};
        document.getElementById('modalCaseNumber').textContent = caseData.case_number || 'N/A';
        document.getElementById('modalCaseStatus').textContent = caseData.case_status || 'N/A';
        const rawLink = document.getElementById('modalRawLink');
        if (data.raw_path) { rawLink.href = data.raw_path; rawLink.textContent = 'Download saved HTML'; }
        else { rawLink.href = '#'; rawLink.textContent = 'No raw saved'; }
  
        const pdfContainer = document.getElementById('modalPdfContainer');
        pdfContainer.innerHTML = '';
        if (caseData.pdf_path) {
          pdfContainer.innerHTML = `<p><a class="btn btn-outline-primary" href="${caseData.pdf_path}" target="_blank">Open PDF</a></p>`;
        }
  
        let modalEl = document.getElementById('caseDetailsModal');
        let modal = new bootstrap.Modal(modalEl);
        modal.show();
  
      } catch (err) { console.error(err); alert('Error loading details'); }
    };
  })();
  