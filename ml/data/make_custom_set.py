"""3-тапсырма, 5-тармақ: қолдан жасалған (жасанды) орысша/қазақша SMS жиыны.

Барлығы ЖАСАНДЫ. Нақты телефон, карта, жеке деректер жоқ.
Сілтемелер тек сақталған домендерде (.example, .test).
Нәтиже: data/raw/custom_ru_kk.csv  (100 ru + 50 kk, шамамен 50% алаяқтық)

Пайдалану:  python -m ml.data.make_custom_set --author "Аты-жөніңіз"
"""
from __future__ import annotations

import argparse
import csv
import random

from .paths import RAW

URLS = [
    "http://secure-bank-verify.example/login", "http://post-delivery-pay.example",
    "http://bank-kz-verify.test", "http://prize-claim.example/win",
    "http://account-update.example/confirm", "http://gov-fine-pay.test/check",
    "http://bit.ly/prize-claimtest", "http://192.0.2.15/account-update",
]
TIMES = ["09:00", "10:30", "12:00", "14:15", "16:45", "18:00", "19:30", "20:00"]
DAYS_RU = ["завтра", "в понедельник", "в пятницу", "в субботу", "послезавтра"]
DAYS_KK = ["ертең", "дүйсенбіде", "жұмада", "сенбіде", "бүрсігүні"]
SUMS = ["5 000", "12 000", "25 000", "50 000", "150 000", "300"]
NUMS = ["4821", "7730", "1096", "5512", "3347", "9084"]

RU_SAFE = [
    "Привет! Встречаемся {day} в {t} у входа в библиотеку.",
    "Ваш заказ №{n} отправлен и будет доставлен {day}.",
    "Мам, я буду дома в {t}. Купить хлеба?",
    "Напоминаем: приём у врача {day} в {t}. Возьмите паспорт.",
    "Собрание команды {day} в {t}, ссылка на комнату в календаре.",
    "С днём рождения! Желаю здоровья и счастья, увидимся {day}.",
    "Ваш код подтверждения: {n}. Никому не сообщайте этот код.",
    "Занятие по английскому переносится на {t}, {day}.",
]
RU_FRAUD = [
    "Ваша карта заблокирована! Срочно подтвердите данные по ссылке: {url}",
    "Поздравляем! Вы выиграли приз {s} тенге. Получите выигрыш: {url}",
    "Сотрудник службы безопасности банка: назовите код из SMS для отмены операции.",
    "Мама, у меня проблемы, срочно переведи {s} на этот номер, потом всё объясню. Никому не говори.",
    "Ваша посылка ожидает оплаты таможенного сбора {s} ₸: {url}",
    "Ваш аккаунт будет заблокирован в течение 24 часов. Подтвердите пароль: {url}",
    "Вам назначен штраф. Оплатите немедленно, иначе счёт будет арестован: {url}",
    "Инвестиции: гарантированный доход 30% в день! Успейте вступить сегодня: {url}",
]
KK_SAFE = [
    "Сәлем! {day} сағат {t}-де кездесеміз бе?",
    "Сабақ {t}-де басталады, кешікпе.",
    "Тапсырыс №{n} жеткізілді. Рақмет!",
    "Анашым, жұмыстан {t}-де ораламын.",
    "Жиналыс {day} {t}-де болады.",
    "Туған күніңмен! Денсаулық пен бақыт тілеймін!",
    "Дәрігерге жазылу {day} сағат {t}-де.",
    "Кешкі асқа үйге келесің бе?",
]
KK_FRAUD = [
    "Картаңыз бұғатталды! Жедел түрде мына сілтеме арқылы растаңыз: {url}",
    "Құттықтаймыз! Сіз {s} теңге ұтып алдыңыз. Сыйлықты алу үшін: {url}",
    "Банк қызметкері: күдікті операцияны тоқтату үшін SMS-тегі кодты айтыңыз.",
    "Анашым, жағдайым жаман, шұғыл {s} теңге аудар. Ешкімге айтпа.",
    "Сіздің посылкаңыз кеденде тұр. {s} теңге төлеңіз: {url}",
    "Шотыңыз 24 сағат ішінде жабылады. Құпия сөзді жаңарту үшін: {url}",
    "Айыппұл тағайындалды. Төлемесеңіз есепшот бұғатталады: {url}",
    "Инвестиция: күніне 30% табыс кепілдік! Тез арада қосылыңыз: {url}",
]


def _make(templates: list[str], days: list[str], n: int, rng: random.Random) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    guard = 0
    while len(out) < n and guard < 10_000:
        guard += 1
        t = rng.choice(templates).format(
            day=rng.choice(days), t=rng.choice(TIMES), n=rng.choice(NUMS),
            s=rng.choice(SUMS), url=rng.choice(URLS),
        )
        t = t[0].upper() + t[1:]
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def build(author: str, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    spec = [("ru", RU_SAFE, RU_FRAUD, DAYS_RU, 50), ("kk", KK_SAFE, KK_FRAUD, DAYS_KK, 25)]
    for lang, safe_t, fraud_t, days, per_class in spec:
        for label, tpls in ((0, safe_t), (1, fraud_t)):
            for text in _make(tpls, days, per_class, rng):
                rows.append({"text": text, "label": label, "lang": lang, "author": author})
    rng.shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = i
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default="student", help="Белгілеуші авторы (есепке жазылады)")
    args = ap.parse_args()
    rows = build(args.author)
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "custom_ru_kk.csv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "text", "label", "lang", "author"])
        w.writeheader()
        w.writerows(rows)
    ru = sum(r["lang"] == "ru" for r in rows)
    kk = sum(r["lang"] == "kk" for r in rows)
    print(f"Сақталды: {out}  (ru={ru}, kk={kk}, алаяқтық={sum(r['label'] for r in rows)})")


if __name__ == "__main__":
    main()
