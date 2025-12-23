def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    if width <= 1 or height <= 1:
        geom = window.geometry().split('+')[0]
        try:
            width, height = map(int, geom.split('x'))
        except Exception:
            width = window.winfo_reqwidth()
            height = window.winfo_reqheight()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")