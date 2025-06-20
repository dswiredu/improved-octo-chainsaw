document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".tom-select").forEach(function (el) {
        new TomSelect(el, {
            plugins: {
                remove_button: {
                    title: 'Remove this item',
                }
            },
            placeholder: el.getAttribute("placeholder") || "Select options...",
            persist: false,
            allowEmptyOption: true,
            create: false,
            hideSelected: true,
            closeAfterSelect: false,
            maxItems: null
        });
    });
});