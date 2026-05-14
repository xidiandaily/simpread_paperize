/**
 * Paperize 运行时轻量修补（由 Playwright 注入）
 */
(function () {
  function promoteLazyImages() {
    document.querySelectorAll("img[data-src]").forEach(function (img) {
      if (!img.getAttribute("src")) {
        img.setAttribute("src", img.getAttribute("data-src") || "");
      }
    });
    document.querySelectorAll("img[data-original]").forEach(function (img) {
      if (!img.getAttribute("src")) {
        img.setAttribute("src", img.getAttribute("data-original") || "");
      }
    });
  }

  function removeEmptyParagraphs() {
    document.querySelectorAll("p").forEach(function (p) {
      if (!p.textContent || !p.textContent.trim()) {
        p.remove();
      }
    });
  }

  function markWideTables() {
    document.querySelectorAll("table").forEach(function (t) {
      var rect = t.getBoundingClientRect();
      if (rect.width > 700) {
        t.classList.add("paperize-table-wide");
      }
    });
  }

  promoteLazyImages();
  removeEmptyParagraphs();
  markWideTables();
})();
