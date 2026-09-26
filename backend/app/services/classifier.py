"""
জব কোন সেক্টরের আর কোন কাজের ক্ষেত্রের — সেটা ঠিক করে।

LLM নয়, শুধু কি-ওয়ার্ড মিলিয়ে। তাই:
  - খরচ শূন্য
  - ফলাফল সবসময় একই (deterministic)
  - কোনো নেটওয়ার্ক কল নেই, তাই তাৎক্ষণিক

একই অভিধান CV প্রোফাইলেও চলে, তাই ইউজারের CV আর জব দুটোকে
একই ভাষায় মাপা যায় — এটাই "CV অনুযায়ী জব দেখানো"-র ভিত্তি।

নতুন কি-ওয়ার্ড যোগ করা = নিচের তালিকায় এক লাইন। কোনো কোড বদলাতে হবে না।
"""

from __future__ import annotations

# ══════════════════════════════════════════════════════════
# ১. সেক্টর — কেমন প্রতিষ্ঠান
# ══════════════════════════════════════════════════════════
GOVT = "govt"
BANK = "bank"
NGO = "ngo"
EDUCATION = "education"
REMOTE = "remote"
PRIVATE = "private"

SECTOR_LABELS: dict[str, str] = {
    GOVT: "সরকারি",
    BANK: "ব্যাংক / আর্থিক",
    NGO: "NGO / উন্নয়ন",
    EDUCATION: "শিক্ষা প্রতিষ্ঠান",
    REMOTE: "রিমোট / আন্তর্জাতিক",
    PRIVATE: "প্রাইভেট কোম্পানি",
}

SECTOR_LABELS_EN: dict[str, str] = {
    GOVT: "Government",
    BANK: "Bank / Financial",
    NGO: "NGO / Development",
    EDUCATION: "Education",
    REMOTE: "Remote / Global",
    PRIVATE: "Private Company",
}

# ক্রম গুরুত্বপূর্ণ নয় — একটা জব একাধিক সেক্টরে থাকতে পারে
_SECTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    BANK: (
        "bank", "ব্যাংক", "ব্যাংকার", "bankers selection", "bscs",
        "financial institution", "আর্থিক প্রতিষ্ঠান", "microfinance",
        "ক্ষুদ্রঋণ", "insurance", "বীমা", "leasing", "লিজিং",
        "sonali", "janata", "agrani", "rupali", "basic bank", "bkash",
        "nagad", "rocket", "mfs",
    ),
    GOVT: (
        "ministry", "মন্ত্রণালয়", "অধিদপ্তর", "directorate", "সরকারি",
        "government", "govt", "teletalk", "bpsc", "কর্তৃপক্ষ", "authority",
        "জনপ্রশাসন", "পরিষদ", "council", "সেনাবাহিনী", "নৌবাহিনী",
        "বিমান বাহিনী", "পুলিশ", "police", "কর্পোরেশন", "রাষ্ট্রায়ত্ত",
        "প্রজাতন্ত্র", "গণপ্রজাতন্ত্রী", "উপজেলা", "জেলা প্রশাসক",
        "সচিবালয়", "বোর্ড", "commission", "কমিশন", "নিয়োগ বিজ্ঞপ্তি",
        "রাজস্ব", "বিআরটিএ", "brta", "biwta", "badc", "bwdb", "coast guard",
        "আনসার", "বিজিবি", "bgb", "দুদক", "নির্বাচন কমিশন",
    ),
    NGO: (
        "ngo", "brac", "foundation", "ফাউন্ডেশন", "unicef", "undp", "unhcr",
        "save the children", "care bangladesh", "world vision", "oxfam",
        "plan international", "relief", "reliefweb", "উন্নয়ন সংস্থা",
        "প্রকল্প", "project officer", "wfp", "iom", "ilo", "usaid",
        "field facilitator", "community mobilizer", "সমাজসেবা",
    ),
    EDUCATION: (
        "university", "বিশ্ববিদ্যালয়", "college", "কলেজ", "school", "স্কুল",
        "madrasa", "মাদ্রাসা", "lecturer", "প্রভাষক", "professor", "অধ্যাপক",
        "teacher", "শিক্ষক", "ugc", "academy", "একাডেমি", "instructor",
        "প্রশিক্ষক", "শিক্ষা বোর্ড", "nctb", "প্রাথমিক বিদ্যালয়",
    ),
}

# এই সোর্সগুলো এলে সরাসরি সেক্টর বসে যায় — কি-ওয়ার্ড খোঁজার দরকার নেই
_SOURCE_SECTOR: dict[str, str] = {
    "govt": GOVT,
    "teletalk": GOVT,
    "remotive": REMOTE,
    "remoteok": REMOTE,
    "arbeitnow": REMOTE,
    "weworkremotely": REMOTE,
}


# ══════════════════════════════════════════════════════════
# ২. কাজের ক্ষেত্র — কী কাজ করতে হবে
# ══════════════════════════════════════════════════════════
IT = "it"
ENGINEERING = "engineering"
MARKETING = "marketing"
FINANCE = "finance"
HR = "hr"
HEALTHCARE = "healthcare"
TEACHING = "teaching"
DESIGN = "design"
SUPPORT = "support"
LEGAL = "legal"
GENERAL = "general"

FUNCTION_LABELS: dict[str, str] = {
    IT: "IT / সফটওয়্যার",
    ENGINEERING: "ইঞ্জিনিয়ারিং",
    MARKETING: "মার্কেটিং / সেলস",
    FINANCE: "ফিন্যান্স / অ্যাকাউন্টস",
    HR: "HR / প্রশাসন",
    HEALTHCARE: "স্বাস্থ্য",
    TEACHING: "শিক্ষকতা",
    DESIGN: "ডিজাইন / ক্রিয়েটিভ",
    SUPPORT: "কাস্টমার সাপোর্ট",
    LEGAL: "আইন",
    GENERAL: "অন্যান্য",
}

FUNCTION_LABELS_EN: dict[str, str] = {
    IT: "IT / Software",
    ENGINEERING: "Engineering",
    MARKETING: "Marketing / Sales",
    FINANCE: "Finance / Accounts",
    HR: "HR / Admin",
    HEALTHCARE: "Healthcare",
    TEACHING: "Teaching",
    DESIGN: "Design / Creative",
    SUPPORT: "Customer Support",
    LEGAL: "Legal",
    GENERAL: "Others",
}

# ⚠ ক্রম গুরুত্বপূর্ণ — উপরেরটা আগে মিলবে।
# IT সবার আগে, কারণ "Software Engineer"-এ "engineer" আছে কিন্তু
# সেটা ইঞ্জিনিয়ারিং নয়, IT।
_FUNCTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    IT: (
        "software", "developer", "programmer", "frontend", "front-end",
        "backend", "back-end", "full stack", "fullstack", "web develop",
        "react", "next.js", "nextjs", "node", "javascript", "typescript",
        "python", "django", "flask", "laravel", " php", "dotnet", ".net",
        "devops", "data scientist", "data analyst", "machine learning",
        "artificial intelligence", " ai ", "সফটওয়্যার", "প্রোগ্রামার",
        "android", "ios develop", "flutter", "react native", "mobile app",
        "qa engineer", "sqa", "software test", "database administrator",
        "dba", "network engineer", "system admin", "cyber", "security analyst",
        "it officer", "it support", "wordpress", "shopify", "seo specialist",
        "cloud engineer", "aws", "blockchain", "game develop",
        "কম্পিউটার অপারেটর", "তথ্য প্রযুক্তি", "computer operator",
        "data entry operator", "প্রোগ্রামিং",
    ),
    ENGINEERING: (
        "civil engineer", "পুরকৌশল", "mechanical engineer", "যন্ত্রকৌশল",
        "electrical engineer", "তড়িৎ", "প্রকৌশলী", "textile engineer",
        "chemical engineer", "site engineer", "project engineer",
        "sub assistant engineer", "উপসহকারী প্রকৌশলী", "সহকারী প্রকৌশলী",
        "নির্বাহী প্রকৌশলী", "architect", "স্থপতি", "surveyor", "জরিপ",
        "production engineer", "quality control", "maintenance engineer",
        "diploma engineer", "ডিপ্লোমা", "draftsman", "electrician",
        "মেকানিক", "technician", "টেকনিশিয়ান",
    ),
    HEALTHCARE: (
        "doctor", "চিকিৎসক", "মেডিকেল অফিসার", "medical officer", "nurse",
        "নার্স", "সিনিয়র স্টাফ নার্স", "pharmacist", "ফার্মাসিস্ট",
        "lab technician", "ল্যাব", "স্বাস্থ্য সহকারী", "health assistant",
        "physiotherapist", "dental", "radiographer", "midwife", "ধাত্রী",
        "স্বাস্থ্য পরিদর্শক", "consultant physician", "surgeon",
    ),
    TEACHING: (
        "teacher", "শিক্ষক", "সহকারী শিক্ষক", "প্রধান শিক্ষক", "lecturer",
        "প্রভাষক", "instructor", "প্রশিক্ষক", "professor", "অধ্যাপক",
        "tutor", "principal", "অধ্যক্ষ", "faculty", "academic coordinator",
    ),
    LEGAL: (
        "lawyer", "আইনজীবী", "legal officer", "আইন কর্মকর্তা", "advocate",
        "paralegal", "compliance officer", "বিচারক", "judge", "magistrate",
        "সহকারী জজ", "legal advisor",
    ),
    DESIGN: (
        "graphic design", "গ্রাফিক", "ui/ux", "ux designer", "ui designer",
        "product designer", "figma", "motion graphic", "video editor",
        "ভিডিও এডিটর", "animator", "illustrator", "creative designer",
        "content creator", "photographer", "আলোকচিত্র",
    ),
    MARKETING: (
        "marketing", "মার্কেটিং", "sales", "বিক্রয়", "business development",
        "brand manager", "ব্র্যান্ড", "digital marketing", "social media",
        "territory officer", "key account", "trade marketing",
        "merchandiser", "মার্চেন্ডাইজার", "sales executive", "bdm",
        "growth", "e-commerce", "বিপণন",
    ),
    FINANCE: (
        "accountant", "accounts officer", "finance", "হিসাবরক্ষক", "হিসাব",
        "অডিট", "audit", "নিরীক্ষা", " ca ", "cma", "acca", "cashier",
        "ক্যাশিয়ার", "treasury", "tax", "কর", "vat", "ভ্যাট",
        "financial analyst", "credit officer", "ঋণ", "investment",
        "বাজেট", "budget officer", "cost control",
    ),
    HR: (
        "human resource", " hr ", "hr officer", "hr executive", "admin officer",
        "প্রশাসনিক কর্মকর্তা", "প্রশাসন", "recruitment", "নিয়োগ কর্মকর্তা",
        "office assistant", "অফিস সহকারী", "personnel", "compensation",
        "training officer", "অফিস সহায়ক", "উচ্চমান সহকারী", "প্রশাসনিক",
        "executive assistant", "কর্মী ব্যবস্থাপনা",
    ),
    SUPPORT: (
        "customer service", "customer support", "call center", "কল সেন্টার",
        "telecaller", "কাস্টমার", "help desk", "receptionist", "রিসেপশনিস্ট",
        "client relation", "service desk", "গ্রাহক সেবা",
    ),
}


# ══════════════════════════════════════════════════════════
# ৩. সহায়ক
# ══════════════════════════════════════════════════════════
def _haystack(*parts: object) -> str:
    """সব টেক্সট এক জায়গায় এনে lowercase করে। দুই পাশে ফাঁকা রাখে,
    যাতে ' hr ' বা ' ca ' এর মতো ছোট কি-ওয়ার্ড শুরু/শেষেও মেলে।"""
    chunks: list[str] = []
    for p in parts:
        if not p:
            continue
        if isinstance(p, (list, tuple, set)):
            chunks.append(" ".join(str(x) for x in p if x))
        else:
            chunks.append(str(p))
    return f" {' '.join(chunks).lower()} "


# ══════════════════════════════════════════════════════════
# ৪. পাবলিক API
# ══════════════════════════════════════════════════════════
def detect_sectors(
    *,
    title: str = "",
    company: str = "",
    description: str = "",
    tags: list[str] | None = None,
    source: str = "",
    is_remote: bool = False,
) -> list[str]:
    """
    একটা জব কোন কোন সেক্টরে পড়ে। একাধিক হতে পারে।

    উদাহরণ: "সোনালী ব্যাংক নিয়োগ বিজ্ঞপ্তি" → ["bank", "govt"]
    """
    found: list[str] = []

    # সোর্স থেকে নিশ্চিত সেক্টর
    src = (source or "").strip().lower()
    if src in _SOURCE_SECTOR:
        found.append(_SOURCE_SECTOR[src])

    text = _haystack(title, company, (description or "")[:400], tags)
    for sector, words in _SECTOR_KEYWORDS.items():
        if any(w in text for w in words):
            found.append(sector)

    if is_remote:
        found.append(REMOTE)

    # কোনোটাই না মিললে প্রাইভেট ধরে নাও
    if not found:
        found.append(PRIVATE)

    return list(dict.fromkeys(found))  # ডুপ্লিকেট বাদ, ক্রম অপরিবর্তিত


def detect_function(
    *,
    title: str = "",
    tags: list[str] | None = None,
    description: str = "",
) -> str:
    """
    কাজের ক্ষেত্র। টাইটেল সবচেয়ে বেশি নির্ভরযোগ্য, তাই আগে সেটা দেখা হয়।
    না পেলে বর্ণনার প্রথম অংশে খোঁজা হয়।
    """
    title_text = _haystack(title, tags)
    for func, words in _FUNCTION_KEYWORDS.items():
        if any(w in title_text for w in words):
            return func

    desc_text = _haystack((description or "")[:600])
    for func, words in _FUNCTION_KEYWORDS.items():
        if any(w in desc_text for w in words):
            return func

    return GENERAL


def detect_function_from_profile(
    *,
    skills: list[str] | None = None,
    preferred_titles: list[str] | None = None,
    summary: str | None = None,
) -> str:
    """CV প্রোফাইল থেকে একই অভিধানে কাজের ক্ষেত্র বের করে।"""
    return detect_function(
        title=" ".join(preferred_titles or []),
        tags=skills,
        description=summary or "",
    )


def classify_job(job) -> None:
    """
    একটা JobItem-এ sectors ও job_function বসিয়ে দেয় (in place)।
    job_fetcher থেকে লুপে ডাকার জন্য।
    """
    job.sectors = detect_sectors(
        title=job.title,
        company=job.company,
        description=job.description,
        tags=job.tags,
        source=job.source,
        is_remote=job.is_remote,
    )
    job.job_function = detect_function(
        title=job.title,
        tags=job.tags,
        description=job.description,
    )


def all_sectors() -> list[dict[str, str]]:
    """ফ্রন্টএন্ডের ফিল্টার বারের জন্য তালিকা।"""
    return [
        {"id": s, "label_bn": SECTOR_LABELS[s], "label_en": SECTOR_LABELS_EN[s]}
        for s in (GOVT, BANK, PRIVATE, NGO, EDUCATION, REMOTE)
    ]


def all_functions() -> list[dict[str, str]]:
    """ফ্রন্টএন্ডের ফিল্টার বারের জন্য তালিকা।"""
    order = (
        IT, ENGINEERING, TEACHING, HEALTHCARE, FINANCE,
        MARKETING, HR, DESIGN, SUPPORT, LEGAL, GENERAL,
    )
    return [
        {"id": f, "label_bn": FUNCTION_LABELS[f], "label_en": FUNCTION_LABELS_EN[f]}
        for f in order
    ]