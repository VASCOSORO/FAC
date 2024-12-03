import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Cargar el archivo CSV de productos
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
            # Buscar líneas que comiencen con un código (formato aproximado)
            if line[:2].isalpha() and '-' in line:
                codigo = line.split()[0]
                codigos.append(codigo.strip())
    return codigos

# Generar una imagen para el catálogo
def generar_imagen(codigo, nombre, precio, descripcion, url_imagen):
    try:
        # Descargar la imagen del producto
        response = requests.get(url_imagen)
        producto_img = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception:
        # Si falla la descarga, usar una imagen de error
        producto_img = Image.new("RGB", (300, 300), color=(255, 0, 0))

    # Crear el lienzo para el catálogo
    img = Image.new("RGB", (800, 400), "white")
    draw = ImageDraw.Draw(img)

    # Escribir los datos del producto
    font = ImageFont.load_default()
    draw.text((10, 10), f"Código: {codigo}", fill="black", font=font)
    draw.text((10, 30), f"Nombre: {nombre}", fill="black", font=font)
    draw.text((10, 50), f"Precio: ${precio}", fill="black", font=font)
    draw.text((10, 70), f"Descripción: {descripcion}", fill="black", font=font)

    # Insertar la imagen del producto
    producto_img = producto_img.resize((300, 300))
    img.paste(producto_img, (450, 50))

    return img

# App Streamlit
st.title("Generador de Catálogos desde Pedido PDF 📄")

# Subir archivo PDF
pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

# Subir archivo CSV
csv_file = st.file_uploader("Subir Archivo CSV de Productos", type=["csv"])

if pdf_file and csv_file:
    # Cargar datos
    st.info("Cargando datos del CSV...")
    df_productos = cargar_datos(csv_file)

    # Extraer códigos
    st.info("Extrayendo códigos del PDF...")
    codigos = extraer_codigos(pdf_file)

    if codigos:
        st.success(f"{len(codigos)} códigos extraídos con éxito.")

        # Filtrar los productos que coinciden con los códigos
        st.info("Filtrando productos en el catálogo...")
        catalogo = df_productos[df_productos['Codigo'].isin(codigos)]

        if not catalogo.empty:
            st.success(f"Se encontraron {len(catalogo)} productos en el catálogo.")

            # Generar imágenes para los productos seleccionados
            st.info("Generando catálogo...")
            
            cols = st.columns(3)  # Distribuir en 3 columnas por fila
            col_idx = 0
            for _, row in catalogo.iterrows():
                img = generar_imagen(
                    codigo=row['Codigo'],
                    nombre=row['Nombre'],
                    precio=row['Precio'],
                    descripcion=row['Descripcion'],
                    url_imagen=row['imagen'],
                )
                # Mostrar la imagen generada en una columna
                with cols[col_idx]:
                    st.image(img, caption=row['Nombre'], use_column_width=True)
                col_idx = (col_idx + 1) % 3  # Moverse a la siguiente columna

        else:
            st.error("No se encontraron productos que coincidan con los códigos extraídos.")
    else:
        st.error("No se pudieron extraer códigos válidos del PDF.")
