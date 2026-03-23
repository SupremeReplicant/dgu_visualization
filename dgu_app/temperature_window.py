from .base_window import BaseWindow
import pyvista as pv
import numpy as np
from matplotlib.colors import ListedColormap
import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class SetVisibilityCallback:
    def __init__(self, actor: pv.Actor):
        self.actor = actor

    def __call__(self, state: bool) -> None:
        self.actor.SetVisibility(state)

class ComparisonTableWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, table_data: List[dict], check_results: dict):
        super().__init__(parent)
        self.title("Результаты проверки температур")
        self.geometry("900x700")

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('Номер', 'Деталь', 'Введенная', 'Эталонная', 'Комментарий'),
            show='headings',
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading('Номер', text='№')
        self.tree.heading('Деталь', text='Деталь')
        self.tree.heading('Введенная', text='Введенная °C')
        self.tree.heading('Эталонная', text='Эталонная °C')
        self.tree.heading('Комментарий', text='Комментарий')

        self.tree.column('Номер', width=50, anchor='center')
        self.tree.column('Деталь', width=200, anchor='w')
        self.tree.column('Введенная', width=100, anchor='center')
        self.tree.column('Эталонная', width=100, anchor='center')
        self.tree.column('Комментарий', width=250, anchor='w')

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for row in table_data:
            self.tree.insert('', 'end', values=(
                row['Номер'],
                row['Деталь'],
                row['Введенная температура'],
                row['Эталонная температура'],
                row['Комментарий']
            ))

        exhaust_all_ok = all(check_results.get('4-15_individual', [True]))
        spread = check_results.get('4-15_spread', 0.0)

        hatches_all_ok = all(check_results.get('16-27_individual', [True]))

        oil_pump_ok = check_results.get(3, True)
        water_pump_ok = check_results.get(1, True)
        brush_ok = check_results.get(29, True)

        summary_lines = [
            f"абсолютная температура выхлопных газов цилиндров {'соответствует' if exhaust_all_ok else 'не соответствует'} норме (ниже 450 °C);",
            f"различие температур цилиндров {'выше' if spread > 30 else 'ниже'} нормы;",
            f"температура смотровых лючков {'соответствует' if hatches_all_ok else 'не соответствует'} норме (ниже 100 °C);",
            f"температура масляного насоса {'соответствует' if oil_pump_ok else 'не соответствует'} норме (ниже 60 °C);",
            f"температура водяного насоса внутреннего контура {'соответствует' if water_pump_ok else 'не соответствует'} норме (ниже 87 °C);",
            f"температура щеточного механизма генератора {'соответствует' if brush_ok else 'не соответствует'} норме (ниже 80 °C)."
        ]

        summary_text = "По результатам обследования выявлено:\n" + "\n".join([f"        -   {line}" for line in summary_lines])

        self.bottom_label = tk.Label(self, text=summary_text, justify=tk.LEFT, font=("Arial", 14))
        self.bottom_label.pack(pady=10)

class TemperatureWindow(BaseWindow):
    def __init__(self, groups: List[pv.PolyData], group_names: List[str], temperature_data: np.ndarray, full_temperature_data: np.ndarray, parent: Optional[tk.Tk] = None):
        super().__init__(groups, group_names)
        self.temperature_data = temperature_data
        self.full_temperature_data = full_temperature_data
        self.parent = parent
        self.font_path = "C:/Windows/Fonts/arial.ttf"
        self.checkbox_widgets: List[pv.Widget] = []
        self.text_actors: List[pv.Text] = []
        self.temp_text_actors: List[pv.Text] = []

    def show(self) -> None:
        if self.temperature_data is None:
            logger.error("Нет данных о температуре для отображения.")
            return

        cmap_length = 256
        temp_range = (1, 600)
        colors = np.zeros((cmap_length, 4))

        def temp_to_index(temp: float) -> int:
            return int(np.clip((temp - temp_range[0]) / (temp_range[1] - temp_range[0]) * (cmap_length - 1), 0, cmap_length - 1))

        blue = np.array([0, 0, 1, 1])
        violet = np.array([0.5, 0, 0.5, 1])
        green = np.array([0, 1, 0, 1])
        yellow = np.array([1, 1, 0, 1])
        red = np.array([1, 0, 0, 1])

        idx_1_30 = temp_to_index(30)
        idx_30_40 = temp_to_index(40)
        idx_40_50 = temp_to_index(50)
        idx_50_60 = temp_to_index(60)
        idx_60_600 = cmap_length - 1

        def fill_color(start_idx: int, end_idx: int, start_color: np.ndarray, end_color: np.ndarray) -> None:
            length = end_idx - start_idx + 1
            for i in range(length):
                t = i / max(length - 1, 1)
                colors[start_idx + i] = (1 - t) * start_color + t * end_color

        fill_color(0, idx_1_30, blue, blue)
        fill_color(idx_1_30 + 1, idx_30_40, blue, violet)
        fill_color(idx_30_40 + 1, idx_40_50, violet, green)
        fill_color(idx_40_50 + 1, idx_50_60, green, yellow)
        fill_color(idx_50_60 + 1, idx_60_600, yellow, red)

        custom_cmap = ListedColormap(colors)

        temp_min = np.min(self.temperature_data)
        temp_max = np.max(self.temperature_data)

        if temp_min == temp_max:
            temp_min -= 1
            temp_max += 1

        self.plotter = pv.Plotter(shape=(1, 2), window_size=[1200, 800])
        self.plotter.background_color = "white"

        self.plotter.subplot(0, 0)
        self.plotter.background_color = "white"
        self.actors: List[pv.Actor] = []

        length = min(len(self.temperature_data), len(self.groups))

        for i in range(length):
            group = self.groups[i]
            if group.points.dtype != np.float32:
                group.points = group.points.astype(np.float32)
            temp_val = np.clip(self.temperature_data[i], temp_min, temp_max)
            temp_array = np.full(group.n_points, temp_val)
            group.point_data["Temperature"] = temp_array
            actor = self.plotter.add_mesh(
                group,
                cmap=custom_cmap,
                clim=[temp_min, temp_max],
                scalars="Temperature",
                name=self.group_names[i],
                show_scalar_bar=False
            )
            self.actors.append(actor)

        mapper_for_scalar_bar = self.actors[0].GetMapper() if self.actors else None

        if mapper_for_scalar_bar is not None:
            self.plotter.add_scalar_bar(
                title="Temperature (°C)",
                interactive=False,
                color="black",
                vertical=True,
                n_colors=256,
                mapper=mapper_for_scalar_bar,
                position_x=0.95,
                position_y=0.05,
                width=0.03,
                height=0.3,
                title_font_size=12,
                label_font_size=10,
                font_family='arial'
            )

        self.plotter.subplot(0, 1)
        self.plotter.background_color = "white"
        self.plotter.camera_position = 'xy'

        self.title_actor = self.plotter.add_text(
            "Данные диагностики и видимость объектов",
            position="upper_edge",
            color="black",
            font_file=self.font_path,
            font_size=10,
            viewport=True
        )

        self.num_groups = length
        self._create_initial_interface()

        def on_resize(obj, event):
            self._recreate_interface()

        self.plotter.iren.add_observer("ConfigureEvent", on_resize)

        self.plotter.enable_trackball_style()
        self.plotter.subplot(0, 0)
        self.plotter.subplot(0, 1)
        self.plotter.hide_axes()
        self.plotter.link_views()
        self.plotter.show()

    def _create_initial_interface(self) -> None:
        self._recreate_interface()

    def _recreate_interface(self) -> None:
        for widget in self.checkbox_widgets:
            self.plotter.remove_widget(widget)
        self.checkbox_widgets.clear()

        for actor in self.text_actors + self.temp_text_actors:
            self.plotter.remove_actor(actor)
        self.text_actors.clear()
        self.temp_text_actors.clear()

        if not hasattr(self, 'plotter') or not self.plotter.window_size:
            return

        window_width, window_height = self.plotter.window_size
        if window_width <= 0 or window_height <= 0:
            return

        button_size = max(8, int(min(window_width, window_height) * 0.016))
        base_font_size = max(8, int(min(window_width, window_height) * 0.012 * 0.8))

        top_margin_fraction = 0.05
        bottom_margin_fraction = 0.05
        available_height_fraction = 1.0 - top_margin_fraction - bottom_margin_fraction

        line_height_fraction = available_height_fraction / self.num_groups

        checkbox_x = int(window_width * 0.05)
        text_x = checkbox_x + button_size + 10

        temp_x = checkbox_x + button_size + int(window_width * 0.36)

        for i in range(self.num_groups):
            y_fraction = 1.0 - top_margin_fraction - (i + 0.5) * line_height_fraction
            y_pixel = int(y_fraction * window_height)

            callback = SetVisibilityCallback(self.actors[i])
            widget = self.plotter.add_checkbox_button_widget(
                callback,
                value=True,
                position=(checkbox_x, y_pixel),
                size=button_size,
                border_size=1,
                color_on='blue',
                color_off='gray',
                background_color='white'
            )
            self.checkbox_widgets.append(widget)

            text_actor = self.plotter.add_text(
                self.group_names[i],
                position=(text_x, y_pixel),
                font_file=self.font_path,
                font_size=base_font_size,
                color='black',
                shadow=True,
                viewport=False
            )
            self.text_actors.append(text_actor)

            temp_actor = self.plotter.add_text(
                f"{self.temperature_data[i]:.2f} °C",
                position=(temp_x, y_pixel),
                font_file=self.font_path,
                font_size=base_font_size,
                color='black',
                shadow=True,
                viewport=False
            )
            self.temp_text_actors.append(temp_actor)

        self.plotter.render()