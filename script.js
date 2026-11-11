const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#main-nav");
if (menuButton && navigation) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });
  navigation.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => {
    menuButton.setAttribute("aria-expanded", "false");
    navigation.classList.remove("is-open");
  }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      menuButton.setAttribute("aria-expanded", "false");
      navigation.classList.remove("is-open");
      menuButton.focus();
    }
  });
}
const year = document.querySelector("#year");
if (year) year.textContent = String(new Date().getFullYear());

const requestType = document.querySelector('select[name="request_type"]');
const partnerComment = document.querySelector(".partner-comment");
if (requestType && partnerComment) {
  const syncCommentVisibility = () => {
    partnerComment.hidden = requestType.value !== "partner";
  };
  requestType.addEventListener("change", syncCommentVisibility);
  syncCommentVisibility();
}


/* Progressive scroll reveal for content cards */
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!reduceMotion && "IntersectionObserver" in window) {
  const revealItems = document.querySelectorAll(".feature-card, .step-card, .detail-card, .audience-item");
  if (revealItems.length) {
    document.documentElement.classList.add("motion-ready");
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -36px 0px" });
    revealItems.forEach((item, index) => {
      item.classList.add("reveal-on-scroll");
      item.style.transitionDelay = String((index % 4) * 65) + "ms";
      revealObserver.observe(item);
    });
  }
}
