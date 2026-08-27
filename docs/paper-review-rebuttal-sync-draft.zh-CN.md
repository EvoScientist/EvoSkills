# EvoSkills 同步草稿

日期：2026-08-27

## 目标

将当前 `skill-opt` 中经过本地三篇 OpenReview 对照、远程 PR/issue 核验和
盲评审计后的 paper-review / paper-rebuttal 改动，按 EvoSkills 现有 skill
结构同步到 `/Users/muxincg/huawei-research/EvoSkills`，保留其 paper-review
1.2 的 agent/EXPERT/scripts 架构。

## 拟同步内容

- `skills/paper-review/SKILL.md`：同步 claim-evidence、竞争解释、decision
  clusters、最多三个 primary blockers、实验有效性和严重度校准规则。
- `skills/paper-review/references/`：只同步与上述规则直接相关的精简内容，
  不覆盖 EvoSkills 独有的 `EXPERT.md` 和 `scripts/five_aspect_review.js`。
- `skills/paper-rebuttal/SKILL.md` 及其 references/assets：同步 evidence-first、
  resolvability、多轮 discussion 状态和 reviewer-ready 输出。
- 不把本地 PDF、OpenReview 原始抓取、盲评包或 ledger 上传到 EvoSkills；
  它们只作为本次变更的本地证据。

## 真实数据口径

- Review 历史实测：strict recall `0.293 -> 0.387`，lenient recall
  `0.480 -> 0.520`；FP 判分尚未完成。
- Rebuttal 历史 L2：score-driving recall `0.692 -> 0.810`；L1 曾为
  `1 loss / 2 ties`，不能作为稳定胜率。
- 本轮确定性 instruction audit：review `5/14 -> 14/14`，rebuttal
  `1/9 -> 9/9`。这是规则覆盖率，不是端到端模型准确率。
- 盲评快照：review `6/12`、rebuttal `2/8`，存在预披露/未完整回收偏差，
  不作为 release gate。

## 版本和验证

- 本地候选：paper-review `1.1.2`，paper-rebuttal `1.4.2`。
- EvoSkills 当前主线：paper-review `1.2`，因此采用内容迁移而非粗暴覆盖。
- 验证：`validate_skills.py`、现有 human-eval 单测、Python 语法检查；
  如目标仓库允许，再运行其 paper-review script smoke test。

## 提交方式

1. 在 EvoSkills 创建独立分支 `opt/paper-review-rebuttal-evidence-calibration`。
2. 先提交一个 draft commit，正文包含本草稿对应的范围、冲突和数据口径。
3. 检查 diff，确认不覆盖 agent 架构、不上传隐私/评测钥匙。
4. 再提交正式内容 commit，使用 Conventional Commit：
   `feat(paper-review): calibrate evidence and decision blockers`；
   rebuttal 内容若必须拆分，使用独立 commit。
5. 本地验证通过后，再由用户决定是否 push/开 PR；本次默认不直接推送远程。

## 风险和回滚

- EvoSkills 的 paper-review `SKILL.md` 比当前本地版更新，直接替换会丢失
  aspect seats、EXPERT 和 script 入口，因此必须人工合并。
- 当前本地 `skill-opt` 有用户未提交修改，不回滚、不混入无关文件。
- 目标仓库工作树若出现已有修改，停止写入并先报告。
