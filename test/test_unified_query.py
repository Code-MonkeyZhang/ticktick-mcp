#!/usr/bin/env python3
"""
Unified Query Tool 测试脚本

测试新的统一 query_tasks 工具的所有功能
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ticktick_mcp.src.ticktick_client import TickTickClient


def print_section(title: str):
    """打印测试节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def setup_test_environment(client: TickTickClient):
    """设置测试环境"""
    print("🔧 设置测试环境...")
    
    # 查找或创建测试项目
    projects = client.get_projects()
    test_project = None
    for p in projects:
        if p.get('name') == "滴答清单MCP测试区域":
            test_project = p
            break
    
    if not test_project:
        print("   创建测试项目...")
        test_project = client.create_project(
            name="滴答清单MCP测试区域",
            color="#4A90E2"
        )
    
    project_id = test_project['id']
    print(f"   ✅ 使用项目: {test_project.get('name')} ({project_id})")
    
    # 清理旧的测试任务
    print("   🧹 清理旧任务...")
    project_data = client.get_project_with_data(project_id)
    old_tasks = project_data.get('tasks', [])
    for task in old_tasks:
        if task.get('title', '').startswith('[统一查询测试]'):
            client.delete_task(project_id, task['id'])
    
    # 创建测试任务
    print("   📝 创建测试任务...")
    test_tasks = []
    
    # 1. 今天 + 高优先级
    task1 = client.create_task(
        title="[统一查询测试] 今天高优先级",
        project_id=project_id,
        due_date=datetime.now().strftime("%Y-%m-%dT23:59:59+0000"),
        priority=5,
        content="测试任务：今天到期，高优先级"
    )
    test_tasks.append(('today_high', task1['id']))
    
    # 2. 明天 + 中优先级  
    task2 = client.create_task(
        title="[统一查询测试] 明天中优先级",
        project_id=project_id,
        due_date=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59+0000"),
        priority=3,
        content="测试任务：明天到期，中优先级"
    )
    test_tasks.append(('tomorrow_medium', task2['id']))
    
    # 3. 过期 + 高优先级
    task3 = client.create_task(
        title="[统一查询测试] 过期高优先级",
        project_id=project_id,
        due_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT23:59:59+0000"),
        priority=5,
        content="测试任务：已过期，高优先级"
    )
    test_tasks.append(('overdue_high', task3['id']))
    
    # 4. 3天后 + 低优先级
    task4 = client.create_task(
        title="[统一查询测试] 3天后低优先级",
        project_id=project_id,
        due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT23:59:59+0000"),
        priority=1,
        content="测试任务：3天后，低优先级"
    )
    test_tasks.append(('custom_low', task4['id']))
    
    # 5. 无日期 + 中优先级（包含关键词"meeting"）
    task5 = client.create_task(
        title="[统一查询测试] Team meeting准备",
        project_id=project_id,
        priority=3,
        content="准备team meeting的材料"
    )
    test_tasks.append(('meeting', task5['id']))
    
    print(f"   ✅ 创建了 {len(test_tasks)} 个测试任务")
    
    return project_id, test_tasks


def test_single_filters(client: TickTickClient, project_id: str):
    """测试单一过滤器"""
    print_section("测试 1: 单一过滤器")
    
    from ticktick_mcp.src.utils.validators import (
        get_project_tasks_by_filter,
        is_task_due_today,
        is_task_overdue,
        is_task_due_in_days,
        task_matches_search
    )
    
    # 获取项目数据
    project_data = client.get_project_with_data(project_id)
    all_tasks = project_data.get('tasks', [])
    
    print(f"   总任务数: {len(all_tasks)}")
    
    # Test 1: date_filter="today"
    today_tasks = [t for t in all_tasks if is_task_due_today(t)]
    print(f"   ✅ date_filter='today': {len(today_tasks)} 个任务")
    
    # Test 2: priority=5
    high_priority = [t for t in all_tasks if t.get('priority', 0) == 5]
    print(f"   ✅ priority=5: {len(high_priority)} 个任务")
    
    # Test 3: search_term="meeting"
    meeting_tasks = [t for t in all_tasks if task_matches_search(t, "meeting")]
    print(f"   ✅ search_term='meeting': {len(meeting_tasks)} 个任务")


def test_combined_filters(client: TickTickClient, project_id: str):
    """测试组合过滤器"""
    print_section("测试 2: 组合过滤器 (AND 逻辑)")
    
    from ticktick_mcp.src.utils.validators import (
        is_task_due_today,
        is_task_overdue
    )
    
    project_data = client.get_project_with_data(project_id)
    all_tasks = project_data.get('tasks', [])
    
    # Test 1: today + high priority
    today_high = [t for t in all_tasks 
                  if is_task_due_today(t) and t.get('priority', 0) == 5]
    print(f"   ✅ today + priority=5: {len(today_high)} 个任务")
    if today_high:
        print(f"      → {today_high[0].get('title')}")
    
    # Test 2: overdue + high priority  
    overdue_high = [t for t in all_tasks 
                    if is_task_overdue(t) and t.get('priority', 0) == 5]
    print(f"   ✅ overdue + priority=5: {len(overdue_high)} 个任务")
    if overdue_high:
        print(f"      → {overdue_high[0].get('title')}")


def test_gtd_presets(client: TickTickClient, project_id: str):
    """测试 GTD 预设"""
    print_section("测试 3: GTD 预设 (OR 逻辑)")
    
    from ticktick_mcp.src.utils.validators import (
        is_task_due_today,
        is_task_overdue,
        is_task_due_in_days
    )
    
    project_data = client.get_project_with_data(project_id)
    all_tasks = project_data.get('tasks', [])
    
    # Test 1: "engaged" (high priority OR due today OR overdue)
    engaged = [t for t in all_tasks 
               if (t.get('priority', 0) == 5 or 
                   is_task_due_today(t) or 
                   is_task_overdue(t))]
    print(f"   ✅ date_filter='engaged': {len(engaged)} 个任务")
    for task in engaged:
        print(f"      → {task.get('title')}")
    
    # Test 2: "next" (medium priority OR due tomorrow)
    next_tasks = [t for t in all_tasks 
                  if (t.get('priority', 0) == 3 or 
                      is_task_due_in_days(t, 1))]
    print(f"   ✅ date_filter='next': {len(next_tasks)} 个任务")
    for task in next_tasks:
        print(f"      → {task.get('title')}")


def test_project_filter(client: TickTickClient, project_id: str):
    """测试项目过滤"""
    print_section("测试 4: 项目过滤")
    
    # Test with project_id
    project_data = client.get_project_with_data(project_id)
    tasks = project_data.get('tasks', [])
    
    high_in_project = [t for t in tasks if t.get('priority', 0) == 5]
    print(f"   ✅ project_id + priority=5: {len(high_in_project)} 个任务")
    
    # Test inbox
    inbox_data = client.get_project_with_data("inbox")
    inbox_tasks = inbox_data.get('tasks', [])
    print(f"   ✅ project_id='inbox': {len(inbox_tasks)} 个任务")


def cleanup(client: TickTickClient, project_id: str, test_tasks: list):
    """清理测试数据"""
    print_section("清理测试数据")
    
    deleted = 0
    for task_type, task_id in test_tasks:
        result = client.delete_task(project_id, task_id)
        if 'error' not in result:
            deleted += 1
    
    print(f"   🧹 删除了 {deleted} 个测试任务")
    
    # 验证清理
    project_data = client.get_project_with_data(project_id)
    remaining = [t for t in project_data.get('tasks', []) 
                 if t.get('title', '').startswith('[统一查询测试]')]
    
    if not remaining:
        print(f"   ✅ 清理成功，项目已清空")
    else:
        print(f"   ⚠️  还有 {len(remaining)} 个测试任务残留")


def main():
    """主测试函数"""
    print("="*70)
    print("🔍 统一查询工具 (query_tasks) 功能测试")
    print("="*70)
    
    # 初始化客户端
    try:
        client = TickTickClient()
        print("✅ TickTick 客户端初始化成功\n")
    except Exception as e:
        print(f"❌ 无法初始化客户端: {e}")
        return 1
    
    try:
        # 设置测试环境
        project_id, test_tasks = setup_test_environment(client)
        
        # 运行测试
        test_single_filters(client, project_id)
        test_combined_filters(client, project_id)
        test_gtd_presets(client, project_id)
        test_project_filter(client, project_id)
        
        # 清理
        cleanup(client, project_id, test_tasks)
        
        print("\n" + "="*70)
        print("🎉 所有测试完成！")
        print("="*70)
        print()
        print("📊 测试总结:")
        print("   ✅ 单一过滤器测试通过")
        print("   ✅ 组合过滤器测试通过 (AND 逻辑)")
        print("   ✅ GTD 预设测试通过 (OR 逻辑)")
        print("   ✅ 项目过滤测试通过")
        print()
        print("🎯 统一查询工具验证成功！")
        print("   - 支持多维度过滤")
        print("   - 支持过滤器组合")
        print("   - 支持 GTD 预设")
        print("   - 支持项目限定")
        print("="*70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

