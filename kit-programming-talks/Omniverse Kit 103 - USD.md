# Omniverse 开发入门 ——理解 USD
vincentz@nvidia.com
2022-Nov



[toc]

# USD

- USD = Universal Scene Description, 不是美元 $
- 由 Pixar 发明，以优化影视特效行业的生产流程，被 NVIDIA 采纳作为 Omniverse 的核心组件。
- USD 是 Omniverse 最重要的场景格式，除此之外它还包含一个动态运行库（包含 C++ 和 Python）。
- [更多 USD 教程](https://graphics.pixar.com/usd/release/dl_downloads.html)

# UsdView

- 由 Pixar 开发，在 Launcher 中可以下载
- usdview 可视化查阅器
- usdcat 文本显示 usd 内容
- usdtree 树状结构罗列 usd 内容

# USD 高级操作

- 引用外部 USD
- `omni.kit.usda_edit` 插件
- Create 和 Code 协同