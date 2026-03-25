from bs4 import BeautifulSoup

with open("test.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

out = []
for i, s in enumerate(soup.find_all("section")):
    heading = s.find(["h2", "h3"])
    if heading:
        h = heading.get_text(strip=True)
        out.append(f"Section {i}: [{h}]")
        if "share" in h.lower() or "hold" in h.lower():
            out.append("  === SHAREHOLDING MATCH ===")
            table = s.find("table")
            if table:
                rows = table.find_all("tr")
                out.append(f"  Rows: {len(rows)}")
                for j, row in enumerate(rows[:8]):
                    cells = row.find_all(["th", "td"])
                    texts = [c.get_text(strip=True)[:25] for c in cells]
                    out.append(f"  Row{j}: {texts}")
            else:
                out.append("  NO TABLE FOUND")

with open("html_analysis.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("Done! Written to html_analysis.txt")
