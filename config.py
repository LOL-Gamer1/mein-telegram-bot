
# config.py
# LOL Studios Manager

# Telegram-ID des Bot-Owners
OWNER_ID = 8995460599

BOT_NAME = "LOL Studios Manager"
BOT_VERSION = "5.0.0"

# Befehle, die auch ohne Registrierung erlaubt sind
PUBLIC_COMMANDS = {
    "start",
    "register",
    "unregister",
    "cancel",
    "skip",
    "help",
    "myid",
    "id",
    "ping",
    "tos",
    "gdpr",
    "permissions",
    "policy",
    "optout",
    "support",
}

# Altersgruppen statt eines exakten Geburtsdatums
AGE_GROUPS = [
    ("10–12", "10-12"),
    ("13–15", "13-15"),
    ("16–17", "16-17"),
    ("18+", "18+"),
]

# Economy-Belohnungen
REWARDS = {
    "daily": 100,
    "weekly": 1000,
    "monthly": 5000,
    "yearly": 50000,
}

# Virtuelle Spiele: keine Echtgeld-Auszahlungen
STARTING_POINTS = 0
MAX_GIFT_POINTS = 100000
MAX_SUPPORT_LENGTH = 1500
MAX_BIO_LENGTH = 250
MAX_PROFILE_NAME_LENGTH = 40

# Datenschutz- und Community-Texte
COMMUNITY_RULES = [
    "Sei respektvoll gegenüber anderen.",
    "Kein Spam, keine Belästigung und keine Betrugsversuche.",
    "Versuche nicht, Berechtigungen oder Sperren zu umgehen.",
    "Teile keine Passwörter, Tokens oder privaten Zugangsdaten.",
    "Melde Probleme über /support.",
]
