# ui/pages/dpi_settings_page.py
"""Страница настроек DPI"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from .base_page import BasePage
from ui.compat_widgets import SettingsCard, ActionButton
from ui.text_catalog import tr as tr_catalog
from ui.theme import get_theme_tokens
from ui.widgets.win11_controls import (
    Win11ComboRow,
    Win11NumberRow,
    Win11RadioOption,
    Win11ToggleRow,
)
from log import log

try:
    from qfluentwidgets import StrongBodyLabel, CaptionLabel as _CaptionLabel
except ImportError:
    StrongBodyLabel = QLabel  # type: ignore[assignment,misc]
    _CaptionLabel = QLabel  # type: ignore[assignment,misc]


def _build_theme_refresh_key(tokens) -> tuple[str, str, str]:
    return (str(tokens.theme_name), str(tokens.accent_hex), str(tokens.font_family_qss))


class DpiSettingsPage(BasePage):
    """Страница настроек DPI"""

    launch_method_changed = pyqtSignal(str)
    filters_changed = pyqtSignal()  # Сигнал при изменении фильтров
    
    def __init__(self, parent=None):
        super().__init__(
            "Настройки DPI",
            "Параметры обхода блокировок",
            parent,
            title_key="page.dpi_settings.title",
            subtitle_key="page.dpi_settings.subtitle",
        )
        self._method_card = None
        self._method_desc_label = None
        self._zapret1_header = None
        self._orchestra_label = None
        self._advanced_desc_label = None
        self._applying_theme_styles = False
        self._last_theme_refresh_key: tuple[str, str, str] | None = None
        self._theme_refresh_pending_when_hidden = False
        self.enable_deferred_ui_build(after_build=self._after_ui_built)

    def _after_ui_built(self) -> None:
        self._load_settings()

    def _tr(self, key: str, default: str, **kwargs) -> str:
        text = tr_catalog(key, language=self._ui_language, default=default)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def _apply_theme_styles(self, tokens=None) -> None:
        theme_tokens = tokens or get_theme_tokens()
        try:
            if hasattr(self, "zapret2_header") and self.zapret2_header is not None:
                self.zapret2_header.setStyleSheet(
                    f"color: {theme_tokens.accent_hex};"
                )
        except Exception:
            pass

        try:
            if self._zapret1_header is not None:
                self._zapret1_header.setStyleSheet("color: #ff9800;")
        except Exception:
            pass

        try:
            if self._orchestra_label is not None:
                self._orchestra_label.setStyleSheet("color: #9c27b0;")
        except Exception:
            pass

        try:
            if self._advanced_desc_label is not None:
                self._advanced_desc_label.setStyleSheet("color: #ff9800;")
        except Exception:
            pass

        try:
            if hasattr(self, "separator2") and self.separator2 is not None:
                self.separator2.setStyleSheet(f"background-color: {theme_tokens.divider_strong}; margin: 8px 0;")
        except Exception:
            pass

    def changeEvent(self, event):  # noqa: N802 (Qt override)
        try:
            if event.type() in (QEvent.Type.StyleChange, QEvent.Type.PaletteChange):
                if self._applying_theme_styles:
                    return super().changeEvent(event)
                tokens = get_theme_tokens()
                theme_key = _build_theme_refresh_key(tokens)
                if theme_key == self._last_theme_refresh_key:
                    return super().changeEvent(event)
                if not self.isVisible():
                    self._theme_refresh_pending_when_hidden = True
                    return super().changeEvent(event)
                self._applying_theme_styles = True
                try:
                    self._last_theme_refresh_key = theme_key
                    self._apply_theme_styles(tokens)
                finally:
                    self._applying_theme_styles = False
        except Exception:
            pass
        super().changeEvent(event)

    def showEvent(self, event):  # noqa: N802 (Qt override)
        super().showEvent(event)
        if not self._theme_refresh_pending_when_hidden:
            return
        self._theme_refresh_pending_when_hidden = False
        tokens = get_theme_tokens()
        theme_key = _build_theme_refresh_key(tokens)
        if theme_key == self._last_theme_refresh_key:
            return
        self._applying_theme_styles = True
        try:
            self._last_theme_refresh_key = theme_key
            self._apply_theme_styles(tokens)
        finally:
            self._applying_theme_styles = False
        
    def _build_ui(self):
        """Строит UI страницы"""
        
        # Метод запуска
        method_card = SettingsCard(
            self._tr(
                "page.dpi_settings.card.launch_method",
                "Метод запуска стратегий (режим работы программы)",
            )
        )
        self._method_card = method_card
        method_layout = QVBoxLayout()
        method_layout.setSpacing(10)
        
        method_desc = _CaptionLabel(
            self._tr("page.dpi_settings.launch_method.desc", "Выберите способ запуска обхода блокировок")
        )
        self._method_desc_label = method_desc
        method_layout.addWidget(method_desc)

        # ═══════════════════════════════════════
        # ZAPRET 2 (winws2.exe)
        # ═══════════════════════════════════════
        self.zapret2_header = StrongBodyLabel(
            self._tr("page.dpi_settings.section.z2", "Zapret 2 (winws2.exe)")
        )
        self.zapret2_header.setContentsMargins(0, 8, 0, 4)
        method_layout.addWidget(self.zapret2_header)

        # Zapret 2 (direct) - рекомендуется
        self.method_direct = Win11RadioOption(
            self._tr("page.dpi_settings.method.direct_z2.title", "Zapret 2"),
            self._tr(
                "page.dpi_settings.method.direct_z2.desc",
                "Режим со второй версией Zapret (winws2.exe) + готовые пресеты для быстрого запуска. Поддерживает кастомный lua-код чтобы писать свои стратегии.",
            ),
            icon_name="mdi.rocket-launch",
            recommended=True,
            recommended_badge=self._tr("page.dpi_settings.option.recommended", "рекомендуется"),
        )
        self.method_direct.clicked.connect(lambda: self._select_method("direct_zapret2"))
        method_layout.addWidget(self.method_direct)

        # Оркестратор Zapret 2 (direct с другим набором стратегий)
        self.method_direct_zapret2_orchestra = Win11RadioOption(
            self._tr("page.dpi_settings.method.direct_z2_orchestra.title", "Оркестраторный Zapret 2"),
            self._tr(
                "page.dpi_settings.method.direct_z2_orchestra.desc",
                "Запуск Zapret 2 со стратегиями оркестратора внутри каждого профиля. Позволяет настроить для каждого сайта свой оркерстратор. Не сохраняет состояние для повышенной агрессии обхода.",
            ),
            icon_name="mdi.brain",
            icon_color="#9c27b0"
        )
        self.method_direct_zapret2_orchestra.clicked.connect(lambda: self._select_method("direct_zapret2_orchestra"))
        method_layout.addWidget(self.method_direct_zapret2_orchestra)

        # Оркестр (auto-learning)
        self.method_orchestra = Win11RadioOption(
            self._tr("page.dpi_settings.method.orchestra.title", "Оркестратор v0.9.6 (Beta)"),
            self._tr(
                "page.dpi_settings.method.orchestra.desc",
                "Автоматическое обучение. Система сама подбирает лучшие стратегии для каждого домена. Запоминает результаты между запусками.",
            ),
            icon_name="mdi.brain",
            icon_color="#9c27b0"
        )
        self.method_orchestra.clicked.connect(lambda: self._select_method("orchestra"))
        method_layout.addWidget(self.method_orchestra)

        # ───────────────────────────────────────
        # ZAPRET 1 (winws.exe)
        # ───────────────────────────────────────
        zapret1_header = StrongBodyLabel(
            self._tr("page.dpi_settings.section.z1", "Zapret 1 (winws.exe)")
        )
        self._zapret1_header = zapret1_header
        zapret1_header.setContentsMargins(0, 12, 0, 4)
        method_layout.addWidget(zapret1_header)

        # Zapret 1 Direct (прямой запуск winws.exe с JSON стратегиями)
        self.method_direct_zapret1 = Win11RadioOption(
            self._tr("page.dpi_settings.method.direct_z1.title", "Zapret 1"),
            self._tr(
                "page.dpi_settings.method.direct_z1.desc",
                "Режим первой версии Zapret 1 (winws.exe) + готовые пресеты для быстрого запуска. Не использует Lua код, нет понятия блобов.",
            ),
            icon_name="mdi.rocket-launch-outline",
            icon_color="#ff9800"
        )
        self.method_direct_zapret1.clicked.connect(lambda: self._select_method("direct_zapret1"))
        method_layout.addWidget(self.method_direct_zapret1)

        # Разделитель 2
        self.separator2 = QFrame()
        self.separator2.setFrameShape(QFrame.Shape.HLine)
        self.separator2.setFixedHeight(1)
        method_layout.addWidget(self.separator2)

        # Перезапуск Discord (только для Zapret 1/2)
        self.discord_restart_container = QWidget()
        discord_layout = QVBoxLayout(self.discord_restart_container)
        discord_layout.setContentsMargins(0, 0, 0, 0)
        discord_layout.setSpacing(0)

        self.discord_restart_toggle = Win11ToggleRow(
            "mdi.discord",
            self._tr("page.dpi_settings.discord_restart.title", "Перезапуск Discord"),
            self._tr("page.dpi_settings.discord_restart.desc", "Автоперезапуск при смене стратегии"),
            "#7289da",
        )
        discord_layout.addWidget(self.discord_restart_toggle)
        method_layout.addWidget(self.discord_restart_container)

        # ─────────────────────────────────────────────────────────────────────
        # НАСТРОЙКИ ОРКЕСТРАТОРА (только в режиме оркестратора)
        # ─────────────────────────────────────────────────────────────────────
        self.orchestra_settings_container = QWidget()
        orchestra_settings_layout = QVBoxLayout(self.orchestra_settings_container)
        orchestra_settings_layout.setContentsMargins(0, 0, 0, 0)
        orchestra_settings_layout.setSpacing(6)

        orchestra_label = StrongBodyLabel(
            self._tr("page.dpi_settings.section.orchestra_settings", "Настройки оркестратора")
        )
        self._orchestra_label = orchestra_label
        orchestra_settings_layout.addWidget(orchestra_label)

        self.strict_detection_toggle = Win11ToggleRow(
            "mdi.check-decagram",
            self._tr("page.dpi_settings.orchestra.strict_detection.title", "Строгий режим детекции"),
            self._tr("page.dpi_settings.orchestra.strict_detection.desc", "HTTP 200 + проверка блок-страниц"),
            "#4CAF50",
        )
        orchestra_settings_layout.addWidget(self.strict_detection_toggle)

        self.debug_file_toggle = Win11ToggleRow(
            "mdi.file-document-outline",
            self._tr("page.dpi_settings.orchestra.debug_file.title", "Сохранять debug файл"),
            self._tr("page.dpi_settings.orchestra.debug_file.desc", "Сырой debug файл для отладки"),
            "#8a2be2",
        )
        orchestra_settings_layout.addWidget(self.debug_file_toggle)

        self.auto_restart_discord_toggle = Win11ToggleRow(
            "mdi.discord",
            self._tr("page.dpi_settings.orchestra.auto_restart_discord.title", "Авторестарт Discord при FAIL"),
            self._tr(
                "page.dpi_settings.orchestra.auto_restart_discord.desc",
                "Перезапуск Discord при неудачном обходе",
            ),
            "#7289da",
        )
        orchestra_settings_layout.addWidget(self.auto_restart_discord_toggle)

        # Количество фейлов для рестарта Discord
        self.discord_fails_spin = Win11NumberRow(
            "mdi.discord",
            self._tr("page.dpi_settings.orchestra.discord_fails.title", "Фейлов для рестарта Discord"),
            self._tr(
                "page.dpi_settings.orchestra.discord_fails.desc",
                "Сколько FAIL подряд для перезапуска Discord",
            ),
            "#7289da",
            min_val=1, max_val=10, default_val=3)
        orchestra_settings_layout.addWidget(self.discord_fails_spin)

        # Успехов для LOCK (сколько успехов подряд для закрепления стратегии)
        self.lock_successes_spin = Win11NumberRow(
            "mdi.lock",
            self._tr("page.dpi_settings.orchestra.lock_successes.title", "Успехов для LOCK"),
            self._tr(
                "page.dpi_settings.orchestra.lock_successes.desc",
                "Количество успешных обходов для закрепления стратегии",
            ),
            "#4CAF50",
            min_val=1, max_val=10, default_val=3)
        orchestra_settings_layout.addWidget(self.lock_successes_spin)

        # Ошибок для AUTO-UNLOCK (сколько ошибок подряд для разблокировки)
        self.unlock_fails_spin = Win11NumberRow(
            "mdi.lock-open",
            self._tr("page.dpi_settings.orchestra.unlock_fails.title", "Ошибок для AUTO-UNLOCK"),
            self._tr(
                "page.dpi_settings.orchestra.unlock_fails.desc",
                "Количество ошибок для автоматической разблокировки стратегии",
            ),
            "#FF5722",
            min_val=1, max_val=10, default_val=3)
        orchestra_settings_layout.addWidget(self.unlock_fails_spin)

        method_layout.addWidget(self.orchestra_settings_container)

        method_card.add_layout(method_layout)
        self.layout.addWidget(method_card)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
        # ═══════════════════════════════════════════════════════════════════════
        self.advanced_card = SettingsCard(
            self._tr("page.dpi_settings.card.advanced", "ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ")
        )
        advanced_layout = QVBoxLayout()
        advanced_layout.setSpacing(6)
        
        # Описание
        advanced_desc = _CaptionLabel(
            self._tr("page.dpi_settings.advanced.warning", "⚠ Изменяйте только если знаете что делаете")
        )
        self._advanced_desc_label = advanced_desc
        advanced_desc.setContentsMargins(0, 0, 0, 8)
        advanced_layout.addWidget(advanced_desc)
        
        # WSSize
        self.wssize_toggle = Win11ToggleRow(
            "fa5s.ruler-horizontal",
            self._tr("page.dpi_settings.advanced.wssize.title", "Включить --wssize"),
            self._tr("page.dpi_settings.advanced.wssize.desc", "Добавляет параметр размера окна TCP"),
            "#9c27b0",
        )
        advanced_layout.addWidget(self.wssize_toggle)
        
        # Debug лог
        self.debug_log_toggle = Win11ToggleRow(
            "mdi.file-document-outline",
            self._tr("page.dpi_settings.advanced.debug_log.title", "Включить лог-файл (--debug)"),
            self._tr("page.dpi_settings.advanced.debug_log.desc", "Записывает логи winws в папку logs"),
            "#00bcd4",
        )
        advanced_layout.addWidget(self.debug_log_toggle)
        
        self.advanced_card.add_layout(advanced_layout)
        self.layout.addWidget(self.advanced_card)
        
        self.layout.addStretch()

        # Apply token-driven accents/dividers.
        self._apply_theme_styles()
        
    def _load_settings(self):
        """Загружает настройки"""
        try:
            from strategy_menu import get_strategy_launch_method
            method = get_strategy_launch_method()

            # Устанавливаем выбранный метод
            self._update_method_selection(method)

            # Discord restart setting
            self._load_discord_restart_setting()

            # Orchestra settings
            self._load_orchestra_settings()

            self._update_filters_visibility()
            self._load_filter_settings()

        except Exception as e:
            log(f"Ошибка загрузки настроек DPI: {e}", "WARNING")
    
    def _update_method_selection(self, method: str):
        """Обновляет визуальное состояние выбора метода"""
        self.method_direct.setSelected(method == "direct_zapret2")
        self.method_direct_zapret2_orchestra.setSelected(method == "direct_zapret2_orchestra")
        self.method_direct_zapret1.setSelected(method == "direct_zapret1")
        self.method_orchestra.setSelected(method == "orchestra")
    
    def _select_method(self, method: str):
        """Обработчик выбора метода"""
        try:
            from strategy_menu import set_strategy_launch_method, get_strategy_launch_method
            from legacy_registry_launch.selection_store import invalidate_direct_selections_cache
            from preset_orchestra_zapret2 import ensure_default_preset_exists

            # Запоминаем предыдущий метод, чтобы понять, затрагиваем ли мы legacy registry-driven ветки.
            previous_method = get_strategy_launch_method()

            if method == "direct_zapret2_orchestra":
                ensure_default_preset_exists()

            set_strategy_launch_method(method)
            self._update_method_selection(method)
            self._update_filters_visibility()

            # Сбрасываем кэш выборов при смене direct-метода: они будут перечитаны из актуального источника.
            direct_methods = ("direct_zapret2", "direct_zapret2_orchestra", "direct_zapret1")
            if previous_method in direct_methods or method in direct_methods:
                if previous_method != method:
                    log(f"Смена метода {previous_method} -> {method}, сброс direct-кэша...", "INFO")
                    invalidate_direct_selections_cache()

            # Legacy registry reload нужен только для orchestra/registry-driven страниц.
            registry_driven_methods = {"direct_zapret2_orchestra", "orchestra"}
            if (
                previous_method != method
                and (previous_method in registry_driven_methods or method in registry_driven_methods)
            ):
                try:
                    from legacy_registry_launch.strategies_registry import registry

                    registry.reload_strategies()
                except Exception:
                    pass

            self.launch_method_changed.emit(method)
        except Exception as e:
            log(f"Ошибка смены метода: {e}", "ERROR")
    
    def _load_discord_restart_setting(self):
        """Загружает настройку перезапуска Discord"""
        try:
            from discord.discord_restart import get_discord_restart_setting, set_discord_restart_setting
            
            # Загружаем текущее значение (по умолчанию True), блокируя сигналы
            self.discord_restart_toggle.setChecked(get_discord_restart_setting(default=True), block_signals=True)
            
            # Подключаем сигнал сохранения
            self.discord_restart_toggle.toggled.connect(self._on_discord_restart_changed)
            
        except Exception as e:
            log(f"Ошибка загрузки настройки Discord: {e}", "WARNING")
    
    def _on_discord_restart_changed(self, enabled: bool):
        """Обработчик изменения настройки перезапуска Discord"""
        try:
            from discord.discord_restart import set_discord_restart_setting
            set_discord_restart_setting(enabled)
            status = "включён" if enabled else "отключён"
            log(f"Автоперезапуск Discord {status}", "INFO")
        except Exception as e:
            log(f"Ошибка сохранения настройки Discord: {e}", "ERROR")

    def _load_orchestra_settings(self):
        """Загружает настройки оркестратора"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            # Строгий режим детекции (по умолчанию включён)
            saved_strict = reg(f"{REGISTRY_PATH}\\Orchestra", "StrictDetection")
            self.strict_detection_toggle.setChecked(saved_strict is None or bool(saved_strict), block_signals=True)
            self.strict_detection_toggle.toggled.connect(self._on_strict_detection_changed)

            # Debug файл (по умолчанию выключен)
            saved_debug = reg(f"{REGISTRY_PATH}\\Orchestra", "KeepDebugFile")
            self.debug_file_toggle.setChecked(bool(saved_debug), block_signals=True)
            self.debug_file_toggle.toggled.connect(self._on_debug_file_changed)

            # Авторестарт при Discord FAIL (по умолчанию включён)
            saved_auto_restart = reg(f"{REGISTRY_PATH}\\Orchestra", "AutoRestartOnDiscordFail")
            self.auto_restart_discord_toggle.setChecked(saved_auto_restart is None or bool(saved_auto_restart), block_signals=True)
            self.auto_restart_discord_toggle.toggled.connect(self._on_auto_restart_discord_changed)

            # Количество фейлов для рестарта Discord (по умолчанию 3)
            saved_discord_fails = reg(f"{REGISTRY_PATH}\\Orchestra", "DiscordFailsForRestart")
            if saved_discord_fails is not None:
                self.discord_fails_spin.setValue(int(saved_discord_fails))
            self.discord_fails_spin.valueChanged.connect(self._on_discord_fails_changed)

            # Успехов для LOCK (по умолчанию 3)
            saved_lock_successes = reg(f"{REGISTRY_PATH}\\Orchestra", "LockSuccesses")
            if saved_lock_successes is not None:
                self.lock_successes_spin.setValue(int(saved_lock_successes))
            self.lock_successes_spin.valueChanged.connect(self._on_lock_successes_changed)

            # Ошибок для AUTO-UNLOCK (по умолчанию 3)
            saved_unlock_fails = reg(f"{REGISTRY_PATH}\\Orchestra", "UnlockFails")
            if saved_unlock_fails is not None:
                self.unlock_fails_spin.setValue(int(saved_unlock_fails))
            self.unlock_fails_spin.valueChanged.connect(self._on_unlock_fails_changed)

        except Exception as e:
            log(f"Ошибка загрузки настроек оркестратора: {e}", "WARNING")

    def _on_strict_detection_changed(self, enabled: bool):
        """Обработчик изменения строгого режима детекции"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "StrictDetection", 1 if enabled else 0)
            log(f"Строгий режим детекции: {'включён' if enabled else 'выключен'}", "INFO")

            # Обновляем orchestra_runner если запущен
            app = self._get_app()
            if app and hasattr(app, 'orchestra_runner') and app.orchestra_runner:
                app.orchestra_runner.set_strict_detection(enabled)

        except Exception as e:
            log(f"Ошибка сохранения настройки строгого режима: {e}", "ERROR")

    def _on_debug_file_changed(self, enabled: bool):
        """Обработчик изменения сохранения debug файла"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "KeepDebugFile", 1 if enabled else 0)
            log(f"Сохранение debug файла: {'включено' if enabled else 'выключено'}", "INFO")

        except Exception as e:
            log(f"Ошибка сохранения настройки debug файла: {e}", "ERROR")

    def _on_auto_restart_discord_changed(self, enabled: bool):
        """Обработчик изменения авторестарта при Discord FAIL"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "AutoRestartOnDiscordFail", 1 if enabled else 0)
            log(f"Авторестарт при Discord FAIL: {'включён' if enabled else 'выключен'}", "INFO")

            # Обновляем orchestra_runner если запущен
            app = self._get_app()
            if app and hasattr(app, 'orchestra_runner') and app.orchestra_runner:
                app.orchestra_runner.auto_restart_on_discord_fail = enabled

        except Exception as e:
            log(f"Ошибка сохранения настройки авторестарта Discord: {e}", "ERROR")

    def _on_discord_fails_changed(self, value: int):
        """Обработчик изменения количества фейлов для рестарта Discord"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "DiscordFailsForRestart", value)
            log(f"Фейлов для рестарта Discord: {value}", "INFO")

            # Обновляем orchestra_runner если запущен
            app = self._get_app()
            if app and hasattr(app, 'orchestra_runner') and app.orchestra_runner:
                app.orchestra_runner.discord_fails_for_restart = value

        except Exception as e:
            log(f"Ошибка сохранения настройки DiscordFailsForRestart: {e}", "ERROR")

    def _on_lock_successes_changed(self, value: int):
        """Обработчик изменения количества успехов для LOCK"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "LockSuccesses", value)
            log(f"Успехов для LOCK: {value}", "INFO")

            # Обновляем orchestra_runner если запущен
            app = self._get_app()
            if app and hasattr(app, 'orchestra_runner') and app.orchestra_runner:
                app.orchestra_runner.lock_successes_threshold = value

        except Exception as e:
            log(f"Ошибка сохранения настройки LockSuccesses: {e}", "ERROR")

    def _on_unlock_fails_changed(self, value: int):
        """Обработчик изменения количества ошибок для AUTO-UNLOCK"""
        try:
            from config import REGISTRY_PATH
            from config.reg import reg

            reg(f"{REGISTRY_PATH}\\Orchestra", "UnlockFails", value)
            log(f"Ошибок для AUTO-UNLOCK: {value}", "INFO")

            # Обновляем orchestra_runner если запущен
            app = self._get_app()
            if app and hasattr(app, 'orchestra_runner') and app.orchestra_runner:
                app.orchestra_runner.unlock_fails_threshold = value

        except Exception as e:
            log(f"Ошибка сохранения настройки UnlockFails: {e}", "ERROR")

    def _get_app(self):
        """Получает ссылку на главное приложение"""
        try:
            # Ищем через parent виджетов
            widget = self
            while widget:
                if hasattr(widget, 'dpi_controller'):
                    return widget
                if hasattr(widget, 'parent_app'):
                    return widget.parent_app
                widget = widget.parent()
            
            # Пробуем через QApplication
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'dpi_controller'):
                return app
                
            # Пробуем через main_window
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'parent_app'):
                    return widget.parent_app
        except:
            pass
        return None
    
    def _restart_dpi_async(self):
        """Асинхронно перезапускает DPI если он запущен"""
        try:
            app = self._get_app()
            if not app or not hasattr(app, 'dpi_controller'):
                log("DPI контроллер не найден для перезапуска", "DEBUG")
                return

            # Для режима direct_zapret2 используем унифицированный механизм
            from strategy_menu import get_strategy_launch_method
            launch_method = get_strategy_launch_method()

            if launch_method in {"direct_zapret1", "direct_zapret2"}:
                from dpi.direct_runtime_apply_policy import request_direct_runtime_content_apply
                request_direct_runtime_content_apply(
                    app,
                    launch_method=str(launch_method or ""),
                    reason="settings_changed",
                )
                return

            # Для остальных режимов (orchestra, zapret1, bat) - старая логика
            # Проверяем, запущен ли процесс
            if not app.dpi_starter.check_process_running_wmi(silent=True):
                log("DPI не запущен, перезапуск не требуется", "DEBUG")
                return

            log("Перезапуск DPI после изменения настроек...", "INFO")

            # Асинхронно останавливаем
            app.dpi_controller.stop_dpi_async()

            # Запускаем таймер для проверки остановки и перезапуска
            self._restart_check_count = 0
            if not hasattr(self, '_restart_timer') or self._restart_timer is None:
                self._restart_timer = QTimer(self)
                self._restart_timer.timeout.connect(self._check_stopped_and_restart)
            self._restart_timer.start(300)  # Проверяем каждые 300мс

        except Exception as e:
            log(f"Ошибка перезапуска DPI: {e}", "ERROR")
    
    def _check_stopped_and_restart(self):
        """Проверяет остановку DPI и запускает заново"""
        try:
            app = self._get_app()
            if not app:
                self._restart_timer.stop()
                return
                
            self._restart_check_count += 1
            
            # Максимум 30 проверок (9 секунд)
            if self._restart_check_count > 30:
                self._restart_timer.stop()
                log("⚠️ Таймаут ожидания остановки DPI", "WARNING")
                self._start_dpi_after_stop()
                return
            
            # Проверяем, остановлен ли процесс
            if not app.dpi_starter.check_process_running_wmi(silent=True):
                self._restart_timer.stop()
                # Небольшая пауза и запуск
                QTimer.singleShot(200, self._start_dpi_after_stop)
                
        except Exception as e:
            if hasattr(self, '_restart_timer'):
                self._restart_timer.stop()
            log(f"Ошибка проверки остановки: {e}", "ERROR")
    
    def _start_dpi_after_stop(self):
        """Запускает DPI после остановки"""
        try:
            app = self._get_app()
            if not app or not hasattr(app, 'dpi_controller'):
                return
                
            from strategy_menu import get_strategy_launch_method
            launch_method = get_strategy_launch_method()
            
            if launch_method == "direct_zapret1":
                try:
                    from core.services import get_direct_flow_coordinator

                    selected_mode = get_direct_flow_coordinator().build_selected_mode(
                        "direct_zapret1",
                        require_filters=False,
                    )
                except Exception as e:
                    log(f"Перезапуск Zapret1 пропущен: {e}", "WARNING")
                    return
                app.dpi_controller.start_dpi_async(selected_mode=selected_mode, launch_method=launch_method)
            elif launch_method == "direct_zapret2":
                try:
                    from core.services import get_direct_flow_coordinator

                    selected_mode = get_direct_flow_coordinator().build_selected_mode(
                        "direct_zapret2",
                        require_filters=False,
                    )
                except Exception as e:
                    log(f"Перезапуск direct_zapret2 пропущен: {e}", "WARNING")
                    return
                app.dpi_controller.start_dpi_async(selected_mode=selected_mode, launch_method=launch_method)
            elif launch_method == "direct_zapret2_orchestra":
                # Orchestra direct остаётся на своём runtime-file workflow.
                from preset_orchestra_zapret2 import get_active_preset_path, get_active_preset_name

                preset_path = get_active_preset_path()
                if not preset_path.exists():
                    log("Перезапуск direct_zapret2_orchestra пропущен: runtime config не найден", "WARNING")
                    return
                preset_name = get_active_preset_name() or "Default"
                selected_mode = {
                    "is_preset_file": True,
                    "name": f"Пресет оркестра: {preset_name}",
                    "preset_path": str(preset_path),
                }
                app.dpi_controller.start_dpi_async(selected_mode=selected_mode, launch_method=launch_method)
            else:
                # BAT режим
                app.dpi_controller.start_dpi_async()
                
            log("✅ DPI перезапущен с новыми настройками", "INFO")
            
        except Exception as e:
            log(f"Ошибка запуска DPI: {e}", "ERROR")
        
    def _load_filter_settings(self):
        """Загружает настройки фильтров"""
        try:
            getter_wssize = self._get_filter_state_getter("wssize")
            getter_debug = self._get_filter_state_getter("debug")
            setter_wssize = self._get_filter_state_setter("wssize")
            setter_debug = self._get_filter_state_setter("debug")

            # ═══════════════════════════════════════════════════════════════════════
            # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ — остаются активными
            # ═══════════════════════════════════════════════════════════════════════
            self.wssize_toggle.setChecked(bool(getter_wssize()), block_signals=True)
            self.debug_log_toggle.setChecked(bool(getter_debug()), block_signals=True)

            # Подключаем сигналы только для дополнительных настроек
            self.wssize_toggle.toggled.connect(lambda v: self._on_filter_changed(setter_wssize, v))
            self.debug_log_toggle.toggled.connect(lambda v: self._on_filter_changed(setter_debug, v))

        except Exception as e:
            log(f"Ошибка загрузки фильтров: {e}", "WARNING")
            import traceback
            log(traceback.format_exc(), "DEBUG")

    def update_filter_display(self, filters: dict):
        """
        Совместимость: раньше показывало «Фильтры перехвата трафика» в GUI.
        Теперь блок удалён, метод оставлен как no-op для старых вызовов.
        """
        _ = filters
        return
                
    def _on_filter_changed(self, setter_func, value):
        """Обработчик изменения фильтра"""
        setter_func(value)

        self.filters_changed.emit()

    def _get_direct_toggle_facade(self):
        try:
            from strategy_menu import get_strategy_launch_method

            method = (get_strategy_launch_method() or "").strip().lower()
            if method in ("direct_zapret2", "direct_zapret1"):
                from core.presets.direct_facade import DirectPresetFacade

                return DirectPresetFacade.from_launch_method(method)
        except Exception:
            pass
        return None

    def _get_filter_state_getter(self, kind: str):
        facade = self._get_direct_toggle_facade()
        if facade is not None:
            if kind == "wssize":
                return facade.get_wssize_enabled
            return facade.get_debug_log_enabled

        if kind == "wssize":
            from strategy_menu import get_wssize_enabled

            return get_wssize_enabled

        from strategy_menu import get_debug_log_enabled

        return get_debug_log_enabled

    def _get_filter_state_setter(self, kind: str):
        facade = self._get_direct_toggle_facade()
        if facade is not None:
            if kind == "wssize":
                return lambda value: facade.set_wssize_enabled(bool(value))
            return lambda value: facade.set_debug_log_enabled(bool(value))

        if kind == "wssize":
            from strategy_menu import set_wssize_enabled

            return set_wssize_enabled

        from strategy_menu import set_debug_log_enabled

        return set_debug_log_enabled
        
    def _update_filters_visibility(self):
        """Обновляет видимость фильтров и секций"""
        try:
            from strategy_menu import get_strategy_launch_method
            method = get_strategy_launch_method()

            # Режимы
            is_direct_mode = method in ("direct_zapret2", "direct_zapret2_orchestra", "direct_zapret1")
            is_zapret_mode = method in ("direct_zapret2", "direct_zapret1")  # Zapret 1/2 без оркестратора

            # For direct_zapret2 these options are shown on the Strategies/Management page
            # (ui/pages/zapret2/direct_control_page.py), so hide them here.
            self.advanced_card.setVisible(is_direct_mode and method != "direct_zapret2")

            # If we just made the advanced section visible again, re-sync its state
            # from the current mode source of truth (preset for direct preset flow).
            if is_direct_mode and method != "direct_zapret2":
                try:
                    self.wssize_toggle.setChecked(bool(self._get_filter_state_getter("wssize")()), block_signals=True)
                    self.debug_log_toggle.setChecked(bool(self._get_filter_state_getter("debug")()), block_signals=True)
                except Exception:
                    pass

            # Discord restart только для Zapret 1/2 (без оркестратора)
            show_discord_restart = is_zapret_mode and method != "direct_zapret2"
            self.discord_restart_container.setVisible(show_discord_restart)
            if show_discord_restart:
                try:
                    from discord.discord_restart import get_discord_restart_setting

                    self.discord_restart_toggle.setChecked(get_discord_restart_setting(default=True), block_signals=True)
                except Exception:
                    pass

            # Настройки оркестратора только для Python-оркестратора.
            # В direct_zapret2_orchestra оркестрация выполняется Lua-модулем circular —
            # параметры LOCK/UNLOCK/Discord/strict_detection к нему не применяются.
            self.orchestra_settings_container.setVisible(method == "orchestra")

        except:
            pass

    def set_ui_language(self, language: str) -> None:
        super().set_ui_language(language)

        if self._method_card is not None:
            self._method_card.set_title(
                self._tr(
                    "page.dpi_settings.card.launch_method",
                    "Метод запуска стратегий (режим работы программы)",
                )
            )
        if self._method_desc_label is not None:
            self._method_desc_label.setText(
                self._tr("page.dpi_settings.launch_method.desc", "Выберите способ запуска обхода блокировок")
            )

        if hasattr(self, "zapret2_header") and self.zapret2_header is not None:
            self.zapret2_header.setText(self._tr("page.dpi_settings.section.z2", "Zapret 2 (winws2.exe)"))
        if self._zapret1_header is not None:
            self._zapret1_header.setText(self._tr("page.dpi_settings.section.z1", "Zapret 1 (winws.exe)"))
        if self._orchestra_label is not None:
            self._orchestra_label.setText(
                self._tr("page.dpi_settings.section.orchestra_settings", "Настройки оркестратора")
            )

        self.method_direct.set_texts(
            self._tr("page.dpi_settings.method.direct_z2.title", "Zapret 2"),
            self._tr(
                "page.dpi_settings.method.direct_z2.desc",
                "Режим со второй версией Zapret (winws2.exe) + готовые пресеты для быстрого запуска. Поддерживает кастомный lua-код чтобы писать свои стратегии.",
            ),
            recommended_badge=self._tr("page.dpi_settings.option.recommended", "рекомендуется"),
        )
        self.method_direct_zapret2_orchestra.set_texts(
            self._tr("page.dpi_settings.method.direct_z2_orchestra.title", "Оркестраторный Zapret 2"),
            self._tr(
                "page.dpi_settings.method.direct_z2_orchestra.desc",
                "Запуск Zapret 2 со стратегиями оркестратора внутри каждого профиля. Позволяет настроить для каждого сайта свой оркерстратор. Не сохраняет состояние для повышенной агрессии обхода.",
            ),
        )
        self.method_orchestra.set_texts(
            self._tr("page.dpi_settings.method.orchestra.title", "Оркестратор v0.9.6 (Beta)"),
            self._tr(
                "page.dpi_settings.method.orchestra.desc",
                "Автоматическое обучение. Система сама подбирает лучшие стратегии для каждого домена. Запоминает результаты между запусками.",
            ),
        )
        self.method_direct_zapret1.set_texts(
            self._tr("page.dpi_settings.method.direct_z1.title", "Zapret 1"),
            self._tr(
                "page.dpi_settings.method.direct_z1.desc",
                "Режим первой версии Zapret 1 (winws.exe) + готовые пресеты для быстрого запуска. Не использует Lua код, нет понятия блобов.",
            ),
        )

        self.discord_restart_toggle.set_texts(
            self._tr("page.dpi_settings.discord_restart.title", "Перезапуск Discord"),
            self._tr("page.dpi_settings.discord_restart.desc", "Автоперезапуск при смене стратегии"),
        )

        self.strict_detection_toggle.set_texts(
            self._tr("page.dpi_settings.orchestra.strict_detection.title", "Строгий режим детекции"),
            self._tr("page.dpi_settings.orchestra.strict_detection.desc", "HTTP 200 + проверка блок-страниц"),
        )
        self.debug_file_toggle.set_texts(
            self._tr("page.dpi_settings.orchestra.debug_file.title", "Сохранять debug файл"),
            self._tr("page.dpi_settings.orchestra.debug_file.desc", "Сырой debug файл для отладки"),
        )
        self.auto_restart_discord_toggle.set_texts(
            self._tr("page.dpi_settings.orchestra.auto_restart_discord.title", "Авторестарт Discord при FAIL"),
            self._tr(
                "page.dpi_settings.orchestra.auto_restart_discord.desc",
                "Перезапуск Discord при неудачном обходе",
            ),
        )
        self.discord_fails_spin.set_texts(
            self._tr("page.dpi_settings.orchestra.discord_fails.title", "Фейлов для рестарта Discord"),
            self._tr(
                "page.dpi_settings.orchestra.discord_fails.desc",
                "Сколько FAIL подряд для перезапуска Discord",
            ),
        )
        self.lock_successes_spin.set_texts(
            self._tr("page.dpi_settings.orchestra.lock_successes.title", "Успехов для LOCK"),
            self._tr(
                "page.dpi_settings.orchestra.lock_successes.desc",
                "Количество успешных обходов для закрепления стратегии",
            ),
        )
        self.unlock_fails_spin.set_texts(
            self._tr("page.dpi_settings.orchestra.unlock_fails.title", "Ошибок для AUTO-UNLOCK"),
            self._tr(
                "page.dpi_settings.orchestra.unlock_fails.desc",
                "Количество ошибок для автоматической разблокировки стратегии",
            ),
        )

        if hasattr(self, "advanced_card") and self.advanced_card is not None:
            self.advanced_card.set_title(
                self._tr("page.dpi_settings.card.advanced", "ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ")
            )
        if self._advanced_desc_label is not None:
            self._advanced_desc_label.setText(
                self._tr("page.dpi_settings.advanced.warning", "⚠ Изменяйте только если знаете что делаете")
            )
        self.wssize_toggle.set_texts(
            self._tr("page.dpi_settings.advanced.wssize.title", "Включить --wssize"),
            self._tr("page.dpi_settings.advanced.wssize.desc", "Добавляет параметр размера окна TCP"),
        )
        self.debug_log_toggle.set_texts(
            self._tr("page.dpi_settings.advanced.debug_log.title", "Включить лог-файл (--debug)"),
            self._tr("page.dpi_settings.advanced.debug_log.desc", "Записывает логи winws в папку logs"),
        )
