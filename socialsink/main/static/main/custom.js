document.addEventListener("DOMContentLoaded", function () {
    var dropdownButtons = document.querySelectorAll('.dropdown-toggle');

    dropdownButtons.forEach(function (button) {
        var dropdownMenu = button.nextElementSibling;

        button.addEventListener('click', function () {
            dropdownMenu.classList.toggle('show');
        });

        // Close the dropdown menu when clicking outside of it
        window.addEventListener('click', function (event) {
            if (!button.contains(event.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    });

    $("#show-feed-activity").click(function() {
        $("#show-feed-activity").addClass("active-feed");
        $("#show-git-activity").removeClass("active-feed");
        $("#post-container").addClass("active-container");
        $("#create-accordion").addClass("crete-new-active");
        $("#toggle-create-window").removeClass("hide");
        $("#create-accordion").removeClass("hide");
    });

    $("#show-git-activity").click(function() {
        $("#show-git-activity").addClass("active-feed");
        $("#show-feed-activity").removeClass("active-feed");
        $("#post-container").removeClass("active-container");
        $("#create-accordion").removeClass("crete-new-active");
        $("#toggle-create-window").addClass("hide");
        $("#create-accordion").addClass("hide");
    });

    $("#toggle-create-window").click(function() {
        $("#create-accordion").toggleClass("expanded");
        $("#toggle-create-window .create-icon").toggleClass("hide");
    });

});