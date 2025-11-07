from flask import Flask, request, jsonify, render_template, session
import google.genai as genai
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # enable CORS for all routes 

#  Secret key for Flask session
app.secret_key = os.urandom(24)

#  Gemini client
GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
GOLD_API_KEY = os.getenv("GOLD_API_KEY")

client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

# --- Home route ---
@app.route('/')
def home():
    return render_template("index.html")

# --- Chat API ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        #  Create memory if it doesn’t exist yet
        if "chat_history" not in session:
            session["chat_history"] = []

        #  Append user message to memory
        session["chat_history"].append({"role": "user", "content": user_message})

        #  Combine last 5 messages into context for Gemini
        context = "\n".join(
            [f"{m['role']}: {m['content']}" for m in session["chat_history"][-5:]]
        )

        # --- Detect if user is asking anything about gold ---
        gold_keywords = ["gold", "rate", "price", "24k", "22k", "golden", "jewelry", "gram", "tola"]
        is_gold_related = any(keyword in user_message.lower() for keyword in gold_keywords)

        # -----------------------------
        #  Fetch live gold in USD
        # -----------------------------
        GOLD_API_URL = os.getenv("GOLD_API_URL")
        headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}

        try:
            gold_response = requests.get(GOLD_API_URL, headers=headers, timeout=5)

            if gold_response.status_code == 200:
                gold_data = gold_response.json()
            else:
                gold_data = {}
        except requests.RequestException:
            gold_data = {}

        # -----------------------------
        #  Fetch live USDT → PKR rate from CoinGecko
        # -----------------------------
        try:
            cg_response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=pkr",
                timeout=5
            )
            cg_data = cg_response.json()
            usd_to_pkr = cg_data.get("tether", {}).get("pkr", 280)
        except:
            usd_to_pkr = 280  # fallback rate

        # -----------------------------
        #  Build gold reply using CoinGecko conversion
        # -----------------------------
        if is_gold_related and gold_data and "price" in gold_data:
            price_usd = gold_data["price"]
            price_pkr = price_usd * usd_to_pkr

            # 🔍 Smart city detection (insert here)
            city_name = "Pakistan"
            city_aliases = {
                "Karachi": ["karachi", "khi"],
                "Lahore": ["lahore", "lhr"],
                "Islamabad": ["islamabad", "islo", "isl"],
                "Rawalpindi": ["rawalpindi", "pindi"],
                "Peshawar": ["peshawar", "pesh"],
                "Quetta": ["quetta"],
                "Multan": ["multan"],
                "Faisalabad": ["faisalabad", "faisal", "fsd"],
                "Hyderabad": ["hyderabad", "hydr"],
                "Sialkot": ["sialkot", "skt"],
                "Gujranwala": ["gujranwala", "gwl"]
            }

            user_text = user_message.lower()
            for city, aliases in city_aliases.items():
                if any(alias in user_text for alias in aliases):
                    city_name = city
                    break

            reply_text = (
                f" Today's Gold Rates in {city_name} (approx):\n\n"
                f"24K: {price_pkr:.2f} PKR per gram\n"
                f"22K: {(price_pkr*0.9167):.2f} PKR per gram\n"
                f"21K: {(price_pkr*0.875):.2f} PKR per gram\n\n"
                f" Note: Rates may slightly vary across cities and jewelers."
            )

        elif is_gold_related:
            reply_text = "Live gold data is currently unavailable. Please try again soon."
        else:
            reply_text = "Let me check Gemini for that..."

       
        # -----------------------------
        #  Ask Gemini to refine or generate response
        # -----------------------------
        is_gold_related = any(word in user_message.lower() for word in ["gold", "karat", "tola", "gram", "jewelry", "jewel", "mine", "mining", "golden"])

        if is_gold_related:
            prompt = (
                f"User asked: {user_message}\n\n"
                f"If the question is about current gold prices, use the data below:\n{reply_text}\n\n"
                f"But if the question is about gold in general (like mining, purity, history, or other info), "
                f"answer naturally using your own reliable knowledge without saying you lack data."
            )
        else:
            prompt = f"User asked: {user_message}\n\nAnswer clearly and naturally."

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        final_reply = getattr(response, "text", reply_text)

        #  Save bot’s response in memory
        session["chat_history"].append({"role": "bot", "content": final_reply})
        session.modified = True

        return jsonify({"reply": final_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run Flask App ---
if __name__ == '__main__':
    app.run(debug=True)
