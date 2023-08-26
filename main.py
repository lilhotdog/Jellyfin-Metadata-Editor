import sv_ttk
from global_main import *
from edit import *
from database_setup import *
from write import *


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Jellyfin Series Database Tool')
        self.resizable(False, False)  # This code helps to disable windows from resizing

        self.window_height = 1200
        self.window_width = 1200

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        self.x_coordinate = int((self.screen_width / 2) - (self.window_width / 2))
        self.y_coordinate = int((self.screen_height / 2) - (self.window_height / 2))

        self.geometry("{}x{}+{}+{}".format(self.window_width, self.window_height, self.x_coordinate, self.y_coordinate))

        # Configure the root window to expand vertically
        self.grid_rowconfigure(0, weight=1)
        # Configure the root window to expand horizontally
        self.grid_columnconfigure(0, weight=1)
        self.global_methods = GlobalMethods()
        self.global_database = Database()
        self.global_config = Config(self.global_database)
        self.global_settings = None
        sv_ttk.use_dark_theme()
        s = ttk.Style()
        s.configure('TLabel', font='Helvetica')
        s.configure('TEntry', font='Helvetica')
        s.configure('TCombobox', selectbackground='disable')
        s.configure('Red.TLabel', foreground='#c43944', font='bold')
        s.configure('Test.TLabel',
                    font='Helvetica 12 bold', foreground='#c43944')
        s.configure('Green.TLabel', foreground='#4b9123',
                    font='Helvetica 12 bold')
        s.configure('Option.TButton', foreground='#c43944')
        self.frames = [
            SetupScreen,
            SelectSeries,
            SelectFields,
            ImportConfig,
            EditScreen,
            Analysis,
            WriteScreen
        ]
        self.current_frame = SetupScreen(self, self.global_database, self.global_config, self.global_methods)
        self.bind("<Map>", self.on_map_event)
        self.sidebar_window = None
        self.main_x = None
        self.main_y = None
        self.main_width = None
        self.mainloop()

    def on_map_event(self, event):
        # Get the x-coordinate, y-coordinate, and width of the main window
        self.main_x = self.winfo_x()
        self.main_y = self.winfo_y()
        self.main_width = self.winfo_width()

    def switch_frames(self, target):
        self.global_methods.destroy_widgets(self)
        match target:
            case 0:  # SetupScreen
                self.current_frame = self.frames[target](self, self.global_database, self.global_config,
                                                         self.global_methods)
            case 1:  # SelectSeries
                self.current_frame = self.frames[target](self, self.global_methods, self.global_database,
                                                         self.global_config)
            case 2:  # SelectFields
                self.current_frame = self.frames[target](self, self.global_methods, self.global_config,
                                                         self.global_database)
            case 3:  # ImportConfig
                self.current_frame = self.frames[target](self, self.global_config, self.global_methods)

            case 4:  # EditScreen
                self.global_settings = Settings(self.global_config)
                self.current_frame = self.frames[target](self, self.global_settings, self.global_config,
                                                         self.global_methods)
            case 5:  # EditScreen
                self.current_frame = self.frames[target](self, self.global_config, self.global_methods)

            case 6:  # WriteScreen
                self.current_frame = self.frames[target](self, self.global_database, self.global_config,
                                                         self.global_methods)
            case _:  # SetupScreen
                self.current_frame = self.frames[0](self, self.global_database, self.global_config, self.global_methods)

    def create_sidebar(self):
        if not self.sidebar_window:
            self.sidebar_window = SidebarWindow(
                self, self.global_config, self.current_frame, self.global_settings)
            sidebar_x = self.main_x + self.main_width
            sidebar_y = self.main_y
            self.sidebar_window.sidebar.geometry(
                f"360x300+{sidebar_x}+{sidebar_y}")


App()
