"use strict";
const menu = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#primary-nav");
if (menu && navigation) {
  document.documentElement.classList.add("js");
  const desktop = window.matchMedia("(min-width: 761px)");
  const syncMenuAccess = () => {
    navigation.inert = !desktop.matches && !navigation.classList.contains("is-open");
  };
  const closeMenu = (focus = false) => {
    navigation.classList.remove("is-open");
    menu.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-label", "Open menu");
    syncMenuAccess();
    if (focus) menu.focus();
  };
  menu.addEventListener("click", () => {
    const open = navigation.classList.toggle("is-open");
    menu.setAttribute("aria-expanded", String(open));
    menu.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    syncMenuAccess();
  });
  navigation.addEventListener("click", event => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && navigation.classList.contains("is-open")) closeMenu(true);
  });
  document.addEventListener("click", event => {
    if (!event.target.closest(".site-header")) closeMenu();
  });
  desktop.addEventListener("change", () => closeMenu());
  syncMenuAccess();
}
const search = document.querySelector("#app-search");
const filters = [...document.querySelectorAll("[data-filter]")];
const cards = [...document.querySelectorAll("[data-app]")];
let category = "All";
function filterApps() {
  const query = (search?.value || "").trim().toLowerCase();
  let count = 0;
  for (const card of cards) {
    const matches = (category === "All" || card.dataset.category === category) && card.dataset.search.includes(query);
    card.hidden = !matches;
    if (matches) count++;
  }
  const empty = document.querySelector("#empty-apps");
  const results = document.querySelector("#app-count");
  if (empty) empty.hidden = count > 0;
  if (results) results.textContent = `${count} ${count === 1 ? "app" : "apps"}`;
}
search?.addEventListener("input", filterApps);
for (const button of filters) button.addEventListener("click", () => {
  category = button.dataset.filter;
  for (const filter of filters) filter.setAttribute("aria-pressed", String(filter === button));
  filterApps();
});
const contact = document.querySelector("#contact-form");
contact?.addEventListener("submit", event => {
  event.preventDefault();
  if (!contact.reportValidity()) return;
  const values = new FormData(contact);
  const subject = String(values.get("subject"));
  const body = `Name: ${values.get("name")}\nReply email: ${values.get("email")}\n\n${values.get("message")}`;
  const draft = `mailto:${contact.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const status = document.querySelector("#contact-status");
  const retry = document.querySelector("#email-draft");
  retry.href = draft;
  retry.hidden = false;
  status.textContent = "Your email draft is ready. Send it from your email app. If nothing opened, use the draft link below or email us directly.";
  window.location.href = draft;
});
