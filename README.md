# Galaxy Shader

Galaxy Shader—Minecraft Java 光影，当前版本 **1.15.2**。在明亮暖色的基础上加入随昼夜旋转的整片银河、程序化月相与三波段大气透射日光：暖日光、更通透的户外阴影、固定曝光 1.25 与饱和度 1.1，让草木、木材和天空更鲜明。安装与设置见 [玩家说明](Galaxy%20Shader/README.md)，此前的参数映射见 [Photon 参考说明](Galaxy%20Shader/REFERENCE-PHOTON.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。FPS暂未测试。

最新安装包为 `Galaxy Shader-1.15.2.zip` 及其校验值。安装后先恢复光影默认设置，再选择 HIGH；仅切换质量预设不会重置旧曝光与饱和度。

## 效果预览

暖色调整前后对照（合成 GPU 场景，左 1.14.0、右 1.14.1）：

![暖色与亮度对照](Galaxy%20Shader/previews/warm-palette.png)

游戏截图：

![主世界效果](Galaxy%20Shader/previews/main.png)

末地裂隙核心与巨行星特写 (合成 GPU 预览)：

![末地行星天空](Galaxy%20Shader/previews/end-sky.png)

1.15.1 夜间动态银河：黄昏从一侧升起，午夜横跨天顶，黎明在对侧落下（合成 GPU 天空，非游戏截图）：

![夜间动态银河](Galaxy%20Shader/previews/night-galaxy.png)

1.15.1 程序化月相：0–7 月相、月海与环形山纹理、地照与月华，月光随受照比例变化（合成 GPU 天空）：

![程序化月相](Galaxy%20Shader/previews/night-moon.png)

1.15.1 温暖日光：三波段大气透射、加宽的向阳暖带与暖核冷边光晕（合成 GPU 场景，左 1.14.1、右 1.15.1）：

![温暖日光对照](Galaxy%20Shader/previews/warm-sun.png)

## 目录结构

- `Galaxy Shader/`：MIT 光影源码（1.15.2）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.15.2.zip` / `.sha256`：最新安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
