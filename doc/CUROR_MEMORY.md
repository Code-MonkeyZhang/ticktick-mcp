# TickTick MCP 项目改动记录

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
- 更新 `get_projects()` 文档说明 Inbox 需要单独获取

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
- 更新 `get_projects()` 文档
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

_记录日期：2025-10-11（初始修复）_  
_时区修复日期：2025-10-14_  
_项目重构日期：2025-10-14_
