# ui/pages/servers_page.py
"""Страница мониторинга серверов обновлений"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QStackedWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtGui import QColor
import qtawesome as qta
import time

from .base_page import BasePage
from ui.compat_widgets import SettingsCard, ActionButton, PrimaryActionButton
from ui.theme import get_theme_tokens
from ui.theme_refresh import ThemeRefreshController
from ui.text_catalog import tr as tr_catalog
from updater.update_page_controller import UpdatePageController
from updater.server_status_table_state import ServerStatusTableState
from updater.update_page_view_controller import UpdatePageViewController
from ui.pages.servers_page_settings_build import (
    build_servers_settings_section,
    build_servers_telegram_section,
)
from ui.widgets.win11_controls import Win11ToggleRow

try:
    from qfluentwidgets import (
        BodyLabel, CaptionLabel, StrongBodyLabel,
        PushButton, TransparentPushButton,
        TableWidget,
        FluentIcon, PushSettingCard, SettingCardGroup,
    )
    _HAS_FLUENT = True
except ImportError:
    from PyQt6.QtWidgets import QPushButton, QTableWidget as TableWidget
    BodyLabel = QLabel
    CaptionLabel = QLabel
    StrongBodyLabel = QLabel
    PushButton = QPushButton
    TransparentPushButton = QPushButton
    FluentIcon = None
    PushSettingCard = None  # type: ignore[assignment]
    SettingCardGroup = None  # type: ignore[assignment]
    _HAS_FLUENT = False

from config import APP_VERSION, CHANNEL
from ui.pages.servers_page_update_card import UpdateStatusCard
from ui.pages.servers_page_changelog_card import ChangelogCard



# ═══════════════════════════════════════════════════════════════════════════════
# ИНДЕТЕРМИНИРОВАННАЯ КНОПКА С ПРОГРЕСС-КОЛЬЦОМ (аналог IndeterminateProgressPushButton Pro)
# ═══════════════════════════════════════════════════════════════════════════════

class ServersPage(BasePage):
    """Страница мониторинга серверов обновлений"""

    update_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(
            "Серверы",
            "Мониторинг серверов обновлений",
            parent,
            title_key="page.servers.title",
            subtitle_key="page.servers.subtitle",
        )

        self._tokens = get_theme_tokens()
        self._server_table_state = ServerStatusTableState()
        self._update_controller = UpdatePageController(self)
        self._runtime_initialized = False

        self._build_ui()
        self._apply_page_theme(force=True)
        self._run_runtime_init_once()

    def _tr(self, key: str, default: str) -> str:
        return tr_catalog(key, language=self._ui_language, default=default)

    def _run_runtime_init_once(self) -> None:
        plan = self._update_controller.build_page_init_plan(
            runtime_initialized=self._runtime_initialized,
        )
        if not plan.should_apply_idle_view_state:
            return
        self._runtime_initialized = True
        QTimer.singleShot(
            0,
            lambda action=plan.view_action, elapsed=plan.elapsed_seconds: self._update_controller.apply_idle_view_state(
                view_action=action,
                elapsed_seconds=elapsed,
            ),
        )

    def _apply_page_theme(self, tokens=None, force: bool = False) -> None:
        _ = force
        self._tokens = tokens or get_theme_tokens()
        tokens = self._tokens

        if hasattr(self, "servers_table"):
            try:
                accent_qcolor = QColor(tokens.accent_hex)
                for r in range(self.servers_table.rowCount()):
                    item = self.servers_table.item(r, 0)
                    if item and (item.text() or "").lstrip().startswith("⭐"):
                        item.setForeground(accent_qcolor)
            except Exception:
                pass

    def _render_server_row(self, row: int, server_name: str, status: dict) -> None:
        plan = UpdatePageViewController.build_server_row_plan(
            row_server_name=server_name,
            status=status,
            channel=CHANNEL,
            language=self._ui_language,
        )
        name_item = QTableWidgetItem(plan.server_text)
        if plan.server_accent:
            name_item.setForeground(QColor(self._tokens.accent_hex))
        self.servers_table.setItem(row, 0, name_item)

        status_item = QTableWidgetItem(plan.status_text)
        status_item.setForeground(QColor(*plan.status_color))
        self.servers_table.setItem(row, 1, status_item)
        self.servers_table.setItem(row, 2, QTableWidgetItem(plan.time_text))
        self.servers_table.setItem(row, 3, QTableWidgetItem(plan.extra_text))

    def _refresh_server_rows(self) -> None:
        for entry in self._server_table_state.iter_entries():
            if entry.row < 0 or entry.row >= self.servers_table.rowCount():
                continue
            self._render_server_row(entry.row, entry.server_name, entry.status)

    def set_ui_language(self, language: str) -> None:
        super().set_ui_language(language)

        self.update_card.set_ui_language(self._ui_language)
        self.changelog_card.set_ui_language(self._ui_language)

        self._back_btn.setText(self._tr("page.servers.back.about", "О программе"))
        self._page_title_label.setText(self._tr("page.servers.title", "Серверы"))
        self._servers_title_label.setText(self._tr("page.servers.section.update_servers", "Серверы обновлений"))
        self._legend_active_label.setText(self._tr("page.servers.legend.active", "⭐ активный"))
        self.servers_table.setHorizontalHeaderLabels([
            self._tr("page.servers.table.header.server", "Сервер"),
            self._tr("page.servers.table.header.status", "Статус"),
            self._tr("page.servers.table.header.time", "Время"),
            self._tr("page.servers.table.header.versions", "Версии"),
        ])

        self._settings_card.set_title(self._tr("page.servers.settings.title", "Настройки"))
        title_label = getattr(self._settings_card, "titleLabel", None)
        if title_label is not None:
            title_label.setText(self._tr("page.servers.settings.title", "Настройки"))
        if self._toggle_label is not None:
            self._toggle_label.setText(self._tr("page.servers.settings.auto_check", "Проверять обновления при запуске"))
        if hasattr(self, "_auto_check_card") and self._auto_check_card is not None:
            self._auto_check_card.set_texts(
                self._tr("page.servers.settings.auto_check", "Проверять обновления при запуске"),
                self._tr(
                    "page.servers.settings.auto_check.description",
                    "Автоматически проверять наличие обновлений при старте приложения.",
                ),
            )
        self._version_info_label.setText(
            self._tr("page.servers.settings.version_channel_template", "v{version} · {channel}").format(
                version=APP_VERSION,
                channel=CHANNEL,
            )
        )

        self._tg_card.set_title(self._tr("page.servers.telegram.title", "Проблемы с обновлением?"))
        if self._tg_info_label is not None:
            self._tg_info_label.setText(
                self._tr(
                    "page.servers.telegram.info",
                    "Если возникают трудности с автоматическим обновлением, все версии программы выкладываются в Telegram канале.",
                )
            )
        else:
            try:
                self._tg_card.setContent(
                    self._tr(
                        "page.servers.telegram.info",
                        "Если возникают трудности с автоматическим обновлением, все версии программы выкладываются в Telegram канале.",
                    )
                )
            except Exception:
                pass
        self._tg_btn.setText(self._tr("page.servers.telegram.button.open_channel", "Открыть Telegram канал"))

        self._refresh_server_rows()

    def _build_ui(self):
        # ── Custom header (back link + title) ───────────────────────────
        # Hide base title/subtitle and prevent _retranslate_base_texts
        # from re-showing them (it calls setVisible(bool(text))).
        if self.title_label is not None:
            self._title_key = None
            self.title_label.setText("")
            self.title_label.hide()
        if self.subtitle_label is not None:
            self._subtitle_key = None
            self.subtitle_label.setText("")
            self.subtitle_label.hide()

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(4)

        back_row = QHBoxLayout()
        back_row.setContentsMargins(0, 0, 0, 0)
        back_row.setSpacing(0)

        self._back_btn = TransparentPushButton(parent=self)
        self._back_btn.setText(self._tr("page.servers.back.about", "О программе"))
        self._back_btn.setIcon(qta.icon("fa5s.chevron-left", color="#888"))
        self._back_btn.setIconSize(QSize(12, 12))
        self._back_btn.clicked.connect(self._on_back_to_about)
        back_row.addWidget(self._back_btn)
        back_row.addStretch()
        header_layout.addLayout(back_row)

        try:
            from qfluentwidgets import TitleLabel as _TitleLabel
            self._page_title_label = _TitleLabel(self._tr("page.servers.title", "Серверы"))
        except Exception:
            self._page_title_label = QLabel(self._tr("page.servers.title", "Серверы"))
        header_layout.addWidget(self._page_title_label)

        self.add_widget(header)

        # Update status card
        self.update_card = UpdateStatusCard(language=self._ui_language)
        self.update_card.check_clicked.connect(self._request_check_updates)
        self.add_widget(self.update_card)

        # Changelog card (hidden by default)
        self.changelog_card = ChangelogCard(language=self._ui_language)
        self.changelog_card.install_clicked.connect(self._request_install_update)
        self.changelog_card.dismiss_clicked.connect(self._request_dismiss_update)
        self.add_widget(self.changelog_card)

        # Table header row
        servers_header = QHBoxLayout()
        self._servers_title_label = StrongBodyLabel(
            self._tr("page.servers.section.update_servers", "Серверы обновлений")
        )
        servers_header.addWidget(self._servers_title_label)
        servers_header.addStretch()

        self._legend_active_label = CaptionLabel(self._tr("page.servers.legend.active", "⭐ активный"))
        servers_header.addWidget(self._legend_active_label)

        header_widget = QWidget()
        header_widget.setLayout(servers_header)
        self.add_widget(header_widget)

        # Servers table
        self.servers_table = TableWidget()
        self.servers_table.setColumnCount(4)
        self.servers_table.setRowCount(0)
        self.servers_table.setBorderVisible(True)
        self.servers_table.setBorderRadius(8)
        self.servers_table.setHorizontalHeaderLabels([
            self._tr("page.servers.table.header.server", "Сервер"),
            self._tr("page.servers.table.header.status", "Статус"),
            self._tr("page.servers.table.header.time", "Время"),
            self._tr("page.servers.table.header.versions", "Версии"),
        ])
        header = self.servers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.servers_table.verticalHeader().setVisible(False)
        self.servers_table.verticalHeader().setDefaultSectionSize(36)
        self.servers_table.setEditTriggers(TableWidget.EditTrigger.NoEditTriggers)
        self.servers_table.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.add_widget(self.servers_table, stretch=1)

        # Settings card
        settings_widgets = build_servers_settings_section(
            content_parent=self.content,
            tr_fn=self._tr,
            accent_hex=get_theme_tokens().accent_hex,
            auto_check_enabled=self._update_controller.auto_check_enabled,
            app_version=APP_VERSION,
            channel=CHANNEL,
            has_fluent=_HAS_FLUENT,
            setting_card_group_cls=SettingCardGroup,
            settings_card_cls=SettingsCard,
            win11_toggle_row_cls=Win11ToggleRow,
            switch_button_cls=SwitchButton,
            body_label_cls=BodyLabel,
            caption_label_cls=CaptionLabel,
            qhbox_layout_cls=QHBoxLayout,
            qvbox_layout_cls=QVBoxLayout,
            on_auto_check_toggled=self._on_auto_check_toggled,
        )
        self._settings_card = settings_widgets.card
        self._auto_check_card = settings_widgets.auto_check_card
        self.auto_check_toggle = settings_widgets.auto_check_toggle
        self._toggle_label = settings_widgets.toggle_label
        self._version_info_label = settings_widgets.version_info_label
        self.add_widget(self._settings_card)

        # Telegram card
        telegram_widgets = build_servers_telegram_section(
            tr_fn=self._tr,
            accent_hex=tokens.accent_hex,
            has_fluent=_HAS_FLUENT,
            push_setting_card_cls=PushSettingCard,
            settings_card_cls=SettingsCard,
            body_label_cls=BodyLabel,
            action_button_cls=ActionButton,
            qta_module=qta,
            qhbox_layout_cls=QHBoxLayout,
            qvbox_layout_cls=QVBoxLayout,
            on_open_channel=self._open_telegram_channel,
        )
        self._tg_card = telegram_widgets.card
        self._tg_info_label = telegram_widgets.info_label
        self._tg_btn = telegram_widgets.button
        self.add_widget(self._tg_card)

        self._apply_page_theme(force=True)

    def get_ui_language(self) -> str:
        return self._ui_language

    def reset_server_rows(self) -> None:
        self.servers_table.setRowCount(0)
        self._server_table_state.reset()

    def upsert_server_status(self, server_name: str, status: dict) -> None:
        result = self._server_table_state.upsert(
            server_name,
            status,
            next_row=self.servers_table.rowCount(),
        )
        if result.created:
            self.servers_table.insertRow(result.row)
        self._render_server_row(result.row, server_name, result.status)

    def start_checking(self) -> None:
        self.update_card.start_checking()

    def finish_checking(self, found_update: bool, version: str) -> None:
        self.update_card.stop_checking(found_update, version)

    def show_found_update_source(self, version: str, source: str) -> None:
        self.update_card.show_found_update(version, source)

    def show_update_offer(self, version: str, release_notes: str) -> None:
        self.changelog_card.show_update(version, release_notes)

    def hide_update_offer(self) -> None:
        self.changelog_card.hide()

    def is_update_download_in_progress(self) -> bool:
        return bool(getattr(self.changelog_card, "_is_downloading", False))

    def start_update_download(self, version: str) -> None:
        self.changelog_card.start_download(version)

    def update_download_progress(self, percent: int, done_bytes: int, total_bytes: int) -> None:
        self.changelog_card.update_progress(percent, done_bytes, total_bytes)

    def mark_update_download_complete(self) -> None:
        self.changelog_card.download_complete()

    def mark_update_download_failed(self, error: str) -> None:
        self.changelog_card.download_failed(error)

    def show_update_download_error(self) -> None:
        self.update_card.show_download_error()

    def show_update_deferred(self, version: str) -> None:
        self.update_card.show_deferred(version)

    def show_checked_ago(self, elapsed: float) -> None:
        self.update_card.show_checked_ago(elapsed)

    def show_manual_hint(self) -> None:
        self.update_card.show_manual_hint()

    def show_auto_enabled_hint(self) -> None:
        self.update_card.show_auto_enabled_hint()

    def hide_update_status_card(self) -> None:
        self.update_card.hide()

    def show_update_status_card(self) -> None:
        self.update_card.show()

    def set_update_check_enabled(self, enabled: bool) -> None:
        self.update_card.check_btn.setEnabled(bool(enabled))

    def present_startup_update(self, version: str, release_notes: str, *, install_after_show: bool = True) -> bool:
        return self._update_controller.present_startup_update(
            version,
            release_notes,
            install_after_show=install_after_show,
        )

    def _request_check_updates(self) -> None:
        self._update_controller.request_manual_check()

    def _request_install_update(self) -> None:
        self._update_controller.install_update()

    def _request_dismiss_update(self) -> None:
        self._update_controller.dismiss_update()

    def _open_telegram_channel(self):
        result = UpdatePageViewController.open_update_channel(CHANNEL)
        if not result.ok:
            try:
                from qfluentwidgets import InfoBar
            except Exception:
                InfoBar = None
            if InfoBar is not None:
                InfoBar.warning(
                    title=self._tr("page.servers.telegram.error.title", "Ошибка"),
                    content=self._tr(
                        "page.servers.telegram.error.open_channel",
                        "Не удалось открыть Telegram канал:\n{error}",
                    ).format(error=result.message),
                    parent=self.window(),
                )

    def _on_back_to_about(self):
        try:
            from ui.page_names import PageName
            win = self.window()
            if hasattr(win, 'show_page'):
                win.show_page(PageName.ABOUT)
        except Exception:
            pass

    def _on_auto_check_toggled(self, enabled: bool):
        self._update_controller.set_auto_check_enabled(bool(enabled))

    def cleanup(self):
        self._update_controller.cleanup()
