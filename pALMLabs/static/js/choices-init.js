document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".choices-select").forEach(function (el) {
        new Choices(el, {
            removeItemButton: true,
            placeholder: true,
            placeholderValue: el.getAttribute("placeholder") || "Select options",
            searchEnabled: true,
            shouldSort: false
        });
    });
});