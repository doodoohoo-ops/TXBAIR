import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
from playwright.async_api import async_playwright

TARGET_SOURCES = [
    {
        "agency": "SEC (ก.ล.ต.)",
        "category": "ข่าว ก.ล.ต.",
        "url": "https://www.sec.or.th/TH/Pages/News_LISTVIEW.aspx"
    },
    {
        "agency": "RD (กรมสรรพากร)",
        "category": "ข่าวกรมสรรพากร",
        "url": "https://www.rd.go.th/21.html"
    },
    {
        "agency": "RD (กรมสรรพากร)",
        "category": "กฎหมายออกใหม่",
        "url": "https://www.rd.go.th/21221.html"
    },
    {
        "agency": "SET (ตลาดหลักทรัพย์ฯ)",
        "category": "กฎเกณฑ์ตลาดหลักทรัพย์",
        "url": "https://www.set.or.th/th/rules-regulations/regulations"
    },
    {
        "agency": "SET (ตลาดหลักทรัพย์ฯ)",
        "category": "หนังสือเวียน",
        "url": "https://www.set.or.th/th/rules-regulations/circulars"
    },
    {
        "agency": "SET (ตลาดหลักทรัพย์ฯ)",
        "category": "แบบฟอร์ม",
        "url": "https://www.set.or.th/th/rules-regulations/forms"
    },
    {
        "agency": "TFEX",
        "category": "ประกาศและแนวปฏิบัติ TFEX",
        "url": "https://www.tfex.co.th/th/rules-regulations/search-result?type=Announcement,Practice,Guideline,Form&title=8ab78cf4-40a2-4463-a071-19aeed3d8131,fd5f2f24-8fbd-4fe3-9c16-71f8663655b3,87a23195-1cb0-4611-a140-b0a7f2f5ac86,e0a6d2bd-9918-4625-a443-00ee670ec58d&status=EFFECTIVE&relate=%E0%B8%AA%E0%B8%B4%E0%B8%99%E0%B8%84%E0%B9%89%E0%B8%B2%E0%B8%97%E0%B8%B5%E0%B9%88%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B8%82%E0%B8%B2%E0%B8%A2%E0%B9%83%E0%B8%99%20TFEX,%E0%B8%9C%E0%B8%B9%E0%B9%89%E0%B8%94%E0%B8%B9%E0%B9%81%E0%B8%A5%E0%B8%AA%E0%B8%A0%E0%B8%B2%E0%B8%9E%E0%B8%84%E0%B8%A5%E0%B9%88%E0%B8%AD%E0%B8%87,%E0%B8%A3%E0%B8%B2%E0%B8%84%E0%B8%B2%E0%B8%AA%E0%B8%B9%E0%B8%87%E0%B8%AA%E0%B8%B8%E0%B8%94%E0%B9%83%E0%B8%99%E0%B9%81%E0%B8%95%E0%B9%88%E0%B8%A5%E0%B8%B0%E0%B8%A7%E0%B8%B1%E0%B8%99,%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%88%E0%B8%B3%E0%B8%81%E0%B8%B1%E0%B8%94%E0%B8%90%E0%B8%B2%E0%B8%99%E0%B8%B0%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%96%E0%B8%B7%E0%B8%AD%E0%B8%84%E0%B8%A3%E0%B8%AD%E0%B8%87,%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B8%82%E0%B8%B2%E0%B8%A2%E0%B8%A3%E0%B8%B2%E0%B8%A2%E0%B9%83%E0%B8%AB%E0%B8%8D%E0%B9%88%20%28Block%20Trade%29,%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B9%80%E0%B8%A0%E0%B8%97%E0%B8%84%E0%B8%B3%E0%B8%AA%E0%B8%B1%E0%B9%88%E0%B8%87%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B8%82%E0%B8%B2%E0%B8%A2,%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%AB%E0%B8%A2%E0%B8%B8%E0%B8%94%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B8%82%E0%B8%B2%E0%B8%A2%E0%B9%80%E0%B8%9B%E0%B9%87%E0%B8%99%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%8A%E0%B8%B1%E0%B9%88%E0%B8%A7%E0%B8%84%E0%B8%A3%E0%B8%B2%E0%B8%A7,%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B9%80%E0%B8%8A%E0%B8%B7%E0%B9%88%E0%B8%AD%E0%B8%A1%E0%B8%95%E0%B9%88%E0%B8%AD%E0%B8%A3%E0%B8%B0%E0%B8%9A%E0%B8%9A,%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%8A%E0%B8%B3%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%84%E0%B8%B2,%E0%B8%AD%E0%B8%B1%E0%B8%95%E0%B8%A3%E0%B8%B2%E0%B8%AB%E0%B8%A5%E0%B8%B1%E0%B8%81%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%81%E0%B8%B1%E0%B8%99,%E0%B9%81%E0%B8%99%E0%B8%A7%E0%B8%97%E0%B8%B2%E0%B8%87%E0%B8%81%E0%B8%B2%E0%B8%A3%E0%B8%9B%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%AA%E0%B8%B1%E0%B8%8D%E0%B8%8D%E0%B8%B2,%E0%B8%A3%E0%B8%B2%E0%B8%84%E0%B8%B2%E0%B8%97%E0%B8%B5%E0%B9%88%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%8A%E0%B8%B3%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%84%E0%B8%B2"
    },
    {
        "agency": "TCH (สำนักหักบัญชี)",
        "category": "กฎเกณฑ์ TCH",
        "url": "https://www.set.or.th/th/tch/rules-regulations/regulations"
    },
    {
        "agency": "TSD (ศูนย์รับฝากหลักทรัพย์)",
        "category": "กฎเกณฑ์ TSD",
        "url": "https://www.set.or.th/th/tsd/rules-regulations/regulations#equity-tsd"
    },
    {
        "agency": "NVDR",
        "category": "ข่าวประกาศ NVDR",
        "url": "https://www.set.or.th/nvdr/th/news/others_all.html"
    },
    {
        "agency": "ThaiBMA",
        "category": "Rules & Regulations",
        "url": "https://www.thaibma.or.th/EN/Rule/Rules.aspx"
    }
]

OUTPUT_FILE = "scraped_results.json"
MAX_ITEMS_PER_SOURCE = 15

DATE_REGEX = re.compile(
    r'(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|'
    r'มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม|'
    r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    re.IGNORECASE
)

IGNORE_WORDS = [
    "เข้าสู่ระบบ", "สมัครสมาชิก", "หน้าแรก", "ติดต่อเรา", "แผนผังเว็บไซต์",
    "นโยบายความเป็นส่วนตัว", "คุกกี้", "อ่านต่อ", "ดูทั้งหมด", "ดาวน์โหลด",
    "คลิกที่นี่", "ย้อนกลับ", "ถัดไป", "login", "register", "home", "contact",
    "sitemap", "privacy", "cookie", "read more", "view all"
]

async def extract_announcements(page, source, scrape_date_str):
    url = source["url"].strip()
    print(f"กำลังดึงข้อมูล: {source['agency']} - {source['category']} ...")
    items = []

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000)

        raw_links = await page.evaluate("""() => {
            const results = [];
            const root = document.querySelector('main, #main, .main-content, #content, .content') || document.body;
            const anchors = root.querySelectorAll('a[href]');

            for (const a of anchors) {
                const href = a.getAttribute('href') || '';
                if (!href || href.startsWith('javascript:') || href.startsWith('#') || href.startsWith('mailto:')) continue;
                if (a.closest('nav, header, footer, .navbar, .menu, .sidebar, .breadcrumb')) continue;

                let title = (a.innerText || a.getAttribute('title') || '').replace(/\\s+/g, ' ').trim();
                const container = a.closest('tr, li, article, .card, .row, .news-item, .list-group-item, .table-row') || a.parentElement;
                const contextText = container ? container.innerText.replace(/\\s+/g, ' ').trim() : title;

                results.push({
                    href: a.href,
                    title: title,
                    context: contextText
                });
            }
            return results;
        }""")

        seen_urls = set()
        for link in raw_links:
            full_url = urljoin(url, link["href"]).strip()
            if full_url in seen_urls or full_url == url:
                continue

            title = link["title"]
            context = link["context"]

            is_doc_file = any(ext in full_url.lower() for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"])
            if is_doc_file and len(title) < 12 and len(context) >= 12:
                title = context[:200]

            if len(title) < 12:
                continue
            if any(w == title.lower() for w in IGNORE_WORDS):
                continue

            date_match = DATE_REGEX.search(context)
            publish_date = date_match.group(1) if date_match else scrape_date_str

            seen_urls.add(full_url)
            items.append({
                "agency": source["agency"],
                "category": source["category"],
                "title": title[:250],
                "publish_date": publish_date,
                "doc_url": full_url,
                "source_page": url
            })

            if len(items) >= MAX_ITEMS_PER_SOURCE:
                break

        print(f" -> สำเร็จ: พบ {len(items)} รายการ")

    except Exception as e:
        print(f" -> ข้อผิดพลาด ({url}): {e}")

    return items

async def main():
    tz_th = timezone(timedelta(hours=7))
    now = datetime.now(tz_th)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    today_str = now.strftime("%Y-%m-%d")

    all_items = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()

        for source in TARGET_SOURCES:
            extracted = await extract_announcements(page, source, today_str)
            all_items.extend(extracted)

        await browser.close()

    payload = {
        "updated_at": now_str,
        "total_items": len(all_items),
        "items": all_items
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[{now_str}] บันทึกข้อมูลทั้งหมด {len(all_items)} รายการ ลงไฟล์ {OUTPUT_FILE} เรียบร้อย!")

if __name__ == "__main__":
    asyncio.run(main())
