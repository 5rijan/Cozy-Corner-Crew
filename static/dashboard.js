const sessionData = document.getElementById('session-data');
const currentUserName = sessionData.getAttribute('data-username');
const dataAuthId = sessionData.getAttribute('data-authid');
const user_id = sessionData.getAttribute('data-user-id');
const boards = JSON.parse(sessionData.getAttribute('data-boards'));
const collections = JSON.parse(sessionData.getAttribute('data-collections'));



function showTab(tabName) {
    var designsTab = document.getElementById('designs');
    var collectionsTab = document.getElementById('collections');
    var addButtons = document.getElementById('addButtons');
    var allDesignsTab = document.getElementById('allDesignsTab');
    var collectionsTabButton = document.getElementById('collectionsTab');
    var underline = document.querySelector('.underline');

    // Show or hide the content based on the selected tab
    if (tabName === 'designs') {
        designsTab.style.display = 'block';
        collectionsTab.style.display = 'none';
        addButtons.style.display = 'none';
        underline.style.left = '0'; // Move underline to All Designs
        allDesignsTab.classList.add('active');
        collectionsTabButton.classList.remove('active');
    } else {
        designsTab.style.display = 'none';
        collectionsTab.style.display = 'block';
        addButtons.style.display = 'flex'; // Show Add buttons
        underline.style.left = '12%'; // Move underline to Collections
        allDesignsTab.classList.remove('active');
        collectionsTabButton.classList.add('active');
    }
}

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


    window.onclick = function(event) {
        var alertmodal = document.getElementById("customAlert");
        if (event.target == alertmodal) {
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
    
    const boardsContainer = document.getElementById("boardsContainer");
    const collectionsContainer = document.getElementById("collectionsContainer");
    
    // Render boards as cards
    boards.forEach(board => {
        const card = document.createElement('div');
        card.classList.add('board-card');
        card.innerHTML = `
            <div class="card-image">
                <img src="${board.screenshot}" alt="${board.name}">
            </div>
            <div class="card-details">
                <div class="card-title">${board.name}</div>
                <div class="card-link">${board.website_name}</div>
                <div class="card-options">
                    <button class="dropdown-btn">⋮</button>
                    <div class="dropdown-content">
                        <a href="#" class="board-edit" data-board-id="${board.id}">Edit</a>
                        <a href="#" class="board-delete" data-board-id="${board.id}">Delete</a>
                        <a href="#" class="board-download" data-board-id="${board.id}">Download</a>
                    </div>
                </div>
            </div>
        `;
    
        // Attach click event listener to the card itself
        card.addEventListener('click', function(event) {
            // Prevent action on dropdown links (Edit/Delete/Download)
            if (!event.target.classList.contains('dropdown-btn') &&
                !event.target.classList.contains('board-edit') &&
                !event.target.classList.contains('board-delete') &&
                !event.target.classList.contains('board-download')) {
                    
                // Send a POST request to process the board URL
                fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ url: board.website_name })
                })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;  // Redirect if the response is redirected
                    } else {
                        return response.json();
                    }
                })
                .then(data => {
                    if (data) {
                        console.log('URL processed:', data);
                    }
                })
                .catch((error) => {
                    console.error('Error:', error);
                    showAlert();  // Show alert if there's an error
                });
            }
        });
    
        // Append the card to the container
        boardsContainer.appendChild(card);
    });
    
    // Event delegation for board dropdown actions (Edit, Delete, Download)
    boardsContainer.addEventListener('click', function(event) {
        const target = event.target;
    
        if (target.classList.contains('board-edit')) {
            event.preventDefault();
            const boardId = target.getAttribute('data-board-id');
            const boardIdDisplay = document.getElementById("board_id");
            boardIdDisplay.setAttribute("data-board-id", boardId);   
            console.log(`Edit board with ID: ${boardId}`);
            document.getElementById("editBoardModal").style.display = "block";
        }
    
        if (target.classList.contains('board-delete')) {
            event.preventDefault();
            const boardId = target.getAttribute('data-board-id');
            const confirmation = confirm("Are you sure you want to permanently delete this board?");
            
            if (confirmation) {
                // If user confirms, send the delete request
                fetch(`/delete_board/${boardId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        // Handle success
                        alert("Board deleted successfully.");
                        window.location.reload(); // Refresh the page after deletion
                    } else {
                        // Handle error
                        console.error("Error deleting board:", response.statusText);
                    }
                })
                .catch(error => {
                    console.error("Network error:", error);
                });
            } else {
                console.log("Board deletion canceled.");
            }
        }
    
        if (target.classList.contains('board-download')) {
            event.preventDefault();
            const boardId = target.getAttribute('data-board-id');
            console.log(`Download board with ID: ${boardId}`);
        }
    });
    
    // Render collections as cards
    collections.forEach(collection => {
        const folderCard = document.createElement('div');
        folderCard.classList.add('folder-card');
        
        const folderImage = collection.boards.length > 0 
            ? collection.boards[0].screenshot 
            : 'static/resources/empty-folder.png';
        
        const boardCountText = collection.boards.length > 0 
            ? `${collection.boards.length} Designs` 
            : 'Empty Folder';
        
        folderCard.innerHTML = `
            <div class="folder-image">
                <img src="${folderImage}" alt="Folder Image">
            </div>
            <div class="folder-name">${collection.name}</div>
            <div class="folder-info">${boardCountText}</div>
        `;
        
        // Click to show collection modal
        folderCard.addEventListener('click', function() {
            showCollectionPopup(collection.id, collection.name, collection.boards);
        });
    
        collectionsContainer.appendChild(folderCard);
    });
    
    // Function to show the collection popup
    function showCollectionPopup(collectionId, collectionName, boards) {
        const modal = document.getElementById("collectionModal");
        const boardsList = document.getElementById("boardsList");
        const collectionTitle = document.getElementById("collectionName");
    
        // Clear previous content
        boardsList.innerHTML = '';
    
        // Set collection name
        collectionTitle.innerText = collectionName;
    
        // Render boards as cards
        boards.forEach(board => {
            const boardCard = document.createElement('div');
            boardCard.classList.add('board-card');
            boardCard.innerHTML = `
                <div class="card-image">
                    <img src="${board.screenshot}" alt="${board.name}">
                </div>
                <div class="card-details">
                    <div class="card-title">${board.name}</div>
                    <div class="card-link">${board.website_name}</div>
                    <div class="card-options">
                        <button class="dropdown-btn">⋮</button>
                        <div class="dropdown-content">
                            <a href="#" class="board-edit" data-board-id="${board.id}">Edit</a>
                            <a href="#" class="board-delete" data-board-id="${board.id}">Delete</a>
                            <a href="#" class="board-download" data-board-id="${board.id}">Download</a>
                        </div>
                    </div>
                </div>
            `;
            
            // Attach click event listener to the card itself
            boardCard.addEventListener('click', function(event) {
                // Prevent action on dropdown links (Edit/Delete/Download)
                if (!event.target.classList.contains('dropdown-btn') &&
                    !event.target.classList.contains('board-edit') &&
                    !event.target.classList.contains('board-delete') &&
                    !event.target.classList.contains('board-download')) {
                        
                    // Send a POST request to process the board URL
                    fetch('/process', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ url: board.website_name })
                    })
                    .then(response => {
                        if (response.redirected) {
                            window.location.href = response.url;  // Redirect if the response is redirected
                        } else {
                            return response.json();
                        }
                    })
                    .then(data => {
                        if (data) {
                            console.log('URL processed:', data);
                        }
                    })
                    .catch((error) => {
                        console.error('Error:', error);
                        showAlert();  // Show alert if there's an error
                    });
                }
            });

            boardsList.appendChild(boardCard);
        });


        // Show modal
        const collectionIdDisplay = document.getElementById("collection_id");
        collectionIdDisplay.setAttribute("collection-board-id", collectionId); 
        modal.style.display = "block";
    }
    

    // Event delegation for modal dropdown actions
    document.getElementById("boardsList").addEventListener('click', function(event) {
        const target = event.target;
    
        if (target.classList.contains('board-edit')) {
            event.preventDefault();
            const boardId = target.getAttribute('data-board-id');
            const boardIdDisplay = document.getElementById("board_id");
            boardIdDisplay.setAttribute("data-board-id", boardId);   
            console.log(`Edit board with ID: ${boardId} in modal`);
            document.getElementById("editBoardModal").style.display = "block";
        }    
    
        // Deleting a board with confirmation and POST request
        if (target.classList.contains('board-delete')) {
            event.preventDefault();
            const boardId = target.getAttribute('data-board-id');
            
            // Show a confirmation alert
            const confirmation = confirm("Are you sure you want to delete this collection? This action is irreversible.");
            
            if (confirmation) {
                // If user confirms, send the delete request
                fetch(`/delete_board/${boardId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        // Handle success
                        alert("Board deleted successfully.");
                        window.location.reload(); // Refresh the page after deletion
                    } else {
                        // Handle error
                        console.error("Error deleting board:", response.statusText);
                    }
                })
                .catch(error => {
                    console.error("Network error:", error);
                });
            } else {
                console.log("Board deletion canceled.");
            }
        }

    
            if (target.classList.contains('board-download')) {
                event.preventDefault();
                const boardId = target.getAttribute('data-board-id');
                console.log(`Download board with ID: ${boardId} in modal`);
            }
        });
    
        // Cancel button for closing the modal
        document.getElementById("cancelEditBoardButton").addEventListener("click", function() {
            document.getElementById("editBoardModal").style.display = "none";
        });


        // Save button to capture the new board name and send a POST request to update it
        document.getElementById("saveEditBoardButton").addEventListener("click", function() {
            const newBoardName = document.getElementById("newBoardName").value;
            const boardId = document.getElementById("board_id").getAttribute("data-board-id");
            // Check if the new board name is empty
            if (!newBoardName.trim()) {
                alert("Board name cannot be empty!");
                return; // Exit the function if the name is empty
            }
            // Log the new board name and ID
            console.log("New board name:", newBoardName, "to the board_id:", boardId); 

            // Send POST request to update the board
            fetch(`/update_board/${boardId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: newBoardName })
            })
            .then(response => {
                if (response.ok) {
                    // Handle success
                    console.log("Board updated successfully!");
                    window.location.reload(); 
                } else {
                    // Handle error
                    console.error("Error updating board:", response.statusText);
                }
            })
            .catch(error => {
                console.error("Network error:", error);
            });

            document.getElementById("editBoardModal").style.display = "none";
        });


        // Handle dropdown toggle visibility
        document.addEventListener('click', function(event) {
            if (event.target.classList.contains('dropdown-btn')) {
                event.stopPropagation(); 
                const dropdownContent = event.target.nextElementSibling;
                dropdownContent.classList.toggle('show');
            } else {
                // Close all dropdowns if clicked outside
                document.querySelectorAll('.dropdown-content').forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
            }
        });
    
        // Close the modal when clicking outside the content
        window.onclick = function(event) {
            const modal = document.getElementById("collectionModal");
            if (event.target === modal) {
                modal.style.display = "none";
            }
        };
});    


// Close the addcollection screen
document.getElementById("collection-close-button").addEventListener("click", function() {
    var modal = document.getElementById("collectionModal");
    modal.style.display = "none";
});


// Show the addcollection screen
document.getElementById('add-collection').addEventListener('click', function() {
    var modal = document.getElementById("addCollectionScreen");
    modal.style.display = "block";

});


// Close the addcollection screen
document.getElementById("cancelCreateButton").addEventListener("click", function() {
    var modal = document.getElementById("addCollectionScreen");
    modal.style.display = "none";
});



function editCollection() {
    const collection_id = document.getElementById("collection_id").getAttribute("collection-board-id");
    const editmodal = document.getElementById("editCollectionModal");
    editmodal.style.display = "block";
    console.log("Edit request made", collection_id);

    // Get references to the input field and buttons
    const newCollectionNameInput = document.getElementById("newCollectionNameEdit");
    const saveButton = document.getElementById("saveEditCollectionButton");
    const cancelButton = document.getElementById("cancelEditCollectionButton");

    // Event listener for the Save button
    saveButton.onclick = async function() {
        const newName = newCollectionNameInput.value;

        if (!newName) {
            alert("Please enter a new name for the collection.");
            return;
        }

        // Sending POST request to update collection name
        const response = await fetch(`/edit-collection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                collection_id: collection_id,
                new_name: newName
            })
        });

        if (response.ok) {
            console.log(`Collection ID ${collection_id} name changed to ${newName}`);
            window.location.reload();
           
        } else {
            console.error('Failed to update collection name');
        }

        editmodal.style.display = "none"; // Close the modal after saving
    };

    // Event listener for the Cancel button
    cancelButton.onclick = function() {
        editmodal.style.display = "none"; // Close the modal without any action
    };
}


function deleteCollection() {
    const collection_id = document.getElementById("collection_id").getAttribute("collection-board-id");
    console.log("Delete request initiated for collection ID:", collection_id);

    // Show confirmation alert
    const userConfirmed = confirm("Are you sure you want to delete this collection? This action is irreversible.");

    if (userConfirmed) {
        // If user confirms, send the delete request to the backend
        fetch(`/delete-collection`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                collection_id: collection_id
            })
        })
        .then(response => {
            if (response.ok) {
                console.log(`Collection ID ${collection_id} deleted successfully.`);
                // Optionally, you can remove the collection from the UI or reload the page
                alert("Collection deleted successfully.");
                // Reload the page or update the UI after deletion
                location.reload();
            } else {
                console.error("Failed to delete the collection.");
                alert("There was an error deleting the collection.");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Something went wrong. Please try again.");
        });
    } else {
        console.log("User canceled the deletion.");
    }
}

document.getElementById("createButton").addEventListener("click", function() {
    var collectionName = document.getElementById("newCollectionName").value;
    var userId = user_id;

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
            location.reload();
            // Refresh the collections list or add the new collection to the UI
            document.getElementById("addCollectionScreen").style.display = "none";
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});





