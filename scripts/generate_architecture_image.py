import os
import subprocess
from PIL import Image, ImageChops

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML_PATH = os.path.abspath("render_arch.html")
OUTPUT_PNG = os.path.abspath("submission/final_architecture.png")

# Read authoritative mermaid code from docs/architecture/final_system_architecture.md
with open("docs/architecture/final_system_architecture.md", "r", encoding="utf-8") as f:
    arch_doc = f.read()

mermaid_code = arch_doc.split("```mermaid")[1].split("```")[0].strip()

html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Udyam360 System Architecture</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 40px;
      background-color: #ffffff;
      display: inline-block;
    }}
    .header {{
      text-align: center;
      margin-bottom: 25px;
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      font-size: 32px;
      color: #0f172a;
      font-weight: 800;
    }}
    .header p {{
      margin: 0;
      font-size: 18px;
      color: #64748b;
    }}
    .mermaid {{
      background: #ffffff;
      padding: 24px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis'
      }}
    }});
  </script>
</head>
<body>
  <div class="header">
    <h1>Udyam360 — End-to-End System Architecture</h1>
    <p>Airtel SYNC Hackathon 2026 • Enterprise Track A • Final Component & Execution Boundary Blueprint</p>
  </div>
  <div class="mermaid">
{mermaid_code}
  </div>
</body>
</html>
"""

def main():
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {HTML_PATH}")

    file_url = "file:///" + HTML_PATH.replace("\\", "/")
    print(f"Rendering architecture diagram via Chrome to {OUTPUT_PNG}...")

    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={OUTPUT_PNG}",
        "--window-size=5000,1600",
        "--virtual-time-budget=6000",
        "--hide-scrollbars",
        "--disable-gpu",
        file_url
    ]
    subprocess.run(cmd, check=True)

    if os.path.exists(OUTPUT_PNG):
        im = Image.open(OUTPUT_PNG).convert("RGB")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        diff = ImageChops.difference(im, bg)
        bbox = diff.getbbox()
        print(f"Original render size: {im.size}, content bbox: {bbox}")
        
        # Crop with 30px padding around all edges
        pad = 30
        crop_box = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(im.size[0], bbox[2] + pad),
            min(im.size[1], bbox[3] + pad)
        )
        cropped_im = im.crop(crop_box)
        cropped_im.save(OUTPUT_PNG, "PNG", optimize=True)
        
        final_size = os.path.getsize(OUTPUT_PNG)
        print(f"Cropped & saved architecture diagram: {final_size} bytes, dimensions {cropped_im.size}")
        extrema = cropped_im.getextrema()
        print(f"Extrema: {extrema}")
        if not all(e[0] == e[1] for e in extrema):
            print("Successfully rendered high-resolution, unclipped architecture diagram!")
        else:
            print("Warning: rendered image appears blank.")
    
    if os.path.exists(HTML_PATH):
        os.remove(HTML_PATH)

if __name__ == "__main__":
    main()
