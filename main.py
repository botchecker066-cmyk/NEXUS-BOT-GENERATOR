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
from supabase import create_client, Client

# ==============================================
# 🗄️ SUPABASE DATABASE CONFIGURATION
# ==============================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN") # Siguraduhing may BOT_TOKEN ka sa Render

if not SUPABASE_URL or not SUPABASE_KEY or not BOT_TOKEN:
    raise ValueError("Kulangan ng Environment Variables sa Render (SUPABASE_URL, SUPABASE_KEY, o BOT_TOKEN)!")

# Initalize ang Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# System configuration
BASE_DIR = os.getcwd()
SALPAK_DIR = os.path.join(BASE_DIR, "salpak")
os.makedirs(SALPAK_DIR, exist_ok=True)

# Folders para sa logs at tools
FOLDERS = {
    "TOOLS": os.path.join(BASE_DIR, "tools"),
    "LOGS": os.path.join(BASE_DIR, "logs")
}
for folder in FOLDERS.values():
    os.makedirs(folder, exist_ok=True)

ADMIN_ID = 7201369115  # Palitan mo ito ng iyong Admin ID kung iba
BOT_NAME = "NEXUS VIP BOT GENERATOR"
VERSION = "2.0"
MAX_GENERATE = 100
COOLDOWN_TIME = 600
COOLDOWN = {}

# ===== FLASK KEEP-ALIVE WEBSERVER =====
app_web = Flask(__name__)
@app_web.route("/")
def home(): return "Nexus Bot System is Active!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app_web.run(host="0.0.0.0", port=port)).start()

# ==============================================
# 📝 UTILITY HANDLERS
# ==============================================
def get_real_ip():
    """Kukuha ng public IP para sa security locking"""
    try: return requests.get("https://api.ipify.org").text
    except: return "Unknown"

def add_log(action, user_id, details=""):
    log_file = os.path.join(FOLDERS["LOGS"], "bot_logs.txt")
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] | ID: {user_id} | ACTION: {action} | DETAILS: {details}\n")
    except: pass

def generate_key_string():
    chars = string.ascii_uppercase + string.digits
    while True:
        new_key = f"XINNN-{''.join(random.choice(chars) for _ in range(24))}"
        check = supabase.table("keys").select("key_string").eq("key_string", new_key).execute()
        if not check.data: return new_key

def get_available_games():
    try:
        files = [f for f in os.listdir(SALPAK_DIR) if f.endswith(".txt")]
        return {f.replace(".txt", "").upper(): os.path.join(SALPAK_DIR, f) for f in files}
    except: return {}

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

# ==============================================
# 🔑 REDEEM COMMAND (SUPABASE VERSION)
# ==============================================
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
        supabase.table("keys").update({
            "status": "used",
            "user_id": uid,
            "used_at": now_iso
        }).eq("key_string", key).execute()

        supabase.table("users").insert({
            "user_id": uid,
            "active": True,
            "key_used": key,
            "joined_at": now_iso,
            "device_id": str(update.effective_chat.id),
            "locked_ip": user_ip,
            "last_ip": user_ip,
            "banned": False,
            "fullname": str(user_name),
            "username": str(user_tag)
        }).execute()

        add_log("KEY_REDEEMED", uid, f"Key: {key}")
        await update.message.reply_text(f"✅ <b>ACCESS GRANTED!</b>\n🎉 Welcome {user_name}!\n🔓 All features are unlocked.\n🔑 Key: <code>{key}</code>\n🔒 Status: LOCKED TO YOUR ID", parse_mode="HTML")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Transaction failed: {str(e)}")

# ==============================================
# 📊 STATUS COMMAND & BUTTON FUNCTION
# ==============================================
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE, is_button=False):
    if is_button:
        query = update.callback_query
        user = query.from_user
        message_func = query.message.edit_text
    else:
        user = update.effective_user
        message_func = update.message.reply_text

    uid = str(user.id)
    has_access, status_msg = check_access(uid)

    keyboard = [[InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="back_main")]]

    if not has_access:
        text = f"❌ <b>NO ACTIVE ACCESS</b>\n\n{status_msg}\n🔓 Use /redeem &lt;key&gt; to activate"
        await message_func(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    user_data = supabase.table("users").select("*").eq("user_id", uid).execute().data[0]
    try: joined = datetime.fromisoformat(user_data["joined_at"]).strftime("%d-%m-%Y %H:%M")
    except: joined = user_data["joined_at"]

    text = f"👤 <b>MY ACCOUNT INFO</b>\n\n• 📛 Name: {user.first_name}\n• 🆔 ID: <code>{uid}</code>\n• ✅ Status: {status_msg}\n• 🔑 Key Used: <code>{user_data['key_used']}</code>\n• 📅 Joined: {joined}\n• ⏳ Cooldown: 10 minutes\n• 📄 Max Generate: {MAX_GENERATE} Lines\n\n🔒 Your access is secured and lifetime!"
    await message_func(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_status(update, context, is_button=False)

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

    msg = f"╔══════════════════════════════════╗\n║        🤖 {BOT_NAME}        ║\n║            🔖 VERSION {VERSION}           ║\n╚══════════════════════════════════╝\n\n{status_msg}\n👇 Pumili ng opsyon sa ibaba:"
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ==============================================
# 🔘 BUTTON HANDLER
# ==============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)
    data = query.data
    
    if data == "redeem_help":
        text = "🔑 <b>HOW TO REDEEM A KEY</b>\n\nSend command:\n<code>/redeem YOUR_KEY</code>\n\n📌 Important Rules:\n• 1 Key = 1 User only\n• Key is locked to your Telegram ID"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]), parse_mode="HTML")
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

        msg = f"╔══════════════════════════════════╗\n║        🤖 {BOT_NAME}        ║\n║            🔖 VERSION {VERSION}           ║\n╚══════════════════════════════════╝\n\n{status_msg}\n👇 Choose option below:"
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("gen_"):
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

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
                all_lines = [line.strip() for line in f if line.strip()]
            unique_accounts = list(dict.fromkeys(all_lines))
            if not unique_accounts:
                await query.message.reply_text("❌ NO MORE UNIQUE ACCOUNTS AVAILABLE!")
                return

            accounts = unique_accounts[:MAX_GENERATE]
            remaining = unique_accounts[MAX_GENERATE:]

            with open(file_path, "w", encoding="utf-8") as f: f.write("\n".join(remaining))
            temp_file = os.path.join(BASE_DIR, f"{game_name}_ACCOUNTS.txt")
            with open(temp_file, "w", encoding="utf-8") as f: f.write("\n".join(accounts))

            await query.message.reply_document(
                document=open(temp_file, "rb"), filename=f"{game_name}_ACCOUNTS.txt",
                caption=f"✅ <b>GENERATED!</b>\n🎮 ITEM: {game_name}\n🔢 GIVEN: {len(accounts)}\n📊 REMAINING: {len(remaining)}"
            )
            os.remove(temp_file)
            COOLDOWN[uid] = time.time()
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")
        return

    if data == "menu_generate":
        has_access, _ = check_access(uid)
        if not has_access:
            await query.answer("❌ No access!", show_alert=True)
            return

        games = get_available_games()
        if not games:
            await query.edit_message_text("❌ No stock found in 'salpak' folder!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_main")]]))
            return

        text = "🎮 <b>AVAILABLE STOCK</b>\n"
        keyboard = []
        for g_name, f_path in games.items():
            try:
                with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f if line.strip()]
                count = len(lines)
                status_lbl = "🟢 FULL" if count > 50 else "🟡 LOW" if count > 0 else "⚫ OOS"
                text += f"\n• {g_name} | Stock: {count} [{status_lbl}]"
                keyboard.append([InlineKeyboardButton(f"🎮 {g_name} [{count}]", callback_data=f"gen_{g_name}")])
            except: pass
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if data == "menu_status":
        await show_status(update, context, is_button=True)
        return

    if data == "menu_tools":
        has_access, _ = check_access(uid)
        if not has_access: return
        try: tools = [f for f in os.listdir(FOLDERS["TOOLS"]) if os.path.isfile(os.path.join(FOLDERS["TOOLS"], f))]
        except: tools = []
        keyboard = [[InlineKeyboardButton(f"📥 {t}", callback_data=f"dl_{t}")] for t in tools]
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="back_main")])
        await query.edit_message_text("⚙️ <b>TOOLS MENU</b>", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("dl_"):
        filename = data.replace("dl_", "")
        file_path = os.path.join(FOLDERS["TOOLS"], filename)
        if os.path.exists(file_path):
            await query.message.reply_document(document=open(file_path, "rb"), filename=filename, caption=f"✅ Downloaded: {filename}")
        return

    # Admin actions (Fixed fully to Supabase)
    if data == "admin_panel":
        if user.id != ADMIN_ID: return
        keyboard = [
            [InlineKeyboardButton("🔑 GENERATE KEY", callback_data="admin_genkey")],
            [InlineKeyboardButton("👥 VIEW ALL USERS", callback_data="admin_users_1")],
            [InlineKeyboardButton("🔎 SEARCH USER", callback_data="search_user_btn")],
            [InlineKeyboardButton("🗑️ REMOVE USER", callback_data="admin_remove")],
            [InlineKeyboardButton("📊 BOT STATS", callback_data="admin_stats")],
            [InlineKeyboardButton("📜 VIEW LOGS", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 MAIN MENU", callback_data="back_main")]
        ]
        await query.edit_message_text("🔐 <b>ADMIN CONTROL DASHBOARD</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return

    if data == "admin_genkey":
        if user.id != ADMIN_ID: return
        new_key = generate_key_string()
        supabase.table("keys").insert({"key_string": new_key, "status": "unused", "user_id": None, "created_at": datetime.now().isoformat()}).execute()
        await query.edit_message_text(f"✅ <b>KEY GENERATED!</b>\n\n🔑 Key: <code>{new_key}</code>\n⏳ LIFETIME PREMIUM", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="HTML")
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
        curr_page_users = user_list[start_idx:start_idx+limit]

        text = f"👥 <b>ALL USERS LIST</b> ({total_users}) | Page {page}/{total_pages}\n"
        for u in curr_page_users:
            text += f"\n🆔 <code>{u['user_id']}</code>\n👤 {u['fullname']}\n🔑 <code>{u['key_used']}</code>\n ────────────────"
        nav_buttons = []
        if page > 1: nav_buttons.append(InlineKeyboardButton("⬅️ PREV", callback_data=f"admin_users_{page-1}"))
        if page < total_pages: nav_buttons.append(InlineKeyboardButton("NEXT ➡️", callback_data=f"admin_users_{page+1}"))
        kbd = [nav_buttons] if nav_buttons else []
        kbd.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kbd), parse_mode="HTML")
        return

    if data == "admin_remove":
        if user.id != ADMIN_ID: return
        await query.edit_message_text("🗑️ <b>REMOVE USER</b>\n\nUse command:\n<code>/remove &lt;user_id&gt;</code>\n<code>/removeall</code>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="HTML")
        return

    if data == "admin_stats":
        if user.id != ADMIN_ID: return
        tot_users = len(supabase.table("users").select("user_id").execute().data)
        all_keys = supabase.table("keys").select("status").execute().data
        tot_keys = len(all_keys)
        used_k = sum(1 for k in all_keys if k["status"] == "used")
        text = f"📊 <b>BOT STATISTICS</b>\n\n👥 Users: {tot_users}\n🔑 Total Keys: {tot_keys}\n✅ Used: {used_k}\n📭 Unused: {tot_keys - used_k}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="HTML")
        return

    if data == "admin_logs":
        if user.id != ADMIN_ID: return
        log_file = os.path.join(FOLDERS["LOGS"], "bot_logs.txt")
        if not os.path.exists(log_file):
            await query.edit_message_text("📜 No logs found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
            return
        with open(log_file, "r", encoding="utf-8") as f: lines = f.readlines()
        await query.edit_message_text(("📜 <b>LOGS ENGINE</b>\n\n" + "".join(lines[-20:]))[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]), parse_mode="HTML")
        return

    if data == "search_user_btn":
        if user.id != ADMIN_ID: return
        await query.message.edit_text("🔎 <b>SEARCH USER</b>\n\nUse command:\n<code>/search [ID / Username / Name]</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]]))
        return

# ==============================================
# 🛠️ ADMIN COMMANDS
# ==============================================
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: /remove &lt;user_id&gt;")
        return
    target_uid = str(context.args[0])
    check = supabase.table("users").select("key_used").eq("user_id", target_uid).execute()
    if not check.data:
        await update.message.reply_text("❌ User not found.")
        return
    user_key = check.data[0]["key_used"]
    supabase.table("keys").update({"status": "dead", "user_id": "DELETED"}).eq("key_string", user_key).execute()
    supabase.table("users").delete().eq("user_id", target_uid).execute()
    add_log("USER_REMOVED", target_uid, f"Key disabled: {user_key}")
    await update.message.reply_text(f"✅ User {target_uid} removed and key {user_key} permanently killed.")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: /remove <user_id>")
        return
    target_uid = str(context.args[0])
    check = supabase.table("users").select("key_used").eq("user_id", target_uid).execute()
    if not check.data:
        await update.message.reply_text("❌ User not found.")
        return
    user_key = check.data[0]["key_used"]
    supabase.table("keys").update({"status": "dead", "user_id": "DELETED"}).eq("key_string", user_key).execute()
    supabase.table("users").delete().eq("user_id", target_uid).execute()
    add_log("USER_REMOVED", target_uid, f"Key disabled: {user_key}")
    await update.message.reply_text(f"✅ User {target_uid} removed and key {user_key} permanently killed.")

async def remove_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    supabase.table("keys").update({"status": "dead", "user_id": "DELETED"}).execute()
    supabase.table("users").delete().neq("user_id", "0").execute()
    add_log("REMOVE_ALL", "ALL", "Database reset.")
    await update.message.reply_text("🗑️ Database wiped successfully!")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast <msg>")
        return
    msg_text = ' '.join(context.args)
    users = supabase.table("users").select("user_id").execute().data
    await update.message.reply_text(f"📢 Sending broadcast to {len(users)} users...")
    s, f = 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=int(u["user_id"]), text=msg_text)
            s += 1
        except: f += 1
    await update.message.reply_text(f"📢 Broadcast finished.\n🟢 Success: {s}\n🔴 Failed: {f}")

async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Syntax: /search [ID/Username/Name]")
        return
    keyword = " ".join(context.args).lower().replace("@", "")
    res = supabase.table("users").select("*").execute().data
    found = None
    for u in res:
        if keyword == u["user_id"] or keyword in u.get("username", "").lower() or keyword in u.get("fullname", "").lower():
            found = u
            break
    if not found:
        await update.message.reply_text("❌ Walang nahanap.")
        return
    status_str = "🟢 ACTIVE" if found["active"] else "🔴 INACTIVE"
    text = f"🔎 <b>SEARCH RESULT</b>\n━━━━━━━━━\n🆔 ID: <code>{found['user_id']}</code>\n👤 Name: {found['fullname']}\n🔑 Key: <code>{found['key_used']}</code>\n⚡ Status: {status_str}"
    await update.message.reply_text(text, parse_mode="HTML")

# ==============================================
# 🚀 SYSTEM STARTER
# ==============================================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers para sa mga Admin at User Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("removeall", remove_all_users))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("search", search_user))
    
    # Handler para sa Inline Buttons
    application.add_handler(CallbackQueryHandler(button_handler, pattern=".*"))
    
    print("🤖 BOT IS DEPLOYED & ARMED SUCCESSFULLY.")
    application.run_polling()

if __name__ == "__main__":
    keep_alive()
    main()
