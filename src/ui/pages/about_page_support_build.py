"""Build-helper вкладки «Поддержка» для About page."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from qfluentwidgets import SettingCardGroup, PushSettingCard, PrimaryPushSettingCard
from ui.theme import get_themed_qta_icon


@dataclass(slots=True)
class AboutPageSupportWidgets:
    discussions_group: object
    discussions_card: object
    community_group: object
    telegram_card: object
    discord_card: object


def build_about_page_support_content(
    layout,
    *,
    tr_fn: Callable[[str, str], str],
    content_parent,
    tokens,
    on_open_discussions,
    on_open_telegram,
    on_open_discord,
) -> AboutPageSupportWidgets:
    discussions_group = SettingCardGroup(
        tr_fn("page.about.support.section.discussions", "GitHub Discussions"),
        content_parent,
    )
    discussions_card = PrimaryPushSettingCard(
        tr_fn("page.about.support.discussions.button", "Открыть"),
        get_themed_qta_icon("fa5b.github", color=tokens.accent_hex),
        tr_fn("page.about.support.discussions.title", "GitHub Discussions"),
        tr_fn(
            "page.about.support.discussions.desc",
            "Основной канал поддержки. Здесь можно задать вопрос, описать проблему и приложить материалы вручную.",
        ),
    )
    discussions_card.clicked.connect(on_open_discussions)
    discussions_group.addSettingCard(discussions_card)
    layout.addWidget(discussions_group)
    layout.addSpacing(16)

    community_group = SettingCardGroup(
        tr_fn("page.about.support.section.community", "Каналы сообщества"),
        content_parent,
    )
    telegram_card = PushSettingCard(
        tr_fn("page.about.support.button.open", "Открыть"),
        get_themed_qta_icon("fa5b.telegram", color="#229ED9"),
        tr_fn("page.about.support.telegram.title", "Telegram"),
        tr_fn("page.about.support.telegram.desc", "Быстрые вопросы и общение с сообществом"),
    )
    telegram_card.clicked.connect(on_open_telegram)

    discord_card = PushSettingCard(
        tr_fn("page.about.support.button.open", "Открыть"),
        get_themed_qta_icon("fa5b.discord", color="#5865F2"),
        tr_fn("page.about.support.discord.title", "Discord"),
        tr_fn("page.about.support.discord.desc", "Обсуждение и живое общение"),
    )
    discord_card.clicked.connect(on_open_discord)

    community_group.addSettingCards([telegram_card, discord_card])
    layout.addWidget(community_group)
    layout.addStretch()

    return AboutPageSupportWidgets(
        discussions_group=discussions_group,
        discussions_card=discussions_card,
        community_group=community_group,
        telegram_card=telegram_card,
        discord_card=discord_card,
    )
