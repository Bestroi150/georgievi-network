import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from labels import get_labels

def show_network_analysis(data):
    """
    Enhanced network analysis of correspondences with sidebar controls and metrics.
    Nodes represent people, edges represent correspondence relationships.

    :param data: List of dictionaries, each representing a single letter's data.
    """
    lang = st.session_state.get('lang', 'bg')
    L = get_labels(lang)

    st.header(L['na_func_header'])
    st.markdown(L['na_subtitle'])

    st.subheader(L['na_settings'])
    
    # Create columns for control layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Minimum connections filter
        min_connections = st.slider(
            L['na_min_conn'],
            min_value=1,
            max_value=10,
            value=1,
            help=L['na_min_conn_help'],
            key="network_min_connections"
        )
    
    with col2:
        # Layout algorithm
        layout_algorithm = st.selectbox(
            L['na_layout'],
            ["forceAtlas2Based", "repulsion", "hierarchicalRepulsion", "stabilization"],
            index=0,
            help=L['na_layout_help'],
            key="network_layout_algorithm"
        )
    
    with col3:
        # Node size scaling
        node_size_factor = st.slider(
            L['na_node_size'],
            min_value=10,
            max_value=50,
            value=25,
            help=L['na_node_size_help'],
            key="network_node_size"
        )
    
    with col4:
        # Show edge weights
        show_edge_weights = st.checkbox(
            L['na_show_weights'],
            value=True,
            help=L['na_show_weights_help'],
            key="network_show_weights"
        )
    
    st.divider()  # Add a visual separator

    # --- 1. Create a Directed Graph from the Data ---
    G = nx.DiGraph()

    edge_weights = {}
    for entry in data:
        sender = entry.get('sender_name')
        addressee = entry.get('addressee_name')
        if sender and addressee:
            edge_weights[(sender, addressee)] = edge_weights.get((sender, addressee), 0) + 1

    # Add edges to the graph with 'weight' attributes
    for (sender, addressee), weight in edge_weights.items():
        G.add_edge(sender, addressee, weight=weight)

    # Filter nodes by minimum connections
    degree_dict = {node: G.in_degree(node) + G.out_degree(node) for node in G.nodes()}
    filtered_nodes = [node for node, degree in degree_dict.items() if degree >= min_connections]
    G_filtered = G.subgraph(filtered_nodes).copy()

    if len(G_filtered.nodes()) == 0:
        st.warning("🚫 Няма данни за показване с текущите настройки. Намалете минималния брой връзки.")
        return

    # --- 2. Display Network Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Общо лица",
            value=len(G_filtered.nodes()),
            help="Брой уникални лица в мрежата"
        )
    
    with col2:
        st.metric(
            label="📫 Общо връзки",
            value=len(G_filtered.edges()),
            help="Брой връзки между лицата"
        )
    
    with col3:
        total_letters = sum(data.get('weight', 1) for _, _, data in G_filtered.edges(data=True))
        st.metric(
            label="💌 Общо писма",
            value=total_letters,
            help="Общ брой разменени писма"
        )
    
    with col4:
        if len(G_filtered.nodes()) > 1:
            density = nx.density(G_filtered)
            st.metric(
                label="🔗 Плътност",
                value=f"{density:.3f}",
                help="Плътност на мрежата (0-1)"
            )

    # --- 3. Build a PyVis Network from the NetworkX Graph ---
    net = Network(
        height='700px',
        width='100%',
        notebook=False,  
        directed=True,   
        bgcolor='#fafafa',
        font_color='black'
    )
    net.from_nx(G_filtered)

    # --- 4. Color Nodes Based on Total Connections (Degree) ---
    degree_dict_filtered = {node: G_filtered.in_degree(node) + G_filtered.out_degree(node) 
                           for node in G_filtered.nodes()}
    
    if degree_dict_filtered:
        min_deg = min(degree_dict_filtered.values())
        max_deg = max(degree_dict_filtered.values())
    else:
        min_deg, max_deg = 0, 1 

    def get_node_color(degree):
        """
        Generates a color based on the node's degree.
        """
        if min_deg == max_deg:
            color_hex = '#2E86AB' 
        else:
            ratio = (degree - min_deg) / (max_deg - min_deg)
            # Light Blue to Dark Blue gradient
            r1, g1, b1 = 173, 216, 230  
            r2, g2, b2 = 46, 134, 171      
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color_hex = f'#{r:02x}{g:02x}{b:02x}'

        return {
            'background': color_hex,
            'border': '#1e3d59',
            'highlight': {
                'background': color_hex,
                'border': '#1e3d59'
            }
        }

    # Apply colors and sizes to each node
    for node in net.nodes:
        node_label = node["id"]
        degree = degree_dict_filtered.get(node_label, 0)
        node["color"] = get_node_color(degree)
        node["size"] = max(node_size_factor + (degree * 5), 15)
        
        # Enhanced node information
        in_degree = G_filtered.in_degree(node_label)
        out_degree = G_filtered.out_degree(node_label)
        node["title"] = f"""
        <b>{node_label}</b><br>
        {L['na_total_tooltip']}: {degree}<br>
        {L['na_received_tooltip']}: {in_degree}<br>
        {L['na_sent_tooltip']}: {out_degree}
        """

    # --- 5. Style Edges with Different Colors and Weights ---
    max_weight = max([G_filtered[u][v].get('weight', 1) for u, v in G_filtered.edges()]) if G_filtered.edges() else 1

    for edge in net.edges:
        src, dst = edge["from"], edge["to"]
        weight = G_filtered[src][dst].get('weight', 1)
        
        # Edge color based on weight
        intensity = weight / max_weight
        edge_color = f'rgba(136, 136, 136, {0.3 + intensity * 0.7})'
        edge["color"] = edge_color
        
        # Edge width based on weight
        edge["width"] = max(1, weight * 2)
        
        # Edge title with weight information
        if show_edge_weights:
            edge["title"] = f"{src} → {dst}<br>{L['na_letters_label']}: {weight}"
        else:
            edge["title"] = f"{src} → {dst}"

    # --- 6. Configure Physics Based on Selected Algorithm ---
    physics_options = {
        "forceAtlas2Based": """
        {
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.003,
              "springConstant": 0.08,
              "springLength": 100,
              "damping": 0.4
            },
            "stabilization": {"iterations": 1000}
          },
          "nodes": {
            "shape": "dot",
            "font": {
              "size": 14,
              "color": "#2c3e50"
            },
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 1.2 }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 300
          }
        }
        """,
        "repulsion": """
        {
          "physics": {
            "enabled": true,
            "solver": "repulsion",
            "repulsion": {
              "nodeDistance": 150,
              "centralGravity": 0.05,
              "springLength": 200,
              "springConstant": 0.05,
              "damping": 0.09
            },
            "stabilization": {"iterations": 500}
          },
          "nodes": {
            "shape": "dot",
            "font": {
              "size": 14,
              "color": "#2c3e50"
            },
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 1.2 }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 300
          }
        }
        """,
        "hierarchicalRepulsion": """
        {
          "physics": {
            "enabled": true,
            "solver": "hierarchicalRepulsion",
            "hierarchicalRepulsion": {
              "nodeDistance": 120,
              "centralGravity": 0.0,
              "springLength": 100,
              "springConstant": 0.01,
              "damping": 0.09
            },
            "stabilization": {"iterations": 300}
          },
          "nodes": {
            "shape": "dot",
            "font": {
              "size": 14,
              "color": "#2c3e50"
            },
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 1.2 }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 300
          }
        }
        """,
        "stabilization": """
        {
          "physics": {
            "enabled": false
          },
          "layout": {
            "randomSeed": 2
          },
          "nodes": {
            "shape": "dot",
            "font": {
              "size": 14,
              "color": "#2c3e50"
            },
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 1.2 }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 300
          }
        }
        """
    }

    selected_options = physics_options.get(layout_algorithm, physics_options["forceAtlas2Based"])
    net.set_options(selected_options)

    # --- 7. Render the Network in Streamlit ---
    st.subheader(L['na_interactive_net'])
    
    try:
        # Generate HTML content
        html_content = net.generate_html()
        
        # Enhanced container with better styling
        enhanced_html = f"""
        <div style="
            width: 100%;
            height: 720px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            padding: 5px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            {html_content}
        </div>
        """
        
        components.html(enhanced_html, height=740, scrolling=True)
        
    except AttributeError:
        try:
            html_content = net.to_html()
            enhanced_html = f"""
            <div style="
                width: 100%;
                height: 720px;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                padding: 5px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                {html_content}
            </div>
            """
            components.html(enhanced_html, height=740, scrolling=True)
        except Exception as e:
            st.error(f"{L['na_error']}: {e}")

    # --- 8. Additional Analysis Sections ---

    # Top correspondents
    st.subheader(L['na_top_corr'])

    degree_df = pd.DataFrame([
        {
            L['na_person_col']: node,
            L['na_total_conn_col']: degree_dict_filtered[node],
            L['na_received_col']: G_filtered.in_degree(node),
            L['na_sent_col']: G_filtered.out_degree(node)
        }
        for node in degree_dict_filtered.keys()
    ]).sort_values(L['na_total_conn_col'], ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**{L['na_top10_label']}**")
        st.dataframe(
            degree_df.head(10),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # Centrality measures
        if len(G_filtered.nodes()) > 1:
            st.write(f"**{L['na_centrality_label']}**")
            
            betweenness = nx.betweenness_centrality(G_filtered)
            closeness = nx.closeness_centrality(G_filtered)
            
            centrality_df = pd.DataFrame([
                {
                    L['na_person_col']: node,
                    'Betweenness': f"{betweenness.get(node, 0):.3f}",
                    'Closeness': f"{closeness.get(node, 0):.3f}"
                }
                for node in list(G_filtered.nodes())[:10]
            ])
            
            st.dataframe(
                centrality_df,
                use_container_width=True,
                hide_index=True
            )

    st.subheader(L['na_dist_analysis'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Degree distribution
        degrees = list(degree_dict_filtered.values())
        fig_hist = px.histogram(
            x=degrees,
            title=L['na_conn_dist_title'],
            labels={'x': L['na_conn_dist_x'], 'y': L['na_conn_dist_y']},
            color_discrete_sequence=['#2E86AB']
        )
        fig_hist.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Top connections bar chart
        top_10 = degree_df.head(10)
        fig_bar = px.bar(
            top_10,
            x=L['na_total_conn_col'],
            y=L['na_person_col'],
            orientation='h',
            title=L['na_top10_title'],
            color=L['na_total_conn_col'],
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Example usage within a Streamlit app
if __name__ == "__main__":
    st.title(L['na_func_header'] if 'L' in dir() else '📬 Correspondence Network Analysis')
    st.markdown(L['na_advanced'] if 'L' in dir() else 'Advanced correspondence network analysis')


