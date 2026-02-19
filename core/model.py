import pulp
import numpy as np
import os
import sys

# -----------------------------
# Utility
# -----------------------------
# def resource_path(rel):
#     """
#     Resolve resource paths for both:
#     - normal Python execution
#     - PyInstaller --onefile execution
#     """
#     if hasattr(sys, "_MEIPASS"):
#         return os.path.join(sys._MEIPASS, rel)
#     return rel

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def round_result(x, digits=2):
    if isinstance(x, dict):
        return {k: round(v, digits) for k, v in x.items()}
    elif isinstance(x, (list, np.ndarray)):
        return np.round(x, digits)
    else:
        return round(x, digits)


def simplify(x, tol=1e-3):
    if isinstance(x, dict):
        return {k: (0.0 if abs(v.value()) < tol else v.value())
                for k, v in x.items()}
    else:
        x = np.array(x, dtype=float)
        x[np.abs(x) < tol] = 0.0
        return x


def solve_senka(
    sortie_weights,
    senka,
    maxproportion,
    enable_short_bucket=True,
    *,
    activetime,
    inactivetime,
    sleeptime,
    days,
    max_money,
    special,
    initialfuel,
    initialammo,
    initialsteel,
    initialbucket,
    initialcond
):
    sortie_weights = -np.asarray(sortie_weights, dtype=float)
    senka = np.asarray(senka, dtype=float)
    maxproportion = np.asarray(maxproportion, dtype=float)

    n_sorties = sortie_weights.shape[0]

    if senka.shape[0] != n_sorties:
        raise ValueError("senka length must match number of sorties")
    
    if maxproportion.shape[0] != n_sorties:
        raise ValueError("maxproportion length must match number of sorties")
    
    if sortie_weights.ndim != 2 or sortie_weights.shape[1] != 6:
        raise ValueError("sortie_weights must have shape (n_sorties, 6)")
    
    # existing model construction
    # REMOVE any internal definition of sortie_weights
    # -----------------------------
    # Parameters (from GUI)
    # -----------------------------
    if activetime + inactivetime + sleeptime > 24:
        raise ValueError("稼働時間・遠征時間・休息時間の合計が24時間を超えています")

    runtime = activetime * days
    offtime = inactivetime * days

    initial = np.array([
        initialfuel,
        initialammo,
        initialsteel,
        initialbucket,
        initialcond,
        runtime * 60 * 60
    ], dtype=float)

    offsets = initial

    # -----------------------------
    # Data matrices
    # -----------------------------
    # sortie_weights = -np.array([
    #     [23.6, 23.6, 26.7, 51.3, 60.5, 114, 263., -72.7, 23.6, 163],
    #     [39.2, 39.2, 41.3, 56.2, 64.7, 82.1, 183., -115.9, 23.6, 110],
    #     [0,    0,    0,    9,    9,    63.4, 100., 0,     0,    0],
    #     [.102, .117, .182, .245, .26,  1.1,  1.1,  0,     .102, 0.293],
    #     [0.00, 0.00, -31., 0.00, 0.00, 0.00, 0.00, 0,     0.00, 0.00],
    #     [230., 240., 245., 145., 178., 225., 255., 60.,   250., 288.]
    # ])

    exped_weights_run = np.array([
        [-50.0, -50.0, 115.6, 157.0, 133.0, 220.0, 97 , 149.5 , 49.50, 79.50, 171.2, 222.9, -29.1, -29.1, 183.5, 234.5],
        [240.0, 360.0, 63.27, -34.0, 160.0, 244.0, 0 , 0 ,  63.50, 101.0, 138.3, 180.0, 164.9, 213.8, -30.2, -30.2],
        [72, 108, 0, 0, 18, 24, 0 , 0 , 0 , 0, 0, 0, 120, 177, 80, 123],
        [1.000, 1.000, 1.091, 1.000, 0.000, 0.000, 0 , 0.375 ,  0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
        [0.000, -30.0, -13.1, -12.0, 0.000, -10.0, 0 , -3.75 ,  0.000, -4.50, 0.000, -5.15, 0.000, -4.37, 0.000, -4.12],
        [-20.0, -30.0, -16.4, -15.0, -6.67, -10.0, -3.75 , -3.75 ,  -2.50, -3.75, -4.29, -6.43, -3.64, -5.45, -3.43, -5.14]
    ])

    exped_weights_off = np.zeros((6, 16))
    exped_weights_off[:5, :] = exped_weights_run[:5, :]

    exped_weights_sleep = np.array([
        [-25, -25, 106, 157, 200, 330, 388 , 598 , 198, 318, 400, 520, -80, -80, 535, 684],
        [120, 180, 58, -34, 240, 366, 0 , 0 , 254, 404, 323, 420, 453, 588, -84, -84],
        [36, 54, 0, 0, 24, 36, 0 , 0 ,0, 0, 0, 0, 324, 486, 240, 360],
        [0.5, 0.5, 1, 1, 0, 0, 0 , 1.5 ,1, 1, 0, 0, 0, 0, 0, 0],
        [0, -15, -12, -12, 0, -15, 0 , 0 , 0, -18, 0, -12, 0, -12, 0, -12],
        [0, 0, 0, 0, 0, 0, 0 , 0 ,0, 0, 0, 0, 0, 0, 0, 0]
    ])

    exped_weights_time = np.array([0.5, 0.5, 55/60, 1, 1.5, 1.5, 4, 4, 4, 4, 7/3, 7/3, 11/4, 11/4, 175/60, 175/60])

    # senka = np.array([1.47, 1.47, 1.47, 1.30, 1.30, 2.40, 2.48, 0, 1.47, 2.31])

    dupe_exped_constr = np.array([
        [1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1]
    ])

    shopweights = np.array([
        [1200, 0, 0, 500, 0, 200],
        [0, 250, 0, 500, 0, 200],
        [0, 0, 0, 200, 0, 1500],
        [0, 0, 6, 3, 0, 0],
        [0, 0, 0, 0, 180, 0],
        [0, 0, 0, 0, 0, 0]
    ])

    shopcosts = np.array([300, 100, 300, 300, 300, 700])

    # -----------------------------
    # Model
    # -----------------------------
    prob = pulp.LpProblem("Senka_Optimization", pulp.LpMaximize)

    sortie = pulp.LpVariable.dicts(
        "sortie",
        range(n_sorties),
        lowBound=0
    )
    exped_run = pulp.LpVariable.dicts("exped_run", range(16), lowBound=0, upBound=runtime)
    exped_off = pulp.LpVariable.dicts("exped_off", range(16), lowBound=0, upBound=offtime)
    exped_sleep = pulp.LpVariable.dicts("exped_sleep", range(16), lowBound=0)
    shop = pulp.LpVariable.dicts("shop", range(6), lowBound=0)

    prob += pulp.lpSum(senka[i] * sortie[i] for i in range(n_sorties))
    prob += pulp.lpSum(shopcosts[i] * shop[i] for i in range(6)) <= max_money
    prob += pulp.lpSum(exped_run[i] for i in range(16)) == runtime * 3
    prob += pulp.lpSum(exped_off[i] for i in range(16)) == offtime * 3
    prob += pulp.lpSum(exped_sleep[i] for i in range(16)) == 3

    for i in range(16):
        if exped_weights_time[i] >= sleeptime:
            prob += exped_sleep[i] == 0

    for k in range(7):
        prob += pulp.lpSum(dupe_exped_constr[k, i] * exped_sleep[i] for i in range(16)) <= 1
        prob += pulp.lpSum(dupe_exped_constr[k, i] * exped_run[i] for i in range(16)) <= runtime
        prob += pulp.lpSum(dupe_exped_constr[k, i] * exped_off[i] for i in range(16)) <= offtime

    if not enable_short_bucket:
        for i in range(4):
            prob += exped_off[i] == 0

    for r in range(6):
        prob += (
            pulp.lpSum(sortie_weights[i, r] * sortie[i] for i in range(n_sorties)) +
            pulp.lpSum(exped_weights_run[r, i] * exped_run[i] for i in range(16)) +
            pulp.lpSum(exped_weights_off[r, i] * exped_off[i] for i in range(16)) +
            days * pulp.lpSum(exped_weights_sleep[r, i] * exped_sleep[i] for i in range(16)) +
            pulp.lpSum(shopweights[r, i] * shop[i] for i in range(6)) +
            offsets[r]
            >= 0
        )

    for i in range(n_sorties):
        lhs = (1 - maxproportion[i]) * sortie[i]
        rhs = pulp.lpSum(maxproportion[i] * sortie[j] for j in range(n_sorties) if j != i)
        prob += lhs <= rhs


    # -----------------------------
    # CBC solver (PyInstaller-safe, file-logged)
    # -----------------------------
    cbc_path = resource_path(
        os.path.join("solverdir", "cbc", "win", "i64", "cbc.exe")
    )

    # IMPORTANT:
    # logPath must be writable at runtime.
    # Do NOT use sys._MEIPASS for logs.
    log_file = "cbc.log"

    solver = pulp.COIN_CMD(
        path=cbc_path,
        options=["printingOptions", "all"],
        logPath=log_file
    )

    prob.solve(solver)

    # --- forward CBC log to Python stdout (GUI) ---
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            print(f.read())

    sortie = simplify(sortie)
    exped_run_vals = simplify(exped_run)
    exped_off_vals = simplify(exped_off)
    exped_sleep_vals = simplify(exped_sleep)
    shop_vals = simplify(shop)

    final_senka = sum(senka[i] * sortie[i] for i in range(n_sorties)) + special

    final_senka = round_result(final_senka, 2)
    sortie = round_result(sortie, 2)
    exped_run_vals = round_result(exped_run_vals, 2)
    exped_off_vals = round_result(exped_off_vals, 2)
    exped_sleep_vals = round_result(exped_sleep_vals, 2)
    shop_vals = round_result(shop_vals, 2)

    # --- Resource breakdown (first 5 resources only) ---

    sortie_array = np.array([sortie[i] for i in range(n_sorties)])
    run_array = np.array([exped_run_vals[i] for i in range(16)])
    off_array = np.array([exped_off_vals[i] for i in range(16)])
    sleep_array = np.array([exped_sleep_vals[i] for i in range(16)])
    shop_array = np.array([shop_vals[i] for i in range(6)])

    # Sorties consume resources (weights were negated earlier)
    spent_from_sorties = np.dot((-sortie_weights)[:, :5].T, sortie_array)

    # Expeditions earn resources
    earned_from_expeds = (
        np.dot(exped_weights_run[:5, :], run_array) +
        np.dot(exped_weights_off[:5, :], off_array) +
        days * np.dot(exped_weights_sleep[:5, :], sleep_array)
    )

    # Shop purchases
    bought_from_shop = np.dot(shopweights[:5, :], shop_array)

    # Offsets (initial resources)
    offset = offsets[:5]

    remaining = offset - spent_from_sorties + earned_from_expeds + bought_from_shop

    # Round for display
    spent_from_sorties = np.round(spent_from_sorties, 2)
    earned_from_expeds = np.round(earned_from_expeds, 2)
    bought_from_shop = np.round(bought_from_shop, 2)
    remaining = np.round(remaining, 2)


    return (
        final_senka,
        sortie,
        exped_run_vals,
        exped_off_vals,
        exped_sleep_vals,
        shop_vals,
        spent_from_sorties,
        earned_from_expeds,
        bought_from_shop,
        remaining
    )


