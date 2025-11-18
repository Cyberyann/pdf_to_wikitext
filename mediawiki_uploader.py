#!/usr/bin/env python3
"""
Script pour transférer des images vers MediaWiki
Utilise l'API MediaWiki pour uploader des fichiers
"""

import requests
from pathlib import Path
import mimetypes


class MediaWikiUploader:
    def __init__(self, api_url, username, password):
        """
        Initialise l'uploader MediaWiki

        Args:
            api_url: URL de l'API MediaWiki (ex: https://wiki.example.com/api.php)
            username: Nom d'utilisateur
            password: Mot de passe
        """
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.csrf_token = None

    def login(self):
        """Se connecte à MediaWiki"""
        print(f"Connexion en tant que {self.username}...")

        # Obtenir le token de connexion
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }

        response = self.session.get(self.api_url, params=params)
        data = response.json()
        login_token = data["query"]["tokens"]["logintoken"]

        # Se connecter
        login_data = {
            "action": "login",
            "lgname": self.username,
            "lgpassword": self.password,
            "lgtoken": login_token,
            "format": "json",
        }

        response = self.session.post(self.api_url, data=login_data)
        result = response.json()

        if result["login"]["result"] == "Success":
            print("✓ Connexion réussie")
            return True
        else:
            print(f"✗ Échec de connexion: {result['login']['result']}")
            return False

    def get_csrf_token(self):
        """Obtient le token CSRF nécessaire pour l'upload"""
        params = {"action": "query", "meta": "tokens", "format": "json"}

        response = self.session.get(self.api_url, params=params)
        data = response.json()
        self.csrf_token = data["query"]["tokens"]["csrftoken"]
        return self.csrf_token

    def upload_image(self, file_path, description="", overwrite=False):
        """
        Upload une image vers MediaWiki

        Args:
            file_path: Chemin vers le fichier image
            description: Description du fichier (optionnel)
            overwrite: Remplacer le fichier s'il existe déjà

        Returns:
            True si succès, False sinon
        """
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"✗ Fichier non trouvé: {file_path}")
            return False

        # Obtenir le token CSRF si nécessaire
        if not self.csrf_token:
            self.get_csrf_token()

        print(f"Upload de {file_path.name}...")

        # Préparer les données
        mime_type = mimetypes.guess_type(str(file_path))[0]
        upload_data = {
            "action": "upload",
            "filename": file_path.name,
            "text": description,
            "token": self.csrf_token,
            "format": "json",
        }

        if overwrite:
            upload_data["ignorewarnings"] = "1"

        # Upload le fichier
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, mime_type)}
            response = self.session.post(self.api_url, data=upload_data, files=files)

        try:
            result = response.json()

            if "upload" in result and result["upload"]["result"] == "Success":
                print(f"✓ {file_path.name} uploadé avec succès")
                return True
            elif "error" in result:
                print(f"✗ Erreur: {result['error']['info']}")
                return False
            elif "warnings" in result.get("upload", {}):
                warnings = result["upload"]["warnings"]
                print(f"⚠ Avertissements: {warnings}")
                return False
            else:
                print(f"✗ Échec de l'upload: {result}")
                return False
        except ValueError:
            print("Not a valid json response")

    def upload_directory(
        self, directory_path, description="", overwrite=False, extensions=None
    ):
        """
        Upload toutes les images d'un répertoire

        Args:
            directory_path: Chemin vers le répertoire
            description: Description par défaut pour tous les fichiers
            overwrite: Remplacer les fichiers existants
            extensions: Liste des extensions à uploader (ex: ['.jpg', '.png'])
                       Si None, upload toutes les images communes
        """
        if extensions is None:
            extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]

        directory = Path(directory_path)

        if not directory.is_dir():
            print(f"✗ Répertoire non trouvé: {directory}")
            return

        # Trouver toutes les images
        image_files = []
        for ext in extensions:
            image_files.extend(directory.glob(f"*{ext}"))
            image_files.extend(directory.glob(f"*{ext.upper()}"))

        if not image_files:
            print(f"Aucune image trouvée dans {directory}")
            return

        print(f"\nTrouvé {len(image_files)} image(s) à uploader")

        success_count = 0
        for img_file in image_files:
            if self.upload_image(img_file, description, overwrite):
                success_count += 1

        print(f"\n✓ {success_count}/{len(image_files)} images uploadées avec succès")


# def main():
#     """Fonction principale - exemple d'utilisation"""
#     print("=== Upload d'images vers MediaWiki ===\n")

#     # Configuration - à personnaliser
#     api_url = input("URL de l'API MediaWiki (ex: https://wiki.example.com/api.php): ")
#     username = input("Nom d'utilisateur: ")
#     password = getpass.getpass("Mot de passe: ")

#     # Créer l'uploader et se connecter
#     uploader = MediaWikiUploader(api_url, username, password)

#     if not uploader.login():
#         print("Impossible de se connecter")
#         return

#     # Menu de choix
#     print("\nQue voulez-vous faire ?")
#     print("1. Uploader un fichier unique")
#     print("2. Uploader tous les fichiers d'un répertoire")
#     choice = input("Choix (1 ou 2): ")

#     if choice == "1":
#         file_path = input("Chemin du fichier: ")
#         description = input("Description (optionnel): ")
#         overwrite = input("Écraser si existe déjà ? (o/n): ").lower() == 'o'
#         uploader.upload_image(file_path, description, overwrite)

#     elif choice == "2":
#         directory = input("Chemin du répertoire: ")
#         description = input("Description pour tous les fichiers (optionnel): ")
#         overwrite = input("Écraser les fichiers existants ? (o/n): ").lower() == 'o'
#         uploader.upload_directory(directory, description, overwrite)
