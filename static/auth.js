// handles both register.html and login.html
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("auth-form");
  const errorDiv = document.getElementById("error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorDiv.textContent = "";

    // collect all form fields into an object
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // decide endpoint by current page
    const endpoint = window.location.pathname.endsWith("register.html")
      ? "/register"
      : "/login";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();

      if (res.ok) {
        // on success, show message then go home
        const msg = endpoint === "/register" ?
          "Registration successful" :
          "Login successful";
        // you can replace alert with a nicer UI message if you like
        alert(msg);
        window.location.href = "/";
      } else {
        // show the error returned by the API
        errorDiv.textContent =
          json.detail ||
          Object.values(json).flat().join(", ") ||
          "Unknown error";
      }
    } catch (_) {
      errorDiv.textContent = "Server error. Please try again.";
    }
  });
});
