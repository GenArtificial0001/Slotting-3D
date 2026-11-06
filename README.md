# Slotting 3D

Visualizador 3D de slotting de almacén con simulación del recorrido del picker (metros, tiempos, escenario actual vs. futuro). Es una única página HTML sin backend: todo corre en el navegador y los Excel que cargues **no salen de tu equipo**.

## Versión pública = sin datos

Esta compilación **no trae ningún dato real precargado**: arranca vacía y los datos se cargan desde la pestaña *Fuentes de datos* (o con *Importar carpeta*). El dataset embebido de la versión corporativa se reemplaza por uno vacío en el build (`--public`), que además falla si detecta un código real conocido.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | App lista para publicar (GitHub Pages). **Generado**, no editar a mano. |
| `fuente/Slotting-3D.src.html` | Fuente (bloques `vNN` apilados). Es lo que se edita. |
| `build-sharepoint.py` | Genera el HTML final: une el JS en un solo programa y ata los `onclick` por código (necesario en SharePoint por su CSP). |
| `vendor/xlsx.full.min.js` | SheetJS 0.18.5 (Apache-2.0), embebido en el build para la vista Packaging. |

## Compilar

```bash
python build-sharepoint.py --public salida/   # versión pública: salida/index.html + salida/fuente/
python build-sharepoint.py                    # versión corporativa (requiere el dataset real; no publicar)
```

Sin dependencias (solo biblioteca estándar de Python). Para probar: `python -m http.server 8000` y abrir `http://localhost:8000/`.

## GitHub Pages

*Settings → Pages → Deploy from a branch → `main` / `(root)`*.

## Antes de publicar cambios

- No subir exportaciones de SAP/SMART (Storage Bin, Fixed Bin Assignment, Warehouse Task, etc.): quedan fuera por `.gitignore`.
- Compilar siempre con `--public`.
