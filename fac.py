import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from PIL import Image
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

# Streamlit App
st.set_page_config(page_title="Generador de Catálogos", page_icon="📄", layout="wide")

# CSS para centrar el logo
st.markdown(
    """
    <style>
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .block-container {
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

# Título centrado
st.title("Generador de Catálogos desde PDF 📄")

# Cargar datos del CSV
df_productos = cargar_csv()

if not df_productos.empty:
    # Subir archivo PDF
    st.subheader("Subir PDF de Pedido")
    pdf_file = st.file_uploader("Subir PDF de Pedido", type=["pdf"])

    if pdf_file:
        st.success("¡Archivo PDF cargado con éxito!")
        # Aquí se puede implementar la lógica de extracción y generación de catálogos

# Footer fino
st.markdown(
    """
    <footer>
        Powered by Vasco.Soro
    </footer>
    """,
    unsafe_allow_html=True,
)
