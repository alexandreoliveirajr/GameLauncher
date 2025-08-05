# core/artwork_manager.py

import os
import requests
import logging

# Define o diretório base para salvar as artes da Steam
ARTWORK_BASE_DIR = os.path.join("assets", "steam")

def download_steam_artwork(app_id):
    """
    Baixa a capa, o header e o hero de um jogo da Steam usando seu AppID.
    Retorna um dicionário com os caminhos locais para as imagens baixadas.
    """
    if not app_id:
        return {}

    # Cria o diretório específico para este AppID, se não existir
    game_artwork_dir = os.path.join(ARTWORK_BASE_DIR, str(app_id))
    os.makedirs(game_artwork_dir, exist_ok=True)

    urls = {
        "image_path": f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900.jpg",
        "header_path": f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
        "background_path": f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_hero.jpg"
    }

    local_paths = {}

    for key, url in urls.items():
        # Define o nome do arquivo local (ex: cover.jpg, header.jpg)
        file_name = f"{key.split('_')[0]}.jpg"
        local_path = os.path.join(game_artwork_dir, file_name)

        # Se o arquivo já não existir, tenta fazer o download
        if not os.path.exists(local_path):
            try:
                response = requests.get(url, stream=True, timeout=10)
                # Verifica se a imagem existe (status 200) e se o conteúdo não é uma página de erro
                if response.status_code == 200 and 'text/html' not in response.headers.get('content-type', ''):
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    logging.info(f"Arte baixada com sucesso: {local_path}")
                    local_paths[key] = local_path
                else:
                    logging.warning(f"Não foi possível encontrar a arte para {app_id} em {url} (Status: {response.status_code})")
            except requests.RequestException as e:
                logging.error(f"Erro de rede ao baixar {url}: {e}")
        else:
            # Se o arquivo já existe, apenas adiciona seu caminho ao dicionário de retorno
            local_paths[key] = local_path
            
    return local_paths
