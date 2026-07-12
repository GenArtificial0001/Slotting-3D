# Slotting 3D — publicación en GitHub

## Recomendación de seguridad

La versión corporativa puede contener datos reales incrustados dentro del HTML. Aunque se active Modo Demo, un repositorio público permite inspeccionar el código fuente completo. Para publicar en abierto, usar una compilación sanitizada que no incluya datos reales precargados.

## Estructura sugerida

```text
slotting-3d/
├─ index.html
├─ README.md
└─ screenshots/
```

Renombrar la versión que se publicará a `index.html`.

## Subir con Git desde Windows PowerShell

```powershell
mkdir slotting-3d
cd slotting-3d
Copy-Item "C:\RUTA\Sistema_Slotting_3D_v33_Project_Manager_Eliminacion_Swipe.html" ".\index.html"

git init
git add index.html
git commit -m "feat: project manager deletion and swipe actions"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/slotting-3d.git
git push -u origin main
```

## Publicar con GitHub Pages

1. Abrir el repositorio en GitHub.
2. Entrar en **Settings**.
3. Entrar en **Pages**.
4. Elegir **Deploy from a branch**.
5. Seleccionar la rama `main` y la carpeta `/root`.
6. Guardar.

## Actualizaciones posteriores

```powershell
git add index.html
git commit -m "fix: improve project manager"
git push
```

## Antes de hacer público el repositorio

- Verificar que el HTML no contenga productos, ubicaciones, rutas, usuarios ni proyectos reales.
- Probar el Modo Demo desde una ventana privada.
- Revisar el archivo con un editor de texto y buscar códigos reales conocidos.
- Usar repositorio privado mientras se valida la versión pública.
