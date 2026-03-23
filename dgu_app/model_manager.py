import pyvista as pv
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self) -> None:
        if hasattr(self, '_models_loaded'):
            return
        self.file_paths: List[str] = [
            "models/group1.obj",
            "models/group2.obj",
            "models/group3.obj",
            "models/group4.obj",
            "models/group5.obj",
            "models/group6.obj",
            "models/group7.obj",
            "models/group8.obj",
            "models/group9.obj",
            "models/group10.obj",
            "models/group11.obj",
            "models/group12.obj",
            "models/group13.obj",
            "models/group14.obj",
            "models/group15.obj",
            "models/group16.obj",
            "models/group17.obj",
            "models/group18.obj",
            "models/group19.obj",
            "models/group20.obj",
            "models/group21.obj",
            "models/group22.obj",
            "models/group23.obj",
            "models/group24.obj",
            "models/group25.obj",
            "models/group26.obj",
            "models/group27.obj",
            "models/group28.obj",
            "models/group29.obj",
            "models/group30.obj",
            "models/group31.obj",
            "models/group32.obj",
            "models/group33.obj"
        ]
        self.group_names: List[str] = [
            "Водяной насос внутреннего контура",
            "Водяной насос охлаждения промежуточного контура",
            "Масляный насос",
            "Левый борт выпускной патрубок цилиндра 1",
            "Левый борт выпускной патрубок цилиндра 2",
            "Левый борт выпускной патрубок цилиндра 3",
            "Левый борт выпускной патрубок цилиндра 4",
            "Левый борт выпускной патрубок цилиндра 5",
            "Левый борт выпускной патрубок цилиндра 6",
            "Правый борт выпускной патрубок цилиндра 1",
            "Правый борт выпускной патрубок цилиндра 2",
            "Правый борт выпускной патрубок цилиндра 3",
            "Правый борт выпускной патрубок цилиндра 4",
            "Правый борт выпускной патрубок цилиндра 5",
            "Правый борт выпускной патрубок цилиндра 6",
            "Левый борт смотровой люк 1",
            "Левый борт смотровой люк 2",
            "Левый борт смотровой люк 3",
            "Левый борт смотровой люк 4",
            "Левый борт смотровой люк 5",
            "Левый борт смотровой люк 6",
            "Правый борт смотровой люк 1",
            "Правый борт смотровой люк 2",
            "Правый борт смотровой люк 3",
            "Правый борт смотровой люк 4",
            "Правый борт смотровой люк 5",
            "Правый борт смотровой люк 6",
            "Подшипник генератора",
            "Щеточный механизм генератора",
            "Корпус",
            "Коленчатый вал и цилиндры",
            "Вспомогалтельные системы",
            "Генератор"
        ]
        self.groups: Optional[List[pv.PolyData]] = None
        self._models_loaded = True

    def load_models(self) -> None:
        if self.groups is not None:
            return
        try:
            self.groups = [pv.read(path) for path in self.file_paths]
        except FileNotFoundError as e:
            logger.error(f"Model file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
