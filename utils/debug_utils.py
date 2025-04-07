import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from shapely.geometry import LineString

def show_route_shape_debug_page(gtfs_data):
    st.title("🧪 Depuración visual de rutas y shapes")

    routes_df = gtfs_data.get("routes")
    trips_df = gtfs_data.get("trips")
    shapes_df = gtfs_data.get("shapes")
    stop_times_df = gtfs_data.get("stop_times")

    if any(df is None for df in (routes_df, trips_df, shapes_df, stop_times_df)):
        st.error("Faltan datos necesarios (routes, trips, shapes o stop_times).")
        return

    # 🔹 Selector por nombre de ruta
    route_names = routes_df["route_long_name"].dropna().unique().tolist()
    selected_route_name = st.sidebar.selectbox("Selecciona una ruta por nombre", route_names)

    selected_route_id = routes_df[routes_df["route_long_name"] == selected_route_name]["route_id"].values[0]
    st.markdown(f"**route_id seleccionado:** `{selected_route_id}`")

    # 🔸 Filtrar trips para esa ruta
    trips_for_route = trips_df[trips_df["route_id"] == selected_route_id].copy()

    if trips_for_route.empty:
        st.warning("No hay trips asociados a esta ruta.")
        return

    # Comprobar qué trips tienen stop_times
    trip_ids_with_stops = stop_times_df["trip_id"].unique()
    trips_for_route["has_stops"] = trips_for_route["trip_id"].isin(trip_ids_with_stops)

    # Mostrar tabla
    st.subheader("🎫 Trips asociados")
    st.dataframe(trips_for_route[["trip_id", "shape_id", "has_stops"]])

    # Mapa con los shapes
    st.subheader("🗺 Shapes asociados a los trips")

    all_latlons = []

    m = folium.Map(location=[40.4168, -3.7038], zoom_start=7)

    for _, trip in trips_for_route.iterrows():
        shape_id = trip["shape_id"]
        if pd.isna(shape_id):
            continue

        shape_points = shapes_df[shapes_df["shape_id"] == shape_id].sort_values("shape_pt_sequence")
        latlons = list(zip(shape_points["shape_pt_lat"], shape_points["shape_pt_lon"]))
        color = "green" if trip["has_stops"] else "red"

        if len(latlons) > 1:
            folium.PolyLine(
                latlons,
                color=color,
                weight=3,
                tooltip=f"trip_id: {trip['trip_id']} ({'✅' if trip['has_stops'] else '❌'})"
            ).add_to(m)
            all_latlons.extend(latlons)

    # 🔍 Ajustar vista si hay puntos
    if all_latlons:
        m.fit_bounds([[min(lat for lat, lon in all_latlons), min(lon for lat, lon in all_latlons)],
                      [max(lat for lat, lon in all_latlons), max(lon for lat, lon in all_latlons)]])

    st_folium(m, width=2000, height=600)
