from flask import Flask, request, jsonify, render_template
import google.genai as genai
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS

# Secret key for session (still needed if you use session for other things)
app.secret_key = os.urandom(24)

# Gemini client
GOOGLE_GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

# Cache settings (optional)
CACHE_DURATION = 30  # seconds
api_cache = {}

# --- Home route ---
@app.route('/')
def home():
    return render_template("index.html")

# --- Chat route ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        #  MOVE THE DETECTION CODE RIGHT HERE
        price_keywords = ["gold price", "gold rate", "rate of gold", "price of gold", "24k", "22k", "tola rate", "gram rate", "sona rate", "سونے", "سونا"]
        is_price_query = any(keyword in user_message.lower() for keyword in price_keywords)

        general_gold_keywords = ["gold mine", "gold mining", "where gold", "how to mine", "gold reserve", "gold production"]
        is_general_gold = any(keyword in user_message.lower() for keyword in general_gold_keywords)

        is_gold_related = is_price_query and not is_general_gold
        #  END OF DETECTION CODE

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

    
        # Fetch USD → PKR rate from CoinGecko
        try:
            cg_response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=pkr",
                timeout=5
            )
            cg_data = cg_response.json()
            usd_to_pkr = cg_data.get("tether", {}).get("pkr", 280)
        except Exception as e:
            usd_to_pkr = 280
            print(f"🔧 CoinGecko fallback used: {usd_to_pkr}")

    
        # Metals API call - CORRECTED VERSION
        
        gold_price_usd = None
        if is_gold_related:
            try:
                params = {
                    'api_key': os.getenv('METAL_API_KEY'),
                    'base': 'XAU',  # Gold as base currency
                    'currencies': 'USD'
                }
                metal_response = requests.get(os.getenv('METAL_API_URL'), params=params, timeout=5)
                metal_response.raise_for_status()
                metal_data = metal_response.json()
                
                if metal_data.get('success'):
                    # For XAU base, USD rate represents gold price per ounce
                    gold_price_usd = metal_data.get("rates", {}).get("USD")
                    print(f" Gold price fetched: ${gold_price_usd} per ounce")
                else:
                    print(f"❌ Metal API error: {metal_data.get('error')}")
                    
            except requests.RequestException as e:
                print(f"🔧 Metals API request failed: {str(e)}")

        
        # Build gold reply
        
        if is_gold_related and gold_price_usd:
            # Convert gold price from per ounce to per gram
            # 1 ounce = 31.1035 grams
            gold_price_per_gram_usd = gold_price_usd / 31.1035
            price_pkr = gold_price_per_gram_usd * usd_to_pkr

            # Smart city detection
            city_name = "Pakistan"
            city_aliases = {
    # Punjab Cities
    "Lahore": ["lahore", "lhr"],
    "Karachi": ["karachi", "khi"],
    "Islamabad": ["islamabad", "islo", "isl", "isb"],
    "Rawalpindi": ["rawalpindi", "pindi", "rwp"],
    "Faisalabad": ["faisalabad", "faisal", "fsd"],
    "Multan": ["multan"],
    "Gujranwala": ["gujranwala", "gujran", "gwl"],
    "Sialkot": ["sialkot", "skt"],
    "Bahawalpur": ["bahawalpur", "bwp"],
    "Sargodha": ["sargodha", "sgd"],
    "Jhang": ["jhang"],
    "Kasur": ["kasur"],
    "Sheikhupura": ["sheikhupura", "sheikhu"],
    "Rahim Yar Khan": ["rahim yar khan", "rahimyar khan", "ryk"],
    "Dera Ghazi Khan": ["dera ghazi khan", "dg khan", "dgk"],
    "Sahiwal": ["sahiwal", "swl"],
    
    # KPK Cities
    "Peshawar": ["peshawar", "pesh"],
    "Abbottabad": ["abbottabad", "abbott", "abd"],
    "Mardan": ["mardan"],
    "Mingora": ["mingora", "swat"],
    "Kohat": ["kohat"],
    "Bannu": ["bannu"],
    "Dera Ismail Khan": ["dera ismail khan", "d i khan", "dik"],
    "Charsadda": ["charsadda"],
    "Nowshera": ["nowshera"],
    "Mansehra": ["mansehra"],
    "Swabi": ["swabi"],
    "Chitral": ["chitral"],
    
    # Sindh Cities (excluding Karachi)
    "Hyderabad": ["hyderabad", "hyd"],
    "Sukkur": ["sukkur", "skr"],
    "Larkana": ["larkana"],
    "Nawabshah": ["nawabshah", "shaheed benazirabad"],
    "Mirpur Khas": ["mirpur khas", "mirpurkhas"],
    "Jacobabad": ["jacobabad"],
    "Shikarpur": ["shikarpur"],
    "Dadu": ["dadu"],
    "Tando Adam": ["tando adam"],
    "Khairpur": ["khairpur"],
    
    # Balochistan Cities
    "Quetta": ["quetta"],
    "Turbat": ["turbat"],
    "Khuzdar": ["khuzdar"],
    "Hub": ["hub", "hub chowki"],
    "Chaman": ["chaman"],
    "Gwadar": ["gwadar"],
    "Dera Murad Jamali": ["dera murad jamali", "dm jamali"],
    "Zhob": ["zhob"],
    "Sibi": ["sibi"],
    
    # AJK & Gilgit-Baltistan
    "Muzaffarabad": ["muzaffarabad", "muzaffarabad ajk"],
    "Mirpur": ["mirpur", "mirpur ajk"],
    "Rawalakot": ["rawalakot"],
    "Gilgit": ["gilgit"],
    "Skardu": ["skardu"],
    "Hunza": ["hunza"],
    
    # Provinces
    "Punjab": ["punjab"],
    "Sindh": ["sindh"],
    "KPK": ["kpk", "khyber pakhtunkhwa", "khyber", "pakhtunkhwa"],
    "Balochistan": ["balochistan", "baloch"],
    "AJK": ["ajk", "azad kashmir", "kashmir"],
    "Gilgit-Baltistan": ["gilgit baltistan", "gilgit", "baltistan"],
    
    # Major Towns
    "Jhelum": ["jhelum"],
    "Kamoke": ["kamoke"],
    "Hafizabad": ["hafizabad"],
    "Gujrat": ["gujrat"],
    "Wazirabad": ["wazirabad"],
    "Jaranwala": ["jaranwala"],
    "Chiniot": ["chiniot"],
    "Okara": ["okara"],
    "Pakpattan": ["pakpattan"],
    "Bahawalnagar": ["bahawalnagar"]
}

            user_text = user_message.lower()
            for city, aliases in city_aliases.items():
                if any(alias in user_text for alias in aliases):
                    city_name = city
                    break

            reply_text = (
                f" Today's Gold Rates in {city_name} (approx):\n\n"
                f" 24K: {price_pkr:.2f} PKR per gram\n"
                f" 22K: {(price_pkr*0.9167):.2f} PKR per gram\n"
                f" 21K: {(price_pkr*0.875):.2f} PKR per gram\n\n"
                f" Gold Price: ${gold_price_usd:,.2f} per ounce\n"
                f" Note: Rates may slightly vary across cities and jewelers."
            )
            return jsonify({"reply": reply_text})

        elif is_gold_related:
            reply_text = (
                "Live gold data is currently unavailable. Please try again soon."
                "\nI'm here to help only with gold-related topics. "
                "Please ask something about gold."
            )
            return jsonify({"reply": reply_text})

      
        # Non-gold queries: Gemini AI fallback
       
        prompt = f"User asked: {user_message}\n\nAnswer clearly and naturally."

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        final_reply = getattr(response, "text", "I couldn't process your request. Please try again.")

        return jsonify({"reply": final_reply})

    except Exception as e:
        print(f"🔧 General error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
