// State
let destinations = [];
let currentItinerary = null;
let backendURL = 'http://127.0.0.1:8000';
let itineraryHistory = [];

// Helper function to get Tauri invoke if available
function getTauriInvoke() {
    try {
        // Check for loaded Tauri API (ESM import)
        if (window.__TAURI_API__ && window.__TAURI_API__.core && window.__TAURI_API__.core.invoke) {
            return window.__TAURI_API__.core.invoke;
        }
        // Tauri v2 API structure (if available globally)
        if (window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke) {
            return window.__TAURI__.core.invoke;
        }
        // Tauri v1 fallback
        if (window.__TAURI__ && window.__TAURI__.tauri && window.__TAURI__.tauri.invoke) {
            return window.__TAURI__.tauri.invoke;
        }
        console.log('Tauri API not found.');
        console.log('  window.__TAURI_API__:', !!window.__TAURI_API__);
        console.log('  window.__TAURI__:', !!window.__TAURI__);
        console.log('  window.__TAURI_INTERNALS__:', !!window.__TAURI_INTERNALS__);
        return null;
    } catch (e) {
        console.error('Failed to access Tauri invoke:', e);
        return null;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM Content Loaded - initializing app');

    // Debug Tauri availability
    console.log('Tauri INTERNALS available:', !!window.__TAURI_INTERNALS__);
    console.log('Tauri API (global) available:', !!window.__TAURI__);
    console.log('Tauri API (loaded) available:', !!window.__TAURI_API__);

    // Wait a moment for the API to load if it's being imported
    if (window.__TAURI_INTERNALS__ && !window.__TAURI_API__) {
        console.log('Waiting for Tauri API to load...');
        await new Promise(resolve => setTimeout(resolve, 500));
        console.log('Tauri API (after wait) available:', !!window.__TAURI_API__);
    }

    const invoke = getTauriInvoke();
    console.log('Tauri invoke available:', !!invoke);
    if (invoke) {
        console.log('Tauri commands ready!');
    }

    setupEventListeners();
    console.log('Event listeners set up');

    addDestination(); // Add first destination by default
    console.log('First destination added');

    // Load saved itinerary from localStorage
    loadSavedItinerary();

    checkBackendHealth();

    // Check backend health periodically
    setInterval(checkBackendHealth, 10000);
});

function setupEventListeners() {
    document.getElementById('add-destination').addEventListener('click', addDestination);
    document.getElementById('generate-btn').addEventListener('click', generateItinerary);
    // export-pdf-btn uses onclick in HTML, no need to add listener here
    document.getElementById('history-btn').addEventListener('click', toggleHistory);
    document.getElementById('close-history').addEventListener('click', toggleHistory);
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

            <div class="form-section">
                <label>Dates (Optional)</label>
                <div class="date-mode-toggle">
                    <label>
                        <input type="radio" name="date-mode-${id}" value="none" data-field="date_mode" checked onchange="toggleDateMode(${id})">
                        No dates
                    </label>
                    <label>
                        <input type="radio" name="date-mode-${id}" value="single" data-field="date_mode" onchange="toggleDateMode(${id})">
                        Single date
                    </label>
                    <label>
                        <input type="radio" name="date-mode-${id}" value="duration" data-field="date_mode" onchange="toggleDateMode(${id})">
                        Date + Days
                    </label>
                    <label>
                        <input type="radio" name="date-mode-${id}" value="range" data-field="date_mode" onchange="toggleDateMode(${id})">
                        Date range
                    </label>
                </div>

                <div class="date-inputs-container">
                    <div class="date-inputs date-single" data-mode="single" style="display: none;">
                        <input type="date" data-field="single_date" placeholder="Date">
                    </div>

                    <div class="date-inputs date-duration" data-mode="duration" style="display: none;">
                        <input type="date" data-field="duration_start" placeholder="Start date">
                        <input type="number" data-field="num_days" placeholder="Days" min="1" max="365" value="7">
                    </div>

                    <div class="date-inputs date-range" data-mode="range" style="display: none;">
                        <input type="date" data-field="range_start" placeholder="Start date">
                        <input type="date" data-field="range_end" placeholder="End date">
                    </div>
                </div>
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

    // Hide all date input sections
    element.querySelectorAll('.date-inputs').forEach(section => {
        section.style.display = 'none';
    });

    // Show the selected mode's inputs
    if (mode !== 'none') {
        const activeSection = element.querySelector(`.date-${mode}`);
        if (activeSection) {
            activeSection.style.display = 'flex';
        }
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

        if (mode === 'single') {
            start_date = element.querySelector('[data-field="single_date"]')?.value || '';
            end_date = start_date; // Same day trip
        } else if (mode === 'duration') {
            const start = element.querySelector('[data-field="duration_start"]')?.value;
            const numDays = parseInt(element.querySelector('[data-field="num_days"]')?.value) || 7;

            if (start) {
                start_date = start;
                const startDateObj = new Date(start);
                startDateObj.setDate(startDateObj.getDate() + numDays);
                end_date = startDateObj.toISOString().split('T')[0];
            }
        } else if (mode === 'range') {
            start_date = element.querySelector('[data-field="range_start"]')?.value || '';
            end_date = element.querySelector('[data-field="range_end"]')?.value || '';
        }
        // mode === 'none' leaves dates empty

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

    // Show loading overlay
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.add('active');

    try {
        const response = await fetch(`${backendURL}/api/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destinations: destinationsData,
                preferences: preferences
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate itinerary');
        }

        const data = await response.json();
        currentItinerary = data;

        // Save to localStorage
        saveItinerary(data);

        // Display markdown preview
        displayMarkdownPreview(data.markdown);

        showStatus('Itinerary generated successfully!', 'success');

        // Enable export button with multiple attempts
        const exportBtn = document.getElementById('export-pdf-btn');
        console.log('Export button element:', exportBtn);
        console.log('Button disabled state before:', exportBtn?.disabled);

        if (exportBtn) {
            exportBtn.disabled = false;
            exportBtn.removeAttribute('disabled');

            // Force a reflow to ensure the change takes effect
            void exportBtn.offsetWidth;

            console.log('Export button enabled');
            console.log('Button disabled state after:', exportBtn.disabled);
        } else {
            console.error('Export button not found!');
        }

    } catch (error) {
        console.error('Error generating itinerary:', error);
        showStatus(`Error: ${error.message}. Make sure the backend is running.`, 'error');
    } finally {
        // Hide loading overlay
        const loadingOverlay = document.getElementById('loading-overlay');
        loadingOverlay.classList.remove('active');
    }
}

function displayMarkdownPreview(markdown) {
    const previewContent = document.getElementById('preview-content');
    const html = marked.parse(markdown);
    previewContent.innerHTML = html;
    previewContent.scrollTop = 0;
}

window.exportPDF = async function() {
    console.log('Export PDF clicked!');
    console.log('Current itinerary:', currentItinerary);

    if (!currentItinerary) {
        console.error('No current itinerary available');
        alert('No itinerary to export. Please generate an itinerary first.');
        return;
    }

    // Show save dialog
    let savePath = null;
    try {
        console.log('Attempting to show save dialog...');

        // Check if Tauri is available
        if (window.__TAURI__) {
            // Dynamically import the dialog plugin
            const { save } = await import('https://esm.sh/@tauri-apps/plugin-dialog@2');

            savePath = await save({
                defaultPath: 'vacation-itinerary.pdf',
                filters: [{
                    name: 'PDF',
                    extensions: ['pdf']
                }]
            });

            console.log('Save path selected:', savePath);

            if (!savePath) {
                console.log('User cancelled save dialog');
                return; // User cancelled
            }
        } else {
            console.log('Tauri not available, using default location');
        }
    } catch (e) {
        console.log('Dialog error, using default location:', e);
    }

    console.log('Sending PDF generation request...');

    try {
        const response = await fetch(`${backendURL}/api/generate-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                markdown: currentItinerary.markdown,
                output_path: savePath
            })
        });

        console.log('PDF response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('PDF generation failed:', errorText);
            throw new Error('Failed to generate PDF');
        }

        const data = await response.json();
        console.log('PDF generation result:', data);

        if (data.success && data.pdf_path) {
            showPDFNotification(data.pdf_path);
        }

    } catch (error) {
        console.error('Error generating PDF:', error);
        alert(`Error generating PDF: ${error.message}`);
    }
};

async function checkBackendHealth() {
    const statusElement = document.getElementById('backend-status');

    try {
        const response = await fetch(`${backendURL}/health`);
        const data = await response.json();

        statusElement.innerHTML = `
            <span class="status-dot status-online"></span>
            <span>Backend: Online ${data.llm_loaded ? '| LLM: Ready ✓' : '| LLM: Loading...'}</span>
        `;
    } catch (error) {
        console.error('Backend health check failed:', error);
        statusElement.innerHTML = `
            <span class="status-dot status-offline"></span>
            <span>Backend: Offline - ${error.toString()}</span>
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

function showPDFNotification(pdfPath) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'pdf-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">📄</div>
            <div class="notification-text">
                <div class="notification-title">PDF Generated!</div>
                <div class="notification-subtitle">Your itinerary is ready</div>
            </div>
            <button class="notification-btn-open" onclick="openPDFFile('${pdfPath.replace(/'/g, "\\'")}')">
                Open PDF
            </button>
            <button class="notification-btn-close" onclick="this.parentElement.parentElement.remove()">
                ✕
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto remove after 10 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 10000);
}

window.openPDFFile = async function(path) {
    console.log('Opening PDF:', path);
    const invoke = getTauriInvoke();
    if (invoke) {
        try {
            await invoke('open_file', { path });
            console.log('PDF opened successfully');
        } catch (e) {
            console.error('Failed to open PDF:', e);
            alert(`Failed to open PDF: ${e.message}\n\nFile location: ${path}`);
        }
    } else {
        alert(`PDF saved to: ${path}\n\nTauri API not available, please open the file manually.`);
    }
};

function saveItinerary(itinerary) {
    try {
        // Create history entry
        const historyEntry = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            itinerary: itinerary,
            destinations: getDestinationsData().map(d => d.name).join(', '),
            preview: itinerary.markdown.substring(0, 200)
        };

        // Load existing history
        const existingHistory = JSON.parse(localStorage.getItem('itineraryHistory') || '[]');

        // Add new entry at the beginning
        existingHistory.unshift(historyEntry);

        // Keep only last 50 itineraries
        const trimmedHistory = existingHistory.slice(0, 50);

        // Save to localStorage
        localStorage.setItem('itineraryHistory', JSON.stringify(trimmedHistory));
        localStorage.setItem('currentItinerary', JSON.stringify(itinerary));
        localStorage.setItem('lastGenerated', historyEntry.timestamp);

        // Update in-memory history
        itineraryHistory = trimmedHistory;

        console.log('Itinerary saved to history');
        renderHistory();
    } catch (e) {
        console.error('Failed to save itinerary:', e);
    }
}

function loadSavedItinerary() {
    try {
        // Load history
        const historyData = localStorage.getItem('itineraryHistory');
        if (historyData) {
            itineraryHistory = JSON.parse(historyData);
            console.log(`Loaded ${itineraryHistory.length} itineraries from history`);
            renderHistory();
        }

        // Load current itinerary
        const saved = localStorage.getItem('currentItinerary');
        console.log('Checking for saved itinerary...', saved ? 'Found' : 'Not found');

        if (saved) {
            currentItinerary = JSON.parse(saved);
            displayMarkdownPreview(currentItinerary.markdown);

            const exportBtn = document.getElementById('export-pdf-btn');
            console.log('Loading: Export button element:', exportBtn);

            if (exportBtn) {
                exportBtn.disabled = false;
                exportBtn.removeAttribute('disabled');
                console.log('Export button enabled from saved itinerary');
            }

            const lastGenerated = localStorage.getItem('lastGenerated');
            if (lastGenerated) {
                const date = new Date(lastGenerated);
                console.log(`Loaded itinerary from ${date.toLocaleString()}`);
            }
        }
    } catch (e) {
        console.error('Failed to load saved itinerary:', e);
    }
}

function toggleHistory() {
    const historyPanel = document.getElementById('history-panel');
    historyPanel.classList.toggle('open');
}

function renderHistory() {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;

    if (itineraryHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-history">
                <p>No saved itineraries yet</p>
                <p style="font-size: 12px; color: #999;">Generate your first itinerary to see it here</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = itineraryHistory.map(entry => {
        const date = new Date(entry.timestamp);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const timeStr = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

        return `
            <div class="history-item" onclick="loadItineraryFromHistory(${entry.id})">
                <div class="history-item-header">
                    <strong>${entry.destinations || 'Untitled Trip'}</strong>
                    <button class="btn-delete-history" onclick="event.stopPropagation(); deleteHistoryItem(${entry.id})">×</button>
                </div>
                <div class="history-item-date">${dateStr} at ${timeStr}</div>
                <div class="history-item-preview">${entry.preview}...</div>
            </div>
        `;
    }).join('');
}

window.loadItineraryFromHistory = function(id) {
    const entry = itineraryHistory.find(e => e.id === id);
    if (entry) {
        currentItinerary = entry.itinerary;
        displayMarkdownPreview(currentItinerary.markdown);

        const exportBtn = document.getElementById('export-pdf-btn');
        if (exportBtn) {
            exportBtn.disabled = false;
            exportBtn.removeAttribute('disabled');
        }

        toggleHistory(); // Close history panel
        console.log('Loaded itinerary from history:', entry.destinations);
    }
};

window.deleteHistoryItem = function(id) {
    itineraryHistory = itineraryHistory.filter(e => e.id !== id);
    localStorage.setItem('itineraryHistory', JSON.stringify(itineraryHistory));
    renderHistory();
    console.log('Deleted history item:', id);
};
