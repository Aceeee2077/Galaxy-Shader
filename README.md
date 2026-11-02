# Galaxy Shader

Galaxy Shader—Minecraft Java 光影，当前版本 **1.15.12**。在明亮暖色的基础上加入随昼夜旋转的整片银河、程序化月相、三波段大气透射日光，以及反日点地影/金星带、黄道光与夜间黄道带/对日照、夜间气辉、夜光云、冬季珠母云、22° 冰晶晕、46° 晕与环地平弧、雨夜月虹、日落绿闪与反日点光辐条：暖日光、更通透的户外阴影、固定曝光 1.25 与饱和度 1.1，让草木、木材和天空更鲜明。安装与设置见 [玩家说明](Galaxy%20Shader/README.md)，此前的参数映射见 [Photon 参考说明](Galaxy%20Shader/REFERENCE-PHOTON.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。FPS暂未测试。

最新安装包为 `Galaxy Shader-1.15.12.zip` 及其校验值。安装后先恢复光影默认设置，再选择 HIGH；仅切换质量预设不会重置旧曝光与饱和度。

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

1.15.3 晨昏光学现象：反日点地影/金星带、向阳侧黄道光与夜间气辉（合成 GPU 全景，预览增益放大）：

![晨昏光学现象](Galaxy%20Shader/previews/twilight-optics.png)

1.15.12 幻日环：与太阳同高度的淡白色水平光带（合成 GPU 全景，预览增益放大）：

![幻日环](Galaxy%20Shader/previews/parhelic-circle.png)

1.15.11 46° 冰晶晕与环地平弧：22° 晕外的淡环，以及高日时的水平彩色光带（合成 GPU 高空全景，预览增益放大）：

![46° 冰晶晕与环地平弧](Galaxy%20Shader/previews/ice-halo-companions.png)

1.15.10 反日点光辐条：低太阳时背向太阳半边天空的云影辐条（合成 GPU 反日侧全景，预览增益放大）：

![反日点光辐条](Galaxy%20Shader/previews/antisolar-rays.png)

1.15.9 绿闪：日落时太阳上缘的青绿色细弧（合成 GPU 日面特写，预览增益放大）：

![绿闪](Galaxy%20Shader/previews/green-flash.png)

1.15.8 珠母云：冬季暮光高空的粉、绿、蓝珠光透镜状云片（合成 GPU 全景，预览增益放大）：

![珠母云](Galaxy%20Shader/previews/nacreous.png)

1.15.7 黄道带与对日照：夜空中的淡银色黄道光带与反日点椭圆对日照（合成 GPU 全景，预览增益放大）：

![黄道带与对日照](Galaxy%20Shader/previews/zodiacal-band.png)

1.15.6 月虹：雨夜满月时反月点周围约 42° 的淡银色虹弧（合成 GPU 全景，预览增益放大）：

![月虹](Galaxy%20Shader/previews/moonbow.png)

1.15.5 冰晶晕：日/月周围 22° 圆环、低日幻日、上切弧与日柱（合成 GPU 全景，预览增益放大）：

![冰晶晕](Galaxy%20Shader/previews/ice-halos.png)

1.15.4 夜光云：日落后蓝白色高空云带，夏季最强，随视线透视拉伸（合成 GPU 全景，预览增益放大）：

![夜光云](Galaxy%20Shader/previews/noctilucent.png)

1.15.1 温暖日光：三波段大气透射、加宽的向阳暖带与暖核冷边光晕（合成 GPU 场景，左 1.14.1、右 1.15.1）：

![温暖日光对照](Galaxy%20Shader/previews/warm-sun.png)

## 目录结构

- `Galaxy Shader/`：MIT 光影源码（1.15.12）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.15.11.zip` / `.sha256`：最新安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
