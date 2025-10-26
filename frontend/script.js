// Get DOM elements
const uploadForm = document.getElementById('uploadForm');
const validateBtn = document.getElementById('validateBtn');
const resetBtn = document.getElementById('resetBtn');
const retryBtn = document.getElementById('retryBtn');
const executeBtn = document.getElementById('executeBtn');
const backToValidationBtn = document.getElementById('backToValidationBtn');

const uploadSection = document.querySelector('.upload-section');
const loadingSection = document.getElementById('loadingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const executeSection = document.getElementById('executeSection');

const overallResult = document.getElementById('overallResult');
const checkpointsList = document.getElementById('checkpointsList');
const errorMessage = document.getElementById('errorMessage');
const timelineAccordion = document.getElementById('timelineAccordion');

// Section display management
function showSection(section) {
    // Hide all sections
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    executeSection.style.display = 'none';
    
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
    
    // Show Execute button if validation passed
    if (isPass) {
        executeBtn.style.display = 'inline-block';
    } else {
        executeBtn.style.display = 'none';
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
    executeBtn.style.display = 'none';
    showSection(uploadSection);
});

// Retry button
retryBtn.addEventListener('click', () => {
    showSection(uploadSection);
});

// Back to validation button
backToValidationBtn.addEventListener('click', () => {
    showSection(resultSection);
});

// Execute button - Start experiment
executeBtn.addEventListener('click', async () => {
    console.log('Execute button clicked');
    
    // Show loading
    showSection(loadingSection);
    
    try {
        // Call execute API
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to execute experiment');
        }
        
        const experimentData = await response.json();
        console.log('Experiment data:', experimentData);
        
        // Display experiment timeline progressively (10 seconds per timepoint)
        displayExperimentTimelineProgressively(experimentData);
        
    } catch (error) {
        console.error('Execute error:', error);
        showError(error.message || 'An error occurred during experiment execution.');
    }
});

// Display experiment timeline progressively (10 seconds per timepoint)
function displayExperimentTimelineProgressively(data) {
    timelineAccordion.innerHTML = '';
    
    if (!data.timepoints || data.timepoints.length === 0) {
        timelineAccordion.innerHTML = '<p>No timepoints available.</p>';
        showSection(executeSection);
        return;
    }
    
    // Show execute section
    showSection(executeSection);
    
    // Store experiment data
    window.currentExperimentData = data;
    
    // Add timepoints progressively (one every 10 seconds)
    let currentIndex = 0;
    
    // Add first timepoint immediately
    const firstTimepoint = data.timepoints[currentIndex];
    const firstAccordionItem = createTimepointAccordion(firstTimepoint, currentIndex, data.experiment_id);
    timelineAccordion.appendChild(firstAccordionItem);
    currentIndex++;
    
    // Add remaining timepoints every 10 seconds
    const intervalId = setInterval(() => {
        if (currentIndex < data.timepoints.length) {
            const timepoint = data.timepoints[currentIndex];
            const accordionItem = createTimepointAccordion(timepoint, currentIndex, data.experiment_id);
            timelineAccordion.appendChild(accordionItem);
            currentIndex++;
        } else {
            // All timepoints added
            clearInterval(intervalId);
            console.log('All timepoints displayed');
        }
    }, 10000); // 10 seconds
}

// Display experiment timeline (all at once - for testing)
function displayExperimentTimeline(data) {
    timelineAccordion.innerHTML = '';
    
    if (!data.timepoints || data.timepoints.length === 0) {
        timelineAccordion.innerHTML = '<p>No timepoints available.</p>';
        showSection(executeSection);
        return;
    }
    
    // Create accordion items for each timepoint
    data.timepoints.forEach((timepoint, index) => {
        const accordionItem = createTimepointAccordion(timepoint, index, data.experiment_id);
        timelineAccordion.appendChild(accordionItem);
    });
    
    // Show execute section
    showSection(executeSection);
}

// Create timepoint accordion item
function createTimepointAccordion(timepoint, index, experimentId) {
    const time = timepoint.time;
    const wells = timepoint.wells || [];
    
    // Count contamination
    const contamCount = wells.filter(w => 
        w.rf_prediction && w.rf_prediction.label === 'contaminated'
    ).length;
    
    const allClean = contamCount === 0;
    const statusIcon = allClean ? '✅' : '⚠️';
    const statusText = allClean ? 'All Clean' : `${contamCount} Possible Contaminated`;
    
    // Create accordion container
    const accordionDiv = document.createElement('div');
    accordionDiv.className = 'accordion-item';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'accordion-header';
    header.innerHTML = `
        <span class="timepoint-label">t=${time}s ${index === 0 ? '(Initial)' : ''}</span>
        <span class="timepoint-status">${statusIcon} ${statusText}</span>
        <span class="accordion-toggle">▼</span>
    `;
    
    // Create content (wells)
    const content = document.createElement('div');
    content.className = 'accordion-content';
    content.style.display = 'none';
    
    wells.forEach(well => {
        const wellDiv = createWellDisplay(well, time, experimentId);
        content.appendChild(wellDiv);
    });
    
    // Toggle functionality
    header.addEventListener('click', () => {
        const isOpen = content.style.display === 'block';
        content.style.display = isOpen ? 'none' : 'block';
        header.querySelector('.accordion-toggle').textContent = isOpen ? '▼' : '▲';
    });
    
    accordionDiv.appendChild(header);
    accordionDiv.appendChild(content);
    
    return accordionDiv;
}

// Create well display
function createWellDisplay(well, time, experimentId) {
    const wellDiv = document.createElement('div');
    wellDiv.className = 'well-display';
    
    const rfPred = well.rf_prediction || {};
    const llmPred = well.llm_prediction || {};
    
    const rfLabel = rfPred.label || 'unknown';
    const rfConfidence = (rfPred.confidence || 0).toFixed(2);
    const llmLabel = llmPred.label || 'unknown';
    const llmReasoning = llmPred.reasoning || 'No reasoning provided';
    
    const rfIcon = rfLabel === 'clean' ? '✅' : rfLabel === 'contaminated' ? '⚠️' : '❓';
    const llmIcon = llmLabel === 'clean' ? '✅' : llmLabel === 'contaminated' ? '⚠️' : '❓';
    
    // Construct image URL
    const imageUrl = `/api/well_image/${experimentId}/${time}/${well.well_id}`;
    
    wellDiv.innerHTML = `
        <div class="well-header">
            <h4>Well ${well.well_id}</h4>
        </div>
        <div class="well-image-container">
            <img src="${imageUrl}" alt="Well ${well.well_id} at t=${time}s" class="well-image" 
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <p class="image-error" style="display: none;">Image not available</p>
        </div>
        <div class="well-analysis">
            <div class="analysis-section">
                <h5>🔬 Random Forest Analysis</h5>
                <p>${rfIcon} <strong>${rfLabel.toUpperCase()}</strong></p>
                <p>Confidence: ${rfConfidence}</p>
            </div>
            <div class="analysis-section">
                <h5>🤖 Gemini Vision Analysis</h5>
                <p>${llmIcon} <strong>${llmLabel.toUpperCase()}</strong></p>
                <p class="llm-reasoning">${llmReasoning}</p>
            </div>
        </div>
    `;
    
    return wellDiv;
}

// HTML escape
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initial state: show upload section
showSection(uploadSection);

