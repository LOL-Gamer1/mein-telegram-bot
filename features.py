
# ---------------- MODERATIONSMENÜ ----------------

async def moderation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data == "mod:admins":
        text = (
            "👮 GRUPPENADMINS\n\n"
            "Verwende in deiner Telegram-Gruppe:\n"
            "/admins – Gruppenadmins anzeigen\n\n"
            "Der Bot muss Mitglied der Gruppe sein."
        )

    elif data == "mod:groupinfo":
        text = (
            "📋 GRUPPENINFORMATIONEN\n\n"
            "/groupinfo – Gruppeninformationen anzeigen\n"
            "/grouplink – Gruppen-Einladungslink anzeigen\n\n"
            "Öffne die Gruppe und sende dort den gewünschten Befehl."
        )

    elif data == "mod:rules":
        text = (
            "📜 GRUPPENREGELN\n\n"
            "/rules – Regeln anzeigen\n"
            "/rules TEXT – Regeln speichern oder ändern\n"
            "/grouprules – Gruppenregeln anzeigen\n\n"
            "Regeln ändern dürfen nur Gruppenadmins."
        )

    elif data == "mod:commands":
        text = (
            "⚙️ MODERATION – BEFEHLSÜBERSICHT\n\n"
            "👮 GRUPPE UND ADMINS\n"
            "/admins – Admins anzeigen\n"
            "/groupinfo – Gruppeninfos\n"
            "/grouplink – Einladungslink\n"
            "/modhelp – Moderationshilfe\n\n"
            "👥 MITGLIEDER VERWALTEN\n"
            "/kick – Mitglied entfernen\n"
            "/promote – Adminrechte vergeben\n"
            "/demote – Adminrechte entziehen\n"
            "/pin – Nachricht anpinnen\n"
            "/del – Nachricht löschen\n"
            "/mute – Schreibrechte der Gruppe einschränken\n"
            "/unmute – Gruppenschreibrechte wiederherstellen\n"
            "/usermute – Person stummschalten\n"
            "/userunmute – Person entstummen\n"
            "/leave – Bot aus der Gruppe entfernen\n\n"
            "⚠️ VERWARNUNGEN\n"
            "/warn – Mitglied verwarnen\n"
            "/warnings – Verwarnungen anzeigen\n"
            "/resetwarnings – Verwarnungen zurücksetzen\n\n"
            "🛡️ AUTOMATISCHE MODERATION\n"
            "/antispam an|aus – Spamfilter\n"
            "/antiinsult an|aus – Beleidigungsfilter\n"
            "/antisticker an|aus – Stickerfilter\n\n"
            "👋 BEGRÜSSUNG UND REGELN\n"
            "/welcome TEXT – Begrüßungstext festlegen\n"
            "/welcometoggle an|aus – automatische Begrüßung\n"
            "/rules TEXT – Gruppenregeln speichern\n"
            "/rules – Gruppenregeln anzeigen\n\n"
            "ℹ️ WICHTIG\n"
            "Die Gruppenbefehle funktionieren in der Gruppe. "
            "Für Moderationsaktionen brauchst du die entsprechenden "
            "Adminrechte. Der Bot benötigt ebenfalls die nötigen Rechte."
        )

    else:
        text = "Diese Menüoption kenne ich nicht."

    await query.edit_message_text(
        text,
        reply_markup=moderation_keyboard(),
    )
