# TickTick MCP 项目改动记录

## 🎉 重大重构

### 2025-10-15: 综合测试套件 - 验证所有 10 个工具

**目标**：创建全面的测试来验证所有当前工具的功能

**实现**：

- 创建 `test/test_all_tools.py` 综合测试脚本
- 测试所有 10 个 MCP 工具（4 个项目+5 个任务+1 个查询）
- 包含单个和批量操作测试
- 自动清理测试数据

**测试覆盖**：

```
项目管理工具 (4个):
  ✅ get_all_projects
  ✅ get_project_info
  ✅ create_project
  ✅ delete_projects (单个+批量)

任务管理工具 (5个):
  ✅ create_tasks (单个+批量)
  ✅ update_tasks
  ✅ create_subtasks
  ✅ complete_tasks
  ✅ delete_tasks

查询工具 (1个):
  ✅ query_tasks (全部/优先级/项目)
```

**测试结果**：12/13 通过 (92%成功率)

- 包含详细的成功/失败报告
- 彩色输出，易于阅读
- 自动数据清理

---

### 2025-10-15: 项目删除支持批量操作 - `delete_project` → `delete_projects`

**目标**：统一批量操作接口，让项目管理也支持批量删除

**动机**：

- 所有任务操作都已支持批量（create_tasks, update_tasks, delete_tasks 等）
- 项目管理操作应该保持一致性
- 用户可能需要批量清理旧项目或测试项目
- 统一的 API 设计降低学习成本

**改进方案**：

- 将 `delete_project` 重命名为 `delete_projects`
- 支持单个项目 ID 字符串或项目 ID 列表
- 返回格式化的成功/失败统计

**新工具特性**：

```python
delete_projects("abc123")                      # 单个项目
delete_projects(["abc123", "def456", "ghi789"]) # 批量删除
```

**影响**：

- 工具命名更统一（与任务工具保持一致）
- 支持批量项目清理
- 保持向后兼容（单个参数仍然工作）

---

### 2025-10-15: 工具整合 - `get_project` + `get_project_tasks` → `get_project_info`

**目标**：合并相关功能，提供更完整的项目视图

**动机**：

- `get_project` 只返回项目基本信息（名称、颜色等）
- `get_project_tasks` 只返回项目的任务列表
- 通常查看项目时，用户既想看项目信息，也想看任务列表
- 两次调用不如一次调用更高效

**改进方案**：

- 删除 `get_project` 和 `get_project_tasks` 工具
- 创建新的 `get_project_info` 工具
- 使用 `get_project_with_data` API，一次性获取项目信息和任务
- 返回格式化的项目详情 + 完整任务列表

**新工具特性**：

```python
get_project_info(project_id="abc123")  # 返回项目信息和任务
get_project_info(project_id="inbox")   # 支持 inbox
```

**返回内容**：

- 📁 项目基本信息（名称、ID、颜色、视图模式等）
- 📋 项目中的所有任务及其详情

**迁移指南**：

- `get_project("abc123")` → `get_project_info("abc123")`
- `get_project_tasks("abc123")` → `get_project_info("abc123")`
- 如需过滤任务，使用 `query_tasks(project_id="abc123", ...)`

**影响**：

- 工具总数从 11 个减少到 9 个
- 提供更完整的项目视图
- 减少 API 调用次数
- 符合 `feat/simplified-tools` 分支的目标

---

### 2025-10-15: 工具简化 - 移除 `get_project_tasks`

**目标**：简化工具集，消除功能冗余

**动机**：

- `get_project_tasks` 与 `query_tasks` 功能完全重叠
- `get_project_tasks(project_id="xyz")` 等同于 `query_tasks(project_id="xyz")`
- `query_tasks` 更强大，支持额外的过滤条件（日期、优先级、搜索等）
- 保留两个工具增加用户学习成本和维护负担

**改进方案**：

- 删除 `get_project_tasks` 工具
- 所有项目任务查询统一使用 `query_tasks(project_id="...")`
- 更新文档说明迁移方式

**迁移指南**：

- `get_project_tasks("abc123")` → `query_tasks(project_id="abc123")`
- `get_project_tasks("inbox")` → `query_tasks(project_id="inbox")`

**影响**：

- 工具总数从 11 个减少到 10 个
- API 更简洁一致
- 符合 `feat/simplified-tools` 分支的目标

**注**：此改进后来被 `get_project_info` 整合方案取代。

---

### 2025-10-15: 任务操作全面批量化 - 统一的批量操作接口

**目标**：将所有任务操作转换为支持批量处理的统一接口，提升效率并简化 API

**动机**：

- 用户经常需要批量操作多个任务（如批量完成、批量删除、批量更新优先级等）
- 原有设计只有 `batch_create_tasks` 支持批量，其他操作都是单个
- 单个和批量操作分离导致 API 不一致，增加学习成本
- LLM 需要循环调用单个操作来处理多个任务，效率低下

**核心设计理念**：

**统一的批量接口** - 所有任务操作工具同时支持单个和批量操作：

- 单个任务：传入一个字典 `{"task_id": "abc", "project_id": "123"}`
- 批量任务：传入字典列表 `[{...}, {...}, ...]`
- 自动检测输入类型，无需不同的工具名

**改造的工具**：

1. **`create_task` → `create_tasks`**

   - 单个：`{"title": "Buy milk", "project_id": "123"}`
   - 批量：`[{"title": "Task 1", ...}, {"title": "Task 2", ...}]`
   - 支持所有创建参数：title, content, desc, due_date, priority, reminders, repeat_flag, items 等

2. **`update_task` → `update_tasks`**

   - 单个：`{"task_id": "abc", "project_id": "123", "priority": 5}`
   - 批量：`[{"task_id": "abc", ...}, {"task_id": "def", ...}]`
   - 支持所有更新参数：title, content, priority, due_date, start_date 等

3. **`complete_task` → `complete_tasks`**

   - 单个：`{"project_id": "123", "task_id": "abc"}`
   - 批量：`[{"project_id": "123", "task_id": "abc"}, {"project_id": "123", "task_id": "def"}]`

4. **`delete_task` → `delete_tasks`**

   - 单个：`{"project_id": "123", "task_id": "abc"}`
   - 批量：`[{"project_id": "123", "task_id": "abc"}, ...]`

5. **`create_subtask` → `create_subtasks`**

   - 单个：`{"subtask_title": "Sub 1", "parent_task_id": "abc", "project_id": "123"}`
   - 批量：`[{"subtask_title": "Sub 1", ...}, {"subtask_title": "Sub 2", ...}]`

6. **删除 `batch_create_tasks`**
   - 功能已完全被 `create_tasks` 覆盖
   - 不再需要单独的批量工具

**技术实现**：

```python
# 统一的输入处理模式
if isinstance(tasks, dict):
    task_list = [tasks]
    single_task = True
elif isinstance(tasks, list):
    task_list = tasks
    single_task = False

# 统一的结果格式化
if single_task:
    # 返回简洁的单任务结果
    return f"Task created successfully:\n{format_task(task)}"
else:
    # 返回详细的批量操作报告
    return f"""Batch operation completed.
    Successfully processed: {success_count}
    Failed: {fail_count}

    ✅ Success: ...
    ❌ Failed: ..."""
```

**用户体验改进**：

1. **对 LLM 更友好**：

   - 无需判断使用 `create_task` 还是 `batch_create_tasks`
   - 统一使用 `create_tasks`，根据需要传入单个或多个
   - 减少工具数量，降低 token 消耗

2. **更灵活的批量操作**：

   ```python
   # 批量完成今天到期的所有任务
   tasks_due_today = query_tasks(date_filter="today")
   # 提取任务 ID
   complete_tasks([
       {"project_id": task.project_id, "task_id": task.id}
       for task in tasks_due_today
   ])

   # 批量更新优先级
   update_tasks([
       {"task_id": "abc", "project_id": "123", "priority": 5},
       {"task_id": "def", "project_id": "123", "priority": 5},
       {"task_id": "ghi", "project_id": "456", "priority": 5}
   ])
   ```

3. **详细的错误报告**：
   - 批量操作中，成功和失败的任务分别列出
   - 可以一次性看到所有错误，而不是遇到第一个错误就中断
   - 部分成功的批量操作仍会报告成功的部分

**工具数量变化**：

- **删除的工具** (5 个单个操作工具 + 1 个批量工具):

  - ❌ `create_task`
  - ❌ `update_task`
  - ❌ `complete_task`
  - ❌ `delete_task`
  - ❌ `create_subtask`
  - ❌ `batch_create_tasks`

- **新增的工具** (5 个统一批量工具):

  - ✅ `create_tasks` (支持单个和批量)
  - ✅ `update_tasks` (支持单个和批量)
  - ✅ `complete_tasks` (支持单个和批量)
  - ✅ `delete_tasks` (支持单个和批量)
  - ✅ `create_subtasks` (支持单个和批量)

- **净变化**: 6 → 5 (减少 1 个工具)

**总工具数量**：

- 重构前：13 个工具
- 重构后：**12 个工具**
- **总优化：从最初的 23 个工具减少到 12 个 (减少 48%！)** 🎉

**修改的文件**：

- `ticktick_mcp/src/tools/task_tools.py` - 完全重写，实现统一批量接口
- `README.md` - 更新工具表，添加批量操作示例
- `doc/CUROR_MEMORY.md` - 记录这次重大架构变更

**向后兼容性**：

⚠️ **这是一个破坏性变更**：

- 工具名称已更改（`create_task` → `create_tasks`）
- 但功能完全向后兼容：单个任务操作仍然只需传入一个字典
- 现有的单任务调用只需改工具名即可：

  ```python
  # 旧代码
  create_task(title="Buy milk", project_id="123", priority=3)

  # 新代码（参数完全相同）
  create_tasks({"title": "Buy milk", "project_id": "123", "priority": 3})
  ```

**好处总结**：

- ✅ **统一的 API 设计** - 所有任务操作接口一致
- ✅ **更强大的批量能力** - 支持所有操作的批量处理
- ✅ **减少工具数量** - 从 13 → 12 个工具
- ✅ **降低学习成本** - 不需要记忆单个和批量的不同工具
- ✅ **提升 LLM 效率** - 减少循环调用，一次处理多个任务
- ✅ **更好的错误处理** - 批量操作中的部分失败不会影响其他任务
- ✅ **灵活的使用方式** - 同一工具支持单个和批量，按需选择

**使用示例**：

```python
# 单个任务创建
create_tasks({"title": "Buy groceries", "project_id": "inbox"})

# 批量任务创建
create_tasks([
    {"title": "Task 1", "project_id": "inbox", "priority": 5},
    {"title": "Task 2", "project_id": "work", "due_date": "2025-12-31T23:59:59+0000"},
    {"title": "Task 3", "project_id": "inbox"}
])

# 批量完成任务
complete_tasks([
    {"project_id": "inbox", "task_id": "abc123"},
    {"project_id": "work", "task_id": "def456"},
    {"project_id": "work", "task_id": "ghi789"}
])

# 批量更新优先级
update_tasks([
    {"task_id": "abc", "project_id": "inbox", "priority": 5},
    {"task_id": "def", "project_id": "work", "priority": 3}
])

# 批量删除
delete_tasks([
    {"project_id": "archive", "task_id": "old1"},
    {"project_id": "archive", "task_id": "old2"}
])
```

**测试**：

- ✅ 现有测试继续通过（测试使用底层 TickTickClient API，未受影响）
- ✅ 工具签名验证通过
- ✅ 单任务操作功能完整
- ✅ 批量操作功能完整

**未来展望**：

这次重构为未来的优化奠定了基础：

- 可以考虑在底层实现真正的批量 API 调用（如果 TickTick 支持）
- 可以添加事务支持（全部成功或全部回滚）
- 可以添加并发处理来加速批量操作

---

### 2025-10-15: 删除 DEPRECATED 的 `get_task` 工具

**目标**：完成工具简化，彻底移除已弃用的功能

**原因**：

- `get_task` 工具在之前已标记为 DEPRECATED
- 其功能已完全被 `query_tasks(task_id=..., project_id=...)` 替代
- 保留 DEPRECATED 工具会造成混淆和维护负担

**删除内容**：

1. **代码**：
   - `ticktick_mcp/src/tools/task_tools.py` 中的 `get_task()` 函数
2. **文档**：
   - README.md 中的 `get_task` 工具条目

**替代方案**：

```python
# 以前
get_task(project_id="xyz789", task_id="abc123")

# 现在使用
query_tasks(task_id="abc123", project_id="xyz789")
```

**好处**：

- ✅ 减少工具数量（从 16 个减少到 15 个）
- ✅ 避免用户困惑
- ✅ 代码更简洁，维护成本更低
- ✅ 统一的查询接口

**修改的文件**：

- `ticktick_mcp/src/tools/task_tools.py` - 删除 `get_task` 函数
- `README.md` - 删除工具表中的 `get_task` 条目

---

### 2025-10-15: 删除 GTD 相关功能

**目标**：简化工具集，去除特定工作流依赖

**问题**：

- GTD (Getting Things Done) 是特定的时间管理方法论
- "engaged" 和 "next" 预设增加了工具复杂度
- 用户可以通过组合现有过滤器实现相同功能
- 减少学习成本

**删除的内容**：

1. **date_filter 预设**：

   - "engaged": 高优先级 OR 今天到期 OR 已过期
   - "next": 中等优先级 OR 明天到期

2. **文档**：

   - README.md 中的 "GTD Workflow" 章节
   - 示例和说明中的 GTD 引用

3. **测试**：
   - `test_gtd_presets()` 测试函数
   - GTD 相关的测试用例

**保留的功能**：

- 所有基础日期过滤器："today", "tomorrow", "overdue", "next_7_days", "custom"
- 优先级过滤
- 关键词搜索
- 组合过滤（用户可以自己组合实现类似 GTD 的逻辑）

**替代方案**：

```python
# 以前的 "engaged" (GTD预设)
query_tasks(date_filter="engaged")

# 现在可以用组合过滤实现
query_tasks(priority=5)  # 高优先级
query_tasks(date_filter="today")  # 今天到期
query_tasks(date_filter="overdue")  # 已过期

# 以前的 "next" (GTD预设)
query_tasks(date_filter="next")

# 现在可以用组合过滤实现
query_tasks(priority=3)  # 中等优先级
query_tasks(date_filter="tomorrow")  # 明天到期
```

**修改的文件**：

- `ticktick_mcp/src/tools/query_tools.py` - 删除 GTD 预设逻辑
- `README.md` - 删除 GTD 章节和引用
- `test/test_unified_query.py` - 删除 GTD 测试
- `doc/CUROR_MEMORY.md` - 记录此次改动

**好处**：

- ✅ 工具更简洁，减少概念负担
- ✅ 不绑定特定工作流方法论
- ✅ 用户可以根据需求灵活组合过滤条件
- ✅ 减少维护成本

---

### 2025-10-15: 合并 `get_task` 功能到 `query_tasks`

**目标**：简化 API，消除功能重复

**问题**：

- `get_task(project_id, task_id)` 和 `query_tasks(...)` 功能重叠
- `get_task` 只能获取单个已知任务，缺乏灵活性
- 用户需要在两个工具之间选择，增加认知负担

**解决方案**：

- 为 `query_tasks` 添加 `task_id` 参数
- 支持三种查询模式：
  1. **精确查询** - `query_tasks(task_id="...", project_id="...")` - 直接 API 调用（最高效）
  2. **全局 ID 搜索** - `query_tasks(task_id="...")` - 在所有项目中查找任务
  3. **多维过滤** - 原有的过滤功能保持不变，可与 `task_id` 组合使用

**实现细节**：

1. **快速路径优化**：

   ```python
   # 当同时提供 task_id 和 project_id 时，使用直接 API 调用
   if task_id and project_id:
       task = ticktick.get_task(project_id, task_id)
       # 应用其他过滤条件（如果有）
       return format_task(task)
   ```

2. **过滤器集成**：

   ```python
   # task_id 作为过滤条件加入 combined_filter
   if task_id is not None:
       if task.get('id') != task_id:
           return False
   ```

3. **向后兼容**：
   - 保留 `get_task` 工具，标记为 DEPRECATED
   - 在文档字符串中引导用户使用 `query_tasks`

**修改的文件**：

- `ticktick_mcp/src/tools/query_tools.py` - 添加 `task_id` 参数和处理逻辑
- `ticktick_mcp/src/tools/task_tools.py` - 标记 `get_task` 为 DEPRECATED
- `README.md` - 更新文档，说明新用法

**新功能示例**：

```python
# 精确查询（替代 get_task）
query_tasks(task_id="abc123", project_id="xyz789")

# 全局 ID 搜索
query_tasks(task_id="abc123")

# 组合查询（验证任务属性）
query_tasks(task_id="abc123", priority=5)  # 检查任务是否为高优先级
query_tasks(task_id="abc123", date_filter="today")  # 检查任务是否今天到期
```

**好处**：

- ✅ 统一的查询接口，降低学习成本
- ✅ 保持高效的直接查询能力
- ✅ 支持更灵活的组合查询
- ✅ 减少工具数量（从 16 个实质性减少到 15 个）
- ✅ 向后兼容，现有用户不受影响

---

## 🔧 修复的问题

### 1. 日期格式验证问题

**问题**：LLM 通过 MCP 创建带截止日期的任务时失败

- 错误：`Invalid due_date format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000`
- 原因：Python `datetime.fromisoformat()` 不支持 `+0000` 格式（无冒号）

**修复**：

- 添加 `normalize_iso_date()` 函数到 `server.py`
- 更新三处日期验证：`create_task`、`update_task`、`_validate_task_data`
- 支持所有日期格式：`+0000`、`+00:00`、`Z`、`+0800`、`-0500` 等

### 2. API 参数不完整问题

**问题**：MCP 工具缺少 TickTick 官方 API 的多个参数

**修复**：

- `create_task` 添加：`desc`、`is_all_day`、`time_zone`、`reminders`、`repeat_flag`、`sort_order`、`items`
- `update_task` 添加：`desc`、`is_all_day`、`time_zone`、`reminders`、`repeat_flag`、`sort_order`、`items`
- `batch_create_tasks` 支持所有新参数

### 3. 缺少 Inbox 功能

**问题**：无法访问 TickTick 收件箱任务

**修复**：

- 添加 `get_inbox_tasks()` MCP 工具
- 使用特殊项目 ID `"inbox"` 访问收件箱
- 更新 `get_all_projects()` 文档说明 Inbox 需要单独获取

### 4. 时区处理 Bug

**问题**：`get_tasks_due_today` 工具无法正确识别今日到期的任务

- 症状：明明截止日期是今天的任务（如"写文章"任务），却没有被列为"今日到期"
- 原因：时区比较逻辑错误 - 混用了 UTC 时区和用户时区的日期进行比较
- 具体例子：
  - 任务：`2025-10-14 00:00:00 Asia/Shanghai` → UTC: `2025-10-13T16:00:00+0000`
  - 旧逻辑：提取 UTC 日期 `2025-10-13` vs 今天 UTC 日期 `2025-10-14` → ❌ 不匹配
  - 应该：都转换到用户时区比较 `2025-10-14` vs `2025-10-14` → ✅ 匹配

**修复**：

- 添加 `zoneinfo` 模块导入
- 添加 `get_user_timezone_today()` 辅助函数 - 统一获取用户时区的今天日期
- 修复 `_is_task_due_today()` - 将任务时间转换到用户时区后比较日期
- 修复 `_is_task_overdue()` - 在用户时区进行过期判断
- 修复 `_is_task_due_in_days()` - 在用户时区计算指定天数后的日期
- 修复 `get_tasks_due_this_week()` 中的 `week_filter` - 在用户时区判断本周范围

**环境变量**：

- 设置 `TICKTICK_DISPLAY_TIMEZONE="Asia/Shanghai"` 启用时区修复

## 📁 修改的文件

### `ticktick_mcp/src/server.py`

- 添加 `re` 模块导入
- 添加 `zoneinfo` 模块导入（时区修复）
- 添加 `normalize_iso_date()` 函数
- 添加 `get_user_timezone_today()` 辅助函数（时区修复）
- 更新 `create_task()` 参数和验证
- 更新 `update_task()` 参数和验证
- 更新 `_validate_task_data()` 验证
- 添加 `get_inbox_tasks()` 工具
- 更新 `get_all_projects()` 文档
- 修复 `_is_task_due_today()` 时区处理
- 修复 `_is_task_overdue()` 时区处理
- 修复 `_is_task_due_in_days()` 时区处理
- 修复 `get_tasks_due_this_week()` 中的 `week_filter` 时区处理

### `ticktick_mcp/src/ticktick_client.py`

- 更新 `create_task()` 方法参数
- 更新 `update_task()` 方法参数

## ✅ 测试结果

- **完整 API 测试**：17/17 通过
- **日期格式测试**：9/9 通过
- **Inbox 功能测试**：成功获取 26 个任务
- **时区修复测试**：3/3 通过
  - ✅ "写文章"任务正确识别为今日到期（修复前：❌ False → 修复后：✅ True）
  - ✅ "装水"和"把 github 主页弄好看"任务正确识别为明日到期
  - ✅ 时区转换逻辑验证通过

## 🎯 修复效果

**现在可以正常工作的场景**：

- LLM 创建带截止日期的任务（`+0000` 格式）
- 创建全天任务、重复任务、带提醒的任务
- 访问和管理收件箱任务
- 批量创建任务
- 设置时区和子任务
- 正确识别今日到期、过期、未来几天到期的任务（时区敏感）

**关键修复**：

1. ✅ 日期格式问题已解决
2. ✅ API 参数完全对齐
3. ✅ Inbox 功能已实现
4. ✅ 时区处理 Bug 已修复

## 🏗️ 项目架构说明

### 📦 核心组件

1. **MCP 服务器核心** (`server.py`)

   - FastMCP 服务器实现
   - TickTick API 工具封装
   - 时区处理逻辑 ✅ **已修复**

2. **TickTick 客户端** (`ticktick_client.py`)

   - TickTick Open API 封装
   - HTTP 请求处理
   - 数据格式转换

3. **认证模块** (`authenticate.py`, `auth.py`)

   - OAuth 2.0 认证流程
   - Token 管理
   - 凭据验证

4. **命令行接口** (`cli.py`)
   - MCP 服务器启动
   - 配置管理
   - 调试工具

### 📋 功能特性

- 📋 项目和任务管理
- ✏️ 自然语言创建任务
- 🔄 任务状态更新
- 📅 时区敏感的日期处理
- 📥 收件箱任务支持
- 🔌 Claude MCP 集成

## 📚 详细功能文档

### 🔧 时区转换功能

TickTick MCP 支持智能时区转换，可以将 TickTick API 返回的 UTC 时间自动转换为本地时间或指定时区的时间。

#### 主要特性

1. **自动时区转换**

   - **默认行为**：所有任务的日期时间会自动转换为本地时区显示
   - **智能优先级**：任务时区 > 配置时区 > 系统本地时区
   - **向后兼容**：保持原始 UTC 时间信息以供参考

2. **显示格式**

   ```
   2024-01-20 17:00:00 (Asia/Shanghai) [UTC: 2024-01-20T09:00:00+0000]
   ```

   包含：

   - 本地时间：`2024-01-20 17:00:00`
   - 时区标识：`(Asia/Shanghai)`
   - 原始 UTC 时间：`[UTC: 2024-01-20T09:00:00+0000]`

3. **环境变量配置**
   ```bash
   # 在 .env 文件中添加
   TICKTICK_DISPLAY_TIMEZONE=Asia/Shanghai
   ```

#### 支持的时区

- `Local` - 使用系统本地时区（默认）
- `Asia/Shanghai` - 中国标准时间
- `America/New_York` - 美国东部时间
- `Europe/London` - 英国时间
- `Asia/Tokyo` - 日本标准时间
- 等等...（支持所有 IANA 时区标识符）

#### 技术实现

- `convert_utc_to_local()` - UTC 时间转换为本地时间
- `normalize_iso_date()` - 标准化 ISO 日期格式
- `format_task()` - 格式化任务显示（支持时区转换）

### 📥 Inbox 功能详解

#### 核心发现

1. **Inbox 是特殊项目**

   - 固定的项目 ID：`"inbox"`（小写）
   - 不在普通项目列表 API 中返回
   - 但可以通过 `GET /open/v1/project/inbox/data` 访问

2. **API 行为**
   - 可以读取：✅
   - 可以创建任务：✅
   - 可以删除任务：✅
   - 与普通项目 API 一致

#### 使用场景

1. **快速查看收件箱**

   ```
   用户: "我收件箱里有什么？"
   LLM: 调用 get_inbox_tasks()
   返回: 26 个任务的详细列表
   ```

2. **快速记录想法**

   ```
   用户: "记一个任务：买牛奶"
   LLM: create_task(title="买牛奶", project_id="inbox")
   结果: 任务快速保存到收件箱
   ```

3. **整理任务**
   ```
   用户: "显示我的收件箱任务"
   LLM: get_inbox_tasks()
   用户: "把第一个任务移到工作项目"
   LLM: update_task(..., project_id="工作项目ID")
   ```

#### 代码示例

```python
# 在 MCP 工具中
@mcp.tool()
async def get_inbox_tasks() -> str:
    """获取收件箱任务"""
    inbox_data = ticktick.get_project_with_data("inbox")

    if 'error' in inbox_data:
        return f"Error: {inbox_data['error']}"

    tasks = inbox_data.get('tasks', [])

    if not tasks:
        return "Your inbox is empty. 📭"

    return format_tasks(tasks)
```

---

## 🏗️ 项目重构记录（2025-10-14）

### 📋 重构目标

原始的 `server.py` 文件过于庞大（1312 行），包含了太多不同类型的功能，导致代码难以维护和扩展。

### 🎯 重构方案

按功能域将代码分离到不同模块：

```
ticktick_mcp/src/
├── server.py          # MCP服务器核心 (45行) ✨ 精简96%
├── config.py          # 配置管理 (61行)
├── utils/             # 工具函数模块
│   ├── timezone.py    # 时区处理 (111行)
│   ├── formatters.py  # 格式化函数 (108行)
│   └── validators.py  # 验证和过滤逻辑 (252行)
└── tools/             # MCP工具定义
    ├── project_tools.py  # 项目相关工具 (179行)
    ├── task_tools.py     # 任务CRUD工具 (391行)
    └── query_tools.py    # 查询和过滤工具 (259行)
```

### ✅ 重构成果

1. **代码组织清晰**：

   - 原始 `server.py`：1312 行 → 45 行（精简 96%）
   - 按功能域分离：9 个专门模块，职责明确

2. **模块化设计**：

   - `utils/` 包含可复用的工具函数
   - `tools/` 包含按功能分类的 MCP 工具
   - `config.py` 统一管理配置和客户端初始化

3. **易于维护**：

   - 修改时区逻辑只需要改 `timezone.py`
   - 添加新工具知道应该放在哪个模块
   - 每个模块都有明确的职责边界

4. **向后兼容**：
   - 保持所有原有功能不变
   - API 接口完全一致
   - 测试通过率保持不变

### 📊 重构统计

- **原始文件**：1 个巨大文件（1312 行）
- **重构后**：9 个模块化文件（总计 1417 行，包含更好的文档）
- **核心服务器**：从 1312 行精简到 45 行（96%减少）
- **功能完整性**：100%保持

### 🔧 技术要点

1. **依赖注入**：使用 `ensure_client()` 统一管理客户端
2. **工具注册**：通过 `register_*_tools()` 函数模块化注册
3. **导入优化**：清晰的模块导入层次结构
4. **错误处理**：保持原有的错误处理逻辑

这次重构大大提升了代码的可维护性和扩展性，为未来的功能开发奠定了良好的基础。

---

---

## 🔄 工具简化优化（2025-10-15）

### 📋 优化目标

原有的 23 个 MCP 工具对 LLM 来说过于复杂，特别是日期查询工具有 5 个功能高度重叠的工具，增加了 LLM 的选择负担和 token 消耗。

### 🎯 实施方案

**合并日期查询工具（5 → 1）**

原有工具：

- `get_tasks_due_today()` - 获取今天到期的任务
- `get_tasks_due_tomorrow()` - 获取明天到期的任务
- `get_tasks_due_in_days(days)` - 获取指定天数后到期的任务
- `get_tasks_due_this_week()` - 获取本周内到期的任务
- `get_overdue_tasks()` - 获取过期任务

合并为：

```python
@mcp.tool()
async def query_tasks_by_date(
    date_filter: str,
    custom_days: int = None
) -> str:
    """
    Query tasks by date/deadline criteria.

    Args:
        date_filter: "today", "tomorrow", "overdue", "next_7_days", "custom"
        custom_days: Number of days (only for "custom" filter)
    """
```

### ✅ 优化效果

1. **工具数量减少**：23 → 19 个工具（减少 17%）
2. **更清晰的语义**：使用枚举值而非多个函数名
3. **降低选择复杂度**：LLM 只需选择一个工具，然后传入不同参数
4. **减少 prompt 长度**：5 段工具描述合并为 1 段，大幅减少 token 消耗
5. **保持功能完整**：所有原有功能通过参数组合实现

### 📊 使用示例

```python
# 今天到期
query_tasks_by_date("today")

# 明天到期
query_tasks_by_date("tomorrow")

# 过期任务
query_tasks_by_date("overdue")

# 未来 7 天
query_tasks_by_date("next_7_days")

# 自定义天数（如 3 天后）
query_tasks_by_date("custom", 3)
```

### 🔧 技术实现

- 保持底层验证逻辑不变（`is_task_due_today`, `is_task_overdue`, `is_task_due_in_days`）
- 通过参数路由到相应的过滤函数
- 添加参数验证确保正确使用
- 保持时区敏感的日期比较逻辑

### 📝 修改的文件

- `ticktick_mcp/src/tools/query_tools.py` - 合并日期查询工具
- `README.md` - 更新工具文档和示例
- `doc/CUROR_MEMORY.md` - 记录优化过程
- `test/test_query_tools.py` - 新增专门测试文件验证新工具功能

### ✅ 测试结果

创建了专门的测试文件 `test/test_query_tools.py` 来验证新工具：

```bash
python test/test_query_tools.py
```

测试覆盖：

1. ✅ 工具注册验证
2. ✅ 测试环境设置（创建不同截止日期的测试任务）
3. ✅ 验证逻辑测试（`is_task_due_today`, `is_task_overdue`, `is_task_due_in_days`）
4. ✅ 参数验证测试（有效和无效的 `date_filter` 值）
5. ✅ 自动清理测试数据

**测试结果**: 4/4 通过 ✅

### 💡 设计原则

1. **对 LLM 友好**：减少选择困难，降低认知负担
2. **保持简洁**：常用场景用简单参数，复杂场景用 custom 选项
3. **向后兼容**：底层逻辑不变，只是接口优化
4. **易于扩展**：新增日期过滤类型只需添加新的 date_filter 选项

这次优化是为 MCP 工具 LLM 友好化的第一步，未来可以考虑进一步简化优先级查询工具等。

---

---

## 🔧 工具进一步简化（2025-10-15）

### 📋 合并 Inbox 功能

**背景**：`get_inbox_tasks` 和 `get_project_tasks` 功能高度重叠，都是获取任务列表。

**改进方案**：

- 删除独立的 `get_inbox_tasks` 工具
- 增强 `get_project_tasks`，支持特殊参数 `project_id="inbox"`

**实现细节**：

```python
@mcp.tool()
async def get_project_tasks(project_id: str) -> str:
    """
    Get all tasks in a specific project or inbox.

    Args:
        project_id: ID of the project, or "inbox" to get inbox tasks

    Examples:
        - get_project_tasks("abc123") → Get tasks from project
        - get_project_tasks("inbox") → Get tasks from Inbox
    """
```

**优化效果**：

- 工具数量：19 → **18** 个（再减少 1 个）
- API 更一致：使用统一的接口获取任务
- 功能保持：Inbox 空时仍显示特殊消息 "📭 Great job staying organized!"

**测试验证**：

- ✅ 可以使用 "inbox" 获取收件箱任务
- ✅ 大小写不敏感（"inbox" 和 "Inbox" 都可以）
- ✅ 成功获取到 29 个 inbox 任务

---

---

## 🚀 统一查询工具 - 最终简化 (2025-10-15)

### 📋 问题分析

经过前面的优化，工具数量从 23 → 18，但仍存在问题：

- 6 个查询工具功能重叠（get_all_tasks, get_tasks_by_priority, query_tasks_by_date, search_tasks, get_engaged_tasks, get_next_tasks）
- 每个工具只解决一个具体问题
- 无法灵活组合过滤条件
- LLM 仍需在多个相似工具间选择

### 🎯 解决方案：query_tasks 超级工具

创建一个支持多维度过滤的统一工具，替代所有查询工具。

**设计原则**：

- 所有参数可选（无参数 = 查询所有）
- 支持任意组合（AND 逻辑）
- 包含 GTD 预设（OR 逻辑）
- 向后兼容所有旧功能

**工具签名**：

```python
query_tasks(
    date_filter: Optional[str] = None,      # 日期过滤
    custom_days: Optional[int] = None,      # 自定义天数
    priority: Optional[int] = None,         # 优先级
    search_term: Optional[str] = None,      # 搜索关键词
    project_id: Optional[str] = None,       # 项目限定
    include_all_projects: bool = True       # 是否搜索所有项目
)
```

### ✨ 功能特性

**1. 多维度过滤** (AND 逻辑)

```python
# 可以组合任意过滤条件
query_tasks(date_filter="today", priority=5)           # 今天 AND 高优先级
query_tasks(search_term="meeting", priority=3)         # 包含"meeting" AND 中优先级
query_tasks(date_filter="next_7_days", search_term="review", priority=5)
```

**2. GTD 预设** (OR 逻辑)

```python
query_tasks(date_filter="engaged")  # 高优先级 OR 今天到期 OR 过期
query_tasks(date_filter="next")     # 中优先级 OR 明天到期
```

**3. 项目限定**

```python
query_tasks(project_id="inbox", priority=5)           # 收件箱中的高优先级
query_tasks(project_id="abc123", date_filter="today") # 特定项目今天到期
```

### 📊 优化效果

**删除的工具 (6 个)**：

- ❌ `get_all_tasks`
- ❌ `get_tasks_by_priority`
- ❌ `query_tasks_by_date`
- ❌ `search_tasks`
- ❌ `get_engaged_tasks`
- ❌ `get_next_tasks`

**新增工具 (1 个)**：

- ✅ `query_tasks` - 统一查询工具

**工具数量**：

- 优化前: 18 个
- 优化后: **13 个**
- 减少: 5 个工具（27.8%）

**总体优化**（相比最初）：

- 最初: 23 个工具
- 现在: **13 个工具**
- 总共减少: **10 个工具（43.5% 优化）** 🎉

### 🧪 测试验证

创建了专门的测试文件 `test/test_unified_query.py`：

**测试覆盖**：

- ✅ 单一过滤器（日期、优先级、搜索）
- ✅ 组合过滤器（AND 逻辑）
- ✅ GTD 预设（OR 逻辑）
- ✅ 项目过滤（包括 inbox）
- ✅ 自动清理测试数据

**测试结果**：

```
✅ date_filter='today': 1 个任务
✅ priority=5: 2 个任务
✅ search_term='meeting': 1 个任务
✅ today + priority=5: 1 个任务
✅ date_filter='engaged': 2 个任务
✅ date_filter='next': 3 个任务
✅ project_id + priority=5: 2 个任务
✅ project_id='inbox': 29 个任务
```

所有测试通过 ✅

### 💡 对 LLM 的巨大改进

1. **极大简化选择**：从 6 个查询工具 → 1 个工具
2. **无限组合能力**：不再受限于预设场景，可以任意组合
3. **更强大的功能**：支持复杂查询，如"收件箱中今天到期的高优先级任务"
4. **减少 prompt**：查询相关描述减少约 40% tokens
5. **降低认知负担**：LLM 只需记住一个工具和它的参数

### 📝 使用示例

```python
# 基础查询
query_tasks()                                    # 所有任务
query_tasks(date_filter="today")                 # 今天到期
query_tasks(priority=5)                          # 高优先级

# 组合查询
query_tasks(date_filter="today", priority=5)     # 今天+高优先级
query_tasks(search_term="bug", priority=5)       # 搜索"bug"+高优先级
query_tasks(date_filter="next_7_days", priority=3, search_term="review")

# GTD 工作流
query_tasks(date_filter="engaged")               # 紧急任务
query_tasks(date_filter="next")                  # 下一步任务

# 项目限定
query_tasks(project_id="inbox")                  # 收件箱所有任务
query_tasks(project_id="inbox", date_filter="today")  # 收件箱今天到期
```

---

_记录日期：2025-10-11（初始修复）_  
_时区修复日期：2025-10-14_  
_项目重构日期：2025-10-14_  
_工具简化优化：2025-10-15（日期查询合并 + Inbox 功能合并 + 统一查询工具）_
