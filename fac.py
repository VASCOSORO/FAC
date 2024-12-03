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
    codigos = []
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            lines = page.extract_text().splitlines()
            for line in lines:
                if line[:2].isalpha() and '-' in line:  # Modificar si el formato varía
                    codigo = line.split()[0]
                    codigos.append(codigo.strip())
        if not codigos:
            st.warning("No se encontraron códigos válidos en el PDF.")
    except Exception as e:
        st.error(f"Error al procesar el PDF: {e}")
    return codigos

# Función para generar imágenes individuales de productos
def generar_catalogo(productos, df_productos):
    if not productos:
        st.error("No se encontraron productos para generar el catálogo.")
        return

    for codigo in productos:
        producto = df_productos[df_productos['Codigo'] == codigo].iloc[0]

        # Crear una imagen individual para cada producto
        canvas_width, canvas_height = 400, 600
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)

        try:
            font_title = ImageFont.truetype("arial.ttf", 20)
            font_text = ImageFont.truetype("arial.ttf", 14)
        except IOError:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        try:
            # Descargar la imagen del producto
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                response = requests.get(producto['imagen'], timeout=5)
                img = Image.open(BytesIO(response.content))
                img.thumbnail((canvas_width - 20, canvas_height - 200))
                canvas.paste(img, (10, 10))
        except Exception as e:
            st.error(f"Error al cargar la imagen para el producto {codigo}: {e}")

        # Agregar texto del producto
        draw.text((10, canvas_height - 180), f"Código: {producto['Codigo']}", fill="black", font=font_text)
        draw.text((10, canvas_height - 150), f"Nombre: {producto['Nombre'][:30]}...", fill="black", font=font_text)

        # Guardar la imagen en un buffer
        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)

        # Mostrar y permitir descarga de la imagen individual
        st.image(canvas, caption=f"Producto: {producto['Nombre']}", use_column_width=False)
        st.download_button(
            label=f"Descargar {producto['Codigo']}",
            data=buffer,
            file_name=f"{producto['Codigo']}.png",
            mime="image/png",
        )

# Streamlit App
st.set_page_config(page_title="Generador de Catálogos", page_icon="📄", layout="wide")

# CSS para centrar todo el contenido
st.markdown(
    """
    <style>
        .block-container {
            text-align: center;
        }
        img {
            margin-bottom: 20px;
        }
        h1, h2, h3, h4, h5, h6 {
            text-align: center;
        }
        .css-1aumxhk {
            justify-content: center;
        }
        footer {
            font-size: 0.75em;
            text-align: center;
            color: gray;
            margin-top: 50px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Mostrar el logo centrado
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
try:
    logo = Image.open(LOGO_FILE)
    st.image(logo, use_column_width=False, width=250)
except FileNotFoundError:
    st.error(f"No se encontró el logo '{LOGO_FILE}'. Asegúrate de que esté en el directorio del repositorio.")
st.markdown('</div>', unsafe_allow_html=True)

st.title("Generador de Catálogos desde PDF 📄")

# Cargar datos del CSV
df_productos = cargar_csv()

if not df_productos.empty:
    # Subir archivo PDF
    st.subheader("Subir PDF de Pedido")
    pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

    if pdf_file:
        st.success("¡Archivo PDF cargado con éxito!")
        codigos = extraer_codigos(pdf_file)

        if codigos:
            productos_seleccionados = df_productos[df_productos['Codigo'].isin(codigos)]['Codigo'].tolist()
            if productos_seleccionados:
                st.success(f"Se encontraron {len(productos_seleccionados)} productos en el CSV.")
                generar_catalogo(productos_seleccionados, df_productos)
            else:
                st.warning("No se encontraron productos en el CSV que coincidan con los códigos del PDF.")
        else:
            st.warning("No se extrajeron códigos válidos del PDF.")

# Footer fino
st.markdown(
    """
    <footer>
        Powered by Vasco.Soro
    </footer>
    """,
    unsafe_allow_html=True,
)
