import re
import tkinter as tk
from tkinter import ttk
from tkinter import *


class SidebarWindow:
    def __init__(self, parent, config, edit_screen, settings):
        self.parent = parent
        self.config = config
        self.settings = settings
        self.edit_screen = edit_screen
        self.sidebar = tk.Toplevel(self.parent)
        self.sidebar.protocol("WM_DELETE_WINDOW", self.on_close)
        self.sidebar.title("Sidebar Window")
        self.scrollable_sidebar = ScrollableSidebar(
            self.sidebar, self.config, self.edit_screen, settings)
        self.scrollable_sidebar.set_tree_position()

    def on_close(self):
        self.sidebar.destroy()
        self.scrollable_sidebar.destroy()
        self.parent.sidebar_window = None


class ScrollableSidebar(tk.Frame):
    def __init__(self, parent, config, edit_screen, settings):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.config = config
        self.edit_screen = edit_screen
        self.cells = self.config.config_data[self.settings.series]['cells']

        # Create a Canvas widget
        self.canvas = tk.Canvas(self)
        self.canvas.grid_rowconfigure(1, weight=1)
        self.canvas.grid_columnconfigure(1, weight=1)
        self.canvas.grid(sticky='nsew')

        # Create a Frame within the Canvas
        self.frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame)

        # Configure the Treeview to display columns
        # Configure the Treeview to display columns
        self.tree = ttk.Treeview(self.frame, cursor='hand2')
        self.tree["columns"] = ("name",)
        self.tree.heading("#1", text="Name")
        self.tree['show'] = 'headings'
        self.tree.column("name", width=350)
        self.tree.grid()  # Use grid with sticky option
        self.frame.grid_rowconfigure(0, weight=1)  # Make the row expand
        self.frame.grid_columnconfigure(0, weight=1)  # Make the column expand
        self.frame.grid(sticky='nsew')
        # Add rows to the Treeview
        self.add_rows(self.cells)
        self.grid_rowconfigure(0, weight=1)  # Make the row expand
        self.grid_columnconfigure(0, weight=1)  # Make the column expand
        self.grid(sticky='nsew')

        # Bind the canvas to handle resizing
        self.frame.bind("<Configure>", self.on_frame_configure)

    def set_tree_position(self, row_index = None):
        if not row_index:
            row_index = self.edit_screen.current_cell_index
        row_ids = self.tree.get_children()
        if row_index < len(row_ids):
            target_row_id = row_ids[row_index]
            # Scroll the Treeview to the given row ID
            self.tree.see(target_row_id)
    def get_treeview_row_count(self):
        # Get the list of item IDs (rows) in the Treeview
        row_ids = self.tree.get_children()
        return len(row_ids)
    def add_rows(self, cells):
        for index, cell in enumerate(cells):
            # Insert each cell's name into the Treeview
            # You can modify this to display other fields if needed
            self.tree.insert("", index, values=(cell["Name"],))

            # Bind a click event to handle cell selection
            self.tree.bind("<Button-1>", self.on_cell_click)

    def on_frame_configure(self, event):
        # Update the scroll region when the frame size changes
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_cell_click(self, event):
        row_id = self.tree.identify_row(event.y)
        row_index = self.tree.index(row_id)
        if row_index != self.settings.current_cell_index:
            self.edit_screen.current_cell_index = row_index
            self.edit_screen.set_cell()


class EditScreen(ttk.Frame):
    def __init__(self, parent, settings, config, methods):
        super().__init__(parent)
        self.continue_button = None
        self.bottom_buttons_frame = None
        self.save_config = None
        self.back_button = None
        self.sidebar_button = None
        self.regex = {}
        self.remove_dates = {}
        self.auto_add = {}
        self.parent = parent
        self.config = config
        self.options = self.config.options
        self.methods = methods
        self.settings = settings
        self.settings.reload_config()
        self.series = self.config.current_series
        self.cells = self.config.config_data[self.series]["cells"]
        self.series_data = self.config.config_data[self.series]
        self.current_cell_index = self.settings.current_cell_index
        self.current_cell = self.cells[self.current_cell_index]
        self.grid_rowconfigure((0,), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        self.create_widgets()

    def set_cell(self):
        self.methods.destroy_widgets(self)
        self.current_cell = self.cells[self.current_cell_index]
        self.create_widgets()

    def show_sidebar(self):
        if self.parent.main_x:
            self.parent.create_sidebar()

    def create_widgets(self):
        self.methods.destroy_widgets(self)
        ttk.Label(
            self, text=self.config.current_series, font="Helvetica 16 bold").grid(row=0)
        row = 0
        if self.settings.display_only:
            for d in self.settings.display_only:
                row += 1
                ttk.Label(self, text=str(self.current_cell[d])).grid(row=row)
        if self.settings.edit_and_display:
            for ed in self.settings.edit_and_display:
                if ed not in self.regex or ed not in self.remove_dates:  
                    self.regex[ed] = tk.BooleanVar()
                    self.remove_dates[ed] = tk.BooleanVar()
                row += 1
                EditAndDisplay(self, ed, self.current_cell,
                               True, self.methods).grid(row=row)
        if self.settings.separated_options:
            for s in self.settings.separated_options:
                if s not in self.auto_add:
                    self.auto_add[s] = tk.BooleanVar()
                row += 1
                SeparatedFrame(self, s, self.current_cell,
                               self.series_data).grid(row=row)
        if self.settings.edit_only:
            for e in self.settings.edit_only:
                if e not in self.regex or e not in self.remove_dates[e]:  
                    self.regex[e] = tk.BooleanVar()
                    self.remove_dates[e] = tk.BooleanVar()
                row += 1
                EditAndDisplay(self, e, self.current_cell,
                               False).grid(row=row)
        row += 1
        self.bottom_buttons_frame = ttk.Frame(self)
        self.bottom_buttons_frame.grid_rowconfigure(0, weight=1)
        self.bottom_buttons_frame.grid_columnconfigure(
            (0, 1, 2, 3, 4), weight=1)
        self.bottom_buttons_frame.grid(row=row, column=0)
        self.continue_button = ttk.Button(
            self, text="Continue", command=lambda: self.parent.switch_frames(6))
        self.continue_button.grid(row=row+1, column=0)

        self.back_button = ttk.Button(
            self, text="Back", command=lambda: self.parent.switch_frames(3))
        self.back_button.grid(row=row+2, column=0)
        ttk.Button(self.bottom_buttons_frame, text="Previous",
                   command=self.on_back, width=15, cursor="hand2").grid(row=0, column=0, padx=5)
        ttk.Button(self.bottom_buttons_frame, text="Save",
                   command=self.on_save, width=15, cursor="hand2").grid(row=0, column=1, padx=5)
        ttk.Button(self.bottom_buttons_frame, text="Next",
                   command=self.on_next, width=15, cursor="hand2").grid(row=0, column=2, padx=5)
        self.methods.pad_widgets(self)
        self.sidebar_button = ttk.Button(
            self, text='show all', command=self.show_sidebar, width=10, cursor="hand2")
        self.sidebar_button.place(
            rely=0, relx=1, x=-5, y=5, anchor='ne')
        self.save_config = ttk.Button(
            self, text='Save Config', command=self.on_save_config, width=10, cursor="hand2")
        self.save_config.place(
            rely=1.0, relx=1.0, x=-5, y=-5, anchor='se')

    def on_save(self):
        for child in self.winfo_children():
            if isinstance(child, EditAndDisplay):
                entry_value = child.get_entry_value()
                entry_field = child.get_entry_field()  # Add this method to EditAndDisplay
                self.current_cell[f"Updated_{entry_field}"] = entry_value
        self.current_cell_index = self.current_cell_index + 1
        self.set_cell()

    def on_save_config(self):
        self.config.write_cells()
        self.save_config.configure(text='Saved')

    def on_next(self):
        if self.current_cell_index == len(self.cells) - 1:
            self.current_cell_index = 0
            self.set_cell()
        else:
            self.current_cell_index = self.current_cell_index + 1
            self.set_cell()

    def on_back(self):
        if self.current_cell_index > 0:
            self.current_cell_index = self.current_cell_index - 1
            self.set_cell()
        else:
            self.current_cell_index = len(self.cells) - 1
            self.set_cell()

# Frame for any field for editing that isn't "|" separated.


class EditAndDisplay(ttk.Frame):
    def __init__(self, parent, field, current_cell, display, methods):
        super().__init__(parent)
        self.parent = parent
        self.field = field
        self.methods = methods
        self.entry_var = tk.StringVar()
        self.current_cell = current_cell
        self.updated = current_cell[f"Updated_{self.field}"] or None
        self.row = 0
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_configure(sticky='nsew')

        # If the the display option was chosen
        if display:
            self.label = ttk.Label(
                self, text=current_cell[self.field])
            self.label.grid(row=self.row, columnspan=4)
            self.row += 1
        self.entry = ttk.Entry(self, textvariable=self.entry_var, width=75)

        # Fill the entry with relevant text.
        if not self.updated:
            self.on_toggle()
        else:
            self.entry.insert(0, self.updated)
        self.toggle_frame = ttk.Frame(self)
        self.toggle_frame.grid_columnconfigure((0,1), weight=0)
        self.toggle_frame.grid(row=self.row, column=2, sticky='w', padx=10)
        self.toggle_re = ttk.Checkbutton(self.toggle_frame, text='Clean Text',
                                         variable=self.parent.regex[self.field], onvalue=True, offvalue=False, command=self.on_toggle)
        self.toggle_re.grid(row=0, column=0, sticky='w')
        self.toggle_date = ttk.Checkbutton(self.toggle_frame, text='Remove Dates',
                                         variable=self.parent.remove_dates[self.field], onvalue=True, offvalue=False, command=self.on_toggle)
        self.toggle_date.grid(row=0, column=1, sticky='w')
        self.entry.grid(column=1, row=self.row, sticky='e', padx=10)
        self.methods.pad_widgets(self)

    def get_entry_value(self):
        return self.entry_var.get()

    def get_entry_field(self):
        return self.field

    def on_toggle(self):
        self.entry.delete(0, END)
        date_pattern = r'\d+(!?\w\W)'
        temp_date = r'^([^\s]+)'
        no_date = re.sub(temp_date, '',
                         self.current_cell[self.field]).strip()
        clean = re.sub(r'([^a-zA-Z\s]+?)', '',
                       self.current_cell[self.field]).strip()
        if self.parent.regex[self.field].get():
            self.entry.insert(
                0, clean)
        elif self.parent.remove_dates[self.field].get():
            self.entry.insert(
                0, no_date)
        else:
            self.entry.insert(
                0, self.current_cell[self.field].strip())


# Frame for fields separated by "|" in the jellyfin database ex: Genres "Horror|Comedy"
# Displays buttons for individual fields with the ability to add new ones.
class SeparatedFrame(ttk.Frame):
    def __init__(self, parent, field, current_cell, series_data):
        super().__init__(parent)
        self.parent = parent
        self.field = field
        self.series_data = series_data
        self.current_cell = current_cell
        if self.series_data[self.field]:
            self.options = self.series_data[self.field]
        else:
            self.options = []
        self.option_buttons = {}
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8), weight=1)
        self.grid_rowconfigure((0,), weight=1)

        self.current_options = self.current_cell[field] + self.current_cell[f"Updated_{field}"]

        self.list_options = None
        self.update_list()
        # Calculate the number of rows needed based on the number of options
        rows_needed = (len(self.options) + 8) // 9
        # Instantiate and set style of options as buttons
        for index, option in enumerate(self.options):
            button = ttk.Button(
                self, text=option, command=lambda t=option: self.toggle_option(t), width=8, cursor="hand2")
            # Auto relevant fields based on Name of current episode.
            if self.parent.auto_add[self.field].get() and (option.lower() in self.current_cell["Name"].lower()):
                    if option not in self.list_options:
                        self.list_options.append(option)
                        self.post_options()

            if option in self.list_options:
                button.configure(style='Option.TButton')
            button.bind("<Enter>", self.show_tooltip)
            button.bind("<Leave>", self.hide_tooltip)
            # Compute the row and column for each button
            row = index // 9
            col = index % 9
            button.grid(row=row, column=col, padx=5, pady=5)
            self.option_buttons[option] = button

        self.new_option_entry = ttk.Entry(self)
        self.auto_add = ttk.Checkbutton(self, text="Auto Add", variable=self.parent.auto_add[self.field], onvalue=True, offvalue=False, command=self.on_auto_toggle)
        self.new_option_entry.bind("<Return>", self.add_option)
        self.add_button = ttk.Button(
            self, text=f"Add {field}", command=self.add_option, cursor="hand2")
        self.add_button.grid(row=rows_needed + 2, column=4, padx=5, pady=5)
        self.auto_add.grid(row=rows_needed + 2, column=5, padx=5, pady=5, sticky='w')
        self.new_option_entry.grid(
            row=rows_needed + 1, column=0, columnspan=9, padx=5, pady=10)
        self.grid_configure(pady=20, sticky='nsew')
        self.tooltip = None

    def add_option(self, event=None):
        new_option = self.new_option_entry.get()
        if new_option:
            # Append the new tag to the options array
            self.options.append(new_option)
            # Create a new button for the new option and add it to the grid
            index = len(self.options) - 1
            button = ttk.Button(
                self, text=new_option, command=lambda t=new_option: self.toggle_option(t), width=8, cursor="hand2")
            row = (index // 9)
            col = index % 9
            button.bind("<Enter>", self.show_tooltip)
            button.bind("<Leave>", self.hide_tooltip)
            button.grid(row=row, column=col, padx=5, pady=5)
            self.option_buttons[new_option] = button

            # Clear the text box
            self.new_option_entry.delete(0, tk.END)
            self.parent.series_data[self.field] = self.options
            self.parent.create_widgets()

    # Handle button click of a field.
    def toggle_option(self, toggle_option):
        self.update_list()
        if toggle_option in self.list_options:
            self.list_options.remove(toggle_option)
        else:
            self.list_options.append(toggle_option)

        # Call methods to update Frame 
        self.post_options()
        self.update_style()
    
    # If a field is in the episodes Name
    def on_auto_toggle(self):
        self.update_list()
        if self.parent.auto_add[self.field].get():
            for option in self.options:
                if option.lower() in self.current_cell["Name"].lower():
                    if option not in self.list_options:
                        self.list_options.append(option)
                

        # Call methods to update Frame 
            self.post_options()
            self.update_style()
     
    # Updates the list of options used for styling etc.
    def update_list(self):
        self.list_options = self.current_options.split(
            '|') if '|' in self.current_options else [self.current_options] if self.current_options else []

    # Writes updated fields to the current cell
    def post_options(self):
        string = '|'.join(self.list_options) if (len(self.list_options) > 1) else self.list_options[0] if (len(self.list_options) == 1) else ""
        self.parent.current_cell[f"Updated_{self.field}"] = string
        self.current_options = self.parent.current_cell[f"Updated_{self.field}"]        

    # Set the style of buttons currently selected.
    def update_style(self):
        for option, button in self.option_buttons.items():
            if option in self.list_options:
                button.configure(style='Option.TButton')
            else:
                button.configure(style='TButton')

    # Hover to show full text of an option if the text is overflown.
    def show_tooltip(self, event):
        # Get the widget that triggered the event (the button in this case)
        button = event.widget

        # Retrieve the full text from the button
        full_text = button["text"]

        x, y, _, _ = button.bbox("insert")
        x += button.winfo_rootx() + 25
        y += button.winfo_rooty() + 25

        # Create and display the tooltip
        self.tooltip = tk.Toplevel(button)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=full_text,
                         relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event):
        self.tooltip.destroy()
