# 🧾 ETH Zürich Menu to Slack Posting Action Bot

This GitHub Action fetches the daily menus from the ETH Zürich **Fusion** and **Food Market** cafeterias, translates and formats them using GPT, and posts a clean, emoji-enhanced message to a specified Slack channel.,,

---

## 🚀 What It Does

- 🧪 Scrapes the ETH Zürich menu pages using Selenium  
- 🧼 Extracts and cleans the visible text  
- 🌐 Translates and formats the menu using GPT (OpenAI)  
- 💬 Posts the final message to Slack using a bot  

---

## 🕒 Schedule

The workflow runs:

- ⏰ Automatically every weekday at **09:00 UTC (10:00 CET)**  
- 🖱️ Or manually via the GitHub **Actions** tab  

---

## 📁 Files

- `.github/workflows/post_menu.yml` – The workflow definition  
- `main.py` – The script that scrapes, translates, and posts the menu  

---

## 🔐 Required Secrets

These must be set under **Repository Settings → Secrets → Actions**:

| Secret Name        | Description                                      |
|--------------------|--------------------------------------------------|
| `OPENAI_API_KEY`   | Your OpenAI API key for GPT access               |
| `SLACK_BOT_TOKEN`  | Your Slack bot token for posting messages        |
| `SLACK_CHANNEL_ID` | The Slack channel ID to post the menu into       |

---

## 🤖 Creating & Adding the Slack Bot

1. **Create a Slack App**
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click **“Create New App”**.
   - Choose **“From scratch”** and give your bot a name, e.g., `ETH Menu Bot`.

2. **Add Bot Token Scope**
   - In the sidebar, go to **OAuth & Permissions**.
   - Under **Bot Token Scopes**, click **Add an OAuth Scope** and add:
     - `chat:write` – to allow the bot to send messages.

3. **Install the App to Your Workspace**
   - Still in **OAuth & Permissions**, click **Install App to Workspace**.
   - Authorize it. You will receive a **Bot User OAuth Token** (starts with `xoxb-`).
   - Save this token as `SLACK_BOT_TOKEN` in GitHub Secrets.

4. **Invite the Bot to a Channel**
   - In your Slack workspace, open the desired channel.
   - Run the command: `/invite @ETH Menu Bot`
   - Open **channel details → More → Copy channel ID** (e.g., `C01ABC2DEF3`).
   - Save this as `SLACK_CHANNEL_ID` in GitHub Secrets.

---
