# core/igdb_api.py (VERSÃO CORRIGIDA)

import os
import requests
import time
from PIL import Image
from io import BytesIO
from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET

from googletrans import Translator

def _translate_text(text, dest_language='pt'):
    """Função auxiliar para traduzir um texto, com tratamento de erro."""
    if not text:
        return ""
    try:
        translator = Translator()
        # O argumento 'timeout' foi REMOVIDO da chamada abaixo
        translated = translator.translate(text, dest=dest_language)
        
        if translated and translated.text:
            print(f"Texto traduzido com sucesso para: {translated.text[:50]}...")
            return translated.text
        else:
            # Caso a API retorne algo inesperado, mas sem erro
            raise Exception("A API de tradução retornou uma resposta vazia.")

    except Exception as e:
        print(f"Erro na tradução: {e}")
        return text # Em caso de erro, retorna o texto original

def download_and_save_images(game_data):
    # Esta função continua a mesma
    if not game_data or not game_data.get("igdb_id"):
        return {}

    artwork_folder = os.path.join("game_artwork", str(game_data["igdb_id"]))
    os.makedirs(artwork_folder, exist_ok=True)

    saved_paths = {}

    cover_url = game_data.get("cover_url")
    if cover_url:
        try:
            full_url = "https:" + cover_url
            response = requests.get(full_url, stream=True)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            save_path = os.path.join(artwork_folder, "poster.jpg")
            image.convert("RGB").save(save_path, "JPEG", quality=90)
            saved_paths["image"] = save_path
            print(f"Capa salva em: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar a capa de {full_url}: {e}")

    screenshot_urls = game_data.get("screenshot_urls", [])
    if screenshot_urls:
        try:
            full_url = "https:" + screenshot_urls[0]
            response = requests.get(full_url, stream=True)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            save_path = os.path.join(artwork_folder, "background.jpg")
            image.convert("RGB").save(save_path, "JPEG", quality=85)
            saved_paths["background"] = save_path
            saved_paths["header"] = save_path
            print(f"Screenshot salvo em: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o screenshot de {full_url}: {e}")

    return saved_paths

class IGDB_API:
    # O resto da classe continua o mesmo
    def __init__(self):
        self._client_id = TWITCH_CLIENT_ID
        self._client_secret = TWITCH_CLIENT_SECRET
        self._access_token = None
        self._token_expiration_time = 0
        self._api_url = "https://api.igdb.com/v4/"

    def _get_access_token(self):
        try:
            url = "https://id.twitch.tv/oauth2/token"
            params = { "client_id": self._client_id, "client_secret": self._client_secret, "grant_type": "client_credentials" }
            response = requests.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            self._token_expiration_time = time.time() + data["expires_in"] - 60
            print("Novo token de acesso do IGDB obtido com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter token de acesso do IGDB: {e}")
            return False

    def _get_headers(self):
        if not self._access_token or time.time() >= self._token_expiration_time:
            if not self._get_access_token():
                return None
        return { "Client-ID": self._client_id, "Authorization": f"Bearer {self._access_token}" }

    def search_games(self, game_name, limit=5):
        headers = self._get_headers()
        if not headers:
            return None

        query_data = f'search "{game_name}"; fields name, summary, genres.name, first_release_date, cover.url, screenshots.url; limit {limit}; where category = 0;'

        try:
            response = requests.post(self._api_url + "games", headers=headers, data=query_data)
            response.raise_for_status()
            found_games = response.json()
            
            formatted_games = []
            for game in found_games:
                original_summary = game.get("summary", "Nenhuma descrição encontrada.")
                translated_summary = _translate_text(original_summary)

                formatted_game = {
                    "igdb_id": game.get("id"),
                    "name": game.get("name"),
                    "summary": translated_summary,
                    "genres": [genre["name"] for genre in game.get("genres", [])],
                    "release_date": time.strftime('%Y-%m-%d', time.gmtime(game.get("first_release_date", 0))),
                    "cover_url": game.get("cover", {}).get("url", "").replace("/t_thumb/", "/t_cover_big/"),
                    "screenshot_urls": [ss["url"].replace("/t_thumb/", "/t_screenshot_huge/") for ss in game.get("screenshots", [])]
                }
                formatted_games.append(formatted_game)

            return formatted_games

        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar jogos no IGDB: {e}")
            return None