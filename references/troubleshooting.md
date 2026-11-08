# iOS Device Control Troubleshooting & Technical Deep-Dive
# iOS 设备远程接管与控制排错指南与底层技术解析

[English](#english) | [中文版](#中文版)

---

<a name="english"></a>
## English

### 1. Root Cause Analysis: TrollStore "Install Error 175" (`ldid non zero status code`)

#### Problem
When installing standard `WebDriverAgentRunner.ipa` packages via TrollStore, users encounter:
```text
Install Error 175: Failed to sign the app. ldid returned a non zero status code.
```

#### Technical Cause
1. **Mach-O Type Mismatch**: TrollStore uses `ldid` to pseudo-sign installed binaries and inject root CoreTrust entitlements. `ldid` parses standard executables (`MH_EXECUTE`) and dynamic libraries (`MH_DYLIB`).
2. **The `.dSYM` Poisoning**: Official Appium prebuilt runner releases (e.g., `WebDriverAgentRunner-Runner.zip`) bundle debug symbols directly inside the application bundle:
   `Payload/WebDriverAgentRunner-Runner.app/PlugIns/WebDriverAgentRunner.xctest.dSYM/Contents/Resources/DWARF/WebDriverAgentRunner`
   This is a raw DWARF debug slice. When `ldid` recursively scans the bundle and attempts to pseudo-sign this file, it fails with an unsupported Mach-O type error, aborting the entire installation.
3. **Nested Framework Misplacement**: Xcode packages `WebDriverAgentLib.framework` inside `PlugIns/WebDriverAgentRunner.xctest/Frameworks/`. Nested frameworks inside test bundles frequently break mobile package signers.

#### Solution
Run `repack_wda.py`:
* Recursively strips all `.dSYM` directories and intermediate build artifacts.
* Relocates `WebDriverAgentLib.framework` to `Payload/*.app/Frameworks/`.
* Clears all stale `_CodeSignature` directories.
* Packages into a clean, slimmed-down `.ipa` (~1.9 MB instead of 3.0+ MB) that signs cleanly in TrollStore.

---

### 2. Apple Free Developer ID 7-Day Revoke & i4Tools Limitations

* **The 7-Day Revoke**: Free Apple IDs issue provisioning profiles valid for strictly 7 days, after which the OS refuses to launch the app without tethered resigning.
* **Nested XCTest Runner Failure**: Sideloading utilities like i4Tools (爱思助手) or AltStore often fail when resigning `WebDriverAgentRunner-Runner.app` because free developer accounts cannot provision wildcard IDs across nested `.xctest` bundles and frameworks simultaneously.
* **Solution**: TrollStore exploits the Apple CoreTrust bug (CVE-2022-26766 & CVE-2021-30937), permanently granting system-level persistence and arbitrary entitlements without certificates or expirations.

---

### 3. iOS 18 Upgrade Trap vs. iOS 16 CoreTrust Sweet Spot

* Apple closes TSS signing windows quickly (`Signed: False`) for older iOS builds. Upgrading to a specific build (e.g. iOS 18.0) fails with iTunes Error 3194 once the window closes.
* **CoreTrust Sweet Spot**: iOS 14.0 – 16.6.1 natively supports TrollStore. Keeping a device on iOS 16.x provides an ideal long-term environment for persistent AI automation agents without risking lost exploit capabilities.

---

<a name="中文版"></a>
## 中文版

### 1. 深度解析：巨魔安装报错 Error 175（`ldid returned a non zero status code`）

#### 报错现象
在 TrollStore 中从 URL 或本地 IPA 安装 `WebDriverAgentRunner.ipa` 时，弹窗报错：
```text
Install Error 175: Failed to sign the app. ldid returned a non zero status code.
```

#### 底层技术原因
1. **Mach-O 二进制类型冲突**：巨魔安装应用时，会在手机端调用 `ldid` 伪签名器，为所有 Mach-O 二进制文件注入 CoreTrust 系统级权限。`ldid` 仅支持标准可执行文件（`MH_EXECUTE`）和动态库（`MH_DYLIB`）。
2. **调试符号包污染（.dSYM）**：Appium 官方发布的部分预编译包中，直接把调试符号包打进了应用插件目录：
   `Payload/WebDriverAgentRunner-Runner.app/PlugIns/WebDriverAgentRunner.xctest.dSYM/Contents/Resources/DWARF/WebDriverAgentRunner`
   这是一个超过 1MB 的 DWARF 调试文件。`ldid` 递归扫描时尝试对其进行代码签名，直接崩溃抛出非零退出码。
3. **增量打包陷阱**：在 Linux/macOS 上直接对已有 IPA 使用 `zip -r` 时，默认是增量合并，不会删除旧包里已有的 `.dSYM`，导致修改后依然报错。
4. **嵌套 Framework 结构非标**：原包将 `WebDriverAgentLib.framework` 放在 `PlugIns/.../Frameworks` 嵌套目录中，超出了常规移动签名器的识别逻辑。

#### 解决方案
使用本项目提供的 `scripts/repack_wda.py`：
* 彻底删除所有 `.dSYM` 目录；
* 将 `WebDriverAgentLib.framework` 提升至根目录 `Payload/*.app/Frameworks/`；
* 清空所有旧的 `_CodeSignature`；
* 重新打包为标准 1.9MB 的纯净 IPA。

---

### 2. 免费 Apple ID 7 天掉签与签名工具限制

* **7 天掉签痛点**：普通个人 Apple ID 签名的应用只有 7 天有效期，过期即闪退，严重阻碍长期无人值守的 AI 自动化。
* **嵌套插件签名失败**：爱思助手、Sideloadly 等工具对包含 `.xctest` 和嵌套 Framework 的复合包兼容性较差，常提示签名失败或无法生成证书。
* **破局核心**：借助 TrollStore（利用 CoreTrust 漏洞），应用被作为根系统应用永久驻留，**彻底免签、永不过期**。

---

### 3. iOS 升级版本陷阱与停留在 16.x 的战略意义

* 苹果对历史 iOS 固件（IPSW）的签名窗口关闭非常迅速（TSS 验证状态为 `Signed: False`）。一旦关闭，降级或指定升级将直接触发 iTunes 错误 3194。
* **iOS 16.0 ~ 16.6.1 黄金组合**：原生具备 CoreTrust 漏洞，支持 TrollRestore 免越狱注入，是当前搭建 AI Agent 物理机控制中台的最佳固件区间。

