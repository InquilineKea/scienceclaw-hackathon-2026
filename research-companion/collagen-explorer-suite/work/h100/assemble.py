from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2]
original=(root/'outputs/interactive_explorer.html').read_text()
section=(root/'work/h100/section.html').read_text()
data=(root/'work/site/dist/h100/results.json').read_text()
nav='<nav class="explorer-nav" aria-label="Explorer studies"><a href="#original-model">Original adhesion model</a><a class="new-study" href="#matched-stiffness">New: matched-stiffness H100 results →</a><a href="original.html">Unchanged original HTML ↗</a></nav>'
page=original.replace('<title>Collagen Mechanics Explorer | Viscoelastic adhesion lab</title>','<title>Collagen Mechanics Explorer | Adhesion and H100 network results</title>',1)
page=page.replace('</head>','<link rel="stylesheet" href="h100/style.css"></head>',1)
page=page.replace('<main>','<main id="original-model">'+nav,1)
page=page.replace('</main>',section+'</main>',1)
page=page.replace('</body>','<script type="application/json" id="h100-data">'+data.replace('<','\\u003c')+'</script><script src="h100/app.js"></script></body>',1)
(root/'work/site/dist/index.html').write_text(page)
print(json.dumps({'size_bytes':len(page.encode()),'original_sha256':hashlib.sha256((root/'work/site/dist/original.html').read_bytes()).hexdigest()}))
