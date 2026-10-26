# Desk Research: разговоры об AI

Система собирает материалы об AI из Hacker News, arXiv и Хабра, отдает их модели на разбор и показывает находки на странице: какая компания упоминается и о чем материал.

```
источники -> collector -> Postgres -> worker (модель) -> Postgres -> web (страница)
```

Четыре блока, каждый со своей работой:

| Блок | Что делает | Файл |
|---|---|---|
| collector | собирает материалы из источников, один проход и выход | `collector/main.py` |
| Postgres | хранит источники, материалы, находки и прогоны | `db/schema.sql` |
| worker | раз в 10 секунд берет новые материалы и отдает их модели | `worker/main.py` |
| web | показывает схему блоков, счетчики и последние находки | `web/main.py` |

Код один на все блоки: `main.py` запускает тот блок, как называется сервис на Railway (`web`, `collector`, `worker`). Локально блок передается аргументом: `python main.py web`.

## Поднять у себя на Railway

### Кнопкой

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/bFTvXF)

Railway создаст проект: Postgres и три сервиса из этого репозитория. Попросит один ключ, `OPENROUTER_API_KEY`, его берут на https://openrouter.ai/keys. Когда все сервисы позеленеют, откройте адрес сервиса web.

collector проходит источники сразу после деплоя, дальше по расписанию раз в шесть часов (по UTC). Первые находки появляются через несколько минут после того, как все сервисы позеленеют.

### Руками

1. Сделайте форк этого репозитория.
2. В Railway создайте проект, добавьте в него Postgres.
3. Добавьте три сервиса из своего форка, назовите их `web`, `collector`, `worker`. Имена важны: по ним `main.py` выбирает блок.
4. Каждому сервису добавьте переменную `DATABASE_URL` со значением `${{Postgres.DATABASE_URL}}`. Сервису worker добавьте еще `OPENROUTER_API_KEY`.
5. У web в настройках включите публичный адрес (Networking, Generate Domain).
6. У collector в настройках задайте расписание (Cron Schedule), например `0 */6 * * *`: раз в шесть часов. Без расписания он пройдет источники один раз при запуске.

Railway берет деньги за использование. Поставьте лимит расходов в Usage.

## Поднять на своем компьютере

Нужны Python 3.12 и Postgres.

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # впишите свои значения
set -a; source .env; set +a
python main.py collector    # собрать материалы, проходит один раз и выходит
```

worker и web работают, пока их не остановить (Ctrl+C), поэтому каждый запускается в своем окне терминала. В каждом новом окне сначала `source .venv/bin/activate` и `set -a; source .env; set +a`.

```
python main.py worker       # окно 2: разбирает материалы моделью
python main.py web          # окно 3: страница на http://localhost:8000
```

Таблицы создаются сами при первом запуске любого блока.

## Покрутить данные без запуска

В `props/` лежит выгрузка 65 находок от 26.10.2026: `findings.csv` для таблиц и `findings.sqlite` для запросов. В SQLite две таблицы, `sources` и `findings`.

```
sqlite3 props/findings.sqlite "SELECT company, count(*) FROM findings WHERE company <> '' GROUP BY company ORDER BY 2 DESC;"
sqlite3 props/findings.sqlite "SELECT s.name, f.summary FROM findings f JOIN sources s ON s.id = f.source_id LIMIT 10;"
```

То же можно попросить у агента: «открой props/findings.sqlite и покажи, сколько находок по каждой компании».

Примеры запросов к Postgres лежат в `db/queries.sql`.

## Что поменять под свой рынок

- Источники: список в конце `db/schema.sql`. Поддерживаются три вида: `hn` (поиск Hacker News), `arxiv`, `rss`.
- Сколько материалов брать из источника за проход: `MAX_PER_SOURCE` в `collector/main.py`.
- Какие компании ищет модель: список `ENTITIES` в `worker/main.py`. Там же текст запроса к модели.
- Модель: переменная `MODEL`, по умолчанию `anthropic/claude-haiku-5.5` через OpenRouter.
