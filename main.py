import os
from PIL import Image, ImageOps, ImageFilter
import numpy as np

# === CONFIGURATION ===
source_dir = "source"
convert_dir = "converted"
os.makedirs(convert_dir, exist_ok=True)

files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

if not files:
    print("No images found in 'source' folder.")
    exit()

print("Batch Image to C Array Converter")
print("===============================")
print(f"Found {len(files)} image(s) in '{source_dir}':")
for idx, fname in enumerate(files, 1):
    print(f"  [{idx}] {fname}")

print("\nFor each image, you will be prompted to choose bit depth (1 or 2).")

for fname in files:
    input_file = os.path.join(source_dir, fname)
    print(f"\nProcessing: {fname}")
    while True:
        choice = input("  Convert to [1] 1-bit or [2] 2-bit array? Enter 1 or 2: ").strip()
        if choice in ("1", "2"):
            bit_depth = int(choice)
            break
        else:
            print("  Invalid input. Please enter 1 or 2.")

    img = Image.open(input_file).convert("L")  # Grayscale

    # (Optional) Slight blur can help with clean thresholding
    # img = img.filter(ImageFilter.GaussianBlur(0.5))

    if bit_depth == 1:
        img = img.point(lambda x: 255 if x > 128 else 0, mode='1')
        pixels = np.array(img).flatten()
        packed = []
        for i in range(0, len(pixels), 8):
            byte = 0
            for j in range(8):
                if i + j < len(pixels):
                    bit = 0 if pixels[i + j] == 0 else 1
                    byte |= (bit << (7-j))
            packed.append(byte)
        c_array_type = "uint8_t"
        comment = "1-bit per pixel (black & white), 8 pixels per byte"
    elif bit_depth == 2:
        img = img.quantize(colors=4, method=Image.FASTOCTREE, dither=Image.NONE)
        pixels = np.array(img).flatten()
        packed = []
        for i in range(0, len(pixels), 4):
            byte = 0
            for j in range(4):
                if i + j < len(pixels):
                    pix_val = int(pixels[i + j]) & 0x03
                    byte |= (pix_val << (6 - 2*j))
            packed.append(byte)
        c_array_type = "uint8_t"
        comment = "2-bits per pixel (4 colors), 4 pixels per byte"

    # Clean name for variable
    varname = os.path.splitext(fname)[0].replace(" ", "_")
    out_file = os.path.join(convert_dir, f"{varname}_{bit_depth}bit.c")
    with open(out_file, "w") as f:
        f.write(f"// Array length: {len(packed)} bytes ({comment})\n")
        f.write(f"const {c_array_type} {varname}_{bit_depth}bit[{len(packed)}] = {{\n")
        for i, val in enumerate(packed):
            f.write(f"0x{val:02X}")
            if i < len(packed) - 1:
                f.write(",")
            if (i + 1) % 16 == 0:
                f.write("\n")
        f.write("\n};\n")
    print(f"  Saved: {out_file} ({len(packed)} bytes)")

print("\nAll done!")
