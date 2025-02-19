 // Function to hide the popup after 5 seconds
 setTimeout(function() {
    var popup = document.getElementById("popup");
    if (popup) {
      popup.style.display = "none";
    }
  }, 5000); // 5000 milliseconds = 5 seconds