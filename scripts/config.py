"""
French Cloud Ecosystem Tracker — Configuration (v3)
All classification rules, RSS queries, entity lists, and scoring parameters.
"""

BASE_URL = "https://news.google.com/rss/search"
HL = "fr"
GL = "FR"
CEID = "FR:fr"

# ═══════════════════════════════════════════════════════════
# 1. PRIMARY CATEGORIES (7 categories, v3)
# ═══════════════════════════════════════════════════════════

CATEGORIES = {
    "public_cloud": {
        "label": "公有云厂商",
        "label_fr": "Public Cloud Providers",
        "icon": "☁️",
        "color": "#3B82F6",
        "order": 1,
    },
    "private_hybrid": {
        "label": "私有云/混合云",
        "label_fr": "Private & Hybrid Cloud",
        "icon": "🖥️",
        "color": "#A855F7",
        "order": 2,
    },
    "sovereign_trusted": {
        "label": "主权云/可信云",
        "label_fr": "Sovereign & Trusted Cloud",
        "icon": "🛡️",
        "color": "#10B981",
        "order": 3,
    },
    "ecosystem_partners": {
        "label": "云生态合作伙伴",
        "label_fr": "Cloud Ecosystem Partners",
        "icon": "🤝",
        "color": "#F59E0B",
        "order": 4,
    },
    "ai_datacenter": {
        "label": "AI云与数据中心",
        "label_fr": "AI Cloud & Data Centers",
        "icon": "🧠",
        "color": "#EC4899",
        "order": 5,
    },
    "industry_cloud": {
        "label": "行业云/客户案例",
        "label_fr": "Industry Cloud & Client Cases",
        "icon": "🏭",
        "color": "#8B5CF6",
        "order": 6,
    },
    "policy_regulation": {
        "label": "政策监管",
        "label_fr": "Policy & Regulation",
        "icon": "📜",
        "color": "#F97316",
        "order": 7,
    },
}

# Backward compatibility: old 3-category → new 7-category mapping
CATEGORY_COMPAT = {
    "public_cloud": "public_cloud",
    "private_cloud": "private_hybrid",
    "policy": "policy_regulation",
}

# ═══════════════════════════════════════════════════════════
# 2. ENTITY DICTIONARY (providers, partners, regulators)
# ═══════════════════════════════════════════════════════════

ENTITIES = {
    # ── Public Cloud Providers ──
    "cloud_providers": {
        "AWS": {"aliases": ["Amazon Web Services", "amazon"], "color": "#FF9900"},
        "Azure": {"aliases": ["Microsoft Azure", "microsoft"], "color": "#0078D4"},
        "GCP": {"aliases": ["Google Cloud", "google cloud platform"], "color": "#4285F4"},
        "Oracle Cloud": {"aliases": ["oracle cloud infrastructure", "OCI"], "color": "#F80000"},
        "Huawei Cloud": {"aliases": ["huawei cloud", "华为云"], "color": "#CF0A2C"},
        "Alibaba Cloud": {"aliases": ["alibaba cloud", "阿里云"], "color": "#FF6A00"},
        "IBM Cloud": {"aliases": ["ibm cloud", "IBM"], "color": "#052FAD"},
    },

    # ── Private / Hybrid Cloud Vendors ──
    "private_hybrid_vendors": {
        "VMware": {"aliases": ["VMware", "broadcom vmware"], "color": "#607078"},
        "Broadcom": {"aliases": ["broadcom"], "color": "#E21A1A"},
        "Nutanix": {"aliases": ["nutanix", "AHV"], "color": "#1D6F93"},
        "Red Hat": {"aliases": ["Red Hat", "redhat", "OpenShift", "openshift"], "color": "#EE0000"},
        "HPE GreenLake": {"aliases": ["HPE GreenLake", "HPE", "greenlake"], "color": "#01B169"},
        "Dell APEX": {"aliases": ["Dell APEX", "dell technologies", "dell"], "color": "#007DB8"},
        "Cisco": {"aliases": ["cisco", "cisco ucs"], "color": "#1BA0D7"},
        "NetApp": {"aliases": ["netapp"], "color": "#0067C5"},
        "Lenovo": {"aliases": ["lenovo"], "color": "#E2231A"},
    },

    # ── Sovereign / Trusted Cloud ──
    "sovereign_cloud": {
        "OVHcloud": {"aliases": ["OVHcloud", "OVH"], "color": "#002395"},
        "3DS Outscale": {"aliases": ["Outscale", "3DS Outscale", "dassault outscale"], "color": "#005386"},
        "Scaleway": {"aliases": ["scaleway", "iliad scaleway"], "color": "#E6007A"},
        "S3NS": {"aliases": ["S3NS", "thales s3ns"], "color": "#FF6600"},
        "Bleu": {"aliases": ["Bleu", "capgemini orange bleu"], "color": "#000091"},
        "NumSpot": {"aliases": ["NumSpot", "numspot"], "color": "#4051B5"},
        "Cloud Temple": {"aliases": ["Cloud Temple", "cloud temple"], "color": "#00A99D"},
        "Cegedim.Cloud": {"aliases": ["Cegedim.Cloud", "Cegedim Cloud", "cegedim"], "color": "#1B998B"},
        "Free Pro": {"aliases": ["Free Pro", "free pro cloud"], "color": "#C8191E"},
    },

    # ── Ecosystem Partners ──
    "ecosystem_partners": {
        "Capgemini": {"aliases": ["capgemini"], "color": "#0072B8"},
        "Orange Business": {"aliases": ["Orange Business", "orange business services"], "color": "#FF7900"},
        "Accenture": {"aliases": ["accenture"], "color": "#A100FF"},
        "Devoteam": {"aliases": ["devoteam"], "color": "#E20074"},
        "Sopra Steria": {"aliases": ["Sopra Steria", "sopra steria"], "color": "#EC0016"},
        "Atos": {"aliases": ["atos"], "color": "#0066A1"},
        "Eviden": {"aliases": ["eviden", "atos eviden"], "color": "#003B71"},
        "Inetum": {"aliases": ["inetum"], "color": "#6C3"},
        "CGI": {"aliases": ["CGI", "cgi group"], "color": "#E31837"},
        "Onepoint": {"aliases": ["onepoint", "groupe onepoint"], "color": "#000000"},
        "Wavestone": {"aliases": ["wavestone"], "color": "#0096D6"},
        "Talan": {"aliases": ["talan"], "color": "#13294B"},
        "SFEIR": {"aliases": ["sfeir"], "color": "#E60028"},
        "Ippon": {"aliases": ["ippon technologies", "ippon"], "color": "#EE3124"},
        "Claranet": {"aliases": ["claranet"], "color": "#004990"},
        "Kyndryl": {"aliases": ["kyndryl"], "color": "#FF3200"},
        "Computacenter": {"aliases": ["computacenter"], "color": "#D70000"},
        "SCC": {"aliases": ["SCC", "scc france"], "color": "#0077B3"},
        "Deloitte": {"aliases": ["deloitte"], "color": "#86BC25"},
        "PwC": {"aliases": ["pwc", "pricewaterhousecoopers"], "color": "#D04A02"},
        "KPMG": {"aliases": ["kpmg"], "color": "#00338D"},
        "TCS": {"aliases": ["TCS", "tata consultancy"], "color": "#007DC5"},
        "NTT Data": {"aliases": ["NTT Data", "ntt"], "color": "#005BAC"},
        "Axians": {"aliases": ["axians", "vinci energies axians"], "color": "#F58220"},
        "SoftwareOne": {"aliases": ["softwareone"], "color": "#4CB748"},
        "Artefact": {"aliases": ["artefact"], "color": "#0071CE"},
        "Dataiku": {"aliases": ["dataiku"], "color": "#2F4858"},
    },

    # ── Regulators / Public Bodies ──
    "regulators": {
        "ANSSI": {"aliases": ["ANSSI", "anssi"], "color": "#000091"},
        "CNIL": {"aliases": ["CNIL", "cnil"], "color": "#E1000F"},
        "DINUM": {"aliases": ["DINUM", "dinum"], "color": "#000091"},
        "European Commission": {"aliases": ["European Commission", "commission européenne", "EU"], "color": "#003399"},
        "Banque de France": {"aliases": ["Banque de France", "banque de france"], "color": "#0B3B82"},
        "DORA": {"aliases": ["DORA", "digital operational resilience act"], "color": "#475569"},
        "NIS2": {"aliases": ["NIS2", "NIS 2"], "color": "#475569"},
        "EUCS": {"aliases": ["EUCS", "european cybersecurity certification scheme"], "color": "#475569"},
    },
}

# Flattened entity lookup: lowercase alias → (display_name, color, entity_group)
ENTITY_LOOKUP = {}
for group_name, group in ENTITIES.items():
    for display_name, info in group.items():
        aliases = [display_name.lower()] + [a.lower() for a in info.get("aliases", [])]
        for alias in aliases:
            ENTITY_LOOKUP[alias] = (display_name, info["color"], group_name)

# ═══════════════════════════════════════════════════════════
# 3. EVENT TYPES (10 types, v3)
# ═══════════════════════════════════════════════════════════

EVENT_TYPES = {
    "product":       {"label": "产品发布",   "icon": "🆕", "color": "#10B981", "score_bonus": 40},
    "partnership":   {"label": "商务合作",   "icon": "🤝", "color": "#3B82F6", "score_bonus": 35},
    "client_win":    {"label": "客户中标",   "icon": "🎯", "color": "#8B5CF6", "score_bonus": 45},
    "ma_investment": {"label": "并购投资",   "icon": "💰", "color": "#F97316", "score_bonus": 50},
    "datacenter":    {"label": "数据中心/基础设施", "icon": "🏗️", "color": "#EC4899", "score_bonus": 48},
    "policy_law":    {"label": "政策法规",   "icon": "📜", "color": "#F59E0B", "score_bonus": 42},
    "certification": {"label": "认证资质",   "icon": "✅", "color": "#14B8A6", "score_bonus": 38},
    "financial":     {"label": "财务表现",   "icon": "📊", "color": "#6366F1", "score_bonus": 30},
    "personnel":     {"label": "人事组织",   "icon": "👤", "color": "#6B7280", "score_bonus": 20},
    "general":       {"label": "综合动态",   "icon": "📰", "color": "#94A3B8", "score_bonus": 10},
}

# Event type keyword patterns (checked in order)
EVENT_KEYWORDS = [
    ("product", [
        "lancement", "nouveau service", "nouvelle offre", "nouvelle fonctionnalité",
        "sortie", "dévoile", "disponible", "nouvelle version", "introduit",
        "annonce le lancement", "release", "unveiled", "new service",
    ]),
    ("partnership", [
        "partenariat", "collaboration", "alliance", "consortium",
        "signé un partenariat", "s'associe", "strategic partnership",
    ]),
    ("client_win", [
        "contrat", "contract", "selected", "choisit", "déploiement", "projet",
        "marché public", "appel d'offres", "signé un contrat",
        "remporte", "décroche", "client", "implementation",
    ]),
    ("ma_investment", [
        "acquisition", "fusion", "rachat", "levée de fonds", "investissement",
        "financement", "investit", "merger", "funding", "capital risque",
        "prise de participation", "valorisation",
    ]),
    ("datacenter", [
        "data center", "datacenter", "centre de données", "GPU", "AI infrastructure",
        "region", "availability zone", "infrastructure cloud",
        "data centre", "centre data", "ouverture d'un data center",
        "construction data center", "investissement data center",
    ]),
    ("policy_law", [
        "réglementation", "loi", "décret", "ANSSI", "CNIL", "DORA", "NIS2",
        "Data Act", "SREN", "EUCS", "gouvernement", "régulation",
        "souveraineté", "directive", "arrêté", "ministère",
        "conformité réglementaire",
    ]),
    ("certification", [
        "certification", "qualification", "SecNumCloud", "ISO", "HDS",
        "conformité", "certifié", "qualifié", "labellisé", "labellisation",
        "audit", "homologation",
    ]),
    ("financial", [
        "chiffre d'affaires", "résultat", "résultats", "revenu", "bénéfice",
        "trimestre", "exercice", "marge", "rentabilité", "résultats financiers",
        "quarterly results", "earnings", "annual results",
    ]),
    ("personnel", [
        "nomination", "CEO", "directeur", "restructure", "reorganization",
        "recrute", "recrutement", "départ", "nouveau directeur",
        "nouveau président", "nommé", "rejoint",
    ]),
]

# ═══════════════════════════════════════════════════════════
# 4. IMPORTANCE SCORING SYSTEM
# ═══════════════════════════════════════════════════════════

# 4a. Entity bonuses (adds to score when entity is mentioned)
ENTITY_SCORE_BONUS = {
    # High-priority entities
    "AWS": 10, "Azure": 10, "GCP": 10,
    "OVHcloud": 10, "S3NS": 12, "Bleu": 12, "NumSpot": 10,
    "Capgemini": 8, "Orange Business": 8, "Atos": 8, "Eviden": 8,
    "Nutanix": 7, "VMware": 7,
    "ANSSI": 12, "CNIL": 10,
    "Mistral AI": 10,
    # Medium
    "Devoteam": 6, "Sopra Steria": 6, "Accenture": 6,
    "Scaleway": 7, "3DS Outscale": 7, "Cloud Temple": 7,
    "HPE GreenLake": 5, "Dell APEX": 5, "Red Hat": 5,
    # Default
    "_default": 3,
}

# 4b. France relevance keywords (score bonus per match)
FRANCE_KEYWORDS = [
    "france", "french", "français", "française", "francais",
    "paris", "marseille", "lyon", "lille", "toulouse", "bordeaux",
    "île-de-france", "ile-de-france", "seine", "bretagne",
    "france-based", "france basé", "en france", "hexagone",
]

# 4c. Industry relevance keywords (bonus for sector-specific news)
INDUSTRY_SECTORS = {
    "finance": {
        "keywords": ["banque", "bank", "assurance", "insurance", "finance",
                     "fintech", "paiement", "payment", "asset management",
                     "capital markets", "banques françaises"],
        "bonus": 8,
    },
    "public_sector": {
        "keywords": ["administration", "gouvernement", "government", "marché public",
                     "public procurement", "secteur public", "public sector",
                     "collectivité", "mairie", "ministère"],
        "bonus": 8,
    },
    "healthcare": {
        "keywords": ["santé", "health", "hôpital", "hospital", "médical", "medical",
                     "patient", "soins", "healthcare", "pharmaceutique",
                     "données de santé", "health data"],
        "bonus": 8,
    },
    "manufacturing": {
        "keywords": ["industrie", "industry", "manufacturing", "usine", "factory",
                     "industrie 4.0", "production", "supply chain",
                     "aéronautique", "automobile"],
        "bonus": 6,
    },
    "energy": {
        "keywords": ["énergie", "energy", "électricité", "electricity", "utility",
                     "solaire", "nucléaire", "nuclear", "pétrole", "oil",
                     "gaz", "renewable", "renouvelable"],
        "bonus": 6,
    },
    "retail": {
        "keywords": ["retail", "commerce", "distribution", "e-commerce",
                     "luxe", "luxury", "grande distribution"],
        "bonus": 5,
    },
    "telecom": {
        "keywords": ["télécom", "telecom", "opérateur", "operator",
                     "5G", "fibre", "fiber", "connectivité"],
        "bonus": 5,
    },
}

# 4d. Strategic keyword bonuses
STRATEGIC_KEYWORDS = {
    "sovereign_cloud": {
        "keywords": ["cloud souverain", "sovereign cloud", "SecNumCloud",
                     "cloud de confiance", "trusted cloud", "souveraineté numérique",
                     "cloud strategy france"],
        "bonus": 12,
    },
    "ai_gpu": {
        "keywords": ["AI cloud", "GPU", "H100", "B200", "A100",
                     "intelligence artificielle", "artificial intelligence",
                     "Mistral AI", "LLM", "large language model",
                     "AI infrastructure", "cloud GPU", "sovereign AI"],
        "bonus": 12,
    },
    "data_center_investment": {
        "keywords": ["data center", "datacenter", "centre de données",
                     "investissement data", "nouveau data", "ouverture data",
                     "milliard", "billion", "massive investment"],
        "bonus": 10,
    },
    "vmware_alternative": {
        "keywords": ["VMware alternative", "Broadcom VMware", "VMware migration",
                     "quitter VMware", "Nutanix vs VMware", "post-VMware"],
        "bonus": 8,
    },
    "compliance": {
        "keywords": ["DORA", "NIS2", "EUCS", "Data Act", "GDPR",
                     "compliance", "mise en conformité", "regulatory"],
        "bonus": 8,
    },
}

# 4e. Source credibility bonus
CREDIBLE_SOURCES = [
    "le monde", "les echos", "la tribune", "usine nouvelle", "usine digitale",
    "le figaro", "bfm", "zdnet", "silicon", "journal du net", "01net",
    "lemagit", "channelnews", "solutions-numeriques", "informatiquenews",
    "cio online", "alliancy", "it for business", "république",
    "gouvernement", "anssi", "cnil", "commission européenne",
    "reuters", "bloomberg", "financial times",
]

# ═══════════════════════════════════════════════════════════
# 5. IMPORTANCE DISPLAY
# ═══════════════════════════════════════════════════════════

IMPORTANCE_LABELS = {"high": "重要", "medium": "一般", "low": "低"}
IMPORTANCE_STARS = {"high": "★★★", "medium": "★★", "low": "★"}
IMPORTANCE_COLORS = {"high": "#F59E0B", "medium": "#9CA3AF", "low": "#4B5563"}

def importance_level(score):
    """Convert numeric score to importance level."""
    if score >= 75:
        return "high"
    elif score >= 45:
        return "medium"
    return "low"

# ═══════════════════════════════════════════════════════════
# 6. RSS QUERIES (expanded, v3)
# ═══════════════════════════════════════════════════════════

QUERIES = [
    # ── A. Public Cloud Providers ──
    {"name": "AWS_France", "q": '(AWS OR "Amazon Web Services") France (cloud OR "data center" OR région OR annonce OR partenariat)', "category": "public_cloud", "provider": "AWS", "priority": 1},
    {"name": "Azure_France", "q": '("Microsoft Azure" OR Azure) France (cloud OR "data center" OR annonce OR partenariat)', "category": "public_cloud", "provider": "Azure", "priority": 1},
    {"name": "GCP_France", "q": '("Google Cloud" OR GCP) France (cloud OR "data center" OR région OR annonce)', "category": "public_cloud", "provider": "GCP", "priority": 1},
    {"name": "Oracle_Cloud_France", "q": '("Oracle Cloud" OR OCI) France cloud', "category": "public_cloud", "provider": "Oracle Cloud", "priority": 2},
    {"name": "Huawei_Cloud_France", "q": '"Huawei Cloud" France', "category": "public_cloud", "provider": "Huawei Cloud", "priority": 3},
    {"name": "Alibaba_Cloud_France", "q": '"Alibaba Cloud" France', "category": "public_cloud", "provider": "Alibaba Cloud", "priority": 3},
    {"name": "IBM_Cloud_France", "q": '("IBM Cloud" OR "IBM") France cloud', "category": "public_cloud", "provider": "IBM Cloud", "priority": 2},
    {"name": "PublicCloud_M&A", "q": 'France cloud (partenariat OR acquisition OR "levée de fonds" OR investissement OR fusion)', "category": "public_cloud", "provider": None, "priority": 1},

    # ── B. Private / Hybrid Cloud ──
    {"name": "VMware_France", "q": 'VMware France (cloud OR datacenter OR virtualisation OR annonce OR partenariat OR Broadcom)', "category": "private_hybrid", "provider": "VMware", "priority": 1},
    {"name": "Nutanix_France", "q": "Nutanix France (cloud OR datacenter OR annonce OR partenariat OR AHV OR HCI)", "category": "private_hybrid", "provider": "Nutanix", "priority": 1},
    {"name": "RedHat_France", "q": '("Red Hat" OR RedHat OR OpenShift) France (cloud OR "open source" OR annonce)', "category": "private_hybrid", "provider": "Red Hat", "priority": 1},
    {"name": "HPE_GreenLake_France", "q": '"HPE GreenLake" France cloud', "category": "private_hybrid", "provider": "HPE GreenLake", "priority": 2},
    {"name": "Dell_APEX_France", "q": '"Dell APEX" France cloud', "category": "private_hybrid", "provider": "Dell APEX", "priority": 2},
    {"name": "Cisco_France_Cloud", "q": "Cisco France (hybrid cloud OR datacenter)", "category": "private_hybrid", "provider": "Cisco", "priority": 3},
    {"name": "NetApp_France", "q": "NetApp France cloud data", "category": "private_hybrid", "provider": "NetApp", "priority": 3},
    {"name": "K8s_France", "q": "Kubernetes France cloud entreprise", "category": "private_hybrid", "provider": None, "priority": 2},

    # ── C. VMware-Broadcom / Nutanix Alternative ──
    {"name": "Nutanix_VMware_Alt", "q": "Nutanix VMware Broadcom France migration alternative", "category": "private_hybrid", "provider": "Nutanix", "priority": 1},
    {"name": "VMware_Broadcom_France", "q": "VMware Broadcom France cloud migration licence", "category": "private_hybrid", "provider": "VMware", "priority": 1},
    {"name": "VMware_Alt_France", "q": 'VMware alternative France (Nutanix OR "Red Hat" OR OpenShift)', "category": "private_hybrid", "provider": None, "priority": 2},

    # ── D. Sovereign / Trusted Cloud ──
    {"name": "SecNumCloud_Qualif", "q": "SecNumCloud qualification ANSSI cloud France", "category": "sovereign_trusted", "provider": None, "priority": 1},
    {"name": "Cloud_Confiance", "q": 'France (SecNumCloud OR "cloud de confiance" OR "cloud souverain")', "category": "sovereign_trusted", "provider": None, "priority": 1},
    {"name": "S3NS_France", "q": "S3NS France (Google Cloud OR Thales OR partenaires)", "category": "sovereign_trusted", "provider": "S3NS", "priority": 1},
    {"name": "Bleu_France", "q": "Bleu France (Azure OR Orange OR Capgemini)", "category": "sovereign_trusted", "provider": "Bleu", "priority": 1},
    {"name": "OVHcloud_SecNumCloud", "q": "OVHcloud SecNumCloud France partenariat", "category": "sovereign_trusted", "provider": "OVHcloud", "priority": 1},
    {"name": "Outscale_SecNumCloud", "q": "Outscale SecNumCloud France cloud souverain", "category": "sovereign_trusted", "provider": "3DS Outscale", "priority": 2},
    {"name": "CloudTemple_France", "q": "Cloud Temple SecNumCloud France", "category": "sovereign_trusted", "provider": "Cloud Temple", "priority": 2},
    {"name": "NumSpot_France", "q": "NumSpot cloud souverain France", "category": "sovereign_trusted", "provider": "NumSpot", "priority": 2},
    {"name": "Scaleway_Sovereign", "q": "Scaleway cloud souverain France AI", "category": "sovereign_trusted", "provider": "Scaleway", "priority": 2},
    {"name": "Donnees_Sensibles", "q": 'données sensibles hébergement SecNumCloud administration France', "category": "sovereign_trusted", "provider": None, "priority": 1},

    # ── E. Ecosystem Partners ──
    {"name": "Capgemini_Cloud", "q": "Capgemini France cloud (AWS OR Azure OR Google OR souveraineté)", "category": "ecosystem_partners", "provider": "Capgemini", "priority": 1},
    {"name": "OrangeBusiness_Cloud", "q": "Orange Business cloud (AWS OR Azure OR Google) France", "category": "ecosystem_partners", "provider": "Orange Business", "priority": 1},
    {"name": "Devoteam_Cloud", "q": "Devoteam France (Google Cloud OR AWS OR Azure OR AI)", "category": "ecosystem_partners", "provider": "Devoteam", "priority": 2},
    {"name": "SopraSteria_Cloud", "q": "Sopra Steria France cloud (Azure OR AI OR sovereign)", "category": "ecosystem_partners", "provider": "Sopra Steria", "priority": 2},
    {"name": "Atos_Eviden_Cloud", "q": "Atos Eviden France cloud souveraineté SecNumCloud", "category": "ecosystem_partners", "provider": None, "priority": 1},
    {"name": "Inetum_Cloud", "q": "Inetum France cloud (Microsoft OR AWS OR Google)", "category": "ecosystem_partners", "provider": "Inetum", "priority": 3},
    {"name": "CGI_Cloud", "q": "CGI France cloud (AWS OR Azure OR Google)", "category": "ecosystem_partners", "provider": "CGI", "priority": 3},
    {"name": "Partners_Broad", "q": "France cloud (Capgemini OR Accenture OR Deloitte OR PwC OR KPMG OR TCS OR NTT) partenariat", "category": "ecosystem_partners", "provider": None, "priority": 2},
    {"name": "Partners_Mid", "q": "France cloud (Wavestone OR Talan OR Onepoint OR SFEIR OR Ippon OR Claranet OR Kyndryl)", "category": "ecosystem_partners", "provider": None, "priority": 3},

    # ── F. AI Cloud & Data Center ──
    {"name": "AI_DataCenter_FR", "q": "France AI data center cloud GPU investment", "category": "ai_datacenter", "provider": None, "priority": 1},
    {"name": "Sovereign_AI_FR", "q": "France sovereign AI cloud (Mistral OR OVHcloud OR Scaleway)", "category": "ai_datacenter", "provider": None, "priority": 1},
    {"name": "GPU_Cloud_FR", "q": "France GPU cloud AI infrastructure (Nvidia OR H100 OR B200)", "category": "ai_datacenter", "provider": None, "priority": 1},
    {"name": "DataCenter_Energy", "q": "France data center cloud energy renewable AI sustainability", "category": "ai_datacenter", "provider": None, "priority": 2},
    {"name": "MS_AI_FR", "q": "Microsoft France AI cloud data center", "category": "ai_datacenter", "provider": "Azure", "priority": 1},
    {"name": "AWS_AI_FR", "q": "AWS France AI cloud investment", "category": "ai_datacenter", "provider": "AWS", "priority": 1},
    {"name": "GCP_AI_FR", "q": "Google Cloud France AI infrastructure", "category": "ai_datacenter", "provider": "GCP", "priority": 1},
    {"name": "Mistral_AI", "q": "Mistral AI France cloud partnership", "category": "ai_datacenter", "provider": None, "priority": 1},
    {"name": "DataCenter_Invest", "q": 'France ("data center" OR datacenter) (investissement OR construction OR milliard)', "category": "ai_datacenter", "provider": None, "priority": 1},

    # ── G. Industry Cloud / Client Cases ──
    {"name": "Finance_Cloud", "q": "France banque cloud (DORA OR AWS OR Azure OR Google) souverain", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "Insurance_Cloud", "q": "France assurance cloud DORA numérique", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "Gov_Cloud", "q": "France administration cloud SecNumCloud marché public", "category": "industry_cloud", "provider": None, "priority": 1},
    {"name": "Health_Cloud", "q": "France santé cloud (HDS OR SecNumCloud OR Cegedim OR Mipih)", "category": "industry_cloud", "provider": None, "priority": 1},
    {"name": "Hospital_Cloud", "q": "France hôpital cloud souverain données santé", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "Industry_Cloud", "q": "France industrie cloud (data act OR edge OR souveraineté)", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "Energy_Cloud", "q": "France énergie cloud souveraineté data platform", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "Retail_Cloud", "q": "France retail cloud (AWS OR Azure OR Google)", "category": "industry_cloud", "provider": None, "priority": 3},
    {"name": "Telecom_Cloud", "q": "France (télécom OR telecom) cloud (Orange OR SFR OR Bouygues OR Free) migration", "category": "industry_cloud", "provider": None, "priority": 3},

    # ── H. Policy & Regulation ──
    {"name": "DORA_FR", "q": "France DORA cloud ICT third party providers", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "NIS2_FR", "q": "France NIS2 cloud cybersecurity", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "DataAct_FR", "q": "France Data Act cloud switching portability", "category": "policy_regulation", "provider": None, "priority": 2},
    {"name": "EUCS_FR", "q": "France EUCS cloud sovereignty", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "SREN_FR", "q": "France SREN cloud SecNumCloud données sensibles", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "CNIL_Cloud", "q": "CNIL cloud France données personnelles", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "ANSSI_Cloud", "q": "ANSSI cloud France SecNumCloud cybersécurité", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "Gov_Cloud_Strategy", "q": "France (cloud OR numérique) (politique OR stratégie OR gouvernement OR plan)", "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "Digital_Sovereignty", "q": 'France "souveraineté numérique" OR "cloud souverain" OR "digital sovereignty"', "category": "policy_regulation", "provider": None, "priority": 1},
    {"name": "Cloud_Regulation", "q": "France (cloud OR données) (réglementation OR régulation OR conformité)", "category": "policy_regulation", "provider": None, "priority": 2},
    {"name": "Cyber_Cloud_FR", "q": "France cybersécurité cloud (ANSSI OR certification)", "category": "policy_regulation", "provider": None, "priority": 2},
    {"name": "Data_Regulation", "q": "France cloud (données OR data) (réglementation OR protection OR résidence)", "category": "policy_regulation", "provider": None, "priority": 2},

    # ── I. French Cloud Providers (competitive context) ──
    {"name": "FR_Providers", "q": "France (OVHcloud OR Outscale OR Scaleway OR OVH) cloud", "category": "sovereign_trusted", "provider": None, "priority": 2},
    {"name": "Industry_Cloud_Broad", "q": "France (cloud OR hébergement) (santé OR finance OR public OR administration OR banque)", "category": "industry_cloud", "provider": None, "priority": 2},
    {"name": "FR_Tech_Law", "q": "France (numérique OR cloud OR données) (loi OR décret OR arrêté OR directive)", "category": "policy_regulation", "provider": None, "priority": 2},
]


def build_rss_url(query_dict):
    """Build a Google News RSS URL from a query config dict."""
    from urllib.parse import quote
    q = query_dict["q"]
    return f"{BASE_URL}?q={quote(q)}&hl={HL}&gl={GL}&ceid={CEID}"


# ═══════════════════════════════════════════════════════════
# 7. LEGACY PROVIDER COLORS (for backward compat in HTML)
# ═══════════════════════════════════════════════════════════

PROVIDER_COLORS = {name: info["color"] for name, info in ENTITIES["cloud_providers"].items()}
PROVIDER_COLORS.update({name: info["color"] for name, info in ENTITIES["private_hybrid_vendors"].items()})
PROVIDER_COLORS.update({name: info["color"] for name, info in ENTITIES["sovereign_cloud"].items()})

# Legacy labels for backward compatibility
CATEGORY_LABELS = {k: f"{v['icon']} {v['label']}" for k, v in CATEGORIES.items()}
