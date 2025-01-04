function toggleFAQ(element) {
    const answer = element.nextElementSibling;
    const arrow = element.querySelector('.arrow');

    if (answer.style.display === "block") {
        answer.style.display = "none";
        arrow.textContent = "+"; 
    } else {
        answer.style.display = "block";
        arrow.textContent = "-"; 
    }
}

// Show login modal when the "Sign in" button is clicked
document.getElementById("login_btn").addEventListener("click", function() {
    var loginmodal = document.getElementById("customlogin");
    loginmodal.style.display = "block"; 
});


// Show login modal when the "Sign in" button is clicked
document.getElementById("login_btn2").addEventListener("click", function() {
    var loginmodal = document.getElementById("customlogin");
    loginmodal.style.display = "block"; 
});


// Show login modal when the "Sign in" button is clicked
document.getElementById("login_btn3").addEventListener("click", function() {
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
    if (event.target == loginmodal) {
        loginmodal.style.display = "none"; 
    } 
};
