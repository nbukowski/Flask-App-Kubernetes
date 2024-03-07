from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# Check if environment variables are set
if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
    raise ValueError("Twilio account SID and authentication token are required.")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Flask app
app = Flask(__name__)

# Dictionary to store user state (check if its their first interaction)
user_state = {}

# Dictionary to store user's order
order = {}
# Dictionary to store menu items
menu_items = {
    "a": {"name": "Pepperoni Pizza", "price": 12.99},
    "b": {"name": "Hawaiian Pizza", "price": 14.99},
    "c": {"name": "Meat Lovers Pizza", "price": 16.99}
}

@app.route("/", methods=["POST"])
def sms_reply():
    """Respond to incoming messages with a friendly SMS."""
    # Get the incoming message
    incoming_msg = request.values.get("Body", "").lower() # stores content of users messages
    resp = MessagingResponse()

    if user_state.get(request.values.get("From")) is None:
        # If its the users first interaction, send welcome message
        resp.message("Welcome to Domino's! How can we assist you today? "
                     "Type 'menu' to see the menu or 'order' to start your order.")
        # Update user state to indicate that they have interacted and don't need welcome message again
        user_state[request.values.get("From")] = 'interacted'
        return str(resp)
    else: 
        return handle_user_message(incoming_msg, resp) 
    

def handle_user_message(incoming_msg, resp):
    # Check for specific keywords and respond accordingly
    if "menu" == incoming_msg:
        # Send back a list of menu items
        msg = "Here are our menu items:\n\n"

        for number, details in menu_items.items():
            msg += f"{number}. {details['name']} - ${details['price']:.2f}\n"
        resp.message(msg)
    elif "order" in incoming_msg:
        # Start the order process
        order.clear()  # Clear any previous orders
        resp.message(
            "Great! Let's get started with your order. "
            "What type of pizza would you like? (Please reply with a letter)")
    elif incoming_msg.lower() in menu_items:
        # Check if the user has already added the pizza to the order
        pizza_number = incoming_msg
        pizza_name = menu_items[pizza_number]["name"]
        pizza_price = menu_items[pizza_number]["price"]
        if pizza_name in order:
            resp.message(
                f"You've already added {pizza_name} to your order. "
                "How many more would you like?")
        else:
            # Add the pizza to the order
            order[pizza_name] = {"price": pizza_price, "quantity": 0}
            resp.message(
                f"You've selected {pizza_name}. How many would you like to order?")
    elif incoming_msg.isdigit():
        # Check if the user has already selected a pizza
        if not order:
            resp.message("Please select a pizza from the menu first.")
        else:
            # Update the quantity of the selected pizza
            pizza_name = list(order.keys())[-1]
            order[pizza_name]["quantity"] = int(incoming_msg)
            # Check if the user wants to add another pizza or complete the order
            msg = f"You've ordered:\n{order_summary()}\n"
            msg += "Reply with 'menu' to add another pizza or 'done' to complete your order."
            resp.message(msg)
    elif "done" in incoming_msg:
        # Complete the order and send the final message
        msg = f"Thanks for your order!\n{order_summary()}\n"
        msg += f"Total: ${calculate_total():.2f}"
        resp.message(msg)
        # Reset the order dictionary for the next customer
        order.clear()
    else:
        # Handle any other messages
        resp.message(
            "I'm sorry, I didn't understand your message. "
            "Please reply with 'menu' to see our menu, "
            "'order' to start your order, or 'done' to complete your order.")

    return str(resp)

def order_summary():
    """Generate a summary of the current order."""
    summary = ""
    for pizza, details in order.items():
        quantity = details["quantity"]
        price = details["price"]
        summary += f"{quantity} {pizza} - ${price:.2f} each\n"
    return summary

def calculate_total():
    """Calculate the total cost of the current order."""
    return sum(item["price"] * item["quantity"] for item in order.values())

if __name__ == "__main__":
    app.run(debug=True)