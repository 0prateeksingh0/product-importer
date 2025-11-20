// Product Importer Frontend JavaScript

const API_BASE = '/api';
let currentPage = 1;
let currentSearch = '';
let currentActiveFilter = '';
let editingProductId = null;
let editingWebhookId = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeUpload();
    initializeProducts();
    initializeWebhooks();
});

// ============================================================================
// TAB NAVIGATION
// ============================================================================

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Update active button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // Load data for the active tab
            if (targetTab === 'products') {
                loadProducts();
            } else if (targetTab === 'webhooks') {
                loadWebhooks();
            }
        });
    });
}

// ============================================================================
// FILE UPLOAD & IMPORT
// ============================================================================

function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('csvFile');
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) {
            uploadFile(file);
        } else {
            showToast('Please upload a CSV file', 'error');
        }
    });
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/import`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const data = await response.json();
        showToast('File uploaded successfully. Processing...', 'success');
        
        // Show progress container
        document.getElementById('uploadProgress').style.display = 'block';
        
        // Start monitoring progress
        monitorImportProgress(data.id);
        
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
    }
}

function monitorImportProgress(jobId) {
    const eventSource = new EventSource(`${API_BASE}/import/${jobId}/stream`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.error) {
            showToast('Error: ' + data.error, 'error');
            eventSource.close();
            return;
        }
        
        updateProgress(data);
        
        if (data.status === 'completed') {
            showToast('Import completed successfully!', 'success');
            eventSource.close();
            
            // Reset file input after a delay
            setTimeout(() => {
                document.getElementById('csvFile').value = '';
                document.getElementById('uploadProgress').style.display = 'none';
            }, 3000);
        } else if (data.status === 'failed') {
            showToast('Import failed: ' + (data.error_message || 'Unknown error'), 'error');
            eventSource.close();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        
        // Fallback to polling
        pollImportProgress(jobId);
    };
}

async function pollImportProgress(jobId) {
    let isComplete = false;
    
    while (!isComplete) {
        try {
            const response = await fetch(`${API_BASE}/import/${jobId}`);
            const data = await response.json();
            
            updateProgress(data);
            
            if (data.status === 'completed' || data.status === 'failed') {
                isComplete = true;
                
                if (data.status === 'completed') {
                    showToast('Import completed successfully!', 'success');
                } else {
                    showToast('Import failed: ' + (data.error_message || 'Unknown error'), 'error');
                }
                
                setTimeout(() => {
                    document.getElementById('csvFile').value = '';
                    document.getElementById('uploadProgress').style.display = 'none';
                }, 3000);
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            console.error('Polling error:', error);
            isComplete = true;
            showToast('Error monitoring import progress', 'error');
        }
    }
}

function updateProgress(data) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressDetails = document.getElementById('progressDetails');
    const progressStats = document.getElementById('progressStats');
    
    const progress = data.progress || 0;
    
    progressBar.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    progressDetails.textContent = `Status: ${data.status} - ${data.processed_rows} / ${data.total_rows} rows`;
    
    progressStats.innerHTML = `
        <div class="stat-item">
            <div class="stat-value">${data.total_rows}</div>
            <div class="stat-label">Total Rows</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${data.processed_rows}</div>
            <div class="stat-label">Processed</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color: var(--success-color)">${data.success_count}</div>
            <div class="stat-label">Success</div>
        </div>
        <div class="stat-item">
            <div class="stat-value" style="color: var(--danger-color)">${data.error_count}</div>
            <div class="stat-label">Errors</div>
        </div>
    `;
}

// ============================================================================
// PRODUCT MANAGEMENT
// ============================================================================

function initializeProducts() {
    // Search input with debounce
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearch = e.target.value;
            currentPage = 1;
            loadProducts();
        }, 300);
    });
    
    // Active filter
    document.getElementById('activeFilter').addEventListener('change', (e) => {
        currentActiveFilter = e.target.value;
        currentPage = 1;
        loadProducts();
    });
    
    // Add product button
    document.getElementById('addProductBtn').addEventListener('click', () => {
        openProductModal();
    });
    
    // Bulk delete button
    document.getElementById('bulkDeleteBtn').addEventListener('click', () => {
        confirmAction(
            'Are you sure you want to delete ALL products? This action cannot be undone!',
            bulkDeleteProducts
        );
    });
    
    // Product modal handlers
    document.getElementById('closeProductModal').addEventListener('click', closeProductModal);
    document.getElementById('cancelProductBtn').addEventListener('click', closeProductModal);
    document.getElementById('productForm').addEventListener('submit', handleProductSubmit);
    
    // Load products initially
    loadProducts();
}

async function loadProducts() {
    const tbody = document.getElementById('productsTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading products...</td></tr>';
    
    try {
        let url = `${API_BASE}/products?page=${currentPage}&page_size=50`;
        
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }
        
        if (currentActiveFilter) {
            url += `&active=${currentActiveFilter}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        displayProducts(data);
        displayPagination(data);
        
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Error loading products</td></tr>';
        showToast('Error loading products', 'error');
    }
}

function displayProducts(data) {
    const tbody = document.getElementById('productsTableBody');
    
    if (data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.items.map(product => `
        <tr>
            <td><strong>${escapeHtml(product.sku)}</strong></td>
            <td>${escapeHtml(product.name)}</td>
            <td>${escapeHtml(product.description || '-')}</td>
            <td>${escapeHtml(product.price || '-')}</td>
            <td>
                <span class="status-badge ${product.active ? 'status-active' : 'status-inactive'}">
                    ${product.active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <button class="btn btn-small btn-primary" onclick="editProduct(${product.id})">✏️ Edit</button>
                <button class="btn btn-small btn-danger" onclick="deleteProduct(${product.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function displayPagination(data) {
    const pagination = document.getElementById('pagination');
    
    if (data.pages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">« Previous</button>`;
    
    // Page numbers
    for (let i = 1; i <= data.pages; i++) {
        if (i === 1 || i === data.pages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += `<span>...</span>`;
        }
    }
    
    // Next button
    html += `<button class="page-btn" ${currentPage === data.pages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">Next »</button>`;
    
    pagination.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    loadProducts();
}

function openProductModal(product = null) {
    editingProductId = product ? product.id : null;
    
    const modal = document.getElementById('productModal');
    const title = document.getElementById('productModalTitle');
    
    if (product) {
        title.textContent = 'Edit Product';
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productName').value = product.name;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price || '';
        document.getElementById('productActive').checked = product.active;
    } else {
        title.textContent = 'Add Product';
        document.getElementById('productForm').reset();
    }
    
    modal.classList.add('active');
}

function closeProductModal() {
    document.getElementById('productModal').classList.remove('active');
    editingProductId = null;
}

async function handleProductSubmit(e) {
    e.preventDefault();
    
    const productData = {
        sku: document.getElementById('productSku').value,
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value || null,
        price: document.getElementById('productPrice').value || null,
        active: document.getElementById('productActive').checked
    };
    
    try {
        let response;
        
        if (editingProductId) {
            response = await fetch(`${API_BASE}/products/${editingProductId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });
        } else {
            response = await fetch(`${API_BASE}/products`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(productData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save product');
        }
        
        showToast(editingProductId ? 'Product updated successfully' : 'Product created successfully', 'success');
        closeProductModal();
        loadProducts();
        
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/products/${id}`);
        const product = await response.json();
        openProductModal(product);
    } catch (error) {
        showToast('Error loading product', 'error');
    }
}

async function deleteProduct(id) {
    confirmAction('Are you sure you want to delete this product?', async () => {
        try {
            const response = await fetch(`${API_BASE}/products/${id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete product');
            }
            
            showToast('Product deleted successfully', 'success');
            loadProducts();
            
        } catch (error) {
            showToast('Error deleting product', 'error');
        }
    });
}

async function bulkDeleteProducts() {
    try {
        const response = await fetch(`${API_BASE}/products`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete products');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        loadProducts();
        
    } catch (error) {
        showToast('Error deleting products', 'error');
    }
}

// ============================================================================
// WEBHOOK MANAGEMENT
// ============================================================================

function initializeWebhooks() {
    document.getElementById('addWebhookBtn').addEventListener('click', () => {
        openWebhookModal();
    });
    
    document.getElementById('closeWebhookModal').addEventListener('click', closeWebhookModal);
    document.getElementById('cancelWebhookBtn').addEventListener('click', closeWebhookModal);
    document.getElementById('webhookForm').addEventListener('submit', handleWebhookSubmit);
}

async function loadWebhooks() {
    const container = document.getElementById('webhooksList');
    container.innerHTML = '<p class="loading">Loading webhooks...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/webhooks`);
        const webhooks = await response.json();
        
        if (webhooks.length === 0) {
            container.innerHTML = '<p class="loading">No webhooks configured</p>';
            return;
        }
        
        container.innerHTML = webhooks.map(webhook => `
            <div class="webhook-item">
                <div class="webhook-header">
                    <div>
                        <div class="webhook-title">${escapeHtml(webhook.name)}</div>
                        <span class="status-badge ${webhook.enabled ? 'status-active' : 'status-inactive'}">
                            ${webhook.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                    <div class="webhook-actions">
                        <button class="btn btn-small btn-success" onclick="testWebhook(${webhook.id})">🧪 Test</button>
                        <button class="btn btn-small btn-primary" onclick="editWebhook(${webhook.id})">✏️ Edit</button>
                        <button class="btn btn-small btn-danger" onclick="deleteWebhook(${webhook.id})">🗑️</button>
                    </div>
                </div>
                <div class="webhook-info">
                    <div><strong>URL:</strong> <span class="webhook-url">${escapeHtml(webhook.url)}</span></div>
                    <div><strong>Event:</strong> ${escapeHtml(webhook.event_type)}</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        container.innerHTML = '<p class="loading">Error loading webhooks</p>';
        showToast('Error loading webhooks', 'error');
    }
}

function openWebhookModal(webhook = null) {
    editingWebhookId = webhook ? webhook.id : null;
    
    const modal = document.getElementById('webhookModal');
    const title = document.getElementById('webhookModalTitle');
    
    if (webhook) {
        title.textContent = 'Edit Webhook';
        document.getElementById('webhookName').value = webhook.name;
        document.getElementById('webhookUrl').value = webhook.url;
        document.getElementById('webhookEvent').value = webhook.event_type;
        document.getElementById('webhookEnabled').checked = webhook.enabled;
    } else {
        title.textContent = 'Add Webhook';
        document.getElementById('webhookForm').reset();
    }
    
    modal.classList.add('active');
}

function closeWebhookModal() {
    document.getElementById('webhookModal').classList.remove('active');
    editingWebhookId = null;
}

async function handleWebhookSubmit(e) {
    e.preventDefault();
    
    const webhookData = {
        name: document.getElementById('webhookName').value,
        url: document.getElementById('webhookUrl').value,
        event_type: document.getElementById('webhookEvent').value,
        enabled: document.getElementById('webhookEnabled').checked
    };
    
    try {
        let response;
        
        if (editingWebhookId) {
            response = await fetch(`${API_BASE}/webhooks/${editingWebhookId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(webhookData)
            });
        } else {
            response = await fetch(`${API_BASE}/webhooks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(webhookData)
            });
        }
        
        if (!response.ok) {
            throw new Error('Failed to save webhook');
        }
        
        showToast(editingWebhookId ? 'Webhook updated successfully' : 'Webhook created successfully', 'success');
        closeWebhookModal();
        loadWebhooks();
        
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}`);
        const webhook = await response.json();
        openWebhookModal(webhook);
    } catch (error) {
        showToast('Error loading webhook', 'error');
    }
}

async function deleteWebhook(id) {
    confirmAction('Are you sure you want to delete this webhook?', async () => {
        try {
            const response = await fetch(`${API_BASE}/webhooks/${id}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete webhook');
            }
            
            showToast('Webhook deleted successfully', 'success');
            loadWebhooks();
            
        } catch (error) {
            showToast('Error deleting webhook', 'error');
        }
    });
}

async function testWebhook(id) {
    showToast('Testing webhook...', 'info');
    
    try {
        const response = await fetch(`${API_BASE}/webhooks/${id}/test`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`Webhook test successful! Status: ${result.status_code}, Time: ${result.response_time}s`, 'success');
        } else {
            showToast(`Webhook test failed: ${result.error || 'Unknown error'}`, 'error');
        }
        
    } catch (error) {
        showToast('Error testing webhook', 'error');
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function confirmAction(message, callback) {
    const modal = document.getElementById('confirmModal');
    const messageEl = document.getElementById('confirmMessage');
    const confirmBtn = document.getElementById('confirmActionBtn');
    const cancelBtn = document.getElementById('cancelConfirmBtn');
    
    messageEl.textContent = message;
    modal.classList.add('active');
    
    const handleConfirm = () => {
        modal.classList.remove('active');
        callback();
        cleanup();
    };
    
    const handleCancel = () => {
        modal.classList.remove('active');
        cleanup();
    };
    
    const cleanup = () => {
        confirmBtn.removeEventListener('click', handleConfirm);
        cancelBtn.removeEventListener('click', handleCancel);
    };
    
    confirmBtn.addEventListener('click', handleConfirm);
    cancelBtn.addEventListener('click', handleCancel);
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

