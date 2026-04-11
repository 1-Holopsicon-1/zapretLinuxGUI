"""Build-helper секции program settings для Control page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ControlProgramSettingsWidgets:
    section_label: object | None
    program_settings_card: object
    auto_dpi_toggle: object
    defender_toggle: object
    max_block_toggle: object
    reset_program_card: object | None
    reset_program_btn: object | None
    reset_program_desc_label: object | None
    extra_reset_card: object | None


def build_control_program_settings_section(
    *,
    tr_fn,
    content_parent,
    has_fluent_labels: bool,
    setting_card_group_cls,
    push_setting_card_cls,
    settings_card_cls,
    reset_action_button_cls,
    win11_toggle_row_cls,
    caption_label_cls,
    fallback_label_cls,
    qhbox_layout_cls,
    qta_module,
    on_auto_dpi_toggled,
    on_defender_toggled,
    on_max_blocker_toggled,
    on_confirm_reset_program_clicked,
    on_reset_program_clicked,
) -> ControlProgramSettingsWidgets:
    program_settings_title = tr_fn(
        "page.control.section.program_settings",
        "Настройки программы",
    )

    if setting_card_group_cls is not None and push_setting_card_cls is not None and has_fluent_labels:
        section_label = None
        program_settings_card = setting_card_group_cls(program_settings_title, content_parent)
    else:
        section_label = None
        program_settings_card = settings_card_cls()
        try:
            program_settings_card.set_title(program_settings_title)
        except Exception:
            pass

    auto_dpi_toggle = win11_toggle_row_cls(
        "fa5s.bolt",
        tr_fn("page.control.setting.autostart.title", "Автозапуск DPI после старта программы"),
        tr_fn("page.control.setting.autostart.desc", "После запуска ZapretGUI автоматически запускать текущий DPI-режим"),
    )
    auto_dpi_toggle.toggled.connect(on_auto_dpi_toggled)

    defender_toggle = win11_toggle_row_cls(
        "fa5s.shield-alt",
        tr_fn("page.control.setting.defender.title", "Отключить Windows Defender"),
        tr_fn("page.control.setting.defender.desc", "Требуются права администратора"),
    )
    defender_toggle.toggled.connect(on_defender_toggled)

    max_block_toggle = win11_toggle_row_cls(
        "fa5s.ban",
        tr_fn("page.control.setting.max_block.title", "Блокировать установку MAX"),
        tr_fn("page.control.setting.max_block.desc", "Блокирует запуск/установку MAX и домены в hosts"),
    )
    max_block_toggle.toggled.connect(on_max_blocker_toggled)

    add_setting_card = getattr(program_settings_card, "addSettingCard", None)
    if callable(add_setting_card):
        add_setting_card(auto_dpi_toggle)
        add_setting_card(defender_toggle)
        add_setting_card(max_block_toggle)
    else:
        program_settings_card.add_widget(auto_dpi_toggle)
        program_settings_card.add_widget(defender_toggle)
        program_settings_card.add_widget(max_block_toggle)

    reset_program_card = None
    reset_program_btn = None
    reset_program_desc_label = None
    extra_reset_card = None

    if callable(add_setting_card) and push_setting_card_cls is not None:
        reset_program_card = push_setting_card_cls(
            tr_fn("page.control.button.reset", "Сбросить"),
            qta_module.icon("fa5s.undo", color="#ff9800"),
            tr_fn("page.control.setting.reset.title", "Сбросить программу"),
            tr_fn("page.control.setting.reset.desc", "Очистить кэш проверок запуска (без удаления пресетов/настроек)"),
        )
        reset_program_card.clicked.connect(on_confirm_reset_program_clicked)
        add_setting_card(reset_program_card)
    else:
        reset_program_btn = reset_action_button_cls(
            tr_fn("page.control.button.reset", "Сбросить"),
            confirm_text=tr_fn("page.control.button.reset_confirm", "Сбросить?"),
        )
        reset_program_btn.setProperty("noDrag", True)
        reset_program_btn.reset_confirmed.connect(on_reset_program_clicked)

        extra_reset_card = settings_card_cls(
            tr_fn("page.control.setting.reset.title", "Сбросить программу")
        )
        reset_program_desc_label = (
            caption_label_cls(
                tr_fn("page.control.setting.reset.desc", "Очистить кэш проверок запуска (без удаления пресетов/настроек)")
            )
            if has_fluent_labels
            else fallback_label_cls(
                tr_fn("page.control.setting.reset.desc", "Очистить кэш проверок запуска (без удаления пресетов/настроек)")
            )
        )
        reset_program_desc_label.setWordWrap(True)
        extra_reset_card.add_widget(reset_program_desc_label)

        reset_layout = qhbox_layout_cls()
        reset_layout.setSpacing(8)
        reset_layout.addWidget(reset_program_btn)
        reset_layout.addStretch()
        extra_reset_card.add_layout(reset_layout)
        reset_program_card = extra_reset_card

    return ControlProgramSettingsWidgets(
        section_label=section_label,
        program_settings_card=program_settings_card,
        auto_dpi_toggle=auto_dpi_toggle,
        defender_toggle=defender_toggle,
        max_block_toggle=max_block_toggle,
        reset_program_card=reset_program_card,
        reset_program_btn=reset_program_btn,
        reset_program_desc_label=reset_program_desc_label,
        extra_reset_card=extra_reset_card,
    )
