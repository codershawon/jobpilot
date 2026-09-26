"""
ক্যাটাগরির তালিকা — ফ্রন্টএন্ড এখান থেকেই ফিল্টার বার বানাবে।

লেবেল হার্ডকোড না করে এখান থেকে আনার সুবিধা: নতুন সেক্টর বা কাজের ক্ষেত্র
যোগ করলে শুধু classifier.py বদলালেই ফ্রন্টএন্ডে নিজে থেকে চলে আসবে।
"""

from fastapi import APIRouter

from app.services.classifier import all_functions, all_sectors

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
async def get_categories():
    return {
        "sectors": all_sectors(),
        "functions": all_functions(),
        "sources": [
            {"id": "BDJOBS", "label_bn": "বিডিজবস", "label_en": "Bdjobs"},
            {"id": "Govt", "label_bn": "সরকারি পোর্টাল", "label_en": "Govt Portals"},
            {"id": "Remotive", "label_bn": "Remotive", "label_en": "Remotive"},
            {"id": "RemoteOK", "label_bn": "RemoteOK", "label_en": "RemoteOK"},
            {"id": "Arbeitnow", "label_bn": "Arbeitnow", "label_en": "Arbeitnow"},
            {"id": "LinkedIn", "label_bn": "LinkedIn", "label_en": "LinkedIn"},
            {"id": "ReliefWeb", "label_bn": "ReliefWeb (NGO)", "label_en": "ReliefWeb"},
            {"id": "WeWorkRemotely", "label_bn": "WeWorkRemotely", "label_en": "WeWorkRemotely"},
            {"id": "Himalayas", "label_bn": "Himalayas", "label_en": "Himalayas"},
        ],
    }