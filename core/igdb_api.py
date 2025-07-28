# core/igdb_api.py

import os
import requests
import time
from PIL import Image
from io import BytesIO
from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET

# Em core/igdb_api.py

def download_and_save_images(game_data):
    """
    Baixa a capa e o primeiro screenshot de um jogo, salvando localmente.
    Retorna um dicionário com os caminhos locais das imagens salvas.
    """
    if not game_data or not game_data.get("igdb_id"):
        return {}

    artwork_folder = os.path.join("game_artwork", str(game_data["igdb_id"]))
    os.makedirs(artwork_folder, exist_ok=True)

    saved_paths = {}

    # 1. Baixar a Capa (Poster)
    cover_url = game_data.get("cover_url")
    if cover_url:
        try:
            full_url = "https:" + cover_url
            response = requests.get(full_url, stream=True)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            save_path = os.path.join(artwork_folder, "poster.jpg")
            image.convert("RGB").save(save_path, "JPEG", quality=90)

            # --- CORREÇÃO AQUI ---
            saved_paths["image"] = save_path # ANTES: "image_path"
            # ---------------------

            print(f"Capa salva em: {save_path}")

        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar a capa de {full_url}: {e}")

    # 2. Baixar o primeiro Screenshot (para usar como Header/Background)
    screenshot_urls = game_data.get("screenshot_urls", [])
    if screenshot_urls:
        try:
            full_url = "https:" + screenshot_urls[0]
            response = requests.get(full_url, stream=True)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            save_path = os.path.join(artwork_folder, "background.jpg")
            image.convert("RGB").save(save_path, "JPEG", quality=85)

            # --- CORREÇÃO AQUI ---
            saved_paths["background"] = save_path # ANTES: "background_path"
            saved_paths["header"] = save_path     # ANTES: "header_path"
            # ---------------------

            print(f"Screenshot salvo em: {save_path}")

        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o screenshot de {full_url}: {e}")

    return saved_paths

class IGDB_API:
    def __init__(self):
        self._client_id = TWITCH_CLIENT_ID
        self._client_secret = TWITCH_CLIENT_SECRET
        self._access_token = None
        self._token_expiration_time = 0
        self._api_url = "https://api.igdb.com/v4/"

    def _get_access_token(self):
        """Obtém um novo token de acesso da Twitch."""
        try:
            url = "https://id.twitch.tv/oauth2/token"
            params = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "client_credentials"
            }
            response = requests.post(url, params=params)
            response.raise_for_status() # Lança um erro se a requisição falhar
            data = response.json()

            self._access_token = data["access_token"]
            # Guarda o momento em que o token expira (com uma pequena margem de segurança)
            self._token_expiration_time = time.time() + data["expires_in"] - 60
            print("Novo token de acesso do IGDB obtido com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter token de acesso do IGDB: {e}")
            return False

    def _get_headers(self):
        """Verifica se o token é válido e retorna os headers para a requisição."""
        # Se o token expirou ou não existe, pega um novo
        if not self._access_token or time.time() >= self._token_expiration_time:
            if not self._get_access_token():
                return None # Retorna None se não conseguir o token

        return {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {self._access_token}"
        }

    def search_games(self, game_name, limit=5):
        """Busca por jogos no IGDB usando o nome."""
        headers = self._get_headers()
        if not headers:
            return None # Retorna None se não tiver autorização

        # Monta a query na linguagem "Apocalypto" do IGDB
        query_data = f'search "{game_name}"; fields name, summary, genres.name, first_release_date, cover.url, screenshots.url; limit {limit}; where category = 0;'

        try:
            response = requests.post(self._api_url + "games", headers=headers, data=query_data)
            response.raise_for_status()

            found_games = response.json()

            # Formata os dados para facilitar o uso no nosso launcher
            formatted_games = []
            for game in found_games:
                formatted_game = {
                    "igdb_id": game.get("id"),
                    "name": game.get("name"),
                    "summary": game.get("summary"),
                    "genres": [genre["name"] for genre in game.get("genres", [])],
                    "release_date": time.strftime('%Y-%m-%d', time.gmtime(game.get("first_release_date", 0))),
                    # Pega a URL da capa e a troca por uma versão de alta resolução
                    "cover_url": game.get("cover", {}).get("url", "").replace("/t_thumb/", "/t_cover_big/"),
                    "screenshot_urls": [ss["url"].replace("/t_thumb/", "/t_screenshot_huge/") for ss in game.get("screenshots", [])]
                }
                formatted_games.append(formatted_game)

            return formatted_games

        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar jogos no IGDB: {e}")
            return None