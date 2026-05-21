(() => {
  // Delete-confirm dialogs
  document.querySelectorAll("form[data-confirm]").forEach((f) => {
    f.addEventListener("submit", (e) => {
      const msg = f.dataset.confirm || "Are you sure?";
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // "Now" button — set date+time inputs to current local time
  const nowBtn = document.getElementById("now-btn");
  if (nowBtn) {
    nowBtn.addEventListener("click", () => {
      const now = new Date();
      const pad = (n) => String(n).padStart(2, "0");
      const dateInput = document.getElementById("reading-date");
      const timeInput = document.getElementById("reading-time");
      if (dateInput) dateInput.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
      if (timeInput) timeInput.value = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
    });
  }

  // Extract from photo — POSTs to /readings/extract and pre-fills the form
  const extractBtn = document.getElementById("extract-btn");
  const captureInput = document.getElementById("capture-image");
  const statusEl = document.getElementById("extract-status");
  if (extractBtn && captureInput && statusEl) {
    extractBtn.addEventListener("click", async () => {
      const file = captureInput.files?.[0];
      if (!file) {
        statusEl.textContent = "Pick an image first.";
        statusEl.className = "status error";
        return;
      }
      statusEl.textContent = "Reading…";
      statusEl.className = "status";

      const fd = new FormData();
      fd.append("image", file);
      const url = "/readings/extract";
      try {
        const res = await fetch(url, { method: "POST", body: fd });
        const data = await res.json();
        if (!res.ok || data.error) {
          statusEl.textContent = `Error: ${data.error || res.statusText}`;
          statusEl.className = "status error";
          return;
        }
        const set = (id, v) => {
          if (v == null) return;
          const el = document.getElementById(id);
          if (el) el.value = v;
        };
        set("systolic", data.systolic);
        set("diastolic", data.diastolic);
        set("pulse", data.pulse);
        set("reading-date", data.reading_date);
        set("reading-time", data.reading_time);

        // Also stash the file on the entry form so it saves alongside the reading.
        const entryFile = document.querySelector('#entry-form input[name="image"]');
        if (!entryFile) {
          const dt = new DataTransfer();
          dt.items.add(file);
          const hidden = document.createElement("input");
          hidden.type = "file";
          hidden.name = "image";
          hidden.hidden = true;
          hidden.files = dt.files;
          document.getElementById("entry-form")?.appendChild(hidden);
        }

        const conf = typeof data.confidence === "number" ? data.confidence : 0;
        const pct = Math.round(conf * 100);
        if (conf < 0.7) {
          statusEl.textContent = `Confidence ${pct}% — review the values carefully.`;
          statusEl.className = "status low-confidence";
        } else {
          statusEl.textContent = `Confidence ${pct}%. Review and Add.`;
          statusEl.className = "status";
        }
      } catch (err) {
        statusEl.textContent = `Network error: ${err.message}`;
        statusEl.className = "status error";
      }
    });
  }
})();
