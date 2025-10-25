import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Text
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import the network simulation classes from the other file
from network_simulator import Network, build_common_topology

class RoutingSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Routing Protocol Simulator")
        self.geometry("1200x800")

        # Initialize the network
        self.network = Network()

        # --- Main Layout ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # --- Control Panel (Left Side) ---
        self.create_control_panel(main_frame)

        # --- Visualization Area (Right Side) ---
        graph_frame = ttk.LabelFrame(main_frame, text="Network Visualization", padding="10")
        graph_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial draw
        self.redraw_network()

    def create_control_panel(self, parent):
        """Creates the left-side panel with all user controls."""
        control_frame = ttk.Frame(parent, width=350)
        control_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        control_frame.pack_propagate(False) # Prevent frame from shrinking

        # --- Add/Remove Router ---
        router_frame = ttk.LabelFrame(control_frame, text="Manage Routers", padding="10")
        router_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(router_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.router_name_entry = ttk.Entry(router_frame)
        self.router_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        add_router_btn = ttk.Button(router_frame, text="Add Router", command=self.add_router)
        add_router_btn.grid(row=1, column=0, padx=5, pady=5)
        
        remove_router_btn = ttk.Button(router_frame, text="Remove Router", command=self.remove_router)
        remove_router_btn.grid(row=1, column=1, padx=5, pady=5)

        # --- Add/Remove Link ---
        link_frame = ttk.LabelFrame(control_frame, text="Manage Links", padding="10")
        link_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(link_frame, text="Router 1:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.link_r1_entry = ttk.Entry(link_frame)
        self.link_r1_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(link_frame, text="Router 2:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.link_r2_entry = ttk.Entry(link_frame)
        self.link_r2_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(link_frame, text="Cost:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.link_cost_entry = ttk.Entry(link_frame)
        self.link_cost_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        add_link_btn = ttk.Button(link_frame, text="Add Link", command=self.add_link)
        add_link_btn.grid(row=3, column=0, pady=5, padx=5)
        
        remove_link_btn = ttk.Button(link_frame, text="Remove Link", command=self.remove_link)
        remove_link_btn.grid(row=3, column=1, pady=5, padx=5)

        # --- Algorithm Selection ---
        algo_frame = ttk.LabelFrame(control_frame, text="Algorithm", padding="10")
        algo_frame.pack(fill=tk.X, pady=5)
        
        self.algo_var = tk.StringVar(value="dijkstra")
        dijkstra_radio = ttk.Radiobutton(algo_frame, text="Dijkstra", variable=self.algo_var, value="dijkstra")
        dijkstra_radio.pack(anchor=tk.W, padx=5)
        bf_radio = ttk.Radiobutton(algo_frame, text="Bellman-Ford", variable=self.algo_var, value="bellman_ford")
        bf_radio.pack(anchor=tk.W, padx=5)

        # --- Actions ---
        action_frame = ttk.LabelFrame(control_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)

        update_tables_btn = ttk.Button(action_frame, text="Calculate & Show Routing Tables", command=self.show_routing_tables)
        update_tables_btn.pack(fill=tk.X, pady=5, padx=5)

        # --- Shortest Path ---
        path_frame = ttk.LabelFrame(control_frame, text="Find Shortest Path", padding="10")
        path_frame.pack(fill=tk.X, pady=5)
        path_frame.grid_columnconfigure(1, weight=1) # Allow entry to expand
        path_frame.grid_columnconfigure(3, weight=1) # Allow entry to expand

        ttk.Label(path_frame, text="Start:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.path_start_entry = ttk.Entry(path_frame, width=10)
        self.path_start_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(path_frame, text="End:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.path_end_entry = ttk.Entry(path_frame, width=10)
        self.path_end_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        find_path_btn = ttk.Button(path_frame, text="Find and Highlight Path", command=self.find_and_show_path)
        # *** THE FIX IS HERE *** Changed .pack() to .grid()
        find_path_btn.grid(row=1, column=0, columnspan=4, pady=10, sticky="ew")

        # --- Presets and Reset ---
        preset_frame = ttk.LabelFrame(control_frame, text="Network Presets", padding="10")
        preset_frame.pack(fill=tk.X, pady=5)

        load_preset_btn = ttk.Button(preset_frame, text="Load Default Topology", command=self.load_preset)
        load_preset_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        reset_btn = ttk.Button(preset_frame, text="Reset Network", command=self.reset_network)
        reset_btn.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

    def redraw_network(self, shortest_path=None):
        """Clears and redraws the network graph on the canvas."""
        self.network.visualize_network(self.ax, shortest_path)
        self.canvas.draw()

    def add_router(self):
        name = self.router_name_entry.get().strip().upper()
        if not name:
            messagebox.showerror("Error", "Router name cannot be empty.")
            return
        if self.network.add_router(name):
            self.redraw_network()
            self.router_name_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", f"Router '{name}' already exists.")

    def remove_router(self):
        name = self.router_name_entry.get().strip().upper()
        if not name:
            messagebox.showerror("Error", "Router name cannot be empty.")
            return
        if self.network.remove_router(name):
            self.redraw_network()
            self.router_name_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", f"Router '{name}' not found.")
            
    def add_link(self):
        r1 = self.link_r1_entry.get().strip().upper()
        r2 = self.link_r2_entry.get().strip().upper()
        cost_str = self.link_cost_entry.get().strip()

        if not all([r1, r2, cost_str]):
            messagebox.showerror("Error", "All link fields are required.")
            return
        try:
            cost = int(cost_str)
        except ValueError:
            messagebox.showerror("Error", "Cost must be an integer.")
            return
        
        if self.network.add_link(r1, r2, cost):
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Could not add link. Check if routers '{r1}' and '{r2}' exist.")
    
    def remove_link(self):
        r1 = self.link_r1_entry.get().strip().upper()
        r2 = self.link_r2_entry.get().strip().upper()
        if not all([r1, r2]):
            messagebox.showerror("Error", "Router 1 and Router 2 names are required.")
            return
        
        if self.network.remove_link(r1, r2):
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Link between '{r1}' and '{r2}' not found.")

    def show_routing_tables(self):
        if not self.network.routers:
            messagebox.showinfo("Info", "Network is empty. Nothing to calculate.")
            return
            
        algo = self.algo_var.get()
        self.network.update_all_routing_tables(algo)
        
        # Display in a new window
        table_window = Toplevel(self)
        table_window.title(f"Routing Tables ({algo.replace('_', ' ').title()})")
        table_window.geometry("400x500")
        
        text_widget = Text(table_window, wrap="word", font=("Courier New", 10))
        text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        table_str = self.network.get_routing_tables_str()
        text_widget.insert(tk.END, table_str)
        text_widget.config(state="disabled") # Make it read-only
    
    def find_and_show_path(self):
        start_node = self.path_start_entry.get().strip().upper()
        end_node = self.path_end_entry.get().strip().upper()

        if not all([start_node, end_node]):
            messagebox.showerror("Error", "Start and End nodes are required.")
            return
        
        if start_node not in self.network.routers or end_node not in self.network.routers:
            messagebox.showerror("Error", "One or both routers not found in the network.")
            return
            
        algo = self.algo_var.get()
        
        if algo == 'dijkstra':
            all_paths = self.network.dijkstra(start_node)
        else:
            all_paths = self.network.bellman_ford(start_node)

        if all_paths and end_node in all_paths and all_paths[end_node]:
            path = all_paths[end_node]
            self.redraw_network(shortest_path=path)
            messagebox.showinfo("Path Found", f"Shortest path from {start_node} to {end_node}:\n{' -> '.join(path)}")
        else:
            self.redraw_network() # Redraw without path
            messagebox.showwarning("No Path", f"No path found from {start_node} to {end_node}.")

    def load_preset(self):
        self.network = build_common_topology()
        self.redraw_network()
        messagebox.showinfo("Success", "Default network topology has been loaded.")

    def reset_network(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the entire network?"):
            self.network = Network()
            self.redraw_network()

if __name__ == '__main__':
    app = RoutingSimulatorGUI()
    app.mainloop()
