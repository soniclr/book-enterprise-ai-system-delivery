# 附录 E：参考框架与进一步阅读

核查日：2026-07-17。本书的方法来自系统思维、业务流程、软件架构、AI 风险管理、生成式 AI 安全和工程运营实践的综合。除标准或官方规范本身外，列入参考不表示本书认可某个厂商产品，也不把公开实践当作跨行业普遍结论。

## 业务流程、分布式系统与架构

1. Object Management Group. *Business Process Model and Notation (BPMN), Version 2.0.2*. 2013. https://www.omg.org/spec/BPMN/2.0.2/About-BPMN
2. Garcia-Molina, H., and Salem, K. “Sagas.” *Proceedings of SIGMOD*. 1987. https://dl.acm.org/doi/10.1145/38713.38742
3. Gray, J. “Why Do Computers Stop and What Can Be Done About It?” Tandem Technical Report 85.7. 1985. https://www.hpl.hp.com/techreports/tandem/TR-85.7.pdf
4. Lewis, P., et al. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *NeurIPS*. 2020. https://arxiv.org/abs/2005.11401
5. Anthropic. “Building Effective Agents.” 2024. https://www.anthropic.com/research/building-effective-agents

## 协议、接口与可观测

6. Model Context Protocol. *Specification 2025-11-25: Authorization*. https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
7. Model Context Protocol. *Security Best Practices*. https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
8. OpenTelemetry. *Semantic Conventions 1.43.0*. https://opentelemetry.io/docs/specs/semconv/
9. OpenTelemetry. *Semantic Conventions for Generative AI Systems*. https://github.com/open-telemetry/semantic-conventions-genai
10. Google. *Site Reliability Engineering: How Google Runs Production Systems*. 2016. https://sre.google/sre-book/table-of-contents/
11. Google. *The Site Reliability Workbook*. 2018. https://sre.google/workbook/table-of-contents/

## 风险、治理、安全与供应链

12. NIST. *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, NIST AI 100-1. 2023. https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
13. NIST. *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile*, NIST AI 600-1. 2024. https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
14. ISO/IEC. *ISO/IEC 42001:2023 Information technology — Artificial intelligence — Management system*. https://www.iso.org/standard/42001.html
15. OWASP GenAI Security Project. *OWASP Top 10 for LLM Applications 2025*. https://genai.owasp.org/llm-top-10/
16. OWASP GenAI Security Project. *OWASP Top 10 for Agentic Applications*. 2025. https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/
17. NIST. *Secure Software Development Framework (SSDF), SP 800-218*. 2022. https://csrc.nist.gov/pubs/sp/800/218/final
18. CISA. *Secure by Design*. https://www.cisa.gov/securebydesign

## 中国境内规则与官方文件

19. 国家互联网信息办公室等：《生成式人工智能服务管理暂行办法》，2023-07-13 发布，2023-08-15 施行。https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm
20. 国家互联网信息办公室等：《人工智能生成合成内容标识办法》，2025-03-14 发布，2025-09-01 施行。https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm
21. 全国人民代表大会常务委员会：《中华人民共和国个人信息保护法》，2021。http://www.npc.gov.cn/npc/c2/c30834/202108/t20210820_313088.html
22. 全国人民代表大会常务委员会：《中华人民共和国数据安全法》，2021。http://www.npc.gov.cn/npc/c2/c30834/202106/t20210610_311888.html
23. 全国人民代表大会常务委员会：《中华人民共和国网络安全法》（及现行修订文本应按项目日期核查）。http://www.npc.gov.cn/

正式项目应从主管部门官方渠道核对当前文本、配套标准、备案/登记要求与行业规则，并由企业法务、合规和安全确认适用性。本书链接用于形成问题清单，不直接给出法律意见。

## 证据使用原则

- 标准和框架用于校验风险与管理思路，不代替企业控制设计或外部认证。
- 规范和工具文档必须记录版本与核查日；接口、字段、许可证和产品能力可能变化。
- 法规页面用于形成适用性问题，不用一句摘要替代法务结论。
- 本书案例均为虚构的合成案例，数字和目标不是外部成效证据。
