# core/steam_web_api.py

import requests
import logging

# URL base para a API da Steam
API_BASE_URL = "https://api.steampowered.com"

def get_player_summary(api_key, steam_id_64):
    """
    Busca o resumo do perfil de um jogador (nome, avatar, status).
    Retorna um dicionário com os dados do jogador, ou None em caso de erro.
    """
    if not api_key or not steam_id_64:
        logging.warning("API Key ou SteamID64 da Steam não fornecidos.")
        return None

    endpoint = f"{API_BASE_URL}/ISteamUser/GetPlayerSummaries/v2/"
    params = {
        'key': api_key,
        'steamids': steam_id_64
    }

    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        players = data.get('response', {}).get('players', [])
        if players:
            logging.info(f"Resumo do perfil de {players[0].get('personaname')} obtido com sucesso.")
            return players[0]
        else:
            logging.warning(f"Nenhum jogador encontrado para o SteamID {steam_id_64}.")
            return None
            
    except requests.RequestException as e:
        logging.error(f"Erro de rede ao buscar o resumo do perfil da Steam: {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar o resumo do perfil da Steam: {e}")
        return None

def get_owned_games(api_key, steam_id_64):
    """
    Busca a lista completa de jogos que um jogador possui, incluindo tempo de jogo.
    Retorna uma lista de dicionários de jogos, ou None em caso de erro.
    """
    if not api_key or not steam_id_64:
        logging.warning("API Key ou SteamID64 da Steam não fornecidos.")
        return None

    endpoint = f"{API_BASE_URL}/IPlayerService/GetOwnedGames/v1/"
    params = {
        'key': api_key,
        'steamid': steam_id_64,
        'include_appinfo': True,  # Inclui nome e ícones dos jogos
        'include_played_free_games': True # Inclui jogos gratuitos que foram jogados
    }

    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        games = data.get('response', {}).get('games', [])
        game_count = data.get('response', {}).get('game_count', 0)
        
        if game_count > 0:
            logging.info(f"Lista de {game_count} jogos possuídos obtida com sucesso.")
            return games
        else:
            logging.warning(f"Nenhum jogo encontrado para o SteamID {steam_id_64}. O perfil pode ser privado.")
            return [] # Retorna lista vazia se não houver jogos

    except requests.RequestException as e:
        logging.error(f"Erro de rede ao buscar a lista de jogos da Steam: {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar a lista de jogos da Steam: {e}")
        return None
