---
name: ios-device-control
description: >-
  Autonomous control and automation of physical iOS devices (iPhone/iPad) from Mac/PC
  without jailbreak, without paid developer accounts, and without 7-day certificate
  revocation. Provides high-res screenshots, UI element inspection, native OCR,
  precise tapping, swiping, text typing, app launching, and hardware button control via
  WebDriverAgent and pymobiledevice3.
metadata:
  version: 1.0.0
  author: Open Source Contributor
  tags: [ios, automation, rpa, agent, trollstore, wda, pymobiledevice3]
---

# iOS Device Control (Agent Skill)

Provides an end-to-end toolchain for an autonomous AI Agent to drive, inspect, and automate a physical iPhone/iPad connected via USB, without jailbreak, without paid developer accounts, and without 7-day certificate revocation limits.

## Overview

Traditional iOS automation requires paid developer accounts or tethered Xcode debug sessions that revoke every 7 days. This skill employs a permanent, robust architecture:
1. **CoreTrust Persistence (TrollStore)**: Permanently installs the WebDriverAgent runner bundle as a system-level app using TrollStore/TrollRestore, bypassing certificate expiration permanently.
2. **Bundle Sanitization**: Strips `.dSYM` DWARF Mach-O symbols and normalizes framework hierarchies to resolve TrollStore `Install Error 175 (ldid returned a non zero status code)`.
3. **USB Protocol Driver (`pymobiledevice3` + WDA)**: Communicates over `usbmuxd` and Apple `testmanagerd` services to drive UI interactions without Xcode GUI overhead.

## Architecture

```
[ AI Agent / Mac Terminal ]
        │
        ▼ (Python CLI: ios_controller.py)
   pymobiledevice3
        │
   (USB / usbmuxd tunnel)
        ▼
   Apple testmanagerd & DDI (Developer Disk Image)
        │
        ▼
WebDriverAgentRunner-Runner (Permanently installed via TrollStore)
        │
   (Accessibility & XCTest APIs)
        ▼
[ Target iOS Apps: Settings, Safari, App Store, etc. ]
```

## Quick Start

### 1. Prerequisites
Ensure device is in Developer Mode with DDI mounted:
```bash
# Reveal developer mode menu (if not yet visible)
pymobiledevice3 amfi reveal-developer-mode

# Auto-mount Developer Disk Image (iOS 16.x)
pymobiledevice3 mounter auto-mount
```

### 2. Verify WDA Status
```bash
python3 scripts/ios_controller.py status
```
Expected output: `"ready": true`, `"state": "success"`, `"message": "WebDriverAgent is ready to accept commands"`.

---

## Agent Command Reference

The agent executes actions via `scripts/ios_controller.py`. All structured inspection commands write results to files to keep token usage minimal.

### 1. Screen Capture
Capture full hardware screenshot to PNG:
```bash
python3 scripts/ios_controller.py screenshot -o /tmp/screen.png
```

### 2. UI Element Inspection
Dump all visible UI elements, coordinates, and labels to a JSON file:
```bash
python3 scripts/ios_controller.py list-elements --visible-only -o /tmp/elements.json
```

### 3. Screen Text Extraction (Apple Vision OCR)
Perform high-accuracy native OCR with normalized bounding boxes:
```bash
python3 scripts/ios_controller.py ocr -i /tmp/screen.png -o /tmp/ocr_results.json
```

### 4. App Launching
Launch an app using its bundle identifier:
```bash
# Launch Safari
python3 scripts/ios_controller.py launch com.apple.mobilesafari

# Launch iOS Settings
python3 scripts/ios_controller.py launch com.apple.Preferences
```

### 5. Touch & Tap Interactions
```bash
# Tap by accessibility name / label / xpath
python3 scripts/ios_controller.py tap -s "设置" -u name
python3 scripts/ios_controller.py tap -s '//XCUIElementTypeSwitch[@name="查找我的iPhone"]' -u xpath

# Tap by exact screen coordinates (points)
python3 scripts/ios_controller.py tap -x 332 -y 148
```

### 6. Gestures & Hardware Buttons
```bash
# Swipe (e.g. scroll down)
python3 scripts/ios_controller.py swipe 200 600 200 200 --duration 0.3

# Press Home button
python3 scripts/ios_controller.py press home

# Lock device screen
python3 scripts/ios_controller.py press lock
```

---

## WDA Packaging Protocol (Fixing Error 175)

If preparing a new WebDriverAgentRunner IPA for TrollStore:
```bash
python3 scripts/repack_wda.py -i /path/to/WebDriverAgentRunner-Runner.zip -o /path/to/clean_wda.ipa
```
This automatically removes offending `.dSYM` DWARF symbol bundles, elevates frameworks from `PlugIns/` to root `Frameworks/`, and purges stale signatures.

