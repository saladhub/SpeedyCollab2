import subprocess
import os
import shutil
import argparse
import time
import sys
from fractions import Fraction


# ─── FONT ─────────────────────────────────────────────────────────────────────
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"

# ─── FORMAT → CODEC MAP ───────────────────────────────────────────────────────
FORMAT_CODEC = {
    "mkv": ["-c:a", "pcm_s16le"],
    "mxf": ["-c:v", "mpeg2video", "-qscale", "1", "-qmin", "1", "-c:a", "pcm_s16le", "-ar", "48000"],
    "mov": ["-c:v", "libx264", "-q:v", "1", "-crf", "23", "-preset", "slow", "-q:a", "5"],
    "mp4": ["-c:v", "libx264", "-q:v", "1", "-crf", "23", "-preset", "slow", "-c:a", "flac"],
}

# ─── ANSI COLORS ──────────────────────────────────────────────────────────────
R  = "\033[91m"
G  = "\033[92m"
Y  = "\033[93m"
B  = "\033[94m"
M  = "\033[95m"
C  = "\033[96m"
W  = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RST = "\033[0m"


# ─── TEXT COLOR PRESETS ───────────────────────────────────────────────────────
COLOR_PRESETS = {
    "red":     "#ff0000",
    "white":   "#ffffff",
    "black":   "#000000",
    "yellow":  "#ffff00",
    "green":   "#00ff00",
    "blue":    "#0000ff",
    "cyan":    "#00ffff",
    "magenta": "#ff00ff",
    "orange":  "#ff8800",
    "pink":    "#ff69b4",
}

def resolve_color(value: str) -> str:
    """Accept a preset name or hex code like #ff0000 or ff0000."""
    v = value.strip().lower()
    if v in COLOR_PRESETS:
        return COLOR_PRESETS[v]
    # Normalize hex
    v = v.lstrip("#")
    if len(v) == 6:
        try:
            int(v, 16)
            return f"#{v}"
        except ValueError:
            pass
    return None


def detect_video_codec() -> str:
    """Pick the fastest available intermediate codec."""
    try:
        result = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
        encoders = result.stdout + result.stderr
        if "libx264" in encoders:
            return "libx264"
        if "libx265" in encoders:
            return "libx265"
        if "mpeg4" in encoders:
            return "mpeg4"
    except Exception:
        pass
    return "ffv1"


def intermediate_codec_flags(vcodec: str) -> list:
    if vcodec == "ffv1":
        return ["-c:v", "ffv1"]
    return ["-c:v", vcodec, "-preset", "ultrafast", "-crf", "0"]


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(R + BOLD)
    print(' _________                        .___      _________        .__  .__        ___.                  ________     _______   ')
    print('  /   _____/_____   ____   ____   __| _/__.__.\\_   ___ \\  ____ |  | |  | _____ \\_ |__   ___________  \\_____  \\    \\   _  \\  ')
    print('  \\_____  \\\\____ \\_/ __ \\_/ __ \\/ __ <   |  |/    \\  \\/ /  _ \\|  | |  | \\__  \\ | __ \\_/ __ \\_  __ \\  /  ____/    /  /_\\  \\ ')
    print('  /        \\  |_> >  ___/\\  ___// /_/ |\\___  |\\     \\___(  <_> )  |_|  |__/ __ \\| \\_\\ \\  ___/|  | \\/ /       \\    \\  \\_/   \\\\')
    print(' /_______  /   __/ \\___  >\\___  >____ |/ ____| \\______  /\\____/|____/____(____  /___  /\\___  >__|    \\_______ \\ /\\ \\_____  /')
    print('         \\/|__|        \\/     \\/     \\/\\/             \\/                      \\/    \\/     \\/                \\/ \\/       \\/ ')
    print(RST)
    print(f"  {DIM}[ Patch 1 // Linux Support update & QoL changes ]{RST}")
    print()
def prompt(label: str, default: str, hint: str = "") -> str:
    hint_str = f"{DIM}  {hint}{RST}" if hint else ""
    val = input(f"  {C}{label}{RST} {DIM}[{default}]{RST}{hint_str}: ").strip()
    return val if val else default


def parse_duration(value: str) -> float:
    try:
        return float(Fraction(value))
    except Exception:
        return None


def start_menu(input_file: str) -> dict:
    cls()
    banner()
    print(f"  {DIM}Input:{RST} {W}{input_file}{RST}")
    print(f"  {DIM}{'─'*48}{RST}")
    print()

    # Powers
    while True:
        val = prompt("Powers (iterations)", "55", "how many times to reprocess")
        try:
            powers = int(val)
            if powers > 0:
                break
        except ValueError:
            pass
        print(f"  {R}Must be a positive integer.{RST}")

    # Duration
    while True:
        val = prompt("Duration per export", "0.5", "seconds, or fraction like 30/60")
        dur = parse_duration(val)
        if dur and dur > 0:
            duration = dur
            duration_raw = val
            break
        print(f"  {R}Must be a positive number or fraction.{RST}")

    # Start index (the i+ value)
    while True:
        val = prompt("Counter start (i+?)", "1", "number shown on first frame")
        try:
            start_index = int(val)
            break
        except ValueError:
            print(f"  {R}Must be an integer.{RST}")

    # Text color
    preset_list = ", ".join(COLOR_PRESETS.keys())
    while True:
        val = prompt("Text color", "red", f"preset or hex: {preset_list}")
        color = resolve_color(val)
        if color:
            text_color = color
            break
        print(f"  {R}Invalid color. Use a preset name or hex like #ff0000{RST}")

    # Format
    print(f"\n  {C}Output format{RST} {DIM}[mov]{RST}  {DIM}mp4 / mov / mkv / mxf{RST}: ", end="")
    fmt_input = input().strip().lower()
    fmt = fmt_input if fmt_input in ["mp4", "mov", "mkv", "mxf"] else "mov"

    # Notrim
    notrim_input = prompt("Disable trim? (y/N)", "n", "process full clip length each pass")
    notrim = notrim_input.lower() in ["y", "yes"]

    print()
    print(f"  {DIM}{'─'*48}{RST}")
    print(f"  {DIM}powers   :{RST} {Y}{powers}{RST}")
    print(f"  {DIM}duration :{RST} {Y}{duration_raw}s{RST}")
    print(f"  {DIM}i+       :{RST} {Y}{start_index}{RST}")
    print(f"  {DIM}format   :{RST} {Y}{fmt}{RST}")
    print(f"  {DIM}notrim   :{RST} {Y}{notrim}{RST}")
    print(f"  {DIM}{'─'*48}{RST}")
    print()
    input(f"  {G}Press Enter to start...{RST} ")

    # Rubberband toggle
    rb_input = prompt("Disable rubberband? (y/N)", "n", "faster iterations, no pitch shift")
    no_rubberband = rb_input.lower() in ["y", "yes"]

    # Fast mode
    fast_input = prompt("Fast mode? (y/N)", "n", "half res during iterations, upscale at end")
    fast_mode = fast_input.lower() in ["y", "yes"]

    return {
        "powers": powers,
        "duration": duration,
        "start_index": start_index,
        "format": fmt,
        "notrim": notrim,
        "no_rubberband": no_rubberband,
        "fast_mode": fast_mode,
        "text_color": text_color,
    }


# Fallback font URL if no system font is found
FALLBACK_FONT_URL = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/Arial.ttf"

def resolve_font(font_path: str, local_name: str = "font.ttf") -> str:
    """Find a usable font, falling back to download if needed."""
    # Already copied locally
    if os.path.exists(local_name):
        return local_name

    # Try the provided path (works on Windows)
    if os.path.exists(font_path):
        shutil.copy2(font_path, local_name)
        return local_name

    # Linux/Termux: search common system font locations
    linux_candidates = [
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/data/data/com.termux/files/usr/share/fonts/dejavu-fonts/DejaVuSans-Bold.ttf",
    ]
    for candidate in linux_candidates:
        if os.path.exists(candidate):
            shutil.copy2(candidate, local_name)
            print(f"  {G}Font found:{RST} {DIM}{candidate}{RST}")
            return local_name

    # Nothing found — download fallback
    print(f"  {Y}No system font found, downloading fallback...{RST}")
    try:
        import urllib.request
        urllib.request.urlretrieve(FALLBACK_FONT_URL, local_name)
        print(f"  {G}Font downloaded.{RST}")
        return local_name
    except Exception as e:
        print(f"  {R}Failed to download font: {e}{RST}")
        print(f"  {DIM}Place a font.ttf in the script directory and retry.{RST}")
        sys.exit(1)


def build_vf(local_font: str, counter: int, scale_down: bool = False, text_color: str = "#ff0000") -> str:
    drawtext = (
        f"drawtext=fontfile={local_font}"
        f":text={counter}"
        f":borderw=2"
        f":fontsize=w/8"
        f":fontcolor={text_color}"
        f":x=(w-text_w)/2"
        f":y=(h-text_h)/1.02"
    )
    vf = "hue=0,setpts=1/2*PTS,fps=60"
    if scale_down:
        vf += ",scale=iw/2:ih/2:flags=fast_bilinear"
    vf += f",{drawtext}"
    return vf


def run_iteration(i: int, powers: int, input_file: str, output_file: str, cfg: dict, local_font: str):
    counter = cfg["start_index"] + i

    cmd = ["ffmpeg", "-hide_banner", "-y"]

    if not cfg["notrim"]:
        cmd += ["-stream_loop", "1"]

    cmd += ["-i", input_file]
    scale_down = cfg.get("fast_mode", False)
    cmd += ["-vf", build_vf(local_font, counter, scale_down, cfg.get("text_color", "#ff0000"))]
    vcodec = detect_video_codec()
    if cfg["no_rubberband"]:
        cmd += [*intermediate_codec_flags(vcodec), "-c:a", "pcm_s16le"]
    else:
        cmd += [
            "-filter_complex",
            "[0:a]rubberband=formant=2.14748e+09/4.9:pitch=2^(0/25):detector=712923000/634:tempo=2:pitchq=consistency[a1]"
            ";[a1]amix=1,volume=4,alimiter=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            *intermediate_codec_flags(vcodec),
            "-c:a", "pcm_s16le",
        ]

    if not cfg["notrim"]:
        cmd += ["-t", str(cfg["duration"])]

    cmd += [output_file]

    print(f"  {DIM}[{i}/{powers}]{RST} {input_file} {DIM}->{RST} {output_file}  {DIM}counter: {counter}{RST}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    global FONT_PATH
    # Enable ANSI on Windows
    if os.name == "nt":
        os.system("color")

    # Accept drag-and-drop (file as first arg) or CLI
    # Collect drag-and-drop path: spaces cause argv to split, rejoin non-flag tokens
    raw_argv = sys.argv[1:]
    input_parts = []
    flags = []
    i = 0
    while i < len(raw_argv):
        a = raw_argv[i]
        if a.startswith("-"):
            flags.append(a)
            if i + 1 < len(raw_argv) and not raw_argv[i+1].startswith("-"):
                flags.append(raw_argv[i+1])
                i += 2
            else:
                i += 1
        else:
            input_parts.append(a)
            i += 1
    drag_input = " ".join(input_parts).strip().strip('"').strip("'") if input_parts else None

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-p", "--powers", type=int, default=None)
    parser.add_argument("-d", "--duration", type=str, default=None)
    parser.add_argument("-s", "--start-index", type=int, default=None)
    parser.add_argument("-f", "--format", default=None)
    parser.add_argument("--notrim", action="store_true", default=False)
    parser.add_argument("--no-rubberband", action="store_true", default=False, dest="no_rubberband",
        help="Skip rubberband pitch shifting (faster)")
    parser.add_argument("--fast", action="store_true", default=False, dest="fast_mode",
        help="Half resolution during iterations, upscale at end (much faster)")
    parser.add_argument("--color", default="red", metavar="COLOR",
        help="Text color: preset name or hex code (default: red)")
    parser.add_argument("--font", default=FONT_PATH)
    args = parser.parse_args(flags)
    args.input = drag_input

    if not args.input:
        cls()
        banner()
        print(f"  {R}No input file provided.{RST}")
        print(f"  {DIM}Drag a video file onto this script to use it.{RST}")
        print()
        input("  Press Enter to exit... ")
        sys.exit(1)

    # Normalize path separators and check existence
    args.input = os.path.normpath(args.input)
    exists = os.path.exists(args.input)

    if not exists:
        cls()
        banner()
        print(f"  {R}File not found.{RST}")
        print(f"  {DIM}Path    : {args.input}{RST}")
        print(f"  {DIM}Exists  : {exists}{RST}")
        print(f"  {DIM}Is file : {os.path.isfile(args.input)}{RST}")
        print(f"  {DIM}Repr    : {repr(args.input)}{RST}")
        print(f"  {DIM}Bytes   : {list(args.input.encode())[:20]}{RST}")
        print()
        input("  Press Enter to exit... ")
        sys.exit(1)

    FONT_PATH = args.font

    # If key params were passed via CLI, skip menu
    if args.powers is not None and args.duration is not None:
        dur = parse_duration(args.duration)
        cfg = {
            "powers": args.powers,
            "duration": dur,
            "start_index": args.start_index or 1,
            "format": args.format or "mov",
            "notrim": args.notrim,
            "no_rubberband": args.no_rubberband,
            "fast_mode": args.fast_mode,
            "text_color": resolve_color(args.color) or "#ff0000",
        }
    else:
        cfg = start_menu(args.input)

    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"output.{cfg['format']}")

    local_font = resolve_font(FONT_PATH)

    cls()
    banner()
    print(f"  {G}{BOLD}Running...{RST}")
    print(f"  {DIM}{'─'*48}{RST}")
    print()

    start_time = time.time()

    # Step 1: prep 0.mkv
    print(f"  {Y}Preparing 0.mkv...{RST}")
    prep_vf = "scale=iw/2:ih/2:flags=fast_bilinear" if cfg.get("fast_mode") else None
    vcodec = detect_video_codec()
    print(f"  {DIM}Using codec: {vcodec}{RST}")
    prep_cmd = [
        "ffmpeg", "-hide_banner", "-y",
        "-stream_loop", "1", "-i", args.input,
    ]
    if prep_vf:
        prep_cmd += ["-vf", prep_vf]
    prep_cmd += [
        *intermediate_codec_flags(vcodec),
        "-c:a", "flac",
        "-strict", "experimental",
        "-t", str(cfg["duration"]),
        "0.mkv"
    ]
    subprocess.run(prep_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 2: first pass
    run_iteration(0, cfg["powers"], "0.mkv", "1.mkv", cfg, local_font)

    # Step 3: recursive iterations
    for i in range(1, cfg["powers"] + 1):
        run_iteration(i, cfg["powers"], f"{i}.mkv", f"{i+1}.mkv", cfg, local_font)

    # Step 4: concat list
    print(f"\n  {Y}Concatenating...{RST}")
    with open("concat.txt", "w") as f:
        for i in range(1, cfg["powers"] + 1):
            f.write(f"file '{i}.mkv'\n")

    # Step 5: final output
    codec_flags = FORMAT_CODEC.get(cfg["format"], FORMAT_CODEC["mp4"])
    subprocess.run([
        "ffmpeg", "-hide_banner", "-y",
        "-f", "concat", "-safe", "0", "-i", "concat.txt",
        *codec_flags,
        "-pix_fmt", "yuv420p",
        "-maxrate", "1024K", "-bufsize", "1M",
        "-threads", "0",
        *([ "-vf", "scale=iw*2:ih*2:flags=lanczos"] if cfg.get("fast_mode") else []),
        "-movflags", "+faststart",
        output_file
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elapsed = time.time() - start_time

    # Cleanup
    for i in range(0, cfg["powers"] + 2):
        try:
            os.remove(f"{i}.mkv")
        except FileNotFoundError:
            pass
    for f in ["concat.txt", "font.ttf"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    print()
    print(f"  {DIM}{'─'*48}{RST}")
    print(f"  {G}{BOLD}Done in {elapsed:.3f} seconds{RST}")
    print(f"  {DIM}Output:{RST} {W}{output_file}{RST}")
    print()
    input(f"  {DIM}Press Enter to close...{RST} ")


if __name__ == "__main__":
    main()
    
