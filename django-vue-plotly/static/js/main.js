document.addEventListener("DOMContentLoaded", function () {
    window.stockApp = Vue.createApp({
        data() {
            return {
                loading: false, // Default state is NOT loading
            };
        },
        methods: {
            showSpinner() {
                this.loading = true; // Show spinner
            },
            hideSpinner() {
                this.loading = false; // Hide spinner after loading
            }
        },
        mounted() {
            this.loading = false; // Reset loading after page refresh
        }
    });

    stockApp.mount("#stockApp");
});
