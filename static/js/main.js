document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("bite-form");
  const submitBtn = document.getElementById("submit-btn");
  const progress = document.getElementById("progress");

  if (!form || !submitBtn) return;

  form.addEventListener("submit", () => {
    submitBtn.disabled = true;
    submitBtn.dataset.originalText = submitBtn.textContent;
    submitBtn.textContent = "Generating...";

    if (progress) {
      progress.classList.remove("hidden");
    }
  });
});
