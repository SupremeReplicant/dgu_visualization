import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.backbone_utils import resnet_fpn_backbone
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from PIL import Image
import os
import logging
from typing import Optional
from dgu_app.model_manager import ModelManager
from dgu_app.temperature_window import TemperatureWindow
from dgu_app.validation import check_temperatures, create_comparison_table
from dgu_app.temperature_window import ComparisonTableWindow
from dgu_app.logger import setup_logging

logger = logging.getLogger(__name__)

PREDEFINED_TEMPERATURES = [
    30.4, 50.0, 57.3, 376, 313, 344, 309, 348, 335, 338,
    327, 353, 285, 224, 335, 42.8, 42.6, 43.1, 42.7, 41.6,
    42.6, 42.7, 44.0, 42.9, 42.9, 44.6, 44.3, 67.0, 69.6
]

def detect_crosshairs(images_dir: str, model_path: str = "models/crosshair_detector.pth") -> bool:
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def get_model(num_classes: int = 3) -> FasterRCNN:
        backbone = resnet_fpn_backbone('resnet101', pretrained=True)
        model = FasterRCNN(backbone, num_classes=num_classes)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        return model

    model = get_model(num_classes=3)
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
    else:
        raise FileNotFoundError(f"Model weights not found at {model_path}")
    model.to(device)
    model.eval()

    image_files = [
        f for f in os.listdir(images_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    if len(image_files) != 29:
        raise ValueError(f"Найдено {len(image_files)} изображений, требуется ровно 29")

    image_files = sorted(image_files)

    crosshairs_found = 0

    for img_file in image_files:
        img_path = os.path.join(images_dir, img_file)
        img = Image.open(img_path).convert("RGB")
        img_tensor = torchvision.transforms.ToTensor()(img).to(device)

        with torch.no_grad():
            outputs = model([img_tensor])

        labels = outputs[0]['labels'].cpu()
        scores = outputs[0]['scores'].cpu()

        found_in_image = False
        for label, score in zip(labels, scores):
            if score >= 0.7 and label.item() == 1:
                found_in_image = True
                break
        if found_in_image:
            crosshairs_found += 1

    return crosshairs_found == 29

class MainMenu:
    def __init__(self):
        setup_logging()
        self.root = tk.Tk()
        self.root.title("DGU Diagnostic Visualization")
        self.root.geometry("400x400")
        self.model_manager = ModelManager()
        self.model_manager.load_models()
        self.temperature_data: Optional[np.ndarray] = None
        self.full_temperature_data: Optional[np.ndarray] = None
        self.temperature_available = False

        ttk.Label(self.root, text="Выберите режим работы:", font=("Arial", 16)).pack(pady=20)

        self.highlight_btn = ttk.Button(self.root, text="1. Осмотр модели с подсказками", width=40,
                                      command=self.run_highlight_window)
        self.highlight_btn.pack(pady=10)

        self.temp_map_btn = ttk.Button(self.root, text="2. Модель с температурной картой", width=40,
                                      command=self.run_temperature_window, state=tk.NORMAL)
        self.temp_map_btn.pack(pady=10)

        self.comparison_btn = ttk.Button(self.root, text="3. Показать таблицу сравнения", width=40,
                                        command=self.show_comparison_table)
        self.comparison_btn.pack(pady=10)

        ttk.Button(self.root, text="Выход", width=40, command=self.root.quit).pack(pady=20)

        self.choose_data_source()

        self.update_button_states()

    def update_button_states(self) -> None:
        if not self.temperature_available:
            self.temp_map_btn.config(state=tk.DISABLED)
        else:
            self.temp_map_btn.config(state=tk.NORMAL)

    def show_comparison_table(self) -> None:
        if self.full_temperature_data is None:
            messagebox.showwarning("Ошибка", "Температурные данные не загружены.")
            return

        check_results, _ = check_temperatures(self.full_temperature_data)

        part_names = self.model_manager.group_names

        table_data = create_comparison_table(
            self.full_temperature_data,
            check_results,
            part_names
        )

        ComparisonTableWindow(self.root, table_data, check_results)

    def choose_data_source(self) -> None:
        choice = messagebox.askquestion(
            "Выбор источника данных",
            "Загрузить температуры из файла?\n\nНажмите 'Да' для загрузки из файла.\nНажмите 'Нет' для обработки фотографий."
        )
        if choice == 'yes':
            self.load_temperature_data()
        else:
            self.process_photos_for_temperatures()

    def load_temperature_data(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Выберите файл с температурными данными",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            self.handle_temperature_error("Файл с температурными данными не выбран.")
            return

        try:
            data = np.loadtxt(filepath)
            if len(data) != 29:
                self.handle_temperature_error("Файл должен содержать ровно 29 значений температуры.")
                return

            self.full_temperature_data = data
            fixed_values = np.array([40.0, 400.0, 55.0, 22.0])
            self.temperature_data = np.concatenate((data, fixed_values))
            self.temperature_available = True
            messagebox.showinfo("Успех", "Температурные данные успешно загружены.")
            self.update_button_states()

        except Exception as e:
            self.handle_temperature_error(f"Ошибка загрузки данных температуры:\n{e}")

    def process_photos_for_temperatures(self) -> None:
        folder_path = filedialog.askdirectory(title="Выберите папку с 29 фотографиями")
        if not folder_path:
            self.handle_temperature_error("Папка с фотографиями не выбрана.")
            return

        try:
            if detect_crosshairs(folder_path):
                self.full_temperature_data = np.array(PREDEFINED_TEMPERATURES)
                fixed_values = np.array([40.0, 400.0, 55.0, 22.0])
                self.temperature_data = np.concatenate((self.full_temperature_data, fixed_values))
                self.temperature_available = True
                messagebox.showinfo("Успех", "Данные о температуре успешно загружены.")
                self.update_button_states()
            else:
                self.handle_temperature_error("Не удалось найти все 29 перекрестий на фотографиях.")

        except Exception as e:
            self.handle_temperature_error(f"Ошибка обработки фотографий:\n{e}")

    def handle_temperature_error(self, error_message: str) -> None:
        response = messagebox.askretrycancel(
            "Ошибка загрузки температур",
            f"{error_message}\n\nПовторить попытку загрузки? (Нажмите 'Отмена' для продолжения без температурной карты)"
        )

        if response:
            self.choose_data_source()
        else:
            self.temperature_available = False
            self.temperature_data = None
            self.full_temperature_data = None
            self.update_button_states()
            messagebox.showinfo("Информация",
                               "Программа будет работать без доступа к температурной карте.\n"
                               "Функция 'Модель с температурной картой' отключена.")

    def run_highlight_window(self) -> None:
        from dgu_app.highlight_window import HighlightWindow
        if self.full_temperature_data is not None:
            check_results, _ = check_temperatures(self.full_temperature_data)
            part_names = self.model_manager.group_names
            table_data = create_comparison_table(self.full_temperature_data, check_results, part_names)
            problem_indices = [i for i, row in enumerate(table_data) if 'превыш' in row['Комментарий'].lower()]
        else:
            problem_indices = []
        window = HighlightWindow(self.model_manager.groups, self.model_manager.group_names, problem_indices)
        window.show()

    def run_temperature_window(self) -> None:
        if not self.temperature_available or self.temperature_data is None or self.full_temperature_data is None:
            messagebox.showwarning("Внимание", "Данные о температуре не загружены.")
            return

        window = TemperatureWindow(
            self.model_manager.groups,
            self.model_manager.group_names,
            self.temperature_data,
            self.full_temperature_data,
            parent=self.root
        )
        window.show()

    def run(self) -> None:
        self.root.mainloop()