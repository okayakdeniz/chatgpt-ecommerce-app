import os
from dataclasses import dataclass
from .config import MIME_TYPE

@dataclass(frozen=True)
class EcommerceWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "widget_html.html")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    E_COMMERCE_HTML = f.read()


widget = EcommerceWidget(
    identifier="ecommerce-widget",
    title="Mini E-Ticaret",
    template_uri="ui://widget/ecommerce.html",
    invoking="Widget hazırlanıyor…",
    invoked="Widget hazır.",
    html=E_COMMERCE_HTML,
)
