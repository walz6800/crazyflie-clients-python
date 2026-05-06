翻译维护说明 / Translation Maintenance Guide
================================================

提取/更新翻译源文件:
    pylupdate6 pyproject.toml

编译翻译文件:
    lrelease src/cfclient/locale/cfclient_zh_CN.ts

工作流程:
1. 代码中用 tr() 包裹新字符串
2. 运行 pylupdate6 更新 .ts 文件
3. 在 Qt Linguist 或文本编辑器中编辑 .ts 文件，填写中文翻译
4. 运行 lrelease 编译为 .qm 文件
5. 重新运行应用以验证翻译
