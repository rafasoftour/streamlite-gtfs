import streamlit as st
from utils.gtfs_utils import load_gtfs_data, check_integrity, check_required_files
from utils.stops_utils import show_schedule_page, show_schedule_page2, show_routes_per_stop, show_routes_info_per_stop, show_routes_map_per_stop
from utils.services_utils import show_services_page
from utils.visualization import display_stops, display_calendar_and_dates, display_routes, display_route_map, display_route_directions, display_route_directions_map, display_route_directions_with_shapes
from utils.validation_utils import check_unused_shapes, check_trips_without_stop_times, check_invalid_stop_ids, check_stops_far_from_shapes
from utils.unused_shapes_utils import show_unused_shapes_page
from utils.debug_utils import show_route_shape_debug_page

st.set_page_config("Visor GTFS", layout="wide")

def main():
    # Subir archivo GTFS
    uploaded_file = st.sidebar.file_uploader("Sube un archivo GTFS", type=["zip"])
    if uploaded_file is not None:
        # Cargar los datos del archivo GTFS
        gtfs_data = load_gtfs_data(uploaded_file)
        show_gtfs_sidebar_and_content(gtfs_data)

def show_gtfs_sidebar_and_content(gtfs_data):
    """Mostrar el sidebar y gestionar el contenido dinámicamente"""
    # 🔹 Sidebar principal con opciones
    page = st.sidebar.selectbox(
        "Selecciona una página",
        ["Inicio", "Paradas", "Calendario", "Rutas", "Mapa de Rutas", "Horarios de paradas", "Rutas por parada", "Información de servicios", "Validaciones de Shapes",
        "Shapes no usados (fantasmas)", "Depuración de rutas"]  
    )

    if page == "Inicio":
        st.title("Bienvenido a la vista de GTFS")
        st.write("Selecciona una opción en el sidebar para ver más detalles.")
        st.divider()
        st.subheader("Resultados de chequeo:")
        check_integrity(gtfs_data)
        check_required_files(gtfs_data)

    elif page == "Paradas":
        display_stops(gtfs_data)

    elif page == "Calendario":
        display_calendar_and_dates(gtfs_data)

    elif page == "Rutas":
        display_routes(gtfs_data)

    elif page == "Mapa de Rutas":  # ✅ Nueva opción
        show_route_selector_page(gtfs_data)  # Llama a la función que mostrará el selector y el mapa

    elif page == "Horarios de paradas":
        show_schedule_page2(gtfs_data)   
        show_schedule_page(gtfs_data)    

    elif page == "Rutas por parada":
        # show_routes_per_stop(gtfs_data)           
        stop_name = show_routes_info_per_stop(gtfs_data)
        show_routes_map_per_stop(gtfs_data, stop_name)

    elif page == "Información de servicios":
        show_services_page(gtfs_data)   

    elif page == "Validaciones de Shapes":
        st.title("Validaciones relacionadas con Shapes y Trips")
        check_unused_shapes(gtfs_data)
        st.divider()
        check_trips_without_stop_times(gtfs_data) 
        st.divider()
        check_invalid_stop_ids(gtfs_data)
        st.divider()
        check_stops_far_from_shapes(gtfs_data)     

    elif page == "Shapes no usados (fantasmas)":
        show_unused_shapes_page(gtfs_data)

    elif page == "Depuración de rutas":
        show_route_shape_debug_page(gtfs_data)

def show_route_selector_page(gtfs_data):
    """Muestra la página con el selector de rutas y el mapa de la ruta seleccionada"""
    routes = gtfs_data.get("routes")

    if routes is None or routes.empty:
        st.warning("No se han encontrado datos de rutas en el GTFS.")
        return

    # 🔹 Crear el selector de rutas en el sidebar
    route_names = routes['route_long_name'].tolist()
    selected_route_name = st.sidebar.selectbox("Selecciona una ruta", route_names)

    # 🔹 Obtener el route_id de la ruta seleccionada
    selected_route_id = routes.loc[routes['route_long_name'] == selected_route_name, 'route_id'].values[0]

    # 🔹 Mostrar el mapa de la ruta seleccionada
    st.title(f"Mapa de la Ruta: {selected_route_name}")
    display_route_directions_with_shapes(gtfs_data, selected_route_id)


# 🔹 Punto de entrada de la aplicación
if __name__ == "__main__":
    main()
