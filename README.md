# -cm1-

本仓库记录了使用 **CM1（Cloud Model 1）** 进行双台风数值模拟的全流程配置与后处理可视化代码，涵盖从零开始的模式配置、背景场设置、初始台风涡旋定义、MPI 并行运行，以及输出结果的 Python 可视化分析。

---

## 仓库结构

```
-cm1-/
├── cm1配置/
│   ├── namelist.input        # CM1 主要运行参数配置文件
│   └── init3d.F              # 三维初始条件配置（Fortran 源码，含台风涡旋定义）
└── 可视化code/
    ├── intensity_visual_1tc.py   # 台风强度时间序列可视化（最低气压 & 最大风速）
    └── theta_z_t.py              # 中心点位温垂直廓线随时间演变的可视化
```

---

## 配置流程

### 1. `namelist.input` 参数配置

CM1 核心运行参数，关键设置包括：

| 参数 | 值 | 说明 |
|------|----|------|
| `nx / ny / nz` | 1200 / 1200 / 59 | 网格点数 |
| `dx / dy / dz` | 4000 / 4000 / 500 m | 网格分辨率 |
| `dtl` | 10 s | 时间步长 |
| `timax` | 432000 s（≈120 h） | 积分总时长 |
| `imoist` | 1 | 启用湿物理 |
| `ipbl` | 2 | PBL 参数化方案 |
| `sgsmodel` | 1 | SGS 湍流方案 |
| `isnd` | **7** | 从外部文件读取背景场探空（必须） |
| `iinit` | 7 | 初始台风涡旋设置方式 |

> 部分参数附有 `!change` 注释，表示针对双台风模拟做出的修改。

---

### 2. 背景场探空配置（`input_sounding`）

> **必须设置 `isnd = 7`**，CM1 将从外部文本文件 `input_sounding` 读取背景大气廓线。

**文件格式说明：**

- **第一行（文件头）：**
  ```
  sfc_pres(mb)    sfc_theta(K)    sfc_qv(g/kg)
  ```
  表示近地面（约 2 m AGL）的气压、位温和混合比。

- **后续各行：**
  ```
  z(m)    theta(K)    qv(g/kg)    u(m/s)    v(m/s)
  ```

- **注意事项：**
  - 层数任意，但**最后一行的高度 `z` 必须大于模式顶高度**
    - 当 `stretch_z=0` 时，模式顶 = `nz × dz`
    - 当 `stretch_z=1` 时，模式顶 = `ztop`
  - 设置 `isnd=7` 时，`iwnd` 参数将被忽略

---

### 3. 初始台风涡旋配置（`init3d.F`）

在 `init3d.F` 中，通过搜索 `tctype=` 可以找到台风涡旋参数定义区域，支持自定义台风初始结构（如涡旋半径、强度等）。
目前已经实现**双台风**的初始化。

---

### 4. 小技巧

- 可在 `namelist.input` 中通过注释标记 `!change` 快速定位本次模拟修改的参数。
- 建议为每次模拟保留一份 `namelist.input` 和 `input_sounding` 的备份。

---

## 编译与运行

### 5. 加入 MPI 并行环境

使用 MPI 加速运算时，需先激活相应的编译环境（如加载 MPI 模块），然后按以下步骤编译：

```bash
# 进入源码目录
cd src/

# 清理旧的编译文件
make clean

# 重新编译
make
```

编译完成后，进入运行目录并提交作业：

```bash
cd run/

# 使用 128 个进程运行 CM1，输出日志重定向到 output.log
mpirun -np 128 ./cm1.exe > output.log 2>&1 &
```

---

## 后处理与可视化

### 6. Python 环境与可视化代码

**依赖环境：**

```bash
Python >= 3.8
numpy
xarray
matplotlib
```

**脚本说明：**

- **`intensity_visual_1tc.py`**：逐文件读取 CM1 输出的 NetCDF（`cm1out_*.nc`），提取全域最低地面气压（`psfc`）和最大近地面风速，绘制台风强度演变时间序列图。

- **`theta_z_t.py`**：读取中心网格点的位温（`th`）垂直廓线，生成位温随高度（z）和时间（t）变化的二维填色图。

> 使用前请根据实际情况修改脚本中的 `data_dir` 路径变量。

---

## 文件管理

### 7. 文件迁移

如需将所有运行文件转移到其他目录或机器，建议使用 `rsync` 或 `scp`：

```bash
rsync -avz run/ user@remote:/path/to/dest/
```

### 8. 清理输出文件

运行结束后，可清理日志和 NetCDF 输出文件：

```bash
# 清空日志文件（保留文件本身）
> output.log

# 将所有 NetCDF 输出移动到指定目录
mv *.nc /path/to/archive/
```

---

## 参考资料

- [CM1 官方网站](http://www2.mmm.ucar.edu/people/bryan/cm1/)
- [CM1 控制方程文档](http://www2.mmm.ucar.edu/people/bryan/cm1/cm1_equations.pdf)
