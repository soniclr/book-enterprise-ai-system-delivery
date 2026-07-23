# 参与贡献

感谢帮助改进《企业 AI 系统落地》。本仓库接受以下公开贡献：

- PDF 勘误与事实更新建议；
- 配套代码的缺陷修复、测试与可读性改进；
- 模板中的错别字、字段一致性和说明改进。

提交 Issue 时，请提供 PDF 页码、相关原文位置、问题说明和可公开核查的来源。不要提交真实客户数据、内部资料、访问凭据、受保密协议约束的内容或无权再许可的材料。

提交修改前请运行：

```bash
python3 scripts/validate_book_manuscript.py
python3 -m unittest discover -s code/tests -v
```

涉及图片或出版构建的修改，还应按 [BUILDING.md](BUILDING.md) 重新生成并检查输出。构建产物不提交到 Git；正式 PDF 由维护者在版本发布时作为 Release 附件上传。

代码贡献按 `LICENSE-CODE.md` 中的 MIT License 处理。书稿与模板的版权边界见 `CONTENT-LICENSE.md`；提交大段正文或新增插图前，请先通过 Issue 确认授权范围。
