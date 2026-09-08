"""Construct both real desktop interfaces without launching aria2 or using the network."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_language(language):
    path = ROOT / f"aria2_gui_downloader_{language}.py"
    spec = importlib.util.spec_from_file_location("app_" + language, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app_class = module.Aria2Downloader
    app_class.load_config = lambda self: None
    app_class.find_aria2 = lambda self: setattr(self, "aria_path", None)
    app = app_class()
    errors = []
    app.report_callback_exception = lambda *args: errors.append(str(args))
    try:
        for size in ("1180x780", "1000x700"):
            app.geometry(size)
            app.update()
            for name in app.pages:
                app.show_page(name)
                app.update()
                page = app.pages[name]
                assert page.winfo_width() > 600, (language, size, name, page.winfo_width())
                assert page.winfo_height() > 200, (language, size, name, page.winfo_height())
            for button in (app.start_button, app.pause_button, app.stop_button):
                assert button.winfo_rootx() >= app.winfo_rootx()
                assert button.winfo_rootx() + button.winfo_width() <= app.winfo_rootx() + app.winfo_width()
                assert button.winfo_rooty() + button.winfo_height() <= app.winfo_rooty() + app.winfo_height()
        app.show_page("queue")
        app.input_var.set("https://example.com/demo.zip")
        app.add_url_to_queue()
        app.refresh_velocity_ui()
        app.update()
        assert len(app.queue_tree.get_children()) == 1
        assert not app.queue_empty.winfo_ismapped()
        app.populate_archive("demo", [("demo.zip", "1024")])
        app.set_all_archive(True)
        app.update()
        assert len(app.queue_data) == 2
        app.clear_queue()
        app.refresh_velocity_ui()
        app.update()
        assert app.queue_empty.winfo_ismapped()
        assert not errors, errors
        print(language + ": real GUI, four pages, two sizes, queue and Archive selection OK")
    finally:
        app.destroy()


if __name__ == "__main__":
    check_language("PL")
    check_language("ENG")
