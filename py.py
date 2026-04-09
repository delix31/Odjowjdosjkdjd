import telebot
import threading
import time
import socket
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.getLogger("telebot").setLevel(logging.CRITICAL)

TOKEN = "8108298669:AAHkUgOu5BtD-aqx6rkmHGCc9m5ZqdNUORc"
bot = telebot.TeleBot(TOKEN, threaded=True)

YETKILI_ID = 7181611360

KANALLAR = [-1002993493265,1003737129518,-1003762161757,]

ANAHTAR_KELIMELER = [
    "çalma", "sorgu", "panel", "klasör",
    "@klosorcu", "@crazysaplar", "@azedestekhat",
    "@tassaklireal", "instagram", "free",
    "kanal", "botlar", "ss", "bot", "kanallarda",
    "sxrgu", "𝙄𝙉𝙎𝙏𝘼𝙂𝙍𝘼𝙈","Hesab"
]

OZEL_SUPHELI_CUMLELER = [
    "herkese 5 hesap çalma hakkı verildi süresi dolmadan kullanın!",
    "herkese 3 hesap çalma hakkı verildi!",
    "hesap çalma hakkı verildi!",
    "hesap çalma hakkı verildi",
    "herkese 3 hesap çalma hakkı verildi",
    "herkese 5 hesap ç#lma hakkı verildi !",
    "herkesin 5 ücretsiz hesab ç@lma hakkı var",
    "Hesab Ç@lma Özelliği Aktif!"
]

silme_isleri = {}          # message_id: cancel_flag
album_cache = {}           # media_group_id: [message_ids]

def internet_var_mi():
    try:
        socket.create_connection(("api.telegram.org", 443), timeout=5)
        return True
    except:
        return False

def yetkiliye_bildir(text, reply_markup=None):
    try:
        bot.send_message(
            YETKILI_ID,
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except:
        pass

def gecikmeli_sil(chat_id, message_ids):
    for _ in range(15 * 60):
        if any(silme_isleri.get(mid) is False for mid in message_ids):
            return
        time.sleep(1)

    for mid in message_ids:
        try:
            bot.delete_message(chat_id, mid)
        except:
            pass

    yetkiliye_bildir(
        f"🗑️ **ŞÜPHELİ MESAJ(LAR) SİLİNDİ**\n\n"
        f"📌 Kanal ID: `{chat_id}`\n"
        f"🆔 Mesaj ID'ler: `{message_ids}`"
    )

def mesaj_kontrol(m):
    if m.chat.id not in KANALLAR:
        return

    icerik = ""

    if getattr(m, "text", None):
        icerik += m.text.lower()
    if getattr(m, "caption", None):
        icerik += m.caption.lower()
    if m.document and m.document.file_name:
        icerik += m.document.file_name.lower()

    is_forward = bool(m.forward_from or m.forward_from_chat or m.forward_date)

    supheli = False

    if is_forward and any(k in icerik for k in ANAHTAR_KELIMELER):
        supheli = True

    if not is_forward and any(c in icerik for c in OZEL_SUPHELI_CUMLELER):
        supheli = True

    if not supheli:
        return

    # ===== ALBUM KONTROL =====
    message_ids = [m.message_id]

    if m.media_group_id:
        album_cache.setdefault(m.media_group_id, []).append(m.message_id)
        message_ids = album_cache[m.media_group_id]

    for mid in message_ids:
        silme_isleri[mid] = True

    threading.Thread(
        target=gecikmeli_sil,
        args=(m.chat.id, message_ids.copy()),
        daemon=True
    ).start()

    link = f"https://t.me/c/{str(m.chat.id)[4:]}/{m.message_id}"

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "✅ Bu şüpheli bir mesaj değil",
            callback_data=f"iptal_{m.message_id}"
        )
    )

    yetkiliye_bildir(
        f"⚠️ **ŞÜPHELİ MESAJ TESPİT EDİLDİ (ALBUM DESTEKLİ)**\n\n"
        f"🔗 [Mesaja Git]({link})\n\n"
        f"⏳ 15 dk sonra silinecek",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("iptal_"))
def iptal_handler(call):
    if call.from_user.id != YETKILI_ID:
        bot.answer_callback_query(call.id, "❌ Yetkin yok")
        return

    msg_id = int(call.data.split("_")[1])
    silme_isleri[msg_id] = False

    bot.answer_callback_query(call.id, "✅ Silme işlemi iptal edildi")
    bot.edit_message_text(
        "🟢 **Admin onayı verildi**\n\nBu mesaj artık silinmeyecek.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

@bot.channel_post_handler(content_types=["text", "photo", "document", "video", "audio"])
def kanal_handler(m):
    mesaj_kontrol(m)

@bot.message_handler(func=lambda m: m.chat.type == "private")
def ozel(m):
    if m.from_user.id != YETKILI_ID:
        bot.reply_to(m, "⛔ Bu botu kullanmak için yetkiniz yok.")
    else:
        bot.reply_to(m, "✅ Yetkili erişim aktif.")

while True:
    if not internet_var_mi():
        time.sleep(5)
        continue
    try:
        bot.polling(none_stop=True)
    except:
        time.sleep(5)
