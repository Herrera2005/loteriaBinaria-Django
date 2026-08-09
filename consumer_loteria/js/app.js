"use strict";

const API_BASE_URL = "https://crherrer.alwaysdata.net/api";

const elements = {
  apiState: document.querySelector("#api-state"),
  apiBadge: document.querySelector(".api-badge"),
  status: document.querySelector("#status"),
  search: document.querySelector("#search"),
  kind: document.querySelector("#kind-filter"),
  statusFilter: document.querySelector("#status-filter"),
  productFilter: document.querySelector("#product-filter"),
  productKindControl: document.querySelector("#product-kind-control"),
  eventStatusControl: document.querySelector("#event-status-control"),
  productFilterControl: document.querySelector("#product-filter-control"),
  reload: document.querySelector("#reload"),
  products: document.querySelector("#products"),
  events: document.querySelector("#events"),
  results: document.querySelector("#results"),
  productsSection: document.querySelector("#products-section"),
  eventsSection: document.querySelector("#events-section"),
  resultsSection: document.querySelector("#results-section"),
  detailPanel: document.querySelector("#detail-panel"),
  detailContent: document.querySelector("#detail-content"),
  detailTitle: document.querySelector("#detail-title"),
  closeDetail: document.querySelector("#close-detail"),
  countProducts: document.querySelector("#count-products"),
  countEvents: document.querySelector("#count-events"),
  countResults: document.querySelector("#count-results"),
  tabs: [...document.querySelectorAll(".tab")],
};

const state = {
  section: "products",
  products: [],
  events: [],
  results: [],
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("es-EC", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", isError);
}

function setApiState(message, mode = "") {
  elements.apiState.textContent = message;
  elements.apiBadge.classList.remove("ok", "error");
  if (mode) elements.apiBadge.classList.add(mode);
}

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`${path}: HTTP ${response.status}`);
  }
  return response.json();
}

function asResults(payload) {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

function populateFilters() {
  elements.productFilter.innerHTML = '<option value="">Todos</option>';
  for (const product of state.products) {
    const option = document.createElement("option");
    option.value = String(product.id);
    option.textContent = `${product.name} (${product.code})`;
    elements.productFilter.append(option);
  }

  const statuses = new Map();
  for (const event of state.events) {
    statuses.set(event.status, event.status_label);
  }

  elements.statusFilter.innerHTML = '<option value="">Todos</option>';
  for (const [value, label] of [...statuses.entries()].sort((a, b) => a[1].localeCompare(b[1]))) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    elements.statusFilter.append(option);
  }
}

function filteredProducts() {
  const query = elements.search.value.trim().toLocaleLowerCase("es");
  const kind = elements.kind.value;
  return state.products.filter((product) => {
    const text = `${product.name} ${product.code}`.toLocaleLowerCase("es");
    return text.includes(query) && (!kind || product.kind === kind);
  });
}

function filteredEvents() {
  const query = elements.search.value.trim().toLocaleLowerCase("es");
  const status = elements.statusFilter.value;
  const productId = elements.productFilter.value;

  return state.events.filter((event) => {
    const text = `${event.name} ${event.product?.name ?? ""} ${event.status_label ?? ""}`
      .toLocaleLowerCase("es");
    return (
      text.includes(query) &&
      (!status || event.status === status) &&
      (!productId || String(event.product?.id) === productId)
    );
  });
}

function filteredResults() {
  const query = elements.search.value.trim().toLocaleLowerCase("es");
  const productId = elements.productFilter.value;

  return state.results.filter((result) => {
    const text = `${result.event?.name ?? ""} ${result.event?.product?.name ?? ""} ${result.winning_key ?? ""}`
      .toLocaleLowerCase("es");
    return (
      text.includes(query) &&
      (!productId || String(result.event?.product?.id) === productId)
    );
  });
}

function emptyState(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function renderProducts() {
  const visible = filteredProducts();
  elements.products.innerHTML = "";

  if (!visible.length) {
    elements.products.innerHTML = emptyState("No hay productos que coincidan con los filtros.");
    setStatus("0 productos mostrados.");
    return;
  }

  for (const product of visible) {
    const article = document.createElement("article");
    article.className = "data-card";
    article.style.setProperty("--card-color", product.accent_color || "#d9a629");
    article.innerHTML = `
      <div>
        <h3>${escapeHtml(product.name)}</h3>
        <div class="meta">
          <span class="chip">${escapeHtml(product.code)}</span>
          <span class="chip">${escapeHtml(product.kind_label)}</span>
          <span class="chip ${product.is_active ? "success" : "warning"}">${product.is_active ? "Activo" : "Inactivo"}</span>
        </div>
      </div>
      <p><strong>Posiciones:</strong> ${escapeHtml(product.selection_count)}</p>
      <p><strong>Símbolos:</strong> ${(product.symbols || []).map(escapeHtml).join(", ")}</p>
      <div class="card-actions">
        <button type="button" data-detail-product="${product.id}">Ver detalle</button>
      </div>
    `;
    article.querySelector("button").addEventListener("click", () => loadProductDetail(product.id));
    elements.products.append(article);
  }

  setStatus(`${visible.length} producto(s) mostrado(s).`);
}

function renderEvents() {
  const visible = filteredEvents();
  elements.events.innerHTML = "";

  if (!visible.length) {
    elements.events.innerHTML = emptyState("No hay sorteos que coincidan con los filtros.");
    setStatus("0 sorteos mostrados.");
    return;
  }

  for (const event of visible) {
    const article = document.createElement("article");
    article.className = "data-card";
    article.style.setProperty("--card-color", event.product?.accent_color || "#d9a629");
    article.innerHTML = `
      <div>
        <h3>${escapeHtml(event.name)}</h3>
        <div class="meta">
          <span class="chip">${escapeHtml(event.product?.name ?? "Producto")}</span>
          <span class="chip">${escapeHtml(event.status_label)}</span>
          ${event.is_open_now ? '<span class="chip success">Ventas abiertas</span>' : ""}
        </div>
      </div>
      <p><strong>Sorteo:</strong> ${escapeHtml(formatDate(event.draw_at))}</p>
      <p><strong>Cierre de ventas:</strong> ${escapeHtml(formatDate(event.sales_close_at))}</p>
      <p><strong>Precio:</strong> ${escapeHtml(event.price?.display ?? "—")} · <strong>Premio:</strong> ${escapeHtml(event.prize?.display ?? "—")}</p>
      <div class="card-actions">
        <button type="button" data-detail-event="${event.id}">Ver detalle</button>
      </div>
    `;
    article.querySelector("button").addEventListener("click", () => loadEventDetail(event.id));
    elements.events.append(article);
  }

  setStatus(`${visible.length} sorteo(s) mostrado(s).`);
}

function renderResults() {
  const visible = filteredResults();
  elements.results.innerHTML = "";

  if (!visible.length) {
    elements.results.innerHTML = emptyState("Todavía no hay resultados que coincidan con los filtros.");
    setStatus("0 resultados mostrados.");
    return;
  }

  for (const result of visible) {
    const article = document.createElement("article");
    article.className = "data-card";
    article.style.setProperty("--card-color", result.event?.product?.accent_color || "#d9a629");
    article.innerHTML = `
      <div>
        <h3>${escapeHtml(result.event?.name ?? "Resultado")}</h3>
        <div class="meta">
          <span class="chip">${escapeHtml(result.event?.product?.name ?? "Producto")}</span>
          <span class="chip">${escapeHtml(result.publication_source_label ?? result.publication_source)}</span>
        </div>
      </div>
      <div class="winning-key">${escapeHtml(result.winning_key)}</div>
      <p><strong>Símbolos ganadores:</strong> ${(result.winning_symbols || []).map(escapeHtml).join(" · ")}</p>
      <p><strong>Publicado:</strong> ${escapeHtml(formatDate(result.published_at))}</p>
      <div class="card-actions">
        <button type="button" data-detail-result="${result.id}">Ver detalle</button>
      </div>
    `;
    article.querySelector("button").addEventListener("click", () => loadResultDetail(result.id));
    elements.results.append(article);
  }

  setStatus(`${visible.length} resultado(s) mostrado(s).`);
}

function renderActiveSection() {
  if (state.section === "products") renderProducts();
  if (state.section === "events") renderEvents();
  if (state.section === "results") renderResults();
}

function configureControls() {
  elements.productKindControl.hidden = state.section !== "products";
  elements.eventStatusControl.hidden = state.section !== "events";
  elements.productFilterControl.hidden = state.section === "products";

  elements.productsSection.hidden = state.section !== "products";
  elements.eventsSection.hidden = state.section !== "events";
  elements.resultsSection.hidden = state.section !== "results";

  elements.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.section === state.section);
  });
}

function switchSection(section) {
  state.section = section;
  elements.search.value = "";
  elements.kind.value = "";
  elements.statusFilter.value = "";
  elements.productFilter.value = "";
  elements.detailPanel.hidden = true;
  elements.detailContent.innerHTML = "";
  configureControls();
  renderActiveSection();
}

async function loadAll() {
  setStatus("Consultando productos, sorteos y resultados…");
  setApiState("Conectando con Django…");

  try {
    const [root, productsPayload, eventsPayload, resultsPayload] = await Promise.all([
      getJson("/"),
      getJson("/products/"),
      getJson("/events/"),
      getJson("/results/"),
    ]);

    state.products = asResults(productsPayload);
    state.events = asResults(eventsPayload);
    state.results = asResults(resultsPayload);

    elements.countProducts.textContent = String(state.products.length);
    elements.countEvents.textContent = String(state.events.length);
    elements.countResults.textContent = String(state.results.length);

    populateFilters();
    configureControls();
    renderActiveSection();

    setApiState(`${root.name ?? "API"} disponible`, "ok");
  } catch (error) {
    console.error(error);
    setStatus("No se pudo consultar la API. Revisa AlwaysData y CORS.", true);
    setApiState("API no disponible", "error");
  }
}

function showDetail(title, html) {
  elements.detailTitle.textContent = title;
  elements.detailContent.innerHTML = html;
  elements.detailPanel.hidden = false;
  elements.detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadProductDetail(id) {
  setStatus("Cargando detalle del producto…");
  try {
    const product = await getJson(`/products/${id}/`);
    showDetail("Detalle del producto", `
      <dl class="detail-grid">
        <div><dt>Nombre</dt><dd>${escapeHtml(product.name)}</dd></div>
        <div><dt>Código</dt><dd>${escapeHtml(product.code)}</dd></div>
        <div><dt>Tipo</dt><dd>${escapeHtml(product.kind_label)}</dd></div>
        <div><dt>Posiciones</dt><dd>${escapeHtml(product.selection_count)}</dd></div>
        <div><dt>Símbolos</dt><dd>${(product.symbols || []).map(escapeHtml).join(", ")}</dd></div>
        <div><dt>Estado</dt><dd>${product.is_active ? "Activo" : "Inactivo"}</dd></div>
      </dl>
    `);
    setStatus("Detalle cargado.");
  } catch (error) {
    console.error(error);
    setStatus("No se pudo cargar el detalle del producto.", true);
  }
}

async function loadEventDetail(id) {
  setStatus("Cargando detalle del sorteo…");
  try {
    const event = await getJson(`/events/${id}/`);
    showDetail("Detalle del sorteo", `
      <dl class="detail-grid">
        <div><dt>Nombre</dt><dd>${escapeHtml(event.name)}</dd></div>
        <div><dt>Producto</dt><dd>${escapeHtml(event.product?.name)}</dd></div>
        <div><dt>Estado</dt><dd>${escapeHtml(event.status_label)}</dd></div>
        <div><dt>Ventas abiertas ahora</dt><dd>${event.is_open_now ? "Sí" : "No"}</dd></div>
        <div><dt>Apertura de ventas</dt><dd>${escapeHtml(formatDate(event.sales_open_at))}</dd></div>
        <div><dt>Cierre de ventas</dt><dd>${escapeHtml(formatDate(event.sales_close_at))}</dd></div>
        <div><dt>Fecha del sorteo</dt><dd>${escapeHtml(formatDate(event.draw_at))}</dd></div>
        <div><dt>Precio</dt><dd>${escapeHtml(event.price?.display ?? "—")}</dd></div>
        <div><dt>Premio</dt><dd>${escapeHtml(event.prize?.display ?? "—")}</dd></div>
      </dl>
    `);
    setStatus("Detalle cargado.");
  } catch (error) {
    console.error(error);
    setStatus("No se pudo cargar el detalle del sorteo.", true);
  }
}

async function loadResultDetail(id) {
  setStatus("Cargando detalle del resultado…");
  try {
    const result = await getJson(`/results/${id}/`);
    showDetail("Detalle del resultado", `
      <dl class="detail-grid">
        <div><dt>Sorteo</dt><dd>${escapeHtml(result.event?.name)}</dd></div>
        <div><dt>Producto</dt><dd>${escapeHtml(result.event?.product?.name)}</dd></div>
        <div><dt>Fecha del sorteo</dt><dd>${escapeHtml(formatDate(result.event?.draw_at))}</dd></div>
        <div><dt>Clave ganadora</dt><dd>${escapeHtml(result.winning_key)}</dd></div>
        <div><dt>Símbolos ganadores</dt><dd>${(result.winning_symbols || []).map(escapeHtml).join(" · ")}</dd></div>
        <div><dt>Origen</dt><dd>${escapeHtml(result.publication_source_label ?? result.publication_source)}</dd></div>
        <div><dt>Publicado</dt><dd>${escapeHtml(formatDate(result.published_at))}</dd></div>
      </dl>
    `);
    setStatus("Detalle cargado.");
  } catch (error) {
    console.error(error);
    setStatus("No se pudo cargar el detalle del resultado.", true);
  }
}

elements.tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchSection(tab.dataset.section));
});

elements.search.addEventListener("input", renderActiveSection);
elements.kind.addEventListener("change", renderActiveSection);
elements.statusFilter.addEventListener("change", renderActiveSection);
elements.productFilter.addEventListener("change", renderActiveSection);
elements.reload.addEventListener("click", loadAll);

elements.closeDetail.addEventListener("click", () => {
  elements.detailPanel.hidden = true;
  elements.detailContent.innerHTML = "";
});

document.addEventListener("DOMContentLoaded", loadAll);
