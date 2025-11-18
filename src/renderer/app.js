// State
let destinations = [];
let currentItinerary = null;
let backendURL = 'http://127.0.0.1:8000';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    backendURL = await window.electronAPI.getBackendURL();
    setupEventListeners();
    addDestination(); // Add first destination by default
    checkBackendHealth();

    // Check backend health periodically
    setInterval(checkBackendHealth, 10000);
});

function setupEventListeners() {
    document.getElementById('add-destination').addEventListener('click', addDestination);
    document.getElementById('generate-btn').addEventListener('click', generateItinerary);
    document.getElementById('export-pdf-btn').addEventListener('click', exportPDF);
}

function addDestination() {
    const id = Date.now();
    const destinationHTML = `
        <div class="destination-item" data-id="${id}">
            <div class="destination-header">
                <strong>Destination ${destinations.length + 1}</strong>
                ${destinations.length > 0 ? `<button class="btn-remove" onclick="removeDestination(${id})">Remove</button>` : ''}
            </div>
            <input type="text" placeholder="Destination name (e.g., Paris, France)" data-field="name" required>

            <div class="date-mode-toggle">
                <label>
                    <input type="radio" name="date-mode-${id}" value="range" data-field="date_mode" checked onchange="toggleDateMode(${id})">
                    Date Range
                </label>
                <label>
                    <input type="radio" name="date-mode-${id}" value="days" data-field="date_mode" onchange="toggleDateMode(${id})">
                    Number of Days
                </label>
            </div>

            <div class="input-group date-range-inputs" data-mode="range">
                <input type="date" placeholder="Start date" data-field="start_date">
                <input type="date" placeholder="End date" data-field="end_date">
            </div>

            <div class="input-group date-days-inputs" data-mode="days" style="display: none;">
                <input type="date" placeholder="Start date" data-field="start_date_days">
                <input type="number" placeholder="Number of days" data-field="num_days" min="1" max="365" value="7">
            </div>
        </div>
    `;

    document.getElementById('destinations-list').insertAdjacentHTML('beforeend', destinationHTML);
    destinations.push({ id });
}

function removeDestination(id) {
    const element = document.querySelector(`[data-id="${id}"]`);
    element.remove();
    destinations = destinations.filter(d => d.id !== id);
    updateDestinationNumbers();
}

function updateDestinationNumbers() {
    document.querySelectorAll('.destination-item').forEach((item, index) => {
        item.querySelector('strong').textContent = `Destination ${index + 1}`;
    });
}

function toggleDateMode(id) {
    const element = document.querySelector(`[data-id="${id}"]`);
    const mode = element.querySelector('[data-field="date_mode"]:checked').value;

    const rangeInputs = element.querySelector('.date-range-inputs');
    const daysInputs = element.querySelector('.date-days-inputs');

    if (mode === 'range') {
        rangeInputs.style.display = 'flex';
        daysInputs.style.display = 'none';
    } else {
        rangeInputs.style.display = 'none';
        daysInputs.style.display = 'flex';
    }
}

function getDestinationsData() {
    const destElements = document.querySelectorAll('.destination-item');
    const data = [];

    destElements.forEach(element => {
        const name = element.querySelector('[data-field="name"]').value.trim();
        const mode = element.querySelector('[data-field="date_mode"]:checked').value;

        let start_date = '';
        let end_date = '';

        if (mode === 'range') {
            start_date = element.querySelector('.date-range-inputs [data-field="start_date"]').value;
            end_date = element.querySelector('.date-range-inputs [data-field="end_date"]').value;
        } else {
            // Calculate end date from start date + number of days
            const start = element.querySelector('.date-days-inputs [data-field="start_date_days"]').value;
            const numDays = parseInt(element.querySelector('[data-field="num_days"]').value) || 7;

            if (start) {
                start_date = start;
                const startDateObj = new Date(start);
                startDateObj.setDate(startDateObj.getDate() + numDays);
                end_date = startDateObj.toISOString().split('T')[0];
            }
        }

        if (name) {
            data.push({ name, start_date, end_date });
        }
    });

    return data;
}

async function generateItinerary() {
    const preferences = document.getElementById('preferences').value.trim();
    const destinationsData = getDestinationsData();

    // Validation
    if (!preferences) {
        showStatus('Please enter your preferences', 'error');
        return;
    }

    if (destinationsData.length === 0) {
        showStatus('Please add at least one destination', 'error');
        return;
    }

    // Show loading state
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const btnLoader = generateBtn.querySelector('.btn-loader');

    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    generateBtn.disabled = true;

    showStatus('Generating your itinerary... This may take a minute.', 'info');

    try {
        const response = await fetch(`${backendURL}/api/plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                destinations: destinationsData,
                preferences: preferences
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            const errorMessage = errorData.detail || `Server error: ${response.status}`;
            throw new Error(errorMessage);
        }

        const data = await response.json();
        currentItinerary = data;

        // Display markdown preview
        displayMarkdownPreview(data.markdown);

        showStatus('Itinerary generated successfully!', 'success');
        document.getElementById('export-pdf-btn').style.display = 'block';

    } catch (error) {
        console.error('Error generating itinerary:', error);
        showStatus(`Error: ${error.message}. Make sure the backend is running.`, 'error');
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        generateBtn.disabled = false;
    }
}

function displayMarkdownPreview(markdown) {
    const previewContent = document.getElementById('preview-content');
    const html = marked.parse(markdown);
    previewContent.innerHTML = html;
    previewContent.scrollTop = 0;
}

async function exportPDF() {
    if (!currentItinerary) {
        showStatus('No itinerary to export', 'error');
        return;
    }

    showStatus('Generating PDF...', 'info');

    try {
        const response = await fetch(`${backendURL}/api/generate-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ markdown: currentItinerary.markdown })
        });

        if (!response.ok) {
            const errorData = await response.json();
            const errorMessage = errorData.detail || `Server error: ${response.status}`;
            throw new Error(errorMessage);
        }

        const data = await response.json();

        if (data.success && data.pdf_path) {
            showStatus('PDF generated successfully! Opening...', 'success');
            await window.electronAPI.openPDF(data.pdf_path);
        }

    } catch (error) {
        console.error('Error generating PDF:', error);
        showStatus(`Error generating PDF: ${error.message}`, 'error');
    }
}

async function checkBackendHealth() {
    const statusElement = document.getElementById('backend-status');

    try {
        const response = await fetch(`${backendURL}/health`, {
            method: 'GET',
            timeout: 5000
        });

        if (response.ok) {
            const data = await response.json();
            statusElement.innerHTML = `
                <span class="status-dot status-online"></span>
                <span>Backend: Online ${data.llm_loaded ? '| LLM: Ready ✓' : '| LLM: Loading...'}</span>
            `;
        } else {
            throw new Error('Backend not responding');
        }
    } catch (error) {
        statusElement.innerHTML = `
            <span class="status-dot status-offline"></span>
            <span>Backend: Offline - Please check console</span>
        `;
    }
}

function showStatus(message, type) {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;

    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.className = 'status-message';
        }, 5000);
    }
}

// Listen to backend logs
window.electronAPI.onBackendLog((event, log) => {
    console.log('Backend:', log);
});
