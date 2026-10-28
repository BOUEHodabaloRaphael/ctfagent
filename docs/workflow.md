# 解题流程

更新时间：2026-03-29

## 用户入口

默认入口不是脚本列表，而是：

1. 配置 `Claude Code`
2. 在仓库根目录打开会话
3. 运行 `/setup`
4. 提供题目标题、分类、描述、目标和附件

如果字段已经够用，`/setup` 应直接创建 workspace。

## 标准链路

一条题目通常按这个顺序流转：

1. `setup`
2. `challenge-workspace-bootstrap`
3. `ctf-solver-profile`
4. 一个具体题型 skill
5. 需要时调用浏览器自动化或网络搜索
6. `ctf-knowledge-capture`
7. `skill-maintainer`

这是 agent 的内部顺序，不是要求用户手动逐项调用。

当第 7 步准备新增 skill 时，`skill-maintainer` 应先做增长审计：

- 是否和已有 skill 重叠
- 是否只是脚本或测试缺失
- 是否有稳定边界
- 是否已经有 lab / smoke / 回归支撑

审计不过时，不新增 skill，直接退回较小改动。

## 输入

开始一道题，至少应提供这些信息中的大部分：

- 题目标题
- 题目分类
- 题目描述
- URL / 主机 / 端口 / 连接方式
- 附件路径
- 限制条件

## 工作默认值

这个仓库的默认解题姿势是：

- 先做低成本验证
- 先读源码、元信息和结构线索
- 根据证据切方向
- 记录失败路径，不只记录成功路径

## 输出

一次完整流程的产物通常包括：

- `workspaces/<challenge-id>/` 下的题目入口、附件、笔记和工件
- 解题结论
- `knowledge/` 下的 writeup 或 pattern

## 加速工具（可选，新增）

这两个脚本是对标准链路的补充，不改变上面的流程，只是把两个之前靠人工完成的步骤变成可脚本化的动作：

1. **验证循环** — `src/tools/workspace/verify_loop.py`
   - 自动发现 workspace 里的 `solve.py` / `exploit.py` / `exp_*.py` / `exploit_*.py`（或用 `--cmd` 指定），逐个运行，扫描输出里的 flag 模式。
   - 每次运行都追加写入 `<workspace>/verify_log.jsonl`（不覆盖、不删除已有文件）。
   - 命中 flag 时写入 `flags/pending/`；加 `--submit` 可直接调用 `ctf_platform_client.py submit`。
   - 用法：`python3 src/tools/workspace/verify_loop.py --workspace workspaces/<id>`

2. **并行调度建议** — `src/tools/workspace/parallel_dispatch.py`
   - 扫描 `workspaces/`，跳过笔记里已标记 solved 的题目，按最近修改时间排序，给出最活跃的 N 个。
   - 默认只打印建议（`git worktree add` 命令形态），加 `--apply` 才会真正创建新 worktree；从不删除已有 worktree 或文件。
   - 用法：`python3 src/tools/workspace/parallel_dispatch.py --top 3 --apply`，然后在每个 `worktree_path` 分别开一个 Claude Code 会话。

两者都有对应的 `tests/test_verify_loop.py` / `tests/test_parallel_dispatch.py`。

## 边界

当前流程默认解决的是：

- 单题分析
- 人在回路中的工具调用
- 本地知识回查
- 工件和结论沉淀

当前流程不默认解决的是：

- 批量题目调度（`parallel_dispatch.py` 只给建议，不做编排）
- 自动 flag 提交（`verify_loop.py --submit` 覆盖单个 flag 的场景，不是全自动批量提交）
- 多 agent 编排平台
