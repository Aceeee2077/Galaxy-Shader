# Galaxy Shader

Galaxy Shader—Minecraft Java 光影，当前版本 **1.15.34**。在明亮暖色的基础上加入随昼夜旋转的整片银河、程序化月相、三波段大气透射日光，以及反日点地影/金星带、黄道光与夜间黄道带/对日照、夜间气辉、夜光云（含交叉重力波列）、云彩虹彩、冬季珠母云、22° 冰晶晕（含月幻日与月切弧）、46° 晕与环地平弧、环天顶弧、薄云月华、毕晓普环、星光闪烁、恒星颜色与气辉重力波波纹、极光天顶冕与帘幕褶皱、彗星反尾、流星余迹、日全食日冕与红色日珥、雨夜月虹、雨后白虹、日落绿闪、低日与低月的大气折射（日面与月面抬升并竖直压扁）与反日点光辐条：暖日光、更通透的户外阴影、固定曝光 1.25 与饱和度 1.1，让草木、木材和天空更鲜明。安装与设置见 [玩家说明](Galaxy%20Shader/README.md)，此前的参数映射见 [Photon 参考说明](Galaxy%20Shader/REFERENCE-PHOTON.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。FPS暂未测试。

1.15.32 起进入低配优化阶段：不改动 HIGH 预设的可见效果，只跳过那些最终乘以零的计算（例如白昼的夜间宇宙天空），并继续用逐像素等价的合成 GPU 回归守住画面。

最新安装包为 `Galaxy Shader-1.15.34.zip` 及其校验值。安装后先恢复光影默认设置，再选择 HIGH；仅切换质量预设不会重置旧曝光与饱和度。

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

1.15.31 大气折射：贴近地平线的太阳与满月整体上抬、竖直方向被压扁，下缘比上缘抬升更多，低日因此呈现为略扁的椭圆而非正圆（合成 GPU 日/月面对照，左关右开，非游戏截图）：

![大气折射](Galaxy%20Shader/previews/atmospheric-refraction.png)

1.15.30 毕晓普环：太阳周围一圈极宽、极淡的尘埃光环，内缘偏暖棕粉、外缘渐冷蓝白，边缘柔和（合成 GPU 太阳特写，环亮度放大）：

![毕晓普环](Galaxy%20Shader/previews/bishops-ring.png)

1.15.29 云彩虹彩：太阳附近高空薄云中出现柔和的粉彩衍射条纹，越靠近太阳越密，并在破碎云隙间形成弧段（合成 GPU 天空，彩边亮度放大）：

![云彩虹彩](Galaxy%20Shader/previews/cloud-iridescence.png)

1.15.28 极光帘幕褶皱：极光帘幕折成数片大片下垂的褶皱，绿色下缘与紫色上缘一起起伏，细密光柱在收拢处聚亮（合成 GPU 北天对照，同一片极光左关右开，亮度放大）：

![极光帘幕褶皱](Galaxy%20Shader/previews/aurora-folds.png)

1.15.27 夜光云波纹：夜光云内部出现两组交叉的重力波列，波峰弯曲、近地平处被透视拉长并缓慢漂移（合成 GPU 全景，同一片云左关右开，亮度放大）：

![夜光云波纹](Galaxy%20Shader/previews/nlc-waves.png)

1.15.26 气辉重力波波纹：夜间气辉层出现一组淡淡的水平条纹，沿方位缓慢弯曲并整体漂移（合成 GPU 全景，气辉亮度放大）：

![气辉重力波波纹](Galaxy%20Shader/previews/airglow-ripples.png)

1.15.25 恒星颜色：每颗星获得稳定的表面温度色，从暖橙、淡黄到冷蓝白，并带独立亮度差异（合成 GPU 星空，星点放大以便观察）：

![恒星颜色](Galaxy%20Shader/previews/star-colors.png)

1.15.24 日全食日冕与日珥：食甚时黑色月面周围展开淡白日冕流苏、极区羽状结构与赤道带，月缘点缀数处红色日珥（合成 GPU 日食特写，日冕亮度放大）：

![日全食日冕与日珥](Galaxy%20Shader/previews/eclipse-corona.png)

1.15.23 流星余迹：明亮流星划过后，沿轨迹留下数秒的淡绿色余迹，并带缓慢漂移的结节（合成 GPU 夜空视图，余迹亮度放大）：

![流星余迹](Galaxy%20Shader/previews/meteor-train.png)

1.15.22 月幻日与月切弧：低垂明月照亮高空片状冰晶时，22° 晕两侧出现一对冷色、竖向拉长的月幻日，晕顶再覆一条淡淡的月切弧（合成 GPU 夜空全景，冰晶光晕亮度放大）：

![月幻日与月切弧](Galaxy%20Shader/previews/moon-dogs.png)

1.15.21 彗星反尾：彗星活跃时，普通尘埃尾之外还会出现一条指向太阳的极细尘埃针，靠近彗头处最亮并迅速变淡（合成 GPU 彗星视图，反尾亮度放大）：

![彗星反尾](Galaxy%20Shader/previews/comet-antitail.png)

1.15.20 极光天顶冕：极光活跃时，帘幕在天顶汇聚成放射状光冕（合成 GPU 鱼眼天顶视图，光冕亮度放大）：

![极光天顶冕](Galaxy%20Shader/previews/aurora-corona.png)

1.15.19 白虹：雨停后雾中宽而近乎白色的 42° 反日弧，只余很淡的冷色内缘与暖色外缘（合成 GPU 雾天全景，虹弧亮度放大）：

![白虹](Galaxy%20Shader/previews/fogbow.png)

1.15.18 星光闪烁：同一片星空在两个时刻，每颗星以独立相位快速明灭（合成 GPU 夜空对照，闪烁幅度放大）：

![星光闪烁](Galaxy%20Shader/previews/star-scintillation.png)

1.15.17 环天顶弧：低日时高空中向日展开的彩色微笑弧，红边在下、紫边在上（合成 GPU 高空全景，弧亮度放大）：

![环天顶弧](Galaxy%20Shader/previews/circumzenithal-arc.png)

1.15.16 月华：薄云明月周围紧凑的柔和衍射环，内蓝白、外偏暖（合成 GPU 夜空全景，环纹预览放大）：

![月华](Galaxy%20Shader/previews/lunar-corona.png)

1.15.15 干涉虹：主虹紫色内缘的浅绿/浅粉细条纹（合成 GPU 全景，条纹预览放大）：

![干涉虹](Galaxy%20Shader/previews/supernumerary-arcs.png)

1.15.14 副虹与亚历山大暗带：主虹外侧颜色反转的淡虹与两虹之间的暗带（合成 GPU 双虹全景，副虹预览放大）：

![副虹与亚历山大暗带](Galaxy%20Shader/previews/secondary-rainbow.png)

1.15.13 月柱：低月被冰晶拉出的冷色垂直光柱（合成 GPU 夜空全景，预览增益放大）：

![月柱](Galaxy%20Shader/previews/moon-pillar.png)

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

- `Galaxy Shader/`：MIT 光影源码（1.15.34）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.15.34.zip` / `.sha256`：最新安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
