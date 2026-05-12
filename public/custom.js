(function () {
  const PULSE_CLASS = "avm-pulse-loader";

  function isLoadingText(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return false;
    const t = (node.textContent || "").trim();
    return t === "Thinking..." || t === "Thinking…" || /^Using \w/.test(t) || /^Running/.test(t);
  }

  function decorate(root) {
    const candidates = root.querySelectorAll
      ? root.querySelectorAll("p, span, div")
      : [];
    candidates.forEach((el) => {
      if (!isLoadingText(el)) return;
      const row = el.closest("div, section, li") || el.parentElement;
      if (!row) return;
      const svg = row.querySelector("svg");
      if (svg) svg.classList.add(PULSE_CLASS);
    });
  }

  function init() {
    decorate(document.body);
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        m.addedNodes.forEach((n) => {
          if (n.nodeType === Node.ELEMENT_NODE) decorate(n);
        });
        if (m.type === "characterData" && m.target.parentElement) {
          decorate(m.target.parentElement);
        }
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
