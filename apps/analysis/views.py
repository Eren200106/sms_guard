from django.http import JsonResponse


def health(request):
    """Қосымша жұмыс істеп тұрғанын тексеру (2-тапсырма, 8-тармақ)."""
    return JsonResponse({"status": "ok"})
