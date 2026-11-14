from django.shortcuts import render


def home(request):
    """Бас бет-толтырғыш. Нақты Dashboard 17-тапсырмада жасалады."""
    return render(request, "home.html")

from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def dashboard(request):
    stats = {"total": 1240, "spam": 312, "ham": 928, "accuracy": 96.7}
    recent = []  # кейін queryset-пен ауыстырыңыз
    return render(request, "dashboard.html", {"stats": stats, "recent": recent})