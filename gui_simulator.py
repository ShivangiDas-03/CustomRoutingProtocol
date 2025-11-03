import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from network_simulator import Network, build_common_topology
import textwrap

class RoutingSimulatorGUI:
    """
    The main class for the GUI, built with Tkinter.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Routing Protocol Simulator")
        self.root.geometry("1200x800")  # Set a default size
        
        # --- **NEW**: Configure global font style ---
        style = ttk.Style(self.root)
        
        # Set a larger default font for all widgets
        default_font = ("TkDefaultFont", 11)
        style.configure(".", font=default_font)
        
        # Make Labelframe titles larger and bold
        style.configure("TLabelframe.Label", font=("TkDefaultFont", 12, "bold"))
        # --- End of new style ---

        # Initialize the network object
        self.network = Network()
        
        # Configure the main layout
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a PanedWindow for resizable sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # --- Left: Control Panel ---
        self.control_panel_container = ttk.Frame(self.paned_window, width=350, relief=tk.RIDGE)
        self.paned_window.add(self.control_panel_container, weight=1)
        
        # Add a canvas and scrollbar to the control panel
        self.control_canvas = tk.Canvas(self.control_panel_container)
        self.control_scrollbar = ttk.Scrollbar(self.control_panel_container, orient="vertical", command=self.control_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.control_canvas, padding="10")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.control_canvas.configure(
                scrollregion=self.control_canvas.bbox("all")
            )
        )
        
        self.control_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.control_canvas.configure(yscrollcommand=self.control_scrollbar.set)
        
        self.control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.control_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Right: Visualization and Log ---
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=3)
        
        self.right_paned_window = ttk.PanedWindow(self.right_frame, orient=tk.VERTICAL)
        self.right_paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Top-Right: Visualization
        self.vis_frame = ttk.Frame(self.right_paned_window, relief=tk.SUNKEN)
        self.right_paned_window.add(self.vis_frame, weight=3)
        
        # Bottom-Right: Log
        self.log_frame = ttk.Labelframe(self.right_paned_window, text="Log", padding="5")
        self.log_frame.pack_propagate(False) # Prevent shrinking
        self.right_paned_window.add(self.log_frame, weight=1)
        
        # Create all the control widgets
        self.create_control_panel(self.scrollable_frame)
        
        # Create visualization canvas
        self.fig, self.ax = plt.subplots()
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.vis_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add Matplotlib navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.vis_frame)
        self.toolbar.update()
        
        # Create log text box
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.log_scroll = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Initial drawing
        self.log_message("Simulator started. Add routers and links.")
        self.redraw_network()

    def create_control_panel(self, parent_frame):
        """Populates the left-hand scrollable control panel with widgets."""
        
        # --- Network Presets ---
        preset_frame = ttk.Labelframe(parent_frame, text="Network Presets", padding="10")
        preset_frame.pack(fill=tk.X, expand=True, pady=5)
        
        self.load_default_btn = ttk.Button(preset_frame, text="Load Default Topology", command=self._load_default_topology)
        self.load_default_btn.pack(fill=tk.X, expand=True, pady=2)
        
        self.reset_btn = ttk.Button(preset_frame, text="Reset Network", command=self._reset_network)
        self.reset_btn.pack(fill=tk.X, expand=True, pady=2)

        # --- Manage Routers ---
        router_frame = ttk.Labelframe(parent_frame, text="Manage Routers", padding="10")
        router_frame.pack(fill=tk.X, expand=True, pady=5)
        
        ttk.Label(router_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.router_name_entry = ttk.Entry(router_frame, width=20)
        self.router_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        self.add_router_btn = ttk.Button(router_frame, text="Add Router", command=self._add_router)
        self.add_router_btn.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        self.remove_router_btn = ttk.Button(router_frame, text="Remove Router", command=self._remove_router)
        self.remove_router_btn.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        # --- Manage Links ---
        link_frame = ttk.Labelframe(parent_frame, text="Manage Links", padding="10")
        link_frame.pack(fill=tk.X, expand=True, pady=5)
        
        ttk.Label(link_frame, text="Router 1:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.link_r1_entry = ttk.Entry(link_frame, width=20)
        self.link_r1_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(link_frame, text="Router 2:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.link_r2_entry = ttk.Entry(link_frame, width=20)
        self.link_r2_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(link_frame, text="Cost:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.link_cost_entry = ttk.Entry(link_frame, width=20)
        self.link_cost_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        self.add_link_btn = ttk.Button(link_frame, text="Add/Update Link", command=self._add_link)
        self.add_link_btn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        self.remove_link_btn = ttk.Button(link_frame, text="Remove Link", command=self._remove_link)
        self.remove_link_btn.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

        # --- Algorithm Selection ---
        algo_frame = ttk.Labelframe(parent_frame, text="Algorithm", padding="10")
        algo_frame.pack(fill=tk.X, expand=True, pady=5)
        
        self.algo_var = tk.StringVar(value="dijkstra")
        
        self.dijkstra_radio = ttk.Radiobutton(algo_frame, text="Dijkstra (No negative edges)", variable=self.algo_var, value="dijkstra")
        self.dijkstra_radio.pack(anchor=tk.W, pady=2)
        
        self.bellman_radio = ttk.Radiobutton(algo_frame, text="Bellman-Ford (Handles negatives)", variable=self.algo_var, value="bellman_ford")
        self.bellman_radio.pack(anchor=tk.W, pady=2)

        # --- Find Shortest Path ---
        path_frame = ttk.Labelframe(parent_frame, text="Find Shortest Path", padding="10")
        path_frame.pack(fill=tk.X, expand=True, pady=5)
        
        ttk.Label(path_frame, text="Start:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.path_start_entry = ttk.Entry(path_frame, width=20)
        self.path_start_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(path_frame, text="End:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.path_end_entry = ttk.Entry(path_frame, width=20)
        self.path_end_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        self.find_path_btn = ttk.Button(path_frame, text="Find and Highlight Path", command=self._find_and_highlight_path)
        self.find_path_btn.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)

        # --- Actions ---
        action_frame = ttk.Labelframe(parent_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, expand=True, pady=5)
        
        self.calc_tables_btn = ttk.Button(action_frame, text="Calculate & Show Routing Tables", command=self._calculate_and_show_tables)
        self.calc_tables_btn.pack(fill=tk.X, expand=True, pady=2)
        
        self.clear_log_btn = ttk.Button(action_frame, text="Clear Log", command=self._clear_log)
        self.clear_log_btn.pack(fill=tk.X, expand=True, pady=2)

    # --- Event Handler Methods ---
    
    def log_message(self, msg):
        """Adds a message to the log box."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END) # Auto-scroll
        self.log_text.config(state=tk.DISABLED)

    def redraw_network(self, shortest_path=None, cost=None):
        """Clears and redraws the network visualization."""
        # **NEW**: Pass the cost to the visualization function
        self.network.visualize_network(self.ax, shortest_path, cost)
        self.canvas.draw()

    def _add_router(self):
        name = self.router_name_entry.get().strip().upper()
        if not name:
            messagebox.showwarning("Input Error", "Router name cannot be empty.")
            return
        
        if self.network.add_router(name):
            self.log_message(f"Router {name} added.")
            self.router_name_entry.delete(0, tk.END)
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Router {name} already exists.")

    def _remove_router(self):
        name = self.router_name_entry.get().strip().upper()
        if not name:
            messagebox.showwarning("Input Error", "Router name cannot be empty.")
            return

        if self.network.remove_router(name):
            self.log_message(f"Router {name} removed.")
            self.router_name_entry.delete(0, tk.END)
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Router {name} not found.")

    def _add_link(self):
        r1 = self.link_r1_entry.get().strip().upper()
        r2 = self.link_r2_entry.get().strip().upper()
        cost_str = self.link_cost_entry.get().strip()

        if not all([r1, r2, cost_str]):
            messagebox.showwarning("Input Error", "All link fields (Router 1, Router 2, Cost) are required.")
            return
        
        if self.network.add_link(r1, r2, cost_str):
            self.log_message(f"Link {r1}-{r2} (Cost: {cost_str}) added.")
            self.link_r1_entry.delete(0, tk.END)
            self.link_r2_entry.delete(0, tk.END)
            self.link_cost_entry.delete(0, tk.END)
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Could not add link. Check that routers exist and cost is an integer.")

    def _remove_link(self):
        r1 = self.link_r1_entry.get().strip().upper()
        r2 = self.link_r2_entry.get().strip().upper()

        if not all([r1, r2]):
            messagebox.showwarning("Input Error", "Router 1 and Router 2 names are required.")
            return

        if self.network.remove_link(r1, r2):
            self.log_message(f"Link {r1}-{r2} removed.")
            self.link_r1_entry.delete(0, tk.END)
            self.link_r2_entry.delete(0, tk.END)
            self.link_cost_entry.delete(0, tk.END)
            self.redraw_network()
        else:
            messagebox.showerror("Error", f"Link {r1} -> {r2} not found.")

    def _find_and_highlight_path(self):
        start_node = self.path_start_entry.get().strip().upper()
        end_node = self.path_end_entry.get().strip().upper()
        algorithm = self.algo_var.get()

        if not all([start_node, end_node]):
            messagebox.showwarning("Input Error", "Start and End routers are required.")
            return

        try:
            paths = None
            if algorithm == 'dijkstra':
                paths = self.network.dijkstra(start_node)
                if paths is None:
                    # This is our new failure signal from dijkstra
                    messagebox.showerror("Algorithm Error", "Dijkstra's algorithm cannot be used with negative edge weights.")
                    self.redraw_network()
                    return
            else:
                paths = self.network.bellman_ford(start_node)
                if paths is None:
                    # This signals a negative cycle from bellman_ford
                    messagebox.showerror("Algorithm Error", "Bellman-Ford failed. A negative weight cycle was detected.")
                    self.redraw_network()
                    return
            
            # Check if a path to the specific end_node exists
            if not paths or end_node not in paths or not paths[end_node]:
                raise KeyError
            
            shortest_path = paths[end_node]
            cost = self.network.routers[start_node].routing_table.get(end_node, ('', 'N/A'))[1]
            
            # **NEW**: Pass the cost to redraw_network
            self.redraw_network(shortest_path=shortest_path, cost=cost)
            self.log_message(f"Path ({algorithm}): {' -> '.join(shortest_path)} | Cost: {cost}")

        except KeyError:
            messagebox.showinfo("Path Error", f"No path found from {start_node} to {end_node}.")
            self.redraw_network() # Redraw without a path
        except Exception as e:
            messagebox.showerror("An Error Occurred", f"An unexpected error occurred: {e}")
            self.redraw_network()


    def _calculate_and_show_tables(self):
        algorithm = self.algo_var.get()
        
        try:
            success = False
            if algorithm == 'dijkstra':
                success = self.network.update_all_routing_tables_dijkstra()
                if not success:
                    messagebox.showerror("Algorithm Error", "Dijkstra's algorithm cannot be used with negative edge weights.")
                    return
            else:
                success = self.network.update_all_routing_tables_bellman_ford()
                if not success:
                    messagebox.showerror("Algorithm Error", "Bellman-Ford failed. A negative weight cycle was detected.")
                    return
            
            # If successful, show the tables
            self.log_message(f"--- Calculated All Routing Tables ({algorithm}) ---")
            tables_str = self.network.get_routing_tables_str()
            self.log_message(tables_str)
            
        except Exception as e:
            messagebox.showerror("An Error Occurred", f"An unexpected error occurred: {e}")

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_message("Log cleared.")

    def _load_default_topology(self):
        self.network = build_common_topology()
        self.log_message("Loaded default network topology.")
        self.redraw_network()

    def _reset_network(self):
        self.network = Network()
        self.log_message("Network has been reset.")
        self.redraw_network()

if __name__ == '__main__':
    root = tk.Tk()
    app = RoutingSimulatorGUI(root)
    root.mainloop()


