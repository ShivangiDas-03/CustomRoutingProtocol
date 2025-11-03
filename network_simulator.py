import heapq
import matplotlib.pyplot as plt
import networkx as nx
import time
import textwrap

class Router:
    """
    Represents a router in the network.
    Each router has a name and maintains a routing table.
    """
    def __init__(self, name):
        self.name = name
        # The routing table will store the shortest path to other routers.
        # Format: {destination: (next_hop, cost)}
        self.routing_table = {self.name: (self.name, 0)}

    def __repr__(self):
        return f"Router({self.name})"

class Network:
    """
    Represents the entire network, containing routers and links.
    It manages the network topology and runs routing algorithms.
    """
    def __init__(self):
        # Adjacency list to represent the network graph.
        # Format: {router: {neighbor: cost}}
        self.adjacency_list = {}
        self.routers = {}

    def add_router(self, name):
        """Adds a router to the network."""
        if name not in self.routers:
            router = Router(name)
            self.routers[name] = router
            self.adjacency_list[name] = {}
            print(f"INFO: Router {name} added.")
            return True
        else:
            print(f"WARNING: Router {name} already exists.")
            return False

    def remove_router(self, router_name):
        """Removes a router and all its associated links from the network."""
        if router_name in self.routers:
            del self.routers[router_name]
            del self.adjacency_list[router_name]
            
            # Remove any links pointing to this router from other routers
            # Use list() to avoid "dictionary changed size during iteration" error
            for r_name in list(self.adjacency_list.keys()):
                if router_name in self.adjacency_list[r_name]:
                    del self.adjacency_list[r_name][router_name]
            
            print(f"INFO: Router {router_name} and its links have been removed.")
            return True
        else:
            print(f"WARNING: Router {router_name} not found.")
            return False

    def add_link(self, router1_name, router2_name, cost):
        """Adds a ONE-WAY (directed) link from router1 to router2."""
        if router1_name in self.routers and router2_name in self.routers:
            try:
                cost = int(cost)
            except ValueError:
                print(f"ERROR: Cost '{cost}' is not a valid integer.")
                return False

            if cost < 0:
                print(f"WARNING: Negative cost ({cost}) added for link {router1_name}->{router2_name}. Dijkstra's algorithm will not work correctly.")
            
            # This now adds a one-way link
            self.adjacency_list[router1_name][router2_name] = cost
            print(f"INFO: Link added from {router1_name} -> {router2_name} with cost {cost}.")
            return True
        else:
            print(f"ERROR: One or both routers not found for link {router1_name}-{router2_name}.")
            return False

    def remove_link(self, router1_name, router2_name):
        """Removes a ONE-WAY (directed) link from router1 to router2."""
        if router1_name in self.adjacency_list and router2_name in self.adjacency_list.get(router1_name, {}):
            del self.adjacency_list[router1_name][router2_name]
            print(f"INFO: Link removed from {router1_name} -> {router2_name}.")
            return True
        else:
            print(f"WARNING: Link from {router1_name} -> {router2_name} not found.")
            return False

    def has_negative_edges(self):
        """Checks if the graph contains any negative edge weights."""
        for neighbors in self.adjacency_list.values():
            for cost in neighbors.values():
                if cost < 0:
                    return True
        return False

    def dijkstra(self, start_router_name):
        """
        Calculates the shortest path from a starting router to all other routers
        using Dijkstra's algorithm. Assumes non-negative edge weights.
        """
        if start_router_name not in self.routers:
            print(f"ERROR: Router {start_router_name} not found.")
            return {}

        # **NEW**: Check for negative edges before running
        if self.has_negative_edges():
            print(f"ERROR: Dijkstra's algorithm cannot run with negative edge weights.")
            return None # Signal failure

        # Priority queue stores tuples of (cost, router_name, path_list)
        pq = [(0, start_router_name, [])]
        min_costs = {router: float('inf') for router in self.routers}
        min_costs[start_router_name] = 0
        shortest_paths = {router: [] for router in self.routers}
        
        # Get the router object to update its routing table
        router = self.routers[start_router_name]
        router.routing_table = {r: (None, float('inf')) for r in self.routers}
        router.routing_table[start_router_name] = (start_router_name, 0)

        while pq:
            cost, current_router_name, path = heapq.heappop(pq)

            # If we've already found a cheaper path, skip this one
            if cost > min_costs[current_router_name]:
                continue
            
            # Add the current router to the path
            path = path + [current_router_name]
            shortest_paths[current_router_name] = path

            # Update the routing table for the starting router
            if len(path) > 1:
                next_hop = path[1] # The first hop after the start
            else:
                next_hop = start_router_name
            router.routing_table[current_router_name] = (next_hop, cost)

            # Explore neighbors
            for neighbor, weight in self.adjacency_list[current_router_name].items():
                # Removed the old check from here, as we check at the start.
                new_cost = cost + weight
                
                # If this is a new, cheaper path to the neighbor
                if new_cost < min_costs[neighbor]:
                    min_costs[neighbor] = new_cost
                    # Push the new, cheaper path onto the priority queue
                    heapq.heappush(pq, (new_cost, neighbor, path))
        
        return shortest_paths

    def bellman_ford(self, start_router_name):
        """
        Calculates the shortest path from a starting router to all other routers
        using the Bellman-Ford algorithm. Can handle negative edge weights.
        """
        if start_router_name not in self.routers:
            print(f"ERROR: Router {start_router_name} not found.")
            return {}

        min_costs = {router: float('inf') for router in self.routers}
        min_costs[start_router_name] = 0
        predecessors = {router: None for router in self.routers}
        
        # Get the router object to update its routing table
        router = self.routers[start_router_name]
        router.routing_table = {r: (None, float('inf')) for r in self.routers}
        router.routing_table[start_router_name] = (start_router_name, 0)

        # Create a list of all edges (u, v, weight)
        edges = []
        for u, neighbors in self.adjacency_list.items():
            for v, weight in neighbors.items():
                edges.append((u, v, weight))
        
        num_routers = len(self.routers)
        
        # Step 1: Relax edges repeatedly (V-1 times)
        for _ in range(num_routers - 1):
            for u, v, weight in edges:
                if min_costs[u] != float('inf') and min_costs[u] + weight < min_costs[v]:
                    min_costs[v] = min_costs[u] + weight
                    predecessors[v] = u
        
        # Step 2: Check for negative weight cycles
        for u, v, weight in edges:
            if min_costs[u] != float('inf') and min_costs[u] + weight < min_costs[v]:
                print(f"ERROR: Negative weight cycle detected involving edge {u}->{v}. Bellman-Ford cannot proceed.")
                # In a real protocol, this node might be marked as unreachable
                return None # Indicate failure due to negative cycle

        # Step 3: Reconstruct paths and update routing table
        shortest_paths = {}
        for dest_name in self.routers:
            if min_costs[dest_name] != float('inf'):
                path = []
                current = dest_name
                while current is not None:
                    # Check for cycles in path reconstruction (if predecessors form a non-negative cycle)
                    if current in path:
                        print(f"Warning: Cycle detected during path reconstruction to {dest_name}.")
                        path.insert(0, current)
                        break
                    path.insert(0, current)
                    current = predecessors[current]
                
                # Only add if the path starts from the source
                if path and path[0] == start_router_name:
                    shortest_paths[dest_name] = path
                    next_hop = path[1] if len(path) > 1 else dest_name
                    router.routing_table[dest_name] = (next_hop, min_costs[dest_name])
                elif dest_name == start_router_name:
                    shortest_paths[start_router_name] = [start_router_name]
                    router.routing_table[start_router_name] = (start_router_name, 0)

        return shortest_paths

    def update_all_routing_tables(self, algorithm='dijkstra'):
        """Convenience method to run the selected update algorithm."""
        if algorithm == 'dijkstra':
            return self.update_all_routing_tables_dijkstra()
        elif algorithm == 'bellman_ford':
            return self.update_all_routing_tables_bellman_ford()
        else:
            print(f"ERROR: Unknown algorithm '{algorithm}'.")
            return False

    def update_all_routing_tables_dijkstra(self):
        """Updates the routing tables for all routers in the network using Dijkstra."""
        # **NEW**: Check for negative edges
        if self.has_negative_edges():
            print("ERROR: Dijkstra's algorithm cannot run with negative edge weights.")
            return False # Signal failure

        print("\n--- Updating all routing tables using Dijkstra's Algorithm ---")
        start_time = time.time()
        for router_name in self.routers:
            self.dijkstra(router_name)
        end_time = time.time()
        print(f"Dijkstra update took: {end_time - start_time:.6f} seconds.")
        print("--- All routing tables updated. ---")
        return True # Signal success

    def update_all_routing_tables_bellman_ford(self):
        """Updates the routing tables for all routers in the network using Bellman-Ford."""
        print("\n--- Updating all routing tables using Bellman-Ford Algorithm ---")
        start_time = time.time()
        for router_name in self.routers:
            if self.bellman_ford(router_name) is None:
                print(f"Update failed for router {router_name} due to negative cycle.")
                return False # Signal failure
        end_time = time.time()
        print(f"Bellman-Ford update took: {end_time - start_time:.6f} seconds.")
        print("--- All routing tables updated. ---")
        return True # Signal success

    def get_routing_tables_str(self):
        """Returns the routing tables as a formatted string."""
        output = ""
        # Sort router names for consistent output
        sorted_router_names = sorted(self.routers.keys())
        for router_name in sorted_router_names:
            router = self.routers[router_name]
            output += f"\n======= Router: {router.name} =======\n"
            output += "Destination | Next Hop | Cost\n"
            output += "---------------------------------\n"
            # Sort destinations for consistent output
            sorted_table = sorted(router.routing_table.items())
            for dest, (next_hop, cost) in sorted_table:
                cost_str = str(cost) if cost != float('inf') else "inf"
                next_hop_str = str(next_hop) if next_hop is not None else "N/A"
                output += f"{dest: <12}| {next_hop_str: <9}| {cost_str}\n"
        return output

    def visualize_network(self, ax, shortest_path=None, cost=None):
        """
        Visualizes the network graph on a given matplotlib Axes object.
        **NEW**: Accepts cost to display it in the title.
        """
        ax.clear()
        # **FIX**: Turn off the axis box *before* drawing and setting title
        ax.set_axis_off() 
        
        # **NEW**: Use a DiGraph (Directed Graph)
        G = nx.DiGraph()
        
        if not self.routers:
            ax.text(0.5, 0.5, "Network is empty. Add routers and links.", 
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Network Topology")
            # ax.set_axis_off() # Moved to top
            return

        for router_name in self.routers:
            G.add_node(router_name)

        edge_labels = {}
        for router1, neighbors in self.adjacency_list.items():
            for router2, cost_val in neighbors.items():
                # DiGraph handles directed edges, no need to check has_edge
                G.add_edge(router1, router2, weight=cost_val)
                edge_labels[(router1, router2)] = cost_val

        # Use a fixed seed for reproducible layouts
        # **NEW**: Added k=1.0 to increase spacing between nodes
        pos = nx.spring_layout(G, seed=42, k=1.0)
        
        # **NEW**: Increased node_size from 1500 to 2000 and font_size from 12 to 14
        nx.draw(G, pos, ax=ax, with_labels=True, node_color='skyblue', node_size=2000, 
                edge_color='gray', width=1.5, font_size=14, font_weight='bold', 
                arrows=True, arrowstyle='-|>')
        
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels, font_color='red')

        if shortest_path:
            # Create a list of edges in the path
            path_edges = list(zip(shortest_path, shortest_path[1:]))
            # Highlight nodes in the path
            nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=shortest_path, node_color='lightgreen', node_size=2000)
            # Highlight edges in the path
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=path_edges, edge_color='green', width=3, arrows=True, arrowstyle='-|>')
            
            # Re-draw labels for path nodes to ensure they are on top
            path_labels = {node: node for node in shortest_path}
            nx.draw_networkx_labels(G, pos, ax=ax, labels=path_labels, font_weight='bold', font_size=14)

            # **NEW**: Add cost to the title
            title = f"Path: {' -> '.join(shortest_path)}"
            if cost is not None:
                title += f" | Minimum Cost: {cost}"
            
            # Wrap title if it's too long
            # **FIX**: Added pad=20 to give space from the top edge
            ax.set_title(textwrap.fill(title, width=40), size=16, pad=20)
        else:
            # **NEW**: Increased title font size to 16
            # **FIX**: Added pad=20 to give space from the top edge
            ax.set_title("Network Topology", size=16, pad=20)
        
        # ax.set_axis_off() # Moved to top

def build_common_topology():
    """Helper function to create a standard network for simulations."""
    network = Network()
    routers_to_add = ['A', 'B', 'C', 'D', 'E', 'F']
    for r in routers_to_add:
        # Suppress print statements for this helper
        router = Router(r)
        network.routers[r] = router
        network.adjacency_list[r] = {}

    # Add links - **NEW**: Must add links in both directions manually
    network.add_link('A', 'B', 4)
    network.add_link('B', 'A', 4)
    network.add_link('A', 'C', 2)
    network.add_link('C', 'A', 2)
    network.add_link('B', 'C', 1)
    network.add_link('C', 'B', 1)
    network.add_link('B', 'D', 5)
    network.add_link('D', 'B', 5)
    network.add_link('C', 'D', 8)
    network.add_link('D', 'C', 8)
    network.add_link('C', 'E', 10)
    network.add_link('E', 'C', 10)
    network.add_link('D', 'E', 2)
    network.add_link('E', 'D', 2)
    network.add_link('D', 'F', 6)
    network.add_link('F', 'D', 6)
    network.add_link('E', 'F', 3)
    network.add_link('F', 'E', 3)
    
    # Reset print function after building
    print("--- Built default topology ---")
    return network

def run_cli(network):
    """Runs the interactive Command-Line Interface."""
    print("\n--- Interactive CLI Mode ---")
    print("Links are now ONE-WAY. Add A->B and B->A for a two-way link.")
    print("Enter 'menu' to see options, 'exit' to quit.")

    while True:
        choice = input("\nEnter command > ").strip().lower()

        if choice == 'exit':
            print("Exiting CLI mode.")
            break
        
        elif choice == 'menu':
            print("\n--- CLI Menu ---")
            print("  [1] Add Router")
            print("  [2] Add Link (One-Way)")
            print("  [3] Remove Router")
            print("  [4] Remove Link (One-Way)")
            print("  [5] Find Shortest Path (Dijkstra)")
            print("  [6] Find Shortest Path (Bellman-Ford)")
            print("  [7] Calculate All Routing Tables (Dijkstra)")
            print("  [8] Calculate All Routing Tables (Bellman-Ford)")
            print("  [9] Show All Routing Tables")
            print("  [menu] Show this menu")
            print("  [exit] Exit CLI")

        elif choice == '1':
            name = input("Enter router name: ").strip().upper()
            if name:
                network.add_router(name)
            else:
                print("ERROR: Name cannot be empty.")

        elif choice == '2':
            r1 = input("Enter FROM router: ").strip().upper()
            r2 = input("Enter TO router: ").strip().upper()
            cost = input(f"Enter cost for link {r1}->{r2}: ").strip()
            network.add_link(r1, r2, cost)

        elif choice == '3':
            name = input("Enter router name to remove: ").strip().upper()
            network.remove_router(name)

        elif choice == '4':
            r1 = input("Enter FROM router: ").strip().upper()
            r2 = input("Enter TO router: ").strip().upper()
            network.remove_link(r1, r2)

        elif choice == '5':
            start = input("Enter start router: ").strip().upper()
            end = input("Enter end router: ").strip().upper()
            if not start or not end:
                print("ERROR: Start and End nodes cannot be empty.")
                continue
            
            paths = network.dijkstra(start)
            
            if paths is None:
                print("ERROR: Dijkstra's algorithm cannot be used with negative edge weights.")
            elif paths and end in paths and paths[end]:
                path_list = paths[end]
                cost = network.routers[start].routing_table.get(end, ('', 'N/A'))[1]
                print(f"--- Dijkstra Path {start} to {end} ---")
                print(f"  Path: {' -> '.join(path_list)}")
                print(f"  Cost: {cost}")
            else:
                print(f"ERROR: No path found from {start} to {end}.")
        
        elif choice == '6':
            start = input("Enter start router: ").strip().upper()
            end = input("Enter end router: ").strip().upper()
            if not start or not end:
                print("ERROR: Start and End nodes cannot be empty.")
                continue

            paths = network.bellman_ford(start)
            
            if paths is None:
                print("ERROR: Calculation failed, likely due to a negative cycle.")
            elif paths and end in paths and paths[end]:
                path_list = paths[end]
                cost = network.routers[start].routing_table.get(end, ('', 'N/A'))[1]
                print(f"--- Bellman-Ford Path {start} to {end} ---")
                print(f"  Path: {' -> '.join(path_list)}")
                print(f"  Cost: {cost}")
            else:
                print(f"ERROR: No path found from {start} to {end}.")

        elif choice == '7':
            if network.update_all_routing_tables_dijkstra():
                print("Dijkstra tables calculated. Enter '9' to show them.")
            else:
                print("ERROR: Dijkstra calculation failed, likely due to negative edges.")

        elif choice == '8':
            if network.update_all_routing_tables_bellman_ford():
                print("Bellman-Ford tables calculated. Enter '9' to show them.")
            else:
                print("ERROR: Bellman-Ford calculation failed, likely due to a negative cycle.")

        elif choice == '9':
            print(network.get_routing_tables_str())

        else:
            print(f"ERROR: Unknown command '{choice}'. Enter 'menu' for options.")


# This block is only executed when the script is run directly
if __name__ == '__main__':
    
    print("--- Running Network Simulator in Command-Line Mode ---")
    
    # Create an empty network
    cli_network = Network()
    
    # Run the interactive CLI
    run_cli(cli_network)

    print("\n--- Command-Line Simulation Complete ---")


