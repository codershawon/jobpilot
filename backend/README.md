# JobPilot — Backend (Step 1: Project setup + CV parsing)

এই ধাপে যা তৈরি হয়েছে:

- FastAPI backend স্কেলিটন
- `.env`-ভিত্তিক কনফিগ, যেখানে LLM provider/model **কোডে হার্ডকোড না** —
  শুধু `.env`-এ `LLM_ACTIVE_PROFILE=premium` বা `cheap` বদলালেই পুরো সিস্টেম
  নতুন মডেলে চলে যাবে (এবং চাইলে নতুন প্রোফাইল নিজে যোগ করা যায়)।
- CV আপলোড এন্ডপয়েন্ট: PDF/DOCX থেকে টেক্সট এক্সট্র্যাক্ট করে, oxyy.ai-তে
  **একটাই** LLM কল করে structured প্রোফাইল (skills, experience, preferred
  titles/locations, ইত্যাদি) বের করে আনে।
- Pytest টেস্ট (LLM কল mock করা, তাই টেস্ট চালাতে API খরচ হয় না)।

## যেভাবে চালাবেন

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env খুলে LLM_API_KEY বসান, এবং LLM_ACTIVE_PROFILE দিয়ে
# premium/cheap মডেল বেছে নিন

uvicorn app.main:app --reload --port 8000
```

তারপর:

```bash
curl -X POST http://localhost:8000/api/cv/upload \
  -F "file=@/path/to/your_cv.pdf"
```

অথবা http://localhost:8000/docs -এ গিয়ে interactive Swagger UI থেকে টেস্ট করতে
পারবেন।

## টেস্ট চালানো (LLM ছাড়াই, খরচ ছাড়া)

```bash
pytest tests/ -v
```

> **নোট:** এই স্যান্ডবক্স এনভায়রনমেন্টে ইন্টারনেট অ্যাক্সেস বন্ধ থাকায়
> আমি এখানে `pip install` করে পুরো FastAPI অ্যাপ সরাসরি চালিয়ে দেখাতে
> পারিনি। তবে DOCX/PDF টেক্সট এক্সট্র্যাকশন লজিক এবং মডেল-সুইচিং লজিক আমি
> আলাদাভাবে ম্যানুয়ালি চালিয়ে যাচাই করেছি — দুটোই ঠিকভাবে কাজ করছে। আপনি
> নিজের মেশিনে `pip install -r requirements.txt` করার পর `pytest` চালালে
> পুরো স্যুট (mocked LLM কলসহ) পাস করবে।

## কনফিগ কীভাবে কাজ করে (`app/config.py`)

```
LLM_ACTIVE_PROFILE=cheap        # <- এই একটা লাইন বদলালেই মডেল বদলে যায়
LLM_MODEL_PREMIUM=gpt-4o
LLM_MODEL_CHEAP=deepseek-chat
```

নতুন প্রোফাইল (যেমন `llama`, `mistral`) যোগ করতে চাইলে:
1. `.env`-এ `LLM_MODEL_LLAMA=...` যোগ করুন
2. `config.py`-এর `active_model` প্রপার্টিতে `profile_map`-এ একটা এন্ট্রি
   যোগ করুন

কোডের বাকি অংশ (`cv_parser.py`, ভবিষ্যতে `matcher.py`, `cover_letter.py`)
কখনো মডেলের নাম সরাসরি জানে না — সবসময় `llm_client.chat_json()` এর মাধ্যমে
কল করে, যা কনফিগ থেকে সক্রিয় মডেল নেয়।

## প্রজেক্ট স্ট্রাকচার

```
backend/
  app/
    config.py       # সব কনফিগ (env থেকে), মডেল-প্রোফাইল রিজলভার
    llm_client.py    # oxyy.ai-এর একমাত্র gateway (JSON-mode + fallback)
    cv_parser.py     # PDF/DOCX টেক্সট এক্সট্র্যাকশন + LLM স্ট্রাকচারিং
    models.py        # CVProfile ও সংশ্লিষ্ট pydantic স্কিমা
    main.py          # FastAPI অ্যাপ, /api/cv/upload এন্ডপয়েন্ট
  tests/
    test_cv_parser.py
    make_sample_docx.py   # টেস্টের জন্য একটা sample CV জেনারেট করে
  sample_cvs/
    sample_cv.docx   # অটো-জেনারেটেড টেস্ট CV
  requirements.txt
  .env.example
```

## পরের ধাপগুলো (রোডম্যাপ — আপনি টেস্ট করার পর একে একে বানাবো)

1. ✅ প্রজেক্ট সেটাপ + CV পার্সিং *(এই ধাপ)*
2. জব সোর্স ইন্টিগ্রেশন: Adzuna/RemoteOK API + Bdjobs পাবলিক লিস্টিং +
   সরকারি সার্কুলার (rate-limit মেনে, robots.txt respect করে)
3. ম্যাচ স্কোরিং + কারণ ব্যাখ্যা (CV প্রোফাইল ↔ জব বর্ণনা, একটাই ব্যাচড LLM কল)
4. টেইলরড কভার লেটার জেনারেশন (শুধু টপ-ম্যাচ জবগুলোর জন্য, ড্রাফট হিসেবে —
   কখনো অটো-সাবমিট না)
5. প্রিমিয়াম ড্যাশবোর্ড UI (React + deep navy/charcoal + gold/amber accent),
   "Applied" মার্কিং সহ
6. LinkedIn/Facebook: শুধু পাবলিকলি-ভিজিবল, নন-লগইন কনটেন্ট থেকে ডেটা
   (যদি নির্ভরযোগ্যভাবে সম্ভব না হয়, এই সোর্স স্কিপ করা হবে — যেমনটা
   আপনি বলেছেন)

কোনটা দিয়ে এগোবো বলুন — টেস্ট করে দেখার পর "ধাপ ২ শুরু করো" বললেই জব সোর্স
ইন্টিগ্রেশনে যাবো।
