# core/steam_app_list.py

import os
import json
import requests
import logging
import time
from difflib import get_close_matches

CACHE_FILE = "steam_app_cache.json"
CACHE_EXPIRATION_SECONDS = 60 * 60 * 24 * 7 # Cache por 7 dias

def _is_cache_valid():
    """Verifica se o cache existe e não está expirado."""
    if not os.path.exists(CACHE_FILE):
        return False
    
    cache_age = time.time() - os.path.getmtime(CACHE_FILE)
    return cache_age < CACHE_EXPIRATION_SECONDS

def update_steam_app_list():
    """Baixa e salva a lista de todos os aplicativos da Steam."""
    logging.info("Tentando atualizar a lista de aplicativos da Steam...")
    if _is_cache_valid():
        logging.info("Cache da lista de aplicativos da Steam ainda é válido. Nenhuma atualização necessária.")
        return True

    try:
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        response = requests.get(url, timeout=30)
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)
        
        data = response.json()
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
        logging.info(f"Lista de aplicativos da Steam atualizada com sucesso. {len(data.get('applist', {}).get('apps', []))} apps cacheados.")
        return True
    except requests.RequestException as e:
        logging.error(f"Erro ao baixar a lista de aplicativos da Steam: {e}")
        return False
    except json.JSONDecodeError:
        logging.error("Erro ao decodificar a resposta JSON da API da Steam.")
        return False

def find_appid_by_name(game_name):
    """
    Encontra o AppID mais provável para um nome de jogo usando o cache local.
    Retorna o AppID como string, ou None se não encontrar.
    """
    if not os.path.exists(CACHE_FILE):
        logging.warning("Cache da lista de aplicativos não encontrado. Execute update_steam_app_list() primeiro.")
        return None

    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load()

    apps = data.get('applist', {}).get('apps', [])
    if not apps:
        return None

    # Cria um dicionário para busca rápida: {nome_em_minusculo: appid}
    app_map = {app['name'].lower(): str(app['appid']) for app in apps if app.get('name')}
    
    # 1. Tenta uma busca exata (ignorando maiúsculas/minúsculas)
    lower_game_name = game_name.lower()
    if lower_game_name in app_map:
        logging.info(f"Encontrada correspondência exata para '{game_name}': AppID {app_map[lower_game_name]}")
        return app_map[lower_game_name]

    # 2. Se falhar, tenta uma busca por aproximação (fuzzy search)
    all_names = list(app_map.keys())
    best_matches = get_close_matches(lower_game_name, all_names, n=1, cutoff=0.8)
    
    if best_matches:
        best_match_name = best_matches[0]
        appid = app_map[best_match_name]
        logging.info(f"Encontrada correspondência aproximada para '{game_name}': '{best_match_name}' (AppID: {appid})")
        return appid
        
    logging.warning(f"Nenhuma correspondência encontrada para o jogo '{game_name}' na lista da Steam.")
    return None

