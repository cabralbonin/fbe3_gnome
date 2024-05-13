# window.py
#
# Copyright 2024 Cabral
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import Gio
import sys
import os
cur_path = os.path.realpath(__file__)
base_path = os.path.dirname(os.path.dirname(cur_path))
sys.path.insert(1, base_path)
from .fb_editor import FunctionBlockEditor
from .system_editor import SystemEditor
from .xmlParser import *

@Gtk.Template(resource_path='/com/lapas/Fbe/window.ui')
class FbeWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'FbeWindow'

    notebook = Gtk.Template.Child()
    add_fb_btn = Gtk.Template.Child()
    connect_fb_btn = Gtk.Template.Child()
    move_fb_btn = Gtk.Template.Child()
    remove_fb_btn = Gtk.Template.Child()
    edit_fb_btn = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        print(cur_path)
        new_file_action = Gio.SimpleAction(name="new-project")
        new_file_action.connect("activate", self.new_file_dialog)
        self.add_action(new_file_action)
        open_action = Gio.SimpleAction(name="open-project")
        open_action.connect("activate", self.open_file_sys_dialog)
        self.add_action(open_action)

        self.selected_tool = None
        self.notebook.connect('create-window', self.on_notebookbook_create_window)
        self.notebook.connect('page-removed', self.on_notebookbook_page_removed)
        self.add_fb_btn.connect('clicked', self.add_fb_dialog)
        self.edit_fb_btn.connect('clicked',self.inspect_function_block)
        self.connect_fb_btn.connect('clicked', self.connect_function_block)
        self.move_fb_btn.connect('clicked', self.move_function_block)
        self.remove_fb_btn.connect('clicked', self.remove_function_block)

    def new_file_dialog(self, action, param=None):
        app = Application('UntitledApp')
        fb_project = System(name='Untitled')
        fb_project.application_add(app)
        self.add_tab_editor(fb_project, fb_project.name, None)

    def open_file_dialog(self, action, parameter):
        # Create a new file selection dialog, using the "open" mode
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_fbt = Gtk.FileFilter()
        filter_fbt.set_name("fbt Files")
        filter_fbt.add_pattern("*.fbt")
        filters.append(filter_fbt)
        native = Gtk.FileDialog()
        native.set_filters(filters)
        native.open(self, None, self.on_open_response)
        
    def open_file_sys_dialog(self, action, parameter):
        # Create a new file selection dialog, using the "open" mode
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_fbt = Gtk.FileFilter()
        filter_fbt.set_name("sys Files")
        filter_fbt.add_pattern("*.sys")
        filters.append(filter_fbt)
        native = Gtk.FileDialog()
        native.set_filters(filters)
        native.open(self, None, self.on_open_project_response)

    def on_open_project_response(self, dialog, result):
        file = dialog.open_finish(result)
        file_name = file.get_path()
        print(file_name)
        # If the user selected a file...
        if file is not None:
            # ... open it
            fb_project = convert_xml_system(file_name)
            self.add_tab_editor(fb_project, fb_project.name, None)
    
    def on_open_response(self, dialog, result):
        file = dialog.open_finish(result)
        file_name = file.get_path()
        print(file_name)
        # If the user selected a file...
        if file is not None:
            # ... open it
            fb_choosen, _  = convert_xml_basic_fb(file_name)
            fb_diagram = Composite()
            fb_diagram.add_function_block(fb_choosen)
            self.add_tab_editor(fb_diagram, fb_choosen.name, fb_choosen)

    def open_file(self, file):
        file.load_contents_async(None, self.open_file_complete)

    def open_file_complete(self, file, result):

        contents = file.load_contents_finish(result)
        if not contents[0]:
            path = file.peek_path()
            print(f"Unable to open {path}: {contents[1]}")
            return

        try:
            text = contents[1].decode('utf-8')
        except UnicodeError as err:
            path = file.peek_path()
            print(f"Unable to load the contents of {path}: the file is not encoded with UTF-8")
            return

    def add_fb_dialog(self, action):
        # Create a new file selection dialog, using the "open" mode
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_fbt = Gtk.FileFilter()
        filter_fbt.set_name("fbt Files")
        filter_fbt.add_pattern("*.fbt")
        filters.append(filter_fbt)
        native = Gtk.FileDialog()
        native.set_filters(filters)
        native.open(self, None, self.on_add_response)

    def on_add_response(self, dialog, result):
        self.selected_tool = 'add'
        file = dialog.open_finish(result)
        file_name = file.get_path()
        print(file_name)
        # If the user selected a file...
        if file is not None:
            fb_choosen,_  = convert_xml_basic_fb(file_name)
            fb_editor = self.get_current_tab_widget()
            fb_editor.selected_fb = fb_choosen

    def remove_function_block(self, widget):
        self.selected_tool = 'remove'
        print("fb removed")

    def connect_function_block(self, widget):
        self.selected_tool = 'connect'
        print("connect selected")

    def move_function_block(self, widget):
        self.selected_tool = 'move'
        print('move selected')

    def inspect_function_block(self, widget):
        self.selected_tool = 'inspect'
        print('inspect selected')

    def set_tab_label_color(self, widget, color = 'label-black'):

        label = self.notebook.get_tab_label(widget)
        self.add_default_css_provider(label, color)

    def add_tab_editor(self, fb_project, label, fb_chosen):
        already_open_in = None
        if already_open_in is None:
            window = self.get_ancestor(Gtk.Window)
            editor = SystemEditor(window, fb_project)
            self.add_tab(editor, label)
        else:
            tab_id, window = already_open_in
            window.notebook.set_current_page(tab_id)
            window.present()

    def add_tab(self, widget, title):
        notebook = self.notebook.insert_page(widget, Gtk.Label.new(title), -1)
        self.notebook.set_current_page(notebook)
        self.notebook.set_tab_detachable(widget, True)

        return notebook

    def remove_tab(self, _id):
        if _id < 0:
            return False

        self.notebook.set_current_page(_id)

        widget = self.notebook.get_nth_page(_id)
        if widget.has_changes_to_save():
            result = self._popup(widget.get_tab_name())
            if result == Gtk.ResponseType.CANCEL:
                return False
            elif result == Gtk.ResponseType.APPLY:  # save
                if not widget.save():
                    if  not self._save_dialog(widget):
                        return False
        self.notebook.remove_page(_id)
        return True

    def remove_current_tab(self, *args):
        _id = self.notebook.get_current_page()
        self.remove_tab(_id)

    def remove_tabs(self):
        while self.notebook.get_n_pages() > 0:
            if self.remove_tab(0) == False:
                return False  # at least one tab canceled
        return True  # was able to close all tabs

    def get_current_tab_widget(self):
        _id = self.notebook.get_current_page()
        return self.notebook.get_nth_page(_id)

    def on_notebookbook_create_window(self,notebookbook,widget,x,y):
        # handler for dropping outside of notebookbook
        new_window = self.props.application.add_window()

        new_window.move(x, y)
        new_window.show_all()
        new_window.present()
        return new_window.notebook

    def on_notebookbook_page_removed(self, notebookbook, child, page):
        if notebookbook.get_n_pages() == 0:
            self.destroy()
        return True

    def on_close_tab(self, action, param):
        self.remove_current_tab()

    def get_selected_tool(self):
        return self.selected_tool


