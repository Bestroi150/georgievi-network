import streamlit as st
import networkx as nx
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import numpy as np

def show_geographical_network(data):
    """
    Creates and displays a geographical network analysis showing places as nodes
    connected by communication flows (letters).
    
    Nodes: Places mentioned or letter origins/destinations
    Edges: Letters or trade routes connecting them
    Visualization: Map with arcs showing communication/trade flows
    """
    
    st.subheader("Географска мрежа (Мрежа на места)")
    st.markdown("""
    **Възли (Nodes):** Места споменати в писмата или произход/дестинация на писма  
    **Връзки (Edges):** Писма или търговски маршрути, свързващи местата  
    **Визуализация:** Карта с дъги, показващи комуникационни или търговски потоци
    """)
    
    # Extract place connections from the data
    place_connections, place_coordinates, place_info = extract_place_connections(data)
    
    if not place_connections:
        st.warning("Няма достатъчно данни за създаване на географска мрежа.")
        return
    
    # Create tabs for different views
    map_tab, network_tab, stats_tab = st.tabs(["🗺️ Карта с дъги", "🕸️ Мрежова диаграма", "📊 Статистика"])
    
    with map_tab:
        show_geographical_map(place_connections, place_coordinates, place_info)
    
    with network_tab:
        show_network_diagram(place_connections, place_coordinates, place_info)
    
    with stats_tab:
        show_geographical_statistics(place_connections, place_coordinates, place_info, data)

def extract_place_connections(data):
    """
    Extract place-to-place connections from the correspondence data.
    Returns place connections, coordinates, and additional place information.
    """
    place_connections = Counter()
    place_coordinates = {}
    place_info = {}
    
    # Track all places mentioned in letters
    all_places = set()
    
    for entry in data:
        sender_place = entry.get('sender_place')
        addressee_place = entry.get('addressee_place')
        mentioned_places = entry.get('mentioned_places', [])
        
        # Add places to our tracking
        current_letter_places = []
        
        # Add sender and addressee places
        if sender_place:
            all_places.add(sender_place)
            current_letter_places.append(sender_place)
            
        if addressee_place:
            all_places.add(addressee_place)
            current_letter_places.append(addressee_place)
        
        # Add mentioned places with coordinates
        for place in mentioned_places:
            if place['name']:
                all_places.add(place['name'])
                current_letter_places.append(place['name'])
                
                # Store coordinates if available
                if place['latitude'] is not None and place['longitude'] is not None:
                    place_coordinates[place['name']] = {
                        'lat': place['latitude'],
                        'lon': place['longitude'],
                        'ref': place.get('ref', '')
                    }
        
        # Create connections between places mentioned in the same letter
        # This represents communication/trade routes
        for i, place1 in enumerate(current_letter_places):
            for j, place2 in enumerate(current_letter_places):
                if i < j and place1 != place2:  # Avoid self-connections and duplicates
                    place_connections[(place1, place2)] += 1
        
        # Special handling for sender -> addressee connections (direct communication)
        if sender_place and addressee_place and sender_place != addressee_place:
            place_connections[(sender_place, addressee_place)] += 2  # Weight direct communication higher
    
    for place in all_places:
        if place not in place_info:
            place_info[place] = {
                'total_mentions': sum(1 for entry in data 
                                    if (entry.get('sender_place') == place or 
                                        entry.get('addressee_place') == place or
                                        any(p['name'] == place for p in entry.get('mentioned_places', [])))),
                'as_sender': sum(1 for entry in data if entry.get('sender_place') == place),
                'as_addressee': sum(1 for entry in data if entry.get('addressee_place') == place),
                'mentioned': sum(1 for entry in data 
                               if any(p['name'] == place for p in entry.get('mentioned_places', [])))
            }
    
    return place_connections, place_coordinates, place_info

def show_geographical_map(place_connections, place_coordinates, place_info):
    """
    Display an interactive map showing place connections with arcs.
    """
    st.subheader("Интерактивна карта с географски връзки")
    
    if not place_coordinates:
        st.warning("Няма места с координати за показване на картата.")
        return
    
    # Create base map
    lats = [coords['lat'] for coords in place_coordinates.values()]
    lons = [coords['lon'] for coords in place_coordinates.values()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Map display options in sidebar
    with st.sidebar:
        st.subheader("🗺️ Настройки на картата")
        map_height = st.slider("Височина на картата", 500, 1200, 800, 50)
        # Force fullscreen mode - always enabled
        show_fullscreen = True
        st.info("🖥️ Картата винаги се показва в пълноекранен режим")
        connection_threshold = st.slider(
            "Минимален брой връзки:", 
            1, 
            max(place_connections.values()) if place_connections else 5, 
            1
        )
    
    # Create the map with better settings for full screen
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=6, 
        prefer_canvas=True,
        tiles=None  # We'll add custom tiles
    )
    
    # Add tile layers
    folium.TileLayer('openstreetmap', name='OpenStreetMap', control=True).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Topographic',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add fullscreen button
    from folium.plugins import Fullscreen
    Fullscreen(
        position="topright",
        title="Пълен екран",
        title_cancel="Изход от пълен екран",
        force_separate_button=True,
    ).add_to(m)
    
    # Add markers for places
    for place, coords in place_coordinates.items():
        info = place_info.get(place, {})
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 10px 0; color: #2E86AB;">{place}</h4>
            <p style="margin: 5px 0;"><b>Общо споменавания:</b> {info.get('total_mentions', 0)}</p>
            <p style="margin: 5px 0;"><b>Като изпращач:</b> {info.get('as_sender', 0)}</p>
            <p style="margin: 5px 0;"><b>Като получател:</b> {info.get('as_addressee', 0)}</p>
            <p style="margin: 5px 0;"><b>Споменато в писма:</b> {info.get('mentioned', 0)}</p>
        </div>
        """
        
        folium.Marker(
            location=[coords['lat'], coords['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=place,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Add connection lines
    for (place1, place2), weight in place_connections.items():
        if weight >= connection_threshold:
            if place1 in place_coordinates and place2 in place_coordinates:
                coords1 = place_coordinates[place1]
                coords2 = place_coordinates[place2]
                
                # Create arc between places
                folium.PolyLine(
                    locations=[[coords1['lat'], coords1['lon']], 
                             [coords2['lat'], coords2['lon']]],
                    color='red',
                    weight=min(weight, 10),  # Cap line width
                    opacity=0.7,
                    popup=f"{place1} ↔ {place2}<br>Връзки: {weight}"
                ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    # Display the map - always use full width when fullscreen is enabled
    if show_fullscreen:
        # Create a custom container with enhanced full width
        map_html = m._repr_html_()
        
        # Enhanced CSS to make the map truly full screen
        full_width_style = f"""
        <style>
        .stApp > div:first-child {{
            padding-top: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }}
        .main .block-container {{
            padding-top: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
            max-width: 100%;
        }}
        iframe {{
            width: 100vw !important;
            height: {map_height}px !important;
            border: none;
            margin: 0;
            padding: 0;
        }}
        body {{
            margin: 0;
            padding: 0;
        }}
        </style>
        <div style="width: 100vw; height: {map_height}px; margin: 0; padding: 0; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;">
        """
        
        # Display using components.html for true full width
        import streamlit.components.v1 as components
        st.markdown("### 🗺️ Пълноекранна карта на всички споменати места")
        components.html(
            full_width_style + map_html + "</div>", 
            height=map_height + 50,
            scrolling=False
        )
    else:
        # Standard size
        st_folium(
            m, 
            width=900, 
            height=map_height, 
            returned_objects=["last_object_clicked"]
        )
    
    # Legend
    st.markdown("### Легенда:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🔵 Сини маркери:** Всички места
        """)
    with col2:
        st.markdown("""
        **🔴 Червени линии:** Връзки между места (дебелина = брой връзки)
        """)

def show_network_diagram(place_connections, place_coordinates, place_info):
    """
    Display a network diagram using Plotly.
    """
    st.subheader("Мрежова диаграма на места")
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes
    for place, info in place_info.items():
        G.add_node(place, **info)
    
    # Add edges
    for (place1, place2), weight in place_connections.items():
        G.add_edge(place1, place2, weight=weight)
    
    if len(G.nodes()) == 0:
        st.warning("Няма данни за създаване на мрежова диаграма.")
        return
    
    # Calculate layout
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Add edges
    edge_x = []
    edge_y = []
    edge_info = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        weight = G[edge[0]][edge[1]]['weight']
        edge_info.append(f"{edge[0]} ↔ {edge[1]}: {weight} връзки")
    
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y,
                           line=dict(width=0.5, color='#888'),
                           hoverinfo='none',
                           mode='lines'))
    
    # Add nodes
    node_x = []
    node_y = []
    node_text = []
    node_sizes = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        adjacencies = list(G.neighbors(node))
        info = place_info.get(node, {})
        node_text.append(f"{node}<br>Съседи: {len(adjacencies)}<br>"
                        f"Споменавания: {info.get('total_mentions', 0)}")
        
        node_sizes.append(max(10, info.get('total_mentions', 1) * 3))
    
    fig.add_trace(go.Scatter(x=node_x, y=node_y,
                           mode='markers+text',
                           hoverinfo='text',
                           hovertext=node_text,
                           text=[node for node in G.nodes()],
                           textposition="middle center",
                           marker=dict(size=node_sizes,
                                     color='blue',
                                     line=dict(width=2, color='black'))))
    
    fig.update_layout(title='Географска мрежа на места',
                     title_font_size=16,
                     showlegend=False,
                     hovermode='closest',
                     margin=dict(b=20,l=5,r=5,t=40),
                     annotations=[ dict(
                         text="Размерът на възлите е пропорционален на броя споменавания",
                         showarrow=False,
                         xref="paper", yref="paper",
                         x=0.005, y=-0.002 ) ],
                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    
    st.plotly_chart(fig, width='stretch')

def show_geographical_statistics(place_connections, place_coordinates, place_info, data):
    """
    Display statistics about the geographical network.
    """
    st.subheader("Статистика за географската мрежа")
    
    # General statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Общо места", len(place_info))
    
    with col2:
        st.metric("Места с координати", len(place_coordinates))
    
    with col3:
        st.metric("Общо връзки", len(place_connections))
    
    with col4:
        total_weight = sum(place_connections.values())
        st.metric("Общо комуникации", total_weight)
    
    # Most connected places
    st.subheader("Най-свързани места")
    
    place_connectivity = {}
    for (place1, place2), weight in place_connections.items():
        place_connectivity[place1] = place_connectivity.get(place1, 0) + weight
        place_connectivity[place2] = place_connectivity.get(place2, 0) + weight
    
    if place_connectivity:
        top_places = sorted(place_connectivity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        df_connectivity = pd.DataFrame(top_places, columns=['Място', 'Брой връзки'])
        
        st.dataframe(df_connectivity, width='stretch')
        
        # Visualization
        fig = px.bar(df_connectivity, x='Място', y='Брой връзки', 
                    title='Най-свързани места')
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, width='stretch')
    
    # Connection analysis
    st.subheader("Анализ на връзките")
    
    if place_connections:
        connections_df = pd.DataFrame([
            {'Място 1': place1, 'Място 2': place2, 'Брой връзки': weight}
            for (place1, place2), weight in place_connections.items()
        ]).sort_values('Брой връзки', ascending=False)
        
        st.subheader("Най-силни връзки между места")
        st.dataframe(connections_df.head(15), width='stretch')
