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
});