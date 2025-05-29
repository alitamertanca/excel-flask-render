document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const spinner = document.getElementById("spinner");
    const submitBtn = document.getElementById("submitBtn");

    form.addEventListener("submit", function () {
        spinner.style.display = "block";
        submitBtn.disabled = true;
    });
});
