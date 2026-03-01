# -cm1-

本仓库记录了使用 **CM1（Cloud Model 1）** 进行双台风数值模拟的相关配置和后处理可视化代码，主要面向 CM1 从零开始配置、参数调整及结果分析。

---

## 仓库结构

```
-cm1-/
├── cm1配置/
│   ├── namelist.input    # CM1 主要运行参数配置文件
│   └── init3d.F          # 三维初始条件配置（Fortran 源码）
└── 可视化code/
    ├── intensity_visual_1tc.py   # 台风强度时间序列可视化（最低气压 & 最大风速）
    └── theta_z_t.py              # 中心点位温垂直廓线随时间演变的可视化
```

---

## 模块介绍

### `cm1配置/`

包含针对双台风模拟的 CM1 模式配置文件：

- **`namelist.input`**：CM1 核心参数配置，包括：
  - 网格设置：`nx=1200, ny=1200, nz=59`，水平分辨率 `dx=dy=4000 m`，垂直分辨率 `dz=500 m`
  - 时间步长：`dtl=10 s`，积分时长：`timax=360000 s`（约 100 小时）
  - 物理参数化方案：启用湿物理（`imoist=1`）、PBL 方案（`ipbl=2`）、SGS 湍流（`sgsmodel=1`）
  - 边界条件、辐射阻尼、科里奥利力等关键参数均有标注，部分参数附有修改说明（`!change`）

- **`init3d.F`**：CM1 三维初始场设置的 Fortran 模块，基于基本态叠加扰动的方式设置初始条件。

### `可视化code/`

基于 Python（`xarray`, `numpy`, `matplotlib`）的后处理与可视化脚本：

- **`intensity_visual_1tc.py`**：读取 CM1 输出的 NetCDF 文件，提取全域最低地面气压（`psfc`）和最大风速，绘制台风强度时间序列图。

- **`theta_z_t.py`**：逐时次读取 CM1 输出文件，提取模拟区域中心点的位温（`th`）垂直廓线，生成位温随高度和时间变化的二维图。

---

## 环境依赖

```bash
Python >= 3.8
numpy
xarray
matplotlib
```

---

## 数据说明

CM1 输出文件为 NetCDF 格式（`cm1out_*.nc`），默认读取路径见各脚本中的 `data_dir` 变量，使用前请根据实际路径修改。

---

## 参考资料

- [CM1 官方网站](http://www2.mmm.ucar.edu/people/bryan/cm1/)
- [CM1 控制方程文档](http://www2.mmm.ucar.edu/people/bryan/cm1/cm1_equations.pdf)