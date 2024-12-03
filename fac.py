import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Ruta del archivo CSV en el repositorio
CSV_FILE = "1804no.csv"
LOGO_FILE = "logomundo3.png"

# Función para cargar el archivo CSV
@st.cache
def cargar_csv():
    try:
        return pd.read_csv(CSV_FILE, sep=';', quotechar='"', encoding='latin1')
    except FileNotFoundError:
        st.error(f"No se encontró el archivo CSV '{CSV_FILE}'.")
        return pd.DataFrame()  # Devuelve un DataFrame vacío si no se encuentra el archivo

# Función para extraer códigos de productos desde un PDF
def extraer_codigos(pdf_file):
    reader = PdfReader(pdf_file)
    codigos = []
    for page in reader.pages:
        lines = page.extract_text().splitlines()
        for line in lines:
            if line[:2].isalpha() and '-' in line:  # Modificar si el formato varía
                codigo = line.split()[0]
                codigos.append(codigo.strip())
    return codigos

# Función para generar el catálogo
def generar_catalogo(productos, df_productos):
    if not productos:
        st.error("No se encontraron productos para generar el catálogo.")
        return

    layout = (len(productos) // 3 + (len(productos) % 3 > 0), 3)
    canvas_width, canvas_height = 900, layout[0] * 400
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_text = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    item_width = canvas_width // layout[1]
    item_height = canvas_height // layout[0]

    for i, codigo in enumerate(productos):
        producto = df_productos[df_productos['Codigo'] == codigo].iloc[0]
        row, col = divmod(i, layout[1])
        x, y = col * item_width, row * item_height

        try:
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                response = requests.get(producto['imagen'], timeout=5)
                img = Image.open(BytesIO(response.content))
                img.thumbnail((item_width - 20, item_height - 100))
                canvas.paste(img, (x + 10, y + 10))
        except Exception as e:
            st.error(f"Error al cargar la imagen para el producto {codigo}: {e}")

        draw.text((x + 10, y + item_height - 80), f"Código: {producto['Codigo']}", fill="black", font=font_text)
        draw.text((x + 10, y + item_height - 60), f"Nombre: {producto['Nombre'][:30]}...", fill="black", font=font_text)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    st.image(canvas, caption="Catálogo Generado", use_column_width=True)
    st.download_button("Descargar Catálogo", data=buffer, file_name="catalogo.png", mime="image/png")

# Streamlit App
st.set_page_config(page_title="Generador de Catálogos", page_icon="📄", layout="wide")
st.title("")

# Mostrar el logo en el centro superior
try:
    logo = Image.open(LOGO_FILE)
    st.image(logo, use_column_width=False, width=200)
except FileNotFoundError:
    st.error(f"No se encontró el logo '{LOGO_FILE}'. Asegúrate de que esté en el directorio del repositorio.")

st.title("Generador de Catálogos desde PDF 📄")

# Cargar datos del CSV
df_productos = cargar_csv()

if not df_productos.empty:
    # Subir archivo PDF
    pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

    if pdf_file:
        codigos = extraer_codigos(pdf_file)
        if codigos:
            productos_seleccionados = df_productos[df_productos['Codigo'].isin(codigos)]['Codigo'].tolist()
            if productos_seleccionados:
                generar_catalogo(productos_seleccionados, df_productos)
            else:
                st.error("No se encontraron productos en el CSV para los códigos extraídos.")
        else:
            st.error("No se pudieron extraer códigos válidos del PDF.")

# Sección oculta para actualizar el archivo CSV
with st.expander("⚙️ Opciones Avanzadas", expanded=False):
    if st.checkbox("Mostrar opciones avanzadas"):
        st.info("Esta sección permite actualizar el archivo CSV del repositorio.")

        # Solicitar contraseña
        contraseña = st.text_input("Ingrese la contraseña para acceder:", type="password")
        if contraseña == "Rosebud":
            nuevo_csv = st.file_uploader("Subir un nuevo archivo CSV", type=["csv"])
            if nuevo_csv:
                with open(CSV_FILE, "wb") as f:
                    f.write(nuevo_csv.getbuffer())
                st.success("Archivo CSV actualizado exitosamente. Recarga la página para aplicar los cambios.")
        elif contraseña:
            st.error("Contraseña incorrecta.")
