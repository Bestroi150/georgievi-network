import streamlit as st
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import numpy as np

def show_commodity_network_analysis(data):
    """
    Creates and displays commodity network flow analysis.
    
    Analyzes relationships between commodities and places where they are traded.
    """
    
    st.subheader("Анализ на стоковите потоци")
    st.markdown("""
    **Анализ:** Мрежа на стоковите потоци между места  
    **Възли:** Стоки (ключови думи) и места  
    **Връзки:** Споменаване на стока в контекста на място  
    **Цел:** Проследяване на търговските маршрути и стокообмена
    """)
    
    # Extract commodity and place data
    commodity_data = extract_commodity_place_data(data)
    
    if not commodity_data['edges']:
        st.warning("Няма достатъчно данни за анализ на стоковите потоци.")
        return
    
    # Create tabs for different views
    network_tab, flow_tab, analysis_tab = st.tabs(["🕸️ Двустранна мрежа", "📊 Потоци", "🔍 Анализ"])
    
    with network_tab:
        show_commodity_network(commodity_data)
    
    with flow_tab:
        show_commodity_flows(commodity_data)
    
    with analysis_tab:
        show_commodity_analysis(commodity_data)

def extract_commodity_place_data(data):
    """
    Extract commodity and place data from the correspondence data.
    Returns bipartite network data.
    """
    edges = []
    commodities = set()
    places = set()
    
    for entry in data:
        # Extract commodities (keywords)
        entry_commodities = set()
        keywords = entry.get('keywords', [])
        for keyword in keywords:
            if keyword:
                keyword = keyword.strip()
                entry_commodities.add(keyword)
                commodities.add(keyword)
        
        # Extract mentioned places
        entry_places = set()
        mentioned_places = entry.get('mentioned_places', [])
        for place_info in mentioned_places:
            place = place_info.get('name', '')
            if place:
                place = place.strip()
                entry_places.add(place)
                places.add(place)
        
        # Also add sender and addressee places
        sender_place = entry.get('sender_place')
        if sender_place:
            sender_place = sender_place.strip()
            entry_places.add(sender_place)
            places.add(sender_place)
        
        addressee_place = entry.get('addressee_place')
        if addressee_place:
            addressee_place = addressee_place.strip()
            entry_places.add(addressee_place)
            places.add(addressee_place)
        
        # Create edges between commodities and places
        for commodity in entry_commodities:
            for place in entry_places:
                edges.append((commodity, place, 'commodity_place'))
    
    # Count edge frequencies
    edge_counter = Counter(edges)
    
    return {
        'edges': dict(edge_counter),
        'commodities': list(commodities),
        'places': list(places),
        'all_nodes': list(commodities) + list(places)
    }

def show_commodity_network(commodity_data):
    """
    Display bipartite network of commodities and places.
    """
    st.subheader("Двустранна мрежа: Стоки ↔ Места")
    
    # Create bipartite graph
    G = nx.Graph()
    
    # Add nodes with types
    for commodity in commodity_data['commodities']:
        G.add_node(commodity, node_type='commodity')
    
    for place in commodity_data['places']:
        G.add_node(place, node_type='place')
    
    # Add edges
    for (commodity, place, edge_type), weight in commodity_data['edges'].items():
        if edge_type == 'commodity_place':
            G.add_edge(commodity, place, weight=weight)
    
    if G.number_of_nodes() == 0:
        st.warning("Няма данни за създаване на мрежа.")
        return
    
    # Control parameters
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Настройки")
        min_weight = st.slider(
            "Минимален брой споменавания:", 
            1, 
            max([w for (_, _, _), w in commodity_data['edges'].items()]) if commodity_data['edges'] else 5, 
            1,
            key="commodity_min_weight"
        )
        
        show_labels = st.checkbox("Покажи етикети", True, key="commodity_show_labels")
        
        layout_type = st.selectbox(
            "Тип на подредбата:",
            ["bipartite", "spring", "circular"],
            index=0,
            key="commodity_layout_type"
        )
    
    with col1:
        # Filter edges by weight
        filtered_edges = [
            (commodity, place) for (commodity, place, edge_type), weight 
            in commodity_data['edges'].items() 
            if weight >= min_weight and edge_type == 'commodity_place'
        ]
        
        if not filtered_edges:
            st.warning("Няма връзки, които отговарят на критерия.")
            return
        
        # Create filtered graph
        G_filtered = nx.Graph()
        for commodity in commodity_data['commodities']:
            G_filtered.add_node(commodity, node_type='commodity')
        for place in commodity_data['places']:
            G_filtered.add_node(place, node_type='place')
        
        G_filtered.add_edges_from(filtered_edges)
        
        # Remove isolated nodes
        G_filtered.remove_nodes_from(list(nx.isolates(G_filtered)))
        
        # Calculate layout
        if layout_type == "bipartite":
            try:
                commodity_nodes = [n for n in G_filtered.nodes() if n in commodity_data['commodities']]
                place_nodes = [n for n in G_filtered.nodes() if n in commodity_data['places']]
                pos = nx.bipartite_layout(G_filtered, commodity_nodes)
            except:
                pos = nx.spring_layout(G_filtered, k=1, iterations=50)
        elif layout_type == "spring":
            pos = nx.spring_layout(G_filtered, k=1, iterations=50)
        else:  # circular
            pos = nx.circular_layout(G_filtered)
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add edges
        edge_x = []
        edge_y = []
        for edge in G_filtered.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        node_labels = []
        
        for node in G_filtered.nodes():
            if node in pos:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                connections = len(list(G_filtered.neighbors(node)))
                node_type = 'commodity' if node in commodity_data['commodities'] else 'place'
                
                node_text.append(
                    f"<b>{node}</b><br>"
                    f"Тип: {'Стока' if node_type == 'commodity' else 'Място'}<br>"
                    f"Връзки: {connections}"
                )
                
                # Color by type
                node_colors.append('gold' if node_type == 'commodity' else 'skyblue')
                node_sizes.append(max(15, connections * 5 + 10))
                node_labels.append(node if show_labels else '')
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text' if show_labels else 'markers',
            hoverinfo='text',
            hovertext=node_text,
            text=node_labels,
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='black')
            )
        ))
        
        fig.update_layout(
            title='Двустранна мрежа: Стоки ↔ Места',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[dict(
                text="🟡 Стоки | 🔵 Места",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, width='stretch')

def show_commodity_flows(commodity_data):
    """
    Display commodity flow analysis.
    """
    st.subheader("Анализ на стоковите потоци")
    
    # Create flow data
    commodity_flows = {}
    place_flows = {}
    
    for (commodity, place, edge_type), weight in commodity_data['edges'].items():
        if edge_type == 'commodity_place':
            if commodity not in commodity_flows:
                commodity_flows[commodity] = []
            commodity_flows[commodity].append((place, weight))
            
            if place not in place_flows:
                place_flows[place] = []
            place_flows[place].append((commodity, weight))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ стоки по брой места")
        commodity_summary = []
        for commodity, flows in commodity_flows.items():
            total_weight = sum(weight for _, weight in flows)
            num_places = len(flows)
            commodity_summary.append({
                'Стока': commodity,
                'Брой места': num_places,
                'Общо споменавания': total_weight
            })
        
        commodity_df = pd.DataFrame(commodity_summary).sort_values('Брой места', ascending=False)
        st.dataframe(commodity_df.head(15), width='stretch')
        
        # Visualization
        if not commodity_df.empty:
            fig = px.bar(
                commodity_df.head(10),
                x='Брой места',
                y='Стока',
                orientation='h',
                title='Топ 10 стоки по географско разпространение'
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Топ места по брой стоки")
        place_summary = []
        for place, flows in place_flows.items():
            total_weight = sum(weight for _, weight in flows)
            num_commodities = len(flows)
            place_summary.append({
                'Място': place,
                'Брой стоки': num_commodities,
                'Общо споменавания': total_weight
            })
        
        place_df = pd.DataFrame(place_summary).sort_values('Брой стоки', ascending=False)
        st.dataframe(place_df.head(15), width='stretch')
        
        # Visualization
        if not place_df.empty:
            fig = px.bar(
                place_df.head(10),
                x='Брой стоки',
                y='Място',
                orientation='h',
                title='Топ 10 места по стоково разнообразие'
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, width='stretch')

def show_commodity_analysis(commodity_data):
    """
    Show detailed analysis of commodity networks.
    """
    st.subheader("Мрежов анализ на стоковите потоци")
    
    # Create bipartite graph for analysis
    G = nx.Graph()
    
    for commodity in commodity_data['commodities']:
        G.add_node(commodity, node_type='commodity')
    
    for place in commodity_data['places']:
        G.add_node(place, node_type='place')
    
    for (commodity, place, edge_type), weight in commodity_data['edges'].items():
        if edge_type == 'commodity_place':
            G.add_edge(commodity, place, weight=weight)
    
    if G.number_of_nodes() == 0:
        st.warning("Няма данни за мрежов анализ.")
        return
    
    # Calculate centrality measures
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    # Separate analysis for commodities and places
    commodities_centrality = []
    places_centrality = []
    
    for node in G.nodes():
        centrality_data = {
            'Възел': node,
            'Степенна централност': degree_centrality[node],
            'Посредническа централност': betweenness_centrality[node],
            'Връзки': G.degree(node)
        }
        
        if node in commodity_data['commodities']:
            commodities_centrality.append(centrality_data)
        else:
            places_centrality.append(centrality_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ стоки по централност")
        commodities_df = pd.DataFrame(commodities_centrality).sort_values('Степенна централност', ascending=False)
        st.dataframe(commodities_df.head(10), width='stretch')
    
    with col2:
        st.subheader("Топ места по централност")
        places_df = pd.DataFrame(places_centrality).sort_values('Степенна централност', ascending=False)
        st.dataframe(places_df.head(10), width='stretch')
    
    # Network statistics
    st.subheader("Статистики на мрежата")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Стоки", len(commodity_data['commodities']))
    
    with col2:
        st.metric("Места", len(commodity_data['places']))
    
    with col3:
        st.metric("Връзки", G.number_of_edges())
    
    with col4:
        density = nx.density(G)
        st.metric("Плътност", f"{density:.3f}")
    
    # Edge weight distribution
    st.subheader("Разпределение на силата на връзките")
    weights = [w for (_, _, _), w in commodity_data['edges'].items()]
    
    fig = px.histogram(
        x=weights,
        nbins=20,
        title='Разпределение на броя споменавания стока-място'
    )
    fig.update_xaxes(title="Брой споменавания")
    fig.update_yaxes(title="Честота")
    st.plotly_chart(fig, width='stretch')
