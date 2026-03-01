本教程涵盖了从服务器底层环境配置到修改源码实现双台风模拟的全过程。

---

## 一、 环境前期准备

在编译 CM1 之前，必须确保服务器具备高效的编译器和并行计算环境。

### 1. 编译器安装与更新
CM1 对 Fortran 编译器有一定要求，建议安装较新版本的 `gfortran`。
*   **更新系统包**：使用 `dnf` 或 `yum` 更新系统。
*   **安装 gfortran 15**：确保编译器支持最新的 Fortran 规范。
    ```bash
    # 示例命令（根据系统环境调整）
    sudo dnf install gcc-gfortran 
    gfortran --version  # 检查是否为15版本
    ```

### 2. 并行计算环境 (MPI) 配置
单核运行 CM1 速度极慢，必须配置 MPI 跨线程加速。
*   **设置环境变量**：将 `mpif90` 和 `mpirun` 的路径添加到 `~/.bashrc` 中。
    ```bash
    # 编辑 .bashrc
    vi ~/.bashrc
    # 在末尾添加（路径需根据实际安装位置修改）
    export PATH=/usr/local/mpi/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/mpi/lib:$LD_LIBRARY_PATH
    # 生效配置
    source ~/.bashrc
    ```

### 3. 辅助工具安装
*   **tmux**：强烈建议安装 `tmux`。它可以保证在远程连接断开时，模拟任务依然在后台运行。
    ```bash
    sudo dnf install tmux
    tmux new -s cm1_run  # 创建新会话
    ```

---

## 二、 模式源码配置与修改

### 1. 修改 Makefile
进入 `src/` 目录，修改 `Makefile` 以适配编译器和并行环境。
*   **指定编译器**：将 `FC` 指向 `mpif90`。
*   **开启 MPI 选项**：确保 `OPTS` 中包含 `-DMPI` 宏定义，以便启用并行逻辑。

### 2. 修改 `init3d.F` (实现双台风关键)
若要实现双台风模拟，需修改初始化模块。
*   **引入循环**：在 `iinit=7` 部分引入 `do ntc = 1, 2`。
*   **叠加逻辑**：
    *   **扰动场**：使用累加方式（如 `tha = tha + ...`）而非直接赋值。
    *   **水汽场**：需减去背景场再叠加 `qa = qa + (qv_interpolated - qv0)`，防止背景湿度重复。
    *   **矢量合成**：基于各中心方位角计算 $u, v$ 后进行矢量叠加。

### 3. 配置 `input_sounding` (环境场)
*   **设置 `isnd=7`**：在 `namelist.input` 中指定从外部读取探空。
*   **文件格式**：首行为地面气压、位温和水汽；后续行为高度、位温、水汽及 $u/v$ 风速。(具体见`base.F`)
*   **注意**：最后一行高度必须大于模拟区域顶部高度。

---

## 三、 实验参数设置 (`namelist.input`)

### 1. 拉伸网格设计 (Stretched Grid)
为了节省算力并保证分辨率，采用拉伸网格。
*   **内层**：2km 分辨率（例如内层点数 900，长度 2700 km）。
*   **外层**：逐渐拉伸至 27km（外层点数 300，长度 4500 km）。
*   **设置**：在 `namelist.input` 中配置 `stretch_x=1` 及相关参数。
* 具体的参数要求见`README.stretch`

### 2. 台风参数
在 `init3d.F` 对应的参数区设置：
*   `vmax_re87`：最大切向风速（如 30 m/s）。
*   `rmax_re87`：最大风速半径（如 60 km）。
*   `dist`：两个台风中心之间的物理距离（如 900 km）。

---

## 四、 编译与运行流程

### 1. 编译
每次修改源码（如 `init3d.F`）或 `Makefile` 后，必须重新编译。
```bash
cd src/
make clean    # 清理旧的编译文件（非常重要）
make          # 开始编译，成功后会在 run/ 目录下生成 cm1.exe
```

### 2. 准备运行环境
进入 `run/` 目录，确保存在以下文件：
*   `cm1.exe`（编译生成）
*   `namelist.input`（参数配置）
*   `input_sounding`（背景场）

### 3. 执行模拟
利用 MPI 进行多核并行运算：
```bash
# 示例：使用 128 个核心运行，并将日志输出到 output.log
mpirun -np 128 ./cm1.exe > output.log 2>&1 &
```

### 4. 任务管理
*   **查看进度**：`tail -f output.log`
*   **清理垃圾文件**：
    ```bash
    > output.log   # 清空日志
    rm *.nc        # 删除旧的结果文件
    ```

---

