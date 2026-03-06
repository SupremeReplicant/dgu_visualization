from .base_window import BaseWindow
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkCellPicker
import tkinter as tk
from tkinter import ttk
import queue
import threading

class HighlightWindow(BaseWindow):
    def __init__(self, groups, group_names, highlight_indices=None):
        super().__init__(groups, group_names)
        self.font_path = "C:/Windows/Fonts/arial.ttf"
        self.hint_actor = None
        self.highlight_indices = highlight_indices if highlight_indices is not None else []
        self.checkbox_widgets = []
        self.text_actors = []
        self.outline_actor = None
        self.current_hint = ""
        self.detail_queue = queue.Queue()
        self.running = True
        
        self.detailed_descriptions = [f"Детальная информация для группы {i+1}" for i in range(33)]

    def show(self):
        plotter = pv.Plotter()
        actors = []
        
        # Меши с выделением проблемных групп
        for i, group in enumerate(self.groups):
            color = 'red' if i in self.highlight_indices else (0.7, 0.7, 0.7)
            actor = plotter.add_mesh(group, color=color, smooth_shading=True, name=self.group_names[i])
            actors.append(actor)

        picker = vtkCellPicker()
        picker.SetTolerance(0.0005)
        self.outline_actor = None

        def highlight_outline(mesh):
            return mesh.outline()

        def clear_hint():
            if self.hint_actor:
                plotter.remove_actor(self.hint_actor)
                self.hint_actor = None
            self.current_hint = ""

        def show_hint(text):
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

        def mouse_move_callback(obj, event):
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

        def mouse_click_callback(obj, event):
            x, y = obj.GetEventPosition()
            picker.Pick(x, y, 0, plotter.renderer)
            picked_actor = picker.GetActor()

            if picked_actor in actors:
                idx = actors.index(picked_actor)
                self.detail_queue.put(idx)

        # Поток для обработки окон детализации
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

        def toggle_group(group_id, state):
            actor = actors[group_id]
            actor.SetVisibility(state)
            plotter.render()

        def clear_checkboxes_and_texts():
            for widget in self.checkbox_widgets:
                widget.Off()
            plotter.clear_button_widgets()
            self.checkbox_widgets.clear()
            for actor in self.text_actors:
                plotter.remove_actor(actor)
            self.text_actors.clear()

        def update_positions():
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

        def on_resize(obj, event):
            update_positions()

        plotter.iren.add_observer("ConfigureEvent", on_resize)

        self.plotter = plotter
        
        plotter.show(auto_close=False)
        
        # Главный цикл обработки событий
        while plotter._first_time:
            plotter.update()
            
            while not self.detail_queue.empty():
                group_index = self.detail_queue.get()
                if group_index is not None:
                    self.show_detail_window(group_index)
        
        self.running = False
        self.detail_thread.join(timeout=0.5)
    
    def show_detail_window(self, group_index):
        # Описания для каждой группы элементов
        descriptions = [
        """Основной насос системы охлаждения двигателя, обеспечивающий циркуляцию теплоносителя.
    Возможные дефекты: неисправность водяного насоса охлаждения дизеля.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура подшипников водяного насоса охлаждения дизеля выше нормы;
    б) разность температур в отдельных точках на корпусе водяного насоса охлаждения дизеля выше нормы.""",

        """Насос для охлаждения промежуточных систем и компонентов установки.
    Возможные дефекты: неисправность водяного насоса охлаждения наддувочного воздуха.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура подшипников водяного насоса охлаждения наддувочного воздуха выше нормы;
    б) разность температур в отдельных точках на корпусе водяного насоса охлаждения наддувочного воздуха выше нормы.""",

        """Насос системы смазки, обеспечивающий подачу масла к движущимся частям.
    Возможные дефекты: неисправность масляного насоса.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура подшипников масляного насоса выше нормы;
    б) разность температур в отдельных областях на корпусе масляного насоса выше нормы.""",
        
        # Левый борт выпускные патрубки
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        
        # Правый борт выпускные патрубки
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        """Выпускной патрубок для отвода отработавших газов из цилиндра.
    Возможные дефекты: неисправность топливной аппаратуры.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура выхлопных патрубков выше нормы;
    б) разность температур выхлопных патрубков выше нормы.""",
        
        # Левый борт смотровые люки
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        
        # Правый борт смотровые люки
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        "Смотровой люк для доступа к внутренним компонентам двигателя",
        
        # Ключевые компоненты
        """Подшипник, обеспечивающий вращение вала генератора.
    Возможные дефекты: неисправность подшипника генератора.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура подшипника генератора выше нормы.""",

        "Механизм передачи тока между вращающимися и неподвижными частями генератора",

        """Основной корпус, содержащий компоненты дизель-генераторной установки.
    Возможные дефекты: неисправность подшипников коленвала.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) остов имеет области нагрева с температурой выше нормы;
    б) разность температур отдельных областей остова выше нормы.""",

        "Основные движущиеся части двигателя, преобразующие энергию сгорания в механическое движение",
        "Вспомогательные системы, обеспечивающие работу основной установки",

        """Электрический генератор, преобразующий механическую энергию в электрическую.
    Возможные дефекты: неисправность электрической части генератора.
    Может подтверждаться по результатам ТВК при наличии хотя бы одного из признаков:
    а) температура корпуса генератора выше нормы;
    б) температура щеточного механизма выше нормы."""
    ]
        
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
        
        def adjust_font_size(event=None):
            width = text_widget.winfo_width()
            
            base_size = max(8, min(14, int(width / 30)))
            
            text_widget.config(font=("Arial", base_size))
        
        text_widget.bind("<Configure>", adjust_font_size)
        detail_window.bind("<Configure>", adjust_font_size)
        
        adjust_font_size()
        
        close_btn.focus_set()