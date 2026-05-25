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
import random
import string
import time
import requests
from datetime import datetime
from flask import Flask
from threading import Thread
from supabase import create_client, Client  # Fully Integrated

# ==============================================
# 🗄️ SUPABASE DATABASE CONFIGURATION
# ==============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Wala pang SUPABASE_URL o SUPABASE_KEY sa Environment Variables!")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tanggalin na ang local users/keys JSON setup. 
# Tanging ang para sa 'salpak' (stock files) at logs ang ititira.
BASE_DIR = os.getcwd()
FOLDERS = {
    "SALPAK": os.path.join(BASE_DIR, "salpak"),
    "TOOLS": os.path.join(BASE_DIR, "tools"),
    "LOGS": os.path.join(BASE_DIR, "logs")
}
for folder in FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

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
# ⚙️ CONFIGURATION
# ==============================================
BOT_TOKEN = "8521492677:AAFrP9mGWZzehoPs6cNxfyHm5AIy3X8bFWE"
ADMIN_ID = 6538213760
BOT_NAME = "NEXUS VIP BOT GENERATOR"
VERSION = "2.0"

COOLDOWN_TIME = 600  
MAX_GENERATE = 100   
COOLDOWN = {}

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

def get_real_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Unknown"

# ==============================================
# 📝 SUPABASE DATABASE HANDLERS
# ==============================================
def check_access(user_id):
    """Suriin sa Supabase kung active ang user"""
    try:
        response = supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
        if not response.data:
            return False, "🔑 No active key"
        
        user_data = response.data[0]
        if user_data.get("banned", False):
            return False, "🚫 Account Banned!"
        if not user_data.get("active", False):
            return False, "🚫 Access deactivated"
            
        return True, "✅ Access Active"
    except Exception as e:
        print(f"[DB ERROR] check_access: {e}")
        return False, "❌ Database Error"

def generate_key_string():
    chars = string.ascii_uppercase + string.digits
    while True:
        random_part = ''.join(random.choice(chars) for _ in range(24))
        new_key = f"XINNN-{random_part}"
        
        # Siguraduhing walang duplicate sa Supabase bago ibigay
        check = supabase.table("keys").select("key_string").eq("key_string", new_key).execute()
        if not check.data:
            return new_key

def get_available_games():
    try:
        files = [f for f in os.listdir(FOLDERS["SALPAK"]) if f.endswith(".txt")]
        return {f.replace(".txt", "").upper(): os.path.join(FOLDERS["SALPAK"], f) for f in files}
    except:
        return {}

# ==============================================
# 📨 USER COMMANDS
# ==============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
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
        msg = f"╔══════════════════════════════════╗\n║        🤖 {BOT_NAME}        ║\n║            🔖 VERSION {VERSION}           ║\n╚══════════════════════════════════╝\n\n{status_msg}\n🎉 Welcome {user.first_name}!\n\n👇 Choose option below:"
    else:
        msg = f"╔══════════════════════════════════╗\n║        🤖 {BOT_NAME}        ║\n║            🔖 VERSION {VERSION}           ║\n╚══════════════════════════════════╝\n\n{status_msg}\n🔑 Need valid key to unlock all features!\n\n💡 How to activate:\nType: /redeem <your_key>\nExample: /redeem XINNN-ABC123XYZ"

    await update.effective_message.reply_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True
    )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /redeem <key>")
        return

    key = context.args[0].upper()
    uid = str(update.effective_user.id)

    user_check = supabase.table("users").select("*").eq("user_id", uid).execute()
    if user_check.data:
        await update.message.reply_text("❌ You already have an active key!")
        return

    key_check = supabase.table("keys").select("*").eq("key_string", key).execute()
    if not key_check.data:
        await update.message.reply_text("❌ Invalid Key!")
        return
        
    key_data = key_check.data[0]
    if key_data.get("status") != "unused":
        await update.message.reply_text("❌ 𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗢𝗥 𝗘𝗫𝗣𝗜𝗥𝗘𝗗 𝗞𝗘𝗬!")
        return

    user_ip = get_real_ip()
    user_name = update.effective_user.first_name or "No Name"
    user_tag = update.effective_user.username or "No Username"
    now_iso = datetime.now().isoformat()

    try:
        supabase.table("keys").update({"status": "used", "user_id": uid, "used_at": now_iso}).eq("key_string", key).execute()
        supabase.table("users").insert({
            "user_id": uid, "active": True, "key_used": key, "joined_at": now_iso,
            "device_id": str(update.effective_chat.id), "locked_ip": user_ip, "last_ip": user_ip,
            "banned": False, "fullname": str(user_name), "username": str(user_tag)
        }).execute()

        add_log("KEY_REDEEMED", uid, f"Name: {user_name} | Key: {key}")
        await update.message.reply_text(f"✅ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗚𝗥𝗔𝗡𝗧𝗘𝗗!\n🎉 Welcome {user_name}!\n🔑 Key: `{key}`\n🔒 LOCKED TO YOUR ID")
    except Exception as e:
        await update.message.reply_text(f"❌ Transaction failed: {str(e)}")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE, is_button=False):
    query = update.callback_query if is_button else None
    user = query.from_user if is_button else update.effective_user
    message_func = query.message.reply_text if not is_button else query.message.edit_text

    uid = str(user.id)
    has_access, status_msg = check_access(uid)

    keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="back_main")]]

    if not has_access:
        await message_func(f"❌ 𝗡𝗢 𝗔𝗖𝗧𝗜𝗩𝗘 𝗔𝗖𝗧𝗜𝗩𝗜𝗧𝗬\n\n{status_msg}\n🔓 Use /redeem <key>", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    res = supabase.table("users").select("*").eq("user_id", uid).execute()
    user_data = res.data[0]
    joined = datetime.fromisoformat(user_data["joined_at"]).strftime("%d-%m-%Y %H:%M")

    text = f"👤 𝗠𝗬 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗜𝗡𝗙𝗢\n\n• 📛 Name: {user.first_name}\n• 🆔 ID: `{uid}`\n• ✅ Status: {status_msg}\n• 🔑 Key Used: `{user_data['key_used']}`\n• 📅 Joined: {joined}\n• ⏳ Cooldown: 10 minutes\n• 📄 Max Generate: {MAX_GENERATE} Lines"
    
    await message_func(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update, context, is_button=False)

# ==============================================
# 🔘 BUTTON & PROCESS HANDLER
# ==============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)
    data = query.data

    if data == "redeem_help":
        text = "🔑 𝗛𝗢𝗪 𝗧𝗢 𝗥𝗘𝗗𝗘𝗘𝗠\n\nSend command:\n`/redeem YOUR_KEY`\n\n📌 1 Key = 1 User only."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]), parse_mode="Markdown")
        return

    if data == "back_main":
        has_access, status_msg = check_access(uid)
        keyboard = []
        if has_access:
            keyboard.append([InlineKeyboardButton("🎮 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘", callback_data="menu_generate")])
            keyboard.append([InlineKeyboardButton("ℹ️ 𝗠𝗬 𝗦𝗧𝗔𝗧𝗨𝗦", callback_data="menu_status")])
            keyboard.append([InlineKeyboardButton("📥 𝗧𝗢𝗢𝗟𝗦", callback_data="menu_tools")])
        keyboard.append([InlineKeyboardButton("🔑 𝗥𝗘𝗗𝗘𝗘𝗠 𝗛𝗘𝗟𝗣", callback_data="redeem_help")])
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("🔐 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", callback_data="admin_panel")])

        msg = f"╔══════════════════════════════════╗\n║        🤖 {BOT_NAME}        ║\n║            🔖 VERSION {VERSION}           ║\n╚══════════════════════════════════╝\n\n{status_msg}\n👇 Choose option:"
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("gen_"):
        has_access, _ = check_access(uid)
        if not has_access: return

        now = time.time()
        if uid in COOLDOWN and now - COOLDOWN[uid] < COOLDOWN_TIME:
            rem = int(COOLDOWN_TIME - (now - COOLDOWN[uid]))
            await query.answer(f"⏳ Wait {rem//60}m {rem%60}s!", show_alert=True)
            return

        game_name = data.replace("gen_", "").upper()
        games = get_available_games()
        file_path = games.get(game_name)

        if not file_path or not os.path.exists(file_path):
            await query.answer("❌ File not found!", show_alert=True)
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = [l.strip() for l in f if l.strip()]
            unique_accounts = list(dict.fromkeys(all_lines))
            if not unique_accounts:
                await query.message.reply_text("❌ NO STOCK AVAILABLE!")
                return

            accounts = unique_accounts[:MAX_GENERATE]
            remaining = unique_accounts[MAX_GENERATE:]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(remaining))

            temp_file = os.path.join(BASE_DIR, f"{game_name}_ACCOUNTS.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write("\n".join(accounts))

            await query.message.reply_document(
                document=open(temp_file, "rb"), filename=f"{game_name}_ACCOUNTS.txt",
                caption=f"✅ 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘block!\n🎮 ITEM: {game_name}\n🔢 GIVEN: {len(accounts)}\n📊 REMAINING: {len(remaining)}"
            )
            os.remove(temp_file)
            COOLDOWN[uid] = time.time()
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")
        return

    if data == "menu_generate":
        has_access, _ = check_access(uid)
        if not has_access: return
        games = get_available_games()
        if not games:
            await query.edit_message_text("❌ No stock tools inside 'salpak' folder!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]))
            return

        text = "🎮 𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘 𝗦𝗧𝗢𝗖𝗞\n"
        keyboard = []
        for g_name, f_path in games.items():
            try:
                with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
                count = len(lines)
                status = "🟢 FULL" if count > 50 else "🟡 LOW" if count > 0 else "⚫ OOS"
                text += f"\n• 🎮 {g_name} | Stock: {count} [{status}]"
                keyboard.append([InlineKeyboardButton(f"🎮 {g_name} [{count}]", callback_data=f"gen_{g_name}")])
            except:
                pass
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "menu_status":
        await show_status(update, context, is_button=True)
        return

    if data == "menu_tools":
        has_access, _ = check_access(uid)
        if not has_access: return
        try:
            tools = [f for f in os.listdir(FOLDERS["TOOLS"]) if os.path.isfile(os.path.join(FOLDERS["TOOLS"], f))]
        except: tools = []

        keyboard = []
        for t in tools: keyboard.append([InlineKeyboardButton(f"📥 {t}", callback_data=f"dl_{t}")])
        keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="back_main")])
        await query.edit_message_text("⚙️ 𝗧𝗢𝗢𝗟𝗦 𝗠𝗘𝗡𝗨\n\nSelect file below:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("dl_"):
        filename = data.replace("dl_", "")
        file_path = os.path.join(FOLDERS["TOOLS"], filename)
        if os.path.exists(file_path):
            await query.message.reply_document(document=open(file_path, "rb"), filename=filename, caption=f"✅ Downloaded: {filename}")
        return

    # ==============================================
    # 🔐 ADMIN INTERACTIVE MENUS (SUPABASE POWERED)
    # ==============================================
    if data == "admin_panel":
        if user.id != ADMIN_ID: return
        keyboard = [
            [InlineKeyboardButton("🔑 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘 𝗞𝗘𝗬", callback_data="admin_genkey")],
            [InlineKeyboardButton("👥 𝗩𝗜𝗘𝗪 𝗔𝗟🇱 𝗨𝗦𝗘𝗥𝗦", callback_data="admin_users_1")],
            [InlineKeyboardButton("🔎 𝗦𝗘𝗔𝗥𝗖𝗛 𝗨𝗦𝗘𝗥", callback_data="search_user")],
            [InlineKeyboardButton("🗑️ <b>REMOVE MENU</b>", callback_data="admin_remove")],
            [InlineKeyboardButton("📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗦", callback_data="admin_stats")],
            [InlineKeyboardButton("📜 𝗩𝗜𝗘𝗪 𝗟𝗢𝗚𝗦", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗠𝗔𝗜𝗡", callback_data="back_main")]
        ]
        await query.edit_message_text("🔐 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟\n\nSystem Control Center Ready.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if data == "admin_genkey":
        if user.id != ADMIN_ID: return
        new_key = generate_key_string()
        supabase.table("keys").insert({"key_string": new_key, "status": "unused", "user_id": None, "created_at": datetime.now().isoformat()}).execute()
        
        await query.edit_message_text(f"✅ 𝗞𝗘𝗬 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗!\n\n🔑 Key: `{new_key}`\n⏳ LIFETIME ACCESS", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="Markdown")
        return

    if data.startswith("admin_users_"):
        if user.id != ADMIN_ID: return
        page = int(data.split("_")[-1])
        res = supabase.table("users").select("*").execute()
        user_list = res.data
        total_users = len(user_list)
        
        limit = 5
        total_pages = (total_users + limit - 1) // limit if total_users > 0 else 1
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        curr_page_users = user_list[start_idx:end_idx]

        text = f"👥 𝗔𝗟𝗟 𝗨𝗦𝗘𝗥𝗦 (Total: {total_users}) | Page {page}/{total_pages}\n"
        for u in curr_page_users:
            text += f"\n🆔 `{u['user_id']}`\n👤 {u['fullname']} (@{u['username']})\n🔑 `{u['key_used']}`\n🌐 {u['locked_ip']}\n ────────────────"

        nav_buttons = []
        if page > 1: nav_buttons.append(InlineKeyboardButton("⬅️ PREV", callback_data=f"admin_users_{page-1}"))
        if page < total_pages: nav_buttons.append(InlineKeyboardButton("NEXT ➡️", callback_data=f"admin_users_{page+1}"))
        
        kbd = [nav_buttons] if nav_buttons else []
        kbd.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kbd), parse_mode="Markdown")
        return

    if data == "admin_remove":
        if user.id != ADMIN_ID: return
        await query.edit_message_text("🗑️ 𝗥𝗘𝗠𝗢𝗩𝗘 𝗨𝗦𝗘𝗥 𝗔𝗖𝗖𝗘𝗦\n\nCommand format:\n`/remove <user_id>`\n`/removeall` to wipe everyone.", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="Markdown")
        return

    if data == "admin_stats":
        if user.id != ADMIN_ID: return
        tot_users = len(supabase.table("users").select("user_id").execute().data)
        all_keys = supabase.table("keys").select("status").execute().data
        tot_keys = len(all_keys)
        used_k = sum(1 for k in all_keys if k["status"] == "used")
        
        text = f"📊 𝗕𝗢𝗧 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦\n\n👥 Total Active Users: {tot_users}\n🔑 Generated Keys: {tot_keys}\n✅ Activated Keys: {used_k}\n📭 Unused Keys: {tot_keys - used_k}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
        return

    if data == "admin_logs":
        if user.id != ADMIN_ID: return
        log_file = os.path.join(FOLDERS["LOGS"], "bot_logs.txt")
        if not os.path.exists(log_file):
            await query.edit_message_text("📜 No logs recorded yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
            return
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        content = "📜 𝗥𝗘𝗖𝗘𝗡𝗧 𝗔𝗖𝗧𝗜𝗩𝗜𝗧𝗬 𝗟𝗢𝗚𝗦\n\n" + "".join(lines[-25:])
        await query.edit_message_text(content[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
        return

    if data == "search_user":
        if user.id != ADMIN_ID: return
        await query.message.edit_text("🔎 <b>SEARCH USER SYSTEM</b>\n\nGamitin ang command:\n<code>/search [ID / Username / Pangalan]</code>", parse_mode="HTML",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
        return

# ==============================================
# 🛠️ ADMIN SYSTEM COMMANDS (SUPABASE REALTIME)
# ==============================================
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
        
    if not context.args:
        await update.message.reply_text("❌ Usage: `/remove <user_id>`", parse_mode="Markdown")
        return

    target_uid = str(context.args[0])
    
    try:
        # Siyasatin kung ang user ay nasa database ng Supabase
        check = supabase.table("users").select("key_used").eq("user_id", target_uid).execute()
        
        if not check.data:
            await update.message.reply_text("❌ Walang nahanap na user sa Supabase Database.")
            return

        user_key = check.data[0]["key_used"]
        
        # I-update ang status ng key sa 'dead' o 'deleted' sa database
        supabase.table("keys").update({"status": "dead", "user_id": "DELETED"}).eq("key_string", user_key).execute()
        
        # Burahin ang user sa 'users' table ng Supabase
        supabase.table("users").delete().eq("user_id", target_uid).execute()

        add_log("USER_REMOVED", target_uid, f"Wiped by Admin | Disabled key: {user_key}")
        await update.message.reply_text(f"✅ <b>USER REMOVED</b>\n\n🆔 ID: <code>{target_uid}</code>\n🔑 Ang key <code>{user_key}</code> ay permanenteng disabled na.", parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sa pag-remove: {str(e)}")

async def remove_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    
    try:
        # I-invalidate ang lahat ng keys at burahin ang lahat ng users sa Supabase
        supabase.table("keys").update({"status": "dead", "user_id": "DELETED"}).execute()
        supabase.table("users").delete().neq("user_id", "0").execute() # Binubura ang lahat ng laman
        
        add_log("REMOVE_ALL", "ALL", "Admin initiated database factory reset.")
        await update.message.reply_text("🗑️ <b>FACTORY WIPE COMPLETE</b>\n\nLahat ng users ay matagumpay na nabura at ang lahat ng keys ay ginawang 'dead'.", parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sa pag-wipe ng database: {str(e)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
        
    if not context.args:
        await update.message.reply_text("❌ Usage: `/broadcast <mensahe>`", parse_mode="Markdown")
        return
    
    msg_text = ' '.join(context.args)
    
    try:
        # Kunin ang lahat ng user IDs mula sa Supabase
        res = supabase.table("users").select("user_id").execute()
        users = res.data

        await update.message.reply_text(f"📢 Nagsisimula nang mag-broadcast sa {len(users)} na mga users...")
        s_count, f_count = 0, 0
        
        for u in users:
            try:
                await context.bot.send_message(chat_id=int(u["user_id"]), text=msg_text)
                s_count += 1
            except:
                f_count += 1
                
        await update.message.reply_text(f"📢 <b>Broadcast Finished</b>\n\n🟢 Tagumpay: {s_count}\n🔴 Sablay: {f_count}", parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sa pag-broadcast: {str(e)}")

async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
        
    if not context.args:
        await update.message.reply_text("❌ Syntax: `/search [ID/Username/Pangalan]`", parse_mode="Markdown")
        return

    keyword = " ".join(context.args).lower().replace("@", "")
    
    try:
        # Kumuha ng buong listahan ng users sa Supabase para i-filter
        res = supabase.table("users").select("*").execute()
        found_user = None
        
        for u in res.data:
            if (keyword == str(u["user_id"]) or 
                keyword in u.get("username", "").lower() or 
                keyword in u.get("fullname", "").lower()):
                found_user = u
                break

        if not found_user:
            await update.message.reply_text(f"❌ Walang natagpuang user para sa keyword: <code>{keyword}</code>", parse_mode="HTML")
            return

        # Ayusin ang re-formatting ng petsa
        try:
            joined = datetime.fromisoformat(found_user["joined_at"]).strftime("%d-%m-%Y %H:%M")
        except:
            joined = found_user["joined_at"]
            
        status_str = "🟢 ACTIVE ACCESS" if found_user.get("active", False) else "🔴 INACTIVE / REVOKED"
        if found_user.get("banned", False):
            status_str = "🚫 BANNED FROM BOT"
        
        text = f"""
🔎 <b>RESULTA NG PAGHANAP</b>
━━━━━━━━━━━━━━━━━━━━━━

🆔 <b>USER ID:</b> <code>{found_user['user_id']}</code>
👤 <b>PANGALAN:</b> {found_user.get('fullname', 'Walang Pangalan')}
🏷️ <b>USERNAME:</b> @{found_user.get('username', 'Walang Username')}
🔑 <b>KEY GAMIT:</b> <code>{found_user.get('key_used', 'Wala')}</code>
🌐 <b>IP ADDRESS:</b> <code>{found_user.get('locked_ip', 'Hindi alam')}</code>
📅 <b>SUMALI NOONG:</b> {joined}

⚡ <b>STATUS:</b> {status_str}
━━━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(text, parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sa paghahanap: {str(e)}")


# ==============================================
# 🚀 MAIN BOT RUNNER (REQUIRED)
# ==============================================
def main():
    # Siguraduhing ang BOT_TOKEN ay naka-set sa iyong Render Environment Variables
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Admin at User Commands Links
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("removeall", remove_all_users))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("search", search_user)) 

    # Menu Interactive Buttons (FIXED)
    application.add_handler(CallbackQueryHandler(button_handler, pattern=".*"))

    print("🤖 BOT STARTED - FULL SUPABASE INTEGRATION IS ACTIVE.")
    application.run_polling()

if __name__ == "__main__":
    keep_alive() # Patatakbuhin ang Flask Keep-Alive Background Thread
    main()       # Patatakbuhin ang Telegram Bot Polling Engine