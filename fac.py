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

# Función para calcular el layout por cantidad de imágenes
def calcular_layout(n):
    if n == 1:
        return [(3, 1)]  # Una imagen al centro
    elif n == 2:
        return [(2, 1), (2, 1)]  # Dos imágenes en una columna
    elif n == 3:
        return [(3, 1), (3, 1), (1, 1)]  # Una imagen centrada abajo
    elif n == 4:
        return [(2, 2)]  # Cuatro imágenes en dos filas
    elif n == 5:
        return [(2, 2), (1, 1)]  # Cuatro en cuadrado + una centrada
    elif n >= 6:
        return [(2, 3)]  # Seis imágenes distribuidas uniformemente
    return []

# Función para generar el catálogo visual en páginas tipo A4
def generar_catalogo_visual(productos, df_productos, incluir_datos=True):
    a4_width, a4_height = 2480, 3508  # Tamaño en píxeles para A4 (300 dpi)
    max_items_per_page = 6
    paginas = [productos[i:i + max_items_per_page] for i in range(0, len(productos), max_items_per_page)]
    buffer = BytesIO()

    # Crear un catálogo multipágina
    for idx, pagina in enumerate(paginas):
        canvas = Image.new("RGB", (a4_width, a4_height), "white")
        draw = ImageDraw.Draw(canvas)

        # Cargar fuentes
        try:
            font_title = ImageFont.truetype("arial.ttf", 40)
            font_text = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()

        layout = calcular_layout(len(pagina))
        for i, codigo in enumerate(pagina):
            producto = df_productos[df_productos['Codigo'] == codigo].iloc[0]
            row, col = divmod(i, 3)  # Distribuir en filas y columnas
            item_width, item_height = a4_width // 3, a4_height // 2
            x, y = col * item_width, row * item_height

            # Descargar y posicionar la imagen
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                try:
                    response = requests.get(producto['imagen'], timeout=5)
                    img = Image.open(BytesIO(response.content))
                    img.thumbnail((item_width - 50, item_height - 150))
                    canvas.paste(img, (x + 25, y + 25))
                except Exception as e:
                    st.warning(f"No se pudo cargar la imagen del producto {codigo}.")

            # Agregar datos si están habilitados
            if incluir_datos:
                draw.text((x + 25, y + item_height - 100), f"Código: {producto['Codigo']}", fill="black", font=font_text)
                draw.text((x + 25, y + item_height - 50), f"Nombre: {producto['Nombre'][:30]}...", fill="black", font=font_text)

        # Guardar la página en el buffer
        pagina_buffer = BytesIO()
        canvas.save(pagina_buffer, format="PNG")
        pagina_buffer.seek(0)
        buffer.write(pagina_buffer.read())

    buffer.seek(0)
    return buffer

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

                # Elegir si incluir datos o no
                incluir_datos = st.radio("¿Incluir datos en el catálogo?", ["Sí", "No"]) == "Sí"

                # Generar catálogo visual
                buffer = generar_catalogo_visual(productos_seleccionados, df_productos, incluir_datos)
                st.image(buffer, caption="Catálogo Visual Generado", use_column_width=True)

                # Botón para descargar catálogo completo
                st.download_button(
                    label="Descargar Catálogo Completo",
                    data=buffer,
                    file_name="catalogo_completo.png",
                    mime="image/png",
                )
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
