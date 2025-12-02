import os
import re
import requests
import telebot
from fastapi import FastAPI
from pydantic import BaseModel

# ============================
#  BOT TOKEN (Hardcoded)
# ============================
BOT_TOKEN = "8579506667:AAFFQnfUzAOLKgyz2mLzFFCm2mUjLhyWwWc"
bot = telebot.TeleBot(BOT_TOKEN)

app = FastAPI()


def escape_md(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text or ""))


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict | None = None
    edited_message: dict | None = None


def format_ff_info(data: dict) -> str:
    b = data["basicInfo"]
    c = data.get("clanBasicInfo", {})
    cap = data.get("captainBasicInfo", {})
    cr = data.get("creditScoreInfo", {})
    pet = data.get("petInfo", {})
    s = data.get("socialInfo", {})

    txt = f"""
👤 *Basic Info*
• Name: `{escape_md(b.get("nickname"))}`
• UID: `{b.get("accountId")}`
• Region: `{b.get("region")}`
• Level: `{b.get("level")}`
• Likes: `{b.get("liked")}`
• EXP: `{b.get("exp")}`
• BR Rank: `{b.get("brRank")}`
• CS Rank: `{b.get("csRank")}`
• Max BR: `{b.get("brMaxRank")}`
• Max CS: `{b.get("csMaxRank")}`
• Title ID: `{b.get("title")}`
• Banner ID: `{b.get("bannerId")}`
• Avatar ID: `{b.get("headPic")}`
• Version: `{escape_md(b.get("releaseVersion"))}`

🛡️ *Guild Info*
• Name: `{escape_md(c.get("clanName", 'None'))}`
• ID: `{c.get("clanId")}`
• Level: `{c.get("clanLevel")}`
• Members: `{c.get("memberNum")}/{c.get("capacity")}`
• Captain UID: `{c.get("captainId")}`

👑 *Guild Captain*
• Name: `{escape_md(cap.get("nickname", 'N/A'))}`
• UID: `{cap.get("accountId")}`
• Region: `{cap.get("region")}`
• Level: `{cap.get("level")}`
• Likes: `{cap.get("liked")}`
• BR Rank: `{cap.get("brRank")}`
• CS Rank: `{cap.get("csRank")}`
• BR Points: `{cap.get("brRankingPoints")}`
• CS Points: `{cap.get("csRankingPoints")}`

🐾 *Pet Info*
• Pet ID: `{pet.get("id")}`
• Level: `{pet.get("level")}`
• EXP: `{pet.get("exp")}`
• Skin ID: `{pet.get("skinId")}`
• Skill ID: `{pet.get("selectedSkillId")}`

⭐ *Credit Score*
• Score: `{cr.get("creditScore")}`
• Summary: `{cr.get("periodicSummaryStartTime")} to {cr.get("periodicSummaryEndTime")}`
• Reward State: `{cr.get("rewardState")}`

📱 *Social*
• BR Public: `{s.get("brRankShow")}`
• CS Public: `{s.get("csRankShow")}`
• Bio: `{escape_md(s.get("signature", 'None'))}`

⚡ by @mishra_143p
"""
    return txt


@app.post("/api/webhook")
async def telegram_webhook(update: TelegramUpdate):
    msg = update.message or update.edited_message
    if not msg:
        return {"ok": True}

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if not text.startswith("/"):
        return {"ok": True}

    if text.startswith("/start") or text.startswith("/help"):
        h = """
🎯 *Free Fire Player Info Bot*

🚀 Use:
`/check {region} {uid}`

🎮 Example:
`/check ind 10000001`

👨‍💻 Powered by @mishra_143p
"""
        bot.send_message(chat_id, escape_md(h), parse_mode="MarkdownV2")
        return {"ok": True}

    if text.startswith("/check"):
        p = text.split()
        if len(p) < 3:
            bot.send_message(chat_id, escape_md("❌ Usage: `/check {region} {uid}`"), parse_mode="MarkdownV2")
            return {"ok": True}

        region = p[1].lower()
        uid = p[2]

        load = bot.send_message(chat_id, escape_md("⏳ Fetching Free Fire Account Info..."), parse_mode="MarkdownV2")

        try:
            url = f"https://info-ob49.vercel.app/api/account/?uid={uid}&region={region}"
            r = requests.get(url, timeout=10)

            if r.status_code != 200:
                bot.edit_message_text(f"❌ API Error: {r.status_code}", chat_id, load.message_id)
                return {"ok": True}

            data = r.json()
            if not data.get("basicInfo"):
                bot.edit_message_text("❌ No player found.", chat_id, load.message_id)
                return {"ok": True}

            bot.edit_message_text(format_ff_info(data), chat_id, load.message_id, parse_mode="MarkdownV2")
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {e}", chat_id, load.message_id)

    return {"ok": True}
