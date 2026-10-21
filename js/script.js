"use strict";
// Prices are hidden until the backend turns them on (SHOW_PRICES in .env).
// When it does, /api/menu includes a price for each item (in CAD) and the
// page shows prices and an estimated total. Otherwise only item counts show.
let showPrices = false;
const CURRENCY_FORMAT = new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: "CAD"
});
function formatPrice(amount) {
    return CURRENCY_FORMAT.format(amount);
}
// PART 1: ORDER SUMMARY
const quantityInputs = document.querySelectorAll(".quantity");
const itemCount = document.querySelector("#item-count");
const orderTotal = document.querySelector("#order-total");
function calculateOrder() {
    let totalItems = 0;
    let totalPrice = 0;
    quantityInputs.forEach(function (input) {
        const quantity = Number(input.value);
        const price = Number(input.dataset.price || 0);
        totalItems += quantity;
        totalPrice += quantity * price;
    });
    itemCount.textContent = totalItems;
    orderTotal.textContent = showPrices ? formatPrice(totalPrice) : "";
}
quantityInputs.forEach(function (input) {
    input.addEventListener("input", function () {
        const quantity = Number(input.value);
        if (!Number.isFinite(quantity) || quantity < 0) {
            input.value = 0;
        } else if (quantity > 100) {
            input.value = 100;
        } else if (!Number.isInteger(quantity)) {
            input.value = Math.floor(quantity);
        }
        calculateOrder();
    });
});
calculateOrder();
// PART 1B: LIVE MENU FROM THE BACKEND
// Prices only appear if the backend sends them. If the request fails (for
// example, the page was opened directly as a file), no prices are shown.
function showPriceElements() {
    showPrices = true;
    document.querySelectorAll(".price-only").forEach(function (element) {
        element.hidden = false;
    });
    document.querySelectorAll(".pricing-soon").forEach(function (element) {
        element.hidden = true;
    });
}
function applyMenu(menu) {
    const hasPrices = menu.length > 0 && menu.every(function (item) {
        return typeof item.price === "number";
    });
    if (!hasPrices) {
        return;
    }
    document.querySelectorAll(".meal-card").forEach(function (card) {
        const name = card.querySelector("h3").textContent.trim();
        const item = menu.find(function (entry) {
            return entry.name === name;
        });
        if (!item) {
            return;
        }
        card.querySelector(".price").textContent = formatPrice(item.price);
        card.querySelector(".quantity").dataset.price = item.price;
    });
    showPriceElements();
    calculateOrder();
}
if (window.location.protocol.startsWith("http")) {
    fetch("/api/menu")
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Menu request failed: " + response.status);
            }
            return response.json();
        })
        .then(applyMenu)
        .catch(function (error) {
            console.info("Menu details unavailable.", error);
        });
}
// PART 1C: "LEARN TO MAKE IT" BUTTONS
// Each dish card has a button that asks Cookie for that dish's recipe.
document.querySelectorAll(".learn-button").forEach(function (button) {
    button.addEventListener("click", function () {
        const input = document.querySelector("#chat-input");
        const form = document.querySelector("#chat-form");
        input.value = "How do I make " + button.dataset.dish + "?";
        document.querySelector("#assistant").scrollIntoView({ behavior: "smooth" });
        form.requestSubmit();
    });
});
// PART 2: ASK COOKIE CHAT ASSISTANT
// Messages go to the backend (/api/chat) together with the last few messages
// of the conversation, so Cookie understands follow-ups like "how long do I
// fry it?". The backend answers with AI (optionally grounded with web search
// results) or with its own rule-based replies. If the backend can't be
// reached (for example, the page was opened directly as a file), the short
// local replies below are used.
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatMessages = document.querySelector("#chat-messages");
const chatButton = chatForm.querySelector("button");
const chatSuggestions = document.querySelector("#chat-suggestions");
const ORDER_CONTACT = "email alajiadeniyi@gmail.com or call (902) 495-1781";
const PRICING_SOON = "Pricing is coming soon.";
const ALLERGY_NOTE =
    "Allergen information is based on typical recipes and hasn't been verified, and cross-contamination is possible in our kitchen. If you have a severe allergy, please be very cautious.";
// Conversation memory, kept only in this browser tab.
const MAX_HISTORY = 10; // messages sent with each question (about 5 turns)
const MAX_HISTORY_LENGTH = 1000; // characters per remembered message
const chatHistory = [];
function remember(role, content) {
    chatHistory.push({ role: role, content: content.slice(0, MAX_HISTORY_LENGTH) });
    while (chatHistory.length > MAX_HISTORY) {
        chatHistory.shift();
    }
}
// ---- Safe formatting ----
// Replies may contain simple markdown: **bold**, [links](https://...) and
// line breaks. Everything is HTML-escaped FIRST, so any HTML or script in a
// reply is shown as plain text and never runs (no XSS). Only http(s) links
// are turned into <a> tags.
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
function isSafeUrl(url) {
    return /^https?:\/\/[^\s]+$/i.test(url);
}
function renderMarkdown(text) {
    let html = escapeHtml(text);
    html = html.replace(
        /\[([^\]\n]{1,200})\]\((https?:\/\/[^\s)]+)\)/g,
        function (match, label, url) {
            return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + label + "</a>";
        }
    );
    html = html.replace(
        /(^|[\s(])(https?:\/\/[^\s<)]+)/g,
        function (match, before, url) {
            return before + '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + url + "</a>";
        }
    );
    html = html.replace(/\*\*([^*\n]+)\*\*/g, function (match, words) {
        return "<strong>" + words + "</strong>";
    });
    return html.replace(/\n/g, "<br>");
}
// ---- Chat window ----
function scrollToLatest() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
function addSources(container, sources) {
    const safe = (sources || []).filter(function (source) {
        return source && typeof source.url === "string" && isSafeUrl(source.url);
    });
    if (safe.length === 0) {
        return;
    }
    const box = document.createElement("div");
    box.className = "sources";
    const heading = document.createElement("p");
    heading.textContent = "Sources";
    box.appendChild(heading);
    const list = document.createElement("ul");
    safe.slice(0, 3).forEach(function (source) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = source.title || source.url;
        item.appendChild(link);
        list.appendChild(item);
    });
    box.appendChild(list);
    container.appendChild(box);
}
function addMessage(message, sender, options) {
    const settings = options || {};
    const bubble = document.createElement("div");
    bubble.className = sender === "user" ? "user-message" : "bot-message";
    if (settings.error) {
        bubble.classList.add("error-message");
    }
    const body = document.createElement("p");
    if (sender === "user") {
        // The customer's own text is always shown exactly as typed.
        body.textContent = message;
    } else {
        body.innerHTML = renderMarkdown(message);
    }
    bubble.appendChild(body);
    if (sender !== "user") {
        addSources(bubble, settings.sources);
    }
    chatMessages.appendChild(bubble);
    scrollToLatest();
    return bubble;
}
function showTyping() {
    const typing = document.createElement("div");
    typing.className = "bot-message typing";
    typing.setAttribute("aria-label", "Cookie is typing");
    for (let i = 0; i < 3; i += 1) {
        typing.appendChild(document.createElement("span"));
    }
    chatMessages.appendChild(typing);
    scrollToLatest();
    return typing;
}
function showSuggestions(suggestions) {
    chatSuggestions.replaceChildren();
    (suggestions || []).slice(0, 3).forEach(function (text) {
        if (typeof text !== "string" || text.trim() === "") {
            return;
        }
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = text;
        chatSuggestions.appendChild(chip);
    });
}
chatSuggestions.addEventListener("click", function (event) {
    const chip = event.target.closest(".chip");
    if (chip) {
        sendMessage(chip.textContent.trim());
    }
});
// Simple replies used only when the server can't be reached.
function getCookieReply(message) {
    const text = message.toLowerCase();
    if (/allerg|intoleran|gluten|\bnuts?\b|peanut|dairy|milk|\beggs?\b|soy|sesame|wheat|shellfish|shrimp|crayfish/.test(text)) {
        return ALLERGY_NOTE + " Ask again in a moment for details about a specific dish.";
    }
    if (/recipe|how (do|can|would|should) (i|you|we) (cook|make|prepare)|how to (cook|make|prepare)|steps|substitut|tips?\b/.test(text)) {
        return "Cookie's recipe helper can't be reached right now. Please try again in a moment.";
    }
    if (/calorie|nutrition/.test(text)) {
        return "Calorie information for our dishes isn't available yet.";
    }
    if (/price|cost|how much|quote|\$/.test(text)) {
        return PRICING_SOON;
    }
    if (/\b(where|locat\w*|deliver\w*|pick ?up|area|halifax|dartmouth|nova scotia|address|near)\b/.test(text)) {
        return "Cooking with Cookie serves the Halifax area, Nova Scotia. To place a pickup order, " + ORDER_CONTACT + ".";
    }
    if (/bulk|party|event|cater|crowd|wedding|group|people/.test(text)) {
        return "We can cater for groups and events. To place a bulk order, " + ORDER_CONTACT + " and tell us how many people you are feeding.";
    }
    if (/\border/.test(text)) {
        return "Orders aren't placed on this website. To place a pickup order, " + ORDER_CONTACT + ".";
    }
    // Whole-word match so words like "chicken" don't count as "hi".
    if (/\b(hello|hi|hey)\b/.test(text)) {
        return "Hello! Welcome to Cooking with Cookie. Ask me about our dishes or how to make them.";
    }
    return "Browse our menu above, or ask me about a dish, its ingredients or how to make it.";
}
async function askServer(message, history) {
    if (!window.location.protocol.startsWith("http")) {
        return { reply: getCookieReply(message), local: true };
    }
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, history: history })
        });
        const data = await response.json();
        if (response.ok && typeof data.reply === "string") {
            return data;
        }
        // Rate limit or validation message from the server.
        if ((response.status === 429 || response.status === 400) && data.error) {
            return { reply: data.error, error: true };
        }
        return {
            reply: "Sorry, something went wrong on my side. Please try again in a moment.",
            error: true
        };
    } catch (error) {
        console.info("Chat server unavailable, using local replies.", error);
        return { reply: getCookieReply(message), local: true };
    }
}
function setWaiting(isWaiting) {
    chatButton.disabled = isWaiting;
    chatButton.textContent = isWaiting ? "Sending…" : "Send";
    chatSuggestions.querySelectorAll(".chip").forEach(function (chip) {
        chip.disabled = isWaiting;
    });
}
async function sendMessage(message) {
    if (message === "" || chatButton.disabled) {
        return;
    }
    const history = chatHistory.slice();
    addMessage(message, "user");
    chatInput.value = "";
    setWaiting(true);
    const typing = showTyping();
    const result = await askServer(message, history);
    typing.remove();
    addMessage(result.reply, "bot", { sources: result.sources, error: result.error });
    if (!result.error) {
        remember("user", message);
        remember("assistant", result.reply);
    }
    if (Array.isArray(result.suggestions)) {
        showSuggestions(result.suggestions);
    }
    setWaiting(false);
    chatInput.focus({ preventScroll: true });
}
chatForm.addEventListener("submit", function (event) {
    event.preventDefault();
    sendMessage(chatInput.value.trim());
});
