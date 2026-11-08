#!/usr/bin/env python3
"""
ios_controller.py - Unified CLI tool for autonomous iOS device control via WebDriverAgent & pymobiledevice3.

Supported Subcommands:
  - status: Check device connectivity and WDA readiness.
  - screenshot: Capture full-resolution screen image.
  - window-size: Fetch device canvas dimensions (width, height in points).
  - list-elements: Inspect UI element tree with bounding boxes.
  - launch: Launch an app by bundle identifier.
  - tap: Tap UI element by selector (name, xpath, etc.) or (x, y) coordinates.
  - swipe: Perform swipe gesture between coordinates.
  - type: Type text into active element.
  - press: Press hardware buttons (home, volumeup, volumedown, lock).
  - ocr: Run Apple Vision OCR on device screen with bounding boxes.
"""

import os
import sys
import json
import argparse
import subprocess

DEFAULT_XCTRUNNER = "com.facebook.WebDriverAgentRunner.xctrunner"

def run_wda_cmd(args_list, timeout=15):
    cmd = [sys.executable, "-m", "pymobiledevice3", "developer", "wda"] + args_list
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    # Filter out log lines from pymobiledevice3
    stdout_lines = [l for l in proc.stdout.splitlines() if not l.startswith("202")]
    cleaned_stdout = "\n".join(stdout_lines).strip()
    return proc.returncode, cleaned_stdout, proc.stderr

def cmd_status(args):
    code, out, err = run_wda_cmd(["status", "--xctrunner", args.xctrunner])
    if code != 0:
        print(f"[-] WDA status check failed:\n{err}", file=sys.stderr)
        sys.exit(1)
    
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw_output": out}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[✓] Status written to: {args.output}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

def cmd_screenshot(args):
    output_path = args.output or "screen.png"
    cmd = [sys.executable, "-m", "pymobiledevice3", "developer", "dvt", "screenshot", output_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[-] Failed to capture screenshot:\n{proc.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"[✓] Screenshot captured to: {output_path}")

def cmd_window_size(args):
    code, out, err = run_wda_cmd(["window-size", "--xctrunner", args.xctrunner])
    if code != 0:
        print(f"[-] Failed to get window size:\n{err}", file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(out)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[✓] Window size written to: {args.output}")
    else:
        print(json.dumps(data, indent=2))

def cmd_list_elements(args):
    wda_args = ["list-items", "--with-rect", "--xctrunner", args.xctrunner]
    if args.visible_only:
        pass
    code, out, err = run_wda_cmd(wda_args, timeout=25)
    if code != 0:
        print(f"[-] Failed to list UI elements:\n{err}", file=sys.stderr)
        sys.exit(1)

    items = json.loads(out)
    if args.visible_only:
        items = [i for i in items if i.get("visible") == "true"]

    output_path = args.output or "elements.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"[✓] Dumped {len(items)} elements to: {output_path}")

def cmd_launch(args):
    code, out, err = run_wda_cmd(["launch", args.bundle_id, "--xctrunner", args.xctrunner])
    if code != 0:
        print(f"[-] Failed to launch {args.bundle_id}:\n{err}", file=sys.stderr)
        sys.exit(1)
    print(f"[✓] Successfully launched: {args.bundle_id} (Session: {out.strip()})")

def cmd_tap(args):
    if args.selector:
        wda_args = ["tap", args.selector, "--using", args.using, "--xctrunner", args.xctrunner]
        code, out, err = run_wda_cmd(wda_args)
        if code != 0:
            print(f"[-] Tap by selector failed:\n{err}", file=sys.stderr)
            sys.exit(1)
        print(f"[✓] Tapped element: {args.selector}")
    elif args.x is not None and args.y is not None:
        # Tap coordinates via swipe from x,y to x,y or xpath tap
        # In WDA, a quick swipe with dx=0, dy=0 is an instant tap at coordinate
        wda_args = ["swipe", str(args.x), str(args.y), str(args.x), str(args.y), "--duration", "0.05", "--xctrunner", args.xctrunner]
        code, out, err = run_wda_cmd(wda_args)
        if code != 0:
            print(f"[-] Tap at coordinate ({args.x}, {args.y}) failed:\n{err}", file=sys.stderr)
            sys.exit(1)
        print(f"[✓] Tapped coordinate: ({args.x}, {args.y})")
    else:
        print("[-] Either --selector or both -x and -y must be specified.", file=sys.stderr)
        sys.exit(1)

def cmd_press(args):
    code, out, err = run_wda_cmd(["press", args.button, "--xctrunner", args.xctrunner])
    if code != 0:
        print(f"[-] Failed to press button {args.button}:\n{err}", file=sys.stderr)
        sys.exit(1)
    print(f"[✓] Pressed hardware button: {args.button}")

def cmd_swipe(args):
    wda_args = ["swipe", str(args.x1), str(args.y1), str(args.x2), str(args.y2), "--duration", str(args.duration), "--xctrunner", args.xctrunner]
    code, out, err = run_wda_cmd(wda_args)
    if code != 0:
        print(f"[-] Swipe failed:\n{err}", file=sys.stderr)
        sys.exit(1)
    print(f"[✓] Swiped from ({args.x1}, {args.y1}) to ({args.x2}, {args.y2})")

def cmd_ocr(args):
    image_path = args.image
    if not os.path.exists(image_path):
        print(f"[-] Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    swift_script = f"""
import Foundation
import Vision
import AppKit

let url = URL(fileURLWithPath: "{os.path.abspath(image_path)}")
guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {{
    exit(1)
}}

var results: [[String: Any]] = []
let request = VNRecognizeTextRequest {{ req, err in
    guard let observations = req.results as? [VNRecognizedTextObservation] else {{ return }}
    for obs in observations {{
        if let top = obs.topCandidates(1).first {{
            let box = obs.boundingBox
            results.append([
                "text": top.string,
                "confidence": top.confidence,
                "x": box.origin.x,
                "y": box.origin.y,
                "width": box.size.width,
                "height": box.size.height
            ])
        }}
    }}
}}
request.recognitionLevel = .accurate
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])

if let jsonData = try? JSONSerialization.data(withJSONObject: results, options: .prettyPrinted),
   let jsonStr = String(data: jsonData, encoding: .utf8) {{
    print(jsonStr)
}}
"""
    proc = subprocess.run(["swift", "-"], input=swift_script, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[-] OCR failed:\n{proc.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        items = json.loads(proc.stdout)
    except Exception:
        items = []

    output_path = args.output or "ocr_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"[✓] Extracted {len(items)} text segments to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Autonomous iOS Device Controller CLI")
    parser.add_argument("--xctrunner", default=DEFAULT_XCTRUNNER, help="WDA XCUITest runner bundle identifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Get WDA status")
    p_status.add_argument("-o", "--output", help="Save status JSON to file")

    # screenshot
    p_ss = subparsers.add_parser("screenshot", help="Capture hardware screenshot")
    p_ss.add_argument("-o", "--output", default="screen.png", help="Path to save PNG screenshot")

    # window-size
    p_ws = subparsers.add_parser("window-size", help="Get screen dimensions in points")
    p_ws.add_argument("-o", "--output", help="Save window size JSON to file")

    # list-elements
    p_le = subparsers.add_parser("list-elements", help="List UI element tree")
    p_le.add_argument("-o", "--output", default="elements.json", help="Path to save elements JSON")
    p_le.add_argument("--visible-only", action="store_true", help="Only return visible elements")

    # launch
    p_l = subparsers.add_parser("launch", help="Launch app by bundle ID")
    p_l.add_argument("bundle_id", help="Target app bundle identifier")

    # tap
    p_tap = subparsers.add_parser("tap", help="Tap UI element or coordinate")
    p_tap.add_argument("-s", "--selector", help="Element selector string")
    p_tap.add_argument("-u", "--using", default="accessibility id", choices=["accessibility id", "name", "label", "xpath"])
    p_tap.add_argument("-x", type=float, help="X coordinate in points")
    p_tap.add_argument("-y", type=float, help="Y coordinate in points")

    # press
    p_pr = subparsers.add_parser("press", help="Press hardware button")
    p_pr.add_argument("button", choices=["home", "volumeup", "volumedown", "lock"], help="Button name")

    # swipe
    p_sw = subparsers.add_parser("swipe", help="Perform swipe gesture")
    p_sw.add_argument("x1", type=float)
    p_sw.add_argument("y1", type=float)
    p_sw.add_argument("x2", type=float)
    p_sw.add_argument("y2", type=float)
    p_sw.add_argument("--duration", type=float, default=0.3, help="Duration in seconds")

    # ocr
    p_ocr = subparsers.add_parser("ocr", help="Run Apple Vision OCR on an image")
    p_ocr.add_argument("-i", "--image", required=True, help="Image path to OCR")
    p_ocr.add_argument("-o", "--output", default="ocr_results.json", help="Path to save OCR results JSON")

    args = parser.parse_args()

    dispatch = {
        "status": cmd_status,
        "screenshot": cmd_screenshot,
        "window-size": cmd_window_size,
        "list-elements": cmd_list_elements,
        "launch": cmd_launch,
        "tap": cmd_tap,
        "press": cmd_press,
        "swipe": cmd_swipe,
        "ocr": cmd_ocr,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()

