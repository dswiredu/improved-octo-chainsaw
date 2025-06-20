document.body.addEventListener("htmx:beforeSwap", function(evt) {
    document.querySelectorAll(".bk-Tooltip").forEach(t => t.remove());
});