import pyvista as pv

class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.file_paths = [
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
        self.group_names = [
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
        self.groups = None
        self._initialized = True

    def load_models(self):
        if self.groups is None:
            self.groups = [pv.read(path) for path in self.file_paths]
