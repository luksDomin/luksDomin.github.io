import os
import re
import uuid
from datetime import datetime
from PIL import Image

ROOT_SEARCH_DIR = os.getcwd()
OUTPUT_DIR = "output_copy"
SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

def find_directory_recursive(root, target_name):
    for dirpath, dirnames, _ in os.walk(root):
        if target_name in dirnames:
            return os.path.join(dirpath, target_name)
    return None

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def extract_image_references(md_content):
    """
    Extrae referencias Obsidian:
    ![[image.png]]
    ![[image.png|500]]
    """
    pattern = r'!\[\[([^|\]]+\.(?:png|jpg|jpeg|webp))(?:\|\d+)?\]\]'
    return set(re.findall(pattern, md_content, flags=re.IGNORECASE))

def convert_images(attachments_dir, used_images, output_images_dir):
    ensure_dir(output_images_dir)
    image_map = {}
    unused_images = []

    for file in os.listdir(attachments_dir):
        if not file.lower().endswith(SUPPORTED_EXTENSIONS):
            continue

        if file not in used_images:
            unused_images.append(file)
            continue

        src = os.path.join(attachments_dir, file)
        new_name = f"{uuid.uuid4()}.webp"
        dst = os.path.join(output_images_dir, new_name)

        img = Image.open(src).convert("RGB")
        img.save(dst, "WEBP")

        image_map[file] = new_name

    return image_map, unused_images

def process_markdown(md_content, image_map, machine):
    for original, new_name in image_map.items():
        pattern = rf'!\[\[{re.escape(original)}(?:\|\d+)?\]\]'
        replacement = f"![](/assets/machines/{machine.lower()}.htb/images/{new_name})"
        md_content = re.sub(pattern, replacement, md_content)

    return md_content

def main():
    machine = input("¿Qué máquina de Hack The Box quieres documentar?: ").strip()

    source_dir = find_directory_recursive(ROOT_SEARCH_DIR, machine)
    if not source_dir:
        print(f"[✘] No se encontró el directorio '{machine}'")
        return

    md_src = os.path.join(source_dir, f"{machine}.md")
    attachments_dir = os.path.join(source_dir, "attachments")

    if not os.path.isfile(md_src) or not os.path.isdir(attachments_dir):
        print("[✘] Falta el .md o el directorio attachments")
        return

    with open(md_src, "r", encoding="utf-8") as f:
        md_content = f.read()

    used_images = extract_image_references(md_content)

    images_dst = os.path.join(
        OUTPUT_DIR,
        "assets",
        "machines",
        f"{machine.lower()}.htb",
        "images"
    )

    image_map, unused_images = convert_images(
        attachments_dir,
        used_images,
        images_dst
    )

    final_md = process_markdown(md_content, image_map, machine)

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    md_dst = os.path.join(
        OUTPUT_DIR,
        f"{date_prefix}-{machine.lower()}.htb.md"
    )

    ensure_dir(OUTPUT_DIR)

    with open(md_dst, "w", encoding="utf-8") as f:
        f.write(final_md)

    print("\n[✔] Proceso completado correctamente")
    print(f"[📄] Markdown generado: {md_dst}")
    print(f"[🖼] Imágenes usadas: {len(image_map)}")

    if unused_images:
        print("\n[⚠] Imágenes SIN referencia en el markdown:")
        for img in unused_images:
            print(f"   - {img}")
    else:
        print("\n[✔] Todas las imágenes estaban referenciadas")

if __name__ == "__main__":
    main()
