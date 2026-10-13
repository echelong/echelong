#!/usr/bin/env python3
"""Check the profile README and its assets.

    python3 scripts/validate_profile.py            # offline checks
    python3 scripts/validate_profile.py --online   # also request every external URL

GIF checks (frames, looping, visible motion, opacity, fallback size) need
Pillow. If it is not installed they are reported as failed, not skipped.
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MAX_GIF_BYTES = 1_500_000
MAX_ASSET_BYTES = 4_000_000
REQUIRED_LINKS = (
    "mailto:cobalt@mail.grokbot.com",
    "https://x.com/CobaltHere",
    "https://github.com/echelong?tab=repositories",
)

results = []


def check(ok, label, detail=""):
    results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", label, (" - " + detail) if detail else ""))


def attr(tag, name):
    match = re.search(r'\b%s="([^"]*)"' % name, tag)
    return match.group(1) if match else None


def is_local(url):
    return not re.match(r"^(https?:|mailto:|#)", url)


def gif_checks(gif_path, png_path):
    try:
        from PIL import Image, ImageChops
    except ImportError:
        check(False, "%s frame checks ran" % gif_path.name,
              "Pillow is not installed: python3 -m pip install pillow")
        return

    def opaque(image):
        return image.convert("RGBA").getextrema()[3][0] == 255

    gif = Image.open(gif_path)
    frames, durations, solid = [], [], True
    for index in range(gif.n_frames):
        gif.seek(index)
        durations.append(gif.info.get("duration", 0))
        solid = solid and opaque(gif)
        frames.append(gif.convert("RGB").resize((240, 60)))
    check(len(frames) >= 8, "%s is animated" % gif_path.name, "%d frames" % len(frames))
    # No transparent pixels, so the page background never shows through in any theme.
    check(solid, "%s is opaque in every frame" % gif_path.name)
    check(gif.info.get("loop") == 0, "%s loops forever" % gif_path.name)
    check(min(durations) >= 20, "%s frame delays are browser-safe" % gif_path.name,
          "%d-%d ms" % (min(durations), max(durations)))

    def changed(a, b):
        diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 24 else 0)
        return diff.histogram()[255] / (diff.size[0] * diff.size[1])

    steps = [changed(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    seam = changed(frames[-1], frames[0])
    check(max(steps) > 0.002, "%s shows visible motion" % gif_path.name,
          "up to %.1f%% of pixels change per frame" % (max(steps) * 100))
    check(seam <= max(steps) * 1.5 + 0.002, "%s loop seam is no larger than a normal step" % gif_path.name,
          "seam %.2f%%, largest step %.2f%%" % (seam * 100, max(steps) * 100))
    still = Image.open(png_path)
    check(still.size == gif.size, "%s matches %s in size" % (png_path.name, gif_path.name),
          "%dx%d" % gif.size)
    check(opaque(still), "%s is opaque" % png_path.name)


def main():
    online = "--online" in sys.argv
    text = README.read_text(encoding="utf-8")
    check(True, "README.md found", "%d bytes" % len(text.encode("utf-8")))

    images = re.findall(r"<img\b[^>]*>", text)
    check(len(images) > 0, "README contains images", "%d <img> tags" % len(images))
    for tag in images:
        alt = attr(tag, "alt") or ""
        check(len(alt.strip()) >= 3, "alt text present", (attr(tag, "src") or "")[-48:])

    local = set()
    for tag in images:
        src = attr(tag, "src") or ""
        if is_local(src):
            local.add(src)
    for tag in re.findall(r"<source\b[^>]*>", text):
        local.add(attr(tag, "srcset") or "")
    for href in re.findall(r'href="([^"]+)"', text) + re.findall(r"\]\(([^)\s]+)\)", text):
        if is_local(href):
            local.add(href)
    for ref in sorted(local):
        check((ROOT / ref).is_file(), "local file exists", ref)

    for block in re.findall(r"<picture>.*?</picture>", text, flags=re.S):
        img = re.search(r"<img\b[^>]*>", block)
        src = attr(img.group(0), "src") if img else ""
        source = re.search(r'<source\b[^>]*prefers-reduced-motion:\s*reduce[^>]*>', block)
        fallback = attr(source.group(0), "srcset") if source else None
        check(bool(fallback) and fallback.endswith(".png"), "reduced-motion still declared", src)
        if fallback and src.endswith(".gif"):
            gif_checks(ROOT / src, ROOT / fallback)
    for tag in images:
        src = attr(tag, "src") or ""
        if src.endswith(".gif"):
            check(any(src in block for block in re.findall(r"<picture>.*?</picture>", text, flags=re.S)),
                  "animated image is wrapped in <picture>", src)

    assets = [p for p in (ROOT / "assets").iterdir() if p.suffix in (".gif", ".png")]
    for path in sorted(assets):
        if path.suffix == ".gif":
            check(path.stat().st_size <= MAX_GIF_BYTES, "%s within size budget" % path.name,
                  "%.0f KB" % (path.stat().st_size / 1024))
    total = sum(p.stat().st_size for p in assets)
    check(total <= MAX_ASSET_BYTES, "assets within total budget", "%.2f MB" % (total / 1e6))
    used = {Path(ref).name for ref in local}
    for path in sorted(assets):
        check(path.name in used, "asset is referenced by the README", path.name)

    for link in REQUIRED_LINKS:
        check(link in text, "contact link present", link)

    external = sorted(set(re.findall(r'https?://[^\s"\')<>]+', text)))
    print("INFO  %d external URLs on hosts: %s" % (
        len(external), ", ".join(sorted({u.split("/")[2] for u in external}))))
    if online:
        for url in external:
            request = urllib.request.Request(url, headers={"User-Agent": "profile-validator"})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    kind = response.headers.get("Content-Type", "")
                    ok = response.status == 200 and ("svg" in kind if "img.shields.io" in url else True)
                    check(ok, "URL responds", "%s %s" % (response.status, url))
            except Exception as error:  # report, do not crash: some hosts refuse scripted requests
                check(False, "URL responds", "%s (%s)" % (url, error))

    failed = results.count(False)
    print("\n%d checks, %d failed" % (len(results), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
