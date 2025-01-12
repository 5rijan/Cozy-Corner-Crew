// Univerval var
var mouseVirtualX=0
var mouseVirtualY=0
const textBoxes = [];
const images = [];
const colorswatches = [];
var currentUserName = null;
var dataAuthId = null;
var sitename = null;
var userId = null;



// ============================
// Helper Functions
// ============================


/**
 * Adjusts the shade of a hex color.
 * @param {string} color - The original hex color (e.g., "#ff0000").
 * @param {number} percent - The percentage to adjust the shade (-100 to 100).
 * @returns {string} - The adjusted hex color.
 */
function shadeColor(color, percent) {
    const num = parseInt(color.slice(1), 16);
    const amt = Math.round(2.55 * percent);
    let R = (num >> 16) + amt;
    let G = ((num >> 8) & 0x00FF) + amt;
    let B = (num & 0x0000FF) + amt;

    R = Math.max(0, Math.min(255, R));
    G = Math.max(0, Math.min(255, G));
    B = Math.max(0, Math.min(255, B));

    return "#" + ((1 << 24) + (R << 16) + (G << 8) + B).toString(16).slice(1).toUpperCase();
}

/* This updates the current mouse location for easy movement :) */
document.addEventListener('mousemove', function(event) {
    // Get the bounding rectangle of the canvas (virtualWhiteboard)
    const canvasRect = virtualWhiteboard.getBoundingClientRect();

    // Calculate the mouse position relative to the canvas (correct for zoom)
    mouseVirtualX  = ((event.clientX - canvasRect.left) / scale)-16;
    mouseVirtualY = ((event.clientY - canvasRect.top) / scale)-16;
});

/**
 * Converts a hex color to its RGBA representation.
 * @param {string} hex - The hex color (e.g., "#ff0000").
 * @param {number} alpha - The alpha value (default is 1).
 * @returns {string} - The RGBA color string.
 */
function hexToRgba(hex, alpha = 1) {
    const bigint = parseInt(hex.slice(1), 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Converts a hex color to RGB.
 * @param {string} hex - The hex color (e.g., "#ff0000").
 * @returns {object} - An object with r, g, b properties.
 */
function hexToRgb(hex) {
    const bigint = parseInt(hex.slice(1), 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return { r, g, b };
}

/**
 * Determines appropriate text color (black or white) based on background color.
 * @param {string} color - The background hex color (e.g., "#ff0000").
 * @returns {string} - The adjusted text color hex code.
 */
function determineTextColor(color) {
    const rgb = hexToRgb(color);
    const brightness = (rgb.r * 0.299 + rgb.g * 0.587 + rgb.b * 0.114);
    return brightness < 128 ? shadeColor(color, 30) : shadeColor(color, -30);
}

/**
 * Creates a copy button that copies the provided text to the clipboard.
 * @param {string} text - The text to copy.
 * @returns {HTMLElement} - The copy button element.
 */
function createCopyButton(text) {
    const button = document.createElement('button');
    button.textContent = `Copy`;
    button.classList.add('copy-button');
    button.style.marginTop = '5px';
    button.style.padding = '5px 10px';
    button.style.cursor = 'pointer';
    button.style.fontSize = '0.8em';
    button.onclick = () => {
        navigator.clipboard.writeText(text).then(() => {
            // Optional feedback to the user
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    };
    return button;
}

// ============================
// Component Classes
// ============================

/**
 * Class representing an image component with draggable and resizable functionalities.
 */


let selectedComponent = null;

class ImageComponent {
    constructor(imageUrl, altText, width, parentElement, initialX, initialY) {
        this.imageUrl = imageUrl;
        this.altText = altText;
        this.width = width;
        this.parentElement = parentElement;
        this.position = { x: initialX, y: initialY };
        this.scale = 1;
        this.zIndex = 10;
        this.selected = false;
        this.createElement();
        this.initDrag();
        this.initResize();
    }

    createElement() {
        this.container = document.createElement('div');
        this.container.style.position = 'absolute';
        this.container.style.left = `${this.position.x}px`;
        this.container.style.top = `${this.position.y}px`;
        this.container.style.zIndex = `${this.zIndex}`;
        this.container.style.display = 'inline-block';
        this.container.style.cursor = 'move';
        this.container.style.transformOrigin = 'top left';
        this.container.style.boxSizing = 'border-box';

        this.container.style.border = this.selected ? '2px solid blue' : 'none';

        this.img = document.createElement('img');
        this.img.src = this.imageUrl;
        this.img.alt = this.altText;
        this.img.style.width = `${this.width}px`;
        this.img.style.height = 'auto';
        this.img.style.display = 'block';
        this.img.style.pointerEvents = 'none';

        this.container.appendChild(this.img);

        this.resizeHandle = document.createElement('div');
        this.resizeHandle.style.width = '15px';
        this.resizeHandle.style.height = '15px';
        this.resizeHandle.style.background = 'rgba(0,0,0,0.5)';
        this.resizeHandle.style.position = 'absolute';
        this.resizeHandle.style.right = '0';
        this.resizeHandle.style.bottom = '0';
        this.resizeHandle.style.cursor = 'nwse-resize';

        this.container.appendChild(this.resizeHandle);

        this.downloadButton = document.createElement('img');
        this.downloadButton.src = 'static/resources/software-download.svg';
        this.downloadButton.style.position = 'absolute';
        this.downloadButton.style.width = '25px';
        this.downloadButton.style.height = '25px';
        this.downloadButton.style.right = '0';
        this.downloadButton.style.top = '0';
        this.downloadButton.style.cursor = 'pointer';
        this.downloadButton.style.display = 'none';  // Hidden initially
        this.downloadButton.addEventListener('click', () => this.downloadImage());

        this.container.appendChild(this.downloadButton);
        this.parentElement.appendChild(this.container);
    }

    /**
     * Initializes dragging functionality for the color swatch component.
     */
    initDrag() {
        let isDragging = false;
        let offset = { x: 0, y: 0 };

        // Handle mousedown on the container
        this.container.addEventListener('mousedown', (e) => {
            isDragging = true;
            this.selectComponent();
            const rect = this.container.getBoundingClientRect();
            offset.x = mouseVirtualX - this.position.x;
            offset.y = mouseVirtualY -this.position.y;
            document.body.style.cursor = 'grabbing';
            e.preventDefault(); // Prevent text selection
        });

        // Handle mousemove on the document
        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                let x = mouseVirtualX-offset.x;
                let y = mouseVirtualY-offset.y;
                this.updatePosition(x, y);
            }
        });

        // Handle mouseup on the document
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                document.body.style.cursor = 'default';
            }
        });
    }

    updatePosition(x, y) {
        this.container.style.left = `${x}px`;
        this.container.style.top = `${y}px`;
        this.position.x = x;
        this.position.y = y;
    }

    initResize() {
        let isResizing = false;
        let startX, startY, startWidth, startHeight;

        this.resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startY = e.clientY;
            startWidth = this.img.offsetWidth;
            startHeight = this.img.offsetHeight;
            document.body.style.cursor = 'nwse-resize';
            e.stopPropagation();
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (isResizing) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                const newWidth = Math.max(startWidth + dx, 100);
                const newHeight = Math.max(startHeight + dy, 100);

                this.img.style.width = `${newWidth}px`;
                this.img.style.height = `${newHeight}px`;

                this.container.style.width = `${newWidth}px`;
                this.container.style.height = `${newHeight}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
            }
        });
    }

    selectComponent() {
        if (selectedComponent && selectedComponent !== this) {
            selectedComponent.deselectComponent();
        }

        this.zIndex += 1;
        this.container.style.zIndex = `${this.zIndex}`;
        this.selected = true;
        this.container.style.border = '1px solid #FF7F50';
        this.downloadButton.style.display = 'block';  // Show download button
        selectedComponent = this;
    }

    deselectComponent() {
        this.zIndex -= 1;
        this.container.style.zIndex = `${this.zIndex}`;
        this.selected = false;
        this.container.style.border = 'none';
        this.downloadButton.style.display = 'none';  // Hide download button
    }

    downloadImage() {
        const a = document.createElement('a');
        a.href = this.img.src;
        a.download = this.altText || 'downloaded-image';
        a.click();
    }

    updateScale(scaleFactor) {
        this.scale = scaleFactor;
        this.container.style.transform = `scale(${this.scale})`;
    }
}



/**
 * Class representing a color swatch component with draggable and resizable functionalities.
 */
class ColorSwatchComponent {
    /**
     * Creates a ColorSwatchComponent instance.
     * @param {string} label - The label for the color swatch.
     * @param {string} color - The hex color code (e.g., "#ff0000").
     * @param {HTMLElement} parentElement - The parent DOM element to append this component.
     * @param {number} initialX - The initial X position (in pixels).
     * @param {number} initialY - The initial Y position (in pixels).
     */
    constructor(label, color, parentElement, initialX, initialY) {
        this.label = label;
        this.color = color;
        this.parentElement = parentElement;
        this.position = { x: initialX, y: initialY };
        this.scale = 1;
        this.zIndex = 10;
        this.selected = false;
        this.createElement();
        this.initDrag();
        this.initResize();
    }

    createElement() {
        // Container for the swatch and resize handle
        this.container = document.createElement('div');
        this.container.style.position = 'absolute';
        this.container.style.left = `${this.position.x}px`;
        this.container.style.top = `${this.position.y}px`;
        this.container.style.zIndex = `${this.zIndex}`;
        this.container.style.width = '200px';
        this.container.style.height = '200px';
        this.container.style.backgroundColor = this.color;
        this.container.style.borderRadius = '20px';
        this.container.style.cursor = 'move';
        this.container.style.transformOrigin = 'top left';
        this.container.style.boxSizing = 'border-box';
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.container.style.alignItems = 'center';
        this.container.style.justifyContent = 'center';
        this.container.style.padding = '10px';
        this.container.style.border = this.selected ? '2px solid blue' : 'none';

        // Label
        this.title = document.createElement('div');
        this.title.innerText = this.label;
        this.title.style.marginBottom = '10px';
        this.title.style.fontSize = '1.1em';
        this.title.style.fontWeight = 'bold';
        this.title.style.textAlign = 'center';
        this.title.style.color = determineTextColor(this.color);
        this.title.style.transition = 'font-size 0.2s';

        // Description
        this.description = document.createElement('div');
        this.description.style.fontSize = '1em';
        this.description.style.textAlign = 'center';
        this.description.style.color = determineTextColor(this.color);
        this.description.style.transition = 'font-size 0.2s';
        this.description.style.paddingTop = '5px';

        // Hex Value
        this.hexValue = document.createElement('div');
        this.hexValue.classList.add('color-info');
        this.hexValue.innerText = `Hex: ${this.color}`;
        this.hexValue.style.fontSize = '13px';
        this.hexValue.style.color = determineTextColor(this.color);
        this.hexValue.style.transition = 'font-size 0.2s';
        this.hexValue.style.display = 'flex'; 
        this.hexValue.style.alignItems = 'center'; 

        // Hex Copy Button
        this.hexCopyButton = createCopyButton(this.color);
        this.hexCopyButton.style.marginLeft = '5px'; // Space between text and button

        // RGBA Value
        this.rgbaValue = document.createElement('div');
        this.rgbaValue.classList.add('color-info');
        this.rgbaValue.innerText = `RGBA: ${hexToRgba(this.color)}`;
        this.rgbaValue.style.fontSize = '13px';
        this.rgbaValue.style.color = determineTextColor(this.color);
        this.rgbaValue.style.transition = 'font-size 0.2s';
        this.rgbaValue.style.display = 'flex'; 
        this.rgbaValue.style.alignItems = 'center';

        // RGBA Copy Button
        this.rgbaCopyButton = createCopyButton(hexToRgba(this.color));
        this.rgbaCopyButton.style.marginLeft = '5px'; // Space between text and button

        // Append elements to container
        this.container.appendChild(this.title);
        this.container.appendChild(this.description);
        this.container.appendChild(this.hexValue);
        this.container.appendChild(this.hexCopyButton);
        this.container.appendChild(this.rgbaValue);
        this.container.appendChild(this.rgbaCopyButton);

        // Create resize handle
        this.resizeHandle = document.createElement('div');
        this.resizeHandle.style.width = '15px';
        this.resizeHandle.style.height = '15px';
        this.resizeHandle.style.background = 'rgba(0,0,0,0.5)';
        this.resizeHandle.style.position = 'absolute';
        this.resizeHandle.style.right = '0';
        this.resizeHandle.style.bottom = '0';
        this.resizeHandle.style.cursor = 'nwse-resize';
        this.resizeHandle.style.userSelect = 'none';
        this.resizeHandle.style.borderRadius = '5px'; 

        // Append resize handle to container
        this.container.appendChild(this.resizeHandle);

        // Add Bulb Icon
        this.bulbIcon = document.createElement('div');
        this.bulbIcon.innerHTML = '🌕'; // Bulb icon
        this.bulbIcon.style.position = 'absolute';
        this.bulbIcon.style.top = '10px'; // Position it near the top
        this.bulbIcon.style.right = '10px'; // Position it near the right
        this.bulbIcon.style.cursor = 'pointer'; // Change cursor to pointer
        this.bulbIcon.style.fontSize = '20px'; // Size of the icon
        this.bulbIcon.style.zIndex = '20'; // Ensure it is above the swatch

        // Toggle text and button visibility on click
        this.bulbIcon.addEventListener('click', () => {
            const isHidden = this.title.style.display === 'none';
            this.title.style.display = isHidden ? 'block' : 'none';
            this.description.style.display = isHidden ? 'block' : 'none';
            this.hexValue.style.display = isHidden ? 'flex' : 'none';
            this.rgbaValue.style.display = isHidden ? 'flex' : 'none';
            this.hexCopyButton.style.display = isHidden ? 'inline' : 'none';
            this.rgbaCopyButton.style.display = isHidden ? 'inline' : 'none';
        });

        // Append bulb icon to container
        this.container.appendChild(this.bulbIcon);

        // Append container to parent
        this.parentElement.appendChild(this.container);
    }


    /**
     * Initializes dragging functionality for the color swatch component.
     */
    initDrag() {
        let isDragging = false;
        let offset = { x: 0, y: 0 };

        // Handle mousedown on the container
        this.container.addEventListener('mousedown', (e) => {
            isDragging = true;
            this.selectComponent();
            const rect = this.container.getBoundingClientRect();
            offset.x = mouseVirtualX - this.position.x;
            offset.y = mouseVirtualY -this.position.y;
            document.body.style.cursor = 'grabbing';
            e.preventDefault(); // Prevent text selection
        });

        // Handle mousemove on the document
        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                let x = mouseVirtualX-offset.x;
                let y = mouseVirtualY-offset.y;
                this.updatePosition(x, y);
            }
        });

        // Handle mouseup on the document
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                this.deselectComponent();
                document.body.style.cursor = 'default';
            }
        });
    }


    /**
     * Updates the component's position.
     * @param {number} x - New X position.
     * @param {number} y - New Y position.
     */
    updatePosition(x, y) {
        // Ensure the text box stays within the active tab boundaries
        this.container.style.left = `${x}px`;
        this.container.style.top = `${y}px`;
        this.position.x = x;
        this.position.y = y;
    }
       

    selectComponent() {
        // If there is already a selected component, deselect it
        if (selectedComponent && selectedComponent !== this) {
            selectedComponent.deselectComponent();
        }

        // Select this component and increase its zIndex
        this.zIndex += 1;
        this.container.style.zIndex = `${this.zIndex}`;
        this.selected = true;
        this.container.style.border = '1px solid #FF7F50'; // Highlight border
        selectedComponent = this;
    }


    deselectComponent() {
        this.zIndex -= 1; // Decrease the zIndex of the previously selected component
        this.container.style.zIndex = `${this.zIndex}`;
        this.selected = false;
        this.container.style.border = 'none'; // Remove the highlight
    }

    /**
     * Initializes resizing functionality for the color swatch component.
     */
    initResize() {
        let isResizing = false;
        let startX, startY, startWidth, startHeight;

        // Mouse down on the resize handle initiates resizing
        this.resizeHandle.addEventListener('mousedown', (e) => {
            if (isMoving) return; // Prevent resizing when grid is moving
            isResizing = true;
            startX = e.clientX;
            startY = e.clientY;
            startWidth = this.container.offsetWidth;
            startHeight = this.container.offsetHeight; // Store initial height
            document.body.style.cursor = 'nwse-resize';
            e.stopPropagation(); // Prevent dragging
            e.preventDefault();
        });

    // Mouse move adjusts the width and height
    document.addEventListener('mousemove', (e) => {
        if (isResizing && !isMoving) {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            const newWidth = Math.max(startWidth + dx, 200); 
            const newHeight = Math.max(startHeight + dy, 200); 

            this.container.style.width = `${newWidth}px`;
            this.container.style.height = `${newHeight}px`; // Adjust height

            // Define fixed base sizes for scaling
            const baseWidth = 250; // Base width for scaling
            const baseHeight = 550; // Base height for scaling

            // Calculate scale factors
            const scaleFactorWidth = newWidth / baseWidth;
            const scaleFactorHeight = newHeight / baseHeight;

            // Set maximum scale factor to avoid excessive growth
            const maxScaleFactor = 4; 
            this.scale = Math.min(scaleFactorWidth, scaleFactorHeight, maxScaleFactor); 

            // Define base font sizes in pixels
            const baseTitleFontSize = 50; 
            const baseDescriptionFontSize = 40; 
            const baseHexFontSize = 35; 
            const baseRgbaFontSize = 35; 

            // Update font sizes with proper template literals
            this.title.style.fontSize = `${baseTitleFontSize * this.scale}px`;
            this.description.style.fontSize = `${baseDescriptionFontSize * this.scale}px`;
            this.hexValue.style.fontSize = `${baseHexFontSize * this.scale}px`;
            this.rgbaValue.style.fontSize = `${baseRgbaFontSize * this.scale}px`;
        }
        });

        // Mouse up ends resizing
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
            }
        });
    }
}



// ============================
// Global Variables and State
// ============================

let isMoving = false; // Global flag to indicate if the grid is moving
let current_x = -5000; // Initial X position for components (center of 10000px grid)
let current_y = -5000; // Initial Y position for components
const spacing = 320;
const scaleStep = 0.1; 
let scale = 1;

const virtualWhiteboard = document.getElementById('virtual-whiteboard');
const moveButton = document.getElementById('toggleMove');
const coordinatesDisplay = document.getElementById('coordinates');

// ============================
// Event Listeners for Modals and Tabs
// ============================

// Event listener for showing the login modal
document.getElementById("login_btn").addEventListener("click", function() {
    const loginModal = document.getElementById("customlogin");
    loginModal.style.display = "block";
});

// Event listener for closing the login modal
document.getElementById("loginmodalclose").addEventListener("click", function() {
    const loginModal = document.getElementById("customlogin");
    loginModal.style.display = "none";
});

window.onclick = function(event) {
    var loginmodal = document.getElementById("customlogin");
    var alertmodal = document.getElementById("customAlert");
    if (event.target == loginmodal) {
        loginmodal.style.display = "none";
    } else if (event.target == alertmodal) {
        alertmodal.style.display = "none";
    }
};

// Event listeners for tab navigation
const tabs = document.querySelectorAll('.dropdown-content a');
const tabContents = document.querySelectorAll('.tab-content');
const dropdownBtn = document.querySelector('.dropbtn'); // Select the dropdown button

tabs.forEach(tab => {
    tab.addEventListener('click', function(e) {
        e.preventDefault();
        const tabId = this.getAttribute('data-tab');
        const tabText = this.textContent; 

        // Remove active class from all tab contents
        tabContents.forEach(content => content.classList.remove('active'));

        // Add active class to the selected tab content
        document.getElementById(tabId).classList.add('active');

        // Update the dropdown button text with the clicked tab's text
        dropdownBtn.textContent = tabText;
    });
});



// ============================
// Whiteboard Movement and Zooming
// ============================

// Toggle moving mode
moveButton.addEventListener('click', () => {
    isMoving = !isMoving;
    moveButton.textContent = isMoving ? 'Stop' : 'Move';
    virtualWhiteboard.style.cursor = isMoving ? 'grabbing' : 'grab';
});

// Variables for panning
let startX, startY, initialX, initialY;
let isDragging = false;

// Mouse down event on whiteboard
virtualWhiteboard.addEventListener('mousedown', (e) => {
    if (isMoving) {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        // Get current transform values
        const matrix = new WebKitCSSMatrix(window.getComputedStyle(virtualWhiteboard).transform);
        initialX = matrix.m41; // Current translation X
        initialY = matrix.m42; // Current translation Y
        virtualWhiteboard.style.cursor = 'grabbing';
        e.preventDefault();
    }
});

// Mouse move event on document
document.addEventListener('mousemove', (e) => {
    if (isDragging && isMoving) {
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        current_x = initialX + dx; // Update current X
        current_y = initialY + dy; // Update current Y
        updateTransform();
        updateCoordinates(current_x, current_y);
    }
});

// Mouse up event on document
document.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        virtualWhiteboard.style.cursor = 'grab';
    }
});

// Function to update the transform style
function updateTransform() {
    virtualWhiteboard.style.transform = `translate(${current_x}px, ${current_y}px) scale(${scale})`;
}

// Function to update the coordinates display
function updateCoordinates(x, y) {
    const centerOffset = 5000; 
    const relativeX = Math.round((x + centerOffset) / 25); 
    const relativeY = Math.round((y + centerOffset) / 25);
    coordinatesDisplay.textContent = `X: ${relativeX}, Y: ${relativeY}`;
}

// Initialize coordinates on page load
window.addEventListener('load', () => {
    updateCoordinates(current_x, current_y);
});

// Zoom In button
document.getElementById('zoomIn').addEventListener('click', () => {
    updateTransform(); 
    scale += scaleStep; 
    updateTransform(); 
});

// Zoom Out button
document.getElementById('zoomOut').addEventListener('click', () => {
    scale -= scaleStep;
    updateTransform(); 
});


// ============================
// Main Initialization Code
// ============================

window.onload = function () {
    // Retrieve session data from data attributes
    const sessionData = document.getElementById('session-data');
    currentUserName = sessionData.getAttribute('data-username');
    dataAuthId = sessionData.getAttribute('data-authid');
    sitename = sessionData.getAttribute('site-name');
    userId = sessionData.getAttribute('user-id');

    // Check if both username and auth id are present and valid (not "None" or empty)
    const isUserLoggedIn = currentUserName && currentUserName !== "None" && dataAuthId && dataAuthId !== "None";

    // Fetch data from '/get-features' route
    const urlPath = window.location.pathname;
    const url = urlPath.slice(1);

    fetch('/get-features', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const moodBoard = document.getElementById('mood-board');
            const components = document.getElementById('components');
            const fontTab = document.getElementById('font');
            const colorTab = document.getElementById('color');
    
            // Color tab coordinates and layout tracking
            let colorX = 4500;
            let colorY = 4800;
            const colorRowSpacing = 250;  
            const colorColumnSpacing = 220;  
    
            // Helper function to toggle between two rows for the layout
            const getNextPosition = (index) => {
                const rowIndex = index % 2; 
                const colIndex = Math.floor(index / 2); 
                return { x: colorX + colIndex * colorColumnSpacing, y: colorY + rowIndex * colorRowSpacing };
            };
    
            // Initialize components for Components tab
            var image = new ImageComponent(data.screenshot, 'Screenshot of the page', 300, components, colorX , colorY );
            images.push(image);
    
            // Now create a new ImageComponent instance for the moodBoard
            var moodBoardImage = new ImageComponent(data.screenshot, 'Screenshot of the page (Mood Board)', 300, moodBoard, colorX -350, colorY );
            images.push(moodBoardImage);
    
            // Initialize color swatches for Color tab and create new instances for MoodBoard
            let colorIndex = 0;
            data.color_json.forEach(jsonUrl => {
                fetch(jsonUrl)
                    .then(res => res.json())
                    .then(colors => {
                        // Process the color array from the JSON file
                        if (Array.isArray(colors)) {
                            colors.forEach(color => {
                                const { x, y } = getNextPosition(colorIndex++);
                                var colorswatch = new ColorSwatchComponent(color.name, color.hex, colorTab, x, y);
                                colorswatches.push(colorswatch);
    
                                // Create a new instance for MoodBoard
                                var moodBoardColorSwatch = new ColorSwatchComponent(color.name, color.hex, moodBoard, x, y);
                                colorswatches.push(moodBoardColorSwatch);
                            });
                        }
                    })
                    .catch(err => console.error('Error fetching JSON:', err));
            });
    
            // Initialize font images for Font tab
            let fontX = 4500;  
            let fontY = colorY + (2 * colorRowSpacing); 
            data.fontimages.forEach((imageUrl, index) => {
                const spacing = 350; 
                var image = new ImageComponent(imageUrl, 'Extracted Font Image', 300, fontTab, fontX + index * spacing - 100, fontY - 300);
                images.push(image);
    
                // Create new instances for MoodBoard (same row as fonts)
                var moodBoardFontImage = new ImageComponent(imageUrl, 'Extracted Font Image (Mood Board)', 300, moodBoard, fontX + index * spacing, fontY);
                images.push(moodBoardFontImage);
            });
    
            // Update the navigation bar based on whether the user is logged in (username and auth id are present)
            const loginBtn = document.getElementById('login_btn');
            const pricingLink = document.querySelector('.pricing-link'); 
            const userDashboardLink = document.getElementById('userDashboard'); 
    
            if (isUserLoggedIn) {
                // User is logged in (username and auth id are valid)
                loginBtn.style.display = 'none'; 
                pricingLink.style.display = 'none';
    
                // Show the dashboard link
                userDashboardLink.innerHTML = "Dashboard"; 
                userDashboardLink.href = "dashboard"; 
                userDashboardLink.style.display = 'flex';
                userDashboardLink.style.alignItems = 'center';  
                userDashboardLink.style.justifyContent = 'center';
            } else {
                // User is not logged in (username or auth id is missing or invalid)
                loginBtn.innerHTML = "Sign in"; 
                loginBtn.style.display = 'inline'; 
                pricingLink.style.display = 'flex'; 
                userDashboardLink.style.display = 'none'; 
            }
        } else {
            console.error('Error message:', data.message);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}


// ============================
// TextBox Class Definition
// ============================

class TextBox {
    constructor({ content = 'Click to edit', fontSize = 26, fontFamily = 'Arial', color = '#000000', scale = 1.0, zIndex = 1000 }) {
        this.content = content;
        this.fontSize = fontSize;
        this.fontFamily = fontFamily;
        this.color = color;
        this.position =  { x: mouseVirtualX, y: mouseVirtualY };
        this.scale = scale;
        this.zIndex = zIndex;

        // Create the DOM elements
        this.createElements();

        // Initialize event listeners
        this.addEventListeners();

        // Make the text box draggable
        this.makeDraggable();
    }

    // Method to create DOM elements
    createElements() {
        // Container for the text box and options
        this.container = document.createElement('div');
        this.container.classList.add('text-box-container');
        this.container.style.position = 'absolute';
        this.container.style.left = `${this.position.x}px`;
        this.container.style.top = `${this.position.y}px`;
        this.container.style.zIndex = this.zIndex;
        this.container.style.display = 'flex';
        this.container.style.alignItems = 'center';
        this.container.style.border = '1px solid transparent';
        this.container.style.padding = '5px';
        this.container.style.cursor = 'pointer';
        this.container.style.transform = `scale(${this.scale})`;

        // Editable text area
        this.textBox = document.createElement('div');
        this.textBox.classList.add('text-box');
        this.textBox.contentEditable = true;
        this.textBox.innerText = this.content;
        this.textBox.style.color = this.color;
        this.textBox.style.fontSize = `${this.fontSize}px`;
        this.textBox.style.fontFamily = this.fontFamily;
        this.textBox.style.backgroundColor = 'transparent';
        this.textBox.style.cursor = 'text';
        this.textBox.style.flexGrow = '1';
        this.textBox.style.outline = 'none'; // Remove default outline

        // Options container (hidden by default)
        this.optionsContainer = document.createElement('div');
        this.optionsContainer.classList.add('text-box-options');
        this.optionsContainer.style.position = 'absolute';
        this.optionsContainer.style.top = '0';
        this.optionsContainer.style.right = '-50px';
        this.optionsContainer.style.display = 'none';
        this.optionsContainer.style.flexDirection = 'column';
        this.optionsContainer.style.gap = '5px';
        this.optionsContainer.style.zIndex = '1001';

        // Define button styles
        const buttonStyle = `
            background-color: transparent;
            border: 1px solid #ccc;
            padding: 5px;
            border-radius: 5px;
            cursor: pointer;
            color: black;
            width: 30px;
            height: 30px;
            font-size: 16px;
        `;

        // Create Delete Button
        this.deleteBtn = document.createElement('button');
        this.deleteBtn.innerText = '×'; // Multiplication sign for better appearance
        this.deleteBtn.style.cssText = buttonStyle;
        this.deleteBtn.title = 'Delete Text Box';

        // Create Increase Font Size Button
        this.increaseFontBtn = document.createElement('button');
        this.increaseFontBtn.innerText = '+';
        this.increaseFontBtn.style.cssText = buttonStyle;
        this.increaseFontBtn.title = 'Increase Font Size';

        // Create Decrease Font Size Button
        this.decreaseFontBtn = document.createElement('button');
        this.decreaseFontBtn.innerText = '−'; // Minus sign
        this.decreaseFontBtn.style.cssText = buttonStyle;
        this.decreaseFontBtn.title = 'Decrease Font Size';

        // Create Change Font Style Button
        this.fontStyleBtn = document.createElement('button');
        this.fontStyleBtn.innerText = 'Aa';
        this.fontStyleBtn.style.cssText = buttonStyle;
        this.fontStyleBtn.title = 'Change Font Style';

        // Append buttons to options container
        this.optionsContainer.appendChild(this.deleteBtn);
        this.optionsContainer.appendChild(this.increaseFontBtn);
        this.optionsContainer.appendChild(this.decreaseFontBtn);
        this.optionsContainer.appendChild(this.fontStyleBtn);

        // Append options and text box to the container
        this.container.appendChild(this.optionsContainer);
        this.container.appendChild(this.textBox);

        // Append the container to the parent element (active tab)
        document.querySelector('.tab-content.active').appendChild(this.container);
    }

    // Method to add event listeners
    addEventListeners() {
        // Handle selection
        this.container.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering global deselect
            this.select();
        });

        // Handle deselection when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.deselect();
            }
        });

        // Handle Delete Button
        this.deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.delete();
            // Remove from the global textBoxes array
            TextBoxManager.removeTextBox(this);
        });

        // Handle Increase Font Size
        this.increaseFontBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeFontSize(1);
            // Update the global textBoxes array or perform other actions if needed
        });

        // Handle Decrease Font Size
        this.decreaseFontBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeFontSize(-1);
            // Update the global textBoxes array or perform other actions if needed
        });

        // Handle Change Font Style
        this.fontStyleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.changeFontStyle();
            // Update the global textBoxes array or perform other actions if needed
        });

        // Handle content changes (for real-time updates)
        this.textBox.addEventListener('input', () => {
            this.content = this.textBox.innerText;
            // Optionally, emit an event or callback for real-time updates
        });
    }

    // Method to select the text box
    select() {
        // Deselect any previously selected text boxes
        TextBoxManager.deselectAll();
        this.selected = true;
        this.optionsContainer.style.display = 'flex';
        this.container.style.border = '1px solid #FF7F50'; // Highlight border
        this.textBox.focus();
        TextBoxManager.selectedTextBox = this; // Track the currently selected text box
    }

    // Method to deselect the text box
    deselect() {
        if (this.selected) {
            this.selected = false;
            this.optionsContainer.style.display = 'none';
            this.container.style.border = '1px solid transparent';
            if (TextBoxManager.selectedTextBox === this) {
                TextBoxManager.selectedTextBox = null;
            }
        }
    }

    // Method to change font size
    changeFontSize(change) {
        this.fontSize += change;
        if (this.fontSize < 8) this.fontSize = 8; // Minimum font size
        this.textBox.style.fontSize = `${this.fontSize}px`;
    }

    // Method to change font style
    changeFontStyle() {
        const fonts = ['Arial', 'Times New Roman', 'Courier New', 'Georgia'];
        const currentIndex = fonts.indexOf(this.fontFamily);
        const nextFont = fonts[(currentIndex + 1) % fonts.length];
        this.fontFamily = nextFont;
        this.textBox.style.fontFamily = this.fontFamily;
    }

    // Method to delete the text box
    delete() {
        this.container.remove();
        this.selected = false;
        if (TextBoxManager.selectedTextBox === this) {
            TextBoxManager.selectedTextBox = null;
        }
    }

    // Method to make the text box draggable
    makeDraggable() {
        let isDragging = false;
        let offset = { x: 0, y: 0 };

        // Handle mousedown on the container
        this.container.addEventListener('mousedown', (e) => {
            isDragging = true;
            offset.x = mouseVirtualX - this.position.x;
            offset.y = mouseVirtualY - this.position.y;
            document.body.style.cursor = 'grabbing';
            e.preventDefault(); // Prevent text selection
        });

        // Handle mousemove on the document
        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const activeTab = document.querySelector('.tab-content.active');
                if (activeTab) {
                    let x = mouseVirtualX  - offset.x;
                    let y = mouseVirtualY - offset.y;

                    // Ensure the text box stays within the active tab boundaries
                    x = Math.max(0, Math.min(x, activeTab.clientWidth - this.container.clientWidth));
                    y = Math.max(0, Math.min(y, activeTab.clientHeight - this.container.clientHeight));

                    this.container.style.left = `${x}px`;
                    this.container.style.top = `${y}px`;
                    this.position = { x, y };
                }
            }
        });

        // Handle mouseup on the document
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                document.body.style.cursor = 'default';
            }
        });
    }


    // Method to serialize the text box state for storage
    serialize() {
        return {
            content: this.content,
            fontSize: this.fontSize,
            fontFamily: this.fontFamily,
            color: this.color,
            position: this.position,
            scale: this.scale,
            zIndex: this.zIndex
        };
    }

    // Static method to deserialize and create a TextBox instance
    static deserialize(data) {
        return new TextBox(data);
    }
}

// ============================
// TextBox Manager Singleton
// ============================

const TextBoxManager = (() => {
    let selectedTextBox = null;

    return {
        addTextBox: (textBox) => {
            textBoxes.push(textBox);
        },
        removeTextBox: (textBox) => {
            const index = textBoxes.indexOf(textBox);
            if (index > -1) {
                textBoxes.splice(index, 1);
            }
        },
        deselectAll: () => {
            textBoxes.forEach(tb => tb.deselect());
        },
        getAllTextBoxes: () => textBoxes,
        selectedTextBox: selectedTextBox
    };
})();


// ============================
// Initialization and Event Listeners
// ============================

let isAddingText = false;

// Toggle the text adding mode when the button is clicked
document.getElementById('addText').addEventListener('click', (e) => {
    e.stopPropagation();
    const button = document.getElementById('addText');

    if (!isAddingText) {
        isAddingText = true;
        document.getElementById('toggleEraser').style.backgroundColor = '#22303F';
        document.getElementById('toggleDraw').style.backgroundColor = '#22303F';
        button.style.backgroundColor = '#FF7F50';
    } else {
        isAddingText = false;
        button.style.backgroundColor = '#22303F';
        if (TextBoxManager.selectedTextBox) {
            TextBoxManager.selectedTextBox.deselect();
        }
    }
});

// Event listener for clicks on the main content area to add text boxes
document.querySelector('.main-content').addEventListener('click', (e) => {
    if (isAddingText) {
        const activeTab = document.querySelector('.tab-content.active'); // Get currently active tab
        if (activeTab) {
            // Calculate mouse position relative to the active tab
            const rect = activeTab.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Create a new TextBox instance
            const newTextBox = new TextBox({
                content: 'Click to edit',
                position: { x, y },
                parentElement: activeTab,
                zIndex: 1000 // Adjust as needed
            });

            // Add the new TextBox to the manager
            TextBoxManager.addTextBox(newTextBox);
        }

        // Exit adding text mode after adding one text box
        isAddingText = false;
        document.getElementById('addText').style.backgroundColor = '#22303F';
    }
});






let isDrawing = false;
let isErasing = false;
let selectedTextBox = null;
let ctx; 
let currentTabCanvas;
let lineSize = 3;
let lineColor = '#000000';



// ============================
// Add Draw and erase code 
// ============================

const lineSizeInput = document.getElementById('lineSize');
const lineColorInput = document.getElementById('lineColor');

// Toggle drawing mode when the button is clicked
document.getElementById('toggleDraw').addEventListener('click', (e) => {
    e.stopPropagation(); 
    const button = document.getElementById('toggleDraw');

    if (!isDrawing) {
        isDrawing = true; 
        isErasing = false;
        isAddingText = false; 
        button.style.backgroundColor = '#FF7F50'; 
        document.getElementById('toggleEraser').style.backgroundColor = '#22303F'; 
        document.getElementById('addText').style.backgroundColor = '#22303F'; 
    } else {
        isDrawing = false; 
        button.style.backgroundColor = '#22303F'; 
    }
});


// Set up line size and color controls
lineSizeInput.addEventListener('input', (e) => {
    lineSize = e.target.value;
});
lineColorInput.addEventListener('input', (e) => {
    lineColor = e.target.value;
});

// Event listener for erasing tool
document.getElementById('toggleEraser').addEventListener('click', (e) => {
    e.stopPropagation(); 
    const button = document.getElementById('toggleEraser');

    if (!isErasing) {
        isErasing = true; 
        isDrawing = false; 
        button.style.backgroundColor = '#FF7F50';
        document.getElementById('toggleDraw').style.backgroundColor = '#22303F'; 
        document.getElementById('addText').style.backgroundColor = '#22303F'; 

    } else {
        isErasing = false;
        button.style.backgroundColor = '#22303F';
    }
});

// Event listener for mouse movements on the whiteboard
document.querySelector('.main-content').addEventListener('mousedown', (e) => {
    if (isDrawing || isErasing) {
        e.preventDefault(); // Prevent text selection or other browser events
        const activeTab = document.querySelector('.tab-content.active'); // Get the currently active tab

        // Set up drawing context for this tab
        if (!currentTabCanvas) {
            currentTabCanvas = document.createElement('canvas');
            currentTabCanvas.width = activeTab.offsetWidth;
            currentTabCanvas.height = activeTab.offsetHeight;
            activeTab.appendChild(currentTabCanvas);
            ctx = currentTabCanvas.getContext('2d');
        }

        // Start drawing
        ctx.beginPath();
        ctx.moveTo(mouseVirtualX, mouseVirtualY);

        document.addEventListener('mousemove', draw);
        document.addEventListener('mouseup', () => {
            document.removeEventListener('mousemove', draw);
            ctx.closePath();
        });
    }
});

// Function to handle drawing
function draw(e) {
    if (isDrawing) {
        ctx.lineWidth = lineSize;
        ctx.strokeStyle = lineColor;
        ctx.lineCap = 'round';
        ctx.lineTo(mouseVirtualX, mouseVirtualY); // Draw lines with virtual mouse coordinates
        ctx.stroke();
    } else if (isErasing) {
        ctx.clearRect(mouseVirtualX - lineSize / 2, mouseVirtualY - lineSize / 2, lineSize, lineSize); // Erase
    }
}



// ============================
// Save button
// ============================


document.getElementById('save').addEventListener('click', function() {

    // Check if currentUserName and dataAuthId are null, undefined, empty, or 'none'
    if (!currentUserName || currentUserName === 'None' || currentUserName.trim() === '' ||
        !dataAuthId || dataAuthId === 'None' || dataAuthId.trim() === '') {
        showAlert();
        console.log(sitename)
    } else {
        showSavingpage();
        console.log(sitename)
    }
});



// Show the Save screen
function showSavingpage() {
    var modal = document.getElementById("saveScreen");
    modal.style.display = "block"; 

}

// Close the Save screen
document.getElementById("cancelButton").addEventListener("click", function() {
    var modal = document.getElementById("saveScreen");
    modal.style.display = "none";
});


// Function to show the custom alert modal
function showAlert() {
    var modal = document.getElementById("customAlert");
    var alertMessage = document.getElementById("alertMessage");
    alertMessage.innerHTML = "<strong style='font-size: 1.5em;'>You can't save cauz u aint logged in :).</strong> <br>";
    modal.style.display = "block"; 
}

// Close the custom alert modal when the OK button is clicked
document.getElementById("closeAlertButton").addEventListener("click", function() {
    var modal = document.getElementById("customAlert");
    modal.style.display = "none";
});




document.getElementById("addCollectionButton").addEventListener("click", function() {
    var collectionName = document.getElementById("newCollectionName").value;
    console.log(userId)

    fetch('/create-collection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: collectionName, user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error); 
        } else {
            // Handle success
            alert('Collection created: ' + data.collection.name);
            // Refresh the collections list or add the new collection to the UI
            window.location.reload();

        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});



document.getElementById('saveButton').addEventListener('click', function() {
    const saveName = document.getElementById('saveName').value.trim();
    const selectedCollections = Array.from(document.querySelectorAll('input[name="collection"]:checked')).map(input => input.value);
    
    // Check if the save name is empty
    if (!saveName) {
        alert("Please enter a name to save your board.");
        return;
    }

    // Prepare the data to send
    const data = {
        name: saveName,
        collections: selectedCollections,
        websiteName: sitename,
        userId: userId
    };

    // Send POST request to save the board
    fetch('/save_board', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())  
    .then(data => {
        if (data.message === "Board saved successfully.") {
            alert("Board saved successfully!");
            document.getElementById('saveScreen').style.display = 'none'; 
            window.location.reload();
        } else if (data.message === "Board limit reached for normal subscription.") {
            alert("Board limit reached! You cannot save more than 5 boards with a normal subscription.");
        } else {
            alert("Failed to save the board. Please try again.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("An error occurred while saving the board.");
    });
});



let isDownloadModeActive = false;
let downloadStartX, downloadStartY, downloadEndX, downloadEndY;
let downloadButton = document.getElementById('download');
let selectionBox = document.createElement('div');

// Style for the selection area (dotted lines and blue shade)
selectionBox.style.position = 'absolute';
selectionBox.style.border = '2px dashed #3498db';
selectionBox.style.backgroundColor = 'rgba(52, 152, 219, 0.3)';
selectionBox.style.pointerEvents = 'none';
document.body.appendChild(selectionBox);

// Set up download button click event
downloadButton.addEventListener('click', () => {
    if (!isDownloadModeActive) {
        // Enable download mode
        isDownloadModeActive = true;
        downloadButton.style.backgroundColor = '#FF7F50';  // Change button color to active state
        document.body.style.cursor = 'crosshair';          // Change cursor to crosshair
        disableSelection();                                // Disable text selection
    }
});

// Handle mouse down, move, and up events for dragging the screenshot area
document.addEventListener('mousedown', function (e) {
    if (isDownloadModeActive) {
        downloadStartX = e.clientX;
        downloadStartY = e.clientY;

        // Initialize the position of the selection box
        selectionBox.style.left = `${downloadStartX}px`;
        selectionBox.style.top = `${downloadStartY}px`;
        selectionBox.style.width = '0px';
        selectionBox.style.height = '0px';
        selectionBox.style.display = 'block';
    }
});

document.addEventListener('mousemove', function (e) {
    if (isDownloadModeActive) {
        downloadEndX = e.clientX;
        downloadEndY = e.clientY;

        // Update the size and position of the selection box
        selectionBox.style.width = `${Math.abs(downloadEndX - downloadStartX)}px`;
        selectionBox.style.height = `${Math.abs(downloadEndY - downloadStartY)}px`;
        selectionBox.style.left = `${Math.min(downloadStartX, downloadEndX)}px`;
        selectionBox.style.top = `${Math.min(downloadStartY, downloadEndY)}px`;
    }
});

document.addEventListener('mouseup', function (e) {
    if (isDownloadModeActive) {
        downloadEndX = e.clientX;
        downloadEndY = e.clientY;

        // Hide the selection box after the drag ends
        selectionBox.style.display = 'none';

        // Capture the selected area
        takeScreenshotOfSelection();

        // Auto-disable download mode after one capture
        isDownloadModeActive = false;
        downloadButton.style.backgroundColor = '#22303F';  
        document.body.style.cursor = 'default';            
        enableSelection();                                 
    }
});

// Function to capture the screenshot of the selected area
function takeScreenshotOfSelection() {
    // Calculate the width and height of the selected area
    const selectionWidth = Math.abs(downloadEndX - downloadStartX);
    const selectionHeight = Math.abs(downloadEndY - downloadStartY);
    const startX = Math.min(downloadStartX, downloadEndX);
    const startY = Math.min(downloadStartY, downloadEndY);

    // Hide the button temporarily to avoid capturing it in the screenshot
    downloadButton.style.display = 'none';

    // Use html2canvas to capture the screenshot
    html2canvas(document.body, {
        x: startX,
        y: startY,
        width: selectionWidth,
        height: selectionHeight
    }).then(canvas => {
        // Show the button again after capturing
        downloadButton.style.display = 'block';

        // Create an image link
        const link = document.createElement('a');
        link.href = canvas.toDataURL('image/png');  
        link.download = 'screenshot.png';           
        link.click();                               
    });
}

// Disable text selection
function disableSelection() {
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';
    document.body.style.mozUserSelect = 'none';
}

// Re-enable text selection
function enableSelection() {
    document.body.style.userSelect = 'auto';
    document.body.style.webkitUserSelect = 'auto';
    document.body.style.mozUserSelect = 'auto';
}

document.getElementById('viewGrid').addEventListener('click', function() {
    this.classList.toggle('active');
    
    // Get the virtual whiteboard element
    const whiteboard = document.getElementById('virtual-whiteboard');
    
    // Toggle the grid lines and background color
    if (this.classList.contains('active')) {
        // Hide all lines and set background to white
        whiteboard.style.backgroundImage = 'none';
        whiteboard.style.backgroundColor = '#ffffff'; // Set to white
    } else {
        // Restore the original grid lines and background color
        whiteboard.style.backgroundImage = 
            'linear-gradient(90deg, #e0e0e0 1px, transparent 1px), ' +
            'linear-gradient(180deg, #e0e0e0 1px, transparent 1px)';
        whiteboard.style.backgroundColor = ''; // Reset to default
    }
});


document.addEventListener('DOMContentLoaded', function() {
    // Remove spaces as the user types
    const urlInput = document.getElementById("urlInput");
    urlInput.addEventListener("input", function() {
        this.value = this.value.replace(/\s/g, ''); 
    });

    // Function to show the custom alert modal
    function showAlert() {
        var modal = document.getElementById("customAlert");
        var alertMessage = document.getElementById("alertMessage");
        alertMessage.innerHTML = "<strong style='font-size: 1.5em;'>That's not a valid URL. ☁️</strong> <br> Peew! We think you made a mistake while giving us the URL. Copy and paste the URL again of the webpage you want moodboard for.";
        modal.style.display = "block"; 
    }

    // Close the custom alert modal when the OK button is clicked
    document.getElementById("closeAlertButton").addEventListener("click", function() {
        var modal = document.getElementById("customAlert");
        modal.style.display = "none";
    });


    // Close the login modal when the OK button is clicked
    document.getElementById("loginmodalclose").addEventListener("click", function() {
        var loginmodal = document.getElementById("customlogin");
        loginmodal.style.display = "none"; 
    });

    window.onclick = function(event) {
        var loginmodal = document.getElementById("customlogin");
        var alertmodal = document.getElementById("customAlert");
        if (event.target == loginmodal) {
            loginmodal.style.display = "none";
        } else if (event.target == alertmodal) {
            alertmodal.style.display = "none";
        }
    };

    // Process Checker
    document.getElementById("processButton").addEventListener("click", function() {
        var url = urlInput.value;
        if (url === "" || !url.includes(".") || !/\.[a-zA-Z/]{2,}$/.test(url)) {
            showAlert(); 
            return;
        }

        document.getElementById("processButton").disabled = true;
        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;  
            } else {
                return response.json();
            }
        })
        .then(data => {
            if (data) {
                console.log('URL processed:', data);
                urlInput.value = "";  
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            showAlert();  
        })
        .finally(() => {
            document.getElementById("processButton").disabled = false;
        });
    
    });
});

