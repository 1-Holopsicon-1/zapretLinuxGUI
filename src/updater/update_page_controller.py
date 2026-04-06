from __future__ import annotations

import time

from PyQt6.QtCore import QThread, QTimer

from config import CHANNEL
from log import log
from updater.rate_limiter import UpdateRateLimiter


class UpdatePageController:
    """Сценарный слой страницы обновлений.

    Держит фоновые воркеры, кэш состояния проверки и установку обновления.
    Сама страница остаётся экраном: отображает состояние и пробрасывает действия
    пользователя в этот контроллер.
    """

    def __init__(self, view) -> None:
        self._view = view

        self.server_worker = None
        self.version_worker = None
        self._update_thread = None
        self._update_worker = None

        self._checking = False
        self._found_update = False
        self._remote_version = ""
        self._release_notes = ""
        self._update_in_progress = False

        self._last_check_time = 0.0
        self._check_cooldown = 60
        self._has_cached_data = False

        try:
            from config import get_auto_update_enabled

            self._auto_check_enabled = bool(get_auto_update_enabled())
        except Exception:
            self._auto_check_enabled = True

    @property
    def auto_check_enabled(self) -> bool:
        return bool(self._auto_check_enabled)

    def on_page_shown(self) -> None:
        if self._update_in_progress or self._is_download_in_progress():
            return

        elapsed = time.time() - self._last_check_time
        if self._has_cached_data and elapsed < self._check_cooldown:
            self._view.show_checked_ago(elapsed)
            return

        if self._auto_check_enabled:
            if elapsed >= self._check_cooldown:
                QTimer.singleShot(200, self.start_checks)
        else:
            self._view.show_manual_hint()

    def present_startup_update(self, version: str, release_notes: str, *, install_after_show: bool = True) -> bool:
        if self._update_in_progress or self._is_download_in_progress():
            log("Обновление уже загружается, пропускаем startup-триггер", "🔄 UPDATE")
            return False

        self._remote_version = str(version or "")
        self._release_notes = str(release_notes or "")
        self._found_update = bool(self._remote_version)

        self._view.show_update_offer(self._remote_version, self._release_notes)

        if install_after_show:
            QTimer.singleShot(300, self.install_update)
        return True

    def start_checks(self, telegram_only: bool = False, skip_server_rate_limit: bool = False) -> None:
        if self._checking:
            return

        if self._update_in_progress or self._is_download_in_progress():
            log("⏭️ Пропуск проверки - идёт скачивание обновления", "🔄 UPDATE")
            return

        keep_existing_rows = False

        if not telegram_only:
            if not skip_server_rate_limit:
                can_full, msg = UpdateRateLimiter.can_check_servers_full()
                if not can_full:
                    telegram_only = True
                    keep_existing_rows = True
                    log(f"⏱️ Полная проверка VPS заблокирована: {msg}. fallback=telegram-only", "🔄 UPDATE")

            if not telegram_only:
                UpdateRateLimiter.record_servers_full_check()
                self._last_check_time = time.time()

        self._checking = True
        self._found_update = False
        self._remote_version = ""
        self._release_notes = ""

        self._view.start_checking()
        if not keep_existing_rows:
            self._view.reset_server_rows()

        self._stop_server_workers()

        from updater.server_status_workers import ServerCheckWorker

        self.server_worker = ServerCheckWorker(
            update_pool_stats=False,
            telegram_only=telegram_only,
            language=self._view.get_ui_language(),
        )
        self.server_worker.server_checked.connect(self._on_server_checked)
        self.server_worker.all_complete.connect(self._on_servers_complete)
        self.server_worker.dpi_restart_needed.connect(self._restart_dpi_after_update)
        self.server_worker.start()

    def request_manual_check(self) -> None:
        if self._update_in_progress or self._is_download_in_progress():
            return

        self._view.hide_update_offer()
        self._found_update = False
        self._remote_version = ""
        self._release_notes = ""

        from updater import invalidate_cache

        invalidate_cache(CHANNEL)
        log("🔄 Полная проверка всех серверов (ручная)", "🔄 UPDATE")

        self.start_checks(telegram_only=False, skip_server_rate_limit=True)

    def install_update(self) -> None:
        if self._update_in_progress:
            log("Загрузка уже выполняется, повторный запуск проигнорирован", "🔄 UPDATE")
            return

        self._update_in_progress = True
        log(f"Запуск установки обновления v{self._remote_version}", "🔄 UPDATE")

        from updater import invalidate_cache

        invalidate_cache(CHANNEL)

        self._view.start_update_download(self._remote_version)
        self._view.hide_update_status_card()
        self._view.set_update_check_enabled(False)

        try:
            from updater.update import UpdateWorker

            parent_window = self._view.window()

            self._update_thread = QThread(parent_window)
            self._update_worker = UpdateWorker(parent_window, silent=True, skip_rate_limit=True)
            self._update_worker.moveToThread(self._update_thread)

            self._update_thread.started.connect(self._update_worker.run)
            self._update_worker.finished.connect(self._update_thread.quit)
            self._update_worker.finished.connect(self._update_worker.deleteLater)
            self._update_thread.finished.connect(self._update_thread.deleteLater)

            def _on_thread_done():
                self._update_in_progress = False
                self._update_thread = None
                self._update_worker = None
                self._view.set_update_check_enabled(True)

            self._update_thread.finished.connect(_on_thread_done)

            self._update_worker.progress_bytes.connect(
                lambda p, d, t: self._view.update_download_progress(p, d, t)
            )
            self._update_worker.download_complete.connect(self._view.mark_update_download_complete)
            self._update_worker.download_failed.connect(self._view.mark_update_download_failed)
            self._update_worker.download_failed.connect(self._on_download_failed)
            self._update_worker.dpi_restart_needed.connect(self._restart_dpi_after_update)
            self._update_worker.progress.connect(lambda m: log(f"{m}", "🔁 UPDATE"))

            self._update_thread.start()
        except Exception as e:
            log(f"Ошибка при запуске обновления: {e}", "❌ ERROR")
            self._update_in_progress = False
            self._update_thread = None
            self._update_worker = None
            self._view.set_update_check_enabled(True)
            self._view.mark_update_download_failed(str(e)[:50])

    def dismiss_update(self) -> None:
        log("Обновление отложено пользователем", "🔄 UPDATE")
        self._view.show_update_deferred(self._remote_version)

    def set_auto_check_enabled(self, enabled: bool) -> None:
        self._auto_check_enabled = bool(enabled)

        try:
            from config import set_auto_update_enabled

            set_auto_update_enabled(bool(enabled))
        except Exception:
            pass

        if enabled:
            self._view.show_auto_enabled_hint()
        else:
            self._view.show_manual_hint()

        log(f"Автопроверка при запуске: {'включена' if enabled else 'отключена'}", "🔄 UPDATE")

    def cleanup(self) -> None:
        self._stop_server_workers()

        try:
            thread = self._update_thread
            if thread is not None and thread.isRunning():
                log("Останавливаем update_thread...", "DEBUG")
                thread.quit()
                if not thread.wait(2000):
                    log("⚠ update_thread не завершился, принудительно завершаем", "WARNING")
                    thread.terminate()
                    thread.wait(500)
        except Exception as e:
            log(f"Ошибка при очистке update controller: {e}", "DEBUG")

    def _on_server_checked(self, server_name: str, status: dict) -> None:
        self._view.upsert_server_status(server_name, status)
        self._maybe_offer_update_from_server(server_name, status)

    def _on_servers_complete(self) -> None:
        try:
            if self.version_worker and self.version_worker.isRunning():
                self.version_worker.terminate()
                self.version_worker.wait(500)
        except Exception:
            pass

        from updater.server_status_workers import VersionCheckWorker

        self.version_worker = VersionCheckWorker()
        self.version_worker.version_found.connect(self._on_version_found)
        self.version_worker.complete.connect(self._on_versions_complete)
        self.version_worker.start()

    def _on_version_found(self, channel: str, version_info: dict) -> None:
        target_channel = "test" if self._is_test_update_channel() else "stable"
        if channel in {"stable", "test"} and channel == target_channel and not version_info.get("error"):
            version = version_info.get("version", "")
            try:
                from updater.update import compare_versions

                if compare_versions(self._app_version(), version) < 0:
                    self._found_update = True
                    self._remote_version = version
                    self._release_notes = version_info.get("release_notes", "")
            except Exception:
                pass

    def _on_versions_complete(self) -> None:
        self._checking = False
        self._has_cached_data = True
        self._view.finish_checking(self._found_update, self._remote_version)

        if self._found_update and not self._update_in_progress and not self._is_download_in_progress():
            self._view.show_update_offer(self._remote_version, self._release_notes)

    def _on_download_failed(self, error: str) -> None:
        _ = error
        self._view.show_update_status_card()
        self._view.show_update_download_error()

    def _maybe_offer_update_from_server(self, server_name: str, status: dict) -> None:
        if not self._checking:
            return

        if self._found_update is False and not status.get("is_current"):
            return

        if self._update_in_progress or self._is_download_in_progress():
            return

        candidate_version, candidate_notes = self._get_candidate_version_and_notes(status)
        if not candidate_version:
            return

        try:
            from updater.update import compare_versions

            if compare_versions(self._app_version(), candidate_version) >= 0:
                return

            if self._remote_version and compare_versions(self._remote_version, candidate_version) >= 0:
                return
        except Exception:
            return

        self._found_update = True
        self._remote_version = candidate_version
        self._release_notes = candidate_notes or ""

        self._view.show_update_offer(self._remote_version, self._release_notes)
        self._view.show_found_update_source(self._remote_version, server_name)

    def _get_candidate_version_and_notes(self, status: dict) -> tuple[str | None, str]:
        if self._is_test_update_channel():
            raw_version = status.get("test_version")
            notes = status.get("test_notes", "") or ""
        else:
            raw_version = status.get("stable_version")
            notes = status.get("stable_notes", "") or ""

        if not raw_version or raw_version == "—":
            return None, ""

        try:
            from updater.github_release import normalize_version

            return normalize_version(str(raw_version)), notes
        except Exception:
            return None, ""

    def _restart_dpi_after_update(self) -> None:
        try:
            win = self._view.window()
            if hasattr(win, "dpi_controller") and win.dpi_controller:
                log("🔄 Перезапуск DPI после скачивания обновления", "🔁 UPDATE")
                win.dpi_controller.restart_dpi_async()
        except Exception as e:
            log(f"Не удалось перезапустить DPI: {e}", "❌ ERROR")

    def _stop_server_workers(self) -> None:
        try:
            if self.server_worker and self.server_worker.isRunning():
                log("Останавливаем server_worker...", "DEBUG")
                self.server_worker.quit()
                if not self.server_worker.wait(2000):
                    log("⚠ server_worker не завершился, принудительно завершаем", "WARNING")
                    self.server_worker.terminate()
                    self.server_worker.wait(500)
        except Exception as e:
            log(f"Ошибка остановки server_worker: {e}", "DEBUG")
        finally:
            self.server_worker = None

        try:
            if self.version_worker and self.version_worker.isRunning():
                log("Останавливаем version_worker...", "DEBUG")
                self.version_worker.quit()
                if not self.version_worker.wait(2000):
                    log("⚠ version_worker не завершился, принудительно завершаем", "WARNING")
                    self.version_worker.terminate()
                    self.version_worker.wait(500)
        except Exception as e:
            log(f"Ошибка остановки version_worker: {e}", "DEBUG")
        finally:
            self.version_worker = None

    def _is_download_in_progress(self) -> bool:
        try:
            return bool(self._view.is_update_download_in_progress())
        except Exception:
            return False

    @staticmethod
    def _app_version() -> str:
        from config import APP_VERSION

        return APP_VERSION

    @staticmethod
    def _is_test_update_channel() -> bool:
        from updater.channel_utils import is_test_update_channel

        return bool(is_test_update_channel(CHANNEL))
