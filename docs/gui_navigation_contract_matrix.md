# GUI Navigation Contract Matrix

Дата фиксации: 2026-04-12

Этот документ — первая рабочая `navigation contract matrix` для новой GUI-архитектуры.

Он нужен как технический артефакт перед реальной реализацией cutover.
Его задача:

- дать одну каноническую таблицу по страницам;
- зафиксировать режимную доступность;
- зафиксировать, что видно в sidebar, а что нет;
- зафиксировать, что должно участвовать в sidebar search;
- зафиксировать, кто владеет созданием страницы и кто владеет её workflow.

Этот документ не описывает текущую реализацию как есть.
Он описывает целевую модель новой архитектуры, опираясь на текущие данные из `router.py`, но уже в терминах нового каркаса.

## 1. Правила чтения матрицы

### 1.1 `mode_scope`

Показывает, в каких режимах страница вообще допустима:

- `common`
- `direct_zapret2`
- `direct_zapret1`
- `orchestra`

### 1.2 `entry_kind`

Показывает роль страницы в новой navigation architecture:

- `root` — корневая страница, может жить в sidebar;
- `hidden` — пользовательская страница, но не root-entry;
- `detail` — экран деталей или редактор детали;
- `internal` — внутренняя страница, не предназначенная как самостоятельный root-entry.

### 1.3 `sidebar_visible`

Показывает, должна ли страница быть видимой в sidebar.

### 1.4 `search_visible`

Показывает, должна ли страница участвовать в sidebar search.

Правило для первой версии матрицы:

- user-facing страницы могут быть `search_visible=true`, даже если они не root;
- detail/edit-страницы обычно `search_visible=false`;
- технические internal-страницы не должны всплывать в поиске без явной пользы для пользователя.

### 1.5 `allow_direct_open`

Показывает, можно ли открыть страницу как прямой route из navigation/workflow,
или она должна открываться только через сценарий.

### 1.6 `factory_owner`

Показывает, кто отвечает за создание страницы в новом каркасе.

Для первой фазы canonical owner один:

- `UiPageFactory`

Если позже factory будет разделён по доменам, это допустимо, но до этого момента owner считается единым.

### 1.7 `workflow_owner`

Показывает, какой workflow-слой владеет переходами к странице и её orchestration.

Для первой версии матрицы используются role-level owner'ы:

- `CommonWorkflow`
- `DirectZ2Workflow`
- `DirectZ1Workflow`
- `OrchestraWorkflow`
- `AboutWorkflow`
- `ListsWorkflow`

Это role labels, а не обязательные точные имена классов.

## 2. Матрица

| PageName | Module | mode_scope | entry_kind | sidebar_visible | search_visible | breadcrumb_parent | allow_direct_open | factory_owner | workflow_owner | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `CONTROL` | `ui.pages.control_page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Fallback/common root page |
| `ZAPRET2_DIRECT_CONTROL` | `direct_control.zapret2.page` | `direct_zapret2` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `DirectZ2Workflow` | Root page режима `direct_zapret2` |
| `ZAPRET2_DIRECT` | `filters.pages.direct_zapret2_targets_page` | `direct_zapret2` | `hidden` | `false` | `true` | `ZAPRET2_DIRECT_CONTROL` | `true` | `UiPageFactory` | `DirectZ2Workflow` | Экран списка стратегий Z2 |
| `ZAPRET2_STRATEGY_DETAIL` | `filters.strategy_detail.zapret2.page` | `direct_zapret2` | `detail` | `false` | `false` | `ZAPRET2_DIRECT` | `false` | `UiPageFactory` | `DirectZ2Workflow` | Открывается только из workflow выбора target/strategy |
| `ZAPRET2_PRESET_DETAIL` | `preset_zapret2.ui.preset_detail_page` | `direct_zapret2` | `detail` | `false` | `false` | `ZAPRET2_USER_PRESETS` | `false` | `UiPageFactory` | `DirectZ2Workflow` | Подстраница конкретного пресета Z2 |
| `ZAPRET1_DIRECT_CONTROL` | `direct_control.zapret1.page` | `direct_zapret1` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `DirectZ1Workflow` | Root page режима `direct_zapret1` |
| `ZAPRET1_DIRECT` | `filters.pages.direct_zapret1_targets_page` | `direct_zapret1` | `hidden` | `false` | `true` | `ZAPRET1_DIRECT_CONTROL` | `true` | `UiPageFactory` | `DirectZ1Workflow` | Экран списка стратегий Z1 |
| `ZAPRET1_USER_PRESETS` | `preset_zapret1.ui.user_presets_page` | `direct_zapret1` | `hidden` | `false` | `true` | `ZAPRET1_DIRECT_CONTROL` | `true` | `UiPageFactory` | `DirectZ1Workflow` | Список пользовательских пресетов Z1 |
| `ZAPRET1_STRATEGY_DETAIL` | `filters.strategy_detail.zapret1.page` | `direct_zapret1` | `detail` | `false` | `false` | `ZAPRET1_DIRECT` | `false` | `UiPageFactory` | `DirectZ1Workflow` | Detail-экран стратегии Z1 |
| `ZAPRET1_PRESET_DETAIL` | `preset_zapret1.ui.preset_detail_page` | `direct_zapret1` | `detail` | `false` | `false` | `ZAPRET1_USER_PRESETS` | `false` | `UiPageFactory` | `DirectZ1Workflow` | Подстраница конкретного пресета Z1 |
| `HOSTLIST` | `lists.ui.hostlist_page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `ListsWorkflow` | Общая страница списков |
| `BLOBS` | `blobs.ui.page` | `common` | `hidden` | `false` | `true` | `-` | `true` | `UiPageFactory` | `ListsWorkflow` | Доступна из direct/list workflows, не root-entry |
| `DPI_SETTINGS` | `settings.dpi.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая системная страница |
| `ZAPRET2_USER_PRESETS` | `preset_zapret2.ui.user_presets_page` | `direct_zapret2` | `hidden` | `false` | `true` | `ZAPRET2_DIRECT_CONTROL` | `true` | `UiPageFactory` | `DirectZ2Workflow` | Список пользовательских пресетов Z2 |
| `NETROGAT` | `lists.ui.netrogat_page` | `common` | `internal` | `false` | `true` | `HOSTLIST` | `true` | `UiPageFactory` | `ListsWorkflow` | Внутренняя list-subpage, не root-entry |
| `CUSTOM_DOMAINS` | `lists.ui.custom_domains_page` | `common` | `internal` | `false` | `true` | `HOSTLIST` | `true` | `UiPageFactory` | `ListsWorkflow` | Внутренняя list-subpage |
| `CUSTOM_IPSET` | `lists.ui.custom_ipset_page` | `common` | `internal` | `false` | `true` | `HOSTLIST` | `true` | `UiPageFactory` | `ListsWorkflow` | Внутренняя list-subpage |
| `AUTOSTART` | `autostart.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая системная страница |
| `NETWORK` | `dns.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая системная страница |
| `HOSTS` | `hosts.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая диагностическая страница |
| `BLOCKCHECK` | `blockcheck.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая диагностическая страница |
| `APPEARANCE` | `ui.pages.appearance_page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая visual/system страница |
| `PREMIUM` | `donater.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая premium страница |
| `LOGS` | `log.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая logs страница |
| `SERVERS` | `updater.ui.page` | `common` | `hidden` | `false` | `true` | `ABOUT` | `true` | `UiPageFactory` | `AboutWorkflow` | Подстраница обновлений из About |
| `ABOUT` | `ui.pages.about_page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `AboutWorkflow` | Root page раздела About |
| `SUPPORT` | `ui.pages.support_page` | `common` | `hidden` | `false` | `true` | `ABOUT` | `true` | `UiPageFactory` | `AboutWorkflow` | Подстраница поддержки |
| `ORCHESTRA` | `orchestra.ui.page` | `orchestra` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `OrchestraWorkflow` | Root page режима orchestra |
| `ORCHESTRA_SETTINGS` | `orchestra.ui.settings_page` | `orchestra` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `OrchestraWorkflow` | Root/settings page orchestra |
| `TELEGRAM_PROXY` | `telegram_proxy.ui.page` | `common` | `root` | `true` | `true` | `-` | `true` | `UiPageFactory` | `CommonWorkflow` | Общая system/network страница |

## 3. Наблюдения по матрице

### 3.1 Root pages

Корневыми страницами новой архитектуры считаются:

- `CONTROL`
- `ZAPRET2_DIRECT_CONTROL`
- `ZAPRET1_DIRECT_CONTROL`
- `HOSTLIST`
- `DPI_SETTINGS`
- `AUTOSTART`
- `NETWORK`
- `HOSTS`
- `BLOCKCHECK`
- `APPEARANCE`
- `PREMIUM`
- `LOGS`
- `ABOUT`
- `ORCHESTRA`
- `ORCHESTRA_SETTINGS`
- `TELEGRAM_PROXY`

### 3.2 Hidden pages

Hidden pages не должны жить как root-entry в sidebar, но могут открываться workflow-слоем:

- `ZAPRET2_DIRECT`
- `ZAPRET2_USER_PRESETS`
- `ZAPRET1_DIRECT`
- `ZAPRET1_USER_PRESETS`
- `BLOBS`
- `SERVERS`
- `SUPPORT`

### 3.3 Detail pages

Detail pages не должны открываться как прямой пользовательский маршрут без сценария:

- `ZAPRET2_STRATEGY_DETAIL`
- `ZAPRET2_PRESET_DETAIL`
- `ZAPRET1_STRATEGY_DETAIL`
- `ZAPRET1_PRESET_DETAIL`

### 3.4 Internal pages

Internal pages не являются root-entry, но остаются user-facing страницами внутри list/workflow сценариев:

- `NETROGAT`
- `CUSTOM_DOMAINS`
- `CUSTOM_IPSET`

## 4. Жёсткие инварианты матрицы

- `direct_zapret2` не открывает `ZAPRET1_*` и `ORCHESTRA*`.
- `direct_zapret1` не открывает `ZAPRET2_*` и `ORCHESTRA*`.
- `orchestra` не открывает `ZAPRET1_*` и `ZAPRET2_*`.
- Detail pages не должны быть `allow_direct_open=true`.
- Страница не может быть `sidebar_visible=true`, если её `entry_kind` не `root`.
- Search visibility не должна нарушать mode gating.

## 5. Что должен сделать следующий ИИ с этой матрицей

1. Сверить матрицу с новым schema-модулем.
2. Явно перенести эти поля в schema-data.
3. Не переносить вслепую старую `router.py` семантику, если она противоречит этой матрице.
4. Проверить отдельные спорные страницы:
   - `BLOBS`
   - `NETROGAT`
   - `CUSTOM_DOMAINS`
   - `CUSTOM_IPSET`
   - `SERVERS`
   - `SUPPORT`
5. После внедрения schema убедиться, что sidebar, search, breadcrumbs и hidden-page open работают по одной и той же матрице.

## 6. Статус документа

Этот документ является первой рабочей версией матрицы.

Он уже пригоден как входной артефакт для начала реализации, но допускает уточнение в одном месте:

- если в реальном UX выяснится, что отдельная hidden/internal page должна быть `search_visible=false` или иметь другого `workflow_owner`, это можно скорректировать;
- при этом нельзя менять сам принцип матрицы: один schema source, один mode gating contract, одна owner-model по странице.
