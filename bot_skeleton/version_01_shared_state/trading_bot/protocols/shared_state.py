import asyncio

# Responsabilité : servir de mémoire partagée entre toutes les classes.
# Rôle : stocker les prix, carnet, indicateurs, support/resistance et signaux de façon thread-safe/asynchrone.
class SharedState:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()

    async def set(self, key, value):
        async with self.lock:
            self.data[key] = value

    async def get(self, key, default=None):
        async with self.lock:
            return self.data.get(key, default)