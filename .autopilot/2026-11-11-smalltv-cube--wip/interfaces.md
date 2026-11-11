# Интерфейсы

## Правила проекта
- Python ≥3.9, пакет `cube/` в корне репозитория, зависимости через `uv` (`pyproject.toml`). Запуск: `uv run python -m cube <команда>`.
- Секреты только из `.env` (через `cube/config.py`), никогда в лог, в код, в git.
- Тексты на экране — по-русски. Код и имена — по-английски.
- Каждый источник ловит свои ошибки сам и никогда не роняет главный цикл.
- Сеть в тестах не вызывается: источники и устройство подменяются фейками.
- Прошивку кубика не трогать: никаких `/set?reset`, `/set?reboot`, `/set?clear=image`, удаление только своих файлов (префикс `cube-`).

## Команды
- Установка: `uv sync`
- Проверка (одна команда): `uv run pytest -q` — таск 01 создаёт её; один файл: `uv run pytest -q tests/test_x.py`
- Запуск: `uv run python -m cube run` · превью: `uv run python -m cube preview out/`
- Таск 01 ставит все зависимости из спецификации: pillow, httpx, telethon, python-dotenv, pytest.
- Не трогать: `.autopilot/`, `AGENTS.md`, `CLAUDE.md` (это пишет оркестратор). В реальный `~/.claude/settings.json` и `~/Library/LaunchAgents` тесты не пишут — только во временные пути.
- Живой кубик 192.168.100.54 доступен для ручной проверки: можно грузить свои кадры `cube-*`, нельзя reset/reboot/clear.

## Дизайн-скиллы (R12, R13)
Перед тем как рисовать экраны, прочитай `~/.claude/skills/impeccable/SKILL.md` (или найди его: `find -L ~/.claude ~/.agents -name SKILL.md -path '*impeccable*'`) и правила движения из `hyperframes-animation` (`find -L ~/.claude ~/.agents -path '*hyperframes-animation*' -name '*.md'`). Бери из них только применимое к статичному экрану 240×240 и короткому GIF. Решения (шрифты, размеры, цвета, контраст, длительность и кривая анимации, со ссылкой на правило скилла) — в `docs/design.md`.

## Границы, решённые в спецификации

### `cube/config.py` — владеет настройками
```python
@dataclass(frozen=True)
class Config:
    cube_host: str            # CUBE_HOST, default "192.168.100.54"
    figma_token: str | None   # FIGMA_TOKEN
    figma_project_id: str     # FIGMA_PROJECT_ID, default "450204584"
    telegram_api_id: int | None
    telegram_api_hash: str | None
    lat: float; lon: float; tz: str   # default Nha Trang 12.2388, 109.1967, "Asia/Ho_Chi_Minh"
    data_dir: Path            # ~/Library/Application Support/smalltv-cube
def load_config() -> Config
```

### `cube/model.py` — общие типы (данные, без логики)
```python
@dataclass
class Notification:
    source: Literal["figma", "telegram", "claude_limit", "claude_waiting"]
    title: str        # «Анна · Лендинг v3» / «Claude ждёт ответа»
    body: str         # первая строка текста, ≤ 120 симв.
    created_at: datetime
    key: str          # стабильный id для дедупликации

@dataclass
class Weather:
    temp_c: float; code: int; label_ru: str; fetched_at: datetime

@dataclass
class ClaudeUsage:
    used_pct: float; resets_at: datetime | None

@dataclass
class Snapshot:       # всё, что нужно нарисовать часы
    now: datetime
    weather: Weather | None
    usage: ClaudeUsage | None
    badges: dict[str, int]        # {"figma": 2, "telegram": 5}
    claude_waiting: int           # число ждущих сессий, 0 = нет
```

### `cube/device.py` — владеет общением с кубиком
```python
class CubeClient:
    def __init__(self, host: str, timeout: float = 5.0)
    def is_online(self) -> bool                 # GET /v.json
    def prepare(self) -> None                   # /set?theme=3, /set?i_i=…&autoplay=0
    def show(self, data: bytes, ext: Literal["jpg", "gif"]) -> None
        # upload /doUpload?dir=/image/ как cube-<n>.<ext>, /set?img=/image/<файл>,
        # затем удалить свой предыдущий файл. Бросает CubeOffline.
class CubeOffline(Exception)
```

### `cube/render.py` — владеет внешним видом (чистые функции, без сети)
```python
SIZE = 240
def render_clock(s: Snapshot) -> Image.Image
def render_card(n: Notification, s: Snapshot) -> Image.Image          # конечный кадр карточки
def render_card_intro(n: Notification, s: Snapshot) -> list[tuple[Image.Image, int]]  # кадры GIF + длительность мс
def encode_jpeg(img) -> bytes
def encode_gif(frames) -> bytes
```

### `cube/sources/*` — каждый источник: один класс
```python
class Source(Protocol):
    name: str
    interval_s: int
    def poll(self) -> SourceResult   # не бросает; ошибки → result.error

@dataclass
class SourceResult:
    notifications: list[Notification] = field(default_factory=list)
    badge: int | None = None          # None = источник не трогает счётчик
    weather: Weather | None = None
    usage: ClaudeUsage | None = None
    waiting: int | None = None
    error: str | None = None
```
Файлы: `weather.py` (WeatherSource), `figma.py` (FigmaSource), `telegram.py` (TelegramSource — держит клиент Telethon в своём потоке, `poll()` отдаёт накопленное), `claude_usage.py` (ClaudeUsageSource), `claude_waiting.py` (ClaudeWaitingSource — читает файл состояния хуков). Источник без ключей в `.env` не создаётся.

Состояние «уже видел» (Figma — id комментариев, лимиты — какие пороги уже показаны в окне) — в `data_dir/state.json` через `cube/store.py`:
```python
class Store:
    def __init__(self, path: Path)
    def get(self, key: str, default=None); def set(self, key: str, value) -> None   # атомарная запись
```

### `cube/hook.py` — точка входа для хуков Claude Code
```python
# python -m cube.hook waiting|answered   (JSON хука на stdin, берётся session_id)
# пишет data_dir/claude_sessions.json: {session_id: {"waiting": bool, "at": iso}}
```
Записи старше 12 часов игнорируются.

### `cube/app.py` — главный цикл, владеет очередью и расписанием
```python
class App:
    def __init__(self, cfg: Config, device: CubeClient, sources: list[Source], clock: Callable[[], datetime] = ...)
    def tick(self) -> None     # один шаг: опросить созревшие источники, обновить Snapshot, решить кадр, отправить если изменился
    def run_forever(self) -> None
```
Очередь уведомлений, 15 с на карточку, сводная карточка «ещё N», сброс счётчиков через час, повтор при CubeOffline раз в 30 с — всё здесь.

### `cube/__main__.py` — команды
`run` · `preview <папка>` · `telegram-login` · `install` · `uninstall` · `status`

`install`: LaunchAgent `~/Library/LaunchAgents/ru.designbynikita.smalltv-cube.plist` (RunAtLoad, KeepAlive), запуск под `caffeinate -i`; дописывает хуки в `~/.claude/settings.json` (Stop, Notification → waiting; UserPromptSubmit → answered), не трогая существующие. `uninstall` убирает ровно своё.

## Швы для тестов
- `CubeClient` ← фейк, записывающий показанные кадры.
- `Source` ← фейки с заданными `SourceResult`.
- `App(clock=…)` — подменяемое время.
- `render.*` — чистые функции, проверяются по размеру/непустоте и через `preview`.

## Что построили законченные таски

### Таск 01
- `CubeClient(host, timeout=5.0, transport=None)`; `prepare()` удаляет оставшиеся с прошлого запуска `cube-*`.
- `WeatherSource(lat, lon, transport=None)`, name="weather", interval 900 с.
- `render.SOURCES`, `render.weather_kind(code)`.
- `cube.sources.build_sources(cfg)` импортирует `cube.sources.{figma,telegram,claude_usage,claude_waiting}`, если модуль есть, и вызывает в нём `create(cfg) -> Source | None`.
- `__main__`: `telegram-login` → `cube.sources.telegram.login(cfg)`; `install`/`uninstall` → `cube.install.install(cfg)` / `uninstall(cfg)`.
- Необязательные .env: CUBE_DATA_DIR, CUBE_LAT, CUBE_LON, CUBE_TZ.
- Счётчик бейджа растёт по `result.badge`; полоска лимита прячется, если 15 мин нет свежих `usage`.

### Таск 02
- `base.Background`: `start()`, `fetch() -> SourceResult` в своём потоке раз в `every_s`, `poll()` отдаёт накопленное.
- `FigmaSource(token, project_id, store, transport=None)`; `ClaudeUsageSource(store, tz, token=keychain_token, transport=None)`; `TelegramSource` (`on_message`/`on_read` async, `start(cfg)`); `telegram.login(cfg)`, `session_path(cfg)`; `ClaudeWaitingSource(path)`.
- Состояние источников — отдельные файлы `figma.json`, `claude_usage.json` в data_dir.
- `hook.record(path, session_id, waiting, project)`, файл `claude_sessions.json` `{sid: {waiting, at, project}}`.
- `install(cfg, settings=~/.claude/settings.json, agents=~/Library/LaunchAgents, launchctl=True)` / `uninstall(...)`; хуки Stop, Notification → waiting; UserPromptSubmit, SessionEnd → answered; метка `-m cube.hook`; копия `settings.json.smalltv-cube.bak`.

### F1
- `hook.record(path, session_id, waiting, project="", event="")` — event = hook_event_name.
- Формат error: "<источник>: HTTP <status>" или "<источник>: <ИмяТипа>".
