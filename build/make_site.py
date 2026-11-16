"""Прави docs/index.html + docs/app.js от шаблона: приложението зарежда ./data.json при отваряне,
така че всяко ежедневно обновяване стига до потребителите без нова версия на приложението."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
t = (ROOT / "build" / "template.html").read_text()
head, rest = t.split("<script>", 1)
js, tail = rest.split("</script>", 1)
assert js.count("const D = __DATA__;") == 1
(ROOT / "docs" / "app.js").write_text(js.replace("const D = __DATA__;", "const D = window.__D;"))
loader = """<script>
fetch("data.json", { cache: "no-cache" }).then(r => { if (!r.ok) throw r.status; return r.json(); })
  .then(d => { window.__D = d; const s = document.createElement("script"); s.src = "app.js?v=" + encodeURIComponent(d.date); document.body.appendChild(s); })
  .catch(() => document.body.insertAdjacentHTML("afterbegin", '<p style="padding:24px;font:16px sans-serif">Цените не се заредиха. Провери връзката и опитай пак.</p>'));
</script>"""
(ROOT / "docs" / "index.html").write_text(head + loader + tail)
print("docs/index.html + app.js")
