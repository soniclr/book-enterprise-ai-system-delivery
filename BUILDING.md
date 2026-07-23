# 构建书稿

仓库中的 Markdown、插图、样式和脚本可以生成合并版 Markdown、DOCX、PDF 与随书附件。正式 PDF 不提交到 Git，只在 GitHub Release 中发布。

## 1. 校验源稿

源稿校验只需要 Python 3.10 或更高版本：

```bash
python3 scripts/validate_book_manuscript.py
```

校验范围包括章节数量与编号、正文结构、已知改写残留、引用、相对链接、插图目录和代码围栏。

## 2. 安装构建依赖

Python 依赖：

```bash
python3 -m pip install -r requirements-build.txt
```

系统还需要以下命令位于 `PATH`：

- Pandoc；
- LibreOffice 的 `soffice`；
- ExifTool。

建议安装 Noto Sans SC 字体，以保持中文排版接近发布版本。

## 3. 生成出版文件

```bash
python3 scripts/build_enterprise_ai_system_book.py
```

构建结果写入被 Git 忽略的 `output/` 目录：

- 合并版 Markdown；
- DOCX 出版稿；
- PDF 阅读版；
- 随书附件 ZIP；
- SHA-256 校验和。

构建会根据源稿中的图片引用重新生成 `appendices/G-figure-list.md`。提交源稿修改前，请检查该文件是否随插图变化而更新。

## 4. 运行配套代码测试

```bash
python3 -m unittest discover -s code/tests -v
```
