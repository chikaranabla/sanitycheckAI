// Get DOM elements
const uploadForm = document.getElementById('uploadForm');
const validateBtn = document.getElementById('validateBtn');
const resetBtn = document.getElementById('resetBtn');
const retryBtn = document.getElementById('retryBtn');

const uploadSection = document.querySelector('.upload-section');
const loadingSection = document.getElementById('loadingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

const overallResult = document.getElementById('overallResult');
const checkpointsList = document.getElementById('checkpointsList');
const errorMessage = document.getElementById('errorMessage');

// Section display management
function showSection(section) {
    // Hide all sections
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Show specified section
    section.style.display = 'block';
}

// Form submission handling
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const protocolFile = document.getElementById('protocolFile').files[0];
    const imageFile = document.getElementById('imageFile').files[0];
    
    // Check if files are selected
    if (!protocolFile || !imageFile) {
        showError('Please select both protocol file and image file.');
        return;
    }
    
    // Show loading
    showSection(loadingSection);
    
    try {
        // Create FormData
        const formData = new FormData();
        formData.append('protocol_file', protocolFile);
        formData.append('image_file', imageFile);
        
        // API request
        const response = await fetch('/api/validate', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Server error occurred');
        }
        
        const result = await response.json();
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred during verification.');
    }
});

// Display results
function displayResults(data) {
    // Display overall result
    const isPass = data.overall_result === 'pass';
    overallResult.className = `overall-result ${data.overall_result}`;
    overallResult.innerHTML = `
        <span class="overall-result-icon">${isPass ? '✅' : '❌'}</span>
        <div>${isPass ? 'Verification Passed' : 'Verification Failed'}</div>
        <small style="font-size: 1rem; font-weight: normal; display: block; margin-top: 10px;">
            ${isPass ? 'All checkpoints cleared successfully' : 'Issues detected in some checkpoints'}
        </small>
    `;
    
    // Display checkpoints list
    checkpointsList.innerHTML = '';
    
    if (data.checkpoints && data.checkpoints.length > 0) {
        data.checkpoints.forEach(checkpoint => {
            const checkpointItem = createCheckpointItem(checkpoint);
            checkpointsList.appendChild(checkpointItem);
        });
    } else {
        checkpointsList.innerHTML = '<p>No checkpoints available.</p>';
    }
    
    // Show result section
    showSection(resultSection);
}

// Create checkpoint item
function createCheckpointItem(checkpoint) {
    const div = document.createElement('div');
    div.className = `checkpoint-item ${checkpoint.result}`;
    
    const icon = checkpoint.result === 'pass' ? '✅' : '❌';
    
    div.innerHTML = `
        <div class="checkpoint-icon">${icon}</div>
        <div class="checkpoint-content">
            <div class="checkpoint-description">
                <span class="checkpoint-id">#${checkpoint.id}</span>
                ${escapeHtml(checkpoint.description)}
            </div>
            ${checkpoint.details ? `
                <div class="checkpoint-details">
                    ${escapeHtml(checkpoint.details)}
                </div>
            ` : ''}
        </div>
    `;
    
    return div;
}

// Show error
function showError(message) {
    errorMessage.innerHTML = `
        <p><strong>Error Message:</strong></p>
        <p>${escapeHtml(message)}</p>
    `;
    showSection(errorSection);
}

// Reset button
resetBtn.addEventListener('click', () => {
    uploadForm.reset();
    showSection(uploadSection);
});

// Retry button
retryBtn.addEventListener('click', () => {
    showSection(uploadSection);
});

// HTML escape
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initial state: show upload section
showSection(uploadSection);

