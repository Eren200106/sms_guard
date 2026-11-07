import os

# Тест кезінде .env болмауы мүмкін: уақытша мәндер қоямыз.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
