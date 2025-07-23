# core/theme.py

from PyQt5.QtGui import QColor

# Dicionário para o nosso tema escuro padrão
THEME_DARK = {
    # Cores principais
    "background": QColor("#1e1e1e"),
    "card": QColor("#2e2e2e"),
    "card_border": QColor("#3a3d40"),
    
    # Cores de texto
    "text_primary": QColor("#ffffff"),
    "text_secondary": QColor("#ccc"),
    "text_placeholder": QColor("#888"),
    "text_inverted": QColor("#000000"),

    # Cores de ênfase (accent)
    "accent": QColor("#4a90e2"),
    "accent_success": QColor("#2c9a48"),
    "accent_success_hover": QColor("#36b558"),

    # Cores de componentes
    "button_neutral": QColor("#444"),
    "button_options": QColor("#2a2a2a"),
    "button_options_hover": QColor("#3a3a3a"),
    "scrollbar": QColor("#4a4a4a"),
    "menu_background": QColor("#2a2d30"),

    # Cores com transparência
    "panel_background": QColor(42, 45, 48, 191),    # rgba(42, 45, 48, 0.75)
    "overlay_background": QColor(20, 20, 22, 166), # rgba(20, 20, 22, 0.65)

    "background_darker": QColor("#111111"),
    "input_background": QColor("#333333"),
    "input_border": QColor("#555555"),
    "accent_success_bright": QColor("#33cc33")
}

# No futuro, para o tema claro, basta criar um novo dicionário aqui
THEME_LIGHT = {
    # Exemplo de como seria
    "background": QColor("#f0f0f0"),
    "card": QColor("#ffffff"),
    "card_border": QColor("#dcdcdc"),
    "text_primary": QColor("#000000"),
    # ... etc
}

# Definimos o tema atual que será usado por todo o aplicativo
current_theme = THEME_DARK