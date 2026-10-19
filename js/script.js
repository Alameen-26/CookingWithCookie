"use strict";
// All prices are in Canadian dollars (CAD).
const CURRENCY_FORMAT = new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: "CAD"
});
function formatPrice(amount) {
    return CURRENCY_FORMAT.format(amount);
}
// PART 1: ORDER CALCULATOR
const quantityInputs = document.querySelectorAll(".quantity");
const itemCount = document.querySelector("#item-count");
const orderTotal = document.querySelector("#order-total");
function calculateOrder() {
    let totalItems = 0;
    let totalPrice = 0;
    quantityInputs.forEach(function (input) {
        const quantity = Number(input.value);
        const price = Number(input.dataset.price);
        totalItems += quantity;
        totalPrice += quantity * price;
    });
    itemCount.textContent = totalItems;
    orderTotal.textContent = formatPrice(totalPrice);
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
// When the site is served by Flask, prices come from /api/menu.
// If the request fails (for example, the page was opened directly
// as a file), the prices already written in index.html are kept.
function applyMenu(menu) {
    const cards = document.querySelectorAll(".meal-card");
    cards.forEach(function (card) {
        const name = card.querySelector("h3").textContent.trim();
        const item = menu.find(function (entry) {
            return entry.name === name;
        });
        if (!item) {
            return;
        }
        const priceText = card.querySelector(".price");
        const input = card.querySelector(".quantity");
        priceText.textContent = formatPrice(item.price);
        input.dataset.price = item.price;
    });
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
            console.info("Using the built-in menu prices.", error);
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
const UNCONFIRMED_NOTE =
    "Calorie and allergen details haven't been confirmed yet. Please contact Cooking with Cookie before ordering, especially if you have a severe allergy, as cross-contamination is possible.";
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
    if (text.includes("jollof")) {
        return "Our proposed Jollof Rice Plate is $18 and includes chicken, plantain and salad.";
    }
    if (text.includes("fried rice")) {
        return "Our proposed Fried Rice Plate is $18 and includes chicken, plantain and salad.";
    }
    if (text.includes("shawarma")) {
        return "Our proposed Chicken Shawarma is $15 and is a chicken wrap with vegetables and sauce.";
    }
    if (text.includes("bulk") || text.includes("party")) {
        return "We can discuss catering for groups. Tell us how many people you are feeding and your preferred meals.";
    }
    if (text.includes("price") || text.includes("cost")) {
        return "Our current demonstration menu includes meals from $15 to $18 (CAD). These prices still need validation against actual business costs.";
    }
    // Whole-word match so words like "chicken" don't count as "hi".
    if (/\b(hello|hi|hey)\b/.test(text)) {
        return "Hello! Welcome to Cooking with Cookie. What kind of meal are you looking for?";
    }
    return "I'd be happy to help with your meal choices. Try asking about Jollof, fried rice, shawarma, prices, calories, allergens or bulk orders.";
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
