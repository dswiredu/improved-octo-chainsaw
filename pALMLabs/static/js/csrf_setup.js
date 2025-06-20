document.body.addEventListener("htmx:configRequest", (event) => {
    const token = document.querySelector('meta[name="csrf-token"]').content;
    if (token) {
        event.detail.headers["X-CSRFToken"] = token;
    }
});