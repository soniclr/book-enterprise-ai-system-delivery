# 《企业 AI 系统落地》

副标题：从业务重构到可治理架构

编著：海波AI

这是《企业 AI 系统落地》的公开源稿仓库。仓库提供完整可编辑的 Markdown 书稿、案例、附录、插图源文件、配套 Python 示例、项目模板和出版构建脚本。PDF 不进入 Git 历史，仅作为版本化 Release 附件发布。

## 下载与阅读

- [下载 v0.1 PDF](https://github.com/soniclr/book-enterprise-ai-system-delivery/releases/download/v0.1/企业AI系统落地-v0.1.pdf)
- [查看 v0.1 Release](https://github.com/soniclr/book-enterprise-ai-system-delivery/releases/tag/v0.1)
- [校验文件完整性](SHA256SUMS.txt)
- [从 Markdown 源稿开始阅读](manuscript/README.md)

v0.1 对应第一版·第四稿，出版稿日期为 2026-07-22，共 487 页。

- [版本说明](RELEASE_NOTES.md)
- [变更记录](CHANGELOG.md)

## 仓库内容

```text
manuscript/   前言、序章和二十章正文
cases/        三个完整合成案例与阅读说明
appendices/   工具箱、术语、技术卡、参考资料与实践手册
assets/       正文引用的插图、流程图及 Graphviz 源文件
publication/  出版说明、权利说明和排版样式
tools/        项目诊断、架构评审、评估门禁与生产运营模板
code/         无外部依赖的 Python 示例与单元测试
scripts/      书稿校验与 Markdown、DOCX、PDF 构建脚本
```

模板包括：

- [项目诊断模板](tools/01-project-diagnosis-template.md)
- [架构评审模板](tools/02-architecture-review-template.md)
- [评估与发布门禁模板](tools/03-evaluation-release-gate-template.md)
- [POC 到生产阶段门模板](tools/04-poc-production-template.md)
- [生产运营模板](tools/05-production-operations-template.md)

公开范围及未公开材料的判断依据见 [OPEN_SOURCE_SCOPE.md](OPEN_SOURCE_SCOPE.md)。

出版信息见 [出版说明](publication/00-publication-note.md) 与 [编著、审校及使用说明](publication/01-editorial-and-rights.md)。

## 运行配套代码

代码需要 Python 3.10 或更高版本，只使用标准库。

```bash
python3 code/run_demo.py
python3 -m unittest discover -s code/tests -v
```

## 校验与构建书稿

仅校验 Markdown 源稿不需要第三方 Python 包：

```bash
python3 scripts/validate_book_manuscript.py
```

生成合并版 Markdown、DOCX、PDF 和随书附件前，请先安装构建依赖。完整说明见 [BUILDING.md](BUILDING.md)。

```bash
python3 -m pip install -r requirements-build.txt
python3 scripts/build_enterprise_ai_system_book.py
```

示例中的企业、用户、项目和数据均为虚构内容，不对应真实客户或生产系统。

## 反馈与勘误

欢迎通过 GitHub Issues 提交：

- PDF 页码与原文位置；
- 问题说明与建议修订；
- 可公开核查的参考来源。

请勿在 Issue 中提交客户资料、内部文档、访问凭据或其他敏感信息。代码修订方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可与版权

- `code/` 中的配套代码采用 [MIT License](LICENSE-CODE.md)。
- Markdown 书稿、PDF、模板、书名、正文、案例、表格和插图不适用 MIT License，版权与允许用途见 [CONTENT-LICENSE.md](CONTENT-LICENSE.md)。

因此，本仓库公开完整书稿源文件，配套代码属于开源软件；书稿内容虽然公开可见，并不因托管在 GitHub 上而自动变更为开放内容许可。
