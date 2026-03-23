from .base_window import BaseWindow
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkCellPicker
import tkinter as tk
from tkinter import ttk
import queue
import threading
import logging
from typing import List, Optional
from dgu_app.descriptions import DETAILED_DESCRIPTIONS

logger = logging.getLogger(__name__)

class HighlightWindow(BaseWindow):
    def __init__(self, groups: List[pv.PolyData], group_names: List[str], highlight_indices: Optional[List[int]] = None):
        super().__init__(groups, group_names)
        self.font_path = "C:/Windows/Fonts/arial.ttf"
        self.hint_actor: Optional[pv.Text] = None
        self.highlight_indices = highlight_indices if highlight_indices is not None else []
        self.checkbox_widgets: List[pv.Widget] = []
        self.text_actors: List[pv.Text] = []
        self.outline_actor: Optional[pv.Actor] = None
        self.current_hint = ""
        self.detail_queue: queue.Queue[int] = queue.Queue()
        self.running = True

    def show(self) -> None:
        plotter = pv.Plotter()
        actors: List[pv.Actor] = []

        # Меши с выделением проблемных групп
        for i, group in enumerate(self.groups):
            color = 'red' if i in self.highlight_indices else (0.7, 0.7, 0.7)
            actor = plotter.add_mesh(group, color=color, smooth_shading=True, name=self.group_names[i])
            actors.append(actor)

        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        self.outline_actor = None

        def highlight_outline(mesh: pv.PolyData) -> pv.PolyData:
            return mesh.outline()

        def clear_hint() -> None:
            if self.hint_actor:
                plotter.remove_actor(self.hint_actor)
                self.hint_actor = None
            self.current_hint = ""

        def show_hint(text: str) -> None:
            clear_hint()
            if not text:
                return

            self.current_hint = text
            self.hint_actor = plotter.add_text(
                text,
                position='bottom',
                font_file=self.font_path,
                font_size=14,
                color='black',
                shadow=True
            )

        def mouse_move_callback(obj, event) -> None:
            x, y = obj.GetEventPosition()
            picker.Pick(x, y, 0, plotter.renderer)
            picked_actor = picker.GetActor()

            if self.outline_actor:
                plotter.remove_actor(self.outline_actor)
                self.outline_actor = None

            clear_hint()

            if picked_actor in actors:
                idx = actors.index(picked_actor)
                mesh = self.groups[idx]
                outline_mesh = highlight_outline(mesh)
                self.outline_actor = plotter.add_mesh(outline_mesh, color='red', line_width=3, opacity=0.8)
                show_hint(self.group_names[idx])

            plotter.render()

        def mouse_click_callback(obj, event) -> None:
            x, y = obj.GetEventPosition()
            picker.Pick(x, y, 0, plotter.renderer)
            picked_actor = picker.GetActor()

            if picked_actor in actors:
                idx = actors.index(picked_actor)
                self.detail_queue.put(idx)

        def detail_window_thread():
            while self.running:
                try:
                    group_index = self.detail_queue.get(timeout=0.1)
                    if group_index is not None:
                        self.show_detail_window(group_index)
                except queue.Empty:
                    continue

        self.detail_thread = threading.Thread(target=detail_window_thread, daemon=True)
        self.detail_thread.start()

        plotter.enable_trackball_style()
        plotter.iren.add_observer("MouseMoveEvent", mouse_move_callback)
        plotter.iren.add_observer("LeftButtonPressEvent", mouse_click_callback)

        num_groups = len(self.groups)

        def toggle_group(group_id: int, state: bool) -> None:
            actor = actors[group_id]
            actor.SetVisibility(state)
            plotter.render()

        def clear_checkboxes_and_texts() -> None:
            for widget in self.checkbox_widgets:
                if hasattr(widget, 'Off'):
                    widget.Off()
            plotter.clear_button_widgets()
            self.checkbox_widgets.clear()
            for actor in self.text_actors:
                plotter.remove_actor(actor)
            self.text_actors.clear()

        def update_positions() -> None:
            window_width, window_height = plotter.window_size
            if window_width <= 0 or window_height <= 0:
                return

            button_size = max(8, int(min(window_width, window_height) * 0.016))
            base_font_size = max(10, int(min(window_width, window_height) * 0.012))
            
            top_margin = 0.05
            bottom_margin = 0.05
            available_height = 1.0 - top_margin - bottom_margin
            line_height = available_height / num_groups
            
            clear_checkboxes_and_texts()
            
            for i in range(num_groups):
                y_pos = 1.0 - top_margin - (i + 0.5) * line_height
                checkbox_x = int(window_width * 0.05)
                checkbox_y = int(y_pos * window_height)
                
                widget = plotter.add_checkbox_button_widget(
                    lambda state, idx=i: toggle_group(idx, state),
                    value=True,
                    position=(checkbox_x, checkbox_y),
                    size=button_size,
                    color_on='blue',
                    color_off='gray'
                )
                self.checkbox_widgets.append(widget)
                
                text_x = (checkbox_x + button_size + 10) / window_width
                
                text_actor = plotter.add_text(
                    self.group_names[i],
                    position=(text_x, y_pos),
                    viewport=True,
                    font_file=self.font_path,
                    font_size=base_font_size,
                    color='black',
                    shadow=True
                )
                self.text_actors.append(text_actor)

            plotter.render()

        self.checkbox_widgets = []
        self.text_actors = []
        update_positions()

        def on_resize(obj, event) -> None:
            update_positions()

        plotter.iren.add_observer("ConfigureEvent", on_resize)

        self.plotter = plotter

        plotter.show(auto_close=False)

        # Главный цикл обработки событий
        while plotter._first_time:
            plotter.update()
            
        self.running = False
        self.detail_thread.join(timeout=0.5)
    
    def show_detail_window(self, group_index: int) -> None:
        if group_index < 0 or group_index >= len(DETAILED_DESCRIPTIONS):
            logger.error(f"Invalid group index: {group_index}")
            return

        # Описания для каждой группы элементов
        descriptions = DETAILED_DESCRIPTIONS

        detail_window = tk.Toplevel()
        detail_window.title(f"Детальная информация: {self.group_names[group_index]}")
        detail_window.geometry("600x500")
        detail_window.minsize(500, 400)

        main_frame = ttk.Frame(detail_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(
            header_frame,
            text=self.group_names[group_index],
            font=("Arial", 16, "bold"),
            anchor="center"
        )
        title_label.pack(fill=tk.X)

        subtitle_label = ttk.Label(
            header_frame,
            text="Подробная информация:",
            font=("Arial", 12, "bold")
        )
        subtitle_label.pack(anchor=tk.W, pady=(10, 5))

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert(tk.END, descriptions[group_index])
        text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        close_btn = ttk.Button(button_frame, text="Закрыть", command=detail_window.destroy)
        close_btn.pack(side=tk.RIGHT)

        def adjust_font_size(event=None) -> None:
            width = text_widget.winfo_width()

            base_size = max(8, min(14, int(width / 30)))

            text_widget.config(font=("Arial", base_size))

        text_widget.bind("<Configure>", adjust_font_size)
        detail_window.bind("<Configure>", adjust_font_size)

        adjust_font_size()

        close_btn.focus_set()