import streamlit as st
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import numpy as np
from labels import get_labels

def show_commodity_network_analysis(data):
    """
    Creates and displays commodity network flow analysis.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ca_subheader'])
    st.markdown(L['ca_desc'])
    
    # Extract commodity and place data
    commodity_data = extract_commodity_place_data(data)
    
    if not commodity_data['edges']:
        st.warning(L['ca_no_data'])
        return
    
    # Create tabs for different views
    network_tab, flow_tab, analysis_tab = st.tabs([L['ca_inner_network'], L['ca_inner_flows'], L['ca_inner_analysis']])
    
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
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ca_net_header'])
    
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
        st.warning(L['ca_no_net'])
        return
    
    # Control parameters
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader(L['ca_settings'])
        min_weight = st.slider(
            L['ca_min_mentions'],
            1,
            max([w for (_, _, _), w in commodity_data['edges'].items()]) if commodity_data['edges'] else 5,
            1,
            key="commodity_min_weight"
        )
        
        show_labels = st.checkbox(L['ca_show_labels'], True, key="commodity_show_labels")
        
        layout_type = st.selectbox(
            L['ca_layout_type'],
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
            st.warning(L['ca_no_match'])
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
                    f"{L['ca_type_commodity'] if node_type == 'commodity' else L['ca_type_place']}<br>"
                    f"{L['ca_conn_label'].format(n=connections)}"
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
            title=L['ca_net_title'],
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[dict(
                text=L['ca_annotation'],
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
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ca_flows_header'])
    
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
        st.subheader(L['ca_top_commodities'])
        commodity_summary = []
        for commodity, flows in commodity_flows.items():
            total_weight = sum(weight for _, weight in flows)
            num_places = len(flows)
            commodity_summary.append({
                L['ca_commodity_col']: commodity,
                L['ca_num_places_col']: num_places,
                L['ca_total_mentions_col']: total_weight
            })
        
        commodity_df = pd.DataFrame(commodity_summary).sort_values(L['ca_num_places_col'], ascending=False)
        st.dataframe(commodity_df.head(15), width='stretch')
        
        # Visualization
        if not commodity_df.empty:
            fig = px.bar(
                commodity_df.head(10),
                x=L['ca_num_places_col'],
                y=L['ca_commodity_col'],
                orientation='h',
                title=L['ca_top_comm_title']
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader(L['ca_top_places'])
        place_summary = []
        for place, flows in place_flows.items():
            total_weight = sum(weight for _, weight in flows)
            num_commodities = len(flows)
            place_summary.append({
                L['ca_place_col']: place,
                L['ca_num_commodities_col']: num_commodities,
                L['ca_total_mentions_col']: total_weight
            })
        
        place_df = pd.DataFrame(place_summary).sort_values(L['ca_num_commodities_col'], ascending=False)
        st.dataframe(place_df.head(15), width='stretch')
        
        # Visualization
        if not place_df.empty:
            fig = px.bar(
                place_df.head(10),
                x=L['ca_num_commodities_col'],
                y=L['ca_place_col'],
                orientation='h',
                title=L['ca_top_places_title']
            )
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, width='stretch')

def show_commodity_analysis(commodity_data):
    """
    Show detailed analysis of commodity networks.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['ca_network_analysis'])
    
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
        st.warning(L['ca_no_net_analysis'])
        return
    
    # Calculate centrality measures
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    
    # Separate analysis for commodities and places
    commodities_centrality = []
    places_centrality = []
    
    for node in G.nodes():
        centrality_data = {
            L['ca_node_col']: node,
            L['ca_degree_col']: degree_centrality[node],
            L['ca_betweenness_col']: betweenness_centrality[node],
            L['ca_connections_col']: G.degree(node)
        }
        
        if node in commodity_data['commodities']:
            commodities_centrality.append(centrality_data)
        else:
            places_centrality.append(centrality_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(L['ca_top_commodities_central'])
        commodities_df = pd.DataFrame(commodities_centrality).sort_values(L['ca_degree_col'], ascending=False)
        st.dataframe(commodities_df.head(10), width='stretch')
    
    with col2:
        st.subheader(L['ca_top_places_central'])
        places_df = pd.DataFrame(places_centrality).sort_values(L['ca_degree_col'], ascending=False)
        st.dataframe(places_df.head(10), width='stretch')
    
    st.subheader(L['ca_net_stats'])
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(L['ca_commodities_metric'], len(commodity_data['commodities']))
    
    with col2:
        st.metric(L['ca_places_metric'], len(commodity_data['places']))
    
    with col3:
        st.metric(L['ca_edges_metric'], G.number_of_edges())
    
    with col4:
        density = nx.density(G)
        st.metric(L['ca_density_metric'], f"{density:.3f}")
    
    st.subheader(L['ca_weight_dist'])
    weights = [w for (_, _, _), w in commodity_data['edges'].items()]
    
    fig = px.histogram(
        x=weights,
        nbins=20,
        title=L['ca_weight_dist_title']
    )
    fig.update_xaxes(title=L['ca_weight_x'])
    fig.update_yaxes(title=L['ca_weight_y'])
    st.plotly_chart(fig, width='stretch')
