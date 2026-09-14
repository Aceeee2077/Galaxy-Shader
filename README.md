# Galaxy Shader

Galaxy Shader 的 Minecraft Java 光影源码，当前最新版本 **1.5.0**（程序化天气、雨水交互、晨昏光柱与地形雾升级）。玩家安装与功能说明见 [Galaxy Shader/README.md](Galaxy Shader/README.md)，英文版见 [README-EN.md](Galaxy Shader/README-EN.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。当前为首轮实现：GPU 编译与合成场景渲染已检查，Minecraft 游戏内兼容性与 FPS 尚未验收。

最新发布安装包为 `Galaxy Shader-1.5.0.zip` 及其校验值；历史版本后续可改用 GitHub Releases 管理。

## 效果预览

主世界效果图：

![主世界效果](Galaxy%20Shader/previews/main.png)

末地（合成场景 GPU 渲染预览，非实际游戏截图）：

![末地](Galaxy%20Shader/previews/end.png)

末地行星天空特写：

![末地行星天空](Galaxy%20Shader/previews/end-sky.png)

## 目录结构

- `Galaxy Shader/`：MIT 光影源码（1.5.0）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.5.0.zip` / `.sha256`：最新发布安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
