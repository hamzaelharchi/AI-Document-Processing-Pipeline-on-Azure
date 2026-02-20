// State
let currentDocumentId = null;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const documentsList = document.getElementById('documentsList');
const documentModal = document.getElementById('documentModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    loadDocuments();
});

// Upload Setup
function setupUpload() {
    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());

    // File selected
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

// Upload File
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    uploadProgress.hidden = false;
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';

    try {
        // Simulate progress (XHR would give real progress)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);

        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const result = await response.json();
        progressText.textContent = 'Complete!';

        // Document is already processed by the upload endpoint
        console.log('Upload result:', result);
        setTimeout(() => {
            uploadProgress.hidden = true;
            loadDocuments();
        }, 1000);

    } catch (error) {
        console.error('Upload error:', error);
        progressText.textContent = 'Error: ' + error.message;
        progressFill.style.width = '0%';
        progressFill.style.background = '#fc8181';
    }

    fileInput.value = '';
}

// Poll document status
async function pollDocumentStatus(documentId, maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000));

        try {
            const response = await fetch(`${API_URL}/documents/${documentId}`);
            if (response.ok) {
                const doc = await response.json();
                if (doc.status === 'completed' || doc.status === 'failed') {
                    return doc;
                }
            }
        } catch (error) {
            console.error('Poll error:', error);
        }
    }
    throw new Error('Processing timeout');
}

// Load Documents
async function loadDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents`);

        if (!response.ok) {
            throw new Error('Failed to load documents');
        }

        const data = await response.json();
        renderDocuments(data.documents || []);

    } catch (error) {
        console.error('Load error:', error);
        documentsList.innerHTML = `
            <p class="empty-state">
                Unable to connect to API.<br>
                <small>Make sure the Function App is running.</small>
            </p>
        `;
    }
}

// Render Documents
function renderDocuments(documents) {
    if (!documents || documents.length === 0) {
        documentsList.innerHTML = '<p class="empty-state">No documents yet. Upload a file to get started.</p>';
        return;
    }

    documentsList.innerHTML = documents.map(doc => `
        <div class="document-card" onclick="openDocument('${doc.id}')">
            <div class="document-info">
                <h3>${escapeHtml(doc.id)}</h3>
                <span class="document-meta">${doc.exports?.json?.last_modified ? formatDate(doc.exports.json.last_modified) : ''}</span>
            </div>
            <div class="document-status">
                <span class="status-badge status-completed">completed</span>
            </div>
        </div>
    `).join('');
}

// Render Confidence Badge
function renderConfidenceBadge(confidence) {
    if (confidence === undefined || confidence === null) {
        return '';
    }

    const percent = Math.round(confidence * 100);
    let level = 'low';
    if (percent >= 80) level = 'high';
    else if (percent >= 60) level = 'medium';

    return `<span class="confidence-badge confidence-${level}">${percent}%</span>`;
}

// Open Document Modal
async function openDocument(documentId) {
    currentDocumentId = documentId;

    try {
        const response = await fetch(`${API_URL}/documents/${documentId}`);
        if (!response.ok) throw new Error('Failed to load document');

        const doc = await response.json();

        document.getElementById('modalTitle').textContent = doc.document_id || documentId;
        document.getElementById('modalConfidence').textContent =
            doc.confidence?.overall ? Math.round(doc.confidence.overall * 100) + '%' : 'N/A';
        document.getElementById('modalConfidence').className =
            'confidence-badge ' + getConfidenceClass(doc.confidence?.overall);
        document.getElementById('modalContent').textContent =
            doc.content?.markdown || doc.content?.raw_text || 'No content extracted';

        documentModal.classList.add('active');

    } catch (error) {
        console.error('Error loading document:', error);
        alert('Failed to load document details');
    }
}

// Close Modal
function closeModal() {
    documentModal.classList.remove('active');
    currentDocumentId = null;
}

// Export Document
async function exportDocument(format) {
    if (!currentDocumentId) return;

    try {
        const response = await fetch(`${API_URL}/documents/${currentDocumentId}/export?format=${format}`);
        if (!response.ok) throw new Error('Export failed');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document.${format === 'markdown' ? 'md' : format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export document');
    }
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function getConfidenceClass(confidence) {
    if (confidence === undefined || confidence === null) return '';
    const percent = confidence * 100;
    if (percent >= 80) return 'confidence-high';
    if (percent >= 60) return 'confidence-medium';
    return 'confidence-low';
}

// Close modal on outside click
documentModal.addEventListener('click', (e) => {
    if (e.target === documentModal) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && documentModal.classList.contains('active')) {
        closeModal();
    }
});
