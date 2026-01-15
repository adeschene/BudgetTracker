from decimal import Decimal, InvalidOperation

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

def fuzzy_match(keyword, text, threshold=0.9):
        # Simple fuzzy matching: treat as match if substring OR if
        # a sufficient fraction of keyword characters appear in text.
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        if keyword_lower in text_lower:
            return True
        # character-level matching
        matches = sum(1 for c in keyword_lower if c in text_lower)
        score = matches / len(keyword_lower) if keyword_lower else 0
        return score >= threshold

def exact_match(keyword, text):
    # Case-insensitive substring match
    return keyword.lower() in text.lower()



# Ensure only valid numbers are entered in a given Entry textbox (allow minus sign at start)
def validate_money_string(new_value: str, allow_negative: str, allow_decimal: str) -> bool:
    # Allow empty for editing
    if new_value == "":
        return True
    
    # Don't allow negative sign if neg nums turned off in call
    if allow_negative == 'False' and '-' in new_value:
        return False
    
    # Reject decimals entirely if disabled
    if allow_decimal == 'False' and '.' in new_value:
        return False

    # Structural checks: only one '.', only one '-' in front, no other chars
    if new_value.count('.') > 1:
        return False
    if new_value.count('-') > 1:
        return False
    if '-' in new_value[1:]:
        return False

    # Must be digits / '.' / '-'
    for ch in new_value:
        if ch not in "0123456789.-":
            return False

    # Enforce at most 2 decimal places
    if '.' in new_value:
        frac = new_value.split('.', 1)[1]
        if len(frac) > 2:
            return False

    # Reject leading zeros on integer part, allow 0.x / .x**
    if '.' in new_value:
        integer_part = new_value.split('.')[0].lstrip('-')
    else:
        integer_part = new_value.lstrip('-')
    
    # Reject if integer part starts with '0' and has more than one digit
    if len(integer_part) > 1 and integer_part[0] == '0':
        return False

    # Finally, make sure it parses as a number
    if new_value != '-' and new_value != '.' and new_value != '-.':
        try:
            Decimal(new_value)
        except InvalidOperation:
            return False
    return True

#----COLOR PALETTE DEFINITIONS----

# Datepicker colors
DP_COLORS = {
    'main_bg'    : '#232323', 
    'main_fg'    : '#f5f5f5',
    'header_bg'  : '#454545', 
    'header_fg'  : '#f5f5f5',
    'otherwe_bg' : '#565656', 
    'otherwe_fg' : '#f5f5f5',
    'weekend_bg' : '#666666', 
    'weekend_fg' : '#f5f5f5',
    'other_bg'   : '#777777', 
    'other_fg'   : '#232323',
    'nm_bg'      : '#888888', 
    'nm_fg'      : 'black',
    'disabled_bg': '#454545', 
    'disabled_fg': '#888888',
    'border'     : '#343434'
}

# Chart color definitions
VIS_CLRS = {
    'normal_text': '#f5f5f5',
    'normal_bg'  : '#313131',
    'chart_bg'   : '#444445',
    'highlighted': '#9D9D9D',
    'indented'   : '#9D9D9D',
    'emphasis'   : '#595959',
    'income'     : '#36B56F',
    'expense'    : '#EB5353',
    'net'        : '#1674b4',
    'neutral'    : '#737373',
}

# Report color definitions
REPORT_CLRS = {
    'normal_text': '#f5f5f5',
    'normal_bg'  : '#313131',
    'chart_bg'   : '#444445',
    'highlighted': '#9D9D9D',
    'indented'   : '#9D9D9D',
    'emphasis'   : '#595959',
    'income'     : '#36B56F',
    'expense'    : '#EB5353',
    'line'       : '#1674b4',
}

# Budget tab color definitions
BDGT_CLRS = {
    'income'     : '#36B56F',
    'expense'    : '#EB5353',
    'savings'    : '#1674b4',
}