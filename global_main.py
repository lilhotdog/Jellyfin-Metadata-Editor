import json
import os

import sqlite3
from tkinter import ttk
from tkinter import filedialog


class Database:
    def __init__(self):
        self.database_ready = None
        self.series = None
        self.database_location = None
        self.columns = None
        self.keys = None
        self.ready = False
        self.backup = None
        self.supported_fields = ["Name",
                                 "Overview",
                                 "PremiereDate",
                                 "Genres",
                                 "EpisodeTitle",
                                 "Studios",
                                 "Tags",
                                 "ProductionLocations"]

        if os.path.exists('library.db'):
            self.database_location = 'library.db'
            self.verify()
            self.get_series()

    # tkinter file browser for locating library.db
    def browse(self, frame):
        allowed = [("db files", "*.db*")]
        filename = filedialog.askopenfilename(initialdir='/',
                                              title="located \Jellyfin\Server\data",
                                              filetypes=allowed)
        self.database_location = filename
        self.verify()
        frame.create_widgets()

    # Handles the selection of all "episodes" of a given series. Used for creating "cells" in the config
    def query(self, series_name, options=None):
        try:
            if not options:
                selections = '*'
            else:
                selections_list = [m['key'] for m in options]
                selections = ', '.join(selections_list)
            if 'Size' not in selections:
                selections += ', Size'
            con = sqlite3.connect(self.database_location)
            cur = con.cursor()

            query = f"SELECT {selections} FROM TypedBaseItems WHERE SeriesName = ? AND Size > 0"
            db = cur.execute(query, (series_name,))

            return db.fetchall()
        except sqlite3.Error as e:
            self.database_ready = False
            print(f"SQLite error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Makes sure we are working with a valid Jellyfin library.db file.
    def verify(self):
        try:
            con = sqlite3.connect(self.database_location)
            cur = con.cursor()
            col = cur.execute("PRAGMA table_info(TypedBaseItems)").fetchall()
            self.columns = []
            self.keys = []
            # Create the columns and keys we reference for adding options to the config.
            for c in col:
                if c[1] in self.supported_fields:
                    if c[2] == 'TEXT' or c[2] == 'DATETIME':
                        self.columns.append({'key': c[1], 'data_type': c[2]})
                        self.keys.append(c[1])
            con.close()
            self.ready = True
            return True
        except Exception as e:
            print(e)

    # Query to the database to get unique Series
    def get_series(self):
        try:
            con = sqlite3.connect(self.database_location)
            cur = con.cursor()
            series_query = cur.execute(
                "SELECT DISTINCT SeriesName FROM TypedBaseItems")
            series = []
            for s in series_query:
                if s[0]:
                    series.append(s[0])
            self.series = series
            con.close()
            return series
        except Exception as e:
            print('temp series failure')

    # Handles writing cells based on the config to the TypedBaseItems Table
    def write_cells(self, cells, progress_callback=None, complete_callback=None):
        con = sqlite3.connect(self.database_location)
        cur = con.cursor()
        try:
            total_cells = len(cells)
            for index, cell in enumerate(cells):

                target_name = cell["Name"]  #
                # Used for matching to the database.
                target_size = cell["Size"]
                field_list = []
                field_values = []
                set_string = None
                progress = (index + 1) / total_cells * 100
                if progress_callback:
                    progress_callback(progress)

                # Iterate through the keys in the cell dictionary
                for key in cell.keys():
                    # Check if the key starts with "Updated_" and if the value is not empty
                    if key.startswith("Updated_") and cell[key]:
                        # Extract the field name without the "Updated_" prefix
                        field = key[len("Updated_"):]
                        # Fix typo: append(field), not [field]
                        field_list.append(field)
                        field_values.append(cell[key])
                for field in field_list:
                    if set_string:
                        set_string += f", {field} = ?"
                    else:
                        set_string = f"{field} = ?"
                query = f"UPDATE TypedBaseItems SET {set_string} WHERE Name = ? AND Size = ?"
                if set_string:
                    # Append target_name and target_size to field_values
                    field_values.append(target_name)
                    field_values.append(target_size)
                    # Execute the query with the appropriate values
                    cur.execute(query, field_values)
            # Commit the transaction after all updates
            con.commit()
            if complete_callback:
                complete_callback()
        except Exception as e:
            con.rollback()  # Roll back the transaction if an error occurs
            print('temp database write cells', e)
        finally:
            con.close()


class OptionsSchema:
    def __init__(self, key, edit, display, data_type):
        self.key = key
        self.edit = edit
        self.display = display
        self.data_type = data_type
        self.valid_types = ['TEXT', 'DATETIME']

    def validate_entry(self):
        if self.data_type not in self.valid_types:
            raise ValueError(f"Invalid Data Type: {self.data_type}")

    def __getitem__(self, key):
        return self.key

    def to_dict(self):
        return {
            "key": self.key,
            "edit": self.edit,
            "display": self.display,
            "data_type": self.data_type
        }


# Handle all interactions with config.json
class Config:
    def __init__(self, database):
        # Create config.json if not found
        if not os.path.exists('config.json') or (os.stat("config.json").st_size == 0):
            with open('config.json', 'w') as config_file:
                json.dump({}, config_file)
                pass
        self.config_location = "config.json"
        self.database = database
        self.config_data = None
        # Jellyfin fields that are separated by | for edit screen
        self.separated_entries = ["Genres", "Tags",
                                  "Studios", "ProductionLocations"]
        self.current_series = None
        self.ready = False
        self.deep_analysis = None
        self.import_ready = None
        self.import_data = None
        self.prune_stats = None
        self.last_updated_index = None
        self.options = [
            OptionsSchema(key="Name", edit=True,
                          display=True, data_type='TEXT'),
            OptionsSchema(key="Tags", edit=True,
                          display=False, data_type='TEXT'),
            OptionsSchema(key="PremiereDate", edit=False,
                          display=True, data_type='DATETIME')
        ]
        self.found_values = {

        }
        # if a local config is found verify it
        if os.stat("config.json").st_size > 2:
            self.verify()

    # Handle writing initial series and options to config.json
    def create_series(self, series_name=None):
        if series_name is None:
            series_name = self.current_series or self.database.current_series
        self.current_series = series_name
        # Create Json data
        options_json = [option.to_dict() for option in self.options]
        series_json = {
            self.current_series: {
                "options": options_json
            }
        }
        # Write to the config.json file
        with open(self.config_location, 'w') as file:
            # Check if a config has already been loaded
            json_conf = self.config_data or None
            if not json_conf:
                json_conf = series_json
                json.dump(series_json, file)
            elif json_conf and (self.current_series in json_conf):
                json_conf[self.current_series]["options"] = options_json
                json.dump(json_conf, file)
            else:
                json_conf.update(series_json)
                json.dump(json_conf, file)
            self.config_data = json_conf

    # Handle writing initial cells to config.json based on the current series
    def create_cells(self):
        try:
            sql_cells = self.database.query(self.current_series, self.options)
            temp_cells = []
            for cell in sql_cells:
                temp_cell = {

                }
                for index, option in enumerate(self.options):

                    # Find and store separated values.
                    if option.key in self.separated_entries and option.edit and cell[index]:
                        if option.key not in self.found_values:
                            self.found_values[option.key] = []
                        temp_list = []
                        if '|' in cell[index]:
                            temp_list = cell[index].split('|')
                        else:
                            temp_list = [cell[index]]
                        for item in temp_list:
                            if item not in self.found_values[option.key]:
                                self.found_values[option.key].append(item)

                    temp_cell[f"{option.key}"] = cell[index] if cell[index] else ''
                    if option.edit:
                        temp_cell[f"Updated_{option.key}"] = ''
                temp_cell["Size"] = cell[-1]
                temp_cells.append(temp_cell)

            # Add the found values into the config
            for key, value in self.found_values.items():
                if key not in self.config_data[self.current_series]:
                    self.config_data[self.current_series][key] = value
            
            with open(self.config_location, 'w') as file:
                self.config_data[self.current_series]["cells"] = temp_cells
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print(e)

    # write cells to config.json
    def write_cells(self):
        try:
            with open(self.config_location, 'r+') as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print('write', e)

    # Handle file browsing
    def browse(self, frame):
        allowed = [("json files", "*.json*")]
        filename = filedialog.askopenfilename(initialdir='/',
                                              title="import a config",
                                              filetypes=allowed)
        self.config_location = filename
        self.verify()
        frame.create_widgets()

    # Make sure the config is valid
    def verify(self):
        try:
            with open(self.config_location, 'r') as file:
                self.config_data = json.load(file)
            if not self.current_series:
                self.current_series = list(self.config_data.keys())[0]
            for series, series_data in self.config_data.items():
                if 'options' in series_data:
                    self.extract_options(series_data, series)
                    self.quick_analyze(series_data, series)
                    self.ready = True
        except Exception as e:
            print('verify', e)

    # Extract the options from the config
    def extract_options(self, series_data, series):
        try:
            temp_data = {series: {
                "options": [

                ],
                "errors": [

                ]
            }}
            for option in series_data['options']:
                new_option = OptionsSchema(
                    key=option['key'], edit=option['edit'], display=option['display'], data_type=option['data_type'])
                try:
                    new_option.validate_entry()
                    if new_option.key in self.separated_entries and new_option.edit:
                        self.add_separated(new_option.key)
                    temp_data[series]["options"].append(new_option)

                except Exception as e:
                    if str(e).startswith('Invalid key'):
                        temp_data[series]["errors"].append(
                            {option[
                                "key"]: f'This key does not exist in your current database or is not currently support. Edits to this field ({option["key"]}) will be ignored'})
                    elif option["key"].startswith('Invalid Data'):
                        temp_data[series]["errors"].append(
                            {option[
                                "key"]: f'This option tries to update an unsupported data type. Edits to this field ({option["key"]}) will be ignored'})
                    else:
                        temp_data[series]["errors"].append(
                            {option[
                                "key"]: f'An unknown error occurred with the option targeting ({option["key"]}) edits to this field will be ignored'})
                    continue

            if not self.import_data:
                self.import_data = {}
                self.import_data.update(temp_data)
            else:
                self.import_data.update(temp_data)
        except Exception as e:
            print(e)

    # Quick check the cells in a config
    def quick_analyze(self, series_data, series):
        count = 0
        updates = 0
        check_updates = []
        cells = series_data["cells"]
        try:
            for option in self.import_data[series]["options"]:
                if option.edit:
                    check_updates.append(option.key)
            if len(check_updates) > 0:
                for cell in cells:
                    if count > 5 or updates > 5:
                        break
                    for field in check_updates:
                        if len(cell[f'Updated_{field}']) > 0:
                            updates += 1
                    count += 1
                if updates > 3:
                    analysis = {
                        "status": True,
                        "message": "pass_1"
                    }
                    self.ready = True
                else:
                    analysis = {
                        "status": False,
                        "message": "fail_1"
                    }
            else:
                analysis = {
                    "status": False,
                    "message": "fail_2"
                }
            self.import_data[series].update({"quick_analysis": analysis})
        except Exception as e:
            print('analysis: ', e)

    # Check all the cells in a config
    def deep_analyze(self, target_series=None, parent=None):
        try:
            if not target_series:
                target_series = self.current_series or list(
                    self.config_data.keys())[0]
            cells = self.config_data[target_series]['cells']
            options = self.config_data[target_series]['options']
            check_updates = []
            analysis = {}
            for option in options:
                if option['edit']:
                    check_updates.append(option['key'])
            updates = 0

            for index, cell in enumerate(cells):
                for field in check_updates:
                    if len(cell[f'Updated_{field}']) > 0:
                        updates += 1
                        self.last_updated_index = index
            total_possible_updates = len(check_updates) * len(cells)
            update_percent = updates / total_possible_updates * 100
            analysis["options"] = check_updates
            analysis["percentage"] = update_percent
            analysis["total_updates"] = updates
            self.deep_analysis = {target_series: analysis}
            if parent:
                parent.create_widgets()
        except Exception as e:
            print('temp deep:', e)

    # Compare config cells to database
    def final_prune(self, target_series=None, parent=None, progress_callback=None, complete_callback=None):
        try:
            if not target_series:
                target_series = self.current_series or list(
                    self.config_data.keys())[0]
            sql_cells = self.database.query(target_series, self.options)
            config_cells = self.config_data[target_series]["write_cells"]
            updated_cells = []
            total_cells = len(config_cells)
            for index, cell in enumerate(config_cells):
                # Check if the episode "Name" is in the database
                if any(cell[self.options[0].key] == t[0] for t in sql_cells):
                    updated_cells.append(cell)
                progress = (index + 1) / total_cells * 100
                if progress_callback:
                    progress_callback(progress)

            pruned_cells = [d for d in config_cells if d not in updated_cells]
            self.prune_stats = {
                "cells_ready": len(updated_cells),
                "cells_removed": len(pruned_cells),
                "cells": pruned_cells
            }
            self.config_data[target_series]["write_cells"] = updated_cells

            if parent:
                parent.create_widgets()
            if complete_callback:
                complete_callback()
        except Exception as e:
            print('prune', e)

    # Remove cells that don't update anything
    def prune(self, target_series=None, parent=None):
        try:
            if not target_series:
                target_series = self.current_series or list(
                    self.config_data.keys())[0]
            config_cells = self.config_data[target_series]["cells"]
            options = self.config_data[target_series]['options']
            check_updates = [option['key']
                             for option in options if option['edit']]

            def should_prune(cell):
                for field in check_updates:
                    if cell[f'Updated_{field}']:
                        return True
                return False

            updated_cells = list(filter(should_prune, config_cells))
            pruned_cells = [d for d in config_cells if d not in updated_cells]
            self.prune_stats = {
                "cells_ready": len(updated_cells),
                "cells_removed": len(pruned_cells),
                "cells": pruned_cells
            }
            self.config_data[target_series]["write_cells"] = updated_cells
            if parent:
                parent.create_widgets()
        except Exception as e:
            print('prune', e)

    # Add | separated options
    def add_separated(self, target_field, target_series=None, new_field=None):
        try:
            if not target_series:
                target_series = self.current_series or list(
                    self.config_data.keys())[0]
            if target_field not in self.config_data[target_series]:
                print("hi")
                self.config_data[target_series][target_field] = []
            if new_field:
                self.config_data[target_series][target_field].append(new_field)
            with open(self.config_location, 'r+') as file:
                json.dump(self.config_data, file, indent=4)
        except Exception as e:
            print('write', e)


class GlobalMethods:
    @staticmethod
    def destroy_widgets(target):
        for widget in target.winfo_children():
            widget.destroy()

    @staticmethod
    def pad_widgets(target):
        for child in target.winfo_children():
            child.grid_configure(pady=10)

    @staticmethod
    def pad_widgets_light(target):
        for child in target.winfo_children():
            child.grid_configure(pady=5)

    @staticmethod
    def pad_widgets_medium(target):
        for child in target.winfo_children():
            child.grid_configure(pady=5)

    @staticmethod
    def to_bool(s):
        return True if s == 'True' else False

    @staticmethod
    def set_cursor(target):
        for widget in target.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(cursor="hand2")


class Settings:
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_cell_index = self.config.last_updated_index or 0
        self.config_data = self.config.config_data
        self.series = self.config.current_series
        self.options = self.config.config_data[self.config.current_series]["options"]
        self.separated_options = [option['key'] for option in self.options if option['edit']
                                  and option['key'] in self.config.separated_entries] or None
        self.display_only = [
            option['key'] for option in self.options if
            option['display'] and not option['edit']] or None
        self.edit_and_display = [option['key'] for option in self.options if option['edit']
                                 and option['display'] and not option['key'] in self.config.separated_entries] or None
        self.edit_only = [option['key'] for option in self.options if option['edit']
                          and not option['display'] and not option['key'] in self.config.separated_entries] or None

    def reload_config(self):
        self.current_cell_index = self.config.last_updated_index or 0
        self.config_data = self.config.config_data
        self.series = self.config.current_series
        self.options = self.config.config_data[self.config.current_series]["options"]
        self.separated_options = [option['key'] for option in self.options if option['edit']
                                  and option['key'] in self.config.separated_entries] or None
        self.display_only = [
            option['key'] for option in self.options if
            option['display'] and not option['edit']] or None
        self.edit_and_display = [option['key'] for option in self.options if option['edit']
                                 and option['display'] and not option['key'] in self.config.separated_entries] or None
        self.edit_only = [option['key'] for option in self.options if option['edit']
                          and not option['display'] and not option['key'] in self.config.separated_entries] or None
