/* Minimal accessible lightbox for album masonry images. */
(function () {
  const links = Array.from(document.querySelectorAll("a[data-lightbox]"));
  if (!links.length) return;

  let current = 0;

  const overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.innerHTML =
    '<button class="lightbox-close" aria-label="Close">&times;</button>' +
    '<button class="lightbox-nav lightbox-prev" aria-label="Previous">&#8249;</button>' +
    '<img alt="" />' +
    '<button class="lightbox-nav lightbox-next" aria-label="Next">&#8250;</button>' +
    '<div class="lightbox-caption"></div>';
  document.body.appendChild(overlay);

  const imgEl = overlay.querySelector("img");
  const captionEl = overlay.querySelector(".lightbox-caption");

  function show(index) {
    current = (index + links.length) % links.length;
    const link = links[current];
    imgEl.src = link.getAttribute("href");
    imgEl.alt = link.querySelector("img") ? link.querySelector("img").alt : "";
    captionEl.textContent = link.getAttribute("data-caption") || "";
  }

  function open(index) {
    show(index);
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function close() {
    overlay.classList.remove("open");
    document.body.style.overflow = "";
    imgEl.src = "";
  }

  links.forEach((link, index) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      open(index);
    });
  });

  overlay.querySelector(".lightbox-close").addEventListener("click", close);
  overlay.querySelector(".lightbox-prev").addEventListener("click", (e) => { e.stopPropagation(); show(current - 1); });
  overlay.querySelector(".lightbox-next").addEventListener("click", (e) => { e.stopPropagation(); show(current + 1); });
  overlay.addEventListener("click", (event) => { if (event.target === overlay) close(); });

  document.addEventListener("keydown", (event) => {
    if (!overlay.classList.contains("open")) return;
    if (event.key === "Escape") close();
    else if (event.key === "ArrowLeft") show(current - 1);
    else if (event.key === "ArrowRight") show(current + 1);
  });
})();
