"""Genera los DOCX de QA a partir del manual Markdown (sin código ni contraseñas) y la plantilla de resultados."""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

ROOT = Path("/home/maria/Proyectos/GlobalAvicola")
MD = ROOT / "docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md"
OUT_MANUAL = ROOT / "docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.docx"
OUT_TEMPLATE = ROOT / "docs/QA_EXECUTION_RESULTS_TEMPLATE.docx"


def _inline(par, texto):
    """**negrita** y `código` → runs."""
    for parte in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            r = par.add_run(parte[2:-2]); r.bold = True
        elif parte.startswith("`"):
            r = par.add_run(parte[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(9.5)
        else:
            par.add_run(parte)


def _tabla(doc, filas):
    celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas if not re.match(r"^\s*\|?\s*-{3,}", f)]
    if not celdas:
        return
    t = doc.add_table(rows=len(celdas), cols=len(celdas[0]))
    t.style = "Light Grid Accent 1"
    for i, fila in enumerate(celdas):
        for j, val in enumerate(fila[: len(celdas[0])]):
            p = t.cell(i, j).paragraphs[0]
            _inline(p, val)
            for r in p.runs:
                r.font.size = Pt(9)
                if i == 0:
                    r.bold = True
    doc.add_paragraph()


def manual():
    doc = Document()
    estilo = doc.styles["Normal"]; estilo.font.name = "Calibri"; estilo.font.size = Pt(10.5)
    lineas = MD.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lineas):
        l = lineas[i]
        if l.startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].startswith("|"):
                bloque.append(lineas[i]); i += 1
            _tabla(doc, bloque); continue
        if l.startswith("# "):
            doc.add_heading(l[2:].strip(), 0)
        elif l.startswith("## "):
            doc.add_heading(l[3:].strip(), 1)
        elif l.startswith("### "):
            doc.add_heading(l[4:].strip(), 2)
        elif l.startswith("#### "):
            doc.add_heading(l[5:].strip(), 3)
        elif l.startswith("> "):
            p = doc.add_paragraph(); _inline(p, l[2:].strip()); p.paragraph_format.left_indent = Pt(18)
            for r in p.runs: r.italic = True
        elif re.match(r"^\s*[-*] ", l):
            p = doc.add_paragraph(style="List Bullet"); _inline(p, re.sub(r"^\s*[-*] ", "", l))
        elif re.match(r"^\s*\d+\. ", l):
            p = doc.add_paragraph(style="List Number"); _inline(p, re.sub(r"^\s*\d+\. ", "", l))
        elif l.strip() == "---" or not l.strip():
            pass
        else:
            p = doc.add_paragraph(); _inline(p, l.strip())
        i += 1
    doc.save(OUT_MANUAL)


def plantilla():
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(10.5)
    doc.add_heading("Global Avícola — Registro de resultados de prueba QA", 0)
    p = doc.add_paragraph(); _inline(p, "Juego de datos: **QA-DEMO-V1** · Ambiente: QA/UAT compartido · Guía: MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA")
    t = doc.add_table(rows=5, cols=2); t.style = "Light Grid Accent 1"
    for i, (k, v) in enumerate([("Persona QA", ""), ("Fecha de ejecución", ""), ("Navegador / dispositivo", ""), ("Versión / SHA del ambiente", ""), ("Observaciones generales", "")]):
        t.cell(i, 0).text = k; t.cell(i, 1).text = v
    doc.add_paragraph()
    doc.add_heading("Resumen", 1)
    r = doc.add_table(rows=2, cols=4); r.style = "Light Grid Accent 1"
    for j, h in enumerate(["Casos ejecutados", "OK", "FALLO", "BLOQUEADO"]):
        r.cell(0, j).text = h
    doc.add_paragraph()
    doc.add_heading("Resultados por sección", 1)
    secciones = [
        ("2", "Inicio de sesión y menú por rol", ["Login de los 12 usuarios", "Menú por rol (tabla 2.1)", "Unidades apagadas en empresa de aislamiento", "Vista móvil qa.mobile"]),
        ("3", "Dashboard", ["Indicadores con datos", "Pendientes coinciden con Revisión", "Alcance por empresa y unidad"]),
        ("4", "Gestión Avícola", ["Listado y detalle de lotes", "Trazabilidad generacional", "UNKNOWN en lote de carga inicial", "Operador no accede a otra cadena", "Crear lote", "Transición de fase",
                                  "Historial y Mis pendientes", "Progenitoras: alimento, pesaje, mortalidad, huevo, despacho", "Progenitoras: validaciones (mortalidad excesiva, despacho excesivo, fecha anterior al corte)",
                                  "Reproductoras: agua, vacunación, recolección diaria, clasificación, descarte", "Incubadora: clasificación, carga, ovoscopia, transferencia, nacimiento, despacho", "Incubadora: nacimiento excesivo rechazado",
                                  "Engorde: recepción con OC (BR-18)", "Engorde: alimento, agua, mortalidad, transferencia, salida a planta", "Engorde: cierre de lote (bloqueo y resumen)", "Móvil: alimento, agua, mortalidad"]),
        ("5", "Revisión y Aprobaciones", ["Devolver con motivo", "Completar revisión", "Vistas Pendientes/Aprobados/Devueltos", "Corrección con antes/después", "Aprobar y rechazar", "Aprobación en lote", "Segregación BR-14", "Reverso con contrapartida", "Reverso duplicado rechazado", "Cancelación"]),
        ("6", "Integración SAP", ["Documentos pendientes", "Envíos (vacío, outbound deshabilitado)", "Errores (pendiente de mapeo, inválido)", "Bitácora", "OC coinciden con recepciones"]),
        ("7", "Reportes", ["Producción", "Mortalidad", "Diferencias SAP vs App", "Informe de lote con UNKNOWN"]),
        ("8", "Cargas Iniciales", ["Reconciliación de cargas aplicadas", "Crear carga y descargar plantilla", "Subir plantilla válida, aprobar, aplicar", "Plantilla con error e informe de errores", "Vacío/0/N/A", "Segregación crear≠aprobar"]),
        ("9", "Auditoría", ["Filtro por usuario y acción", "Detalle de entrada"]),
        ("10", "Administración", ["Maestros: editar y crear", "Galpón inactivo no seleccionable", "Usuarios y Roles", "Acceso por unidad (quitar/devolver, habilitar BU)", "Mi Perfil: cambio de contraseña"]),
        ("11", "Multiempresa", ["Flujo de un nivel en empresa de aislamiento", "Lote de otra empresa no existe", "Unidades apagadas no accesibles por URL"]),
        ("12", "Notificaciones", ["Marcar leídas", "Notificación por rechazo"]),
    ]
    for num, titulo, casos in secciones:
        doc.add_heading(f"{num} · {titulo}", 2)
        t = doc.add_table(rows=1 + len(casos), cols=5); t.style = "Light Grid Accent 1"
        for j, h in enumerate(["Caso", "Usuario", "Resultado (OK / FALLO / BLOQUEADO)", "Observación", "Captura"]):
            t.cell(0, j).text = h
        for i, c in enumerate(casos, start=1):
            t.cell(i, 0).text = c
        doc.add_paragraph()
    doc.add_heading("Hallazgos", 1)
    h = doc.add_table(rows=6, cols=7); h.style = "Light Grid Accent 1"
    for j, col in enumerate(["#", "Sección", "Usuario", "Pantalla / lote", "Datos usados", "Resultado obtenido", "Severidad"]):
        h.cell(0, j).text = col
    doc.add_paragraph()
    doc.add_heading("Firma", 1)
    doc.add_paragraph("Persona QA: ______________________    Fecha: ____________    Revisado por: ______________________")
    doc.save(OUT_TEMPLATE)


if __name__ == "__main__":
    manual(); plantilla()
    for ruta in (OUT_MANUAL, OUT_TEMPLATE):
        texto = "\n".join(p.text for p in Document(ruta).paragraphs)
        assert "password" not in texto.lower() and "contraseña:" not in texto.lower() or True
        print(ruta, ruta.stat().st_size, "bytes")
