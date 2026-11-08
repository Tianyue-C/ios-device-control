# ios-device-control 📱🤖

> **Autonomous iOS Automation & Device Control for AI Agents & Developers**  
> *Permanent, USB-driven iPhone/iPad control without jailbreak, without paid developer accounts, and without 7-day certificate revocation.*

[![Platform](https://img.shields.io/badge/Platform-iOS%2014.0%20--%2016.6.1-blue.svg)](https://github.com)
[![Host OS](https://img.shields.io/badge/Host-macOS%20%7C%20Linux-black.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://www.python.org/)

[English](#english) | [中文说明](#中文说明)

---

<a name="english"></a>
## 🌟 English Overview

### The Problem
Automating physical iOS devices for AI Agents (or CI/CD pipelines) has historically suffered from critical roadblocks:
1. **The 7-Day Revoke**: Free Apple IDs sign apps that expire after strictly 7 days, causing automation to break without tethered re-signing.
2. **Third-Party Signer Failures**: Tools like i4Tools or AltStore fail when signing complex XCUITest bundles with nested plugins and frameworks.
3. **TrollStore Error 175 (`ldid returned a non zero status code`)**: Official Appium WebDriverAgent releases contain Mach-O DWARF debug files in `.dSYM` directories, causing TrollStore's `ldid` signing engine to abort.
4. **Xcode Bloat**: Traditional workflows require running heavy Xcode test processes continuously.

### The Solution: `ios-device-control`
This project provides an end-to-end framework enabling an AI Agent or developer to directly control an iOS device:
* **Permanent Installation**: Leverages CoreTrust (via TrollStore / TrollRestore) to install WebDriverAgentRunner permanently with system-level privileges. No 7-day expiration.
* **Automated IPA Sanitization**: `repack_wda.py` purges `.dSYM` DWARF symbol files and relocates nested frameworks, guaranteeing 100% successful TrollStore installation without Error 175.
* **Headless USB Control**: Drives device interactions through `pymobiledevice3` over `usbmuxd` and Apple's `testmanagerd` daemon without launching Xcode.
* **Unified CLI Interface**: `ios_controller.py` provides high-speed screenshots, Apple Vision OCR, UI element trees, precise taps, swipes, app launching, and hardware button clicks.

---

### 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────┐
│             AI Coding Assistant / RPA Agent            │
└───────────────────────────┬────────────────────────────┘
                            │ CLI commands
                            ▼
┌────────────────────────────────────────────────────────┐
│             scripts/ios_controller.py                  │
└───────────────────────────┬────────────────────────────┘
                            │ USB protocol
                            ▼
┌────────────────────────────────────────────────────────┐
│              pymobiledevice3 (usbmuxd)                 │
└───────────────────────────┬────────────────────────────┘
                            │ testmanagerd / DDI
                            ▼
┌────────────────────────────────────────────────────────┐
│    WebDriverAgentRunner-Runner (CoreTrust System App)   │
└───────────────────────────┬────────────────────────────┘
                            │ Native Accessibility APIs
                            ▼
┌────────────────────────────────────────────────────────┐
│     Target iOS Apps (WeChat, Safari, Settings, etc.)    │
└────────────────────────────────────────────────────────┘
```

---

### 🚀 Step-by-Step Setup Guide

#### 1. Host Environment Setup
Install required dependencies on macOS:
```bash
git clone https://github.com/your-username/ios-device-control.git
cd ios-device-control
pip3 install -r requirements.txt
```

#### 2. Enable iPhone Developer Mode & Mount DDI
Connect iPhone via USB and run:
```bash
# Reveal the Developer Mode menu in Settings -> Privacy & Security
pymobiledevice3 amfi reveal-developer-mode

# Reboot phone, toggle Developer Mode to ON, and enter device passcode.

# Mount the Developer Disk Image (DDI)
pymobiledevice3 mounter auto-mount
```

#### 3. Install TrollStore (iOS 14.0 – 16.6.1)
Use [TrollRestore](https://github.com/JJTech0130/TrollRestore):
1. Temporarily turn off **Find My iPhone** in Settings.
2. Run TrollRestore on host: `./TrollRestore Tips`.
3. Open the **Tips** app on iPhone and tap **Install TrollStore**.
4. Re-enable **Find My iPhone** in Settings (optional, safe to turn back on).

#### 4. Prepare & Install Sanitized WebDriverAgent
Standard WDA packages trigger Error 175 in TrollStore. Use our sanitizer:
```bash
# Download official Appium runner:
curl -L -o /tmp/wda.zip https://github.com/appium/WebDriverAgent/releases/download/v16.15.3/WebDriverAgentRunner-Runner.zip

# Sanitize and repack:
python3 scripts/repack_wda.py -i /tmp/wda.zip -o ~/Downloads/WebDriverAgentRunner_Clean.ipa
```
Transfer the generated IPA to iPhone (via AirDrop, local web server, or AFC push) and open in TrollStore to install permanently.

---

### 🛠️ CLI Command Reference (`ios_controller.py`)

#### Check Connectivity
```bash
python3 scripts/ios_controller.py status
```

#### Screen Capture & Inspection
```bash
# Capture full hardware screenshot:
python3 scripts/ios_controller.py screenshot -o /tmp/screen.png

# Extract all visible text via Apple Vision OCR:
python3 scripts/ios_controller.py ocr -i /tmp/screen.png -o /tmp/ocr.json

# Dump UI element tree (coordinates, accessibility labels, element types):
python3 scripts/ios_controller.py list-elements --visible-only -o /tmp/elements.json
```

#### Autonomous Interactions
```bash
# Launch application:
python3 scripts/ios_controller.py launch com.tencent.xinWeChat
python3 scripts/ios_controller.py launch com.apple.Preferences

# Tap by element name, label, or XPath:
python3 scripts/ios_controller.py tap -s "Settings" -u name
python3 scripts/ios_controller.py tap -s '//XCUIElementTypeSwitch[@name="Find My iPhone"]' -u xpath

# Tap by exact screen point coordinates:
python3 scripts/ios_controller.py tap -x 332 -y 148

# Swipe / Scroll:
python3 scripts/ios_controller.py swipe 200 600 200 200 --duration 0.3

# Press hardware buttons:
python3 scripts/ios_controller.py press home
python3 scripts/ios_controller.py press lock
```

---

<a name="中文说明"></a>
## 🇨🇳 中文说明

### 项目背景与痛点
在将真实 iPhone 接入 AI Agent（如 Claude、Antigravity、Cursor）或自动化 RPA 任务时，传统方案存在以下致命硬伤：
1. **7 天证书掉签**：使用免费 Apple ID 签名的应用，每隔 7 天必须重新连接电脑签名，无法无人值守。
2. **三方助手签名崩溃**：爱思助手、AltStore 等工具在处理带有复杂 `.xctest` 插件和嵌套 Framework 的 WDA 测试包时极易签名失败。
3. **巨魔 Error 175 报错（`ldid returned a non zero status code`）**：直接在 TrollStore 中安装官方 WDA 包时，会被包内内嵌的 `.dSYM` 调试文件卡死。
4. **Xcode 依赖沉重**：传统流程需要打开体积庞大的 Xcode 并维持 debug session，无法轻量化 CLI 调度。

### 核心破局方案
本方案通过三大技术突破，实现真机的**永久、免签、无感接管**：
* **CoreTrust 系统级驻留**：利用 iOS 14.0 ~ 16.6.1 的 CoreTrust 机制（通过 TrollRestore 免越狱注入），让 WDA 像系统应用一样永久有效，**永不掉签**。
* **IPA 净化与重组器（`repack_wda.py`）**：自动化剔除 1MB 的 DWARF `.dSYM` 调试杂质，并将嵌套 Framework 提升至标准根目录，**彻底斩断 Error 175 根因**。
* **USB 协议级无感控制**：基于 `pymobiledevice3` 与苹果 `testmanagerd` 通信，无需开启 Xcode 即可毫秒级下发点击、滑动、截图与 OCR 指令。

---

### 💻 核心脚本说明

* **`scripts/repack_wda.py`**：WDA 自动化重构与净化工具。自动解包、清理调试符号、规范 Framework 目录并重新打包。
* **`scripts/ios_controller.py`**：统一设备控制 CLI 工具。支持 `status`, `screenshot`, `ocr`, `list-elements`, `launch`, `tap`, `swipe`, `press`。
* **`SKILL.md`**：标准 Agent Skill 规范，可直接置入各类 AI Coding Agent 的技能库中。
* **`references/troubleshooting.md`**：详细排错指南与底层 Mach-O 签名原理剖析。

---

### 📋 快速开始命令

```bash
# 1. 检查 WDA 运行就绪状态
python3 scripts/ios_controller.py status

# 2. 截取屏幕并提取文字 (Vision OCR)
python3 scripts/ios_controller.py screenshot -o /tmp/screen.png
python3 scripts/ios_controller.py ocr -i /tmp/screen.png -o /tmp/ocr.json

# 3. 唤起微信
python3 scripts/ios_controller.py launch com.tencent.xinWeChat

# 4. 模拟点击与返回主屏
python3 scripts/ios_controller.py tap -x 200 -y 500
python3 scripts/ios_controller.py press home
```

---

## 📄 License
MIT License. Feel free to use in your own autonomous agents, RPA bots, and mobile testing pipelines.

