import os
import re
import requests
from datetime import date
from slack_sdk import WebClient
from dotenv import load_dotenv
from openai import OpenAI as OpenAIClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

# Load env vars
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID")

client = OpenAIClient(api_key=OPENAI_API_KEY)

def extract_visible_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()  # Remove scripts and styles
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text

def fetch_eth_webpage_raw_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # Wait for JS to load
    html = driver.page_source
    driver.quit()
    return html


def translate_menu_with_gpt(visible_text: str) -> str:
    prompt = f"""🧠 TASK: Translate ETH Zürich Cafeteria Menu for Today
(Use this prompt daily to extract and format the menu from one restaurant section on the ETH Zürich cafeteria site.)

🎯 Your Instructions:
	•	Extract only the menu items: main dishes and sides from the visible page.
	•	Output a clean, friendly English translation.
	•	Format for Slack, following the rules below.

✅ Formatting Rules:
	•	One bullet per dish – no grouping of multiple dishes together.
	•	Bold dish name using Slack-style asterisks (*).
	•	Add 1 relevant emoji per dish to increase clarity and engagement. The emoji can be very funny or a joke of the dish sometimes. 
	•	No code blocks, tables, or long explanations.
	•	Combine any buffets into one bullet (e.g. Salad Buffet, Oriental Buffet).
	•	Keep it short, clear, skimmable.
	•	Include the student and worker price where possible at the end of each dish: example 7(11). 

🚫 Do NOT include:
	•	allergens, times, or dates.
	•	Any metadata, commentary, or formatting notes.
	•	Section headers (e.g., no “Food Market” or “Fusion Menu” titles).
	•	The Choose 5 option, pizza margherita, or any buffets.

✅ Example Output:
• 🔥 Spicy Meatballs – In tangy tomato sauce, served with smoked polenta and broccoli with seeds. 11(13)
• 🍖 Schnitzeljagd – Breaded pork schnitzel with tartar sauce, fries, coleslaw, onion ring, and a slice of lemon. 7(11)
• 🥗 Onigiri Woodsmoke (Vegan) – Smoked salmon alternative with sushi rice, edamame, cucumber, nori, and wasabi mayonnaise. 9(11)
• 🍅 Pizza Bruschetta (Vegetarian) – Tomatoes, mozzarella, garlic, basil, and balsamic glaze, served with salad or lemonade. 12(11)
• 🍝 Spaghetti all’Arrabbiata (Vegan) – Spicy tomato sauce with bell pepper strips, topped with grated cheese, served with salad or lemonade. 13(12)

🛑 If no dishes are found, output:
Restaurant Closed."

--- PAGE TEXT START ---
{visible_text}
--- PAGE TEXT END ---
"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content.strip()
            if "Menu translation failed today" not in result:
                return result
        except Exception as e:
            print(f"❌ GPT attempt {attempt + 1} failed:", e)
            time.sleep(1)
    return "Menu translation failed today."


def post_to_slack(message: str):
    client = WebClient(token=SLACK_TOKEN)
    client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
    print("✅ Menu posted to Slack.")


if __name__ == "__main__":
    today = date.today().isoformat()
    url_fm = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?date={today}&id=19#content"
    url_fu = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?date={today}&id=20#content"
    raw_html_fm = fetch_eth_webpage_raw_selenium(url_fm)
    raw_html_fu = fetch_eth_webpage_raw_selenium(url_fu)

    visible_text_fm = extract_visible_text(raw_html_fm)
    visible_text_fu = extract_visible_text(raw_html_fu)

    with open("raw_menu_fm_text.txt", "w", encoding="utf-8") as f:
        f.write(visible_text_fm)
    with open("raw_menu_fu_text.txt", "w", encoding="utf-8") as f:
        f.write(visible_text_fu)

    print("\n📄 Extracted FM text:\n")
    print(visible_text_fm[:2000])
    print("\n📄 Extracted FU text:\n")
    print(visible_text_fu[:2000])
    print("\n--- END OF TEXT SNIPPETS ---\n")

    translated_menu_fm = translate_menu_with_gpt(visible_text_fm)
    translated_menu_fu = translate_menu_with_gpt(visible_text_fu)

    full_message = (f"🍽️ ETH Zürich Menu – Today’s Options\n\n\n "
                    f"*🍽️ Food Market Menu:*\n\n"
                    f"{translated_menu_fm}\n\n\n"
                    f"*🥗 Fusion Menu:*\n\n{translated_menu_fu}\n\n\n"
                    f"Enjoy your meal! 😋🥄")
    print("🔍 Final Menu Message:\n", full_message)
    post_to_slack(full_message)
