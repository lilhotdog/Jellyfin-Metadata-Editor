from datetime import datetime
from tkinter import ttk
import shutil


class WriteScreen(ttk.Frame):
    def __init__(self, parent, database, config, methods):
        super().__init__(parent)
        self.back_button = None
        self.parent = parent
        self.database = database
        self.config = config
        self.methods = methods
        self.current_series = self.config.current_series
        self.config_pruned = None
        self.complete = None

        # instantiate tk components
        self.prune_label = None
        self.progress_bar = None
        self.start_button = None
        self.start_label = None
        self.error_label = None
        self.prepare_label = None
        self.prepare_button = None
        self.backup_button = None
        self.complete_button = None 
        self.complete_label = None
        # layout methods
        self.grid_rowconfigure((0,), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew', pady=50)
        # initialize widgets
        self.create_widgets()

    def create_widgets(self):
        self.methods.destroy_widgets(self)
        row = 0
        if self.complete:
            self.complete_label = ttk.Label(self, text='Complete! Make sure to refresh your metadata in Jellyfin!')
            self.complete_button = ttk.Button(self, text='Start Over', command=lambda: self.parent.switch_frames(0))
            self.complete_label.grid(row=row)
            self.complete_button.grid(row=row+1)
            self.methods.pad_widgets_medium(self)
            return
        if not self.database.backup:
            self.backup_button = ttk.Button(self, text='Backup your library.db', command=self.create_backup)
            self.backup_button.grid(row=row+20)
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(pady=20, row=row)

        if self.config_pruned and self.config.config_data[self.current_series]["write_cells"]:
            self.prune_label = ttk.Label(self, text=f"{self.config.prune_stats['cells_ready']} cells will be updated.")
            self.prune_label.grid(row=row+2)
            self.start_label = ttk.Label(self, text='Start Writing to your database.')
            self.start_label.grid(row=row+3)
            self.start_button = ttk.Button(self, text="Start Writing", command=self.start_writing)
            self.start_button.grid(row=row+4)
        elif self.config_pruned and self.config.prune_stats:
            self.error_label = ttk.Label(self, text=f"Your config was scanned and no valid changes were found.")
            self.error_label.grid(row=row)
        else: 
            self.prepare_label = ttk.Label(self, text="Almost there... prepare your config.")
            self.prepare_label.grid(row=row+2)
            self.prepare_button = ttk.Button(self, text='Prepare', command=self.prepare_config)
            self.prepare_button.grid(row=row+3)
        self.back_button = ttk.Button(self, text='back', command=lambda: self.parent.switch_frames(4))
        self.back_button.grid(row=row+5)
        self.methods.pad_widgets_medium(self)
    
    def update_progress(self, progress):
        self.progress_bar["value"] = progress
        self.update()

    def write_complete(self):
        self.progress_bar["value"] = 100

    def start_writing(self):
        cells = self.config.config_data[self.current_series]['write_cells']
        self.database.write_cells(cells, self.update_progress, self.write_complete)
        self.complete = True
        self.create_widgets()


    def create_backup(self):
        now = datetime.now()
        dt_string = now.strftime("%d%m%Y%H%M%S")
        shutil.copy(self.database.database_location, 'library' + dt_string + '.db')
        self.database.backup = True
        self.create_widgets()

    def prepare_config(self):
        self.config.prune()
        self.config.final_prune(None, None, self.update_progress, self.write_complete)
        self.config_pruned = True
        self.create_widgets()