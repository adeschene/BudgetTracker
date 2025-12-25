def center_window(window):
    '''
    Center a tkinter window on the screen.

    This helper attempts to use the actual window size (after layout)
    and falls back to the window's requested size if the real size
    is not yet available (small or 1x1). It then calculates the
    screen-centered x/y coordinates and applies a new geometry.

    Args:
        window: a tkinter Toplevel or root window instance.
    '''
    # Ensure geometry/layout calculations are up-to-date
    window.update_idletasks()

    # Try to get the actual rendered size first
    width = window.winfo_width()
    height = window.winfo_height()

    # If the window hasn't been drawn yet, winfo_width/height
    # may return 1 (or 0); fall back to geometry or requested size
    if width <= 1 or height <= 1:
        geom = window.geometry().split('+')[0]
        try:
            # geometry returns something like '400x300+100+100'
            width, height = map(int, geom.split('x'))
        except Exception:
            # As a final fallback use the requested size
            width = window.winfo_reqwidth()
            height = window.winfo_reqheight()

    # Compute center position on the current screen
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Apply the calculated geometry so the window appears centered
    window.geometry(f"{width}x{height}+{x}+{y}")