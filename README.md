# Galaxy Shader

Galaxy Shader 的 Minecraft Java 光影源码，当前最新版本 **1.12.1**：末地中央天体由黑洞/虫洞改为裂隙核心（多面水晶核心、衍射星芒、对向喷流与碎裂石片带），并按 Photon 方向重做水面与水下开销——水面反射默认为解析天空反射（`WATER_REFLECTIONS` 可选叠加屏幕空间命中）、折射改为单次偏移采样、云层远段自动降级细节、反射不再二次 march 体积云。1.12.1 进一步参考 Photon 1.3 的默认参数调整了环境光遮蔽半径/采样、PCSS 阴影采样区间、水体每格吸收系数与体积光天顶采样。玩家安装与功能说明见 [Galaxy Shader/README.md](Galaxy Shader/README.md)，英文版见 [README-EN.md](Galaxy Shader/README-EN.md)。

目标：Minecraft Java 26.2、Fabric、Iris、Sodium、OpenGL。FPS暂未测试。

最新安装包为 `Galaxy Shader-1.12.1.zip` 及其校验值。仓库只保留 1.5.0 与当前版本的安装包，另有 `Galaxy Shader-1.11.2-baseline.zip`（1.11.2 源码快照，用于复现性能对比）；其余历史版本已删除。GPU 合成渲染已验证，与 1.11.2 的 A/B 计时与画面差异报告见 `validation/performance-report.json`；游戏内画面与 FPS 仍待实测。

## 效果预览

1.12.1 合成 GPU 预览（非游戏截图）：

![主世界效果](Galaxy%20Shader/previews/main.png)

末地裂隙核心与巨行星特写：

![末地行星天空](Galaxy%20Shader/previews/end-sky.png)

## 目录结构

- `Galaxy Shader/`：MIT 光影源码（1.12.1）、菜单与随包文档。
- `tools/`：入口生成、GPU 编译、离屏渲染和确定性打包工具。
- `validation/`：纳入版本管理的验证报告与测试清单；合成场景 PNG/GIF 等生成产物仅保留本地，不入库。
- `Galaxy Shader-1.12.1.zip` / `.sha256`：最新安装包与 SHA-256 校验值。

开发与验证流程见 [Galaxy Shader/ARCHITECTURE.md](Galaxy Shader/ARCHITECTURE.md)。
