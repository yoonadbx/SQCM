from matplotlib.pyplot import (figure, plot, xlabel, ylabel, title, xlim, ylim, yscale, xscale, legend, text, \
                               pcolormesh, colorbar, axhline, axvline, tick_params)
from numpy import polyfit, poly1d, average, unique, shape, reshape
from numpy import linspace, max
import numpy as np


def generate_label(tup):
    label = ""
    for parameter in tup:
        label += " %s " % parameter.label
    return label


def generate_text(station, tup1=None, tup2=None):
    text = ''
    para_dict = station.components.copy()
    try:
        if tup1:
            for parameter in tup1:
                del para_dict[parameter.name]
        if tup2:
            for parameter in tup2:
                del para_dict[parameter.name]
    except:
        pass

    for parameter in para_dict.values():
        # del para of 0
        try:
            if parameter.settable:
                value = average(parameter())
                if value == 0 or value == -1e-6:
                    continue
                unit = parameter.unit
                text += parameter.name + " = " + "%.4g " % value + unit + "\n"
        except:
            pass
    return text


def generate_notes(project, run_id, start_time, end_time, para_meas=None, para_scan_x=None, para_scan_y=None,
                   memsize=None, sr=None, repeat=None):
    subtitle = f"id:{run_id} " + project.data_path + "\n" + start_time + " --- " + end_time + "\n" + f"sample: {project.sample_name}, T={project.temperature}, tester: {project.tester}"
    text = generate_text(project.station, para_scan_x, para_scan_y)

    notes = {"text": text, "subtitle": subtitle, "comment": ""}

    if para_scan_x:
        exec(f"notes['label_x'] =  generate_label(para_scan_x)")
        exec(f"notes['label_x_unit'] = para_scan_x[0].unit")

        if para_meas:
            exec(f"notes['label_z'] = para_meas[0].label")
            exec(f"notes['label_z_unit'] = para_meas[0].unit")

        if para_scan_y:
            exec(f"notes['label_y'] =  generate_label(para_scan_y)")
            exec(f"notes['label_y_unit'] = para_scan_y[0].unit")

    if memsize:
        notes["memsize"] = memsize
    if sr:
        notes["sr"] = sr
    if repeat:
        notes["repeat"] = repeat

    return notes


def fit_1d(x, y, notes=None):
    p = polyfit(x[:], y[:], 1)
    z = poly1d(p)
    plot(x[:], z(x)[:])

    if notes:
        if notes['label_x_unit'] == "V" and notes['label_z_unit'] == "A":
            R = 1 / p[0] / 1.0e3
        elif notes['label_x_unit'] == "A" and notes['label_z_unit'] == "V":
            R = p[0] / 1.0e3
        R = "%.6g k" % R

    else:
        R = p[0]
        R = "%.6g" % R
    return R


def plot_1d(x, y, marker=".", fit=True, notes=None, label_x=None, label_y=None, tit=None):
    figure(figsize=(5, 4.5))
    plot(x[:], y[:], marker)

    if label_x:
        xlabel(label_x, fontsize=12)
    elif notes:
        xlabel(f"{notes['label_x']} ({notes['label_x_unit']})", fontsize=12)

    if label_y:
        ylabel(label_y, fontsize=12)
    elif notes:
        ylabel(f"{notes[f'label_z']} ({notes[f'label_z_unit']})", fontsize=12)

    if tit:
        tit = tit
    elif notes:
        tit = f"{notes['subtitle']}\n{notes['comment']}"
    else:
        tit = ""
    if fit:
        R = fit_1d(x, y, notes)
        tit = tit + "\n" + f"R={R}"
    title(tit)

    tick_params(labelsize=12)


def plot_2d(x, y, z, marker=None, notes=None, label_x=None, label_z=None, tit=None, legend_state=True,
            loc=None, visible=True, alpha=0.5):
    figure(figsize=(5, 4.5))

    for i in range(len(y)):
        plot(x[:], z[i, :], marker=marker, label=f'{notes["label_y"]} = %.4g{notes["label_y_unit"]}' % (y[i]))

        if label_x:
            label_x = label_x
        elif notes:
            label_x = f"{notes['label_x']} ({notes['label_x_unit']})"
        xlabel(label_x, fontsize=12)

        if label_z:
            label_z = label_z
        elif notes:
            label_z = f"{notes['label_z']} ({notes['label_z_unit']})"
        ylabel(label_z, fontsize=12)

        if tit:
            tit = tit
        elif notes:
            tit = f"{notes['subtitle']}\n{notes['comment']}"
        title(tit)

        if legend_state:
            legend(loc=loc)

        if notes:
            if notes["text"]:
                text(min(x), max(z), notes["text"], fontsize=11, style="italic", alpha=alpha,
                     horizontalalignment="left", verticalalignment="top", visible=visible)

    tick_params(labelsize=12)


def plot_3d(x, y, z, notes, label_x=None, label_y=None, label_z=None, tit=None, vmax=None, vmin=None, cmap=None,
            visible=True, alpha=0.5, scale_x="linear", scale_y="linear", figsize=(6, 4.5), lim_x=None, lim_y=None,
            a=None, b=None, c=None, d=None, ):
    if len(unique(y)) == 1:
        label_y = "Repeat times"
        y = range(len(y))

    figure(figsize=figsize)
    imag = pcolormesh(x, y, z, vmax=vmax, vmin=vmin, cmap=cmap)
    cbar = colorbar(imag)
    font = {'size': 12, }  # 设置colorbar的标签字体及其大小

    if label_x:
        xlabel(label_x, fontsize=12)
    elif notes:
        xlabel(f"{notes['label_x']} ({notes['label_x_unit']})", fontsize=12)

    if label_y:
        ylabel(label_y, fontsize=12)
    elif notes:
        ylabel(f"{notes[f'label_y']} ({notes[f'label_y_unit']})", fontsize=12)

    if label_z:
        cbar.set_label(f"{label_z}", fontdict=font)
    elif notes:
        cbar.set_label(f"{notes[f'label_z']} ({notes[f'label_z_unit']})", fontdict=font)

    if tit:
        tit = tit
    elif notes:
        tit = f"{notes['subtitle']}\n{notes['comment']}"
    title(tit)

    text(min(x), max(y), notes["text"], fontsize=11, style="italic", alpha=alpha,
         horizontalalignment="left", verticalalignment="top", visible=visible)

    xscale(scale_x)
    yscale(scale_y)

    xlim(lim_x)
    ylim(lim_y)

    if a:
        axvline(a, color="red")
    if b:
        axvline(b, color="red")
    if c:
        axhline(c, color="red")
    if d:
        axhline(d, color="red")


def plot_raw(y, notes=None, marker=None, label_x="T (s)", label_y="Voltage (V)", tit=None, unit=None):
    sr = notes["sr"]
    memsize = len(y)
    t = memsize / sr
    x = linspace(0, t, memsize, endpoint=False)

    if unit == "ms":
        x = linspace(0, t, memsize, endpoint=False) * 1e3
        label_x = "T (ms)"

    if unit == "us":
        x = linspace(0, t, memsize, endpoint=False) * 1e6
        label_x = "T (us)"

    plot(x, y, marker=marker)
    xlabel(label_x)
    ylabel(label_y)

    if tit:
        tit = tit
    elif notes:
        tit = f"{notes['subtitle']}\n{notes['comment']}"
    title(tit)
