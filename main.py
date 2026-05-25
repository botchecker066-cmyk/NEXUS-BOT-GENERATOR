#!/usr/bin/env python3
"""
🔥 NEXUS BOT GENERATOR - FULL WORKING VERSION
✅ All Features Implemented | Single File | Termux & VPS Ready
"""

# ==============================================
# 📦 IMPORT LIBRARIES
# ==============================================
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler
)
import os
import json
import random
import string
import time
import requests # For IP Grabber
from datetime import datetime
from flask import Flask
from threading import Thread

# ===== WEBKEEP ALIVE =====
app_web = Flask(__name__)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

@app_web.route("/")
def home():
    return "Bot is online!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()

# ==============================================
# ⚙️ CONFIGURATION - EDIT THESE VALUES
# ==============================================
BOT_TOKEN = "8521492677:AAFrP9mGWZzehoPs6cNxfyHm5AIy3X8bFWE"
ADMIN_ID = 6538213760
BOT_NAME = "NEXUS VIP BOT GENERATOR"
VERSION = "2.0"

# ⏳ REQUIREMENTS SETTINGS
COOLDOWN_TIME = 600  # 10 MINUTES = 600 SECONDS
MAX_GENERATE = 100   # MAX 100 LINES PER GENERATE

# 🛡️ SECURITY SETTINGS
ENABLE_IP_LOCK = True      # I-lock sa device/IP
AUTO_BAN_ON_SHARE = True   # Auto ban kapag ginamit sa iba

# ==============================================
# 📂 FOLDER & FILE PATHS - AUTO SETUP
# ==============================================
BASE_DIR = os.getcwd()
FOLDERS = {
    "DATA": os.path.join(BASE_DIR, "data"),
    "LOGS": os.path.join(BASE_DIR, "logs"),
    "SALPAK": os.path.join(BASE_DIR, "salpak"),
    "TOOLS": os.path.join(BASE_DIR, "tools")
}

FILES = {
    "USERS": os.path.join(FOLDERS["DATA"], "users.json"),
    "KEYS": os.path.join(FOLDERS["DATA"], "keys.json")
}

# GLOBAL VARIABLES
COOLDOWN = {}

# ==============================================
# 🛠️ AUTO CREATE FOLDERS & FILES
# ==============================================
def setup_system():
    """Create required folders and files automatically"""
    # Create all folders
    for folder in FOLDERS.values():
        os.makedirs(folder, exist_ok=True)
    
    # Create default JSON files if not exist
    for file_path in [FILES["USERS"], FILES["KEYS"]]:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({}, f, indent=4)

setup_system()

# ==============================================
# 📝 JSON FILE HANDLERS
# ==============================================
def load_json(file_path):
    try:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Loading {file_path}: {e}")
        return {}

def save_json(file_path, data):
    try:
        temp_file = f"{file_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        print(f"[ERROR] Saving {file_path}: {e}")
        return False

# ==============================================
# 📜 LOG SYSTEM
# ==============================================
def add_log(action, user_id, details=""):
    log_file = os.path.join(FOLDERS["LOGS"], "bot_logs.txt")
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_text = f"[{timestamp}] | ID: {user_id} | ACTION: {action} | DETAILS: {details}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_text)
    except:
        pass

# ==============================================
# 🔐 ACCESS & KEY SYSTEMS
# ==============================================
def check_access(user_id):
    """Check if user has active access"""
    users = load_json(FILES["USERS"])
    uid = str(user_id)
    
    if uid not in users:
        return False, "🔑 No active key"
    
    user_data = users[uid]
    if not user_data.get("active", False):
        return False, "🚫 Access deactivated"
    
    return True, "✅ Access Active"

def generate_key_string():
    chars = string.ascii_uppercase + string.digits
    keys = load_json(FILES["KEYS"])

    while True:
        random_part = ''.join(random.choice(chars) for _ in range(24))  # mas mahaba
        new_key = f"XINNN-{random_part}"

        if new_key not in keys:
            return new_key

# ==============================================
# 🎮 GENERATOR FUNCTIONS
# ==============================================
def get_available_games():
    """Get all .txt files from salpak folder"""
    try:
        files = [f for f in os.listdir(FOLDERS["SALPAK"]) if f.endswith(".txt")]
        return {f.replace(".txt", "").upper(): os.path.join(FOLDERS["SALPAK"], f) for f in files}
    except:
        return {}

def load_accounts(file_path):
    """Load accounts max 200 lines only"""
    try:
        with open(file_path, "r", errors="ignore") as f:
            lines = [x.strip() for x in f if x.strip()]
        
        if not lines:
            return []
        
        # Remove duplicates
        lines = list(dict.fromkeys(lines))
        
        # Return max 200 only
        return lines if len(lines) <= MAX_GENERATE else random.sample(lines, MAX_GENERATE)
    except Exception as e:
        print(f"[ERROR] Loading accounts: {e}")
        return []

# ==============================================
# 📨 COMMANDS & HANDLERS
# ==============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main start command with inline menu"""

    user = update.effective_user
    uid = str(user.id)
    has_access, status_msg = check_access(uid)

    # Build buttons
    keyboard = []

    if has_access:
        keyboard.append([InlineKeyboardButton("🎮 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘", callback_data="menu_generate")])
        keyboard.append([InlineKeyboardButton("ℹ️ 𝗠𝗬 𝗦𝗧𝗔𝗧𝗨𝗦", callback_data="menu_status")])
        keyboard.append([InlineKeyboardButton("📥 𝗧𝗢𝗢𝗟𝗦", callback_data="menu_tools")])

    keyboard.append([InlineKeyboardButton("🔑 𝗥𝗘𝗗𝗘𝗘𝗠 𝗛𝗘𝗟𝗣", callback_data="redeem_help")])

    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🔐 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel")])

    # Message text
    if has_access:
        msg = f"""
╔══════════════════════════════════╗
║        🤖 {BOT_NAME}        ║
║            🔖 VERSION {VERSION}           ║
╚══════════════════════════════════╝

{status_msg}
🎉 Welcome {user.first_name}!

📌 BOT DESCRIPTION:
• ⚡ This bot is an automated generator system designed to process and produce structured TXT outputs in a simple and efficient way
• 📄 It generates results in a user:pass format and organizes them into clean text files for easy use and readability
• 🛠️ The system includes multiple built-in tools that help perform different automated functions inside the bot
• 🔐 Each access key is strictly limited to one user only to ensure security, fairness, and controlled usage
• ⏳ A cooldown system is implemented to prevent overload and maintain stable performance during continuous use
• 🤖 The entire process is fully automated, allowing users to operate the bot easily without complicated steps or setup
• 📡 Built for consistent performance, fast processing, and reliable output generation at all times
• 📁 Outputs are delivered in TXT format, making it easy to download, store, and manage results efficiently

👇 Choose option below:
        """
    else:
        msg = f"""
╔══════════════════════════════════╗
║        🤖 {BOT_NAME}        ║
║            🔖 VERSION {VERSION}           ║
╚══════════════════════════════════╝

{status_msg}
🔑 Need valid key to unlock all features!

💡 How to activate:
Type: /redeem <your_key>
Example: /redeem XINNN-ABC123XYZ

⚠️ 1 Key = 1 User Only, cannot be shared!
        """

    # 🔥 IMPORTANT FIX HERE
    await update.effective_message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    
# ==============================================
# 🌐 GET REAL IP (FIX CRASH)
# ==============================================
def get_real_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Unknown"
        
# ==============================================
# 🔑 REDEEM COMMAND
# ==============================================
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /redeem <key>")
        return

    key = context.args[0].upper()
    uid = str(update.effective_user.id)
    users = load_json(FILES["USERS"])
    keys = load_json(FILES["KEYS"])

    # 🛡️ CHECK KUNG MAY ACTIVE KEY NA
    if uid in users:
        await update.message.reply_text("❌ You already have an active key!")
        return

    # 🛡️ CHECK KUNG EXIST YUNG KEY
    if key not in keys:
        await update.message.reply_text("❌ Invalid Key!")
        return

    # 🛡️ CHECK KUNG GINAMIT NA
    # 🛡️ CHECK KUNG VALID PA ANG KEY (NEW SYSTEM)
    if keys[key].get("status") != "unused":
        await update.message.reply_text("""
❌ 𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗢𝗥 𝗘𝗫𝗣𝗜𝗥𝗘𝗗 𝗞𝗘𝗬!
🔒 This key cannot be used anymore.
        """)
        return

    # 🌐 GET IP
    user_ip = get_real_ip()

    # 📝 GET USER INFO
    user_name = update.effective_user.first_name or "No Name"
    user_tag = update.effective_user.username or "No Username"

    # 📝 SAVE KEY INFO
    keys[key]["used"] = True
    keys[key]["status"] = "used"  # ✅ NEW
    keys[key]["user_id"] = uid
    keys[key]["used_at"] = datetime.now().isoformat()

    # 📝 SAVE USER INFO
    users[uid] = {
        "active": True,
        "key_used": key,
        "joined_at": datetime.now().isoformat(),
        "device_id": str(update.effective_chat.id),
        "locked_ip": user_ip,
        "last_ip": user_ip,
        "banned": False,
        "fullname": str(user_name),
        "username": str(user_tag)
    }

    # 💾 SAVE
    save_json(FILES["USERS"], users)
    save_json(FILES["KEYS"], keys)
    
    # 📝 LOGS
    add_log("KEY_REDEEMED", uid, f"Name: {user_name} | User: @{user_tag} | Key: {key} | Device Locked")

    # ✅ REPLY
    await update.message.reply_text(f"""
✅ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗚𝗥𝗔𝗡𝗧𝗘𝗗!
🎉 Welcome {user_name}!
🔓 All features are now unlocked.
🔑 Key: `{key}`
⏳ Type: LIFETIME ACCESS
🔒 Status: LOCKED TO YOUR ID
✅ Enjoy using the bot!
        """)


# ==============================================
# 📊 STATUS COMMAND & BUTTON FUNCTION
# ==============================================
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE, is_button=False):
    """Show user status - works for both command and button"""
    if is_button:
        query = update.callback_query
        user = query.from_user
        message_func = query.message.reply_text
    else:
        user = update.effective_user
        message_func = update.message.reply_text

    uid = str(user.id)
    has_access, status_msg = check_access(uid)

    if not has_access:
        text = f"""
❌ 𝗡𝗢 𝗔𝗖𝗧𝗜𝗩𝗘 𝗔𝗖𝗖𝗘𝗦𝗦

{status_msg}
🔓 Use /redeem <key> to activate
        """
        keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="back_main")]]
        await message_func(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    users = load_json(FILES["USERS"])
    user_data = users[uid]
    joined = datetime.fromisoformat(user_data["joined_at"]).strftime("%d-%m-%Y %H:%M")

    keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡", callback_data="back_main")]]

    text = f"""
👤 𝗠𝗬 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗜𝗡𝗙𝗢

• 📛 Name: {user.first_name}
• 🆔 ID: `{uid}`
• ✅ Status: {status_msg}
• 🔑 Key Used: `{user_data['key_used']}`
• 📅 Joined: {joined}
• ⏳ Cooldown: 10 minutes 
• 📄 Max Generate: {MAX_GENERATE} Lines

🔒 Your access is secured and lifetime!
            """
    
    if is_button:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message_func(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Old status command para gumana pa rin /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update, context, is_button=False)


# ==============================================
# 🔘 BUTTON HANDLER
# ==============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    uid = str(user.id)
    data = query.data
    
    
    # ==============================================
    # 🔑 REDEEM HELP MENU (FIX)
    # ==============================================
    if data == "redeem_help":
        text = """
    🔑 𝗛𝗢𝗪 𝗧𝗢 𝗥𝗘𝗗𝗘𝗘𝗠 𝗔 𝗞𝗘𝗬

    Step 1:
    Send command:
    `/redeem YOUR_KEY`

    Example:
    `/redeem XINNN-ABCD1234EFGH5678`

    📌 Important Rules:
    • 1 Key = 1 User only
    • Key cannot be shared
    • Key cannot be reused
    • Key is locked to your Telegram ID

    ⚠️ If key is already used → it will NOT work.

    After redeeming, all features unlock automatically 🎉
        """

        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    

    # BACK TO MAIN
    if data == "back_main":
        user = update.callback_query.from_user
        uid = str(user.id)
        has_access, status_msg = check_access(uid)

        keyboard = []

        if has_access:
            keyboard.append([InlineKeyboardButton("🎮 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘", callback_data="menu_generate")])
            keyboard.append([InlineKeyboardButton("ℹ️ 𝗠𝗬 𝗦𝗧𝗔𝗧𝗨𝗦", callback_data="menu_status")])
            keyboard.append([InlineKeyboardButton("📥 𝗧𝗢𝗢𝗟𝗦", callback_data="menu_tools")])

        keyboard.append([InlineKeyboardButton("🔑 𝗥𝗘𝗗𝗘𝗘𝗠 𝗛𝗘𝗟𝗣", callback_data="redeem_help")])

        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("🔐 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel")])

        if has_access:
            msg = f"""
╔══════════════════════════════════╗
║        🤖 {BOT_NAME}        ║
║            🔖 VERSION {VERSION}           ║
╚══════════════════════════════════╝

{status_msg}
🎉 Welcome {user.first_name}!

📌 SYSTEM RULES:
• ⏳ Cooldown: 10 minutes 
• 📄 Max Generate: {MAX_GENERATE} Lines
• 🔒 1 Key = 1 User Only

👇 Choose option below:
            """
        else:
            msg = f"""
╔══════════════════════════════════╗
║        🤖 {BOT_NAME}        ║
║            🔖 VERSION {VERSION}           ║
╚══════════════════════════════════╝

{status_msg}
🔑 Need valid key to unlock all features!

💡 How to activate:
Type: /redeem <your_key>
Example: /redeem XINNN-ABC123XYZ

⚠️ 1 Key = 1 User Only, cannot be shared!
            """

        await update.callback_query.message.edit_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        return

    # ==============================================
    # ⚡ GENERATE ACCOUNT PROCESS (NO DUPLICATE)
    # ==============================================
    if data.startswith("gen_"):
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

        # ⏳ CHECK COOLDOWN 3 MINUTES
        now = time.time()
        if uid in COOLDOWN:
            last_used = COOLDOWN[uid]
            if now - last_used < COOLDOWN_TIME:
                remaining = int(COOLDOWN_TIME - (now - last_used))
                mins = remaining // 60
                secs = remaining % 60
                await query.answer(f"⏳ Wait {mins}min {secs}sec!", show_alert=True)
                return

        # Get file path
        game_name = data.replace("gen_", "").upper()
        games = get_available_games()
        file_path = games.get(game_name)

        if not file_path or not os.path.exists(file_path):
            await query.answer("❌ File not found!", show_alert=True)
            return

        # 🧹 LOAD + REMOVE DUPLICATES AUTOMATICALLY
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = [line.strip() for line in f if line.strip()]
            
            # ✅ TANGGAL ANG DOBLE (PRESERVE ORDER)
            unique_accounts = list(dict.fromkeys(all_lines))
            total_unique = len(unique_accounts)

            if total_unique == 0:
                await query.message.reply_text("❌ NO MORE UNIQUE ACCOUNTS AVAILABLE!")
                return

            # ✅ KUNIN ANG BIBIGAY (BASE SA LIMIT MO)
            accounts = unique_accounts[:MAX_GENERATE]
            count_given = len(accounts)

        except Exception as e:
            await query.message.reply_text(f"❌ Error reading file: {str(e)}")
            return

        # 🗑️ I-UPDATE ANG STOCK - TANGGALIN ANG IBINIGAY
        remaining = [acc for acc in unique_accounts if acc not in accounts]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining))

        # 📄 I-SAVE AT IPADALA
        temp_file = os.path.join(BASE_DIR, f"{game_name}_ACCOUNTS.txt")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("\n".join(accounts))

        await query.message.reply_document(
            document=open(temp_file, "rb"),
            filename=f"{game_name}_ACCOUNTS.txt",
            caption=f"""
✅ 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬!
🎮 ITEM: {game_name}
🔢 GIVEN: {count_given} ACCOUNTS
📊 REMAINING: {len(remaining)} UNIQUE
✨ FEATURE: NO DUPLICATE SYSTEM
⏳ COOLDOWN: 10 minutes 
        """
      
        
        )

        os.remove(temp_file)

        # 💾 I-SET ANG COOLDOWN
        COOLDOWN[uid] = time.time()

        keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗟𝗜𝗦𝗧", callback_data="menu_generate")]]
        await query.message.reply_text("👇 Tap to generate again:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    
    # ==============================================
    # 🎮 GENERATE MENU WITH STOCK
    # ==============================================
    if data == "menu_generate":
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

        games = get_available_games()
        if not games:
            keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
            await query.edit_message_text("❌ No tools found in 'salpak' folder!", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        text = """
╔══════════════════════════════════╗
║       🎮 𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘 𝗦𝗧𝗢𝗖𝗞       ║
╚══════════════════════════════════╝

📋 Select item to generate:
"""

        keyboard = []
        for game_name, file_path in games.items():
            try:
                # 📊 COUNT LINES
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f if line.strip()]
                count = len(lines)

                # 🎨 STATUS COLOR
                if count > 50:
                    status = "🟢 FULL"
                elif count > 10:
                    status = "🟡 LOW"
                elif count > 0:
                    status = "🔴 CRITICAL"
                else:
                    status = "⚫ OOS"

                # ➕ SA TEXT
                text += f"\n• 🎮 {game_name}\n  📊 Stock: {count} Lines | {status}\n"

                # ➕ SA BUTTON
                keyboard.append([InlineKeyboardButton(f"🎮 {game_name} [{count}]", callback_data=f"gen_{game_name}")])

            except:
                # KUNG MAY ERROR SA FILE
                text += f"\n• 🎮 {game_name}\n  ⚠️ Cannot read file\n"
                keyboard.append([InlineKeyboardButton(f"🎮 {game_name} [ERROR]", callback_data=f"gen_{game_name}")])

        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        return


    # ==============================================
    # 📊 MY STATUS MENU
    # ==============================================
    if data == "menu_status":
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

        user_data = load_json(FILES["USERS"])[uid]
        name = user_data.get('fullname', 'No Name')
        username = user_data.get('username', 'No Username')
        key_used = user_data.get('key_used', 'None')
        joined = datetime.fromisoformat(user_data['joined_at']).strftime("%d-%m-%Y")
        ip_addr = user_data.get('locked_ip', 'Unknown')

        text = f"""
📊 𝗬𝗢𝗨𝗥 𝗦𝗧𝗔𝗧𝗨𝗦

👤 Name: {name}
🏷️ User: @{username}
🆔 ID: `{uid}`
🔑 Key: `{key_used}`
🌐 IP: `{ip_addr}`
📅 Joined: {joined}
✅ Status: 𝗔𝗖𝗧𝗜𝗩𝗘

🔒 1 Key = 1 User Only
        """

        keyboard = [[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
        
    
    
    # ==============================================
    # 📥 TOOLS MENU
    # ==============================================
    if data == "menu_tools":
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

        try:
            tools = [f for f in os.listdir(FOLDERS["TOOLS"]) if os.path.isfile(os.path.join(FOLDERS["TOOLS"], f))]
        except:
            tools = []

        if not tools:
            keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="back_main")]]
            await query.edit_message_text("❌ No tools available yet!", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        keyboard = []
        for tool in tools:
            keyboard.append([InlineKeyboardButton(f"📥 {tool}", callback_data=f"dl_{tool}")])
        
        keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="back_main")])

        await query.edit_message_text(
            """
    ⚙️ 𝗧𝗢𝗢𝗟𝗦 𝗠𝗘𝗡𝗨

    📋 Available files for download:
    • All files are safe and working
    • Exclusive for premium users
    👇 Select file below:
            """, reply_markup=InlineKeyboardMarkup(keyboard))
        return
        



    # DOWNLOAD TOOL
    if data.startswith("dl_"):
        filename = data.replace("dl_", "")
        file_path = os.path.join(FOLDERS["TOOLS"], filename)

        if not os.path.exists(file_path):
            await query.message.reply_text("❌ File not found!")
            return

        await query.message.reply_document(
            document=open(file_path, "rb"),
            filename=filename,
            caption=f"✅ Downloaded: {filename}"
        )
        return

    # ==============================================
    # 🔐 ADMIN PANEL MAIN MENU
    # ==============================================
    if data == "admin_panel":
        if user.id != ADMIN_ID:
            await query.answer("❌ Admin only!", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("🔑 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘 𝗞𝗘𝗬", callback_data="admin_genkey")],
            [InlineKeyboardButton("👥 𝗩𝗜𝗘𝗪 𝗔𝗟𝗟 𝗨𝗦𝗘𝗥𝗦", callback_data="admin_users")],
            [InlineKeyboardButton("🔎 𝗦𝗘𝗔𝗥𝗖𝗛 𝗨𝗦𝗘𝗥", callback_data="search_user")], # <-- DAGDAG ITO
            [InlineKeyboardButton("🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗨𝗦𝗘𝗥", callback_data="admin_remove")],
            [InlineKeyboardButton("📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗦", callback_data="admin_stats")],
            [InlineKeyboardButton("📜 𝗩𝗜𝗘𝗪 𝗟𝗢𝗚𝗦", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡", callback_data="back_main")]
        ]



        await query.edit_message_text(
            f"""
🔐 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟

🤖 Bot: {BOT_NAME} v{VERSION}
👤 Admin: {user.first_name}

📌 Features:
• Generate Lifetime Keys
• Manage Users
• Broadcast Messages
• Full System Control
            """, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ==============================================
    # 🔑 ADMIN GENERATE KEY
    # ==============================================
    if data == "admin_genkey":
        if user.id != ADMIN_ID: return

        new_key = generate_key_string()
        keys = load_json(FILES["KEYS"])

        keys[new_key] = {
            "used": False,
            "status": "unused",  # ✅ NEW
            "user_id": None,
            "created_at": datetime.now().isoformat()
        }

        save_json(FILES["KEYS"], keys)

        keyboard = [
            [InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗔𝗗𝗠𝗜𝗡", callback_data="admin_panel")]
        ]

        await query.edit_message_text(
            f"""
✅ 𝗞𝗘𝗬 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗!

🔑 Key: `{new_key}`
⏳ Type: LIFETIME ACCESS
🔒 Status: UNUSED

📝 Note: 1 Key = 1 User Only
            """, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ==============================================
    # 👥 VIEW ALL USERS (FULL INFO + IP | FIXED)
    # ==============================================
    if data.startswith("admin_users"):
        if user.id != ADMIN_ID:
            await query.answer("❌ ADMIN ONLY!", show_alert=True)
            return

    # page number extractor
    try:
        page = int(data.split("_")[-1])
    except:
        page = 1

    users_data = load_json(FILES["USERS"])
    user_list = list(users_data.items())
    total_users = len(user_list)

    USERS_PER_PAGE = 10
    total_pages = (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE

    start = (page - 1) * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    users_page = user_list[start:end]

    text = f"""
╔══════════════════════════════════╗
║         👥 ALL USERS LIST        ║
║        📊 TOTAL: {total_users} USERS        ║
║        📄 PAGE {page}/{total_pages}        ║
╚══════════════════════════════════╝
"""

    count = start + 1
    for uid, info in users_page:
        name = info.get('fullname', 'No Name')
        username = info.get('username', 'No Username')
        key = info.get('key_used', 'N/A')
        ip_addr = info.get('locked_ip', 'Unknown')

        try:
            joined = datetime.fromisoformat(info.get('joined_at')).strftime("%d-%m-%Y")
        except:
            joined = "Unknown"

        text += f"""
{count}. 🆔 ID: `{uid}`
👤 NAME: {name}
🏷️ USER: @{username}
🔑 KEY: `{key}`
🌐 IP: {ip_addr}
📅 JOINED: {joined}
──────────────────────────────────
"""
        count += 1

    # buttons
    keyboard = []

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ PREV", callback_data=f"admin_users_{page-1}"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("NEXT ➡️", callback_data=f"admin_users_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
    return


    # ==============================================
    # 🗑️ ADMIN REMOVE USER MENU
    # ==============================================
    if data == "admin_remove":
        if user.id != ADMIN_ID: return

        keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_panel")]]
        await query.edit_message_text(
            """
🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗨𝗦𝗘𝗥 𝗔𝗖𝗖𝗘𝗦𝗦

📝 Command: /remove <user_id>
Example: /remove 123456789

⚠️ This will free up the key!
            """, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ==============================================
    # 📊 ADMIN BOT STATS
    # ==============================================
    if data == "admin_stats":
        if user.id != ADMIN_ID: return

        users = load_json(FILES["USERS"])
        keys = load_json(FILES["KEYS"])

        total_users = len(users)
        total_keys = len(keys)
        used_keys = sum(1 for k in keys.values() if k["used"])
        unused_keys = total_keys - used_keys

        keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_panel")]]

        await query.edit_message_text(
            f"""
📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦

👥 Total Users: {total_users}
🔑 Total Keys: {total_keys}
✅ Used Keys: {used_keys}
📭 Unused Keys: {unused_keys}
⏳ Cooldown: 3 Minutes
📄 Max Generate: {MAX_GENERATE} Lines
🔒 System: 1 Key = 1 User
            """, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ==============================================
    # 📜 ADMIN VIEW LOGS
    # ==============================================
    if data == "admin_logs":
        if user.id != ADMIN_ID:  # ✅ MAY INDENT
            await query.answer("❌ ADMIN ONLY!", show_alert=True)
            return
    
        log_file = os.path.join(FOLDERS["LOGS"], "bot_logs.txt")
        if not os.path.exists(log_file):
            keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_panel")]]
            await query.edit_message_text("📜 No logs found yet!", reply_markup=InlineKeyboardMarkup(keyboard))
            return
    
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
            content = "📜 𝗥𝗘𝗖𝗘𝗡𝗧 𝗔𝗖𝗧𝗜𝗩𝗜𝗧𝗬 𝗟𝗢𝗚𝗦\n\n"
            content += "".join(lines[-30:]) if len(lines) > 30 else "".join(lines)
            keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_panel")]]
            await query.edit_message_text(content[:4000], reply_markup=InlineKeyboardMarkup(keyboard))


    # ==============================================
    # 🔎 SEARCH USER SYSTEM (ADMIN)
    # ==============================================
    if data == "search_user":
        if user.id != ADMIN_ID:
            await query.answer("❌ Admin only!", show_alert=True)
            return

        await query.message.edit_text(
            "🔎 <b>SEARCH USER</b>\n\n"
            "Paano maghanap:\n"
            "Gamitin ang command na:\n"
            "/search <id> o /search <pangalan> o /search <username>\n\n"
            "Halimbawa:\n"
            "/search 123456789\n"
            "/search Juan Dela Cruz\n"
            "/search juandelacruz\n",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 BUMALIK", callback_data="admin_panel")]
            ])
        )
        return

        


# ==============================================
# 🛠️ ADMIN COMMANDS
# ==============================================
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove user access and permanently disable key"""
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("""
🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗨𝗦𝗘𝗥 𝗔𝗖𝗖𝗘𝗦𝗦

📝 Command: /remove <user_id>
Example: /remove 123456789

⚠️ This will permanently remove the user!
        """)
        return

    target_uid = context.args[0]
    users = load_json(FILES["USERS"])
    keys = load_json(FILES["KEYS"])

    if target_uid not in users:
        await update.message.reply_text("❌ User not found!")
        return

    # Get key info
    user_key = users[target_uid]["key_used"]

    # 🔒 PERMANENTLY DISABLE KEY
    if user_key in keys:
        keys[user_key]["used"] = True
        keys[user_key]["status"] = "dead"  # ✅ IMPORTANT
        keys[user_key]["user_id"] = "DELETED"
        keys[user_key]["used_at"] = datetime.now().isoformat()

    # 🗑️ DELETE USER
    del users[target_uid]

    # Save
    save_json(FILES["USERS"], users)
    save_json(FILES["KEYS"], keys)

    # Log
    add_log("USER_REMOVED", target_uid, f"Removed by admin | Key: {user_key}")

    await update.message.reply_text(f"""
✅ 𝗨𝗦𝗘𝗥 𝗥𝗘𝗠𝗢𝗩𝗘𝗗!

🆔 ID: `{target_uid}`
🔑 Key: `{user_key}`
📌 Status: PERMANENTLY DELETED

🔒 Key is now permanently disabled!
❌ This key can no longer be used.
        """)
async def remove_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove ALL users and free all keys"""
    if update.effective_user.id != ADMIN_ID:
        return

    users = load_json(FILES["USERS"])
    keys = load_json(FILES["KEYS"])

    if not users:
        await update.message.reply_text("✅ No users to remove!")
        return

    count = len(users)

    # Free all keys
    for key_data in keys.values():
        key_data["status"] = "dead"
        key_data["used"] = True
        key_data["user_id"] = "DELETED"
        key_data["used_at"] = datetime.now().isoformat()

    # Delete all users
    users.clear()

    # Save
    save_json(FILES["USERS"], users)
    save_json(FILES["KEYS"], keys)
    
    add_log("REMOVE_ALL", "ALL", f"Removed all {count} users!")

    await update.message.reply_text(f"""
🗑️ 𝗔𝗟𝗟 𝗨𝗦𝗘𝗥𝗦 𝗥𝗘𝗠𝗢𝗩𝗘𝗗!

👥 Total Removed: {count} users
🔑 All keys are now reusable.
📂 users.json is now empty!
        """)
        

# ==============================================
# 📢 BROADCAST COMMAND (ADMIN ONLY)
# ==============================================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # CHECK KUNG ADMIN
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    # KUNIN YUNG MESSAGE
    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast <message>")
        return
    
    message_text = ' '.join(context.args)
    
    # LOAD LAHAT NG USERS
    users = load_json(FILES["USERS"])
    
    # COUNTER
    sent_count = 0
    fail_count = 0
    
    await update.message.reply_text(f"📢 Starting broadcast...\nTotal users: {len(users)}")
    
    # LOOP SA LAHAT NG USER
    for uid, user_data in users.items():
        try:
            # SEND MESSAGE
            await context.bot.send_message(
                chat_id=int(uid),
                text=message_text
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
            fail_count += 1
    
    # REPORT RESULT
    await update.message.reply_text(f"""
✅ Broadcast Complete!

📊 Result:
• Total Users: {len(users)}
• Successfully Sent: {sent_count}
• Failed/Skipped: {fail_count}
""")


async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔎 MAGHANAP NG USER - TUMATALAKAY SA ID, USERNAME, O PANGALAN LANG"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Para sa Admin lamang!")
        return

    # KUNG WALANG NILAGAY NA HINAHANAP
    if not context.args:
        await update.message.reply_text("""
🔎 <b>SEARCH USER SYSTEM</b>

❌ Kailangan mong ilagay ang hinahanap!

✅ Gamitin:
<code>/search [ID / USERNAME / PANGALAN]</code>

📌 Halimbawa:
<code>/search 7520906627</code>
<code>/search @ShibTokyo</code>
<code>/search Shib</code>

📌 Ilalabas lang kung MAY TUGMA SA HINANAP!
""", parse_mode="HTML")
        return

    # KUNIN ANG HINAHANAP (tanggalin ang @ kung meron)
    keyword = " ".join(context.args).lower().replace("@", "")
    users = load_json(FILES["USERS"])
    
    # 🔄 AUTO UPDATE USERNAMES
    updated = False

    for uid, info in users.items():
        try:
            chat = await context.bot.get_chat(int(uid))

            new_username = chat.username or "No Username"
            new_name = chat.first_name or "No Name"

            # update kapag nagbago
            if info.get("username") != new_username:
                info["username"] = new_username
                updated = True

            if info.get("fullname") != new_name:
                info["fullname"] = new_name
                updated = True

        except:
            pass

    # save kapag may nabago
    if updated:
        save_json(FILES["USERS"], users)

    found = None
    found_uid = None

    # 🔍 HANAPIN SA LAHAT NG USERS
    for uid, info in users.items():
        # I-check kung tugma sa ID, Username, o Pangalan
        if (
            keyword == uid.lower()
            or keyword in info.get("username", "").lower()
            or keyword in info.get("fullname", "").lower()
        ):
            found = info
            found_uid = uid
            break  # ✅ Huminto agad kapag nahanap na (isa lang ilalabas)

    # ❌ KUNG WALANG MAHANAP
    if not found:
        await update.message.reply_text(f"""
❌ <b>WALANG MAHANAP!</b>

🔎 Hinanap mo: <code>{keyword}</code>
❌ Wala sa listahan o hindi nag-redeem ng key.
""", parse_mode="HTML")
        return

    # ✅ KUNG MAY MAHANAP - IPAKITA ANG DETALYE
    try:
        joined = datetime.fromisoformat(found["joined_at"]).strftime("%d-%m-%Y")
    except:
        joined = "Hindi alam"

    # 🔘 ALAMIN KUNG MAY ACCESS O WALA
    if found.get('active', False):
        status = "✅ <b>STATUS: MAY ACCESS SA BOT</b> 🟢"
    else:
        status = "❌ <b>STATUS: WALANG ACCESS SA BOT</b> 🔴"

    # 📤 IPADALA ANG RESULTA
    text = f"""
🔎 <b>RESULTA NG PAGHANAP</b>
━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>USER ID:</b> <code>{found_uid}</code>
👤 <b>PANGALAN:</b> {found.get('fullname', 'Walang Pangalan')}
🏷️ <b>USERNAME:</b> @{found.get('username', 'Walang Username')}
🔑 <b>KEY GAMIT:</b> <code>{found.get('key_used', 'Wala')}</code>
🌐 <b>IP ADDRESS:</b> <code>{found.get('locked_ip', 'Hindi alam')}</code>
📅 <b>SUMALI NOONG:</b> {joined}

{status}
━━━━━━━━━━━━━━━━━━━━━━
"""
    await update.message.reply_text(text, parse_mode="HTML")



# ==============================================
# 🚀 MAIN BOT RUNNER (REQUIRED)
# ==============================================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("removeall", remove_all_users))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("search", search_user)) 


    # Buttons (FIXED)
    application.add_handler(CallbackQueryHandler(button_handler, pattern=".*"))

    print("🤖 BOT IS RUNNING...")
    application.run_polling()

if __name__ == "__main__":
    keep_alive()
    main()