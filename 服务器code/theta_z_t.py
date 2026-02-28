from pathlib import Path
import re
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

# =========================
# 1) 文件列表
# =========================
data_dir = Path(rf"/data1/home/qiuzy/cm1/cm1r21.1/run")
nc_files = sorted(data_dir.glob("cm1out_[0-9]*.nc"))
if len(nc_files) == 0:
    raise FileNotFoundError(f"No NetCDF files found in {data_dir}")

# =========================
# 2) 逐文件读取中心点
#    th(time=1, zh=59, yh=600, xh=600)
#    psfc(time=1, yh=600, xh=600)
# =========================
theta_profiles = []   # 每时次中心点 th(z)
psfc_center_pa = []   # 每时次中心点 psfc(Pa)
time_h = []           # 小时
z_km = None

def file_index_hours(fp: Path):
    """如果时间变量不可用，则从文件名提取序号作为时间轴。"""
    m = re.search(r"cm1out_(\d+)\.nc$", fp.name)
    return float(m.group(1)) if m else np.nan

for f in nc_files:
    ds = xr.open_dataset(f)

    # 中心网格点索引
    ny = ds.dims["yh"]
    nx = ds.dims["xh"]
    iy = ny // 2
    ix = nx // 2

    # 高度坐标（km）
    if z_km is None:
        z_km = ds["zh"].values.astype(float)   # CM1常见为 m
        #z_km = z_m / 1000.0

    # 中心点 th 垂直廓线: (zh,)
    th_prof = ds["th"].isel(time=0, yh=iy, xh=ix).values.astype(float)
    theta_profiles.append(th_prof)

    # 中心点 psfc: 标量(Pa)
    p0 = float(ds["psfc"].isel(time=0, yh=iy, xh=ix).values)
    psfc_center_pa.append(p0)

    # 时间（优先读取 time 变量；否则用文件序号）
    if "time" in ds:
        tval = ds["time"].values
        tval = np.asarray(tval).squeeze()
        t_dtype = np.asarray(tval).dtype
        if np.issubdtype(t_dtype, np.datetime64):
            # 先存 datetime，后面统一转相对小时
            time_h.append(tval)
        elif np.issubdtype(t_dtype, np.timedelta64):
            # 直接转小时（相对时间）
            time_h.append(float(tval / np.timedelta64(1, "h")))
        else:
            time_h.append(float(tval))
    else:
        time_h.append(file_index_hours(f))

    ds.close()

theta_tz = np.vstack(theta_profiles)          # (nt, nz)
psfc_center_pa = np.array(psfc_center_pa)     # (nt,)
time_h = np.array(time_h)

# 时间统一为相对小时
if np.issubdtype(time_h.dtype, np.datetime64):
    time_h = (time_h - time_h[0]) / np.timedelta64(1, "h")
elif np.issubdtype(time_h.dtype, np.timedelta64):
    time_h = time_h / np.timedelta64(1, "h")
else:
    # 若time本身不是小时，可按需要自行换算
    time_h = time_h.astype(float)
    # 如果文件号从1开始，且你想从0开始，可取消下一行注释
    # time_h = time_h - time_h[0]

# 压力变化（相对初始时刻），单位 hPa
dp_hpa = (psfc_center_pa - psfc_center_pa[0]) / 100.0

# 按时间排序（防止文件顺序导致乱序）
order = np.argsort(time_h)
time_h = time_h[order]
theta_tz = theta_tz[order, :]
dp_hpa = dp_hpa[order]

# 位温异常：当前时刻 - 上一时刻
dtheta_tz = np.full_like(theta_tz, np.nan, dtype=float)
dtheta_tz[1:, :] = theta_tz[1:, :] - theta_tz[:-1, :]

# =========================
# 3) 可视化
# =========================
fig, ax = plt.subplots(figsize=(11, 6), dpi=120)

# 用异常场作图（建议用发散色标）
vmax = np.nanpercentile(np.abs(dtheta_tz[1:, :]), 98)
cf = ax.contourf(
    time_h, z_km, dtheta_tz.T,
    levels=np.linspace(-vmax, vmax, 25),
    cmap="RdBu_r", extend="both"
)
cbar = fig.colorbar(cf, ax=ax, pad=0.02)
cbar.set_label("Potential Temperature Anomaly Δθ (K, t - t-1)")

ax.set_xlabel("Time (h)")
ax.set_ylabel("Height (km)")

ax2 = ax.twinx()
ax2.plot(time_h, dp_hpa, color="tab:blue", linewidth=2.2)
ax2.set_ylabel("Pressure Change Δp (hPa)", color="tab:blue")
ax2.tick_params(axis="y", labelcolor="tab:blue")

ax.set_title("Center-point Δθ (t - t-1) and Surface Pressure Change")

plt.tight_layout()

# 保存图片
out_dir = Path(r"/data1/home/qiuzy/code/2026/output/theta_t_z")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "theta_dp_center_timeheight.png"
fig.savefig(out_file, dpi=300, bbox_inches="tight")
print(f"Figure saved to: {out_file}")

plt.show()