from django.shortcuts import render


def home(request):
    """Бас бет-толтырғыш. Нақты Dashboard 17-тапсырмада жасалады."""
    return render(request, "home.html")
