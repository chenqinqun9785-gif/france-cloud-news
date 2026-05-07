"""RSS query definitions for French cloud computing news tracking."""

BASE_URL = "https://news.google.com/rss/search"
HL = "fr"
GL = "FR"
CEID = "FR:fr"

# Category display labels (Chinese for the UI)
CATEGORY_LABELS = {
    "public_cloud": "公有云市场 Public Cloud",
    "private_cloud": "私有云市场 Private Cloud",
    "policy": "政策与监管 Policy & Regulation",
}

# Importance levels
IMPORTANCE_LABELS = {
    "high": "重要",
    "medium": "一般",
    "low": "低",
}

IMPORTANCE_STARS = {
    "high": "★★★",
    "medium": "★★",
    "low": "★",
}

IMPORTANCE_COLORS = {
    "high": "#F59E0B",
    "medium": "#9CA3AF",
    "low": "#4B5563",
}

# Event type labels and colors
EVENT_TYPES = {
    "product": {"label": "产品发布", "color": "#10B981", "icon": "🆕"},
    "partnership": {"label": "商务合作", "color": "#3B82F6", "icon": "🤝"},
    "ma_finance": {"label": "资本与架构", "color": "#F97316", "icon": "💰"},
    "financial": {"label": "财务表现", "color": "#8B5CF6", "icon": "📊"},
    "policy": {"label": "政策监管", "color": "#EC4899", "icon": "📜"},
    "general": {"label": "综合动态", "color": "#6B7280", "icon": "📰"},
}

# Provider brand colors for badges
PROVIDER_COLORS = {
    "AWS": "#FF9900",
    "Azure": "#0078D4",
    "GCP": "#4285F4",
    "Huawei Cloud": "#CF0A2C",
    "Alibaba Cloud": "#FF6A00",
    "VMware": "#607078",
    "Nutanix": "#1D6F93",
    "Red Hat": "#EE0000",
    "OVHcloud": "#002395",
}

QUERIES = [
    # ── Public Cloud ──
    {
        "q": '(AWS OR "Amazon Web Services") France (cloud OR "data center" OR région OR annonce OR partenariat)',
        "category": "public_cloud",
        "provider": "AWS",
    },
    {
        "q": '("Microsoft Azure" OR Azure) France (cloud OR "data center" OR annonce OR partenariat)',
        "category": "public_cloud",
        "provider": "Azure",
    },
    {
        "q": '("Google Cloud" OR GCP) France (cloud OR "data center" OR région OR annonce)',
        "category": "public_cloud",
        "provider": "GCP",
    },
    {
        "q": '"Huawei Cloud" France',
        "category": "public_cloud",
        "provider": "Huawei Cloud",
    },
    {
        "q": '"Alibaba Cloud" France',
        "category": "public_cloud",
        "provider": "Alibaba Cloud",
    },
    {
        "q": 'France cloud (partenariat OR acquisition OR "levée de fonds" OR investissement OR fusion)',
        "category": "public_cloud",
        "provider": None,
    },
    # ── Private Cloud ──
    {
        "q": 'VMware France (cloud OR datacenter OR virtualisation OR annonce OR partenariat)',
        "category": "private_cloud",
        "provider": "VMware",
    },
    {
        "q": "Nutanix France (cloud OR datacenter OR annonce OR partenariat)",
        "category": "private_cloud",
        "provider": "Nutanix",
    },
    {
        "q": '("Red Hat" OR RedHat) France (cloud OR "open source" OR OpenShift OR annonce)',
        "category": "private_cloud",
        "provider": "Red Hat",
    },
    # ── French Cloud Policy ──
    {
        "q": 'France (SecNumCloud OR "cloud de confiance" OR "cloud souverain" OR "cloud de confiance")',
        "category": "policy",
        "provider": None,
    },
    {
        "q": 'France "cloud computing" (réglementation OR loi OR ANSSI OR CNIL OR régulation OR souveraineté)',
        "category": "policy",
        "provider": None,
    },
    {
        "q": 'France ("data center" OR datacenter) (investissement OR ouverture OR création OR construction)',
        "category": "policy",
        "provider": None,
    },
    # ── French Cloud Providers (competitive context) ──
    {
        "q": "France (OVHcloud OR Outscale OR Scaleway OR OVH) cloud",
        "category": "policy",
        "provider": None,
    },
    # ── Policy Expansion (v2) ──
    {
        "q": 'France cloud "souveraineté numérique" OR "cloud souverain"',
        "category": "policy",
        "provider": None,
    },
    {
        "q": "France (cloud OR numérique) (politique OR stratégie OR gouvernement OR plan)",
        "category": "policy",
        "provider": None,
    },
    {
        "q": "France (cloud OR données) (réglementation OR régulation OR conformité OR GDPR)",
        "category": "policy",
        "provider": None,
    },
    {
        "q": 'France ("cloud computing" OR "informatique en nuage") industrie',
        "category": "policy",
        "provider": None,
    },
    {
        "q": "France (cloud OR hébergement) (santé OR finance OR public OR administration OR banque)",
        "category": "policy",
        "provider": None,
    },
    {
        "q": "France (numérique OR cloud OR données) (loi OR décret OR arrêté OR directive)",
        "category": "policy",
        "provider": None,
    },
]


def build_rss_url(query_dict):
    """Build a Google News RSS URL from a query config dict."""
    from urllib.parse import quote

    q = query_dict["q"]
    return f"{BASE_URL}?q={quote(q)}&hl={HL}&gl={GL}&ceid={CEID}"
