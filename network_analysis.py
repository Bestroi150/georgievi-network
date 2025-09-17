import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

def show_network_analysis(data):
    """
    Creates and displays an interactive network graph of correspondences (sender -> addressee).
    Nodes are colored based on their total number of connections and both nodes and edges are translucent.

    :param data: List of dictionaries, each representing a single letter's data.
    """
    st.subheader("--------")

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

    # --- 2. Build a PyVis Network from the NetworkX Graph ---
    net = Network(
        height='600px',
        width='100%',
        notebook=False,  
        directed=True,   
        bgcolor='#ffffff',
        font_color='black'
    )
    net.from_nx(G)

    # --- 3. Color Nodes Based on Total Connections (Degree) ---
    degree_dict = {node: G.in_degree(node) + G.out_degree(node) for node in G.nodes()}
    
    if degree_dict:
        min_deg = min(degree_dict.values())
        max_deg = max(degree_dict.values())
    else:
        min_deg, max_deg = 0, 1 

    def get_node_color(degree):
        """
        Generates a translucent color between light blue and dark blue based on the node's degree.

        :param degree: The degree of the node.
        :return: Dictionary with background and border colors including opacity.
        """
        if min_deg == max_deg:
            color_hex = '#5b86c5' 
        else:
            ratio = (degree - min_deg) / (max_deg - min_deg)
            # Light Blue (#ADD8E6) to Dark Blue (#00008B)
            r1, g1, b1 = 173, 216, 230  
            r2, g2, b2 = 0, 0, 139      
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color_hex = f'#{r:02x}{g:02x}{b:02x}'

        return {
            'background': color_hex,
            'border': color_hex,
            'highlight': {
                'background': color_hex,
                'border': color_hex
            },
            'opacity': 0.8,    # 80% opacity for nodes
            'borderWidth': 2
        }

    # Apply colors to each node based on their degree
    for node in net.nodes:
        node_label = node["id"]
        degree = degree_dict.get(node_label, 0)
        node["color"] = get_node_color(degree)
        # Display degree on hover
        node["title"] = f"{node_label} (Connections: {degree})"

    # --- 4. Style Edges with Different Colors and Translucency ---
    def get_edge_color():
        """
        Returns a consistent translucent color for all edges.

        :return: Dictionary with edge color and opacity.
        """
        return {
            'color': '#888888',  # Gray color for edges
            'opacity': 0.5        # 50% opacity for edges
        }

    # Apply styles to each edge
    for edge in net.edges:
        edge["color"] = get_edge_color()
        src, dst = edge["from"], edge["to"]
        weight = G[src][dst].get('weight', 1)
        edge["title"] = f"Letters exchanged: {weight}"

    # --- 5. Configure Physics for Network Stability ---    
    net.set_options("""
    var options = {
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
        "stabilization": {
          "iterations": 1000
        }
      },
      "nodes": {
        "shape": "dot",
        "font": {
          "size": 12
        }
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true }
        },
        "smooth": false
      }
    }
    """)

    # --- 6. Render the Network in Streamlit Within a Resizable Container ---
    try:
        # Generate HTML content as a string
        html_content = net.generate_html()  # For pyvis versions < 0.5.1
        # For pyvis versions >= 0.5.1, use:
        # html_content = net.to_html()

        # Create a resizable container using a div with CSS
        resizable_html = f"""
            <div style="
                resize: both;
                overflow: auto;
                width: 100%;
                height: 600px;
                border: 1px solid #ccc;
                padding: 10px;
            ">
                {html_content}
            </div>
        """

        # Render the resizable HTML content in Streamlit
        components.html(resizable_html, height=620, scrolling=True)
    except AttributeError:
        try:
            # For pyvis versions >= 0.5.1
            html_content = net.to_html()
            resizable_html = f"""
                <div style="
                    resize: both;
                    overflow: auto;
                    width: 100%;
                    height: 600px;
                    border: 1px solid #ccc;
                    padding: 10px;
                ">
                    {html_content}
                </div>
            """
            components.html(resizable_html, height=620, scrolling=True)
        except Exception as e:
            st.error(f"⚠️ An error occurred while generating the network chart: {e}")
    except Exception as e:
        st.error(f"⚠️ An error occurred while generating the network chart: {e}")

# Example usage within a Streamlit app
if __name__ == "__main__":
    st.title("📬-------")


