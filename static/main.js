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


    // Show login modal when the "Sign in" button is clicked
    document.getElementById("login_btn").addEventListener("click", function() {
        var loginmodal = document.getElementById("customlogin");
        loginmodal.style.display = "block";
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
