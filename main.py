import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# 5x7 font data for uppercase letters, numbers, and basic punctuation
FONT_5X7 = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
    'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
    'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
    'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
    'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
    'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7F, 0x02, 0x04, 0x02, 0x7F],
    'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
    'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
    'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
    'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
    'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
    'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
    'W': [0x3F, 0x40, 0x30, 0x40, 0x3F],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x03, 0x04, 0x78, 0x04, 0x03],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
    '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x49, 0x4D, 0x33],
    '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3E, 0x49, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x49, 0x3E],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '&': [0x36, 0x49, 0x55, 0x22, 0x50],
    '\'': [0x00, 0x07, 0x03, 0x00, 0x00],
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    '!': [0x00, 0x41, 0x7F, 0x01, 0x00],
    '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
    '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
}

def create_image():
    # Initialize RGB buffer (1024 x 1024, dark background #0F172A)
    bg_color = (15, 23, 42)
    img = bytearray(WIDTH * HEIGHT * 3)
    for i in range(0, len(img), 3):
        img[i] = bg_color[0]
        img[i+1] = bg_color[1]
        img[i+2] = bg_color[2]

    def set_pixel(x, y, color):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = (y * WIDTH + x) * 3
            img[idx] = color[0]
            img[idx+1] = color[1]
            img[idx+2] = color[2]

    def draw_rect(x, y, w, h, color):
        for cy in range(y, y + h):
            if 0 <= cy < HEIGHT:
                start = (cy * WIDTH + max(0, x)) * 3
                end = (cy * WIDTH + min(WIDTH, x + w)) * 3
                for i in range(start, end, 3):
                    img[i] = color[0]
                    img[i+1] = color[1]
                    img[i+2] = color[2]

    def draw_line(x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_circle(cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx)**2 + (y - cy)**2 <= r**2:
                    set_pixel(x, y, color)

    def draw_icon(icon_type, ix, iy, color):
        cx, cy = ix + 14, iy + 14
        if icon_type == "missile":
            draw_line(ix + 4, iy + 20, ix + 22, iy + 8, color)
            draw_line(ix + 22, iy + 8, ix + 18, iy + 18, color)
            draw_line(ix + 4, iy + 20, ix + 10, iy + 24, color)
            draw_circle(cx - 4, cy + 4, 2, color)
        elif icon_type == "bridge":
            for x in range(ix + 2, ix + 26):
                dy = int(12 - 12 * ((x - cx) / 12)**2)
                set_pixel(x, iy + 22 - dy, color)
                set_pixel(x, iy + 23 - dy, color)
            draw_line(ix + 4, iy + 22, ix + 24, iy + 22, color)
            draw_line(ix + 4, iy + 22, ix + 4, iy + 26, color)
            draw_line(ix + 24, iy + 22, ix + 24, iy + 26, color)
        elif icon_type == "monitor":
            draw_rect(ix + 2, iy + 6, 24, 16, color)
            draw_rect(ix + 4, iy + 8, 20, 12, (30, 41, 59))
            draw_line(ix + 12, iy + 22, ix + 16, iy + 22, color)
            draw_line(ix + 14, iy + 22, ix + 14, iy + 25, color)
            draw_line(ix + 10, iy + 25, ix + 18, iy + 25, color)
        elif icon_type == "virus_spikes":
            draw_circle(cx, cy, 6, color)
            draw_line(cx - 10, cy, cx - 6, cy, color)
            draw_line(cx + 6, cy, cx + 10, cy, color)
            draw_line(cx, cy - 10, cx, cy - 6, color)
            draw_line(cx, cy + 6, cx, cy + 10, color)
            draw_line(cx - 7, cy - 7, cx - 4, cy - 4, color)
            draw_line(cx + 4, cy + 4, cx + 7, cy + 7, color)
            draw_line(cx + 7, cy - 7, cx + 4, cy - 4, color)
            draw_line(cx - 7, cy + 7, cx - 4, cy - 4, color)
        elif icon_type == "ballot":
            draw_rect(ix + 4, iy + 10, 20, 14, color)
            draw_rect(ix + 7, iy + 12, 14, 10, (30, 41, 59))
            draw_line(ix + 10, iy + 7, ix + 18, iy + 7, color)
            draw_line(ix + 4, iy + 10, ix + 24, iy + 10, color)
        elif icon_type == "virus":
            draw_circle(cx, cy, 8, color)
            draw_circle(cx - 3, cy - 3, 2, (30, 41, 59))
            draw_circle(cx + 3, cy + 3, 2, (30, 41, 59))

    def draw_char(ch, x, y, scale, color):
        ch_upper = ch.upper()
        glyph = FONT_5X7.get(ch_upper, FONT_5X7['?'])
        for col_idx, col_val in enumerate(glyph):
            for row_idx in range(7):
                if (col_val >> row_idx) & 1:
                    for sx in range(scale):
                        for sy in range(scale):
                            set_pixel(x + col_idx * scale + sx, y + row_idx * scale + sy, color)

    def draw_text(text, x, y, scale, color):
        cur_x = x
        char_w = 6 * scale
        for ch in text:
            if ch == '\n':
                pass
            else:
                draw_char(ch, cur_x, y, scale, color)
                cur_x += char_w

    def wrap_text(text, scale, max_w):
        limit = max_w // (6 * scale)
        result = []
        for segment in text.split('\n'):
            chunks = segment.split(' ')
            current = ''
            for word in chunks:
                combined = (current + ' ' + word).strip()
                if len(combined) <= limit:
                    current = combined
                else:
                    if current:
                        result.append(current)
                    while len(word) > limit:
                        result.append(word[:limit])
                        word = word[limit:]
                    current = word
            if current or not result:
                result.append(current)
        return result

    def draw_wrapped(text, x, y, scale, color, max_w, line_h):
        lines_list = wrap_text(text, scale, max_w)
        for idx, line_text in enumerate(lines_list):
            draw_text(line_text, x, y + idx * line_h, scale, color)
        return len(lines_list)

    # --- DRAWING POSTER LAYOUT ---

    # 1. Header Banner
    draw_rect(0, 0, WIDTH, 104, (30, 41, 59))
    draw_rect(0, 100, WIDTH, 4, (59, 130, 246))

    # Header Titles
    draw_text("WEDNESDAY 18 NOVEMBER 2026", 48, 24, 3, (255, 255, 255))
    draw_text("THE WORLD TODAY IN SIX STORIES", 48, 66, 2, (148, 163, 184))

    # 2. News Cards (6 stories in 2x3 grid)
    stories = [
        {
            "cat": "GEOPOLITICS",
            "cat_color": (239, 68, 68), # Red
            "headline": "US STRIKES IRAN AS GULF CRISIS GROWS",
            "desc": "US jets hit a missile site on Qeshm Island, Iran fires drones at US bases in Bahrain and Kuwait.",
            "icon": "missile"
        },
        {
            "cat": "UKRAINE CONFLICT",
            "cat_color": (234, 179, 8), # Amber
            "headline": "CRIMEAN BRIDGE PARTLY COLLAPSES",
            "desc": "Zelensky hails unprecedented strike as Putin's strategic bridge suffers major damage after attack.",
            "icon": "bridge"
        },
        {
            "cat": "TECHNOLOGY",
            "cat_color": (59, 130, 246), # Blue
            "headline": "US OUTAGES SPREAD, REACH THE NSA",
            "desc": "Repeated computer outages hit US systems, officials see no sign of a systemic attack.",
            "icon": "monitor"
        },
        {
            "cat": "PUBLIC HEALTH",
            "cat_color": (168, 85, 247), # Purple
            "headline": "US LOSES MEASLES ELIMINATION STATUS",
            "desc": "United States loses elimination status after 26 years following record cases and 10 deaths.",
            "icon": "virus_spikes"
        },
        {
            "cat": "US POLITICS",
            "cat_color": (20, 184, 166), # Teal
            "headline": "DEMOCRATS WIN ALASKA SENATE RACE",
            "desc": "Mary Peltola wins Alaska, Democrats take a 56-44 Senate majority.",
            "icon": "ballot"
        },
        {
            "cat": "PUBLIC HEALTH",
            "cat_color": (168, 85, 247), # Purple
            "headline": "EBOLA SURGE IN CONGO TOPS 11,000 CASES",
            "desc": "DRC outbreak doubles in three months, over 5,400 dead, children hit hardest.",
            "icon": "virus"
        },
    ]

    card_w = 440
    card_h = 230
    cols = 2
    start_x = 48
    start_y = 106
    gap_x = 48
    gap_y = 16

    for idx, s in enumerate(stories):
        c = idx % cols
        r = idx // cols
        x = start_x + c * (card_w + gap_x)
        y = start_y + r * (card_h + gap_y)

        # Card Background
        draw_rect(x, y, card_w, card_h, (30, 41, 59))
        # Card Top Accent Bar
        draw_rect(x, y, card_w, 8, s["cat_color"])

        # Category Tag
        draw_text(s["cat"], x + 20, y + 20, 2, s["cat_color"])

        # Icon at top right
        draw_icon(s["icon"], x + card_w - 44, y + 14, s["cat_color"])

        # Headline
        draw_wrapped(s["headline"], x + 20, y + 48, 2, (255, 255, 255),
                     card_w - 40, 20)

        # Divider line inside card
        draw_rect(x + 20, y + 92, card_w - 40, 2, (51, 65, 85))

        # Description
        draw_wrapped(s["desc"], x + 20, y + 108, 2,
                     (203, 213, 225), card_w - 40, 20)

        # Bottom status/source tag in card
        draw_text("VERIFIED WORLD NEWS REPORT", x + 20, y + card_h - 22, 1, (100, 116, 139))

    # 3. Footer Banner
    draw_rect(0, 884, WIDTH, 34, (30, 41, 59))
    draw_text("NEWS-IMAGE-20261118 - DETERMINISTIC RENDER", 48, 894, 1, (148, 163, 184))

    # --- PNG ENCODER ---
    def make_png(width, height, rgb_data):
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

        row_size = width * 3
        raw_scanlines = bytearray()
        for y in range(height):
            raw_scanlines.append(0)
            start = y * row_size
            raw_scanlines.extend(rgb_data[start:start+row_size])

        compressed_data = zlib.compress(raw_scanlines, level=9)
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        
        png = bytearray(b'\x89PNG\r\n\x1a\n')
        png.extend(chunk(b'IHDR', ihdr_data))
        png.extend(chunk(b'IDAT', compressed_data))
        png.extend(chunk(b'IEND', b''))
        return bytes(png)

    png_bytes = make_png(WIDTH, HEIGHT, img)
    
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'entry.png')
    
    with open(out_path, 'wb') as f:
        f.write(png_bytes)
    
    print(f"Successfully wrote {len(png_bytes)} bytes to {out_path}")

if __name__ == '__main__':
    create_image()
