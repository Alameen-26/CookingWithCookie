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
// PART 2: DEMONSTRATION CHAT ASSISTANT
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-input");
const chatMessages = document.querySelector("#chat-messages");
function addMessage(message, sender) {
    const paragraph = document.createElement("p");
    paragraph.className =
        sender === "user" ? "user-message" : "bot-message";
    // textContent displays text without interpreting it as HTML.
    paragraph.textContent = message;
    chatMessages.appendChild(paragraph);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
function getCookieReply(message) {
    const text = message.toLowerCase();
    if (text.includes("jollof")) {
        return "Our proposed Jollof Rice Plate is $18 and includes chicken, plantain and salad.";
    }
    if (text.includes("fried rice")) {
        return "Our proposed Fried Rice Plate is $18 and includes chicken, plantain and salad.";
    }
    if (text.includes("shawarma")) {
        return "Our proposed Chicken Shawarma is $15, and Beef Shawarma is $18.";
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
    return "I'd be happy to help with your meal choices. Try asking about Jollof, fried rice, shawarma, prices or bulk orders.";
}
chatForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const message = chatInput.value.trim();
    if (message === "") {
        return;
    }
    addMessage(message, "user");
    const reply = getCookieReply(message);
    addMessage(reply, "bot");
    chatInput.value = "";
    chatInput.focus();
});
