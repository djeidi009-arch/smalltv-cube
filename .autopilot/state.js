window.STATE =
{
  "version": 2,
  "slug": "smalltv-cube",
  "dir": "2026-11-11-smalltv-cube--wip",
  "title": "Кубик-экран: часы, погода и уведомления",
  "mode": "semi",
  "depth": "normal",
  "tier": "T1",
  "briefFile": "2026-11-11-brief.md",
  "memoryFile": "AGENTS.md",
  "memoryOwner": "autopilot",
  "skillDir": "/Users/nikitacernomyrdin/.agents/skills/autopilot",
  "baseCommit": null,
  "startedAt": "2026-11-11T16:22:14+07:00",
  "updatedAt": "2026-11-11T16:28:49+07:00",
  "finishedAt": null,
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
      "status": "active",
      "startedAt": "2026-11-11T16:28:49+07:00"
    },
    {
      "id": "build",
      "status": "pending"
    },
    {
      "id": "review",
      "status": "pending"
    },
    {
      "id": "final",
      "status": "pending"
    }
  ],
  "requirements": {
    "total": 19,
    "done": 0,
    "inTicket": 19,
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
      "status": "pending",
      "retries": 0,
      "repairs": 0
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
      "status": "pending",
      "retries": 0,
      "repairs": 0
    }
  ],
  "tests": null,
  "debt": {
    "placeholders": [],
    "assumptions": [],
    "emptyEnv": []
  },
  "additions": [],
  "coverage": {
    "found": 0,
    "fixed": 0,
    "deferred": 0,
    "items": []
  },
  "concerns": [],
  "blind": null,
  "beats": [
    "2026-11-11T16:22:14+07:00",
    "2026-11-11T16:22:26+07:00",
    "2026-11-11T16:22:44+07:00",
    "2026-11-11T16:23:04+07:00",
    "2026-11-11T16:26:18+07:00",
    "2026-11-11T16:28:46+07:00",
    "2026-11-11T16:28:49+07:00"
  ],
  "rev": 12,
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
    }
  ],
  "reqList": [
    {
      "id": "R01",
      "text": "«Настольный кубик-экран 240×240 (китайский клон GeekMagic SmallTV, IP: 192.168.100.54) в моём Wi‑Fi»",
      "status": "in-ticket"
    },
    {
      "id": "R02",
      "text": "«Mac mini рисует картинки»",
      "status": "in-ticket"
    },
    {
      "id": "R03",
      "text": "«и отправляет их на кубик»",
      "status": "in-ticket"
    },
    {
      "id": "R04",
      "text": "«Обычный режим: часы»",
      "status": "in-ticket"
    },
    {
      "id": "R05",
      "text": "«и погода»",
      "status": "in-ticket"
    },
    {
      "id": "R06",
      "text": "«Поверх них уведомления»",
      "status": "in-ticket"
    },
    {
      "id": "R07",
      "text": "«новые комментарии в Figma»",
      "status": "in-ticket"
    },
    {
      "id": "R08",
      "text": "«новые сообщения в Telegram»",
      "status": "in-ticket"
    },
    {
      "id": "R09",
      "text": "«лимиты Claude Code (5‑часовое окно»",
      "status": "in-ticket"
    },
    {
      "id": "R10",
      "text": "«и время сброса)»",
      "status": "in-ticket"
    },
    {
      "id": "R11",
      "text": "«сигнал «Claude ждёт ответа»»",
      "status": "in-ticket"
    },
    {
      "id": "R12",
      "text": "«При разработки бери скилы по анимации»",
      "status": "in-ticket"
    },
    {
      "id": "R13",
      "text": "«и ux дизайну из установленных»",
      "status": "in-ticket"
    },
    {
      "id": "R14i",
      "text": "(подразумевается) работает само, постоянно, переживает перезагрузку Mac mini",
      "status": "in-ticket"
    },
    {
      "id": "R15i",
      "text": "(подразумевается) погода — для какого города",
      "status": "in-ticket"
    },
    {
      "id": "R16i",
      "text": "(подразумевается) Figma — из каких файлов брать комментарии",
      "status": "in-ticket"
    },
    {
      "id": "R17i",
      "text": "(подразумевается) Telegram — вход в аккаунт и что показывать из сообщения",
      "status": "in-ticket"
    },
    {
      "id": "R18i",
      "text": "(подразумевается) несколько уведомлений подряд, сколько висит, когда исчезает",
      "status": "in-ticket"
    },
    {
      "id": "R19i",
      "text": "(подразумевается) кубик или интернет недоступны — ничего не падает",
      "status": "in-ticket"
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
      "at": "2026-11-11T16:28:49+07:00",
      "problems": 0
    }
  },
  "result": null
}
