window.STATE =
{
  "version": 2,
  "slug": "smalltv-cube",
  "dir": "2026-11-11-smalltv-cube",
  "title": "Кубик-экран: часы, погода и уведомления",
  "mode": "semi",
  "depth": "normal",
  "tier": "T1",
  "briefFile": "2026-11-11-brief.md",
  "memoryFile": "AGENTS.md",
  "memoryOwner": "autopilot",
  "skillDir": "/Users/nikitacernomyrdin/.agents/skills/autopilot",
  "baseCommit": "8b4b127",
  "startedAt": "2026-11-11T16:22:14+07:00",
  "updatedAt": "2026-11-11T17:29:23+07:00",
  "finishedAt": "2026-11-11T17:29:23+07:00",
  "stages": [
    {
      "id": "preflight",
      "status": "done",
      "startedAt": "2026-11-11T16:22:14+07:00",
      "finishedAt": "2026-11-11T16:22:26+07:00"
    },
    {
      "id": "manifest",
      "status": "done",
      "startedAt": "2026-11-11T16:22:26+07:00",
      "finishedAt": "2026-11-11T16:22:44+07:00"
    },
    {
      "id": "briefing",
      "status": "done",
      "startedAt": "2026-11-11T16:22:44+07:00",
      "finishedAt": "2026-11-11T16:26:18+07:00"
    },
    {
      "id": "spec",
      "status": "done",
      "startedAt": "2026-11-11T16:26:18+07:00",
      "finishedAt": "2026-11-11T16:28:49+07:00"
    },
    {
      "id": "plan",
      "status": "done",
      "startedAt": "2026-11-11T16:28:49+07:00",
      "finishedAt": "2026-11-11T16:29:21+07:00"
    },
    {
      "id": "build",
      "status": "done",
      "startedAt": "2026-11-11T16:29:21+07:00",
      "finishedAt": "2026-11-11T16:47:27+07:00"
    },
    {
      "id": "review",
      "status": "done",
      "startedAt": "2026-11-11T16:47:27+07:00",
      "finishedAt": "2026-11-11T16:55:45+07:00"
    },
    {
      "id": "final",
      "status": "done",
      "startedAt": "2026-11-11T16:55:45+07:00",
      "finishedAt": "2026-11-11T17:29:23+07:00"
    }
  ],
  "requirements": {
    "total": 19,
    "done": 19,
    "inTicket": 0,
    "inSpec": 0,
    "placeholder": 0,
    "deferred": 0,
    "dropped": 0
  },
  "tickets": [
    {
      "id": "01",
      "title": "Часы с погодой на кубике и движок уведомлений",
      "requirements": [
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R12",
        "R13",
        "R15i",
        "R18i",
        "R19i"
      ],
      "blockedBy": [],
      "wave": 1,
      "zone": [
        "pyproject.toml",
        "cube/",
        "cube/sources/figma.py",
        "telegram.py",
        "claude_usage.py",
        "claude_waiting.py",
        "cube/hook.py",
        "cube/install.py",
        "tests/",
        "docs/design.md",
        ".env.example"
      ],
      "review": "да — фундамент",
      "model": "сильная",
      "status": "done",
      "startedAt": "2026-11-11T16:29:21+07:00",
      "finishedAt": "2026-11-11T16:42:16+07:00",
      "retries": 0,
      "repairs": 1,
      "repairFindings": [
        "счётчик, погасший через час, не зажигается тем же badge — тест"
      ],
      "tests": {
        "passed": 18,
        "failed": 0
      },
      "commit": "cbc4555"
    },
    {
      "id": "02",
      "title": "Figma, Telegram, лимиты Claude, «Claude ждёт» и автозапуск",
      "requirements": [
        "R07",
        "R08",
        "R09",
        "R10",
        "R11",
        "R14i",
        "R16i",
        "R17i"
      ],
      "blockedBy": [
        "01"
      ],
      "wave": 2,
      "zone": [
        "cube/sources/figma.py",
        "cube/sources/telegram.py",
        "cube/sources/claude_usage.py",
        "cube/sources/claude_waiting.py",
        "cube/hook.py",
        "cube/install.py",
        "cube/__main__.py",
        "tests/sources/",
        "tests/test_install.py",
        "tests/test_hook.py",
        "README.md"
      ],
      "review": "да — ключи и секреты (токен Claude из Связки ключей, Figma, сессия Telegram)",
      "model": "сильная",
      "status": "done",
      "startedAt": "2026-11-11T16:38:35+07:00",
      "finishedAt": "2026-11-11T16:47:27+07:00",
      "retries": 0,
      "repairs": 0,
      "tests": {
        "passed": 28,
        "failed": 0
      },
      "commit": "c08106e"
    },
    {
      "id": "F1",
      "title": "Правки по ревью ветки",
      "requirements": [
        "R05",
        "R07",
        "R08",
        "R11",
        "R14i",
        "R19i"
      ],
      "blockedBy": [],
      "wave": 3,
      "zone": [
        "cube/sources/weather.py",
        "cube/sources/figma.py",
        "cube/sources/telegram.py",
        "cube/sources/claude_waiting.py",
        "cube/install.py",
        "cube/hook.py",
        "cube/app.py",
        "cube/device.py",
        "tests/"
      ],
      "review": "да — ремонт ветки",
      "model": "сильная",
      "status": "done",
      "startedAt": "2026-11-11T16:51:22+07:00",
      "finishedAt": "2026-11-11T16:55:45+07:00",
      "retries": 0,
      "repairs": 0,
      "tests": {
        "passed": 36,
        "failed": 0
      },
      "commit": "10e9f54"
    },
    {
      "id": "F2",
      "title": "Кубик не «пропадает» из-за двойного Content-Length",
      "requirements": [
        "R03",
        "R06"
      ],
      "blockedBy": [],
      "wave": 4,
      "zone": [
        "cube/device.py",
        "tests/test_device.py"
      ],
      "review": "нет",
      "model": "сильная",
      "status": "done",
      "retries": 0,
      "repairs": 0,
      "startedAt": "2026-11-11T17:07:27+07:00",
      "finishedAt": "2026-11-11T17:28:51+07:00",
      "tests": {
        "passed": 40,
        "failed": 0
      },
      "commit": "4ba1356"
    }
  ],
  "tests": {
    "passed": 40,
    "failed": 0
  },
  "debt": {
    "placeholders": [],
    "assumptions": [],
    "emptyEnv": []
  },
  "additions": [
    "хук SessionEnd снимает «Claude ждёт» у закрытой сессии — ради R11"
  ],
  "coverage": {
    "found": 0,
    "fixed": 0,
    "deferred": 0,
    "items": []
  },
  "concerns": [
    "cube/sources/__init__.py:23 — исключение в create() роняет run при старте",
    "cube/app.py:64-85 — медленный poll задерживает кадр",
    "tests/test_app.py — тесты читают App.snapshot/current вне interfaces.md",
    "cube/device.py:42 — нет границы имени перед cube-",
    "cube/app.py:128-134 — GIF выезда может проиграться дважды",
    "cube/sources/telegram.py — живой Telethon не запускался, только фейки",
    "cube/sources/claude_usage.py — протухший токен (401) не обновляется, полоска скрыта",
    "cube/install.py:130-134 — симлинк settings.json заменяется файлом, права не сохраняются",
    "cube/install.py:161-162 — повторный install перезаписывает .bak",
    "cube/install.py:151-152 — uninstall удаляет исходно пустой hooks:{}",
    "cube/sources/figma.py:434, telegram.py:541 — в ошибку идёт str(e), а не тип+статус",
    "README.md:72 — журнал назван cube.log, а launchd пишет launchd.log",
    "история 18 — при ошибке лимита полоска прячется через 15 мин, а не сразу"
  ],
  "blind": {
    "checked": 12,
    "matched": 9,
    "mismatches": [
      "R03 — кубик иногда отвечает с двумя Content-Length, httpx считает его недоступным на 30 с; карточки теряются",
      "R06 — при этом сбое карточка не доходит или висит 32 с вместо 15",
      "R11 — ответ на запрос разрешения не гасит «Claude ждёт» до следующего запроса (по спецификации так и задумано)"
    ]
  },
  "beats": [
    "2026-11-11T16:22:14+07:00",
    "2026-11-11T16:22:26+07:00",
    "2026-11-11T16:22:44+07:00",
    "2026-11-11T16:23:04+07:00",
    "2026-11-11T16:26:18+07:00",
    "2026-11-11T16:28:46+07:00",
    "2026-11-11T16:28:49+07:00",
    "2026-11-11T16:29:08+07:00",
    "2026-11-11T16:29:21+07:00",
    "2026-11-11T16:38:35+07:00",
    "2026-11-11T16:40:34+07:00",
    "2026-11-11T16:42:16+07:00",
    "2026-11-11T16:45:15+07:00",
    "2026-11-11T16:47:27+07:00",
    "2026-11-11T16:51:22+07:00",
    "2026-11-11T16:54:17+07:00",
    "2026-11-11T16:55:45+07:00",
    "2026-11-11T17:07:26+07:00",
    "2026-11-11T17:07:27+07:00",
    "2026-11-11T17:28:51+07:00",
    "2026-11-11T17:29:23+07:00"
  ],
  "rev": 44,
  "waiting": null,
  "waits": [
    {
      "kind": "briefing",
      "from": "2026-11-11T16:23:04+07:00",
      "to": "2026-11-11T16:26:18+07:00"
    }
  ],
  "log": [
    {
      "t": "2026-11-11T16:22:14+07:00",
      "k": "init"
    },
    {
      "t": "2026-11-11T16:22:26+07:00",
      "k": "stage",
      "id": "manifest",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:22:44+07:00",
      "k": "stage",
      "id": "briefing",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:23:04+07:00",
      "k": "ask",
      "kind": "briefing",
      "note": "4 вопроса — Figma-файлы, Telegram, сон Mac mini, поведение уведомлений"
    },
    {
      "t": "2026-11-11T16:26:18+07:00",
      "k": "answered",
      "kind": "briefing"
    },
    {
      "t": "2026-11-11T16:26:18+07:00",
      "k": "gate",
      "g": "G1",
      "ok": false,
      "open": 19,
      "total": 19
    },
    {
      "t": "2026-11-11T16:26:18+07:00",
      "k": "stage",
      "id": "spec",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:28:46+07:00",
      "k": "tier",
      "v": "T1"
    },
    {
      "t": "2026-11-11T16:28:49+07:00",
      "k": "gate",
      "g": "G2",
      "ok": true,
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    {
      "t": "2026-11-11T16:28:49+07:00",
      "k": "stage",
      "id": "plan",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:28:49+07:00",
      "k": "tickets",
      "n": 2
    },
    {
      "t": "2026-11-11T16:28:49+07:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    },
    {
      "t": "2026-11-11T16:29:21+07:00",
      "k": "stage",
      "id": "build",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:29:21+07:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "start"
    },
    {
      "t": "2026-11-11T16:38:35+07:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "done",
      "tests": {
        "passed": 16,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:38:35+07:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "review"
    },
    {
      "t": "2026-11-11T16:38:35+07:00",
      "k": "ticket",
      "ids": [
        "02"
      ],
      "act": "start"
    },
    {
      "t": "2026-11-11T16:40:34+07:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "repair",
      "note": "счётчик, погасший через час, не зажигается тем же badge — тест"
    },
    {
      "t": "2026-11-11T16:40:34+07:00",
      "k": "add",
      "key": "concerns",
      "n": 5
    },
    {
      "t": "2026-11-11T16:42:16+07:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "done",
      "tests": {
        "passed": 18,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:45:15+07:00",
      "k": "ticket",
      "ids": [
        "02"
      ],
      "act": "done",
      "tests": {
        "passed": 28,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:45:15+07:00",
      "k": "ticket",
      "ids": [
        "02"
      ],
      "act": "review"
    },
    {
      "t": "2026-11-11T16:45:15+07:00",
      "k": "add",
      "key": "concerns",
      "n": 2
    },
    {
      "t": "2026-11-11T16:47:27+07:00",
      "k": "ticket",
      "ids": [
        "02"
      ],
      "act": "done",
      "tests": {
        "passed": 28,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:47:27+07:00",
      "k": "add",
      "key": "concerns",
      "n": 6
    },
    {
      "t": "2026-11-11T16:47:27+07:00",
      "k": "add",
      "key": "additions",
      "n": 1
    },
    {
      "t": "2026-11-11T16:47:27+07:00",
      "k": "stage",
      "id": "review",
      "act": "start"
    },
    {
      "t": "2026-11-11T16:51:22+07:00",
      "k": "tickets",
      "n": 3
    },
    {
      "t": "2026-11-11T16:51:22+07:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    },
    {
      "t": "2026-11-11T16:51:22+07:00",
      "k": "add",
      "key": "report",
      "n": 7
    },
    {
      "t": "2026-11-11T16:51:22+07:00",
      "k": "ticket",
      "ids": [
        "F1"
      ],
      "act": "start"
    },
    {
      "t": "2026-11-11T16:54:17+07:00",
      "k": "ticket",
      "ids": [
        "F1"
      ],
      "act": "done",
      "tests": {
        "passed": 36,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:54:17+07:00",
      "k": "ticket",
      "ids": [
        "F1"
      ],
      "act": "review"
    },
    {
      "t": "2026-11-11T16:55:45+07:00",
      "k": "ticket",
      "ids": [
        "F1"
      ],
      "act": "done",
      "tests": {
        "passed": 36,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T16:55:45+07:00",
      "k": "stage",
      "id": "final",
      "act": "start"
    },
    {
      "t": "2026-11-11T17:07:26+07:00",
      "k": "gate",
      "g": "G4",
      "ok": false,
      "checked": 12,
      "matched": 9
    },
    {
      "t": "2026-11-11T17:07:27+07:00",
      "k": "tickets",
      "n": 4
    },
    {
      "t": "2026-11-11T17:07:27+07:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    },
    {
      "t": "2026-11-11T17:07:27+07:00",
      "k": "ticket",
      "ids": [
        "F2"
      ],
      "act": "start"
    },
    {
      "t": "2026-11-11T17:28:51+07:00",
      "k": "ticket",
      "ids": [
        "F2"
      ],
      "act": "done",
      "tests": {
        "passed": 40,
        "failed": 0
      }
    },
    {
      "t": "2026-11-11T17:28:51+07:00",
      "k": "tests",
      "passed": 40,
      "failed": 0
    },
    {
      "t": "2026-11-11T17:28:51+07:00",
      "k": "add",
      "key": "report",
      "n": 1
    },
    {
      "t": "2026-11-11T17:29:23+07:00",
      "k": "finish",
      "result": "Кубик показывает часы, погоду, лимит Claude и «Claude ждёт»; Figma и Telegram готовы, ждут ключей"
    }
  ],
  "reqList": [
    {
      "id": "R01",
      "text": "«Настольный кубик-экран 240×240 (китайский клон GeekMagic SmallTV, IP: 192.168.100.54) в моём Wi‑Fi»",
      "status": "done"
    },
    {
      "id": "R02",
      "text": "«Mac mini рисует картинки»",
      "status": "done"
    },
    {
      "id": "R03",
      "text": "«и отправляет их на кубик»",
      "status": "done"
    },
    {
      "id": "R04",
      "text": "«Обычный режим: часы»",
      "status": "done"
    },
    {
      "id": "R05",
      "text": "«и погода»",
      "status": "done"
    },
    {
      "id": "R06",
      "text": "«Поверх них уведомления»",
      "status": "done"
    },
    {
      "id": "R07",
      "text": "«новые комментарии в Figma»",
      "status": "done"
    },
    {
      "id": "R08",
      "text": "«новые сообщения в Telegram»",
      "status": "done"
    },
    {
      "id": "R09",
      "text": "«лимиты Claude Code (5‑часовое окно»",
      "status": "done"
    },
    {
      "id": "R10",
      "text": "«и время сброса)»",
      "status": "done"
    },
    {
      "id": "R11",
      "text": "«сигнал «Claude ждёт ответа»»",
      "status": "done"
    },
    {
      "id": "R12",
      "text": "«При разработки бери скилы по анимации»",
      "status": "done"
    },
    {
      "id": "R13",
      "text": "«и ux дизайну из установленных»",
      "status": "done"
    },
    {
      "id": "R14i",
      "text": "(подразумевается) работает само, постоянно, переживает перезагрузку Mac mini",
      "status": "done"
    },
    {
      "id": "R15i",
      "text": "(подразумевается) погода — для какого города",
      "status": "done"
    },
    {
      "id": "R16i",
      "text": "(подразумевается) Figma — из каких файлов брать комментарии",
      "status": "done"
    },
    {
      "id": "R17i",
      "text": "(подразумевается) Telegram — вход в аккаунт и что показывать из сообщения",
      "status": "done"
    },
    {
      "id": "R18i",
      "text": "(подразумевается) несколько уведомлений подряд, сколько висит, когда исчезает",
      "status": "done"
    },
    {
      "id": "R19i",
      "text": "(подразумевается) кубик или интернет недоступны — ничего не падает",
      "status": "done"
    }
  ],
  "gates": {
    "G1": {
      "ok": false,
      "at": "2026-11-11T16:26:18+07:00",
      "open": 19,
      "total": 19
    },
    "G2": {
      "ok": true,
      "at": "2026-11-11T16:28:49+07:00",
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    "G3": {
      "ok": true,
      "at": "2026-11-11T17:07:27+07:00",
      "problems": 0
    },
    "G4": {
      "ok": false,
      "at": "2026-11-11T17:07:26+07:00",
      "checked": 12,
      "matched": 9
    }
  },
  "result": "Кубик показывает часы, погоду, лимит Claude и «Claude ждёт»; Figma и Telegram готовы, ждут ключей",
  "report": [
    "Figma не сообщает «прочитано» — счётчик Figma гаснет через час без новых",
    "При ошибке чтения лимита полоска прячется через 15 минут, а не сразу",
    "Если один файл Figma недоступен (403/429), в этот опрос не придут уведомления и из остальных файлов",
    "Без интернета часы могут на секунды подвисать раз в 15 минут — погода опрашивается в главном цикле",
    "Команда status ненадолго запускает источники, а не только перечисляет их",
    "Журнал пишется в два файла и не очищается сам",
    "Telegram проверен только на тестовых данных — первый настоящий вход покажет, всё ли работает",
    "Кубик отдаёт служебный заголовок дважды; если когда-нибудь числа в нём разойдутся, старые кадры программы могут не удалиться"
  ]
}
