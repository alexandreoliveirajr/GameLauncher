# utils/path_utils.py
import os
import sys

def get_app_root_path():
    """Retorna o caminho absoluto para a pasta raiz do projeto."""
    # Se a aplicação estiver congelada (pyinstaller), pega o diretório do executável
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Senão, pega o diretório onde o main.py está
    else:
        return os.path.dirname(os.path.abspath(sys.argv[0]))

def get_absolute_path(relative_path):
    """
    Converte um caminho relativo (como os salvos no DB) para um caminho absoluto.
    Retorna None se o caminho de entrada for None ou vazio.
    """
    if not relative_path:
        return None
    
    # Se o caminho já for absoluto, retorna ele mesmo
    if os.path.isabs(relative_path):
        return relative_path

    # Combina o caminho raiz da aplicação com o caminho relativo
    return os.path.join(get_app_root_path(), relative_path)