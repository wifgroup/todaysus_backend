document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("contactForm");
    if (!form) return;

    const note = form.querySelector(".form-note");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        note.textContent = "Sending…";
        note.className = "form-note";

        const data = {
            name: form.name.value.trim(),
            email: form.email.value.trim(),
            message: form.message.value.trim()
        };

        try {
            const res = await fetch("/api/v1/contact", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            const result = await res.json();

            if (res.ok) {
                note.textContent = "✅ Message sent successfully. Thank you!";
                note.classList.add("success");
                form.reset();
            } else {
                note.textContent = result.error || "Something went wrong.";
                note.classList.add("error");
            }
        } catch (err) {
            note.textContent = "Network error. Please try again.";
            note.classList.add("error");
        }
    });
});
