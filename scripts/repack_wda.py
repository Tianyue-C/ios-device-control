#!/usr/bin/env python3
"""
repack_wda.py - Automates sanitization and repacking of WebDriverAgentRunner IPA for TrollStore.

Background & Root Cause:
Official Appium WebDriverAgent releases include Mach-O DWARF debug symbol files inside
nested `.dSYM` directories (e.g. `PlugIns/WebDriverAgentRunner.xctest.dSYM`).
When TrollStore installs an IPA, its internal `ldid` signing engine attempts to parse and
pseudo-sign every Mach-O file in the bundle. DWARF files cause `ldid` to fail with:
    "Install Error 175: Failed to sign the app. ldid returned a non zero status code."

This script cleanses the bundle by:
1. Stripping all `.dSYM` folders and intermediate build products.
2. Promoting nested frameworks (e.g. `WebDriverAgentLib.framework`) from inside `PlugIns/`
   up to the standard `Payload/*.app/Frameworks/` root directory.
3. Stripping stale `_CodeSignature` directories so TrollStore / ldid applies clean CoreTrust signatures.
4. Repacking into a clean, standalone installable `.ipa`.
"""

import os
import sys
import shutil
import zipfile
import argparse
import subprocess

def clean_and_repack(input_path: str, output_ipa_path: str, work_dir: str = "/tmp/wda_repack_workspace") -> str:
    print(f"[*] Starting WDA sanitization on: {input_path}")
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    extracted_dir = os.path.join(work_dir, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    # 1. Unzip input
    print(f"[*] Extracting input archive...")
    if not zipfile.is_zipfile(input_path):
        raise ValueError(f"Input file '{input_path}' is not a valid zip/ipa archive.")

    with zipfile.ZipFile(input_path, 'r') as z:
        z.extractall(extracted_dir)

    # Locate the .app directory
    app_dir = None
    for root, dirs, _ in os.walk(extracted_dir):
        for d in dirs:
            if d.endswith(".app"):
                app_dir = os.path.join(root, d)
                break
        if app_dir:
            break

    if not app_dir:
        raise FileNotFoundError("Could not find any '.app' directory in the extracted archive.")

    print(f"[*] Found app bundle at: {app_dir}")

    # 2. Strip all .dSYM folders
    dsym_count = 0
    for root, dirs, _ in os.walk(app_dir, topdown=False):
        for d in dirs:
            if d.endswith(".dSYM"):
                dsym_path = os.path.join(root, d)
                print(f"  [-] Removing debug symbol package: {dsym_path}")
                shutil.rmtree(dsym_path)
                dsym_count += 1
    print(f"[*] Removed {dsym_count} .dSYM package(s).")

    # 3. Strip stale _CodeSignature folders
    sig_count = 0
    for root, dirs, _ in os.walk(app_dir, topdown=False):
        for d in dirs:
            if d == "_CodeSignature":
                sig_path = os.path.join(root, d)
                shutil.rmtree(sig_path)
                sig_count += 1
    print(f"[*] Cleared {sig_count} existing code signature folder(s).")

    # 4. Reorganize nested frameworks (PlugIns -> Frameworks)
    plugins_dir = os.path.join(app_dir, "PlugIns")
    target_frameworks_dir = os.path.join(app_dir, "Frameworks")
    os.makedirs(target_frameworks_dir, exist_ok=True)

    if os.path.exists(plugins_dir):
        for root, dirs, _ in os.walk(plugins_dir, topdown=False):
            for d in list(dirs):
                if d.endswith(".framework"):
                    src_framework = os.path.join(root, d)
                    dst_framework = os.path.join(target_frameworks_dir, d)
                    print(f"  [+] Relocating framework: {d} -> Payload/*.app/Frameworks/")
                    if os.path.exists(dst_framework):
                        shutil.rmtree(dst_framework)
                    shutil.move(src_framework, dst_framework)

    # 5. Build clean Payload structure
    payload_dir = os.path.join(work_dir, "Payload")
    os.makedirs(payload_dir, exist_ok=True)
    clean_app_path = os.path.join(payload_dir, os.path.basename(app_dir))
    shutil.move(app_dir, clean_app_path)

    # 6. Compress into clean IPA
    output_abs_path = os.path.abspath(output_ipa_path)
    if os.path.exists(output_abs_path):
        os.remove(output_abs_path)

    print(f"[*] Packaging clean IPA to: {output_abs_path}")
    zip_cmd = f"cd '{work_dir}' && zip -qr '{output_abs_path}' Payload"
    ret = subprocess.run(zip_cmd, shell=True, check=True)

    # 7. Cleanup
    shutil.rmtree(work_dir)

    size_mb = os.path.getsize(output_abs_path) / (1024 * 1024)
    print(f"[✓] Successfully generated sanitized IPA ({size_mb:.2f} MB): {output_abs_path}")
    return output_abs_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sanitize and repack WDA for TrollStore.")
    parser.add_argument("-i", "--input", required=True, help="Path to input WebDriverAgent zip or ipa")
    parser.add_argument("-o", "--output", default="WebDriverAgentRunner_TrollStore.ipa", help="Output .ipa file path")
    args = parser.parse_args()

    clean_and_repack(args.input, args.output)

