import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def show_unused_shapes_page(gtfs_data):
    st.title("🔍 Shapes no usados (posibles fantasmas)")

    shapes_df = gtfs_data.get("shapes")
    trips_df = gtfs_data.get("trips")

    if shapes_df is None or trips_df is None:
        st.warning("Faltan shapes.txt o trips.txt.")
        return

    used_shape_ids = set(trips_df["shape_id"].dropna().unique())
    all_shape_ids = set(shapes_df["shape_id"].unique())
    unused_shape_ids = sorted(all_shape_ids - used_shape_ids)

    if not unused_shape_ids:
        st.success("✅ Todos los shapes están en uso por algún trip.")
        return

    st.warning(f"⚠️ Hay {len(unused_shape_ids)} shapes que no están referenciados en ningún trip.")
    st.dataframe(pd.DataFrame({"shape_id_no_usado": unused_shape_ids}))

    # Mostrar en mapa
    st.subheader("🗺 Vista en mapa de los shapes no usados")

    m = folium.Map(location=[40.4168, -3.7038], zoom_start=6)  # Centrado en España

    for shape_id in unused_shape_ids:
        shape_points = shapes_df[shapes_df["shape_id"] == shape_id]
        shape_points = shape_points.sort_values("shape_pt_sequence")
        latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))

        if len(latlons) > 1:
            folium.PolyLine(latlons, color="red", weight=3, tooltip=f"shape_id: {shape_id}").add_to(m)

    st_folium(m, width=700, height=500)
