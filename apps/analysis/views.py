from django.http import JsonResponse


def health(request):
    """Қосымша жұмыс істеп тұрғанын тексеру (2-тапсырма, 8-тармақ)."""
    return JsonResponse({"status": "ok"})

from django.shortcuts import render


def sms_check(request):
    result = None
    text = ""
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        # TODO: модель қосқанда нақты болжам шақырыңыз
        # from ml.predict import predict_sms
        # result = predict_sms(text)
        result = {
            "label": "spam",
            "probability": 92.4,
            "reasons": ["<url> белгісі бар", "<money> белгісі бар"],
        }
    return render(request, "sms_check.html", {"result": result, "text": text})


def url_check(request):
    result = None
    url = ""
    if request.method == "POST":
        url = request.POST.get("url", "").strip()
        # TODO: модель қосқанда нақты болжам шақырыңыз
        result = {
            "label": "phishing",
            "probability": 87.1,
            "features": {"url_length": len(url), "has_ip": False},
        }
    return render(request, "url_check.html", {"result": result, "url": url})