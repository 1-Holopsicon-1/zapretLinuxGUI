"""Build-helper shell вкладок для About page."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import SegmentedWidget


@dataclass(slots=True)
class AboutPageTabsWidgets:
    tabs_pivot: SegmentedWidget
    stacked_widget: QStackedWidget
    about_tab: QWidget
    about_layout: QVBoxLayout
    support_tab: QWidget
    support_layout: QVBoxLayout
    help_tab: QWidget
    help_layout: QVBoxLayout
    kvn_tab: QWidget
    kvn_layout: QVBoxLayout


def _make_tab_widget() -> tuple[QWidget, QVBoxLayout]:
    tab = QWidget()
    layout = QVBoxLayout(tab)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(16)
    return tab, layout


def build_about_page_tabs(*, tr_fn, on_switch_tab) -> AboutPageTabsWidgets:
    tabs_pivot = SegmentedWidget()
    tabs_pivot.addItem(
        routeKey="about",
        text=" " + tr_fn("page.about.tab.about", "О ПРОГРАММЕ"),
        onClick=lambda: on_switch_tab(0),
    )
    tabs_pivot.addItem(
        routeKey="support",
        text=" " + tr_fn("page.about.tab.support", "ПОДДЕРЖКА"),
        onClick=lambda: on_switch_tab(1),
    )
    tabs_pivot.addItem(
        routeKey="help",
        text=" " + tr_fn("page.about.tab.help", "СПРАВКА"),
        onClick=lambda: on_switch_tab(2),
    )
    tabs_pivot.addItem(
        routeKey="kvn",
        text=" ZAPRET KVN",
        onClick=lambda: on_switch_tab(3),
    )
    tabs_pivot.setCurrentItem("about")
    tabs_pivot.setItemFontSize(13)

    stacked_widget = QStackedWidget()

    about_tab, about_layout = _make_tab_widget()
    support_tab, support_layout = _make_tab_widget()
    help_tab, help_layout = _make_tab_widget()
    kvn_tab, kvn_layout = _make_tab_widget()

    stacked_widget.addWidget(about_tab)
    stacked_widget.addWidget(support_tab)
    stacked_widget.addWidget(help_tab)
    stacked_widget.addWidget(kvn_tab)

    return AboutPageTabsWidgets(
        tabs_pivot=tabs_pivot,
        stacked_widget=stacked_widget,
        about_tab=about_tab,
        about_layout=about_layout,
        support_tab=support_tab,
        support_layout=support_layout,
        help_tab=help_tab,
        help_layout=help_layout,
        kvn_tab=kvn_tab,
        kvn_layout=kvn_layout,
    )
