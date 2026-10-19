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
// PART 2: ASK COOKIE CHAT ASSISTANT
// Messages go to the backend (/api/chat), which answers with AI or with
// its own rule-based replies. If the backend can't be reached (for example,
// the page was opened directly as a file), the local replies below are used.
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatMessages = document.querySelector("#chat-messages");
const chatButton = chatForm.querySelector("button");
const CONTACT = "alajiadeniyi@gmail.com or (902) 495-1781";
const PRICING_SOON =
    "Pricing is coming soon. Please contact Cooking with Cookie at " + CONTACT + " for details in the meantime.";
const UNCONFIRMED_NOTE =
    "Calorie and allergen details haven't been confirmed yet. Please contact Cooking with Cookie at " + CONTACT + " before ordering, especially if you have a severe allergy, as cross-contamination is possible.";
function addMessage(message, sender) {
    const paragraph = document.createElement("p");
    paragraph.className =
        sender === "user" ? "user-message" : "bot-message";
    // textContent displays text without interpreting it as HTML.
    paragraph.textContent = message;
    chatMessages.appendChild(paragraph);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return paragraph;
}
function getCookieReply(message) {
    const text = message.toLowerCase();
    if (/allerg|gluten|\bnuts?\b|peanut|dairy|milk|\beggs?\b|soy|sesame|wheat|calorie|nutrition/.test(text)) {
        return UNCONFIRMED_NOTE;
    }
    if (/price|cost|how much|quote|\$/.test(text)) {
        return PRICING_SOON;
    }
    if (/\b(recipes?|learn\w*|lessons?|class(es)?|teach\w*|how (do|can|would) (i|you|we) (cook|make|prepare)|how to (cook|make|prepare))\b/.test(text)) {
        return "Cookie offers cooking lessons for the dishes on our menu. Format and dates: details on request. Email alajiadeniyi@gmail.com (subject: Cooking Lesson Enquiry) or call (902) 495-1781.";
    }
    if (text.includes("jollof")) {
        return "Our Jollof Rice Plate comes with jollof rice, chicken, plantain and salad.";
    }
    if (text.includes("fried rice")) {
        return "Our Fried Rice Plate comes with fried rice, chicken, plantain and salad.";
    }
    if (text.includes("shawarma")) {
        return "Our Chicken Shawarma is a chicken wrap with vegetables and sauce.";
    }
    if (/\b(where|locat\w*|deliver\w*|pick ?up|area|halifax|dartmouth|nova scotia|address|near)\b/.test(text)) {
        return "Cooking with Cookie serves the Halifax area, Nova Scotia. For delivery or pickup details, please contact us at " + CONTACT + ".";
    }
    if (/bulk|party|event|cater|crowd|wedding|group|people/.test(text)) {
        return "We can discuss catering for groups. Email or call us at " + CONTACT + " and tell us how many people you are feeding and your preferred meals.";
    }
    // Whole-word match so words like "chicken" don't count as "hi".
    if (/\b(hello|hi|hey)\b/.test(text)) {
        return "Hello! Welcome to Cooking with Cookie. What kind of meal are you looking for?";
    }
    return "I'd be happy to help with your meal choices. Try asking about Jollof, fried rice, shawarma, ingredients, calories, allergens or bulk orders.";
}
async function askServer(message) {
    if (!window.location.protocol.startsWith("http")) {
        return getCookieReply(message);
    }
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        if (response.ok && typeof data.reply === "string") {
            return data.reply;
        }
        // Rate limit or validation message from the server.
        if ((response.status === 429 || response.status === 400) && data.error) {
            return data.error;
        }
    } catch (error) {
        console.info("Chat server unavailable, using local replies.", error);
    }
    return getCookieReply(message);
}
function setWaiting(isWaiting) {
    chatButton.disabled = isWaiting;
    chatButton.textContent = isWaiting ? "Sending…" : "Send";
}
chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (message === "" || chatButton.disabled) {
        return;
    }
    addMessage(message, "user");
    chatInput.value = "";
    setWaiting(true);
    const typing = addMessage("Cookie is typing…", "bot");
    typing.classList.add("typing");
    const reply = await askServer(message);
    typing.remove();
    addMessage(reply, "bot");
    setWaiting(false);
    chatInput.focus();
});
