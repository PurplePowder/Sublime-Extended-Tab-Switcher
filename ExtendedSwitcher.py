import sublime, sublime_plugin, os

class Example(sublime_plugin.EventListener):
    def on_activated(self, view):
        """This method is called whenever a view (tab, quick panel, etc.) gains focus, but we only want to get the quick panel view, so we use a flag"""
        if sublime.capturingQuickPanelView == True:
            sublime.capturingQuickPanelView = False
            """View saved as an attribute of the global variable sublime so it can be accesed from your plugin or anywhere"""
            sublime.quickPanelView = view

class ExtendedSwitcherCommand(sublime_plugin.WindowCommand):
  # declarations
  open_files = []
  open_views = []
  window = []
  settings = []

  def get_file_path(self, file_name):
    folders = self.window.folders()
    for folder in folders:
      if os.path.commonprefix([folder, file_name]) == folder:
        return os.path.relpath(file_name, folder)

    return ""

  def append_view(self, view):
    self.open_views.append(view) # add the view object
    file_name = view.file_name() # get the full path

    if file_name:
      file_path = self.get_file_path(file_name)
      if view.is_dirty():
        file_name += self.settings.get('mark_dirty_file_char') # if there are any unsaved changes to the file

      if self.settings.get('show_full_file_path') == True:
        self.open_files.append([os.path.basename(file_name), file_path])
      else:
        self.open_files.append([os.path.basename(file_name), ''])
    elif view.name():
      if view.is_dirty():
        self.open_files.append([view.name() + self.settings.get('mark_dirty_file_char'), ''])
      else:
        self.open_files.append([view.name(), ''])
    else:
      if view.is_dirty():
        self.open_files.append(["Untitled"+self.settings.get('mark_dirty_file_char'), ''])
      else:
        self.open_files.append(["Untitled", ''])


  # lets go
  def run(self, list_mode):
    # self.view.insert(edit, 0, "Hello, World!")
    self.open_files = []
    self.open_views = []
    self.window = sublime.active_window()
    self.settings = sublime.load_settings('ExtendedSwitcher.sublime-settings')

    self.append_view(self.window.active_view())
    for f in self.getViews(list_mode):
      if f.id() == self.window.active_view().id():
        continue
      self.append_view(f)

    if self.check_for_sorting() == True:
      self.sort_files()

    self.views_per_group = [self.window.active_view_in_group(g) for g in range(self.window.num_groups())]

    sublime.capturingQuickPanelView = True
    self.active_group = self.window.active_group();
    self.window.show_quick_panel(self.open_files,
                                 self.tab_selected,
                                 sublime.KEEP_OPEN_ON_FOCUS_LOST,
                                 -1,
                                 self.tab_highlighted) # show the file list
    sublime.capturingQuickPanelView = False

  # display the selected open file
  def tab_selected(self, selected):
    self.restore_views()
    if selected != -1:
      view = self.open_views[selected]
      target_group, _ = self.window.get_view_index(view)
      self.window.focus_group(target_group)
      self.window.focus_view(view)

    return selected

  def restore_views(self):
    for g in range(self.window.num_groups()):
      self.window.focus_group(g)
      self.window.focus_view(self.views_per_group[g])
    self.window.focus_group(self.active_group)

  def tab_highlighted(self, highlighted):
    # self.close_previous_preview()
    view = self.open_views[highlighted]
    file_name = view.file_name()
    if file_name:
      project_path = self.window.extract_variables()["project_path"]
      file_path = (file_name if os.path.abspath(file_name) == file_name
                             else os.path.join(project_path, self.open_files[highlighted][1]))
      if os.path.exists(file_path):
        self.preview = self.window.open_file(file_path, sublime.TRANSIENT | 8)
        self.window.focus_group(self.active_group)
        self.window.focus_view(sublime.quickPanelView)

    return highlighted

  # sort the files for display in alphabetical order
  def sort_files(self):
    open_files = self.open_files
    open_views = []

    open_files.sort()

    for f in open_files:
      f = f[0]
      for fv in self.open_views:
        if fv.file_name():
          f = f.replace(" - " + os.path.dirname(fv.file_name()),'')
          if (f == os.path.basename(fv.file_name())) or (f == os.path.basename(fv.file_name())+self.settings.get('mark_dirty_file_char')):
            open_views.append(fv)
            self.open_views.remove(fv)
        elif fv.name() == f or fv.name()+self.settings.get('mark_dirty_file_char') == f:
          open_views.append(fv)
          self.open_views.remove(fv)
        elif f == "Untitled" and not fv.name():
          open_views.append(fv)
          self.open_views.remove(fv)


    self.open_views = open_views



  # flags for sorting
  def check_for_sorting(self):
    if self.settings.has("sort"):
      return self.settings.get("sort", False)


  def getViews(self, list_mode):
    views = []
    # get only the open files for the active_group
    if list_mode == "active_group":
      views = self.window.views_in_group(self.window.active_group())

    # get all open view if list_mode is window or active_group doesn't have any files open
    if (list_mode == "window") or (len(views) < 1):
      views = self.window.views()

    return views


