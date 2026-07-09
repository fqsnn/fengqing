from backend_bridge import ensure_backend
from ui import FengqingApp


if __name__ == "__main__":
    ensure_backend()
    FengqingApp().run()
