const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#main-nav");

if (menuButton && navigation) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });
  navigation.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      navigation.classList.remove("is-open");
    });
  });
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

const contactType = document.querySelector("#contact-type");
const partnerComment = document.querySelector(".partner-comment");
if (contactType && partnerComment) {
  const syncComment = () => {
    const isPartner = contactType.value === "partner";
    partnerComment.hidden = !isPartner;
    const comment = partnerComment.querySelector("textarea");
    if (comment) comment.required = false;
  };
  const requestedType = new URLSearchParams(window.location.search).get("type");
  if (requestedType === "partner") contactType.value = "partner";
  contactType.addEventListener("change", syncComment);
  syncComment();
}

const contactForm = document.querySelector("#contact-form");
if (contactForm) {
  contactForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const status = contactForm.querySelector(".form-status");
    if (status) status.textContent = "Приём заявок пока не включён. Не отправляйте контактные данные.";
  });
}
