# Omniverse 开发入门 ——理解 Extension

Vinjn 张静
2022-Nov



[toc]

# 调试自带插件

launch.json

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "attach",
            "port": 3000,
            "host": "localhost",
            "subProcess": true
        }
    ]
}
```

# 开始开发插件

基于官方模板

- https://github.com/NVIDIA-Omniverse/kit-extension-template
- https://github.com/NVIDIA-Omniverse/kit-extension-template-cpp

或 Vinjn 的自定义版

- https://github.com/vinjn/kit-extension-template

文档

- [Omniverse Kit Python Snippets](https://docs.omniverse.nvidia.com/prod_kit/prod_kit/python-snippets.html)
- [Universal Scene Description Python Snippets](https://docs.omniverse.nvidia.com/prod_usd/prod_usd/python-snippets.html)

# 调试

- 推荐安装 [VS Code](https://code.visualstudio.com/)
- 启用插件 `omni.kit.debug.vscode`
- 在 VS Code 中按 F5，选择 `Attach to Kit`
- 在 Kit 中观察连接情况

# 实战时间

- 今年官方竞赛 [#ExtendOmniverse](https://www.youtube.com/hashtag/extendomniverse) 上的国人获奖作品 - [Exploded View 爆炸图](https://www.youtube.com/watch?v=NWGXmNMldPY&ab_channel=NVIDIAOmniverse)
- 作者：Cheng He，来自湖南省建筑设计院
- 思路拆解
  - 获取选中节点
  - 遍历所有子节点
    - 让坐标变大
  - 提供 UI 控件
    - `app\omni.app.uidoc.bat` 是最佳的 UI 文档

# 课件及代码分享

- 课件：https://github.com/vinjn/one-minute-omniverse/tree/main/kit-programming-talks
- 爆炸图插件：https://github.com/vinjn/one-minute-omniverse/tree/main/exploded-view-extension-final



