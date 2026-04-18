import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from unstructured.partition.auto import partition
import tempfile
import time

st.set_page_config(
    page_title="Extractor fiscal",
    page_icon=":money_with_wings:",
    layout="wide"
)
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("La llave API no está configurada")
    st.stop()

client = OpenAI(api_key=api_key)

MAX_ARCHIVOS = 5
MAX_SIZE_MB = 2


def leer_archivo(file):
    try:
        elementos = partition(filename=file)
        texto_completo = []
        for elemento in elementos:
            texto_completo.append(str(elemento))
        return "\n".join(texto_completo)
    except Exception as e:
        return None


def extraer_datos_con_ia(texto):
    prompt = f"""
Eres un asistente que extrae información de textos desordenados.

TEXTO A ANALIZAR:
{texto}

INSTRUCCIONES:
Extrae la siguiente información del texto y responde ÚNICAMENTE con un JSON válido, sin texto adicional:

{{
  "nombre_cliente": "nombre completo del cliente",
  "monto": "monto en números (sin símbolos)",
  "fecha": "fecha en formato YYYY-MM-DD",
  "tipo_solicitud": "VENTA, QUEJA o FACTURA"
}}

REGLAS IMPORTANTES:
- Si no encuentras algún dato, pon "NO_ENCONTRADO"
- NO agregues explicaciones, solo el JSON
- El monto debe ser solo números (sin $, sin comas)
- La fecha debe estar en formato YYYY-MM-DD
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un extractor de datos. Solo respondes en formato JSON válido."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content


def validar_y_convertir_json(respuesta):
    respuesta_limpia = respuesta.strip()

    if respuesta_limpia.startswith("```json"):
        respuesta_limpia = respuesta_limpia.replace("```json", "").replace("```", "").strip()
    elif respuesta_limpia.startswith("```"):
        respuesta_limpia = respuesta_limpia.replace("```", "").strip()

    try:
        return json.loads(respuesta_limpia)
    except json.JSONDecodeError:
        return None


def validar_datos_extraidos(datos_json):
    if not datos_json:
        return False

    campos_encontrados = 0

    for valor in datos_json.values():
        if valor and valor != "NO_ENCONTRADO":
            campos_encontrados += 1

    return campos_encontrados >= 1


def procesar_archivo(archivo_subido):

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo_subido.name)[1]) as tmp_file:
        tmp_file.write(archivo_subido.getvalue())
        tmp_path = tmp_file.name

    texto = leer_archivo(tmp_path)
    os.unlink(tmp_path)

    if not texto:
        return {
            "datos": None,
            "estado": "error_lectura",
            "mensaje": "Error al leer el archivo"
        }

    status_placeholder = st.empty()

    max_intentos = 3

    for intento in range(1, max_intentos + 1):
        status_placeholder.info(f" Intento {intento} de {max_intentos}")

        respuesta_ia = extraer_datos_con_ia(texto)
        datos_json = validar_y_convertir_json(respuesta_ia)

        if datos_json:
            if validar_datos_extraidos(datos_json):
                status_placeholder.success(f"✅ Datos extraídos en intento {intento}")
                return {
                    "datos": datos_json,
                    "estado": "exitoso",
                    "mensaje": f"Intento {intento}"
                }
            else:
                status_placeholder.empty()
                return {
                    "datos": None,
                    "estado": "sin_datos",
                    "mensaje": "Sin información relevante"
                }

        if intento < max_intentos:
            time.sleep(1)
        else:
            status_placeholder.empty()
            return {
                "datos": None,
                "estado": "error_procesamiento",
                "mensaje": "Error después de 3 intentos"
            }
    return {
        "datos": None,
        "estado": "error_procesamiento",
        "mensaje": "Error inesperado"
    }



st.title("Extractor Fiscal - Text-to-Structured-Data")
st.markdown("---")

st.markdown("""
###  Objetivo
Convertir textos desordenados en datos estructurados (JSON) para sistemas administrativos o fiscales.

###  Formatos soportados:
- Archivos de texto (.txt)
- Documentos Word (.docx)
- Hojas de cálculo Excel (.xlsx)
- PDF
""")

st.markdown("---")

st.subheader("Subir archivos")
st.caption(f"Demo: máx {MAX_ARCHIVOS} archivos por sesión, {MAX_SIZE_MB}MB por archivo")

archivos_subidos = st.file_uploader(
    "Arrastra o selecciona uno o más archivos",
    type=["txt", "docx", "xlsx", "pdf"],
    accept_multiple_files=True
)

st.markdown("---")

if archivos_subidos:
    # Validar cantidad
    if len(archivos_subidos) > MAX_ARCHIVOS:
        st.error(f"Máximo {MAX_ARCHIVOS} archivos por sesión")
        st.stop()

    # Validar tamaño
    for archivo in archivos_subidos:
        size_mb = archivo.size / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            st.error(f"{archivo.name} pesa {size_mb:.1f}MB (máx {MAX_SIZE_MB}MB)")
            st.stop()

    st.success(f"{len(archivos_subidos)} archivo(s) cargado(s)")

    if st.button("Procesar archivos", type="primary"):

        resultados = []
        archivos_sin_datos = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, archivo in enumerate(archivos_subidos):
            progreso = (i + 1) / len(archivos_subidos)
            progress_bar.progress(progreso)
            status_text.text(f"Procesando {i+1}/{len(archivos_subidos)}: {archivo.name}")

            resultado = procesar_archivo(archivo)

            if resultado["estado"] == "sin_datos":
                archivos_sin_datos += 1
            else:
                resultados.append({
                    "archivo": archivo.name,
                    "datos": resultado["datos"],
                    "estado": resultado["estado"],
                    "mensaje": resultado["mensaje"]
                })

        progress_bar.empty()
        status_text.empty()

        if archivos_sin_datos > 0:
            st.info(f"{archivos_sin_datos} archivo(s) sin información relevante")

        if resultados:
            st.markdown("---")
            st.subheader(" Resultados")

            for resultado in resultados:
                if resultado['estado'] == "exitoso":
                    with st.expander(f" {resultado['archivo']}", expanded=True):
                        st.json(resultado['datos'])
                else:
                    with st.expander(f" {resultado['archivo']}", expanded=False):
                        st.error(resultado['mensaje'])

            resultados_exitosos = [r for r in resultados if r['estado'] == 'exitoso']

            if resultados_exitosos:
                json_completo = {
                    "total_archivos_procesados": len(archivos_subidos),
                    "archivos_exitosos": len(resultados_exitosos),
                    "archivos_sin_datos": archivos_sin_datos,
                    "archivos_con_errores": len(resultados) - len(resultados_exitosos),
                    "resultados": resultados_exitosos
                }

                json_string = json.dumps(json_completo, indent=2, ensure_ascii=False)

                st.markdown("---")
                st.download_button(
                    label=" Descargar resultados (JSON)",
                    data=json_string,
                    file_name="resultados_extraccion.json",
                    mime="application/json"
                )
            else:
                st.warning(" No se pudieron extraer datos válidos")
        else:
            st.info(" no se encontraron datos relevantes en los archivos")

else:
    st.info(" Sube uno o más archivos para comenzar")

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p style='color: gray;'>Brandon Enrique Eroza Torres</p>
</div>
""", unsafe_allow_html=True)