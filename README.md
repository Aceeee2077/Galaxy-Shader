# Galaxy Shader

Galaxy Shader—Minecraft Java 光影，当前版本 **1.14.0**。根据用户提供的 Photon 1.3 参数校准：太阳角半径 2°、云影强度 80%、默认固定曝光；正午更中性的日光、偏冷的天空补光、低地晨雾与蓝调时刻共同改善自然光照观感。安装与设置见 [玩家说明](Galaxy%20Shader/README.md)，参数映射见 [Photon 参考说明](Galaxy%20Shader/REFERENCE-PHOTON.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。FPS暂未测试。

最新安装包为 `Galaxy Shader-1.14.0.zip` 及其校验值。

## 效果预览

本次调整前后对照（合成 GPU 场景，左旧右新）：

![Photon calibration](Galaxy%20Shader/previews/photon-calibration.png)

游戏截图：

![主世界效果](Galaxy%20Shader/previews/main.png)

末地裂隙核心与巨行星特写 (合成 GPU 预览)：

![末地行星天空](Galaxy%20Shader/previews/end-sky.png)

## 目录结构

- `Galaxy Shader/`：MIT 光影源码（1.14.0）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.14.0.zip` / `.sha256`：最新安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
