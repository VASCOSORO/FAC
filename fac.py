import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO


# Función para cargar el archivo CSV de productos
@st.cache
def cargar_datos(csv_file):
    return pd.read_csv(csv_file, sep=';', quotechar='"', encoding='latin1')

# Extraer códigos de productos desde el PDF
def extraer_codigos(pdf_file):
    reader = PdfReader(pdf_file)
    codigos = []
    for page in reader.pages:
        lines = page.extract_text().splitlines()
        for line in lines:
            # Buscar líneas que comiencen con un código (modificar si el formato varía)
            if line[:2].isalpha() and '-' in line:
                codigo = line.split()[0]
                codigos.append(codigo.strip())
    return codigos

# Función para calcular la distribución del layout
def calcular_layout(n):
    if n == 1:
        return (1, 1)
    elif n == 2:
        return (2, 1)
    elif n <= 4:
        return (2, 2)
    elif n <= 6:
        return (2, 3)
    else:
        return ((n // 3) + (n % 3 > 0), 3)  # Máximo 3 columnas

# Generar las imágenes del catálogo
def generar_catalogo(productos, df_productos):
    if not productos:
        st.error("No se encontraron productos para generar el catálogo.")
        return

    # Crear un canvas para cada grupo de productos
    layout = calcular_layout(len(productos))
    canvas_width, canvas_height = 900, layout[0] * 400
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    # Cargar fuentes
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

        # Descargar imagen
        try:
            if pd.notna(producto['imagen']) and producto['imagen'] != '':
                response = requests.get(producto['imagen'], timeout=5)
                img = Image.open(BytesIO(response.content))
                img.thumbnail((item_width - 20, item_height - 100))
                canvas.paste(img, (x + 10, y + 10))
        except Exception as e:
            st.error(f"Error al cargar la imagen para el producto {codigo}: {e}")

        # Agregar texto (código y nombre)
        draw.text((x + 10, y + item_height - 80), f"Código: {producto['Codigo']}", fill="black", font=font_text)
        draw.text((x + 10, y + item_height - 60), f"Nombre: {producto['Nombre'][:30]}...", fill="black", font=font_text)

    # Mostrar y descargar el catálogo generado
    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    st.image(canvas, caption="Catálogo Generado", use_column_width=True)
    st.download_button("Descargar Catálogo", data=buffer, file_name="catalogo.png", mime="image/png")

# Streamlit App
st.title("Generador de Catálogos desde PDF 📄")

# Subir archivos
csv_file = st.file_uploader("Subir Archivo CSV de Productos", type=["csv"])
pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

if csv_file and pdf_file:
    st.info("Cargando datos del CSV...")
    df_productos = cargar_datos(csv_file)

    st.info("Extrayendo códigos del PDF...")
    codigos = extraer_codigos(pdf_file)

    if codigos:
        st.success(f"Se extrajeron {len(codigos)} códigos del PDF.")
        productos_seleccionados = df_productos[df_productos['Codigo'].isin(codigos)]['Codigo'].tolist()

        if productos_seleccionados:
            st.success(f"Se encontraron {len(productos_seleccionados)} productos en el CSV.")
            generar_catalogo(productos_seleccionados, df_productos)
        else:
            st.error("No se encontraron coincidencias entre los códigos del PDF y el CSV.")
    else:
        st.error("No se pudieron extraer códigos válidos del PDF.")
