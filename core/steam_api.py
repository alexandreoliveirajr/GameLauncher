# core/steam_api.py

import os
import re
import sys
import json
import requests
from PIL import Image
from io import BytesIO

def get_app_root_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- NOVAS FUNÇÕES PARA A LISTA MESTRA DE APPS ---

def update_steam_app_list(app_list_file="steam_app_list.json"):
    """Baixa a lista completa de apps da Steam e salva localmente."""
    print("Tentando atualizar a lista de aplicativos da Steam... (Isso pode levar um momento)")
    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Salva o arquivo na pasta raiz do projeto
        file_path = os.path.join(get_app_root_path(), app_list_file)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data['applist']['apps'], f, indent=4)
            
        print(f"Lista de aplicativos da Steam atualizada com sucesso! {len(data['applist']['apps'])} apps encontrados.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a lista de apps da Steam: {e}")
        return False

def find_appid_by_name(game_name, app_list_file="steam_app_list.json"):
    """Procura por uma AppID em um arquivo de lista de apps local."""
    file_path = os.path.join(get_app_root_path(), app_list_file)
    if not os.path.exists(file_path):
        return None # Retorna None se a lista de apps não foi baixada

    with open(file_path, "r", encoding="utf-8") as f:
        apps = json.load(f)

    # Procura por uma correspondência exata (ignorando maiúsculas/minúsculas)
    game_name_lower = game_name.lower()
    for app in apps:
        if app['name'].lower() == game_name_lower:
            print(f"Correspondência exata encontrada: '{app['name']}' -> AppID {app['appid']}")
            return str(app['appid'])
    
    print(f"Nenhuma correspondência exata encontrada para '{game_name}'. Tentando busca parcial...")
    # Se não encontrar, procura por uma correspondência parcial
    for app in apps:
        if game_name_lower in app['name'].lower():
            print(f"Correspondência parcial encontrada: '{app['name']}' -> AppID {app['appid']}")
            return str(app['appid'])

    return None

# --- FUNÇÕES ANTIGAS (CONTINUAM IGUAIS) ---

def find_steam_app_id(game_folder_path):
    # ... (código igual)
    try:
        appid_file_path = os.path.join(game_folder_path, "steam_appid.txt")
        if os.path.exists(appid_file_path):
            with open(appid_file_path, "r") as f: content = f.read().strip()
            if content.isdigit(): return content
    except Exception as e: print(f"Erro ao ler steam_appid.txt: {e}")
    try:
        steamapps_path = os.path.dirname(game_folder_path); game_folder_name = os.path.basename(game_folder_path)
        if os.path.basename(steamapps_path) == "common": steamapps_path = os.path.dirname(steamapps_path)
        if os.path.basename(steamapps_path) == "steamapps":
            for filename in os.listdir(steamapps_path):
                if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                    try:
                        with open(os.path.join(steamapps_path, filename), "r", encoding="utf-8") as f: content = f.read()
                        if f'"installdir"\t\t"{game_folder_name}"' in content:
                            app_id_match = re.search(r'"appid"\t\t"(\d+)"', content)
                            if app_id_match: return app_id_match.group(1)
                    except Exception: continue
    except Exception as e: print(f"Erro ao procurar por manifestos: {e}")
    return None

def download_steam_artwork(app_id, output_folder_name="steam_artwork"):
    # ... (código igual)
    if not app_id: return None
    cover_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900.jpg"
    background_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_hero.jpg"
    base_path = get_app_root_path()
    artwork_folder = os.path.join(base_path, output_folder_name, app_id)
    if not os.path.exists(artwork_folder): os.makedirs(artwork_folder)
    artwork_paths = {}
    try:
        response = requests.get(cover_url, stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)); cover_path = os.path.join(artwork_folder, "cover.png")
            image.save(cover_path, "PNG"); artwork_paths["image"] = cover_path; print(f"Capa (pôster) baixada para: {cover_path}")
    except requests.exceptions.RequestException as e: print(f"Não foi possível baixar a capa para o AppID {app_id}: {e}")
    try:
        response = requests.get(background_url, stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)); background_path = os.path.join(artwork_folder, "background.png")
            image.save(background_path, "PNG"); artwork_paths["background"] = background_path; print(f"Fundo (hero) baixado para: {background_path}")
    except requests.exceptions.RequestException as e: print(f"Não foi possível baixar o fundo para o AppID {app_id}: {e}")
    return artwork_paths if artwork_paths else None