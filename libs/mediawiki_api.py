#!/usr/bin/env python3
"""
Script to transfer image to MediaWiki
It use MediaWiki API  to upload file
"""
from pathlib import Path
from libs.logger import log
import mimetypes
import os
import requests


class MediaWikiApi:
    def __init__(self):
        """
        Initialize MediaWiki API
        """
        self.api_url = os.getenv("MEDIAWIKI_URL") or "http://wiki.example.com/api.php"
        self.username = os.getenv("MEDIAWIKI_USER") or "adminUser"
        self.password = os.getenv("MEDIAWIKI_MDP") or "adminPwd"
        self.session = requests.Session()
        self.csrf_token = None
        self.login_error = None

    def login(self):
        log(f"Connection as {self.username}...")

        # Get connection token
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json",
        }

        try:
            response = self.session.get(self.api_url, params=params)
        except:
            log(f"Mediawiki server {self.api_url} not found")
            self.login_error = True
            return False

        data = response.json()
        login_token = data["query"]["tokens"]["logintoken"]

        # Connection
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
            log("Connection done")
            return True
        else:
            log(f"Connection error: {result['login']['result']}")
            self.login_error = True
            return False

    def get_csrf_token(self):
        """Get CSRF token nedeed to upload"""
        params = {"action": "query", "meta": "tokens", "format": "json"}

        response = self.session.get(self.api_url, params=params)
        data = response.json()
        self.csrf_token = data["query"]["tokens"]["csrftoken"]
        return self.csrf_token

    def upload_image(self, file_path, description=""):
        """
        Upload image to MediaWiki

        Args:
            file_path: image file path
            description: File description (option)
            overwrite: Replace file if exist

        Returns:
            True if success, False if not
        """
        if self.login_error:
            return False

        file_path = Path(file_path)

        if not file_path.exists():
            log(f"File not found: {file_path}")
            return False

        # Get token if not already done
        if not self.csrf_token:
            self.get_csrf_token()

        if not self.csrf_token:
            log("No link to Mediawiki. Image files will not be upload ")
            return

        log(f"Upload of {file_path.name}...")

        mime_type = mimetypes.guess_type(str(file_path))[0]
        upload_data = {
            "action": "upload",
            "filename": file_path.name,
            "text": description,
            "token": self.csrf_token,
            "format": "json",
            "ignorewarnings": "1",
        }

        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, mime_type)}
            response = self.session.post(self.api_url, data=upload_data, files=files)  # type: ignore

        try:
            result = response.json()

            if "upload" in result and result["upload"]["result"] == "Success":
                log(f"{file_path.name} uploaded with success")
                return True
            elif "error" in result:
                log(f"Error: {result['error']['info']}")
                return False
            elif "warnings" in result.get("upload", {}):
                warnings = result["upload"]["warnings"]
                log(f"Warning: {warnings}")
                return False
            else:
                log(f"Upload failed: {result}")
                return False
        except ValueError:
            log("Not a valid json response")

    def create_page(self, page_name: str, content: str):
        if not self.csrf_token:
            self.get_csrf_token()

        params = {
            "action": "edit",
            "title": page_name,
            "text": content,
            "summary": "Create or update page",
            "token": self.csrf_token,
            "format": "json",
        }

        response = self.session.post(self.api_url, data=params)
        data = response.json()

        if "edit" in data and data["edit"]["result"] == "Success":
            log(f"Page '{page_name}' created/modified successfully")
            if "new" in data["edit"]:
                log("New page created")
            else:
                log("Page updated")
            mediawiki_url = (
                os.getenv("MEDIAWIKI_URL") or "http://wiki.example.com/api.php"
            )
            return mediawiki_url.replace(
                "api.php", f"index.php?title={data["edit"]["title"]}"
            )
        else:
            log(f"Page creation fail: {data}")
            return "Page not created"
