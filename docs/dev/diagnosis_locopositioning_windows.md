# 无线定位标签页问题诊断

## 现象

| 场景 | 操作顺序 | 结果 |
|------|---------|------|
| 1 | 先勾选"无线定位"标签页 → 再连接 | 内存缓慢增加，位置数据不更新 |
| 2 | 先连接 → 再勾选"无线定位"标签页 | 内存缓慢增加，位置数据不更新 |
| 3 | 第 2 次重连 | 内存稳定，位置数据不更新 |

## 根因分析

### 问题1：_update_graphics 中位置标签刷新条件错误（导致位置数据不更新）

**调用链**：
1. `_update_graphics()` 中位置标签更新被 `is_loco_deck_active` 条件包裹
2. 位置数据来自 `PoseLogger`（姿态日志），不依赖 loco deck
3. 场景1/2 中 loco deck 尚未被检测到 → `is_loco_deck_active=False` → 位置标签从不刷新
4. 场景3 中 loco deck 已被检测到 → 位置标签正常更新

**修复**：将位置标签更新条件从 `is_loco_deck_active` 改为 `_is_connected`。位置数据来自 PoseLogger，只要已连接就应该更新。

### 问题2：QLabel 指示灯不刷新

**调用链**：
1. `_update_ranging_status_indicators()` 仅在 `_active_id_list_updated()` 回调中调用
2. `_active_id_list_updated()` 由 `AnchorStateMachine` 以 1Hz 频率轮询触发
3. 但 `AnchorStateMachine` 的轮询周期为 8 步（8 秒），且只有 2/8 步触发 `GET_ACTIVE`
4. 实际有效更新频率约为 0.25Hz，UI 响应极慢

**修复**：将 `_update_ranging_status_indicators()` 加入 `_update_graphics()` 定时器回调（5Hz），在 `is_loco_deck_active and self._anchors` 条件下执行。

### 问题3：QLabel 样式缓存导致"既非红也非绿"的白框

**调用链**：
1. `_indicator_state` 字典以 anchor ID 为 key 缓存当前样式
2. 当 anchor ID 集合从 [1,2,3] 扩展到 [0-7] 时，QLabel 按行/列位置重新分配
3. 原先位于位置 0 的 label（曾分配给 ID=1）现在被分配给 ID=0
4. 缓存中有 ID=0 的旧样式，但新 label widget 从未调用过 `setStyleSheet()`
5. `new_style == old_style` 命中缓存 → 跳过 `setStyleSheet()` → 新 label 显示无背景色（白色）

**修复**：在 `_update_ranging_status_indicators()` 中检测 anchor ID 集合变化，当 `set(ids) != set(cached_ids)` 时清空整个 `_indicator_state` 缓存。

### 问题4：3D 渲染每帧无差别上传 vispy GPU 数据（内存持续增长的主要原因）

**调用链**：
1. `_graph_timer` 每 500ms（2Hz）触发 `_update_graphics()` → `_update_3d_plot()` → `update_data()`
2. `update_data()` 对每个 anchor 调用 `_update_anchor()` → 8 anchor × 2 visual（marker + text）= 16 次 `set_data()`
3. 每次 `set_data()` 创建 numpy 数组 + 调用 vispy `set_data()` → 上传 OpenGL GPU 缓冲区
4. 即使 anchor 位置是静态的（物理基站不移动），每 2 秒仍创建 32 个数组 + 32 次 GPU 上传
5. vispy SceneCanvas 的背景渲染（即使 `autoswap=False`）也会消耗 GPU 内存

**修复**（三管齐下）：
1. 将 3D 渲染从 2Hz 的 `_update_graphics()` 分离，由独立 1Hz 的 `_plot_timer` 驱动
2. `_update_3d_plot()` 仅调用 `update_cf_position()`（只更新 CF 无人机标记），不触碰 anchor visual
3. Anchor visual 仅在 `_anchor_data_updated()` 回调中更新（anchor 数量变化时触发一次完整渲染）
4. 添加 5cm² 姿态变化阈值，过滤传感器噪声（`dist < 0.0005`）

### 问题5：__init__ 中状态变量初始化顺序错误

**调用链**：
1. `__init__` 调用 `_clear_state()`
2. `_clear_state()` 访问 `self._indicator_state.clear()` 和 `self._last_pose`
3. 但 `_clear_state()` → `_clear_anchors()` 访问 `self._plot_3d`（尚在 `_set_up_plots()` 之前）
4. AttributeError 崩溃

**修复**：
- 在 `_clear_state()` 调用之前初始化 `_anchors`、`_indicator_state`、`_last_pose`、`_is_connected`
- 在 `_clear_anchors()` 中添加 `hasattr(self, '_plot_3d')` 守卫

### 问题6：AnchorStateMachine 轮询效率低

**分析**：
- `AnchorStateMachine` 的 8 步轮询周期中：4 步 GET_ACTIVE、1 步 GET_IDS、1 步 GET_DATA、2 步冗余 GET_ACTIVE
- 实际 anchor 数据更新周期为 8 秒（8 × 1s 定时器间隔）
- 这是 cflib 层面的设计，不在本次修改范围内

## 最终修改清单

| 修改 | 位置 | 说明 |
|------|------|------|
| `FPS 2→5` | `FPS` 常量 | QLabel 矩阵刷新更灵敏 |
| 状态变量提前初始化 | `__init__` | `_anchors`/`_indicator_state`/`_last_pose`/`_is_connected` 在 `_clear_state()` 前初始化 |
| `_plot_timer` 独立 3D 定时器 | `__init__` | 1Hz，与 UI 刷新（5Hz）解耦 |
| 位置标签解耦 | `_update_graphics()` | `_is_connected` 替代 `is_loco_deck_active` 作为守卫条件 |
| QLabel 指示灯定时刷新 | `_update_graphics()` | 加入 `_update_ranging_status_indicators()` 到 5Hz 回调 |
| 3D 仅更新 CF 标记 | `_update_3d_plot()` | 调用 `update_cf_position()` 而非 `update_data()` |
| `update_cf_position()` 新增 | `Plot3dLps` | 仅更新无人机位置，不触碰 anchor visual |
| 姿态变化阈值 5cm² | `_update_3d_plot()` | 过滤传感器噪声，静止时不触发 GPU 上传 |
| Anchor 按需更新 | `_anchor_data_updated()` | 仅在 anchor 数量变化时触发完整 3D 渲染 |
| QLabel 缓存失效 | `_update_ranging_status_indicators()` | anchor ID 集合变化时清空 `_indicator_state` |
| `_is_connected` 守卫 | `_update_graphics()` / `_update_3d_plot()` | 忽略断开连接后的残留信号 |
| `_clear_anchors` 守卫 | `_clear_anchors()` | `hasattr(self, '_plot_3d')` 防止 `__init__` 早期访问 |
| `_indicator_state.clear()` | `_clear_state()` | 重置样式缓存 |
| `_last_pose = None` | `_clear_state()` | 重置姿态缓存 |
| `_remove_loco_param_callbacks()` 新增 | `_disconnected()` | 移除连接时注册的参数回调，防止回调累积 |
