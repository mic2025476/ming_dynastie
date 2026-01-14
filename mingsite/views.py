from django.shortcuts import render


def index(request):
    context = {
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
                {
                    "image": "mingsite/img/hero-1.jpg",
                    "alt": "Restaurant Innenraum der Ming Dynastie",
                },
                {
                    "image": "mingsite/img/hero-2.jpg",
                    "alt": "Festlich gedeckter Tisch in der Ming Dynastie",
                },
                {
                    "image": "mingsite/img/hero-3.jpg",
                    "alt": "Traditionelle chinesische Speisen",
                },
            ],
            "logo": "mingsite/img/logo.png",
            "social_links": [
                {
                    "slug": "instagram",
                    "title": "Instagram",
                    "href": "https://www.instagram.com/ming_dynastie/",
                    "icon": "mingsite/icons/instagram.png",
                },
                {
                    "slug": "facebook",
                    "title": "Facebook",
                    "href": "https://www.facebook.com/restaurantmingdynastie",
                    "icon": "mingsite/icons/facebook.png",
                },
                {
                    "slug": "whatsapp",
                    "title": "WhatsApp",
                    "href": "https://wa.me/01771688168",
                    "icon": "mingsite/icons/whatsapp.png",
                },
            ],
            "nav_links": [
                {"label": "START", "href": "#start"},
                {"label": "LOCATIONS", "href": "#locations"},
                {"label": "SPEISEKARTE", "href": "#speisekarte"},
                {"label": "TAKEAWAY / DELIVERY", "href": "#delivery"},
                {"label": "GALERIE", "href": "#galerie"},
                {"label": "KONTAKT", "href": "#kontakt"},
            ],
            "contact_links": [
                {
                    "type": "phone",
                    "title": "Telefonnummer",
                    "display": "030 308 756 80",
                    "href": "tel:03030875680",
                },
            ],
            "reserve_link": {
                "label": "Jetzt Reservieren",
                "href": "#kontakt",
            },
            "ctas": [
                {"label": "Reservieren", "href": "#kontakt"},
                {"label": "Speisekarten", "href": "#speisekarte", "variant": "outline"},
            ],
        },
        "locations": [
            {
                "anchor": "jannowitzbruecke",
                "name": "Ming Dynastie Jannowitzbrücke",
                "image": "https://cdn2.site-media.eu/images/1024%2C5118x3202%2B0%2B0/5999794/_M4B1325.jpg",
                "address_lines": ["Brückenstraße 6", "10179 Berlin"],
                "hours": "Mo - So: 12:00 - 22:00 Uhr",
                "description": (
                    "Tauchen Sie ein in die Welt der chinesischen Esskultur direkt neben der "
                    "chinesischen Botschaft! Unsere vielseitige Speisekarte garantiert ein "
                    "Geschmackserlebnis, das Ihre Sinne für immer prägen wird."
                ),
                "menu_label": "Zu den Speisekarten",
                "menu_href": "#speisekarte",
            },
            {
                "anchor": "europa-center",
                "name": "Ming Dynastie Europa-Center",
                "image": "https://cdn2.site-media.eu/images/1024%2C5760x3595%2B0%2B0/5999792/_M4B1125.jpg",
                "address_lines": ["Tauentzienstraße 9-12", "10789 Berlin"],
                "hours": "Mo - So: 12:00 - 22:00 Uhr",
                "description": (
                    "Erleben Sie echte chinesische Küche direkt neben der Gedächtniskirche – mitten "
                    "im Wahrzeichen West-Berlins. Unsere ausgefallene Karte bietet jedem "
                    "Feinschmecker genau die richtige Auswahl an Speisen."
                ),
                "menu_label": "Zu den Speisekarten",
                "menu_href": "#speisekarte",
            },
        ],
        "catering_cards": [
            {
                "title": "Catering",
                "image": "https://cdn2.site-media.eu/images/1920/5174611/_M4B1307.jpg",
                "align": "left",
                "copy": [
                    "Unser Service umfasst unter anderem die Anlieferung von Essen und Büffet Vorrichtungen inkl. Wärmeplatten.",
                    "Auf Wunsch auch mit Servicepersonal. Für ein individuelles Angebot sprechen Sie uns gerne an oder nutzen Sie unser Kontaktformular.",
                ],
                "button": {"label": "Zum Kontaktformular", "href": "#kontakt"},
            },
            {
                "title": "Events",
                "image": "https://cdn2.site-media.eu/images/1920/5167958/_M4B1322.jpg",
                "align": "right",
                "copy": [
                    "Gerne richten wir für Sie Firmenfeiern, Geburtstage, Hochzeiten und Events mit chinesischer Spezialitätenküche aus.",
                    "Hierfür bieten wir Ihnen die Räumlichkeiten in unseren Restaurants an oder beliefern einen von Ihnen gewählten Veranstaltungsort.",
                    "Zu unseren zufriedenen Kunden gehören unter anderem das Rote Rathaus, Q-Cells, das Chinesische Kulturzentrum, die chinesische Botschaft und Huawei.",
                ],
                "button": {"label": "Event planen", "href": "#kontakt"},
            },
        ],
        "delivery": {
            "note": (
                
            ),
            "services": [
                {
                    "location": "Ming Dynastie Jannowitzbrücke",
                    "links": [
                        {
                            "name": "Uber Eats",
                            "url": "https://www.ubereats.com/de/store/ming-dynastie-jannowitzbrucke/PYnM4OPTV8OXtpngj8PQ2g",
                            "logo": "mingsite/img/logo-ubereats.png",
                            "logo_alt": "Uber Eats",
                        },
                    ],
                },
                {
                    "location": "Ming Dynastie Europa-Center",
                    "links": [
                        {
                            "name": "Uber Eats",
                            "url": "https://www.ubereats.com/de/store/ming-dynastie-europa-center/Fhuc066PViOnIIq3Cc_sUA",
                            "logo": "mingsite/img/logo-ubereats.png",
                            "logo_alt": "Uber Eats",
                        },
                    ],
                },
            ],
        },
        "feast": {
            "title": "Feast Berlin",
            "description": (
                "Lorem ipsum dolor sitope amet, consectetur adipisicing elitip. Massumenda, dolore, "
                "cum vel modi asperiores consequatur suscipit quidem ducimus eveniet iure expedita "
                "consecteture odiogil voluptatum similique fugit voluptates atem accusamus quae quas "
                "dolorem tenetur facere tempora maiores adipisci reiciendis accusantium voluptatibus "
                "id voluptate tempore dolor harum nisi amet! Nobis, eaque. Aenean commodo ligula eget "
                "dolor. Lorem ipsum dolor sit amet, consectetuer adipiscing elit leget odiogil voluptatum "
                "similique fugit voluptates dolor. Libero assumenda, dolore, cum vel modi asperiores "
                "consequatur."
            ),
            "menu_links": [
                {"label": "Speisekarte", "url": "#"},
                {"label": "Getränkekarte", "url": "#"},
            ],
            "images": [
                "https://cdn2.site-media.eu/images/1010/5183023/MING_DYANASTIE-0955.jpg",
                "https://cdn2.site-media.eu/images/1920/5238025/red-wine-pouring-into-a-wine-glass-at-a-tasting-wine-sommeliers-serving-red-wine-in-glasses-free-photo.jpg",
            ],
        },
        "gallery_images": [
            "https://cdn2.site-media.eu/images/600x450%2C757x568%2B126%2B0/5183031/MING_DYANASTIE-0964.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C3776x2832%2B240%2B0/5181396/no013gebrateneteigtaschenschwein.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C725x544%2B142%2B0/5181025/MING_DYANASTIE-0960.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C725x544%2B142%2B0/5181018/MING_DYANASTIE-0954.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C3633x2725%2B230%2B0/5174605/Bild1.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C3633x2725%2B230%2B0/5174602/Bild2.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C3945x2959%2B246%2B0/5174596/L20.jpg",
            "https://cdn2.site-media.eu/images/600x450%2C3776x2832%2B240%2B0/5174694/Bild7.jpg",
        ],
        "testimonials": [
            {
                "quote": "Vielen Dank für das hervorragende Essen und der herzlichen Bedienung.",
                "author": "Sarah Tkotsch",
            },
            {
                "quote": "Chinesisches Essen auf dem Punkt.",
                "author": "Heino",
            },
            {
                "quote": "Das erste chinesische Restaurant, in dem auch Chinesen essen... Und das soll was heißen!",
                "author": "Maxi Warwel",
            },
            {
                "quote": "Trotz wolkenverhangenem Himmel, brennt mein Backen wie Feuer!",
                "author": "Benno Fürmann",
            },
            {
                "quote": "Peking Ente wie in Peking.",
                "author": "Peter Maffay",
            },
            {
                "quote": "Meine Freundin kam nach Haus mit den Worten: Hammah Lecker und... Recht hat sie!",
                "author": None,
            },
            {
                "quote": "Wunderbar!!... Nicht hungrig jetzt!",
                "author": "Simon Rattle",
            },
        ],
        "announcements": [
            {
                "title": "Liebe Gäste,",
                "body": [
                    "Die Ming Dynastie Jannowitzbrücke und Europa-Center öffnen Ihren Innen- und Außenbereich wieder für Sie!",
                    "Wir bitten Sie für den Innenbereich einen negativen Covid-19 Test oder einen Nachweis über Ihre Genesung/Impfung vorzuweisen.",
                    "Bitte beachten Sie weiterhin die geltenden Hygiene- und Abstandsregeln. Vielen Dank für Ihr Verständnis!",
                ],
            }
        ],
        "career": {
            "title": "Finance and Accounting Junior Finance Manager (Hybrid)",
            "apply_url": "https://docs.google.com/forms/d/e/1FAIpQLSdCBldNiLjKJUcVR3uEdW21u7GLujJS-ntgAVS_zy7JU7DPFg/viewform",
        },
        "reservations": [
            {
                "id": "reservierung-jannowitz",
                "title": "Reservierung Jannowitzbrücke",
                "phone": "030 30875680",
                "email": "mingeast@ming-dynastie.de",
                "address": "Brückenstraße 6, 10179 Berlin",
            },
            {
                "id": "reservierung-europa",
                "title": "Reservierung Europa-Center",
                "phone": "030 25759886",
                "email": "mingwest@ming-dynastie.de",
                "address": "Tauentzienstraße 9-12, 10789 Berlin",
            },
        ],
        "footer": {
            "company": "Ming Dynastie Jannowitzbrücke GmbH",
            "links": [
                {"label": "Impressum", "href": "/ming/legal/impressum/"},
                {"label": "Datenschutz", "href": "/ming/legal/datenschutz/"},
            ],
            "payment_icons": [
                "https://cdn2.site-media.eu/images/800x600%2C2200x1013%2B0%2B83/5260798/payment-icons.png",
            ],
        },
    }
    context["site_nav"] = context["hero"]["nav_links"]
    context["site_logo"] = context["hero"]["logo"]
    return render(request, "mingsite/index.html", context)
