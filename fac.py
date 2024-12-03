import os
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import tempfile
import requests

# Asegurarse de instalar PyPDF2 si no está instalado
try:
    from PyPDF2 import PdfReader
except ModuleNotFoundError:
    os.system('pip install PyPDF2')
    from PyPDF2 import PdfReader

def modulo_marketing():
    st.header("📢 Marketing y Gestión de Productos 🎈")

    # Sección para cargar un archivo Excel que actualice el DataFrame de productos
    with st.expander("🔄 Actualizar Productos desde Excel", expanded=False):
        archivo_productos = st.file_uploader("Cargar archivo Excel de Productos", type=["xlsx"])

        if archivo_productos is not None:
            try:
                # Leer el archivo Excel cargado
                df_nuevo = pd.read_excel(archivo_productos)

                # Asegurarse de que las columnas necesarias existan
                columnas_necesarias = [
                    'id', 'Codigo', 'Nombre', 'Activo', 'Fecha Creado', 'Fecha Modificado',
                    'Descripcion', 'Orden', 'Codigo de Barras', 'unidad por bulto',
                    'Presentacion/paquete', 'forzar venta x cantidad', 'Costo (Pesos)',
                    'Costo (USD)', 'Etiquetas', 'Stock', 'StockSuc2', 'Proveedor',
                    'Categorias', 'Precio x Mayor', 'Precio Venta', 'Precio x Menor',
                    'Pasillo', 'Estante', 'Columna', 'Fecha de Vencimiento', 'imagen'
                ]

                for columna in columnas_necesarias:
                    if columna not in df_nuevo.columns:
                        df_nuevo[columna] = None  # Agregar columna faltante con valores vacíos

                # Actualizar el DataFrame de productos en el estado de sesión
                st.session_state.df_productos = df_nuevo

                # Guardar automáticamente en archivo Excel para futuras sesiones
                df_nuevo.to_excel('archivo_modificado_productos.xlsx', index=False)

                # Mostrar confirmación de la carga
                st.success("Datos de productos actualizados y guardados exitosamente.")
                st.write(f"Fecha de última modificación: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                st.error(f"Error al cargar el archivo de productos: {e}")
        elif 'df_productos' not in st.session_state:
            # Si no se cargó un archivo y no existe el DataFrame, intentar cargar desde el archivo guardado
            try:
                st.session_state.df_productos = pd.read_excel('archivo_modificado_productos.xlsx')
                st.success("Datos de productos cargados desde archivo previamente guardado.")
            except FileNotFoundError:
                st.error("No se encontró un archivo previo de productos. Por favor, cargue un archivo Excel.")

    # Verificar si la columna 'id' existe en el DataFrame; si no, crearla con IDs únicos
    if 'id' not in st.session_state.df_productos.columns:
        st.session_state.df_productos['id'] = range(1, len(st.session_state.df_productos) + 1)

    # Asegurarse de que las columnas 'Costo (Pesos)' y 'Costo (USD)' existan en el DataFrame
    if 'Costo (Pesos)' not in st.session_state.df_productos.columns:
        st.session_state.df_productos['Costo (Pesos)'] = 0.0
    if 'Costo (USD)' not in st.session_state.df_productos.columns:
        st.session_state.df_productos['Costo (USD)'] = 0.0

    # Extraer categorías únicas para el desplegable
    categorias_series = st.session_state.df_productos['Categorias'].dropna()
    categorias_unicas = set()
    for categorias in categorias_series:
        categorias_list = [categoria.strip() for categoria in categorias.split(',')]
        categorias_unicas.update(categorias_list)
    categorias_unicas = sorted(list(categorias_unicas))

    # Parte 4: Crear Imágenes
    with st.expander("🤓 Crear Imagen con Productos Seleccionados 📄", expanded=False):
        productos_seleccionados = st.multiselect("Seleccionar productos para la Imagen", 
                                                 st.session_state.df_productos['Codigo'].unique())
        # Limitar selección a 6 productos
        if len(productos_seleccionados) > 6:
            st.error("Solo puedes seleccionar hasta 6 productos para la imagen.")
        elif len(productos_seleccionados) > 0:
            # Centrar los botones en la pantalla
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Generar Imagen PNG"):
                    generar_imagenes_png(productos_seleccionados)

    # Botón para descargar la imagen generada
    if 'imagenes_generadas' in st.session_state:
        if len(st.session_state['imagenes_generadas']) > 0:
            with st.container():
                st.download_button(label="Descargar Imagen Generada",
                                   data=st.session_state['imagenes_generadas'][0],
                                   file_name=f"imagen_productos.png",
                                   mime="image/png")

    st.markdown("---")

    # Parte 5: Subir PDF de pedidos y generar catálogos
    with st.expander("📂 Subir PDF de Pedido para Generar Catálogo 📏", expanded=False):
        pdf_pedido = st.file_uploader("Subir PDF de Pedido", type=["pdf"])
        if pdf_pedido is not None:
            productos_en_pedido = extraer_productos_de_pdf(pdf_pedido)
            productos_en_pedido = [codigo.strip().upper() for codigo in productos_en_pedido if codigo.strip()]
            if productos_en_pedido:
                st.success("Productos extraídos del PDF correctamente.")
                if st.button("Generar Catálogo desde PDF"):
                    generar_imagenes_png_por_codigo(productos_en_pedido)
            else:
                st.error("No se pudieron extraer productos válidos del PDF. Verifica el formato.")

    st.markdown("---")

