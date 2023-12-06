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

    $(document).on('click', '.dropdown-toggle', function () {
        var dropdown = $(this).siblings('.dropdown-menu');
        $('.dropdown-menu').not(dropdown).removeClass('show');
        dropdown.toggleClass('show');
    });

    // Close dropdown when clicking outside
    $(document).on('click', function (e) {
        if (!$(e.target).closest('.dropdown').length) {
            $('.dropdown-menu').removeClass('show');
        }
    });

    $("#show-feed-activity").click(function() {
        $(this).addClass("active-feed");
        $("#show-git-activity").removeClass("active-feed");
        // $("#show-manage-posts").removeClass("active-feed");

        $("#git-container").removeClass("active-container");
        // $("#manage-container").removeClass("active-container");
        $("#post-container").addClass("active-container");
        
        $("#create-accordion").addClass("crete-new-active");
        $("#toggle-create-window").removeClass("hide");
        $("#create-accordion").removeClass("hide");
    });

    $("#show-git-activity").click(function() {
        $(this).addClass("active-feed");
        $("#show-feed-activity").removeClass("active-feed");
        // $("#show-manage-posts").removeClass("active-feed");

        $("#post-container").removeClass("active-container");
        // $("#manage-container").removeClass("active-container");
        $("#git-container").addClass("active-container");

        $("#create-accordion").removeClass("crete-new-active");
        $("#toggle-create-window").addClass("hide");
        $("#create-accordion").addClass("hide");
    });

    // Code commented out because the manage posts feature is not implemented
    // separately from the feed activity feature, you can edit/delete posts on the feed
    // $("#show-manage-posts").click(function() {
    //     $(this).addClass("active-feed");
    //     $("#show-git-activity").removeClass("active-feed");
    //     $("#show-feed-activity").removeClass("active-feed");

    //     $("#post-container").removeClass("active-container");
    //     $("#git-container").removeClass("active-container");
    //     $("#manage-container").addClass("active-container");

    //     $("#create-accordion").addClass("crete-new-active");
    //     $("#toggle-create-window").removeClass("hide");
    //     $("#create-accordion").removeClass("hide");
    // });

    $("#toggle-create-window").click(function() {
        $("#create-accordion").toggleClass("expanded");
        $("#toggle-create-window .create-icon").toggleClass("hide");
    });

});