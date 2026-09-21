"""
Teletalk API আসলে কী ফেরত দেয় তা দেখার স্ক্রিপ্ট।

কোড লেখার আগে সবসময় এটা চালাও। ফিল্ডের নাম বদলে গেলে বা
রেসপন্সের কাঠামো ভিন্ন হলে এখানেই ধরা পড়বে।

চালাও:  python tools/inspect_teletalk.py
"""

import asyncio
import json

import httpx

API = "https://alljobs.teletalk.com.bd/api/v1/govt-jobs/list"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://alljobs.teletalk.com.bd/",
}


def show(label: str, value) -> None:
    print(f"\n{'─' * 60}\n{label}\n{'─' * 60}")
    print(value)


async def main() -> None:
    async with httpx.AsyncClient(headers=HEADERS, timeout=25.0) as client:
        print(f"GET {API}?page=1&limit=5")
        try:
            res = await client.get(API, params={"page": 1, "limit": 5})
        except Exception as e:
            print(f"\n❌ রিকোয়েস্ট ব্যর্থ: {type(e).__name__} — {e}")
            print("\nSSL এরর হলে নিচের লাইনটা দিয়ে আবার চেষ্টা করো (শুধু পরীক্ষার জন্য):")
            print('  httpx.AsyncClient(headers=HEADERS, verify=False)')
            return

        print(f"\nStatus: {res.status_code}")
        print(f"Content-Type: {res.headers.get('content-type')}")

        if res.status_code != 200:
            print(f"\n❌ ২০০ আসেনি। বডির প্রথম ৫০০ অক্ষর:\n{res.text[:500]}")
            return

        try:
            data = res.json()
        except Exception:
            print(f"\n❌ JSON নয়। বডির প্রথম ৫০০ অক্ষর:\n{res.text[:500]}")
            return

    # ── টপ-লেভেলে কী কী কী আছে ──
    if isinstance(data, dict):
        show("টপ-লেভেল কী-গুলো", list(data.keys()))
    else:
        show("টপ-লেভেল টাইপ", type(data).__name__)

    # ── জবের তালিকা কোথায় আছে খুঁজে বের করি ──
    items = None
    list_key = None
    if isinstance(data, dict):
        for key in ("govtJobs", "data", "jobs", "results", "items", "circulars"):
            value = data.get(key)
            if isinstance(value, list) and value:
                items, list_key = value, key
                break
            # nested: {"data": {"govtJobs": [...]}}
            if isinstance(value, dict):
                for inner_key, inner in value.items():
                    if isinstance(inner, list) and inner:
                        items, list_key = inner, f"{key}.{inner_key}"
                        break
            if items:
                break
    elif isinstance(data, list):
        items, list_key = data, "(root array)"

    if not items:
        show("⚠️  জবের তালিকা পাওয়া যায়নি", json.dumps(data, ensure_ascii=False)[:1500])
        print("\n👉 উপরের আউটপুটটা আমাকে পাঠাও, আমি সঠিক কী বের করে দেব।")
        return

    print(f"\n✅ জবের তালিকা পাওয়া গেছে — key: '{list_key}', সংখ্যা: {len(items)}")

    first = items[0]
    show("প্রথম আইটেমের সব ফিল্ড", list(first.keys()))

    # ── গুরুত্বপূর্ণ ফিল্ডগুলো আছে কিনা ──
    print(f"\n{'─' * 60}\nযে ফিল্ডগুলো আমাদের দরকার\n{'─' * 60}")
    wanted = [
        "id", "job_id",
        "job_title", "job_title_bn", "title",
        "govtOrganization", "organization", "organization_name",
        "application_start_date", "application_end_date", "end_date", "deadline",
        "application_site", "url", "link",
        "salary_range", "salary", "grade",
        "total_vacancy", "vacancy",
    ]
    for field in wanted:
        if field in first:
            value = first[field]
            preview = json.dumps(value, ensure_ascii=False)[:90]
            print(f"  ✅ {field:<26} = {preview}")
        else:
            print(f"  ❌ {field:<26} (নেই)")

    show("প্রথম আইটেম পুরোটা", json.dumps(first, ensure_ascii=False, indent=2)[:2500])

    # ── পেজিনেশন কীভাবে কাজ করে ──
    if isinstance(data, dict):
        meta = {
            k: v for k, v in data.items()
            if k.lower() in ("total", "totalcount", "total_count", "page",
                             "per_page", "last_page", "meta", "pagination", "count")
        }
        if meta:
            show("পেজিনেশন তথ্য", json.dumps(meta, ensure_ascii=False, indent=2)[:800])


if __name__ == "__main__":
    asyncio.run(main())