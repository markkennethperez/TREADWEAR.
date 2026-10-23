from pyscript import document
from pyodide.ffi import create_proxy
from js import window, navigator
from pyodide.ffi import to_js
import asyncio

# ==========================================
# TREND WEAR - PRODUCT DATABASE
# ==========================================

PRODUCTS = {
    "tee": {
        "name": "Everyday Essential Tee",
        "price": 149,
        "category": "Tees",
        "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=600&q=80"
    },

    "hoodie": {
        "name": "Campus Comfort Hoodie",
        "price": 399,
        "category": "Hoodies",
        "image": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=600&q=80"
    },

    "street": {
        "name": "Street Mode Tee",
        "price": 179,
        "category": "Tees",
        "image": "https://6adb4520086c9bf074107a7f.imgix.net/sandbox/images%20(1).jpg"
    },

    "polo": {
        "name": "Clean Cut Polo",
        "price": 249,
        "category": "Polos",
        "image": "https://images.unsplash.com/photo-1627225924765-552d49cf47ad?auto=format&fit=crop&w=600&q=80"
    },

    "denim": {
        "name": "Everyday Denim",
        "price": 449,
        "category": "Bottoms",
        "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=600&q=80"
    },

    "graphic": {
        "name": "Graphic Day Tee",
        "price": 199,
        "category": "Tees",
        "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=600&q=80"
    }
}


# Shopping cart: product ID -> quantity
cart = {}

active_category = "All"
last_order_summary = ""


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def money(amount):
    return "₱" + format(int(amount), ",")


def show_toast(message):
    toast = document.getElementById("toast")

    toast.textContent = message
    toast.classList.add("show")

    global toast_timer

    try:
        toast_timer.cancel()
    except Exception:
        pass

    loop = asyncio.get_running_loop()

    toast_timer = loop.call_later(
        2.5,
        lambda: toast.classList.remove("show")
    )


toast_timer = None


def calculate_totals():
    item_count = sum(cart.values())

    subtotal = sum(
        PRODUCTS[product_id]["price"] * quantity
        for product_id, quantity in cart.items()
    )

    # 10% discount for 3 or more individual items
    discount = int(subtotal * 0.10) if item_count >= 3 else 0

    total = subtotal - discount

    return item_count, subtotal, discount, total


# ==========================================
# DISPLAY PRODUCTS
# ==========================================

def render_products():
    grid = document.getElementById("product-grid")
    search_input = document.getElementById("search-input")

    search_text = search_input.value.lower().strip()

    grid.innerHTML = ""

    visible_count = 0

    for product_id, product in PRODUCTS.items():

        name = product["name"].lower()
        category = product["category"]

        category_matches = (
            active_category == "All"
            or category == active_category
        )

        search_matches = (
            search_text in name
            or search_text in category.lower()
        )

        if not category_matches or not search_matches:
            continue

        visible_count += 1

        # Create product card using HTML
        card = document.createElement("article")
        card.className = "product-card"

        card.innerHTML = f"""
            <div class="product-image">
                <img
                    src="{product['image']}"
                    alt="{product['name']}"
                    loading="lazy">
            </div>

            <div class="product-info">

                <span class="product-category">
                    {product['category']}
                </span>

                <h3>{product['name']}</h3>

                <div class="product-bottom">

                    <span class="product-price">
                        {money(product['price'])}
                    </span>

                    <button
                        class="add-button"
                        data-action="add"
                        data-id="{product_id}">
                        + Add
                    </button>

                </div>

            </div>
        """

        grid.appendChild(card)

    document.getElementById(
        "no-results"
    ).classList.toggle("hidden", visible_count > 0)


# ==========================================
# PRODUCT SEARCH
# ==========================================

def search_products(event=None):
    render_products()


# ==========================================
# CATEGORY FILTER
# ==========================================

def filter_category(event):
    global active_category

    button = event.target.closest("button")

    if button is None:
        return

    active_category = button.getAttribute("data-category")

    for category_button in document.querySelectorAll(".category"):
        category_button.classList.toggle(
            "active",
            category_button.getAttribute("data-category")
            == active_category
        )

    render_products()


# ==========================================
# ADD PRODUCTS TO CART
# ==========================================

def add_product(product_id):
    if product_id not in PRODUCTS:
        return

    cart[product_id] = cart.get(product_id, 0) + 1

    update_cart()

    show_toast(
        PRODUCTS[product_id]["name"] + " added to your cart!"
    )


def handle_product_click(event):
    button = event.target.closest("button[data-action='add']")

    if button is None:
        return

    product_id = button.getAttribute("data-id")

    add_product(product_id)


# ==========================================
# UPDATE CART
# ==========================================

def update_cart():
    item_count, subtotal, discount, total = calculate_totals()

    document.getElementById("cart-count").textContent = str(
        item_count
    )

    document.getElementById("drawer-count").textContent = (
        f"({item_count})"
    )

    document.getElementById("item-count").textContent = str(
        item_count
    )

    document.getElementById("subtotal").textContent = money(
        subtotal
    )

    document.getElementById("discount").textContent = (
        "-" + money(discount)
    )

    document.getElementById("total").textContent = money(total)

    document.getElementById("checkout-total").textContent = money(
        total
    )

    cart_container = document.getElementById("cart-items")

    cart_container.innerHTML = ""

    if not cart:

        cart_container.innerHTML = """
            <div class="cart-empty">

                <div class="empty-icon">🛍️</div>

                <h3>Your cart is empty.</h3>

                <p>
                    Add something fresh from the shop!
                </p>

                <button
                    class="button primary"
                    data-action="explore">
                    Explore the shop
                </button>

            </div>
        """

        return

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        row = document.createElement("div")
        row.className = "cart-row"

        row.innerHTML = f"""
            <img
                src="{product['image']}"
                alt="{product['name']}">

            <div>

                <h4>{product['name']}</h4>

                <p>{money(product['price'])} each</p>

                <div class="quantity-controls">

                    <button
                        data-action="decrease"
                        data-id="{product_id}"
                        aria-label="Decrease quantity">
                        −
                    </button>

                    <span>{quantity}</span>

                    <button
                        data-action="increase"
                        data-id="{product_id}"
                        aria-label="Increase quantity">
                        +
                    </button>

                </div>

            </div>

            <button
                class="remove-button"
                data-action="remove"
                data-id="{product_id}"
                aria-label="Remove product">
                ×
            </button>
        """

        cart_container.appendChild(row)


# ==========================================
# CART BUTTON EVENTS
# ==========================================

def handle_cart_click(event):
    button = event.target.closest("button[data-action]")

    if button is None:
        return

    action = button.getAttribute("data-action")
    product_id = button.getAttribute("data-id")

    if action == "explore":
        close_panels()
        window.location.hash = "shop"
        return

    if product_id not in PRODUCTS:
        return

    if action == "increase":

        cart[product_id] = cart.get(product_id, 0) + 1

    elif action == "decrease":

        if product_id in cart:
            cart[product_id] -= 1

            if cart[product_id] <= 0:
                del cart[product_id]

    elif action == "remove":

        cart.pop(product_id, None)

        show_toast("Product removed from cart.")

    update_cart()


# ==========================================
# OPEN AND CLOSE SHOPPING CART
# ==========================================

def toggle_cart(event=None):
    drawer = document.getElementById("cart-drawer")
    overlay = document.getElementById("overlay")

    if drawer.classList.contains("open"):

        drawer.classList.remove("open")
        overlay.classList.add("hidden")

    else:

        document.getElementById(
            "checkout-modal"
        ).classList.add("hidden")

        drawer.classList.add("open")
        overlay.classList.remove("hidden")


def close_panels(event=None):
    document.getElementById(
        "cart-drawer"
    ).classList.remove("open")

    document.getElementById(
        "checkout-modal"
    ).classList.add("hidden")

    document.getElementById(
        "overlay"
    ).classList.add("hidden")


# ==========================================
# LIGHT AND DARK MODE
# ==========================================

def toggle_theme(event=None):
    body = document.body

    body.classList.toggle("light-mode")

    button = document.querySelector(".icon-button")

    if body.classList.contains("light-mode"):
        button.textContent = "☾"
    else:
        button.textContent = "☀"


# ==========================================
# MOBILE NAVIGATION
# ==========================================

def toggle_menu(event=None):
    document.body.classList.toggle("menu-open")


def close_mobile_menu(event):
    document.body.classList.remove("menu-open")


# ==========================================
# CHECKOUT
# ==========================================

def open_checkout(event=None):
    if not cart:
        show_toast("Add an item to your cart first.")
        return

    document.getElementById(
        "cart-drawer"
    ).classList.remove("open")

    document.getElementById(
        "checkout-modal"
    ).classList.remove("hidden")

    document.getElementById(
        "overlay"
    ).classList.remove("hidden")

    document.getElementById(
        "order-result"
    ).classList.add("hidden")

    document.getElementById(
        "copy-order"
    ).classList.add("hidden")


def close_checkout(event=None):
    document.getElementById(
        "checkout-modal"
    ).classList.add("hidden")

    document.getElementById(
        "overlay"
    ).classList.add("hidden")


# ==========================================
# PREPARE ORDER SUMMARY
# ==========================================

def submit_order(event):
    global last_order_summary

    event.preventDefault()

    if not cart:
        show_toast("Your shopping cart is empty.")
        return

    name = document.getElementById(
        "customer-name"
    ).value.strip()

    contact = document.getElementById(
        "customer-contact"
    ).value.strip()

    handover = document.getElementById(
        "handover"
    ).value

    notes = document.getElementById(
        "order-notes"
    ).value.strip()

    if not name or not contact:
        show_toast("Please complete your details.")
        return

    item_count, subtotal, discount, total = calculate_totals()

    lines = [
        "TREND WEAR - ORDER SUMMARY",
        "===========================",
        "",
        f"Customer: {name}",
        f"Contact: {contact}",
        f"Handover: {handover}",
        "",
        "ORDER ITEMS:"
    ]

    for product_id, quantity in cart.items():

        product = PRODUCTS[product_id]

        item_total = product["price"] * quantity

        lines.append(
            f"{product['name']} x {quantity}"
        )

        lines.append(
            f"  Price: {money(item_total)}"
        )

    lines.extend([
        "",
        f"Number of items: {item_count}",
        f"Subtotal: {money(subtotal)}",
        f"Discount: -{money(discount)}",
        f"ESTIMATED TOTAL: {money(total)}",
        "",
        f"Notes: {notes or 'None'}",
        "",
        "IMPORTANT:",
        "This is a prepared order summary.",
        "No payment has been processed.",
        "Please contact the shop to confirm",
        "stock, delivery fees, and payment."
    ])

    last_order_summary = "\n".join(lines)

    result = document.getElementById("order-result")

    result.textContent = last_order_summary
    result.classList.remove("hidden")

    document.getElementById(
        "copy-order"
    ).classList.remove("hidden")

    show_toast("Your order summary is ready!")


# ==========================================
# COPY ORDER SUMMARY
# ==========================================

async def copy_order(event=None):
    if not last_order_summary:
        show_toast("Prepare an order first.")
        return

    try:
        await navigator.clipboard.writeText(
            last_order_summary
        )

        show_toast("Order summary copied!")

    except Exception:
        show_toast(
            "Select and copy the order summary manually."
        )


# ==========================================
# BACK TO TOP
# ==========================================

def back_to_top(event=None):
    window.scrollTo(
        to_js({
            "top": 0,
            "behavior": "smooth"
        })
    )


# ==========================================
# NAVIGATION LINKS
# ==========================================

def handle_navigation(event):
    if event.target.closest("a"):
        document.body.classList.remove("menu-open")


# ==========================================
# INITIALIZE THE WEBSITE
# ==========================================

# Product cards are created dynamically by Python.
render_products()

# Display the initial cart state.
update_cart()

# Event delegation allows buttons created dynamically
# by Python to continue working.
product_grid = document.getElementById("product-grid")
cart_items = document.getElementById("cart-items")

product_grid.addEventListener(
    "click",
    create_proxy(handle_product_click)
)

cart_items.addEventListener(
    "click",
    create_proxy(handle_cart_click)
)

# Close mobile navigation after selecting a link.
navigation = document.getElementById("navigation")

navigation.addEventListener(
    "click",
    create_proxy(handle_navigation)
)
