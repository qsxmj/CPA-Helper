# 账号状态页表格列显隐控制改造说明

## 1. 背景与用户需求

用户要求对 `账号状态 -> 账号列表` 页面中的两个账号表格增加“表格内列类目是否显示”的控制能力。

涉及两个表格：

1. **已禁用账号**表格
2. **正常账号**表格

用户明确说明：这里需要的不是继续增加数据筛选条件，而是能够控制表格内部各列是否显示，也就是列类目的显隐控制。

## 2. 本次实际改动

修改文件：

- `frontend/src/features/codex-keeper/views/CodexKeeperStatusView.vue`

### 2.1 新增列类目类型定义

新增 `AccountColumnKey` 类型，用于限定可以被用户控制显示/隐藏的业务列：

```ts
type AccountColumnKey =
  | 'name'
  | 'email'
  | 'account_type'
  | 'disabled'
  | 'priority'
  | 'quota'
  | 'last_checked_at'
  | 'latest_action'
  | 'free_weekly_reset'
```

### 2.2 新增列选项配置

新增普通账号表格列选项：

- 账号：`name`
- 邮箱：`email`
- 类型：`account_type`
- 状态：`disabled`
- 优先级：`priority`
- 额度窗口：`quota`
- 最近巡检：`last_checked_at`
- 最近操作：`latest_action`

新增已禁用账号表格列选项，在普通列基础上额外包含：

- free周刷新：`free_weekly_reset`

### 2.3 新增两个表格各自的列显隐状态

新增状态：

```ts
const visibleDisabledColumnKeys = ref<AccountColumnKey[]>([...defaultDisabledColumnKeys])
const visibleNormalColumnKeys = ref<AccountColumnKey[]>([...defaultAccountColumnKeys])
```

作用：

- `visibleDisabledColumnKeys` 控制“已禁用账号”表格显示哪些业务列。
- `visibleNormalColumnKeys` 控制“正常账号”表格显示哪些业务列。

### 2.4 表格列计算逻辑改造

原先表格列基本是固定输出，现在改为：

1. 先生成基础业务列 `baseColumns`
2. 再根据当前表格的 `visible...ColumnKeys` 过滤业务列
3. 最后保留必要的固定列

保留原则：

- 业务列可以被用户隐藏。
- 表格选择列 `selection` 必须保留。
- 操作列 `actions` 必须保留。

这样避免用户把选择列或操作列隐藏后无法继续执行批量操作、详情、启用、禁用、删除等关键功能。

### 2.5 已禁用账号表格新增“显示列类目”控件

在“已禁用账号”表格顶部筛选/操作区域新增 `NSelect multiple` 控件：

```vue
<NSelect
  v-model:value="visibleDisabledColumnKeys"
  :options="disabledColumnOptions"
  multiple
  size="small"
  placeholder="显示列类目"
  class="account-column-select"
/>
```

可控制显示/隐藏：

- 账号
- 邮箱
- 类型
- 状态
- 优先级
- 额度窗口
- 最近巡检
- 最近操作
- free周刷新

### 2.6 正常账号表格新增“显示列类目”控件

在“正常账号”表格顶部筛选/操作区域新增 `NSelect multiple` 控件：

```vue
<NSelect
  v-model:value="visibleNormalColumnKeys"
  :options="accountColumnOptions"
  multiple
  size="small"
  placeholder="显示列类目"
  class="account-column-select"
/>
```

可控制显示/隐藏：

- 账号
- 邮箱
- 类型
- 状态
- 优先级
- 额度窗口
- 最近巡检
- 最近操作

### 2.7 样式调整

新增或调整了以下样式类：

- `.account-section-controls`
- `.account-section-filter-row`
- `.account-column-select`

作用：

- 将“类型筛选 / 优先级筛选 / 显示列类目”放在同一筛选行中。
- 保持表格顶部筛选项和批量操作按钮布局清晰。
- 避免多选列控件过宽或布局挤压。

## 3. 发现的问题

### 3.1 项目最开始 Docker 部署端口不可访问

项目最开始部署时遇到两个现象：

1. Docker 提示：

```text
Published ports are discarded when using host network mode
```

2. 浏览器访问失败：

```text
http://127.0.0.1:18317/
```

无法打开 CPA Helper 页面。

#### 原因

当 Docker Compose 服务使用 `network_mode: host` 时，Docker 会直接使用宿主机网络命名空间，此时 `ports:` 端口映射配置会被忽略。

也就是说，如果 compose 中同时存在类似配置：

```yaml
network_mode: host
ports:
  - "18317:18317"
```

Docker 会提示端口发布被丢弃，因为 host 网络模式下不再通过 `ports` 做端口转发。

在该项目场景中，期望通过：

```text
127.0.0.1:18317
```

访问容器内服务，因此继续保留 `network_mode: host` 会导致部署行为和预期端口映射不一致。

#### 修复方法

将 `docker-compose.yml` 调整为普通 bridge 网络端口映射方式：

```yaml
services:
  cpa-helper:
    build: .
    image: cpa-helper:local
    container_name: cpa-helper
    restart: always
    environment:
      - TZ=Asia/Shanghai
    ports:
      - "18317:18317"
    volumes:
      - ./data:/app/data
```

关键点：

- 移除 `network_mode: host`。
- 保留 `ports: - "18317:18317"`。
- 让 Docker 正常把宿主机 `18317` 端口映射到容器 `18317` 端口。

#### 验证结果

修复后重新部署：

```bash
docker compose up -d --build cpa-helper
```

再验证：

```text
http://127.0.0.1:18317/
```

返回 HTTP 200，页面可以打开。

当前 `docker-compose.yml` 已是修复后的形式，不再包含 `network_mode: host`。

### 3.2 用户真实需求容易被误解为“数据筛选”

最初页面已有“类型”“优先级”等筛选项，用户再次提出“增加筛选显示，和调整表格内显示，位置的筛选项”时，容易理解成继续增加数据过滤条件。

后续用户明确说明：

> 意思是我需要控制表格内的列类目，是否显示

因此最终确认需求为：**列显隐控制**，不是账号数据过滤。

修复方法：

- 不再改 `filteredDisabledAccounts` / `filteredNormalAccounts` 的过滤规则。
- 改造 `disabledColumns` / `normalColumns` 的列生成逻辑。
- 通过多选控件动态控制列数组。

### 3.3 TypeScript 构建发现列 key 类型不匹配

实现列过滤时，直接从 Naive UI 的表格列对象中读取 `column.key` 参与判断，会遇到类型不够精确的问题。

原因：

- Naive UI DataTable 的列定义类型中，`key` 可能不是严格的 `AccountColumnKey`。
- 直接传入 `visibleColumnKeys.includes(column.key)` 会触发 TypeScript 类型错误。

修复方法：

- 增加显式的 key 提取与类型判断逻辑。
- 仅当列 key 属于允许的 `AccountColumnKey` 时才参与业务列显隐过滤。
- 选择列和操作列不参与过滤，固定保留。

验证：

- 修改后执行 `npm run build`，构建通过。

### 3.4 浏览器页面 initially 仍加载旧前端资源

本地 `npm run build` 通过后，浏览器页面第一次检查时没有看到新增的“显示列类目”控件。

发现现象：

- 页面脚本仍是旧构建资源。
- 容器 `cpa-helper` 还在运行旧镜像。
- 前端代码虽然已构建，但 Docker 服务没有重新构建并部署。

修复方法：

执行：

```bash
docker compose up -d --build cpa-helper
```

结果：

- 镜像 `cpa-helper:local` 重新构建。
- 容器 `cpa-helper` 重新创建并启动。
- `http://127.0.0.1:18317/` 返回 HTTP 200。

### 3.5 UI 下拉测试时首次点击未展开选项

在浏览器自动化验证中，第一次点击 `NSelect` 外层元素后未立刻获取到下拉选项。

原因：

- Naive UI 的 `NSelect` 下拉层不是简单挂在原控件内部。
- 需要点击更精确的内部选择区域，或等待弹层渲染。

修复/验证方法：

- 改为点击 `.n-base-selection-tags` / `.n-base-selection` 这类内部可交互节点。
- 再从全局 DOM 查询 `.n-base-select-option`。
- 成功点击“邮箱”选项后验证表头变化。

## 4. 修复后的验证结果

### 4.1 构建验证

在前端目录执行：

```bash
npm run build
```

结果：

- `vue-tsc -b` 通过。
- `vite build` 通过。
- 前端生产构建成功。

### 4.2 Docker 部署验证

在项目根目录执行：

```bash
docker compose up -d --build cpa-helper
```

结果：

- `cpa-helper:local` 镜像构建成功。
- `cpa-helper` 容器启动成功。
- 访问 `http://127.0.0.1:18317/` 返回 `200`。

### 4.3 页面 DOM 验证

页面地址：

```text
http://127.0.0.1:18317/admin/account-status
```

验证结果：

- “已禁用账号”表格出现第三个选择控件：`显示列类目`。
- “正常账号”表格出现第三个选择控件：`显示列类目`。
- 已禁用账号表格表头包含：
  - 账号
  - 邮箱
  - 类型
  - 状态
  - 优先级
  - 额度窗口
  - 最近巡检
  - 最近操作
  - free周刷新
- 正常账号表格表头包含：
  - 账号
  - 邮箱
  - 类型
  - 状态
  - 优先级
  - 额度窗口
  - 最近巡检
  - 最近操作

### 4.4 列隐藏实测

实测操作：

1. 打开“已禁用账号”表格的“显示列类目”多选控件。
2. 取消选择“邮箱”。
3. 检查表头列 key。

取消前表头包含：

```text
name, email, account_type, disabled, priority, quota, last_checked_at, latest_action, free_weekly_reset
```

取消后表头变为：

```text
name, account_type, disabled, priority, quota, last_checked_at, latest_action, free_weekly_reset
```

结论：

- `email` 列已从表格中隐藏。
- 列显隐控制生效。
- 选择列和操作列仍保留。

## 5. 当前功能效果

现在账号状态页两个账号表格均支持：

- 按账号类型筛选。
- 按优先级筛选。
- 控制表格内业务列是否显示。
- 保留批量操作能力。
- 保留单行操作能力。

其中“已禁用账号”表格额外支持显示/隐藏：

- `free周刷新`

该列用于查看 free 账号周限额刷新时间。

## 6. 后续可选优化

当前列显隐状态是页面内存状态，刷新页面后会恢复默认显示所有业务列。

如果后续需要增强体验，可以继续增加：

1. 将列显隐配置保存到 `localStorage`。
2. 为“已禁用账号”和“正常账号”分别记忆用户上次选择。
3. 增加“一键恢复默认列”按钮。
4. 增加“全选/清空”辅助操作。
5. 根据列显隐结果动态计算 `scroll-x`，减少横向空白。
