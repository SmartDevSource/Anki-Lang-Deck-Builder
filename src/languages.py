LANGUAGES = {
    "English": {
        "title": "Anki Lang Deck Builder",
        "file": "File",
        "language": "Language",
        "load_csv": "Load CSV...",
        "save_csv": "Save CSV...",
        "browse_folder": "Browse output folder...",
        "exit": "Exit",
        "deck_filename": "📂 Deck name",
        "source_voice": "🎙 Source Voice",
        "source_text": "Source text",
        "translation_voice": "🎙 Translation Voice",
        "translation": "Translation",
        "preview_source": "🔊 Preview Source",
        "preview_translation": "🔊 Preview Translation",
        "add_to_list": "➕ Add to list",
        "apply_changes": "✏️ Apply changes",
        "generate_deck": "Generate deck (*.APKG)",
        "temp_cards": "📄 Cards (double-click to edit, DEL to remove)",
        "error": "Error",
        "success": "Success",
        "done": "Done",
        "loading": "🔄 Loading...",
        "enter_text_voice": "Enter text and select a {voice_type}.",
        "source_voice_type": "source voice",
        "translation_voice_type": "translation voice",
        "audio_error": "Audio Error",
        "audio_error_msg": "Error during playback: {error}",
        "all_fields_required": "Source text, translation text, and translation voice must be filled.",
        "enter_deck_filename": "Please enter a deck filename.",
        "no_cards": "No cards in the list.",
        "deck_generated": "Deck generated:\n{path}\n\nColumns: Front, Back, Audio, SourceAudio, TargetAudio",
        "invalid_csv_structure": "Invalid CSV Structure",
        "invalid_csv_msg": "The CSV file must have exactly these columns:\n{expected}\n\nFound columns: {found}",
        "invalid_data": "Invalid Data",
        "invalid_data_msg": "Row {row}: Front and Back fields cannot be empty.\nFront: '{front}'\nBack: '{back}'",
        "encoding_error": "Encoding Error",
        "encoding_error_msg": "Could not read the file. Please ensure it's saved with UTF-8 encoding.",
        "load_error": "Failed to load CSV file:\n{error}",
        "save_error": "Failed to save CSV file:\n{error}",
        "no_cards_to_save": "No cards to save.",
        "cards_loaded": "Successfully loaded {count} cards from:\n{path}",
        "cards_saved": "Successfully saved {count} cards to:\n{path}",
        "load_csv_title": "Load CSV file",
        "save_csv_title": "Save CSV file",
        "csv_files": "CSV files",
        "all_files": "All files",
        "about": "About",
        "about_title": "About",
        "close": "Close",
        "cancel": "Cancel",
        "about_text": "Made with love by Emmanuel Beaugendre\nfor my friends from the Anki community ! :-)"
    },
    "Français": {
        "title": "Anki Lang Deck Builder",
        "file": "Fichier",
        "language": "Langue",
        "load_csv": "Charger CSV...",
        "save_csv": "Sauvegarder CSV...",
        "browse_folder": "Parcourir le dossier de sortie...",
        "exit": "Quitter",
        "deck_filename": "📂 Nom du deck",
        "source_voice": "🎙 Voix Source",
        "source_text": "Texte source",
        "translation_voice": "🎙 Voix Traduction",
        "translation": "Traduction",
        "preview_source": "🔊 Aperçu Source",
        "preview_translation": "🔊 Aperçu Traduction",
        "add_to_list": "➕ Ajouter à la liste",
        "apply_changes": "✏️ Appliquer les modifications",
        "generate_deck": "Générer le deck (*.APKG)",
        "temp_cards": "📄 Cartes (double-clic pour éditer, SUPPR pour supprimer)",
        "error": "Erreur",
        "success": "Succès",
        "done": "Terminé",
        "loading": "🔄 Chargement...",
        "enter_text_voice": "Entrez le texte et sélectionnez une {voice_type}.",
        "source_voice_type": "voix source",
        "translation_voice_type": "voix de traduction",
        "audio_error": "Erreur Audio",
        "audio_error_msg": "Erreur lors de la lecture : {error}",
        "all_fields_required": "Le texte source, la traduction et la voix de traduction doivent être remplis.",
        "enter_deck_filename": "Veuillez entrer un nom de fichier pour le deck.",
        "no_cards": "Aucune carte dans la liste.",
        "deck_generated": "Deck généré :\n{path}\n\nColonnes : Front, Back, Audio, SourceAudio, TargetAudio",
        "invalid_csv_structure": "Structure CSV Invalide",
        "invalid_csv_msg": "Le fichier CSV doit avoir exactement ces colonnes :\n{expected}\n\nColonnes trouvées : {found}",
        "invalid_data": "Données Invalides",
        "invalid_data_msg": "Ligne {row} : Les champs Front et Back ne peuvent pas être vides.\nFront : '{front}'\nBack : '{back}'",
        "encoding_error": "Erreur d'Encodage",
        "encoding_error_msg": "Impossible de lire le fichier. Assurez-vous qu'il est sauvegardé en UTF-8.",
        "load_error": "Échec du chargement du fichier CSV :\n{error}",
        "save_error": "Échec de la sauvegarde du fichier CSV :\n{error}",
        "no_cards_to_save": "Aucune carte à sauvegarder.",
        "cards_loaded": "{count} cartes chargées avec succès depuis :\n{path}",
        "cards_saved": "{count} cartes sauvegardées avec succès dans :\n{path}",
        "load_csv_title": "Charger un fichier CSV",
        "save_csv_title": "Sauvegarder un fichier CSV",
        "csv_files": "Fichiers CSV",
        "all_files": "Tous les fichiers",
        "about": "À propos",
        "about_title": "À propos",
        "close": "Fermer",
        "cancel": "Annuler",
        "about_text": "Fait avec amour par Emmanuel Beaugendre\npour mes amis de la communauté d'Anki ! :-)"
    }
}

def get_available_languages():
    """Retourne la liste des langues disponibles"""
    return list(LANGUAGES.keys())

def get_text(language, key, **kwargs):
    """
    Récupère le texte dans la langue spécifiée
    
    Args:
        language (str): Langue désirée ("English" ou "Français")
        key (str): Clé du texte à récupérer
        **kwargs: Arguments pour le formatage du texte
    
    Returns:
        str: Texte formaté dans la langue demandée
    """
    if language not in LANGUAGES:
        language = "English"  # Fallback vers l'anglais
    
    text = LANGUAGES[language].get(key, key)
    
    # Formatage du texte si des arguments sont fournis
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    
    return text