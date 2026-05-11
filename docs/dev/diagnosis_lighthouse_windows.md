# Lighthouse 标签页 Windows 首次连接诊断

## 现象

| 场景 | 操作顺序 | 结果 |
|------|---------|------|
| 1 | 先勾选"光学定位"标签页 → 再连接 | 异常 |
| 2 | 先连接 → 再勾选"光学定位"标签页 | 异常：显示 16 个白色空框，无颜色，界面卡顿，内存增长 |
| 3 | 第 2 次重连 | 正常 |

## cflib 连接时序

```
_conf_updated()
  ├── log.refresh_toc(cb)     # 发送 CMD_RESET_LOGGING，开始 TOC 下载
  ├── param.all_updated_cb()   # 触发参数同步
  └── connected.call(uri)       # ← _connected(link_uri) 在此被调用
      
      [CRTP 线程异步进行 TOC 下载、参数同步等]

_log_toc_updated_cb()          # TOC 下载完成
  └── mem.refresh()            # 内存子系统初始化
      └── param.refresh_toc()  # 参数 TOC 下载
          └── param.request_update_of_all_params()
              └── _all_parameters_updated()
                  └── fully_connected.call()  # 所有初始化完成
```

## 根因分析

### 问题1：_status_report_received 触发重载导致隐藏状态下 QLabel 矩阵重建（导致 16 个白框）

**调用链**：
1. `_connected(link_uri)` 在 TOC 下载开始时被调用（非完成时）
2. 场景2中 `_connected` 被调用时 `tab_visible=False`（标签页隐藏）
3. `_lighthouse_deck_detected()` 注册 lhStatus 日志块
4. 数据到达 → `_status_report_received()` → 首次数据触发 `_reload_tab()`
5. `_reload_tab()` 在 `tab_visible=False` 时删除并重建 QLabel 矩阵
6. `enable()` 被调用时 `tab_reloaded=True`，跳过所有初始化
7. 标签页显示时 QLabel 矩阵处于未刷新状态 → 16 个白色空框

**修复**：移除 `_status_report_received` 中的重载逻辑。数据回调只负责更新位掩码集合，重载由 `enable()` 独家触发。

### 问题2：双重重载导致 QLabel 重复创建（导致内存泄漏）

**调用链**：
1. `enable()` 调度 `QTimer.singleShot(2000, _reload_tab)`
2. 数据到达 → `_status_report_received` → 立即调用 `_reload_tab()`（第一次重载）
3. 2 秒后定时器触发 → 再次调用 `_reload_tab()`（第二次重载）
4. 每次重载创建 80 个新 QLabel + 删除/创建日志块

**修复**：将 `enable()` 中的 `QTimer.singleShot` 延迟重载改为直接同步调用 `_reload_tab()`。

### 问题3：_update_graphics 每帧无差别更新 3D vispy 渲染（主要原因——内存持续增长 + 卡顿）

**调用链**：
1. `_graph_timer` 每 200ms（5Hz）触发 `_update_graphics()`
2. `_update_graphics()` 无条件调用 `_plot_3d.update_cf_pose()` → `MarkerPose.set_pose()`
3. `set_pose()` 每次创建 6 个 numpy 数组 + 调用 4 次 vispy `set_data()`
4. vispy `set_data()` 上传数据到 OpenGL GPU 缓冲区
5. `update_base_station_geos()` 每帧遍历所有基站调用 `set_pose()`
6. 无人机静止时传感器噪声（0.1mm 级抖动）导致 `_last_pose != current_pose` 永远为 True
7. 5Hz × 6 数组 × N 个基站 = 持续 GPU 内存分配 → 内存泄漏 + 界面卡顿

**根本不是 QLabel stylesheet 的问题，是 vispy OpenGL 每帧无差别上传 GPU 缓冲区导致的。**

**修复**：
1. 将 3D 渲染从 5Hz 的 `_update_graphics()` 中分离，由独立 1Hz 的 `_plot_timer` 驱动
2. 添加 1cm² 姿态变化阈值，过滤传感器噪声（`dist < 0.0001`）
3. `update_base_station_geos()` 从定时器回调中移除，仅在 `_geometry_read_cb` 几何数据加载时调用一次
4. GPU 调用量从 ~20-40 set_data()/秒 降至静止时 ~0/s

## 最终修改清单

| 修改 | 位置 | 说明 |
|------|------|------|
| 移除 `_status_report_received` 中的重载 | `_status_report_received()` | 数据回调只更新位掩码，不触发重载 |
| `enable()` 直接调用重载 | `enable()` | 去掉 `QTimer.singleShot` 延迟，避免竞态 |
| 3D 渲染独立定时器 1Hz | `__init__` | 新增 `_plot_timer`，与 UI 刷新解耦 |
| 姿态变化阈值 1cm² | `_update_3d_plot()` | 过滤传感器噪声，静止时不触发 GPU 上传 |
| 几何数据单次推送 | `_geometry_read_cb()` | `update_base_station_geos` 移至数据回调 |
| QLabel 状态缓存 | `_update_basestation_status_indicators()` | `_bs_indicator_state` 字典追踪当前样式，避免重复 `setStyleSheet()` |
| FPS 2→5 | `FPS` 常量 | QLabel 矩阵刷新更灵敏 |
| `_bs_available.clear()` | `_clear_state()` | 修复 `_clear_state()` 中遗漏该集合的清理 |
| `_is_connected` 守卫 | `_status_report_received()` | 忽略断开连接后的残留信号 |
