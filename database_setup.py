import re
import tkinter as tk
from tkinter import ttk
from global_main import OptionsSchema


# Screen to customize and select options for your config.
class SelectFields(ttk.Frame):
    def __init__(self, parent, methods, config, database):
        super().__init__(parent)
        self.parent = parent
        self.methods = methods
        self.config = config
        self.options = self.config.options
        self.database = database
        # instantiate tk components/variables
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid_rowconfigure((0,), weight=0)
        self.main_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.main_frame.grid(sticky='nsew')
        self.options_tree = None
        self.left_button = None
        self.right_button = None
        self.button_frame = None
        self.text_frame = None
        self.combo_popup = None
        self.create_widgets()
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        self.methods.pad_widgets(self)

    def create_widgets(self):
        self.methods.destroy_widgets(self.main_frame)
        self.create_options()
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.button_frame.grid(sticky='nsew', row=2, column=1)
        self.text_frame = ttk.Frame(self.main_frame)
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure((0,), weight=1)
        self.text_frame.grid(sticky='nsew', row=0, column=1)
        ttk.Label(self.text_frame, text="Options", font='bold').grid(
            row=0)
        ttk.Label(self.text_frame,
                  text='Select the fields you would like to modify or display.').grid(row=1)
        ttk.Label(self.text_frame,
                  text='Double click to edit or add a new field.').grid(row=2)
        ttk.Label(self.text_frame,
                  text='Make sure you understand the Jellyfin data structure if adding your own fields!',
                  style='Red.TLabel').grid(row=3)
        self.methods.pad_widgets_light(self.text_frame)
        self.left_button = ttk.Button(
            self.button_frame, text="Add", command=self.add_option)
        self.left_button.grid(column=1, row=0)
        self.right_button = ttk.Button(
            self.button_frame, text="Remove", command=self.remove_option)
        self.right_button.grid(column=2, row=0)
        ttk.Button(self.main_frame, text="Back",
                   command=lambda: self.parent.switch_frames(1)).grid(row=5, column=1)
        ttk.Button(self.main_frame, text='Continue',
                   command=self.on_continue).grid(row=4, column=1)
        self.methods.pad_widgets(self.main_frame)
        self.methods.set_cursor(self)
        self.methods.set_cursor(self.main_frame)
        self.methods.set_cursor(self.button_frame)

    def on_continue(self):
        # Call config methods
        self.config.create_series()
        self.config.create_cells()
        self.config.verify()
        self.parent.switch_frames(4)

    # create the treeview for options.
    def create_options(self):
        self.options_tree = ttk.Treeview(
            self.main_frame, columns=('a', 'b', 'c'))
        self.options_tree.heading('a', text="Target Field")
        self.options_tree.heading('b', text="Modify?")
        self.options_tree.heading('c', text="Display Original?")
        self.options_tree['show'] = 'headings'
        self.options_tree.grid(row=1, column=1, sticky='nsew')
        self.options_tree.bind("<Double-1>", self.on_double_click)
        for option in self.options:
            self.options_tree.insert("", "end", values=(
                option.key, str(option.edit), str(option.display)))

    def reload_tree(self):
        for item in self.options_tree.get_children():
            self.options_tree.delete(item)
        for option in self.options:
            self.options_tree.insert("", "end", values=(
                option.key, str(option.edit), str(option.display)))

    # create a new option
    def add_option(self):
        self.options_tree.insert("", "end", values=())
        new_options = ['Target Field', 'Modify?', 'Display Original?']
        row_id = self.options_tree.get_children()[-1]
        for index, option in enumerate(new_options):
            column = f'#{index + 1}'
            x, y, width, height = self.options_tree.bbox(row_id, column)
            self.combo_popup = ComboPopup(
                self.options_tree, row_id, None, index, None, self.database)
            self.combo_popup.place(x=x, y=y)
            self.left_button.configure(text="save", command=self.on_add_save)
            self.right_button.configure(text="undo", command=self.on_add_undo)

    # destroy the popups for options
    def on_add_undo(self):
        self.methods.destroy_widgets(self.options_tree)
        self.create_widgets()

    # save a new option
    def on_add_save(self):
        key = None
        edit = None
        display = None
        data_type = None
        bools = [True, False]
        for index, entry in enumerate(self.options_tree.winfo_children()):
            current = entry.current()
            if index == 0:  # Key column
                key = self.database.keys[current]
                data_type = self.database.columns[current]['data_type']  # Get the data_type from the database class
            if index == 1:  # Edit column
                edit = bools[current]
            if index == 2:  # Display column
                display = bools[current]
        self.options.append(OptionsSchema(key, edit, display, data_type))
        self.create_widgets()

    # remove an option
    def remove_option(self):
        target = self.options_tree.focus()
        target_index = self.options_tree.index(target)
        if target_index == 0:
            tk.messagebox.showerror("Error!", "The name option is needed.")
            return
        del self.options[target_index]
        self.create_widgets()

    # function to create combo popup on double-click on treeview
    def on_double_click(self, event):
        self.methods.destroy_widgets(self.options_tree)
        # identify targets
        row_id = self.options_tree.identify_row(event.y)
        column = self.options_tree.identify_column(event.x)
        row_index = self.options_tree.index(row_id)
        column_index = int(re.findall('\d+', column)[0]) - 1
        if row_index == 0 and column_index == 0:
            tk.messagebox.showerror("Error!", "The name option is needed.")
            return
        # get column position info
        x, y, width, height = self.options_tree.bbox(row_id, column)
        value = self.options_tree.item(row_id)['values'][int(column_index)]

        def update_option_value(new_value, cb_index):
            if column_index == 1:  # Edit column
                self.options[row_index].edit = new_value
            elif column_index == 2:  # Display column
                self.options[row_index].display = new_value
            else:  # Key column
                self.options[row_index].key = new_value
                # Also update the data_type
                self.options[row_index].data_type = self.database.columns[cb_index]['data_type']
            self.reload_tree()

        self.combo_popup = ComboPopup(
            self.options_tree, row_id, value, column_index, update_option_value, self.database)
        self.combo_popup.place(x=x, y=y)


# Screen to select the targets series from your library.
class SelectSeries(ttk.Frame):
    def __init__(self, parent, global_methods, database, config):
        super().__init__(parent)
        self.parent = parent
        self.global_methods = global_methods
        self.database = database
        self.config = config
        # instantiate tk components
        self.main_button = None
        self.back_button = None
        self.series_cb = None
        self.series_options = None
        self.main_label = None
        self.select_series = tk.StringVar()

        self.series = self.database.get_series()

        self.create_widgets()
        self.grid_rowconfigure(0, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)

    def create_widgets(self):
        if self.series:
            self.main_label = ttk.Label(
                self, text='Select the series you would like to update')
            self.series_cb = ttk.Combobox(self, textvariable=self.select_series,
                                          values=self.series, state='readonly', font="Helvetica 14 bold", width=50)
            self.back_button = ttk.Button(
                self, text='Back', command=lambda: self.parent.switch_frames(0))
            self.main_button = ttk.Button(
                self, text='Continue', command=self.on_continue)
            self.main_label.grid()
            self.series_cb.bind('<<ComboboxSelected>>', lambda e: self.focus())
            self.series_cb.grid()
            self.main_button.grid()
            self.back_button.grid()
        else:
            self.main_label = ttk.Label(self, text='Something went wrong...')
            self.back_button = ttk.Button(
                self, text='Back', command=lambda: self.parent.switch_frames(0))
            self.main_label.grid()
            self.back_button.grid()
        self.global_methods.pad_widgets(self)

    def on_continue(self):
        if self.select_series.get():
            self.database.current_series = self.select_series.get()
            self.config.current_series = self.select_series.get()
            self.parent.switch_frames(2)
        else:
            tk.messagebox.showerror("No Selection", "Please select a series.")
            return


# Screen 1 importing/detecting config file and db file.
class SetupScreen(ttk.Frame):
    def __init__(self, parent, database, config, methods):
        super().__init__(parent)
        self.config_label = None
        self.db_label = None
        self.continue_db_label = None
        self.continue_config_label = None
        self.parent = parent
        self.database = database
        self.config = config
        self.methods = methods
        self.grid_rowconfigure((0,), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        self.config_frame = None
        self.database_frame = None
        self.import_db_label = None
        self.import_db_button = None
        self.import_config_label = None
        self.import_config_button = None
        self.continue_db_button = None
        self.continue_config_button = None
        self.create_widgets()

    def create_widgets(self):
        self.methods.destroy_widgets(self)
        self.config_frame = ttk.Frame(self)
        self.config_frame.grid_rowconfigure((0,), weight=0)
        self.config_frame.grid_columnconfigure(0, weight=1)
        self.database_frame = ttk.Frame(self)
        self.database_frame.grid_rowconfigure((0,), weight=0)
        self.database_frame.grid_columnconfigure(0, weight=1)

        # if library.db is not in base folder
        if not self.database.database_location:
            self.import_db_label = ttk.Label(
                self.database_frame, text="Import your Jellyfin library.db file.")
            self.import_db_label.grid(row=1)
            self.import_db_button = ttk.Button(
                self.database_frame, text='Import', command=self.on_browse)
            self.import_db_button.grid(row=2)
        # if the db file didn't pass verification
        elif self.database.database_location and not self.database.ready:
            self.import_db_label = ttk.Label(
                self.database_frame, text="Please make sure you import a valid Jellyfin library.db file.")
            self.import_db_label.grid(row=1)
            self.import_db_button = ttk.Button(
                self.database_frame, text='Import', command=self.on_browse)
            self.import_db_button.grid(row=2)
        # the db file is located and verified
        else:
            self.continue_db_label = ttk.Label(
                self.database_frame, text="Database located.")
            self.continue_db_label.grid(row=1)
            self.continue_db_button = ttk.Button(
                self.database_frame, text="Continue", command=self.on_continue)
            self.continue_db_button.grid(row=2)
            self.import_db_label = ttk.Label(
                self.database_frame, text="Or import a different one.")
            self.import_db_label.grid(row=3)
            self.import_db_button = ttk.Button(
                self.database_frame, text='Import', command=self.on_browse)
            self.import_db_button.grid(row=4)
        # if config.json doesn't pass verification.
        if not self.config.ready:
            self.import_config_label = ttk.Label(
                self.config_frame, text="Import a config.")
            self.import_config_label.grid(row=1)
            self.import_config_button = ttk.Button(
                self.config_frame, text="Import", command=self.on_config_import)
            self.import_config_button.grid(row=2)
        # a verified config.json exists.
        else:
            self.continue_config_label = ttk.Label(
                self.config_frame, text="A valid config has been located. Setup imported config.")
            self.continue_config_label.grid(row=1)
            self.continue_config_button = ttk.Button(
                self.config_frame, text="Continue", command=self.on_import_continue)
            self.continue_config_button.grid(row=2)
            self.import_config_label = ttk.Label(
                self.config_frame, text="Or import a different one.")
            self.import_config_label.grid(row=3)
            self.import_config_button = ttk.Button(
                self.config_frame, text="Import", command=self.on_config_import)
            self.import_config_button.grid(row=4)
        self.db_label = ttk.Label(
            self.database_frame, text="Database", font='Helvetica 22 bold')
        self.db_label.grid(row=0)
        self.config_label = ttk.Label(
            self.config_frame, text="Config", font='Helvetica 22 bold')
        self.config_label.grid(row=0)
        self.methods.pad_widgets_medium(self.database_frame)
        self.methods.pad_widgets_medium(self.config_frame)
        self.methods.pad_widgets(self)
        self.database_frame.grid(row=0, sticky='nsew')
        self.config_frame.grid(row=1, sticky='nsew')

    # Call config file browse method if a library.db file has been imported.
    def on_config_import(self):
        if not self.database.database_location:
            tk.messagebox.showerror(
                "No Database", "Please add a library.db file.")
        else:
            self.config.browse(self)

    def on_browse(self):

        self.database.browse(self)

    # Go to the SelectSeries screen
    def on_continue(self):
        if not self.database.database_location:
            tk.messagebox.showerror(
                "No Database", "Please add a library.db file.")
        else:
            self.parent.switch_frames(1)

    # Go to the ImportConfig screen
    def on_import_continue(self):
        if not self.database.database_location:
            tk.messagebox.showerror(
                "No Database", "Please add a library.db file.")
        else:
            self.parent.switch_frames(3)


# Screen for handling an ImportedConfig
class ImportConfig(ttk.Frame):
    def __init__(self, parent, config, global_methods):
        super().__init__(parent)
        self.error_label = None
        self.quick_analysis = None
        self.errors = None
        self.skip_button = None
        self.skip_label = None
        self.edit_button = None
        self.edit_label = None
        self.analyze_label = None
        self.analyze_button = None
        self.back_button = None
        self.parent = parent
        self.config = config
        self.methods = global_methods
        self.grid_rowconfigure((0,), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        self.series = self.config.config_data.keys()
        self.selected_series = tk.StringVar()
        self.import_data = self.config.import_data
        self.current_series = self.config.current_series
        self.series = [
            s for s in self.series if not self.import_data[s]['errors']]
        self.series_cb_label = None
        self.series_cb = None
        self.create_widgets()

    def create_widgets(self):
        self.methods.destroy_widgets(self)
        if self.series and len(self.series) > 1 and not self.selected_series.get():
            self.series_cb_label = ttk.Label(
                self, text="This config contains multiple series please select the one you want to use.")
            self.series_cb_label.grid(row=0)
            self.series_cb = ttk.Combobox(self, textvariable=self.selected_series,
                                          values=self.series, state='readonly', font="Helvetica 14 bold", width=50)
            self.series_cb.bind('<<ComboboxSelected>>', self.on_select)
            self.series_cb.grid(row=1)
        elif self.selected_series.get() or len(self.series) == 1:
            self.analyze_label = ttk.Label(
                self, text="Would you like to analyze this config to see what, and how many fields are updated?")
            self.analyze_label.grid()
            self.analyze_button = ttk.Button(
                self, text="Analyze", command=self.on_analyze)
            self.analyze_button.grid()
            self.edit_label = ttk.Label(
                self, text="Or would you like to continue making changes?")
            self.edit_label.grid()
            self.edit_button = ttk.Button(
                self, text="Edit", command=self.on_edit)
            self.edit_button.grid()
            self.skip_label = ttk.Label(
                self, text="Or skip and start writing to the database?")
            self.skip_label.grid()
            self.skip_button = ttk.Button(
                self, text='Skip', command=self.on_skip)
            self.skip_button.grid()
        else:
            self.errors = self.import_data[self.current_series]['errors']
            self.quick_analysis = self.import_data[self.current_series]['quick_analysis']
            if self.quick_analysis['message'] == 'fail_2':
                self.error_label = ttk.Label(
                    self, text='This configs options are corrupted and do not update any fields.')
                self.error_label.grid()
            else:
                for error in self.errors:
                    ttk.Label(self, text=error).grid()
        self.back_button = ttk.Button(
            self, text='Back', command=lambda: self.parent.switch_frames(0))
        self.methods.pad_widgets(self)

    def on_select(self, event=None):
        self.config.current_series = self.selected_series.get()
        self.create_widgets()

    def on_analyze(self):
        self.config.deep_analyze()
        self.parent.switch_frames(5)

    def on_edit(self):
        self.parent.switch_frames(4)

    def on_skip(self):
        self.parent.switch_frames(6)


# Screen for handling Analysis methods of a config.
class Analysis(ttk.Frame):
    def __init__(self, parent, config, global_methods):
        super().__init__(parent)
        self.main_label = None
        self.info_label = None
        self.continue_button = None
        self.continue_label = None
        self.skip_button = None
        self.skip_label = None
        self.parent = parent
        self.config = config
        self.methods = global_methods
        self.current_series = self.config.current_series
        self.grid_rowconfigure((0,), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        self.analysis = self.config.deep_analysis[self.current_series]
        self.create_widgets()

    def create_widgets(self):
        self.main_label = ttk.Label(self, text='Analysis')
        self.main_label.grid()
        self.info_label = ttk.Label(
            self,
            text=f"This config edits {self.current_series}, there are {self.analysis['total_updates']} to {self.analysis['options']} fields. This is {self.analysis['percentage']}% of possible changes.")
        self.info_label.grid()
        self.continue_label = ttk.Label(
            self, text='If you would like to continue making changes.')
        self.continue_label.grid()
        self.continue_button = ttk.Button(
            self, text='Edit', command=self.on_edit)
        self.continue_button.grid()
        self.skip_label = ttk.Label(
            self, text='Or skip and start writing to your database.')
        self.skip_label.grid()
        self.skip_button = ttk.Button(
            self, text='Skip', command=self.on_skip)
        self.skip_button.grid()
        self.methods.pad_widgets(self)

    def on_edit(self):
        self.parent.switch_frames(4)

    def on_skip(self):
        self.parent.switch_frames(6)


# Combo popup for the SelectFields Screen
class ComboPopup(ttk.Combobox):
    def __init__(self, parent, row_id, value, target_column, update_callback, database):
        super().__init__(parent)
        self.parent = parent
        self.database = database
        self.update_callback = update_callback
        self.keys = [True, False]
        self.old = 0 if value == "True" else 1
        self.target_column = target_column
        self.selected_value = tk.StringVar() if self.target_column == 0 else tk.BooleanVar()
        self.row_id = row_id
        self.focus_force()
        if self.target_column == 0:
            self.keys = self.database.keys
            self.old = self.database.keys.index(value) if value else 0
        self.configure(textvariable=self.selected_value,
                       values=self.keys, state='readonly')
        self.current(self.old)
        self.bind("<<ComboboxSelected>>", self.on_select if value else None)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_select(self, event):
        self.update_callback(self.selected_value.get(), self.current())
        self.destroy()
