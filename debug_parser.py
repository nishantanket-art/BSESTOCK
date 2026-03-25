import sys
sys.path.append(r"d:\pr")
from backend.services.scraper import _parse_screener_page

with open("test.html", "r", encoding="utf-8") as f:
    html = f.read()

result = _parse_screener_page(html, "TCS")
if result is None:
    print("RESULT IS NONE - Parser failed!")
    
    # Debug: manually trace what the parser sees
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    for section in soup.find_all("section"):
        heading = section.find(["h2", "h3"])
        if heading and "shareholding" in heading.get_text(strip=True).lower():
            print(f"Found section: [{heading.get_text(strip=True)}]")
            table = section.find("table")
            if table:
                rows = table.find_all("tr")
                print(f"Table has {len(rows)} rows")
                for row in rows[1:]:
                    cells = row.find_all(["th", "td"])
                    if cells:
                        label = cells[0].get_text(strip=True).lower()
                        print(f"  Label: [{label}] | 'promoter' in label: {'promoter' in label} | 'pledge' not in label: {'pledge' not in label}")
                        if "promoter" in label and "pledge" not in label:
                            vals = [c.get_text(strip=True).replace("%", "").strip() for c in cells[1:]]
                            print(f"  Values: {vals[:5]}...")
                            all_h = []
                            for v in vals:
                                try:
                                    all_h.append(float(v))
                                except ValueError:
                                    all_h.append(None)
                            clean = [v for v in all_h if v is not None]
                            print(f"  Parsed floats: {clean[:5]}...")
                            if len(clean) >= 2:
                                print(f"  Current: {clean[-1]}, Prev: {clean[-2]}")
            else:
                print("NO TABLE found!")
            break
else:
    print(f"SUCCESS! Result: {result}")
