document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("form");
    const spinner = document.getElementById("spinner");
    const submitBtn = document.getElementById("submitBtn");

    form.addEventListener("submit", function () {
        spinner.style.display = "block";
        submitBtn.disabled = true;

        // Spinner'ı 5 saniyede kapat + formu sıfırla
        setTimeout(() => {
            spinner.style.display = "none";
            submitBtn.disabled = false;
            form.reset(); // ✅ form sıfırlanır
        }, 5000);
    });
});
