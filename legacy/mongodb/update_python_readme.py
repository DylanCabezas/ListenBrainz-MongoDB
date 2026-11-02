from pathlib import Path

path = Path('README.md')
text = path.read_text(encoding='utf-8-sig')
if '## Demostración desde PowerShell' not in text:
    raise SystemExit(0)
start = text.index('## Demostración desde PowerShell')
end = text.index('## Pruebas e índices', start)
text = text[:start] + '''## Flujo completo en Python

Todo el flujo operativo de MongoDB se ejecuta con Python. Los archivos `.mongodb.js` y `scripts/baseline.cjs` se conservan como antecedentes; no son necesarios para ejecutar el proyecto.

Iniciar FastAPI:

```powershell
.\\.venv\\Scripts\\python.exe -m scripts.run_api --reload
```

Con el servidor iniciado, ejecutar en otra terminal la demostración HTTP repetible. Cada ronda crea un documento diferente, lo consulta, lo actualiza y elimina exclusivamente ese documento en un bloque de limpieza:

```powershell
.\\.venv\\Scripts\\python.exe -m scripts.demo_crud --rounds 3
```

Consultas analíticas equivalentes a `consultas.mongodb.js`: total de reproducciones, usuarios y artistas únicos, artistas, canciones y usuarios más escuchados, reproducciones recientes, filtro por artista, duración media y reproducciones por día UTC:

```powershell
.\\.venv\\Scripts\\python.exe -m scripts.queries --artist-name "NF & Sasha Sloan"
```

Índices y conteo de referencia, equivalentes a los scripts JavaScript anteriores:

```powershell
.\\.venv\\Scripts\\python.exe -m scripts.verify_indexes
.\\.venv\\Scripts\\python.exe -m scripts.baseline
```

Los scripts analíticos solo consultan datos. La demostración utiliza la API REST y no necesita mongosh ni Node.js. El importador y las pruebas también están implementados en Python. Los nombres de campos históricos presentes en los documentos se conservan.

''' + text[end:]
path.write_text(text, encoding='utf-8')
