#!/usr/bin/env python
# coding: utf-8

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def format_time_value(time_value):
	"""Return numeric time in hours when possible."""
	try:
		value = np.asarray(time_value)
		if np.issubdtype(value.dtype, np.timedelta64):
			hours = value / np.timedelta64(1, 'h')
			return float(hours)
		if np.issubdtype(value.dtype, np.datetime64):
			return value
		return float(value) / 3600.0
	except Exception:
		try:
			return format_time_value(time_value.item())
		except Exception:
			return np.nan


def collect_intensity(file_paths, level_idx=0):
	"""Collect global minimum surface pressure and global maximum wind speed."""
	times = []
	min_psfc = []
	max_wind = []

	for file_path in file_paths:
		ds = xr.open_dataset(file_path)
		try:
			x = ds['xh'].values
			y = ds['yh'].values

			time_value = ds['time'].isel(time=0).values
			times.append(format_time_value(time_value))

			if 'psfc' not in ds.variables:
				raise ValueError("Dataset has no 'psfc' variable.")
			psfc = ds['psfc'].isel(time=0).values

			min_psfc.append(np.nanmin(psfc))

			if len(ds['u'].dims) == 4:
				u_data = ds['u'].isel(time=0, zh=level_idx).values
				v_data = ds['v'].isel(time=0, zh=level_idx).values
				if u_data.shape[1] == x.size + 1:
					u = 0.5 * (u_data[:, :-1] + u_data[:, 1:])
				else:
					u = u_data
				if v_data.shape[0] == y.size + 1:
					v = 0.5 * (v_data[:-1, :] + v_data[1:, :])
				else:
					v = v_data
			elif len(ds['u'].dims) == 3:
				u = ds['u'].isel(time=0, zh=level_idx).values
				v = ds['v'].isel(time=0, zh=level_idx).values
			else:
				u = ds['u'].isel(time=0).values
				v = ds['v'].isel(time=0).values

			min_y = min(u.shape[0], v.shape[0])
			min_x = min(u.shape[1], v.shape[1])
			u = u[:min_y, :min_x]
			v = v[:min_y, :min_x]
			speed = np.sqrt(u**2 + v**2)

			max_wind.append(np.nanmax(speed))
		finally:
			ds.close()

	return {
		"time": np.asarray(times),
		"min_psfc": np.asarray(min_psfc),
		"max_wind": np.asarray(max_wind),
	}


def plot_intensity(time_values, min_psfc, max_wind, output_dir):
	"""Plot global intensity time series and save figures."""
	output_dir = Path(output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)

	fig1, ax1 = plt.subplots(figsize=(10, 6))
	ax1.plot(time_values, min_psfc, label='Global min psfc', color='tab:blue')
	ax1.set_title('Global Minimum Surface Pressure vs Time')
	ax1.set_xlabel('Time (h)')
	ax1.set_ylabel('Minimum psfc (Pa)')
	ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
	ax1.legend()
	fig1.tight_layout()
	fig1.savefig(output_dir / 'min_psfc_time_series.png', dpi=300)
	plt.close(fig1)

	fig2, ax2 = plt.subplots(figsize=(10, 6))
	ax2.plot(time_values, max_wind, label='Global max wind', color='tab:red')
	ax2.set_title('Global Maximum Wind Speed vs Time')
	ax2.set_xlabel('Time (h)')
	ax2.set_ylabel('Maximum wind speed (m/s)')
	ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
	ax2.legend()
	fig2.tight_layout()
	fig2.savefig(output_dir / 'max_wind_time_series.png', dpi=300)
	plt.close(fig2)



def main():
	data_dir = Path(rf"/data1/home/qiuzy/cm1/cm1r21.1/run")
	nc_files = sorted(data_dir.glob("cm1out_[0-9]*.nc"))
	file_count = len(nc_files)
	if file_count == 0:
		raise FileNotFoundError(f"No NetCDF files found in {data_dir}")

	file_path_lst = []
	for i in range(file_count):
		file_path_lst.append(str(nc_files[i]))
	data = collect_intensity(file_path_lst, level_idx=0)
	plot_intensity(
		data["time"],
		data["min_psfc"],
		data["max_wind"],
		output_dir=r"/data1/home/qiuzy/code/2026/output/intensity_visualization/1tc",
	)

if __name__ == "__main__":
	main()
