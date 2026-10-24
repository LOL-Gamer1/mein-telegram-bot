
# translations.py
# LOL Studios Manager — Mehrsprachiger Start

import database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


LANGUAGES = {
    "de": {"flag": "🇩🇪", "name": "Deutsch"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "es": {"flag": "🇪🇸", "name": "Español"},
    "fr": {"flag": "🇫🇷", "name": "Français"},
    "tr": {"flag": "🇹🇷", "name": "Türkçe"},
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "ru": {"flag": "🇷🇺", "name": "Русский"},
    "pt": {"flag": "🇵🇹", "name": "Português"},
    "hi": {"flag": "🇮🇳", "name": "हिन्दी"},
    "zh": {"flag": "🇨🇳", "name": "中文"},
}

TEXTS = {
    "de": {
        "welcome": "👋 Willkommen bei LOL Studios Manager!",
        "intro": "Wähle zuerst deine Sprache, damit du den Bot besser verstehen kannst.",
        "language_button": "🌐 Sprache / Language / Idioma",
        "choose_language": "🌍 Wähle deine Sprache aus:",
        "language_saved": "✅ Sprache geändert: Deutsch",
        "registered": "Du bist bereits registriert.",
        "register_hint": "📝 Erstelle dein Konto mit /register.",
        "menu_hint": "🎮 Hauptmenü: /menu\n❓ Hilfe: /help",
        "language_command": "Du kannst deine Sprache jederzeit mit /language ändern.",
    },
    "en": {
        "welcome": "👋 Welcome to LOL Studios Manager!",
        "intro": "Choose your language first so you can understand and use the bot.",
        "language_button": "🌐 Language / Sprache / Idioma",
        "choose_language": "🌍 Choose your language:",
        "language_saved": "✅ Language changed: English",
        "registered": "You are already registered.",
        "register_hint": "📝 Create your account with /register.",
        "menu_hint": "🎮 Main menu: /menu\n❓ Help: /help",
        "language_command": "You can change your language anytime with /language.",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido a LOL Studios Manager!",
        "intro": "Elige primero tu idioma para entender y utilizar el bot.",
        "language_button": "🌐 Idioma / Language / Sprache",
        "choose_language": "🌍 Elige tu idioma:",
        "language_saved": "✅ Idioma cambiado: Español",
        "registered": "Ya estás registrado.",
        "register_hint": "📝 Crea tu cuenta con /register.",
        "menu_hint": "🎮 Menú principal: /menu\n❓ Ayuda: /help",
        "language_command": "Puedes cambiar el idioma cuando quieras con /language.",
    },
    "fr": {
        "welcome": "👋 Bienvenue sur LOL Studios Manager !",
        "intro": "Choisis d’abord ta langue pour mieux comprendre et utiliser le bot.",
        "language_button": "🌐 Langue / Language / Sprache",
        "choose_language": "🌍 Choisis ta langue :",
        "language_saved": "✅ Langue changée : Français",
        "registered": "Tu es déjà inscrit.",
        "register_hint": "📝 Crée ton compte avec /register.",
        "menu_hint": "🎮 Menu principal : /menu\n❓ Aide : /help",
        "language_command": "Tu peux changer de langue à tout moment avec /language.",
    },
    "tr": {
        "welcome": "👋 LOL Studios Manager'a hoş geldin!",
        "intro": "Botu daha iyi anlayıp kullanabilmek için önce dilini seç.",
        "language_button": "🌐 Dil / Language / Sprache",
        "choose_language": "🌍 Dilini seç:",
        "language_saved": "✅ Dil değiştirildi: Türkçe",
        "registered": "Zaten kayıtlısın.",
        "register_hint": "📝 /register komutuyla hesap oluştur.",
        "menu_hint": "🎮 Ana menü: /menu\n❓ Yardım: /help",
        "language_command": "Dilini istediğin zaman /language komutuyla değiştirebilirsin.",
    },
    "ar": {
        "welcome": "👋 مرحبًا بك في LOL Studios Manager!",
        "intro": "اختر لغتك أولاً حتى تتمكن من فهم البوت واستخدامه.",
        "language_button": "🌐 اللغة / Language",
        "choose_language": "🌍 اختر لغتك:",
        "language_saved": "✅ تم تغيير اللغة إلى العربية",
        "registered": "أنت مسجل بالفعل.",
        "register_hint": "📝 أنشئ حسابك باستخدام /register.",
        "menu_hint": "🎮 القائمة الرئيسية: /menu\n❓ المساعدة: /help",
        "language_command": "يمكنك تغيير اللغة في أي وقت باستخدام /language.",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в LOL Studios Manager!",
        "intro": "Сначала выбери язык, чтобы понимать и использовать бота.",
        "language_button": "🌐 Язык / Language",
        "choose_language": "🌍 Выбери язык:",
        "language_saved": "✅ Язык изменён: Русский",
        "registered": "Ты уже зарегистрирован.",
        "register_hint": "📝 Создай аккаунт с помощью /register.",
        "menu_hint": "🎮 Главное меню: /menu\n❓ Помощь: /help",
        "language_command": "Язык можно изменить в любое время командой /language.",
    },
    "pt": {
        "welcome": "👋 Bem-vindo ao LOL Studios Manager!",
        "intro": "Escolhe primeiro o teu idioma para compreender e utilizar o bot.",
        "language_button": "🌐 Idioma / Language",
        "choose_language": "🌍 Escolhe o teu idioma:",
        "language_saved": "✅ Idioma alterado: Português",
        "registered": "Já estás registado.",
        "register_hint": "📝 Cria a tua conta com /register.",
        "menu_hint": "🎮 Menu principal: /menu\n❓ Ajuda: /help",
        "language_command": "Podes mudar o idioma a qualquer momento com /language.",
    },
    "hi": {
        "welcome": "👋 LOL Studios Manager में आपका स्वागत है!",
        "intro": "बॉट को समझने और इस्तेमाल करने के लिए पहले अपनी भाषा चुनें।",
        "language_button": "🌐 भाषा / Language",
        "choose_language": "🌍 अपनी भाषा चुनें:",
        "language_saved": "✅ भाषा बदल दी गई: हिन्दी",
        "registered": "आप पहले से पंजीकृत हैं।",
        "register_hint": "📝 /register से अपना खाता बनाएँ।",
        "menu_hint": "🎮 मुख्य मेनू: /menu\n❓ सहायता: /help",
        "language_command": "आप कभी भी /language से भाषा बदल सकते हैं।",
    },
    "zh": {
        "welcome": "👋 欢迎使用 LOL Studios Manager！",
        "intro": "请先选择语言，这样你就能更容易理解和使用机器人。",
        "language_button": "🌐 语言 / Language",
        "choose_language": "🌍 请选择你的语言：",
        "language_saved": "✅ 语言已更改为：中文",
        "registered": "你已经注册了。",
        "register_hint": "📝 使用 /register 创建账户。",
        "menu_hint": "🎮 主菜单：/menu\n❓ 帮助：/help",
        "language_command": "你可以随时使用 /language 更改语言。",
    },
}


def init_language_db():
    """Erstellt eine eigene Tabelle, ohne vorhandene Tabellen zu verändern."""
    with database.connect() as db:
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_languages (
                user_id BIGINT PRIMARY KEY,
                language VARCHAR(10) NOT NULL DEFAULT 'en',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.close()


def get_language(user_id):
    """Liefert die gespeicherte Sprache; Englisch ist der sichere Fallback."""
    try:
        with database.connect() as db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT language FROM user_languages WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            cursor.close()

        if row and row[0] in LANGUAGES:
            return row[0]
    except Exception:
        # Falls die Tabelle noch nicht existiert, wird Englisch verwendet.
        pass

    return "en"


def set_language(user_id, language):
    if language not in LANGUAGES:
        return False

    with database.connect() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO user_languages (user_id, language)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE language = VALUES(language)
        """, (user_id, language))
        cursor.close()

    return True


def tr(user_id, key):
    language = get_language(user_id)
    return TEXTS.get(language, TEXTS["en"]).get(
        key,
        TEXTS["en"].get(key, key),
    )


def language_keyboard():
    buttons = []

    for code, info in LANGUAGES.items():
        buttons.append(
            InlineKeyboardButton(
                f"{info['flag']} {info['name']}",
                callback_data=f"lang:{code}",
            )
        )

    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


def language_button_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🌐 Language / Sprache / Idioma",
            callback_data="lang:open",
        )
    ]])
