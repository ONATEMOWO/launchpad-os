// Lightweight UI helpers for public and authenticated pages.
document.addEventListener("click", function (event) {
  const toggle = event.target.closest("[data-password-toggle]");

  if (!toggle) {
    return;
  }

  const targetId = toggle.getAttribute("data-password-target");
  const passwordInput = document.getElementById(targetId);

  if (!passwordInput) {
    return;
  }

  const isHidden = passwordInput.getAttribute("type") === "password";
  passwordInput.setAttribute("type", isHidden ? "text" : "password");
  toggle.textContent = isHidden ? "Hide" : "Show";
  toggle.setAttribute("aria-pressed", isHidden ? "true" : "false");
});
