from django.shortcuts import render

def build_site_context():
    return {
        "hero": {
            "headline": "Ming Dynastie",
            "subheadline": "Chinesisches Restaurant in Berlin & Hamburg",
            "description": (
                "Feinste authentische Spezialitäten aus Fernostasien nur in der Ming Dynastie! "
                "Erleben Sie Asien ein Stückchen näher und lassen Sie sich zwischen schwingenden "
                "Woks und knetenden Dim Sum Meistern begeistern."
            ),
            "secondary_description": (
                "The finest authentic specialties from Far East Asia only in the Ming Dynasty. "
                "Be inspired by swinging woks and kneading dim sum masters and experience China "
                "a little closer."
            ),
            "slides": [
                {"image": "mingsite/img/hero-1.jpg", "alt": "Restaurant Innenraum der Ming Dynastie"},
                {"image": "mingsite/img/hero-2.jpg", "alt": "Festlich gedeckter Tisch in der Ming Dynastie"},
                {"image": "mingsite/img/hero-3.jpg", "alt": "Traditionelle chinesische Speisen"},
            ],
            "logo": "mingsite/img/logo.png",
            "social_links": [
                {"slug": "instagram", "title": "Instagram", "href": "https://www.instagram.com/ming_dynastie/", "icon": "mingsite/icons/instagram.png"},
                {"slug": "facebook", "title": "Facebook", "href": "https://www.facebook.com/restaurantmingdynastie", "icon": "mingsite/icons/facebook.png"},
                {"slug": "whatsapp", "title": "WhatsApp", "href": "https://wa.me/01771688168", "icon": "mingsite/icons/whatsapp.png"},
            ],
            "nav_links": [
                {"label": "START", "href": "/#start"},
                {"label": "LOCATIONS", "href": "/#locations"},
                {"label": "SPEISEKARTE", "href": "/#speisekarte"},
                {"label": "TAKEAWAY / DELIVERY", "href": "/#delivery"},
                {"label": "GALERIE", "href": "/#galerie"},
                {"label": "KONTAKT", "href": "/#kontakt"},
            ],
        },
        "footer": {
            "company": "Ming Dynastie Jannowitzbrücke GmbH",
            "links": [
                {"label": "Impressum", "href": "/legal/impressum/"},
                {"label": "Datenschutz", "href": "/legal/datenschutz/"},
            ],
            "payment_icons": [
                "https://cdn2.site-media.eu/images/800x600%2C2200x1013%2B0%2B83/5260798/payment-icons.png",
            ],
        },
    }

def impressum(request):
    context = build_site_context()
    context["site_nav"] = context["hero"]["nav_links"]
    context["site_logo"] = context["hero"]["logo"]
    return render(request, "legal/impressum.html", context)

def datenschutz(request):
    context = build_site_context()
    context["site_nav"] = context["hero"]["nav_links"]
    context["site_logo"] = context["hero"]["logo"]
    return render(request, "legal/datenschutz.html", context)
