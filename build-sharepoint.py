#!/usr/bin/env python3
"""Genera Slotting-3D.html (el archivo que se publica en SharePoint) a partir de Slotting-3D.src.html (la fuente de verdad).

Por qué hace falta: el Ford Modern Script Editor de SharePoint ejecuta CADA <script> en línea por separado con
eval() y bajo una CSP sin 'unsafe-inline'. Eso rompe la app tal cual está escrita:
  1) `const State`, `function switchView`, etc. del script principal no se ven desde los parches (v23…v56)
     -> "ReferenceError: State is not defined".
  2) Los onclick="..." / onchange="..." del markup quedan bloqueados por la CSP ("Executing inline event handler
     violates the following Content Security Policy directive").

Solución (el HTML de origen no se toca; el generado funciona igual en SharePoint que abierto en una pestaña):
  * Todo el JavaScript en línea, en su orden original, se une en UN solo programa que corre con eval indirecto
    (ámbito global, sin heredar strict del bundle del editor) dentro de una función contenedora: así todos los
    bloques comparten ámbito y no se ensucia window con ~350 nombres.
  * El código viaja dentro de un <textarea> (inerte para el editor) y un cargador mínimo lo ejecuta.
  * Un puente convierte los atributos on* en addEventListener, evaluando el código del atributo dentro del mismo
    ámbito (CSP permite 'unsafe-eval'), también para el HTML que la app genera después con innerHTML.

Uso:  python build-sharepoint.py        (sin dependencias; solo biblioteca estándar)
      python build-sharepoint.py --public CARPETA
          Compilación PÚBLICA (GitHub): igual, pero con el dataset real de Ford (PRELOADED) reemplazado por uno vacío.
          Escribe CARPETA/index.html y CARPETA/fuente/Slotting-3D.src.html (sanitizada). Nunca publicar el archivo normal.
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'fuente' / 'Slotting-3D.src.html'   # se edita ESTE archivo (bloques vNN)
OUT = HERE / 'Slotting-3D.html'       # generado: es el que se sube/publica; no se edita a mano
TEXTAREA_ID = 'slotting-sp-code'
VENDOR_DIR = HERE / 'vendor'
XLSX_FILE = VENDOR_DIR / 'xlsx.full.min.js'
XLSX_URL = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js'   # misma versión que la sub-app de Packaging

SCRIPT_RE = re.compile(r'<script\b([^>]*)>(.*?)</script\s*>', re.S | re.I)

BRIDGE = r'''
/* ===== sp-inline-handler-bridge (generado por build-sharepoint.py) ===== */
(function(){
  'use strict';
  /* Puente de manejadores en línea: la CSP de SharePoint bloquea onclick="..." y similares, pero permite eval.
     Cada atributo on* se quita y se reemplaza por un listener cuyo código se evalúa en el ámbito de la app. */
  function mk(__codigo){ return eval('(function(event){' + __codigo + '\n})'); }
  var EVT = /^(?:data-sp-)?on[a-z]+$/;   // data-sp-on*: el build renombra los on* del markup estático para que la CSP ni los vea
  var EVS = 'click,change,input,keydown,keyup,keypress,submit,focus,blur,dblclick,mousedown,mouseup,mouseover,mouseout,mouseenter,mouseleave,pointerdown,pointerup,touchstart,dragstart,dragover,dragenter,dragleave,dragend,drop,load,error,contextmenu,wheel,scroll'.split(',');
  var SEL = EVS.map(function(e){ return '[on' + e + '],[data-sp-on' + e + ']'; }).join(',');
  var _SEL_VIEJO = '[onclick],[onchange],[oninput],[onkeydown],[onkeyup],[onkeypress],[onsubmit],[onfocus],[onblur],[ondblclick],[onmousedown],[onmouseup],[onmouseover],[onmouseout],[onmouseenter],[onmouseleave],[onpointerdown],[onpointerup],[ontouchstart],[ondragstart],[ondragover],[ondragenter],[ondragleave],[ondragend],[ondrop],[onload],[onerror],[oncontextmenu],[onwheel],[onscroll]';
  function atar(el){
    if(!el || el.nodeType !== 1 || !el.attributes) return;
    var attrs = Array.prototype.slice.call(el.attributes);
    for(var i = 0; i < attrs.length; i++){
      var n = attrs[i].name;
      if(!EVT.test(n)) continue;
      var codigo = attrs[i].value;
      el.removeAttribute(n);
      if(!codigo) continue;
      try{
        var fn = mk(codigo);
        atados++;
        el.addEventListener(n.replace(/^(?:data-sp-)?on/, ''), function(f){
          return function(ev){ var r = f.call(this, ev); if(r === false && ev && ev.cancelable) ev.preventDefault(); };
        }(fn));
      }catch(e){ console.warn('SharePoint: no se pudo atar ' + n + ' =', codigo, e); }
    }
  }
  function recorrer(raiz){
    if(!raiz || raiz.nodeType !== 1) return;
    atar(raiz);
    var hijos = raiz.querySelectorAll(SEL);
    for(var i = 0; i < hijos.length; i++) atar(hijos[i]);
  }
  var atados = 0;
  recorrer(document.body);
  try{
    new MutationObserver(function(muts){
      for(var i = 0; i < muts.length; i++){
        var m = muts[i];
        for(var j = 0; j < m.addedNodes.length; j++) recorrer(m.addedNodes[j]);
      }
    }).observe(document.body, {childList: true, subtree: true});
  }catch(e){}
  window.__spHandlerBridge = {atar: atar, recorrer: recorrer, atados: function(){ return atados; }};
  console.info('Slotting 3D (compilacion SharePoint ' + ((window.__SLOTTING_BUILD || {}).version || '?') + '): ' + atados + ' manejadores atados.');
})();
'''


def xlsx_vendor():
    """SheetJS para la sub-app de Packaging (la CSP de SharePoint puede bloquear jsDelivr). Se cachea en vendor/."""
    if not XLSX_FILE.exists():
        try:
            VENDOR_DIR.mkdir(exist_ok=True)
            with urllib.request.urlopen(XLSX_URL, timeout=30) as r:
                XLSX_FILE.write_bytes(r.read())
            print('descargado', XLSX_FILE.name)
        except Exception as e:
            print('AVISO: no se pudo obtener SheetJS (%s); Packaging no podra leer .xlsx en SharePoint.' % e)
            return ''
    return XLSX_FILE.read_text(encoding='utf-8')


EMPTY_PRELOADED = ('const PRELOADED={"meta":{"generated":"","sourceCounts":{},"defaultAisle":"","routes":["FMC","KIT","LAD","LAL","NPP","NR3","NRC","NRD","NRK","NRT"],'
                   '"sequenceOverrides":{}},"bins":[],"products":{}};')


def sanitize(src):
    """Reemplaza el dataset real embebido (PRELOADED: bins, productos, uso por hora, SMART…) por uno vacío."""
    lines = src.split('\n')
    idx =[i for i, l in enumerate(lines) if l.startswith('const PRELOADED=')]
    if len(idx) != 1:
        sys.exit('No se encontró una única línea "const PRELOADED=".')
    lines[idx[0]] = EMPTY_PRELOADED
    out = '\n'.join(lines)
    if 'N1WB-E27936-BD' in out:
        sys.exit('La versión sanitizada todavía contiene un código real conocido: no se publica.')
    return out


def main(src=None, out_path=None):
    src = src if src is not None else SRC.read_text(encoding='utf-8')
    out_path = out_path or OUT
    parts = []
    for m in SCRIPT_RE.finditer(src):
        attrs, body = m.group(1), m.group(2)
        if re.search(r'\bsrc\s*=', attrs, re.I):
            sys.exit('Hay un <script src>: esta compilación asume que todo el JS está en línea.')
        t = re.search(r'\btype\s*=\s*["\']?([^"\'\s>]+)', attrs, re.I)
        if t and t.group(1).lower() not in ('text/javascript', 'application/javascript', 'module'):
            sys.exit('Script con type=%s: revisar a mano.' % t.group(1))
        if t and t.group(1).lower() == 'module':
            sys.exit('Hay un <script type=module>: no soportado por esta compilación.')
        ident = re.search(r'\bid\s*=\s*["\']([^"\']+)', attrs, re.I)
        parts.append((ident.group(1) if ident else 'principal', body))

    # HTML sin scripts (los <style>, <link> y el markup quedan en su sitio).
    markup = SCRIPT_RE.sub('', src)
    # Los on*="..." del markup estático se renombran a data-sp-on*: así la CSP de SharePoint no los ve (y no llena la
    # consola de avisos); el puente los ata igual. Solo se tocan dentro de etiquetas, respetando las comillas.
    tag_re = re.compile(r"""<[a-zA-Z][^\s>/]*(?:\s+[^\s=>/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*\s*/?>""")
    attr_re = re.compile(r'(\s)on([a-z]+)(\s*=)')
    renamed = [0]

    def fix_tag(m):
        def one(a):
            renamed[0] += 1
            return '%sdata-sp-on%s%s' % (a.group(1), a.group(2), a.group(3))
        return attr_re.sub(one, m.group(0))
    markup = tag_re.sub(fix_tag, markup)
    print('atributos on* renombrados en el markup:', renamed[0])
    if '</body>' not in markup:
        sys.exit('No se encontró </body>.')

    chunks = ['/* Slotting 3D · compilación para SharePoint (todos los bloques en un solo ámbito) */', '(function(){']
    for ident, body in parts:
        chunks.append('\n/* ===== %s ===== */\n%s\n;' % (ident, body.strip('\n')))
    chunks.append('\n/* ===== sp-vendor (SheetJS para Packaging) ===== */\nwindow.__spVendor = {xlsx: %s};' % json.dumps(xlsx_vendor()))
    chunks.append(BRIDGE)
    chunks.append('\n}).call(window);\n//# sourceURL=slotting-3d-bundle.js\n')
    code = '\n'.join(chunks)
    if '</textarea' in code.lower():
        print('aviso: el código contiene "</textarea"; se escapa con &lt; (reversible).')

    # El primer salto de línea tras <textarea> lo descarta el parser; se antepone uno para no perder nada.
    holder = '<textarea id="%s" style="display:none" aria-hidden="true" tabindex="-1">\n%s</textarea>' % (
        TEXTAREA_ID, html.escape(code, quote=False))
    loader = (
        '<script id="slotting-sp-loader">\n'
        '(function(){\n'
        "  var ta = document.getElementById('%s');\n"
        "  if(!ta){ console.error('Slotting 3D: no se encontro el codigo embebido (textarea %s).'); return; }\n"
        '  var code = ta.value;\n'
        '  ta.parentNode.removeChild(ta);\n'
        '  (0, eval)(code);\n'
        '})();\n'
        '</script>\n' % (TEXTAREA_ID, TEXTAREA_ID))

    i = markup.rfind('</body>')
    out = markup[:i] + holder + '\n' + loader + markup[i:]
    out = out.replace('<html', '<!-- GENERADO por build-sharepoint.py desde fuente/Slotting-3D.src.html: no editar este archivo. -->\n<html', 1)
    Path(out_path).write_text(out, encoding='utf-8', newline='')
    print('OK %s  (%.2f MB, %d bloques de JS unidos)' % (Path(out_path).name, len(out.encode('utf-8')) / 1e6, len(parts)))


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--public':
        dest = Path(sys.argv[2])
        (dest / 'fuente').mkdir(parents=True, exist_ok=True)
        clean = sanitize(SRC.read_text(encoding='utf-8'))
        (dest / 'fuente' / 'Slotting-3D.src.html').write_text(clean, encoding='utf-8', newline='')
        main(src=clean, out_path=dest / 'index.html')
    else:
        main()
