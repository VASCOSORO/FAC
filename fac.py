import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import zipfile

# Ruta del archivo CSV en el repositorio
CSV_FILE = "1804no.csv"
LOGO_FILE = "logomundo3.png"

# Función para cargar el archivo CSV
@st.cache
def cargar_csv():
    try:
        return pd.read_csv(CSV_FILE, sep=';', quotechar='"', encoding='utf-8')
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

# Función para generar el catálogo visual en páginas tipo A4
def generar_catalogo_visual(productos, df_productos, incluir_datos=True):
    a4_width, a4_height = 1240, 1754  # Tamaño reducido para visualización tipo A4
    max_items_per_page = 6
    paginas = [productos[i:i + max_items_per_page] for i in range(0, len(productos), max_items_per_page)]
    catalogo_buffers = []

    for pagina in paginas:
        canvas = Image.new("RGB", (a4_width, a4_height), "white")
        draw = ImageDraw.Draw(canvas)

        # Fuentes
        try:
            font_title = ImageFont.truetype("arial.ttf", 28)
            font_text = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        x_offset, y_offset = 20, 20
        col_width, row_height = a4_width // 3, a4_height // 2

        for i, codigo in enumerate(pagina):
            producto = df_productos[df_productos['Codigo'] == codigo].iloc[0]
            col, row = i % 3, i // 3
            x, y = col * col_width + x_offset, row * row_height + y_offset

            # Descargar y posicionar la imagen
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                try:
                    response = requests.get(producto['imagen'], timeout=5)
                    img = Image.open(BytesIO(response.content))
                    img.thumbnail((col_width - 40, row_height - 100))
                    canvas.paste(img, (x + 20, y + 20))
                except Exception as e:
                    st.warning(f"No se pudo cargar la imagen del producto {codigo}.")

            # Agregar datos
            if incluir_datos:
                draw.text((x + 20, y + row_height - 70), f"Código: {producto['Codigo']}", fill="black", font=font_text)
                draw.text((x + 20, y + row_height - 40), f"Nombre: {producto['Nombre'][:30]}...", fill="black", font=font_text)

        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        catalogo_buffers.append(buffer)

    return catalogo_buffers

# Función para generar un archivo ZIP con las imágenes del pedido
def generar_zip_imagenes(productos, df_productos):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for codigo in productos:
            producto = df_productos[df_productos['Codigo'] == codigo].iloc[0]
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                try:
                    response = requests.get(producto['imagen'], timeout=5)
                    img = Image.open(BytesIO(response.content))
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG")
                    img_buffer.seek(0)
                    zip_file.writestr(f"{codigo}.png", img_buffer.read())
                except Exception as e:
                    st.warning(f"No se pudo incluir la imagen del producto {codigo} en el ZIP.")
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit App
st.set_page_config(page_title="Generador de Catálogos", page_icon="📄", layout="wide")

# CSS para centrar contenido
st.markdown(
    """
    <style>
        .block-container {
            text-align: center;
        }
        footer {
            font-size: 0.8em;
            text-align: center;
            color: gray;
            margin-top: 50px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Logo
try:
    logo = Image.open(LOGO_FILE)
    st.image(logo, use_column_width=False, width=200)
except FileNotFoundError:
    st.error(f"No se encontró el logo '{LOGO_FILE}'.")

st.title("Generador de Catálogos desde PDF 📄")

# Cargar CSV
df_productos = cargar_csv()

if not df_productos.empty:
    pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

    if pdf_file:
        codigos = extraer_codigos(pdf_file)
        if codigos:
            productos_seleccionados = df_productos[df_productos['Codigo'].isin(codigos)]['Codigo'].tolist()
            if productos_seleccionados:
                incluir_datos = st.radio("¿Incluir datos en el catálogo?", ["Sí", "No"]) == "Sí"
                catalogo_buffers = generar_catalogo_visual(productos_seleccionados, df_productos, incluir_datos)

                # Mostrar el catálogo
                for idx, buffer in enumerate(catalogo_buffers):
                    st.image(buffer, caption=f"Página {idx + 1}", use_column_width=True)

                # Descargar todo el catálogo
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for idx, buffer in enumerate(catalogo_buffers):
                        buffer.seek(0)
                        zip_file.writestr(f"pagina_{idx + 1}.png", buffer.read())
                zip_buffer.seek(0)
                st.download_button(
                    label="Descargar Catálogo Completo (ZIP)",
                    data=zip_buffer,
                    file_name="catalogo_completo.zip",
                    mime="application/zip",
                )

                # Descargar imágenes individuales
                st.download_button(
                    label="Descargar Todas las Imágenes (ZIP)",
                    data=generar_zip_imagenes(productos_seleccionados, df_productos),
                    file_name="imagenes_pedido.zip",
                    mime="application/zip",
                )
            else:
                st.warning("No se encontraron productos en el CSV que coincidan con los códigos del PDF.")
        else:
            st.warning("No se extrajeron códigos válidos del PDF.")

# Footer
st.markdown("<footer>Powered by Vasco.Soro</footer>", unsafe_allow_html=True)
