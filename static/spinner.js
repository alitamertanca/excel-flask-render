document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("form");
    const spinner = document.getElementById("spinner");
    const submitBtn = document.getElementById("submitBtn");

    form.addEventListener("submit", function () {
        spinner.style.display = "block";
        submitBtn.disabled = true;

        // Spinner'ı 10 saniye sonra otomatik gizle
        setTimeout(() => {
            spinner.style.display = "none";
            submitBtn.disabled = false;
        }, 10000); // işlem ortalama süresine göre ayarlanabilir
    });
});
