const home = document.querySelector("[data-home]");

if (home) {
  const legacyRoutes = new Map([
    ["#home", "./"],
    ["#about", "./about/"],
    ["#themes", "./research-themes/"],
    ["#applications", "./engineering-applications/"],
    ["#resources", "./academic-resources/"],
    ["#authors", "./for-authors/"],
    ["#contact", "./contact/"],
  ]);

  function redirectLegacyRoute() {
    const path = legacyRoutes.get(window.location.hash);
    if (path) {
      const destination = new URL(path, window.location.href);
      destination.search = window.location.search;
      window.location.replace(destination);
    }
  }

  window.addEventListener("hashchange", redirectLegacyRoute);
  redirectLegacyRoute();
}

const journalMenus = [...document.querySelectorAll(".nav-menu")];

for (const menu of journalMenus) {
  menu.addEventListener("toggle", () => {
    if (menu.open) {
      for (const other of journalMenus) {
        if (other !== menu) other.open = false;
      }
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const openMenu = journalMenus.find(menu => menu.open);
  if (openMenu) {
    openMenu.open = false;
    openMenu.querySelector("summary").focus();
  }
});

document.addEventListener("pointerdown", (event) => {
  for (const menu of journalMenus) {
    if (menu.open && !menu.contains(event.target)) menu.open = false;
  }
});

const browse = document.querySelector("[data-browse]");

if (browse) {
  const tablist = browse.querySelector(".browse-tabs");
  const tabs = [...tablist.querySelectorAll("a")];
  const panels = tabs.map(tab => document.getElementById(tab.hash.slice(1)));
  tablist.setAttribute("role", "tablist");
  tablist.setAttribute("aria-label", "Content categories");

  function showPanel(index) {
    tabs.forEach((tab, position) => {
      const active = position === index;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      panels[position].hidden = !active;
    });
  }

  function choosePanel(index) {
    showPanel(index);
    history.replaceState(history.state, "", tabs[index].hash);
  }

  function showPanelFromAddress() {
    const selected = tabs.findIndex(tab => tab.hash === location.hash);
    if (selected >= 0) showPanel(selected);
  }

  tabs.forEach((tab, index) => {
    const panel = panels[index];
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-controls", panel.id);
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", tab.id);
    panel.tabIndex = 0;
    panel.querySelector(".browse-panel-title").classList.add("visually-hidden");

    tab.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      choosePanel(index);
    });

    tab.addEventListener("keydown", (event) => {
      let next;
      switch (event.key) {
        case "ArrowLeft":
          next = (index + tabs.length - 1) % tabs.length;
          break;
        case "ArrowRight":
          next = (index + 1) % tabs.length;
          break;
        case "Home":
          next = 0;
          break;
        case "End":
          next = tabs.length - 1;
          break;
        case " ":
          next = index;
          break;
        default:
          return;
      }
      event.preventDefault();
      choosePanel(next);
      tabs[next].focus();
    });
  });

  showPanel(0);
  showPanelFromAddress();
  window.addEventListener("hashchange", showPanelFromAddress);
}
