import os
import argparse
from datetime import datetime
from subprocess import run, PIPE
from pathlib import PureWindowsPath, PurePosixPath
import json

# Base processing directory
PROCESSING_DIR = "/backlog"

audio_formats = ("wav", "mp3", "m4a")
video_formats = ("mp4", "mov", "m4v", "avi", "wmv", "mpg")
all_input_formats = audio_formats + video_formats

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print("Running:", " ".join(cmd))
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result

def get_av_metadata(filepath):
    """Get AV metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-print_format", "json", filepath
    ]
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if result.returncode != 0:
        print(f"Warning: ffprobe failed on {filepath}")
        return {}
    data = json.loads(result.stdout)
    metadata = {}
    # Duration
    metadata["duration"] = float(data.get("format", {}).get("duration", 0))
    # Bitrate
    metadata["bit_rate"] = int(data.get("format", {}).get("bit_rate", 0))
    # Codec info
    streams = data.get("streams", [])
    for s in streams:
        if s["codec_type"] == "audio":
            metadata["audio_codec"] = s.get("codec_name")
            metadata["sample_rate"] = s.get("sample_rate")
        elif s["codec_type"] == "video":
            metadata["video_codec"] = s.get("codec_name")
            metadata["width"] = s.get("width")
            metadata["height"] = s.get("height")
    return metadata

def convert_av(infile, outfile, extra_args=None):
    """Convert audio/video using ffmpeg."""
    # Print original file metadata
    meta_in = get_av_metadata(infile)
    dur = meta_in.get("duration")
    if dur:
        mins, secs = divmod(dur, 60)
        print(f"Original duration: {int(mins)}:{int(secs):02d}")
    else:
        print("Original duration: unknown")

    cmd = ["ffmpeg", "-y", "-i", infile]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(outfile)
    run_command(cmd)

    # Print converted file metadata
    meta_out = get_av_metadata(outfile)
    dur_out = meta_out.get("duration")
    if dur_out:
        mins, secs = divmod(dur_out, 60)
        print(f"Converted duration: {int(mins)}:{int(secs):02d}")
    else:
        print("Converted duration: unknown")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="Package ID (e.g. ua950.012_Xf5xzeim7n4yE6tjKKHqLM).")
    parser.add_argument("-i", "--input", required=True, choices=all_input_formats, help="Input format")
    parser.add_argument("-o", "--output", required=True, help="Output format (mp3, ogg, webm).")
    parser.add_argument("-p", "--path", help="Subpath relative to masters directory.", default=None)
    return parser.parse_args()

def main():
    args = parse_args()

    # Normalize package paths
    if "_" in args.package:
        ID = args.package.split("_")[0]
    elif "-" in args.package:
        ID = args.package.split("-")[0]
    else:
        raise ValueError(f"Invalid package name {args.package}")

    package = os.path.join(PROCESSING_DIR, ID, args.package)
    masters = os.path.join(package, "masters")
    derivatives = os.path.join(package, "derivatives")
    metadata = os.path.join(package, "metadata")

    for path in [package, masters, derivatives, metadata]:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Invalid package: {args.package}")

    # Handle optional subpath
    if args.path:
        if "\\" in args.path:
            winPath = PureWindowsPath(args.path)
            masters = str(PurePosixPath(masters, *winPath.parts))
        else:
            masters = os.path.join(masters, os.path.normpath(args.path))
        if not os.path.isdir(masters):
            raise FileNotFoundError(f"Invalid subpath {args.path}")

    input_exts = [f".{args.input.lower()}"]
    if args.input.lower() in audio_formats:
        input_exts = [f".{args.input.lower()}"]
    elif args.input.lower() in video_formats:
        input_exts = [f".{args.input.lower()}"]
    
    # Conversion loop
    for root, _, files in os.walk(masters):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in input_exts:
                continue

            infile = os.path.join(root, file)
            rel_root = os.path.relpath(root, masters)
            out_dir = os.path.join(derivatives, rel_root)
            os.makedirs(out_dir, exist_ok=True)

            base_name = os.path.splitext(file)[0]
            out_file = os.path.join(out_dir, f"{base_name}.{args.output.lower()}")

            # Set sensible defaults for ffmpeg conversions
            extra_args = []
            if args.input.lower() in audio_formats and args.output.lower() == "mp3":
                extra_args = ["-codec:a", "libmp3lame", "-q:a", "2"]
            elif args.input.lower() in audio_formats and args.output.lower() == "ogg":
                extra_args = ["-codec:a", "libvorbis", "-q:a", "5"]
            elif args.input.lower() in video_formats and args.output.lower() == "webm":
                extra_args = [
                    "-codec:v", "libvpx",
                    "-b:v", "1M",
                    "-codec:a", "libvorbis",
                    "-auto-alt-ref", "0",
                    "-row-mt", "1",
                ]

            print(f"\nConverting {infile} → {out_file}")
            convert_av(infile, out_file, extra_args)

    print("Complete!")
    print(f"Finished at {datetime.now()}")

if __name__ == "__main__":
    main()
