# SMS Guard

Интеллектуальная система обнаружения мошеннических SMS и подозрительных ссылок
(Django + scikit-learn). Здесь реализованы задания 1–10 из ТЗ.

## Запуск (Windows, PowerShell, 5–7 команд)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # затем заполните значения в .env
python manage.py check
python manage.py runserver
```

Если PowerShell запрещает скрипты: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Пример значений для `.env` (секрет сгенерируйте сами, в репозиторий не отправляйте):

```
DJANGO_SECRET_KEY=<длинная случайная строка>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Секрет можно получить так:
`python -c "import secrets; print(secrets.token_urlsafe(50))"`

Проверка: http://127.0.0.1:8000/ и http://127.0.0.1:8000/api/v1/health/ → `{"status": "ok"}`.

## Задания и команды

| Задание | Что | Команда / файл |
|---|---|---|
| 1 | Анализ предметной области | `docs/01_domain_analysis.md` (заполнить) |
| 2 | Каркас проекта | `python manage.py check` |
| 3 | Загрузка SMS | `python -m ml.data.download_datasets sms` → `python -m ml.data.load_sms` |
| 3 | Свой набор ru/kk | `python -m ml.data.make_custom_set --author "Имя"` |
| 4 | Предобработка | `python -m ml.preprocess_sms` ; тесты: `pytest tests/test_preprocessing.py` |
| 5 | EDA | `notebooks/01_eda_sms.ipynb` |
| 6 | Признаки TF-IDF | `python -m ml.features_sms` |
| 9 | Признаки URL | `ml/url_features.py` ; `pytest tests/test_url_features.py` |
| 10 | Датасет URL | `python -m ml.data.download_datasets url` → `python -m ml.data.prepare_url` |

Тесты: `pytest` (все), `pytest --cov=ml` (покрытие).

## Git: коммит после каждого задания

```powershell
git init
git add .
git commit -m "task-02: project skeleton"
git branch -M main
git remote add origin https://github.com/Eren200106/sms_guard.git
git push -u origin main
```

Сообщения следующих коммитов: `task-03: load SMS dataset`, `task-04: preprocessing`,
`task-05: EDA SMS dataset`, `task-06: TF-IDF features`, `task-09: URL features`, `task-10: URL dataset`.
Перед первым `git add .` убедитесь, что `.env` в `.gitignore` и не попадает в `git status`.

## Важно

- Ссылки анализируются только как строки, сетевых запросов нет.
- Все примеры сообщений искусственные.
- Модели (задания 7–8, 11) обучаются в следующих этапах; `ml/artifacts/` пока пуст.
- Заполните «паспорта» в `docs/` фактическими цифрами и датами.
