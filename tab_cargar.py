import streamlit as st
import gtfs_kit as gk

def cargar_gtfs():
    st.subheader("Sube un archivo GTFS (.zip)")

    gtfs_file = st.file_uploader("Selecciona un archivo", type=["zip"])

    if gtfs_file:
        with open("temp_gtfs.zip", "wb") as f:
            f.write(gtfs_file.getbuffer())

        try:
            # Cargar el archivo con gtfs_kit
            feed = gk.read_feed("temp_gtfs.zip", dist_units="km")

            # Verificar que los datos se cargaron correctamente
            if feed is not None and not feed.routes.empty:
                st.success("El archivo GTFS es válido y ha sido cargado correctamente.")
                st.session_state["feed"] = feed
            else:
                st.error("El archivo GTFS no contiene datos válidos.")

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
