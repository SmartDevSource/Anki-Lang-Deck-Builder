import os, csv, asyncio, tempfile
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import edge_tts
import numpy as np
import sounddevice as sd
import threading
import io
import re

from voices import VOICE_BY_LANG_AND_SEX
from tts import generate_mp3
from languages import LANGUAGES, get_available_languages, get_text

class UI(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.output_dir = os.getcwd()
        self.cards = []
        self.is_playing = False
        self.editing_index = None  # Index de la carte en cours d'édition
        self.current_language = "English"  # Langue par défaut
        self.build()

    def build(self):
        self.master.title(self.get_text("title"))
        self.master.configure(bg="#f9f1da")
        self.master.option_add("*Font", ("Segoe UI", 10))
        
        # Configuration de la taille et empêcher le redimensionnement
        self.master.geometry("900x650")
        self.master.resizable(False, False)

        # Création du menu
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.get_text("file"), menu=file_menu)
        file_menu.add_command(label=self.get_text("load_csv"), command=self.load_csv, accelerator="Ctrl+O")
        file_menu.add_command(label=self.get_text("save_csv"), command=self.save_csv, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label=self.get_text("browse_folder"), command=self.browse)
        file_menu.add_separator()
        file_menu.add_command(label=self.get_text("exit"), command=self.master.quit, accelerator="Alt+F4")
        
        # Menu Language (à droite de File)
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.get_text("language"), menu=language_menu)
        
        # Variable pour les boutons radio
        self.language_var = tk.StringVar(value=self.current_language)
        
        # Créer les boutons radio pour les langues dynamiquement
        for lang in get_available_languages():
            language_menu.add_radiobutton(
                label=lang, 
                command=lambda l=lang: self.change_language(l), 
                value=lang, 
                variable=self.language_var
            )

        # Stocker les références des menus pour la mise à jour
        self.menubar = menubar
        self.language_menu = language_menu
        self.file_menu = file_menu

        # Frame principal avec deux colonnes
        main_frame = tk.Frame(self.master, bg="#f9f1da")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Colonne gauche pour les contrôles (largeur fixe plus large)
        left_frame = tk.Frame(main_frame, bg="#f9f1da", width=480)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)  # Maintient la largeur fixe

        # Colonne droite pour les temporary cards (plus étroite)
        right_frame = tk.Frame(main_frame, bg="#f9f1da", width=370)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        right_frame.pack_propagate(False)  # Maintient la largeur fixe

        # Stocker les références des frames pour la mise à jour
        self.left_frame = left_frame
        self.right_frame = right_frame
        
        self.create_widgets()

    def get_text(self, key, **kwargs):
        """Récupère le texte dans la langue actuelle"""
        return get_text(self.current_language, key, **kwargs)

    def change_language(self, language):
        """Change la langue de l'interface"""
        self.current_language = language
        self.update_interface()

    def focus_next_widget(self, event):
        event.widget.tk_focusNext().focus()
        return "break"
    
    def _language_type_ahead(self, event):
        char = event.char.lower()
        if not char.isalpha():
            return
        # Parcourt toutes les entrées du menu
        for index in range(self.language_menu.index("end") + 1):
            label = self.language_menu.entrycget(index, "label")
            if label.lower().startswith(char):
                self.language_menu.activate(index)
                return

    def _enable_language_type_ahead(self):
        self.master.bind("<Key>", self._language_type_ahead)

    def _disable_language_type_ahead(self, *args):
        self.master.unbind("<Key>")


    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # === COLONNE GAUCHE ===
        self.deck_label = tk.Label(self.left_frame, text=self.get_text("deck_filename"), bg="#f9f1da")
        self.deck_label.pack(anchor="w", pady=(0, 2))
        
        self.deck_var = tk.StringVar()
        self.deck_entry = tk.Entry(self.left_frame, textvariable=self.deck_var)
        self.deck_entry.pack(fill="x", pady=(0, 10))

        # Voix pour le texte source
        self.source_voice_label = tk.Label(self.left_frame, text=self.get_text("source_voice"), bg="#f9f1da")
        self.source_voice_label.pack(anchor="w", pady=(0, 2))
        
        self.source_voice_var = tk.StringVar()
        self.source_voice_combo = ttk.Combobox(self.left_frame, textvariable=self.source_voice_var, state="readonly")
        self.source_voice_combo["values"] = list(VOICE_BY_LANG_AND_SEX.keys())
        self.source_voice_combo.pack(fill="x", pady=(0, 8))
        
        # Définir une voix française par défaut (amélioré)
        french_voices = [v for v in VOICE_BY_LANG_AND_SEX.keys() if "French" in v or "fr-" in v.lower() or "français" in v.lower()]
        if french_voices:
            self.source_voice_combo.set(french_voices[0])

        self.source_text_label = tk.Label(self.left_frame, text=self.get_text("source_text"), bg="#f9f1da")
        self.source_text_label.pack(anchor="w", pady=(0, 2))
        
        self.src_txt = tk.Text(self.left_frame, height=3)
        self.src_txt.pack(fill="x", pady=(0, 5))
        
        # Frame pour bouton preview source et stop
        src_btn_frame = tk.Frame(self.left_frame, bg="#f9f1da")
        src_btn_frame.pack(fill="x", pady=(0, 8))
        
        self.preview_src_btn = tk.Button(src_btn_frame, text=self.get_text("preview_source"), command=self.preview_source, font=("Segoe UI", 9))
        self.preview_src_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        self.stop_src_btn = tk.Button(src_btn_frame, text="⏹", command=self.stop_audio, state="disabled", font=("Segoe UI", 9), width=3)
        self.stop_src_btn.pack(side="right", padx=(2, 0))

        self.swap_btn = tk.Button(self.left_frame, text="⇵", command=self.swap_texts)
        self.swap_btn.pack(pady=(0, 8))

        # Voix pour la traduction
        self.translation_voice_label = tk.Label(self.left_frame, text=self.get_text("translation_voice"), bg="#f9f1da")
        self.translation_voice_label.pack(anchor="w", pady=(0, 2))
        
        self.target_voice_var = tk.StringVar()
        self.target_voice_combo = ttk.Combobox(self.left_frame, textvariable=self.target_voice_var, state="readonly")
        self.target_voice_combo["values"] = list(VOICE_BY_LANG_AND_SEX.keys())
        self.target_voice_combo.pack(fill="x", pady=(0, 8))
        
        # Définir une voix anglaise par défaut (amélioré)
        english_voices = [v for v in VOICE_BY_LANG_AND_SEX.keys() if "English" in v or "en-" in v.lower() or "anglais" in v.lower()]
        if english_voices:
            self.target_voice_combo.set(english_voices[0])

        self.translation_label = tk.Label(self.left_frame, text=self.get_text("translation"), bg="#f9f1da")
        self.translation_label.pack(anchor="w", pady=(0, 2))
        
        self.tgt_txt = tk.Text(self.left_frame, height=3)
        self.tgt_txt.pack(fill="x", pady=(0, 5))
        
        # Frame pour bouton preview translation et stop
        tgt_btn_frame = tk.Frame(self.left_frame, bg="#f9f1da")
        tgt_btn_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_tgt_btn = tk.Button(tgt_btn_frame, text=self.get_text("preview_translation"), command=self.preview_translation, font=("Segoe UI", 9))
        self.preview_tgt_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        self.stop_tgt_btn = tk.Button(tgt_btn_frame, text="⏹", command=self.stop_audio, state="disabled", font=("Segoe UI", 9), width=3)
        self.stop_tgt_btn.pack(side="right", padx=(2, 0))

        # Bouton dynamique Add/Apply
        self.add_apply_btn = tk.Button(self.left_frame, text=self.get_text("add_to_list"), command=self.add_or_apply_card, font=("Segoe UI", 10, "bold"))
        self.add_apply_btn.pack(fill="x", pady=(0, 10))

        self.generate_btn = tk.Button(self.left_frame, text=self.get_text("generate_deck"), command=self.generate, font=("Segoe UI", 10, "bold"), bg="white", fg="black")
        self.generate_btn.pack(side="bottom", fill="x", pady=15)

        # === COLONNE DROITE ===
        self.temp_cards_label = tk.Label(self.right_frame, text=self.get_text("temp_cards"), bg="#f9f1da", font=("Segoe UI", 10, "bold"))
        self.temp_cards_label.pack(anchor="w", pady=(0, 5))
        
        # Frame pour la listbox avec scrollbar
        listbox_frame = tk.Frame(self.right_frame, bg="#f9f1da")
        listbox_frame.pack(fill="both", expand=True)
        
        # Scrollbar pour la listbox
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 9))
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind("<Double-Button-1>", self.edit_selected)
        self.listbox.bind("<KeyPress-Delete>", self.remove_selected)

        self.src_txt.bind("<Tab>", lambda e: self.focus_next_widget(e))
        self.tgt_txt.bind("<Tab>", lambda e: self.focus_next_widget(e))

    def update_interface(self):
        # -- titre fenêtre --
        self.master.title(self.get_text("title"))

        # -- RECONSTRUIT le menubar --
        new_menubar = tk.Menu(self.master)

        # Menu "File"
        self.file_menu = tk.Menu(new_menubar, tearoff=0)
        new_menubar.add_cascade(label=self.get_text("file"), menu=self.file_menu)
        self.file_menu.add_command(label=self.get_text("load_csv"), command=self.load_csv, accelerator="Ctrl+O")
        self.file_menu.add_command(label=self.get_text("save_csv"), command=self.save_csv, accelerator="Ctrl+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.get_text("browse_folder"), command=self.browse)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.get_text("exit"), command=self.master.quit, accelerator="Alt+F4")

        # Menu "Language"
        self.language_menu = tk.Menu(new_menubar, tearoff=0)
        new_menubar.add_cascade(label=self.get_text("language"), menu=self.language_menu)
        self.language_menu.bind("<Key>", self._language_type_ahead)

        # Boutons radio pour les langues
        for lang in get_available_languages():
            self.language_menu.add_radiobutton(
                label=lang,
                command=lambda l=lang: self.change_language(l),
                value=lang,
                variable=self.language_var
            )

        # Applique le nouveau menubar
        self.master.config(menu=new_menubar)
        self.menubar = new_menubar

        # -- reste de l’interface (labels, boutons, etc.) --
        self.deck_label.config(text=self.get_text("deck_filename"))
        self.source_voice_label.config(text=self.get_text("source_voice"))
        self.source_text_label.config(text=self.get_text("source_text"))
        self.translation_voice_label.config(text=self.get_text("translation_voice"))
        self.translation_label.config(text=self.get_text("translation"))
        self.temp_cards_label.config(text=self.get_text("temp_cards"))
        self.preview_src_btn.config(text=self.get_text("preview_source"))
        self.preview_tgt_btn.config(text=self.get_text("preview_translation"))

        # Bouton Add/Apply
        if self.editing_index is not None:
            self.add_apply_btn.config(text=self.get_text("apply_changes"))
        else:
            self.add_apply_btn.config(text=self.get_text("add_to_list"))

        self.generate_btn.config(text=self.get_text("generate_deck"))


    def browse(self):
        d = filedialog.askdirectory(initialdir=self.output_dir)
        if d:
            self.output_dir = d

    def swap_texts(self):
        # Échanger aussi les voix
        src = self.src_txt.get("1.0", tk.END)
        tgt = self.tgt_txt.get("1.0", tk.END)
        src_voice = self.source_voice_var.get()
        tgt_voice = self.target_voice_var.get()
        
        self.src_txt.delete("1.0", tk.END)
        self.tgt_txt.delete("1.0", tk.END)
        self.src_txt.insert(tk.END, tgt.strip())
        self.tgt_txt.insert(tk.END, src.strip())
        
        self.source_voice_var.set(tgt_voice)
        self.target_voice_var.set(src_voice)

    def preview_source(self):
        text = self.src_txt.get("1.0", tk.END).strip()
        voice_key = self.source_voice_var.get().strip()
        self._preview_async(text, voice_key, "source")

    def preview_translation(self):
        text = self.tgt_txt.get("1.0", tk.END).strip()
        voice_key = self.target_voice_var.get().strip()
        self._preview_async(text, voice_key, "target")

    def _preview_async(self, text, voice_key, source_type="target"):
        """Lance la preview dans un thread séparé pour éviter de bloquer l'UI"""
        if self.is_playing:
            return
            
        if not text or not voice_key:
            voice_label = self.get_text("source_voice_type") if source_type == "source" else self.get_text("translation_voice_type")
            messagebox.showerror(self.get_text("error"), self.get_text("enter_text_voice").format(voice_type=voice_label))
            return

        # Désactive les boutons pendant la lecture
        self.is_playing = True
        self.preview_src_btn.config(state="disabled", text=self.get_text("loading"))
        self.preview_tgt_btn.config(state="disabled", text=self.get_text("loading"))
        self.stop_src_btn.config(state="normal")
        self.stop_tgt_btn.config(state="normal")
        self.stop_src_btn.config(state="normal")
        self.stop_tgt_btn.config(state="normal")

        # Lance dans un thread
        thread = threading.Thread(target=self._preview_thread, args=(text, voice_key))
        thread.daemon = True
        thread.start()

    def _preview_thread(self, text, voice_key):
        """Thread pour la preview audio"""
        try:
            voice = VOICE_BY_LANG_AND_SEX[voice_key]
            
            # Méthode 1: Utiliser un fichier temporaire (plus fiable)
            self._preview_with_tempfile(text, voice)
            
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror(self.get_text("audio_error"), self.get_text("audio_error_msg").format(error=str(e))))
        finally:
            # Réactive les boutons dans le thread principal
            self.master.after(0, self._reset_buttons)

    def _preview_with_tempfile(self, text, voice):
        """Preview en utilisant un fichier temporaire"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            temp_path = tmp.name

        try:
            # Génère l'audio dans le fichier temporaire
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def generate_temp_audio():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_path)
            
            loop.run_until_complete(generate_temp_audio())
            loop.close()

            # Lit le fichier avec pygame (plus fiable que sounddevice)
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.is_playing:
                    pygame.time.wait(100)
            except ImportError:
                # Fallback avec sounddevice si pygame n'est pas disponible
                self._play_with_sounddevice(temp_path)
                
        finally:
            # Nettoie le fichier temporaire
            try:
                os.unlink(temp_path)
            except:
                pass

    def _play_with_sounddevice(self, file_path):
        """Fallback pour lire un fichier MP3 avec sounddevice"""
        try:
            import librosa
            audio, sr = librosa.load(file_path, sr=None)
            sd.play(audio, sr, blocking=True)
        except ImportError:
            # Si librosa n'est pas disponible, utilise une méthode basique
            messagebox.showwarning("Warning", "Pour une meilleure qualité audio, installez pygame ou librosa")

    def stop_audio(self):
        """Arrête la lecture audio"""
        self.is_playing = False
        try:
            sd.stop()  # Arrête sounddevice
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
        self._reset_buttons()

    def _reset_buttons(self):
        """Remet les boutons dans leur état normal"""
        self.is_playing = False
        self.preview_src_btn.config(state="normal", text=self.get_text("preview_source"))
        self.preview_tgt_btn.config(state="normal", text=self.get_text("preview_translation"))
        self.stop_src_btn.config(state="disabled")
        self.stop_tgt_btn.config(state="disabled")

    def add_or_apply_card(self):
        """Ajoute une nouvelle carte ou applique les modifications"""
        src = self.src_txt.get("1.0", tk.END).strip()
        tgt = self.tgt_txt.get("1.0", tk.END).strip()
        source_voice_key = self.source_voice_var.get().strip()
        target_voice_key = self.target_voice_var.get().strip()
        
        if src and tgt and target_voice_key:
            if self.editing_index is not None:
                # Mode édition : remplacer la carte existante
                self.cards[self.editing_index] = (src, tgt, source_voice_key, target_voice_key)
                
                # Mettre à jour l'affichage
                display_text = f"{src[:25]}... → {tgt[:25]}..."
                if source_voice_key:
                    display_text += f" (src:{source_voice_key.split()[0]}"
                if target_voice_key:
                    if source_voice_key:
                        display_text += f", tgt:{target_voice_key.split()[0]})"
                    else:
                        display_text += f" (tgt:{target_voice_key.split()[0]})"
                
                self.listbox.delete(self.editing_index)
                self.listbox.insert(self.editing_index, display_text)
                self.listbox.selection_set(self.editing_index)
                
                # Sortir du mode édition
                self.editing_index = None
                self.add_apply_btn.config(text=self.get_text("add_to_list"))
            else:
                # Mode ajout : nouvelle carte
                self.cards.append((src, tgt, source_voice_key, target_voice_key))
                
                display_text = f"{src[:25]}... → {tgt[:25]}..."
                if source_voice_key:
                    display_text += f" (src:{source_voice_key.split()[0]}"
                if target_voice_key:
                    if source_voice_key:
                        display_text += f", tgt:{target_voice_key.split()[0]})"
                    else:
                        display_text += f" (tgt:{target_voice_key.split()[0]})"
                
                self.listbox.insert(tk.END, display_text)
            
            # Effacer les champs
            self.clear_inputs()
        else:
            messagebox.showerror(self.get_text("error"), self.get_text("all_fields_required"))

    def clear_inputs(self):
        """Efface les champs de saisie"""
        self.src_txt.delete("1.0", tk.END)
        self.tgt_txt.delete("1.0", tk.END)

    def edit_selected(self, event):
        """Charge la carte sélectionnée pour édition"""
        sel = self.listbox.curselection()
        if sel:
            index = sel[0]
            card = self.cards[index]
            
            # Charger les données dans les champs
            if len(card) == 4:
                src, tgt, source_voice_key, target_voice_key = card
            else:
                # Rétrocompatibilité
                src, tgt, target_voice_key = card
                source_voice_key = ""
            
            self.src_txt.delete("1.0", tk.END)
            self.tgt_txt.delete("1.0", tk.END)
            self.src_txt.insert(tk.END, src)
            self.tgt_txt.insert(tk.END, tgt)
            
            if source_voice_key:
                self.source_voice_var.set(source_voice_key)
            if target_voice_key:
                self.target_voice_var.set(target_voice_key)
            
            # Passer en mode édition
            self.editing_index = index
            self.add_apply_btn.config(text=self.get_text("apply_changes"))

    def remove_selected(self, event):
        """Supprime la carte sélectionnée avec la touche DEL"""
        sel = self.listbox.curselection()
        if sel:
            for idx in reversed(sel):
                self.listbox.delete(idx)
                del self.cards[idx]
                
                # Si on supprime la carte en cours d'édition
                if self.editing_index == idx:
                    self.editing_index = None
                    self.add_apply_btn.config(text=self.get_text("add_to_list"))
                    self.clear_inputs()
                elif self.editing_index is not None and self.editing_index > idx:
                    # Ajuster l'index si on supprime une carte avant celle en édition
                    self.editing_index -= 1

    def load_csv(self):
        """Charge un fichier CSV avec vérification de structure"""
        file_path = filedialog.askopenfilename(
            title=self.get_text("load_csv_title"),
            initialdir=self.output_dir,
            filetypes=[(self.get_text("csv_files"), "*.csv"), (self.get_text("all_files"), "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Lecture et vérification du fichier
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                headers = reader.fieldnames
                
                # Vérification stricte de la structure
                expected_headers = ["Front", "Back", "Audio", "SourceAudio", "TargetAudio"]
                if not headers or set(headers) != set(expected_headers):
                    messagebox.showerror(
                        self.get_text("invalid_csv_structure"), 
                        self.get_text("invalid_csv_msg").format(
                            expected=', '.join(expected_headers),
                            found=', '.join(headers) if headers else 'None'
                        )
                    )
                    return
                
                # Lecture des données
                loaded_cards = []
                row_count = 0
                
                for row in reader:
                    row_count += 1
                    
                    # Vérification que les champs obligatoires sont présents
                    front = row.get("Front", "").strip()
                    back = row.get("Back", "").strip()
                    target_audio = row.get("TargetAudio", "").strip()
                    
                    if not front or not back:
                        messagebox.showerror(
                            self.get_text("invalid_data"), 
                            self.get_text("invalid_data_msg").format(
                                row=row_count, front=front, back=back
                            )
                        )
                        return
                    
                    # Extraction des voix à partir des champs audio
                    source_voice = self._extract_voice_from_audio(row.get("SourceAudio", ""))
                    target_voice = self._extract_voice_from_audio(target_audio)
                    
                    if not target_voice:
                        # Si on ne peut pas extraire la voix, utiliser la voix par défaut
                        target_voice = self.target_voice_var.get()
                        if not target_voice:
                            english_voices = [v for v in VOICE_BY_LANG_AND_SEX.keys() if "English" in v or "en-" in v.lower()]
                            target_voice = english_voices[0] if english_voices else list(VOICE_BY_LANG_AND_SEX.keys())[0]
                    
                    loaded_cards.append((front, back, source_voice, target_voice))
                
                # Si tout va bien, charger les données
                self.cards = loaded_cards
                self._refresh_listbox()
                
                # Sortir du mode édition si on était en train d'éditer
                self.editing_index = None
                self.add_apply_btn.config(text=self.get_text("add_to_list"))
                self.clear_inputs()
                
                messagebox.showinfo(self.get_text("success"), self.get_text("cards_loaded").format(
                    count=len(loaded_cards), path=file_path
                ))
                
        except UnicodeDecodeError:
            messagebox.showerror(self.get_text("encoding_error"), self.get_text("encoding_error_msg"))
        except Exception as e:
            messagebox.showerror(self.get_text("error"), self.get_text("load_error").format(error=str(e)))

    def _extract_voice_from_audio(self, audio_field):
        """Extrait le nom de la voix à partir du nom de fichier audio"""
        if not audio_field or "[sound:" not in audio_field:
            return ""
        
        # Extraction du nom de fichier depuis [sound:filename.mp3]
        try:
            match = re.search(r'\[sound:([^\]]+)\]', audio_field)
            if match:
                filename = match.group(1)
                # Le nom de fichier devrait contenir des infos sur la voix
                # On essaie de retrouver une voix correspondante
                for voice_key in VOICE_BY_LANG_AND_SEX.keys():
                    # Recherche basique - peut être améliorée selon votre logique de nommage
                    if any(part in filename.lower() for part in voice_key.lower().split()):
                        return voice_key
        except:
            pass
        
        return ""

    def _refresh_listbox(self):
        """Rafraîchit l'affichage de la listbox avec les cartes actuelles"""
        self.listbox.delete(0, tk.END)
        
        for card in self.cards:
            if len(card) == 4:
                src, tgt, source_voice_key, target_voice_key = card
            else:
                src, tgt, target_voice_key = card
                source_voice_key = ""
            
            display_text = f"{src[:25]}... → {tgt[:25]}..."
            if source_voice_key:
                display_text += f" (src:{source_voice_key.split()[0]}"
            if target_voice_key:
                if source_voice_key:
                    display_text += f", tgt:{target_voice_key.split()[0]})"
                else:
                    display_text += f" (tgt:{target_voice_key.split()[0]})"
            
            self.listbox.insert(tk.END, display_text)

    def save_csv(self):
        """Sauvegarde les cartes actuelles dans un fichier CSV"""
        if not self.cards:
            messagebox.showerror(self.get_text("error"), self.get_text("no_cards_to_save"))
            return
        
        file_path = filedialog.asksaveasfilename(
            title=self.get_text("save_csv_title"),
            initialdir=self.output_dir,
            defaultextension=".csv",
            filetypes=[(self.get_text("csv_files"), "*.csv"), (self.get_text("all_files"), "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Génération des données temporaires (sans audio) pour la sauvegarde
            rows = []
            for card in self.cards:
                if len(card) == 4:
                    src, tgt, source_voice_key, target_voice_key = card
                else:
                    src, tgt, target_voice_key = card
                    source_voice_key = ""
                
                # Création des champs audio avec noms de fichiers temporaires
                target_audio_name = f"{target_voice_key.replace(' ', '_')}_{hash(tgt) % 10000}.mp3"
                source_audio_name = f"{source_voice_key.replace(' ', '_')}_{hash(src) % 10000}.mp3" if source_voice_key else ""
                
                audio_field = f"[sound:{target_audio_name}]"
                if source_audio_name:
                    audio_field = f"[sound:{source_audio_name}] / [sound:{target_audio_name}]"
                
                rows.append({
                    "Front": src,
                    "Back": tgt,
                    "Audio": audio_field,
                    "SourceAudio": f"[sound:{source_audio_name}]" if source_audio_name else "",
                    "TargetAudio": f"[sound:{target_audio_name}]"
                })
            
            # Écriture du fichier
            fieldnames = ["Front", "Back", "Audio", "SourceAudio", "TargetAudio"]
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
            
            messagebox.showinfo(self.get_text("success"), self.get_text("cards_saved").format(
                count=len(rows), path=file_path
            ))
            
        except Exception as e:
            messagebox.showerror(self.get_text("error"), self.get_text("save_error").format(error=str(e)))

    def generate(self):
        import genanki
        import hashlib
        import shutil

        deck_name = self.deck_var.get().strip()
        if not deck_name:
            messagebox.showerror(self.get_text("error"), self.get_text("enter_deck_filename"))
            return
        if not self.cards:
            messagebox.showerror(self.get_text("error"), self.get_text("no_cards"))
            return

        async def _run():
            # modèle anki (utilise les balises [sound:...] -> Anki ne joue pas automatiquement tant qu'on ne clique pas)
            model_id = int(hashlib.md5(b"BasicTTSModel").hexdigest()[:8], 16)
            model = genanki.Model(
                model_id,
                'BasicTTSModel',
                fields=[
                    {'name': 'Front'},
                    {'name': 'Back'},
                    {'name': 'SourceAudio'},
                    {'name': 'TargetAudio'},
                ],
                templates=[
                    {
                        'name': 'Card 1',
                        'qfmt': '<div style="text-align:center;">{{Front}}<br>{{SourceAudio}}</div>',
                        'afmt': '<div style="text-align:center;">{{Front}}</div><hr><div style="text-align:center;">{{Back}}<br>{{TargetAudio}}</div>',
                    },
                ])

            deck_id = int(hashlib.md5(deck_name.encode('utf-8')).hexdigest()[:8], 16)
            deck = genanki.Deck(deck_id, deck_name)
            media_files = []

            for card in self.cards:
                if len(card) == 3:
                    src, tgt, target_voice_key = card
                    source_voice_key = None
                else:
                    src, tgt, source_voice_key, target_voice_key = card

                # target audio
                target_mp3 = await generate_mp3(tgt, VOICE_BY_LANG_AND_SEX[target_voice_key], self.output_dir)
                media_files.append(os.path.join(self.output_dir, target_mp3))
                target_audio_tag = f"[sound:{target_mp3}]"

                # source audio (optionnel)
                source_audio_tag = ""
                if source_voice_key and source_voice_key in VOICE_BY_LANG_AND_SEX:
                    source_mp3 = await generate_mp3(src, VOICE_BY_LANG_AND_SEX[source_voice_key], self.output_dir)
                    media_files.append(os.path.join(self.output_dir, source_mp3))
                    source_audio_tag = f"[sound:{source_mp3}]"

                note = genanki.Note(
                    model=model,
                    fields=[src, tgt, source_audio_tag, target_audio_tag]
                )
                deck.add_note(note)

            # dossier dédié
            deck_folder = os.path.join(self.output_dir, deck_name)
            os.makedirs(deck_folder, exist_ok=True)

            # écrit l'apkg
            apkg_path = os.path.join(deck_folder, f"{deck_name}.apkg")
            pkg = genanki.Package(deck)
            pkg.media_files = media_files
            pkg.write_to_file(apkg_path)

            # déplace les mp3 dans le dossier
            for m in media_files:
                filename = os.path.basename(m)
                dst = os.path.join(deck_folder, filename)
                if not os.path.exists(dst):
                    shutil.move(m, dst)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_run())
        loop.close()
        messagebox.showinfo(self.get_text("done"), f"Dossier généré → {os.path.join(self.output_dir, deck_name)}")
