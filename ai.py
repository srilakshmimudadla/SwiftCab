import re
import dateparser
from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_together import ChatTogether
import random

# 🔑 Replace with your actual Together API key
llm = ChatTogether(
    model="meta-llama-3-70b-instruct",
    temperature=0.5,
    together_api_key="your-together-api-key"
)

# Booking info storage
booking_info = {
    "source": None,
    "destination": None,
    "datetime": None,
    "car_type": None,
    "trip_type": None,
    "fare": None
}

car_types = ['sedan', 'suv', 'hatchback']
trip_types = ['one way', 'round trip', 'round-trip', 'return', 'one', 'round']


# 🔍 Parse datetime from user input
def parse_datetime(text):
    return dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})


# 🔧 Normalize time input like "6 30"
def normalize_time_input(raw):
    time_input = raw.lower().strip().replace(
        "::", ":").replace("  ", " ").replace(" ", ":")
    if "am" not in time_input and "pm" not in time_input:
        ampm = input("🌅 Is that AM or PM?\n> ").strip().lower()
        while ampm not in ["am", "pm"]:
            ampm = input(
                "⚠️ Please enter either 'AM' or 'PM'\n> ").strip().lower()
        time_input += f" {ampm}"
    return time_input


# 🧠 If no time in original input, ask for it
def ensure_datetime_complete(dt, original_text):
    if dt:
        original_text_lower = original_text.lower().strip()
        has_explicit_time = any(t in original_text_lower for t in [
                                'am', 'pm', ':', 'morning', 'evening', 'noon', 'night'])
        if not has_explicit_time:
            time_input = input(
                "🕒 Got the date, but what time exactly? (e.g. '6:30 PM')\n> ").strip()
            time_input = normalize_time_input(time_input)
            time_parsed = dateparser.parse(time_input)
            while not time_parsed:
                time_input = input(
                    "⚠️ Still not clear. Try something like '7 PM' or '18:00'\n> ").strip()
                time_input = normalize_time_input(time_input)
                time_parsed = dateparser.parse(time_input)
            dt = dt.replace(hour=time_parsed.hour, minute=time_parsed.minute)
    return dt


# 🗺️ Extract locations from free-form text
def extract_locations(message):
    msg = message.lower()
    match = re.search(r'from\s+(\w[\w\s]+)\s+to\s+(\w[\w\s]+)', msg)
    if match:
        return match.group(1).strip().title(), match.group(2).strip().title()
    to_match = re.search(
        r'(?:ride|cab|taxi|travel)\s+(?:to|towards)\s+(\w[\w\s]+)', msg)
    if to_match:
        return None, to_match.group(1).strip().title()
    return None, None


def confirm_field(field_name, value):
    print(f"✅ Confirmed: {field_name.capitalize()} is **{value}**")


# 💸 Fare estimation + bargaining
def estimate_fare(src, dst, car_type):
    base_fare = {
        "Sedan": 3500,
        "Suv": 4000,
        "Hatchback": 3000
    }.get(car_type, 3500)
    return base_fare + random.randint(-200, 300)


def bargain_fare(fare):
    print(f"\n💸 The estimated fare is ₹{fare}")
    user_response = input("💬 Do you want to bargain? (yes/no)\n> ").lower()

    if user_response.startswith("y"):
        min_fare = fare * 0.8
        current_offer = fare

        while True:
            user_offer = input("💬 What's your offer? (e.g. 3500)\n> ").strip()
            if not user_offer.isdigit():
                print("❌ Please enter a number like 3500.")
                continue

            user_offer = int(user_offer)

            if user_offer >= current_offer:
                print(f"🤝 Deal! We'll go with ₹{user_offer}")
                return user_offer

            elif user_offer >= min_fare:
                counter = (user_offer + current_offer) // 2
                print(f"🤖 Hmm... how about ₹{counter}?")
                confirm = input("💬 Deal? (yes/no)\n> ").strip().lower()
                if confirm.startswith("y"):
                    print(f"✅ Bargain successful! Final fare: ₹{counter}")
                    return counter
                else:
                    current_offer = counter
                    continue

            else:
                print(
                    f"🛑 Sorry, ₹{user_offer} is too low. Lowest I can go is ₹{int(min_fare)}.")
                confirm = input(
                    f"💬 Want to accept ₹{int(min_fare)}? (yes/no)\n> ").strip().lower()
                if confirm.startswith("y"):
                    print(f"✅ Deal at ₹{int(min_fare)}")
                    return int(min_fare)
                else:
                    print("❌ Booking canceled due to failed negotiation.")
                    exit()

    else:
        print(f"✅ Proceeding with ₹{fare}")
        return fare


# ✏️ Confirm and optionally edit before final booking
def confirm_booking():
    # 👉 FIRST estimate and bargain the fare
    fare = estimate_fare(
        booking_info["source"], booking_info["destination"], booking_info["car_type"])
    final_fare = bargain_fare(fare)
    booking_info["fare"] = f"₹{final_fare}"

    # THEN show the booking summary
    print("\n📝 Here's your Booking Summary:")
    for k, v in booking_info.items():
        print(f"➡️ {k.capitalize()}: {v}")

    # Optional edit step
    edit = input(
        "\n✏️ Do you want to **edit** any field? (yes/no)\n> ").lower()
    if edit.startswith("y"):
        field = input(
            "🛠 Which one? (source, destination, datetime, car_type, trip_type)\n> ").lower()
        if field in booking_info:
            new_value = input(f"✏️ Enter new value for {field}:\n> ")
            if field == "datetime":
                parsed = parse_datetime(new_value)
                parsed = ensure_datetime_complete(parsed, new_value)
                while not parsed:
                    new_value = input(
                        "⚠️ Still not valid. Try like 'July 10th 6:30pm'\n> ")
                    parsed = parse_datetime(new_value)
                    parsed = ensure_datetime_complete(parsed, new_value)
                booking_info[field] = parsed.strftime("%Y-%m-%d %I:%M %p")
            else:
                booking_info[field] = new_value.title()
            print(f"✅ Updated: {field} is now **{booking_info[field]}**")
            confirm_booking()
        else:
            print("❌ Invalid field.")
            confirm_booking()
    else:
        print("\n✅ Your cab is being booked. Thank you for choosing SwiftCab!")

# 🧠 Chat loop


def run_booking_assistant():
    print("🚕 Welcome to **SwiftCab Booking Assistant**!")
    print("💬 How may I help you today?")

    history = []

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue

        history.append(HumanMessage(content=user_input))

        # Step 1: Try extracting source/destination immediately
        if not booking_info["source"] or not booking_info["destination"]:
            src, dst = extract_locations(user_input)
            if src and not booking_info["source"]:
                booking_info["source"] = src
                confirm_field("source", src)
            if dst and not booking_info["destination"]:
                booking_info["destination"] = dst
                confirm_field("destination", dst)

        # Ask for missing fields one-by-one
        if not booking_info["source"]:
            booking_info["source"] = input(
                "📍 What's your **pickup location**?\n> ").strip().title()
            confirm_field("source", booking_info["source"])

        if not booking_info["destination"]:
            booking_info["destination"] = input(
                "📍 Where do you want to go?\n> ").strip().title()
            confirm_field("destination", booking_info["destination"])

        if not booking_info["datetime"]:
            time_input = input(
                "🕒 When do you want to travel? (e.g. 'tomorrow 6pm', '27th at 7:30am')\n> ")
            parsed = parse_datetime(time_input)
            parsed = ensure_datetime_complete(parsed, time_input)
            while not parsed:
                time_input = input(
                    "⚠️ Couldn't understand. Try again with format like 'July 10th at 9am'\n> ")
                parsed = parse_datetime(time_input)
                parsed = ensure_datetime_complete(parsed, time_input)
            booking_info["datetime"] = parsed.strftime("%Y-%m-%d %I:%M %p")
            confirm_field("datetime", booking_info["datetime"])

        if not booking_info["car_type"]:
            print("🚗 What car type do you prefer? (sedan / suv / hatchback)")
            while True:
                car_input = input("> ").lower()
                if car_input in car_types:
                    booking_info["car_type"] = car_input.title()
                    confirm_field("car type", booking_info["car_type"])
                    break
                else:
                    print("❌ Invalid. Choose sedan / suv / hatchback.")

        if not booking_info["trip_type"]:
            print("🔁 Is this a one way or round trip?")
            while True:
                trip_input = input("> ").lower()
                if any(t in trip_input for t in trip_types):
                    if "round" in trip_input:
                        booking_info["trip_type"] = "Round Trip"
                    elif "one" in trip_input:
                        booking_info["trip_type"] = "One Way"
                    else:
                        booking_info["trip_type"] = trip_input.title()
                    confirm_field("trip type", booking_info["trip_type"])
                    break
                else:
                    print("❌ Invalid. Say 'one way' or 'round trip'.")

        confirm_booking()
        break


if __name__ == "__main__":
    run_booking_assistant()
