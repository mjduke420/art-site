/* Admin enhancements: drag-and-drop upload preview + drag-to-reorder. */
(function () {
  // ---- Upload dropzone: show selected files, support drag & drop ----
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const fileList = document.getElementById("file-list");

  function renderFileNames() {
    if (!fileList) return;
    fileList.innerHTML = "";
    Array.from(fileInput.files).forEach((file) => {
      const li = document.createElement("li");
      li.textContent = file.name;
      fileList.appendChild(li);
    });
  }

  if (dropzone && fileInput) {
    fileInput.addEventListener("change", renderFileNames);

    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("is-dragover");
      })
    );
    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer && e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        renderFileNames();
      }
    });
  }

  // ---- Drag-to-reorder lists ----
  function enableReorder(container) {
    if (!container) return;
    const reorderUrl = container.getAttribute("data-reorder-url");
    const csrfEl = document.getElementById("reorder-csrf");
    if (!reorderUrl || !csrfEl) return;

    let dragged = null;

    container.querySelectorAll("[draggable='true']").forEach((item) => {
      item.addEventListener("dragstart", () => {
        dragged = item;
        item.classList.add("dragging");
      });
      item.addEventListener("dragend", () => {
        item.classList.remove("dragging");
        container.querySelectorAll(".drop-target").forEach((el) => el.classList.remove("drop-target"));
        persistOrder();
      });
      item.addEventListener("dragover", (e) => {
        e.preventDefault();
        if (!dragged || dragged === item) return;
        const rect = item.getBoundingClientRect();
        const after = (e.clientY - rect.top) / rect.height > 0.5;
        item.classList.add("drop-target");
        if (after) item.after(dragged);
        else item.before(dragged);
      });
      item.addEventListener("dragleave", () => item.classList.remove("drop-target"));
    });

    function persistOrder() {
      const ids = Array.from(container.querySelectorAll("[data-id]")).map((el) => el.getAttribute("data-id"));
      const body = new URLSearchParams();
      body.set("order", ids.join(","));
      body.set("csrf_token", csrfEl.value);
      fetch(reorderUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
        credentials: "same-origin",
      });
    }
  }

  enableReorder(document.getElementById("album-sortable"));
  enableReorder(document.getElementById("photo-sortable"));
})();
