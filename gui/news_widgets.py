# gui/news_widgets.py
# ─────────────────────────────────────────────────────────────────────────────
# Custom News items, loading skeletons, and carousels for JARVIS HUD.
# ─────────────────────────────────────────────────────────────────────────────

import os
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGraphicsOpacityEffect
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, pyqtProperty

from gui import styles
from services.news_services import get_cached_news, fetch_and_cache_news, is_news_cache_expired


class RoundedImageLabel(QLabel):
    """Futuristic wireframe image label that crops images to rounded corners."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_data = None
        self.setMinimumSize(96, 68)
        self.setMaximumSize(96, 68)

    def set_pixmap(self, pixmap):
        self.pixmap_data = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Rounded clipping path
        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 6, 6)
        painter.setClipPath(path)

        if self.pixmap_data and not self.pixmap_data.isNull():
            # Scale and draw image
            scaled = self.pixmap_data.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            # Center offset (integer source rect to match QRect target)
            dx = (scaled.width() - self.width()) // 2
            dy = (scaled.height() - self.height()) // 2
            # Use explicit integer coordinate overload — avoids QRect/QRectF mismatch in PyQt5
            painter.drawPixmap(
                0, 0, self.width(), self.height(),
                scaled,
                dx, dy, self.width(), self.height()
            )
        else:
            # Draw glowing cyan hologram grid/wireframe
            painter.setPen(QPen(QColor(0, 229, 255, 45), 1))
            painter.setBrush(QColor(2, 10, 18, 160))
            painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 6, 6)
            
            # Decorative grid lines
            painter.setPen(QPen(QColor(0, 229, 255, 20), 0.5))
            painter.drawLine(0, 0, self.width(), self.height())
            painter.drawLine(self.width(), 0, 0, self.height())
            painter.drawEllipse(QRectF(self.width() * 0.2, self.height() * 0.2, self.width() * 0.6, self.height() * 0.6))
            
            painter.setPen(QPen(QColor(0, 229, 255, 120), 1))
            painter.setFont(QFont(styles.FONT_FAMILY, 6, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, "HUD FEED")


class NewsCard(QFrame):
    """
    Hoverable, futuristic glassmorphic news card.
    Contains local thumbnail image, source tag, headline, time and summary.
    """

    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.is_hovered = False
        
        # Premium card container
        self.setObjectName("NewsCard")
        self.setStyleSheet(f"""
            QFrame#NewsCard {{
                background-color: {styles.BG_CARD};
                border: 1px solid {styles.CYAN_FAINT};
                border-radius: 10px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # 1. Left side rounded thumbnail
        self.image_label = RoundedImageLabel(self)
        if article.get("thumbnail") and os.path.exists(article["thumbnail"]):
            pix = QPixmap(article["thumbnail"])
            if not pix.isNull():
                self.image_label.set_pixmap(pix)
        layout.addWidget(self.image_label)

        # 2. Right side text information
        txt_layout = QVBoxLayout()
        txt_layout.setContentsMargins(0, 0, 0, 0)
        txt_layout.setSpacing(2)

        # Source / Time bar
        meta_layout = QHBoxLayout()
        meta_layout.setContentsMargins(0, 0, 0, 0)
        
        source_lbl = QLabel(article.get("source", "WORLD NEWS").upper())
        source_lbl.setFont(QFont(styles.FONT_FAMILY, 7, QFont.Bold))
        source_lbl.setStyleSheet(f"color: {styles.GREEN}; background: transparent; border: none;")
        meta_layout.addWidget(source_lbl)

        meta_layout.addStretch()

        time_lbl = QLabel(article.get("time", "Recent"))
        time_lbl.setFont(QFont(styles.FONT_FAMILY, 7))
        time_lbl.setStyleSheet(styles.DIM_LABEL)
        meta_layout.addWidget(time_lbl)

        txt_layout.addLayout(meta_layout)

        # Headline
        headline_lbl = QLabel(article.get("headline", ""))
        headline_lbl.setFont(QFont(styles.FONT_FAMILY, 9, QFont.Bold))
        headline_lbl.setStyleSheet(f"color: {styles.WHITE}; background: transparent; border: none;")
        headline_lbl.setWordWrap(True)
        headline_lbl.setMinimumHeight(28)
        headline_lbl.setMaximumHeight(32)
        txt_layout.addWidget(headline_lbl)

        # Short Summary
        summary_lbl = QLabel(article.get("summary", ""))
        summary_lbl.setFont(QFont(styles.FONT_FAMILY, 8))
        summary_lbl.setStyleSheet(styles.DIM_LABEL)
        summary_lbl.setWordWrap(True)
        summary_lbl.setMinimumHeight(24)
        summary_lbl.setMaximumHeight(28)
        txt_layout.addWidget(summary_lbl)

        layout.addLayout(txt_layout)

    def enterEvent(self, event):
        """Micro-animations: neon hover border glow."""
        self.is_hovered = True
        self.setStyleSheet(f"""
            QFrame#NewsCard {{
                background-color: rgba(6, 18, 30, 240);
                border: 1px solid {styles.CYAN};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Micro-animations: reset glow."""
        self.is_hovered = False
        self.setStyleSheet(f"""
            QFrame#NewsCard {{
                background-color: {styles.BG_CARD};
                border: 1px solid {styles.CYAN_FAINT};
            }}
        """)
        super().leaveEvent(event)


class NewsLoadingSkeleton(QFrame):
    """Shimmering loading mock widget displaying placeholder boxes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shimmer_alpha = 40
        self.shimmer_dir = 1
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.BG_CARD};
                border: 1px solid {styles.CYAN_FAINT};
                border-radius: 10px;
            }}
        """)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.shimmer)
        self.timer.start(50)  # Shimmers quickly

    def shimmer(self):
        self.shimmer_alpha += 4 * self.shimmer_dir
        if self.shimmer_alpha > 120:
            self.shimmer_alpha = 120
            self.shimmer_dir = -1
        elif self.shimmer_alpha < 30:
            self.shimmer_alpha = 30
            self.shimmer_dir = 1
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()

        # Skeleton thumbnail box
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 229, 255, self.shimmer_alpha))
        painter.drawRoundedRect(QRectF(10, 8, 96, 68), 6, 6)

        # Meta tags
        painter.setBrush(QColor(0, 255, 170, self.shimmer_alpha))
        painter.drawRoundedRect(QRectF(118, 10, 70, 8), 2, 2)
        painter.setBrush(QColor(0, 229, 255, self.shimmer_alpha - 10))
        painter.drawRoundedRect(QRectF(w - 60, 10, 50, 8), 2, 2)

        # Title line 1
        painter.setBrush(QColor(255, 255, 255, self.shimmer_alpha))
        painter.drawRoundedRect(QRectF(118, 24, w - 130, 10), 3, 3)
        # Title line 2
        painter.drawRoundedRect(QRectF(118, 38, w * 0.6, 10), 3, 3)

        # Summary line
        painter.setBrush(QColor(255, 255, 255, self.shimmer_alpha - 15))
        painter.drawRoundedRect(QRectF(118, 54, w - 150, 8), 2, 2)


class NewsCarousel(QFrame):
    """
    Continuous auto-scrolling news dashboard ribbon.
    Shows 2 news cards side-by-side. Connects to the caching RSS engine.
    Uses fade transition effects natively.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.articles = []
        self.current_index = 0

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # Load immediate cached state
        self.refresh_articles()

        # Setup auto-scroll transition timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.slide_next)
        self.scroll_timer.start(7000)  # Transitions cards every 7 seconds

        # Setup fetch/caching periodic check timer
        self.fetch_timer = QTimer(self)
        self.fetch_timer.timeout.connect(self.run_background_fetch)
        self.fetch_timer.start(1000 * 60 * 3)  # Every 3 minutes checks cache staleness

        # On startup, immediately fetch if today's cache is missing/stale
        self.run_background_fetch()

    def refresh_articles(self):
        """Loads items from the local news cache immediately."""
        self.articles = get_cached_news()
        if self.articles:
            self.render_cards()
        else:
            self.render_skeletons()
            # Start background retrieval immediately if cache is empty
            self.run_background_fetch(force=True)

    def render_skeletons(self):
        """Renders 2 shimmering skeletons side-by-side."""
        self.clear_layout()
        skel1 = NewsLoadingSkeleton()
        skel2 = NewsLoadingSkeleton()
        self.layout.addWidget(skel1)
        self.layout.addWidget(skel2)

    def render_cards(self):
        """Renders 2 news cards side-by-side based on self.current_index."""
        if not self.articles:
            return
            
        self.clear_layout()
        
        # Get 2 sequential articles (wrapping around indices)
        idx1 = self.current_index % len(self.articles)
        idx2 = (self.current_index + 1) % len(self.articles)

        card1 = NewsCard(self.articles[idx1])
        card2 = NewsCard(self.articles[idx2])

        self.layout.addWidget(card1, stretch=1)
        self.layout.addWidget(card2, stretch=1)

        # Smooth fade-in animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(0.2)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def slide_next(self):
        """Increments index and transitions cleanly."""
        if not self.articles:
            return
        self.current_index = (self.current_index + 2) % len(self.articles)
        self.render_cards()

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def run_background_fetch(self, force=False):
        """Asynchronously updates caching values to prevent cockpit startup delays."""
        if force or is_news_cache_expired():
            import threading
            t = threading.Thread(target=self._async_fetch_job, daemon=True)
            t.start()

    def _async_fetch_job(self):
        """Background thread RSS worker."""
        try:
            fetch_and_cache_news()
            QTimer.singleShot(0, self.refresh_articles)
        except Exception as e:
            print("Background news fetch failed:", e)
