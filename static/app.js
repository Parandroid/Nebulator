// Nebulator Frontend Application

// Global state
let images = [];
let globalMinGray = 0;
let globalMaxGray = 255;
let imageOverrides = {}; // {filename: {min_gray, max_gray}}

// DOM elements (will be initialized in DOMContentLoaded)
let loadingEl;
let imageGridEl;
let emptyStateEl;
let globalMinGraySlider;
let globalMaxGraySlider;
let globalMinGrayValue;
let globalMaxGrayValue;
let applyBtn;
let exportBtn;

// Popup elements
let imagePopup;
let popupOverlay;
let popupContent;
let popupImage;
let popupImageContainer;
let popupFilename;
let popupClose;
let popupBgColor;
let popupBgColorText;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize DOM elements
    loadingEl = document.getElementById('loading');
    imageGridEl = document.getElementById('image-grid');
    emptyStateEl = document.getElementById('empty-state');
    globalMinGraySlider = document.getElementById('global-min-gray');
    globalMaxGraySlider = document.getElementById('global-max-gray');
    globalMinGrayValue = document.getElementById('global-min-gray-value');
    globalMaxGrayValue = document.getElementById('global-max-gray-value');
    applyBtn = document.getElementById('apply-btn');
    exportBtn = document.getElementById('export-btn');
    
    // Initialize popup elements
    imagePopup = document.getElementById('image-popup');
    popupOverlay = imagePopup?.querySelector('.popup-overlay');
    popupContent = imagePopup?.querySelector('.popup-content');
    popupImage = document.getElementById('popup-image');
    popupImageContainer = document.getElementById('popup-image-container');
    popupFilename = document.getElementById('popup-filename');
    popupClose = document.getElementById('popup-close');
    popupBgColor = document.getElementById('popup-bg-color');
    popupBgColorText = document.getElementById('popup-bg-color-text');
    
    // Check if all required elements exist
    if (!loadingEl) console.error('loadingEl not found');
    if (!imageGridEl) console.error('imageGridEl not found');
    if (!emptyStateEl) console.error('emptyStateEl not found');
    if (!globalMinGraySlider) console.error('globalMinGraySlider not found');
    if (!globalMaxGraySlider) console.error('globalMaxGraySlider not found');
    if (!globalMinGrayValue) console.error('globalMinGrayValue not found');
    if (!globalMaxGrayValue) console.error('globalMaxGrayValue not found');
    if (!applyBtn) console.error('applyBtn not found');
    if (!exportBtn) console.error('exportBtn not found');
    
    if (!loadingEl || !imageGridEl || !emptyStateEl || !globalMinGraySlider || 
        !globalMaxGraySlider || !globalMinGrayValue || !globalMaxGrayValue || !applyBtn || !exportBtn) {
        console.error('Required DOM elements not found - cannot continue');
        return;
    }
    
    await loadGlobalSettings();
    await loadImages();
    setupEventListeners();
    setupPopupListeners();
});

// Load global settings from server
async function loadGlobalSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        globalMinGray = data.min_gray;
        globalMaxGray = data.max_gray;
        
        globalMinGraySlider.value = globalMinGray;
        globalMaxGraySlider.value = globalMaxGray;
        globalMinGrayValue.textContent = globalMinGray;
        globalMaxGrayValue.textContent = globalMaxGray;
    } catch (error) {
        console.error('Failed to load global settings:', error);
    }
}

// Load images list
async function loadImages() {
    try {
        loadingEl.style.display = 'block';
        imageGridEl.innerHTML = '';
        emptyStateEl.style.display = 'none';
        
        const response = await fetch('/api/images');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        images = data.images || [];
        
        if (images.length === 0) {
            loadingEl.style.display = 'none';
            emptyStateEl.style.display = 'block';
            return;
        }
        
        // Load per-image settings
        await loadImageSettings();
        
        // Render all images
        renderImageGrid();
        
        loadingEl.style.display = 'none';
    } catch (error) {
        console.error('Failed to load images:', error);
        loadingEl.textContent = `Error loading images: ${error.message}. Please check the server.`;
    }
}

// Load settings for all images
async function loadImageSettings() {
    imageOverrides = {};
    for (const filename of images) {
        try {
            const response = await fetch(`/api/settings/${encodeURIComponent(filename)}`);
            if (!response.ok) {
                console.warn(`Failed to load settings for ${filename}: HTTP ${response.status}`);
                continue;
            }
            const data = await response.json();
            if (data.is_override) {
                imageOverrides[filename] = {
                    min_gray: data.min_gray,
                    max_gray: data.max_gray
                };
            }
        } catch (error) {
            console.error(`Failed to load settings for ${filename}:`, error);
            // Continue with other images even if one fails
        }
    }
}

// Render image grid
function renderImageGrid() {
    imageGridEl.innerHTML = '';
    
    images.forEach(filename => {
        const card = createImageCard(filename);
        imageGridEl.appendChild(card);
    });
}

// Create image card element
function createImageCard(filename) {
    const card = document.createElement('div');
    card.className = 'image-card';
    if (filename in imageOverrides) {
        card.classList.add('override-active');
    }
    card.dataset.filename = filename;
    
    const hasOverride = filename in imageOverrides;
    const minGray = hasOverride ? imageOverrides[filename].min_gray : globalMinGray;
    const maxGray = hasOverride ? imageOverrides[filename].max_gray : globalMaxGray;
    
    card.innerHTML = `
        <div class="image-preview-container">
            <img class="image-preview" 
                 src="/api/preview/${encodeURIComponent(filename)}?min_gray=${minGray}&max_gray=${maxGray}" 
                 alt="${filename}"
                 loading="lazy">
        </div>
        <div class="image-filename">${filename}</div>
        <div class="image-controls">
            <div class="override-toggle">
                <input type="checkbox" 
                       id="override-${filename}" 
                       ${hasOverride ? 'checked' : ''}
                       data-filename="${filename}">
                <label for="override-${filename}">Use custom settings</label>
            </div>
            <div class="override-controls ${hasOverride ? 'active' : ''}">
                <div class="override-control-group">
                    <label>Min Gray:</label>
                    <div class="override-slider-container">
                        <input type="range" 
                               class="override-slider override-min" 
                               min="0" 
                               max="255" 
                               value="${minGray}"
                               data-filename="${filename}">
                        <span class="override-value override-min-value">${minGray}</span>
                    </div>
                </div>
                <div class="override-control-group">
                    <label>Max Gray:</label>
                    <div class="override-slider-container">
                        <input type="range" 
                               class="override-slider override-max" 
                               min="0" 
                               max="255" 
                               value="${maxGray}"
                               data-filename="${filename}">
                        <span class="override-value override-max-value">${maxGray}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Setup event listeners for this card
    setupCardEventListeners(card, filename);
    
    return card;
}

// Setup event listeners for image card
function setupCardEventListeners(card, filename) {
    // Use more specific selectors to avoid issues with special characters in filename
    const checkbox = card.querySelector('input[type="checkbox"][data-filename]');
    const overrideControls = card.querySelector('.override-controls');
    const minSlider = card.querySelector('.override-slider.override-min');
    const maxSlider = card.querySelector('.override-slider.override-max');
    const minValue = card.querySelector('.override-min-value');
    const maxValue = card.querySelector('.override-max-value');
    const previewImg = card.querySelector('.image-preview');
    
    // Check if required elements exist
    if (!checkbox) console.error(`checkbox not found for ${filename}`);
    if (!overrideControls) console.error(`overrideControls not found for ${filename}`);
    if (!minSlider) console.error(`minSlider not found for ${filename}`);
    if (!maxSlider) console.error(`maxSlider not found for ${filename}`);
    if (!minValue) console.error(`minValue not found for ${filename}`);
    if (!maxValue) console.error(`maxValue not found for ${filename}`);
    if (!previewImg) console.error(`previewImg not found for ${filename}`);
    
    if (!checkbox || !overrideControls || !minSlider || !maxSlider || !minValue || !maxValue || !previewImg) {
        console.error(`Missing elements in card for ${filename} - skipping event listeners`);
        return;
    }
    
    // Add click handler to open popup
    previewImg.addEventListener('click', () => {
        openImagePopup(filename, previewImg.src);
    });
    
    // Toggle override
    checkbox.addEventListener('change', async (e) => {
        if (e.target.checked) {
            // Enable override
            overrideControls.classList.add('active');
            card.classList.add('override-active');
            
            // Initialize with current global values
            imageOverrides[filename] = {
                min_gray: globalMinGray,
                max_gray: globalMaxGray
            };
            
            minSlider.value = globalMinGray;
            maxSlider.value = globalMaxGray;
            minValue.textContent = globalMinGray;
            maxValue.textContent = globalMaxGray;
            
            // Save to server
            await saveImageOverride(filename, globalMinGray, globalMaxGray);
            
            // Update preview
            updateImagePreview(previewImg, filename, globalMinGray, globalMaxGray);
        } else {
            // Disable override
            overrideControls.classList.remove('active');
            card.classList.remove('override-active');
            
            delete imageOverrides[filename];
            
            // Remove from server
            await removeImageOverride(filename);
            
            // Update preview with global values
            updateImagePreview(previewImg, filename, globalMinGray, globalMaxGray);
        }
    });
    
    // Min slider change
    minSlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        minValue.textContent = value;
        
        if (checkbox.checked) {
            imageOverrides[filename].min_gray = value;
            saveImageOverride(filename, value, imageOverrides[filename].max_gray);
            updateImagePreview(previewImg, filename, value, imageOverrides[filename].max_gray);
        }
    });
    
    // Max slider change
    maxSlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        maxValue.textContent = value;
        
        if (checkbox.checked) {
            imageOverrides[filename].max_gray = value;
            saveImageOverride(filename, imageOverrides[filename].min_gray, value);
            updateImagePreview(previewImg, filename, imageOverrides[filename].min_gray, value);
        }
    });
}

// Update image preview
function updateImagePreview(img, filename, minGray, maxGray) {
    // Add timestamp to force reload
    const timestamp = new Date().getTime();
    img.src = `/api/preview/${encodeURIComponent(filename)}?min_gray=${minGray}&max_gray=${maxGray}&t=${timestamp}`;
}

// Save image override to server
async function saveImageOverride(filename, minGray, maxGray) {
    try {
        await fetch(`/api/settings/${encodeURIComponent(filename)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                min_gray: minGray,
                max_gray: maxGray
            })
        });
    } catch (error) {
        console.error(`Failed to save override for ${filename}:`, error);
    }
}

// Remove image override from server
async function removeImageOverride(filename) {
    try {
        await fetch(`/api/settings/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error(`Failed to remove override for ${filename}:`, error);
    }
}

// Setup global event listeners
function setupEventListeners() {
    // Check if elements exist before adding listeners
    if (!globalMinGraySlider || !globalMaxGraySlider || !applyBtn || !exportBtn) {
        console.error('Cannot setup event listeners: required elements are missing');
        return;
    }
    
    // Global min gray slider - only update display value, don't apply
    globalMinGraySlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (globalMinGrayValue) {
            globalMinGrayValue.textContent = value;
        }
    });
    
    // Global max gray slider - only update display value, don't apply
    globalMaxGraySlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (globalMaxGrayValue) {
            globalMaxGrayValue.textContent = value;
        }
    });
    
    // Apply button - apply settings and update all images
    applyBtn.addEventListener('click', handleApplySettings);
    
    // Export button
    exportBtn.addEventListener('click', handleExport);
}

// Handle Apply Settings button
async function handleApplySettings() {
    // Get current slider values
    const newMinGray = parseInt(globalMinGraySlider.value);
    const newMaxGray = parseInt(globalMaxGraySlider.value);
    
    // Update global state
    globalMinGray = newMinGray;
    globalMaxGray = newMaxGray;
    
    // Show loader
    if (loadingEl) {
        loadingEl.style.display = 'block';
        loadingEl.textContent = 'Applying settings and updating images...';
    }
    
    // Disable apply button during processing
    if (applyBtn) {
        applyBtn.disabled = true;
        applyBtn.textContent = 'Applying...';
    }
    
    try {
        // Update global settings on server
        await updateGlobalSettings(newMinGray, newMaxGray);
        
        // Update all previews that don't have overrides
        await updateAllNonOverriddenPreviews();
        
        // Hide loader
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to apply settings:', error);
        if (loadingEl) {
            loadingEl.textContent = `Error applying settings: ${error.message}`;
        }
    } finally {
        // Re-enable apply button
        if (applyBtn) {
            applyBtn.disabled = false;
            applyBtn.textContent = 'Apply Settings';
        }
    }
}

// Update global settings on server
async function updateGlobalSettings(minGray, maxGray) {
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                min_gray: minGray,
                max_gray: maxGray
            })
        });
    } catch (error) {
        console.error('Failed to update global settings:', error);
        throw error;
    }
}

// Update all previews for images without overrides (with loading indicator)
async function updateAllNonOverriddenPreviews() {
    const cards = document.querySelectorAll('.image-card');
    const updatePromises = [];
    
    cards.forEach(card => {
        const filename = card.dataset.filename;
        const checkbox = card.querySelector('input[type="checkbox"][data-filename]');
        
        // Only update if override is not active
        if (!checkbox || !checkbox.checked) {
            const previewImg = card.querySelector('.image-preview');
            if (previewImg) {
                // Update preview with new global values
                updateImagePreview(previewImg, filename, globalMinGray, globalMaxGray);
            }
        }
    });
    
    // Wait a bit for images to start loading
    await new Promise(resolve => setTimeout(resolve, 100));
}

// Update previews for images without overrides (legacy function for compatibility)
function updateNonOverriddenPreviews() {
    const cards = document.querySelectorAll('.image-card');
    cards.forEach(card => {
        const filename = card.dataset.filename;
        const checkbox = card.querySelector('input[type="checkbox"][data-filename]');
        
        // Only update if override is not active
        if (!checkbox || !checkbox.checked) {
            const previewImg = card.querySelector('.image-preview');
            if (previewImg) {
                updateImagePreview(previewImg, filename, globalMinGray, globalMaxGray);
            }
        }
    });
}

// Handle export
async function handleExport() {
    exportBtn.disabled = true;
    exportBtn.textContent = 'Exporting...';
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Successfully exported ${data.exported.length} images:\n${data.exported.join('\n')}`);
        } else {
            alert('Export failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed: ' + error.message);
    } finally {
        exportBtn.disabled = false;
        exportBtn.textContent = 'Export All Images';
    }
}

// Open image popup
async function openImagePopup(filename, imageSrc) {
    if (!imagePopup || !popupImage || !popupImageContainer || !popupFilename) {
        console.error('Popup elements not found');
        return;
    }
    
    // Set filename
    popupFilename.textContent = filename;
    
    // Create a new image to get dimensions
    const img = new Image();
    img.onload = () => {
        // Set image source
        popupImage.src = imageSrc;
        
        // Size popup to image (with some padding for controls)
        const padding = 100; // Space for header and controls
        const maxWidth = window.innerWidth * 0.95;
        const maxHeight = window.innerHeight * 0.95;
        
        let popupWidth = img.naturalWidth + 40; // Image width + padding
        let popupHeight = img.naturalHeight + padding; // Image height + header/controls
        
        // Constrain to viewport
        if (popupWidth > maxWidth) {
            const scale = maxWidth / popupWidth;
            popupWidth = maxWidth;
            popupHeight = popupHeight * scale;
        }
        if (popupHeight > maxHeight) {
            const scale = maxHeight / popupHeight;
            popupHeight = maxHeight;
            popupWidth = popupWidth * scale;
        }
        
        // Set popup content size
        if (popupContent) {
            popupContent.style.width = `${popupWidth}px`;
            popupContent.style.maxHeight = `${maxHeight}px`;
        }
        
        // Show popup
        imagePopup.style.display = 'flex';
        
        // Initialize background color
        if (popupBgColor && popupBgColorText) {
            const currentBg = popupImageContainer.style.backgroundColor || '#000000';
            popupBgColor.value = currentBg;
            popupBgColorText.value = currentBg;
            updatePopupBackground(currentBg);
        }
    };
    
    img.onerror = () => {
        console.error('Failed to load image for popup');
    };
    
    img.src = imageSrc;
}

// Close image popup
function closeImagePopup() {
    if (imagePopup) {
        imagePopup.style.display = 'none';
    }
}

// Update popup background color
function updatePopupBackground(color) {
    if (popupImageContainer) {
        popupImageContainer.style.backgroundColor = color;
    }
}

// Setup popup event listeners
function setupPopupListeners() {
    if (!popupClose || !popupOverlay || !popupBgColor || !popupBgColorText) {
        return;
    }
    
    // Close button
    popupClose.addEventListener('click', closeImagePopup);
    
    // Close on overlay click
    popupOverlay.addEventListener('click', closeImagePopup);
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && imagePopup && imagePopup.style.display !== 'none') {
            closeImagePopup();
        }
    });
    
    // Background color picker
    popupBgColor.addEventListener('input', (e) => {
        const color = e.target.value;
        if (popupBgColorText) {
            popupBgColorText.value = color;
        }
        updatePopupBackground(color);
    });
    
    // Background color text input
    popupBgColorText.addEventListener('input', (e) => {
        const color = e.target.value;
        // Validate hex color
        if (/^#[0-9A-F]{6}$/i.test(color)) {
            if (popupBgColor) {
                popupBgColor.value = color;
            }
            updatePopupBackground(color);
        }
    });
    
    // Sync color picker when text changes (on blur)
    popupBgColorText.addEventListener('blur', (e) => {
        let color = e.target.value;
        // Add # if missing
        if (!color.startsWith('#')) {
            color = '#' + color;
        }
        // Validate and update
        if (/^#[0-9A-F]{6}$/i.test(color)) {
            e.target.value = color;
            if (popupBgColor) {
                popupBgColor.value = color;
            }
            updatePopupBackground(color);
        } else {
            // Reset to current color if invalid
            if (popupBgColor) {
                e.target.value = popupBgColor.value;
            }
        }
    });
}

