// handles your index.html calculator form(s)
document.addEventListener("DOMContentLoaded", () => {
  // assume each form has class="calc-form" and data-op="add" | "subtract" | etc.
  document.querySelectorAll(".calc-form").forEach((form) => {
    const resultEl = form.querySelector(".result");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      resultEl.textContent = "";

      const a = parseFloat(form.querySelector("input[name='a']").value);
      const b = parseFloat(form.querySelector("input[name='b']").value);
      const op = form.dataset.op;  // e.g. "add", "subtract", "multiply", "divide"

      try {
        const res = await fetch(`/${op}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ a, b }),
        });
        const json = await res.json();

        if (res.ok) {
          resultEl.textContent = json.result;
        } else {
          resultEl.textContent = json.detail || "Error";
        }
      } catch (_) {
        resultEl.textContent = "Server error";
      }
    });
  });
});
