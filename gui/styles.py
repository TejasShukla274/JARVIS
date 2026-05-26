# gui/styles.py
# ─────────────────────────────────────────────────────────────────────────────
# JARVIS Centralised Design System — Futuristic Dark Theme
# All panels, buttons, and widgets reference these constants.
# ─────────────────────────────────────────────────────────────────────────────

# ── Color Palette ────────────────────────────────────────────────────────────
BG_DEEPEST     = "#020810"
BG_DARK        = "#050a14"
BG_PANEL       = "rgba(6, 14, 22, 225)"
BG_CARD        = "rgba(4, 10, 18, 210)"
BG_INPUT       = "#060e18"

CYAN           = "#00e5ff"
CYAN_DIM       = "rgba(0, 229, 255, 90)"
CYAN_GLOW      = "rgba(0, 229, 255, 40)"
CYAN_FAINT     = "rgba(0, 229, 255, 18)"

GREEN          = "#00ffaa"
GREEN_DIM      = "rgba(0, 255, 170, 70)"
GREEN_GLOW     = "rgba(0, 255, 170, 30)"

RED            = "#ff4b6e"
RED_DIM        = "rgba(255, 75, 110, 50)"

AMBER          = "#ffaa00"
AMBER_DIM      = "rgba(255, 170, 0, 50)"

WHITE          = "#eafaff"
WHITE_DIM      = "rgba(255, 255, 255, 150)"
WHITE_FAINT    = "rgba(255, 255, 255, 60)"

FONT_FAMILY    = "Consolas"

# ── Reusable Style Strings ───────────────────────────────────────────────────

PANEL_STYLE = f"""
    QFrame, .QWidget {{
        background-color: {BG_PANEL};
        border: 1px solid {CYAN_GLOW};
        border-radius: 12px;
    }}
"""

GLASS_PANEL = f"""
    QFrame {{
        background-color: {BG_PANEL};
        border: 1px solid {CYAN_GLOW};
        border-radius: 12px;
    }}
"""

CARD_STYLE = f"""
    QFrame, QWidget {{
        background-color: {BG_CARD};
        border: 1px solid {CYAN_FAINT};
        border-radius: 8px;
    }}
"""

INPUT_STYLE = f"""
    QLineEdit, QSpinBox, QDateTimeEdit, QTimeEdit, QComboBox {{
        color: white;
        background-color: {BG_INPUT};
        border: 1px solid {CYAN_DIM};
        border-radius: 6px;
        padding: 8px;
        font-family: {FONT_FAMILY};
    }}
    QComboBox QAbstractItemView {{
        color: white;
        background-color: {BG_INPUT};
        selection-background-color: {CYAN_GLOW};
    }}
"""

SCROLL_STYLE = "border: none; background: transparent;"


def button_style(color=CYAN, radius=8):
    """Generates a futuristic neon button stylesheet."""
    return f"""
        QPushButton {{
            color: {color};
            background-color: rgba(255, 255, 255, 6);
            border: 1px solid {color};
            border-radius: {radius}px;
            padding: 9px 16px;
            font-family: {FONT_FAMILY};
            font-weight: bold;
            font-size: 10px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 229, 255, 30);
            border: 1px solid {color};
        }}
        QPushButton:pressed {{
            background-color: rgba(0, 229, 255, 55);
        }}
        QPushButton:disabled {{
            color: {WHITE_FAINT};
            border-color: {WHITE_FAINT};
        }}
    """


def nav_button_style(color=CYAN, active=False):
    """Sidebar navigation button."""
    bg = f"rgba(0, 229, 255, 22)" if active else "transparent"
    border = color if active else "rgba(255, 255, 255, 8)"
    text_color = color if active else "rgba(255, 255, 255, 200)"
    return f"""
        QPushButton {{
            color: {text_color};
            background-color: {bg};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 12px 14px;
            text-align: left;
            font-family: {FONT_FAMILY};
            font-weight: bold;
            font-size: 9px;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 229, 255, 18);
            border: 1px solid {color};
            color: {color};
        }}
    """


SIDEBAR_STYLE = f"""
    QWidget {{
        background-color: rgba(4, 8, 16, 240);
        border: 1px solid {CYAN_GLOW};
        border-radius: 14px;
    }}
"""

HEADER_LABEL = f"color: {CYAN}; letter-spacing: 2px; border: none; background: transparent; font-family: {FONT_FAMILY};"
SUBHEADER_LABEL = f"color: {WHITE_FAINT}; letter-spacing: 1px; border: none; background: transparent; font-family: {FONT_FAMILY};"
SECTION_LABEL = f"color: {GREEN}; letter-spacing: 1px; border: none; background: transparent; font-family: {FONT_FAMILY};"
BODY_LABEL = f"color: {WHITE}; border: none; background: transparent; font-family: {FONT_FAMILY};"
DIM_LABEL = f"color: {WHITE_DIM}; border: none; background: transparent; font-family: {FONT_FAMILY};"

TABLE_STYLE = f"""
    QTableWidget {{
        color: white;
        background-color: rgba(2, 8, 14, 190);
        border: 1px solid {CYAN_GLOW};
        gridline-color: {CYAN_FAINT};
        font-family: {FONT_FAMILY};
    }}
    QHeaderView::section {{
        color: {CYAN};
        background-color: {BG_DARK};
        border: none;
        padding: 5px;
        font-family: {FONT_FAMILY};
        font-weight: bold;
    }}
"""

SLIDER_STYLE = f"""
    QSlider {{ border: none; background: transparent; }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: rgba(255,255,255,30);
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        margin: -5px 0;
        border-radius: 8px;
        background: {CYAN};
    }}
    QSlider::sub-page:horizontal {{
        background: {CYAN};
        border-radius: 3px;
    }}
"""

CHECKBOX_STYLE = f"""
    QCheckBox {{
        color: white;
        border: none;
        font-family: {FONT_FAMILY};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
    }}
"""
