import streamlit as st
import itertools
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import numpy as np
from labels import get_labels

def show_topics_keywords_analysis(data):
    """
    Creates and displays topic and keyword co-occurrence network analysis.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['tk_subheader'])
    st.markdown(L['tk_desc'])
    
    # Extract topics and keywords data
    topics_data, cooccurrence_data = extract_topics_keywords_data(data)
    
    if not topics_data:
        st.warning(L['tk_no_data'])
        return
    
    # Create tabs for different views
    network_tab, frequency_tab, analysis_tab = st.tabs([L['tk_inner_network'], L['tk_inner_freq'], L['tk_inner_analysis']])
    
    with network_tab:
        show_topics_network(topics_data, cooccurrence_data)
    
    with frequency_tab:
        show_topics_frequency(topics_data)
    
    with analysis_tab:
        show_topics_analysis(topics_data, cooccurrence_data)

def extract_topics_keywords_data(data):
    """
    Extract topics and keywords data from the correspondence data.
    Returns topics data and co-occurrence information.
    """
    letters_topics = []
    all_topics = Counter()
    
    for entry in data:
        topics = set()
        
        # Add main topics
        main_topics = entry.get('main_topics', [])
        for topic in main_topics:
            if topic:
                topic = topic.strip()
                topics.add(topic)
                all_topics[topic] += 1
        
        # Add keywords
        keywords = entry.get('keywords', [])
        for keyword in keywords:
            if keyword:
                keyword = keyword.strip()
                topics.add(keyword)
                all_topics[keyword] += 1
        
        if topics:
            letters_topics.append(topics)
    
    # Build co-occurrence edges
    cooccurrence = Counter()
    for topics in letters_topics:
        for a, b in itertools.combinations(sorted(topics), 2):
            cooccurrence[(a, b)] += 1
    
    return {
        'letters_topics': letters_topics,
        'all_topics': all_topics,
        'topic_frequency': dict(all_topics)
    }, dict(cooccurrence)

def show_topics_network(topics_data, cooccurrence_data):
    """
    Display interactive network of topics and keywords using Plotly.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['tk_network_header'])
    
    if not cooccurrence_data:
        st.warning(L['tk_no_links'])
        return
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add edges with weights
    for (topic1, topic2), weight in cooccurrence_data.items():
        G.add_edge(topic1, topic2, weight=weight)
    
    # Set node attributes
    topic_freq = topics_data['topic_frequency']
    nx.set_node_attributes(G, topic_freq, 'frequency')
    
    # Control parameters
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader(L['tk_settings'])
        min_cooccurrence = st.slider(
            L['tk_min_cooc'],
            1,
            max(cooccurrence_data.values()) if cooccurrence_data else 5,
            1,
            key="topics_min_cooccurrence"
        )
        
        layout_algorithm = st.selectbox(
            L['tk_layout'],
            ["spring", "circular", "kamada_kawai"],
            index=0,
            key="topics_layout_algorithm"
        )
    
    with col1:
        # Filter edges by minimum co-occurrence
        filtered_edges = [(a, b) for (a, b), w in cooccurrence_data.items() if w >= min_cooccurrence]
        
        if not filtered_edges:
            st.warning(L['tk_no_match'])
            return
        
        # Create filtered graph
        G_filtered = nx.Graph()
        G_filtered.add_edges_from(filtered_edges)
        
        # Calculate layout
        if layout_algorithm == "spring":
            pos = nx.spring_layout(G_filtered, k=1, iterations=50)
        elif layout_algorithm == "circular":
            pos = nx.circular_layout(G_filtered)
        else:  # kamada_kawai
            pos = nx.kamada_kawai_layout(G_filtered)
        
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
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []
        node_colors = []
        
        for node in G_filtered.nodes():
            if node in pos:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                frequency = topic_freq.get(node, 1)
                connections = len(list(G_filtered.neighbors(node)))
                
                node_text.append(
                    f"<b>{node}</b><br>"
                    f"{L['tk_freq_label'].format(n=frequency)}<br>"
                    f"{L['tk_conn_label'].format(n=connections)}"
                )
                
                node_sizes.append(max(20, frequency * 10))
                node_colors.append(frequency)
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            hovertext=node_text,
            text=[node for node in G_filtered.nodes() if node in pos],
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title=L['tk_colorbar_title']),
                line=dict(width=2, color='black')
            )
        ))
        
        fig.update_layout(
            title=L['tk_net_title'],
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[dict(
                text=L['tk_shown'].format(n=len(G_filtered.nodes()), m=min_cooccurrence),
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, width='stretch')

def show_topics_frequency(topics_data):
    """
    Display frequency analysis of topics and keywords.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['tk_freq_header'])
    
    topic_freq = topics_data['topic_frequency']
    
    if not topic_freq:
        st.warning(L['tk_no_freq'])
        return
    
    # Create frequency DataFrame
    freq_df = pd.DataFrame(
        list(topic_freq.items()),
        columns=[L['tk_topic_col'], L['tk_freq_col']]
    ).sort_values(L['tk_freq_col'], ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(L['tk_top20'])
        top_topics = freq_df.head(20)
        st.dataframe(top_topics, width='stretch')
    
    with col2:
        st.subheader(L['tk_freq_dist'])
        fig = px.bar(
            top_topics.head(15),
            x=L['tk_freq_col'],
            y=L['tk_topic_col'],
            orientation='h',
            title=L['tk_freq_dist_title']
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, width='stretch')
    
    st.subheader(L['tk_stats'])
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(L['tk_total'], len(topic_freq))
    
    with col2:
        st.metric(L['tk_avg_freq'], f"{np.mean(list(topic_freq.values())):.1f}")
    
    with col3:
        st.metric(L['tk_max_freq'], max(topic_freq.values()))
    
    with col4:
        unique_topics = sum(1 for freq in topic_freq.values() if freq == 1)
        st.metric(L['tk_unique'], unique_topics)

def show_topics_analysis(topics_data, cooccurrence_data):
    """
    Show detailed analysis of topic relationships.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.subheader(L['tk_conn_analysis'])
    
    if not cooccurrence_data:
        st.warning(L['tk_no_conn'])
        return
    
    # Create co-occurrence DataFrame
    cooc_df = pd.DataFrame([
        {
            L['tk_topic1_col']: topic1,
            L['tk_topic2_col']: topic2,
            L['tk_cooc_col']: weight
        }
        for (topic1, topic2), weight in cooccurrence_data.items()
    ]).sort_values(L['tk_cooc_col'], ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(L['tk_strong_links'])
        st.dataframe(cooc_df.head(15), width='stretch')
    
    with col2:
        st.subheader(L['tk_conn_dist'])
        fig = px.histogram(
            cooc_df,
            x=L['tk_cooc_col'],
            nbins=20,
            title=L['tk_conn_dist_title']
        )
        st.plotly_chart(fig, width='stretch')
    
    # Network metrics
    if cooccurrence_data:
        st.subheader(L['tk_metrics'])
        
        G = nx.Graph()
        for (topic1, topic2), weight in cooccurrence_data.items():
            G.add_edge(topic1, topic2, weight=weight)
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        # Create centrality DataFrame
        centrality_df = pd.DataFrame({
            L['tk_topic_row']: list(degree_centrality.keys()),
            L['tk_degree_centrality']: list(degree_centrality.values()),
            L['tk_betweenness']: list(betweenness_centrality.values()),
            L['tk_closeness']: list(closeness_centrality.values())
        }).round(3)
        
        centrality_df = centrality_df.sort_values(L['tk_degree_centrality'], ascending=False)
        
        st.subheader(L['tk_top15'])
        st.dataframe(centrality_df.head(15), width='stretch')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(L['tk_nodes'], G.number_of_nodes())
        
        with col2:
            st.metric(L['tk_edges'], G.number_of_edges())
        
        with col3:
            density = nx.density(G)
            st.metric(L['tk_density'], f"{density:.3f}")
        
        with col4:
            if nx.is_connected(G):
                avg_path = nx.average_shortest_path_length(G)
                st.metric(L['tk_avg_path'], f"{avg_path:.2f}")
            else:
                st.metric(L['tk_components'], nx.number_connected_components(G))
