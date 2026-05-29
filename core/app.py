import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import pandas as pd
import os
from model import solve_senka


class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.config(state="normal")
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
        self.widget.config(state="disabled")
        self.widget.update_idletasks()

    def flush(self):
        pass


def load_sorties_from_excel(path):

    df = pd.read_excel(path, header=None)

    if df.shape[0] < 11 or df.shape[1] < 2:
        raise ValueError(
            "データの形式が正しくありません．"
            "少なくとも11行2列以上のデータが必要です．"
        )

    sortie_names = []
    sortie_weights = []
    senka = []
    maxproportion = []

    sortie_worlds = []
    sortie_nodes = []

    for col in range(1, df.shape[1]):

        column = df.iloc[:, col]

        # Require rows 0~10 to exist
        if column.iloc[0:11].isnull().any():
            raise ValueError(
                f"列 {col + 1} が完成されていません．"
                "最初の11行にすべて値が入っている必要があります．"
            )

        # sortie name
        name = column.iloc[0]

        if not isinstance(name, str):
            raise ValueError(
                f"列 {col + 1} の出撃の名前が文字列ではありません．"
            )

        # 海域
        world = str(column.iloc[9])

        # 通過マス
        nodes = str(column.iloc[10])

        try:
            weights = [float(x) for x in column.iloc[1:7]]

            s = float(column.iloc[7])

            m = float(column.iloc[8])

        except Exception:
            raise ValueError(
                f"列 {col + 1} に数値以外の値が入っています "
                "(行2～9)."
            )

        if m < 0 or m > 1:
            raise ValueError(
                f"列 {col + 1} の最大割合は0～1の間でなければなりません．"
            )

        sortie_names.append(name)
        sortie_weights.append(weights)
        senka.append(s)
        maxproportion.append(m)

        sortie_worlds.append(world)
        sortie_nodes.append(nodes)

    return (
        sortie_names,
        sortie_weights,
        senka,
        maxproportion,
        sortie_worlds,
        sortie_nodes
    )


def load_drop_data_from_excel(path):

    df = pd.read_excel(path)

    required_cols = [
        "node",
        "SS",
        "DD",
        "CL",
        "AV",
        "CA",
        "BB",
        "CV",
        "CVL"
    ]

    # check columns exist
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"{col} 列が存在しません")

    drop_data = {}

    for _, row in df.iterrows():

        node_name = str(row["node"])

        drop_data[node_name] = {
            "SS": float(row["SS"]),
            "DD": float(row["DD"]),
            "CL": float(row["CL"]),
            "AV": float(row["AV"]),
            "CA": float(row["CA"]),
            "BB": float(row["BB"]),
            "CV": float(row["CV"]),
            "CVL": float(row["CVL"]),
        }

    return drop_data


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("月間戦果最適化計算機 v0.90")
        self.geometry("700x800")

        self.sortie_names = None
        self.sortie_weights = None
        self.senka = None
        self.maxproportion = None
        self.sortie_worlds = None
        self.sortie_nodes = None
        self.drop_data = None
        self.enable_short_bucket = tk.BooleanVar(value=True)
        self.enable_sunk_recovery = tk.BooleanVar(value=True)
        self.sunk_speed_var = tk.StringVar(value="80")
        self.params = {}

        param_defs = [
            ("稼働時間", "activetime", 12, "一日あたりのプレイ時間"),
            ("遠征時間", "inactivetime", 6, "周回はしないが，遠征は継続的に稼働できる時間"),
            ("休息時間", "sleeptime", 6, "睡眠時間を想定，この時間設定以下の遠征が3艦隊送られる"),
            ("日数", "days", 31, "計算日数"),
            ("最大課金額", "max_money", 0, "課金額の上限，0にすると無課金扱いになる"),
            ("特別戦果", "special", 3000, "引継ぎ戦果と特別戦果の合計"),
            ("燃料オフセット", "initialfuel", 200000, "遠征と課金からの獲得資源以外の燃料予算（初期備蓄・任務・自然回復・プレ箱等）"),
            ("弾薬オフセット", "initialammo", 200000, "上記同様"),
            ("鋼材オフセット", "initialsteel", 150000, "上記同様"),
            ("バケツオフセット", "initialbucket", 1900, "上記同様"),
            ("遠征用cond値", "initialcond", 0, "遠征に使用できるcondの初期値"),
        ]

        param_frame = tk.LabelFrame(self, text="パラメータ設定")
        param_frame.pack(padx=10, pady=5, fill="x")

        for i, (label, key, default, note) in enumerate(param_defs):

            tk.Label(
                param_frame,
                text=label
            ).grid(
                row=i,
                column=0,
                sticky="w",
                padx=(0, 5)
            )

            var = tk.StringVar(value=str(default))

            tk.Entry(
                param_frame,
                textvariable=var,
                width=10
            ).grid(
                row=i,
                column=1,
                sticky="w",
                padx=(0, 10)
            )

            tk.Label(
                param_frame,
                text=note,
                fg="gray",
                anchor="w",
                justify="left",
                wraplength=500,
            ).grid(
                row=i,
                column=2,
                sticky="w"
            )

            self.params[key] = var

        # -------------------------
        # checkboxes go here
        # -------------------------

        check_frame = tk.Frame(self)
        check_frame.pack(pady=5, fill="x")

        tk.Checkbutton(
            check_frame,
            text="「遠征時間」中に短時間の遠征（バケツ遠征）を許容",
            variable=self.enable_short_bucket
        ).pack(side="left", padx=10)

        sunk_frame = tk.Frame(check_frame)
        sunk_frame.pack(side="left", padx=10)

        self.sunk_checkbox = tk.Checkbutton(
            sunk_frame,
            text="轟沈回収を許容",
            variable=self.enable_sunk_recovery,
            command=self.toggle_sunk_speed
        )
        self.sunk_checkbox.pack(side="left")

        self.sunk_speed_frame = tk.Frame(sunk_frame)

        tk.Label(
            self.sunk_speed_frame,
            text="轟沈の時速（隻数/時間）"
        ).pack(side="left", padx=(10, 3))

        tk.Entry(
            self.sunk_speed_frame,
            textvariable=self.sunk_speed_var,
            width=6
        ).pack(side="left")

        self.toggle_sunk_speed()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        self.sortie_excel_label = tk.StringVar(value="No file loaded")
        self.drop_excel_label = tk.StringVar(value="No file loaded")

        # -------------------------
        # Sortie excel pair
        # -------------------------
        sortie_frame = tk.Frame(btn_frame)
        sortie_frame.pack(side="left", padx=10)

        tk.Button(
            sortie_frame,
            text="出撃エクセルを読込む",
            command=self.load_excel
        ).pack(side="left")

        tk.Label(
            sortie_frame,
            textvariable=self.sortie_excel_label,
            font=("Consolas", 9),
            fg="gray"
        ).pack(side="left", padx=5)

        # -------------------------
        # Drop excel pair
        # -------------------------
        drop_frame = tk.Frame(btn_frame)
        drop_frame.pack(side="left", padx=10)

        tk.Button(
            drop_frame,
            text="ドロップエクセルを読込む",
            command=self.load_drop_excel
        ).pack(side="left")

        tk.Label(
            drop_frame,
            textvariable=self.drop_excel_label,
            font=("Consolas", 9),
            fg="gray"
        ).pack(side="left", padx=5)

        tk.Button(
            self,
            text="最適化を実行",
            command=self.run
        ).pack(pady=5)

        self.result = tk.StringVar(value="Result: —")
        tk.Label(
            self,
            textvariable=self.result,
            font=("Consolas", 12)
        ).pack()

        self.console = tk.Text(
            self,
            height=20,
            width=90,
            font=("Consolas", 9)
        )
        self.console.pack(padx=10, pady=10)
        self.console.config(state="disabled")

        dev_frame = tk.LabelFrame(self, text="Developer Notes")
        dev_frame.pack(padx=10, pady=10, fill="x")

        dev_label = tk.Label(
            dev_frame,
            text="バグ報告や要望はtwitter(@kc15224)やdiscord(@ha15224)にて対応します",
            fg="gray",
            anchor="center",      # centers text inside the label
            justify="center",     # centers multi-line text horizontally
        )
        dev_label.pack(padx=5, pady=5, fill="x")

    def show_results_window(
        self,
        sortie_names,
        sortie_vals,
        run_vals,
        off_vals,
        sleep_vals,
        shop_vals,
        spent_from_sorties,
        earned_from_expeds,
        bought_from_shop,
        remaining,
        sortie_withdrop, # new items from here
        drops_sunk,
        drops_scrap,
        earned_from_scrap,
        earned_from_sunk,
    ):
        win = tk.Toplevel(self)
        win.title("最適化結果")
        win.geometry("1400x800")

        expedition_names = [
            "長距離", "長距離キラ", "海峡警備キラ", "ブルネイ哨戒キラ",
            "海上護衛", "海上護衛キラ", "タンカー護衛", "タンカー護衛キラ",
            "鼠輸送", "鼠輸送キラ", "北方鼠", "北方鼠キラ",
            "東京急行", "東京急行キラ", "東京急行(弐)", "東京急行(弐)キラ"
        ]

        shop_names = [
            "タンカー徴用", "弾薬", "高速修復材",
            "出撃セット", "間宮", "工廠セット"
        ]

        # -----------------------------
        # Main numeric sections
        # -----------------------------
        sections = [
            (
                "出撃数",
                sortie_names,
                [
                    (
                        sortie_vals[i],
                        sortie_withdrop[i]
                    )
                    for i in range(len(sortie_names))
                ]
            ),

            ("稼働する遠征の時間数", expedition_names,
            [run_vals[i] + off_vals[i] for i in range(16)]),

            ("休息時間の遠征選択", expedition_names,
            [sleep_vals[i] for i in range(16)]),

            ("　　　アイテム屋からの購入数", shop_names,
            [shop_vals[i] for i in range(6)])
        ]

        ship_labels = ["潜水", "駆逐", "軽巡", "水母", "重巡", "戦艦", "軽母", "空母"]
        resource_labels_small = ["燃料", "弾薬", "鋼材"]

        extra_sections = [
            (
                "　　　　　ドロップ処理",
                ship_labels,
                [
                    (drops_sunk[i], drops_scrap[i])
                    for i in range(len(ship_labels))
                ],
                ("轟沈数", "解体数")
            ),
            (
                "　ドロップ処理からの獲得資源",
                resource_labels_small,
                [
                    (earned_from_sunk[i], earned_from_scrap[i])
                    for i in range(len(resource_labels_small))
                ],
                ("轟沈", "解体")
            )
        ]

        col = 0

        for title, names, values in sections:

            # Determine width of section
            section_width = 3 if title == "出撃数" else 2

            tk.Label(
                win,
                text=title,
                font=("Consolas", 12, "bold")
            ).grid(
                row=0,
                column=col,
                columnspan=section_width,
                pady=(10, 0)
            )

            tk.Label(
                win,
                text="Name"
            ).grid(
                row=1,
                column=col,
                sticky="w",
                padx=5
            )

            # -------------------------
            # Headers
            # -------------------------
            if title == "出撃数":

                tk.Label(
                    win,
                    text="全体数"
                ).grid(
                    row=1,
                    column=col+1,
                    sticky="w",
                    padx=5
                )

                tk.Label(
                    win,
                    text="ドロップあり"
                ).grid(
                    row=1,
                    column=col+2,
                    sticky="w",
                    padx=5
                )

            else:

                tk.Label(
                    win,
                    text="Value"
                ).grid(
                    row=1,
                    column=col+1,
                    sticky="w",
                    padx=5
                )

            # -------------------------
            # Rows
            # -------------------------
            for i, name in enumerate(names):

                tk.Label(
                    win,
                    text=name,
                    width=10 if title == "　アイテム屋からの購入数" else 18,
                    anchor="w"
                ).grid(
                    row=i+2,
                    column=col,
                    padx=4,
                    pady=2,
                    sticky="w"
                )

                if title == "出撃数":

                    total_val, drop_val = values[i]

                    tk.Label(
                        win,
                        text=f"{total_val:.2f}",
                        width=12,
                        anchor="w"
                    ).grid(
                        row=i+2,
                        column=col+1,
                        padx=5,
                        pady=2,
                        sticky="w"
                    )

                    tk.Label(
                        win,
                        text=f"{drop_val:.2f}",
                        width=12,
                        anchor="w"
                    ).grid(
                        row=i+2,
                        column=col+2,
                        padx=5,
                        pady=2,
                        sticky="w"
                    )

                else:

                    tk.Label(
                        win,
                        text=f"{values[i]:.2f}",
                        width=12,
                        anchor="w"
                    ).grid(
                        row=i+2,
                        column=col+1,
                        padx=5,
                        pady=2,
                        sticky="w"
                    )

            col += section_width

        # -----------------------------
        # Extra drop statistics sections
        # (display below アイテム屋からの購入数)
        # -----------------------------

        # Reuse the same column as the shop section
        extra_col = col - 2

        # tighter sizing for drop-stat columns
        win.grid_columnconfigure(extra_col, minsize=45)       # ship name
        win.grid_columnconfigure(extra_col + 1, minsize=35)   # 轟沈数
        win.grid_columnconfigure(extra_col + 2, minsize=35)   # 解体数

        # place extra sections directly below shop section
        start_row = len(shop_names) + 2

        for title, names, values, headers in extra_sections:

            tk.Label(
                win,
                text=title,
                font=("Consolas", 12, "bold")
            ).grid(
                row=start_row,
                column=extra_col,
                columnspan=3,
                sticky="w",
                pady=(15, 0)
            )

            tk.Label(
                win,
                text="Name"
            ).grid(
                row=start_row + 1,
                column=extra_col,
                sticky="w",
                padx=3
            )

            tk.Label(
                win,
                text=headers[0]
            ).grid(
                row=start_row + 1,
                column=extra_col + 1,
                sticky="w",
                padx=3
            )

            tk.Label(
                win,
                text=headers[1]
            ).grid(
                row=start_row + 1,
                column=extra_col + 2,
                sticky="w",
                padx=3
            )

            for i, name in enumerate(names):

                tk.Label(
                    win,
                    text=name,
                    width=3,
                    anchor="w"
                ).grid(
                    row=start_row + 2 + i,
                    column=extra_col,
                    padx=1,
                    pady=1,
                    sticky="w"
                )

                tk.Label(
                    win,
                    text=f"{values[i][0]:.1f}",
                    width=8,
                    anchor="e"
                ).grid(
                    row=start_row + 2 + i,
                    column=extra_col + 1,
                    padx=1,
                    pady=1,
                    sticky="w"
                )

                tk.Label(
                    win,
                    text=f"{values[i][1]:.1f}",
                    width=8,
                    anchor="e"
                ).grid(
                    row=start_row + 2 + i,
                    column=extra_col + 2,
                    padx=1,
                    pady=1,
                    sticky="w"
                )

            # move downward for next section
            start_row += len(names) + 4


        # -----------------------------
        # Resource breakdown column
        # -----------------------------
        resource_names = ["燃料", "弾薬", "鋼材", "バケツ", "cond"]

        resource_sections = [
            ("出撃による消費資源", spent_from_sorties),
            ("遠征による獲得資源", earned_from_expeds),
            ("課金による獲得資源", bought_from_shop),
            ("最終残量", remaining),
        ]

        # Create one frame occupying the next two columns
        resource_frame = tk.Frame(win)
        resource_frame.grid(
            row=0,
            column=col,
            rowspan=40,
            padx=(100, 20),
            sticky="n"
        )

        current_row = 0

        for title, values in resource_sections:

            tk.Label(
                resource_frame,
                text=title,
                font=("Consolas", 12, "bold")
            ).grid(row=current_row, column=0, columnspan=2, pady=(10, 0))

            current_row += 1

            tk.Label(resource_frame, text="Resource").grid(
                row=current_row, column=0, sticky="w", padx=5
            )
            tk.Label(resource_frame, text="Value").grid(
                row=current_row, column=1, sticky="w", padx=5
            )

            current_row += 1

            for i, name in enumerate(resource_names):
                tk.Label(
                    resource_frame,
                    text=name,
                    width=10,
                    anchor="w"
                ).grid(row=current_row, column=0, padx=5, pady=2, sticky="w")

                tk.Label(
                    resource_frame,
                    text=f"{values[i]:.2f}",
                    width=12,
                    anchor="w"
                ).grid(row=current_row, column=1, padx=5, pady=2, sticky="w")

                current_row += 1

            current_row += 1  # spacing between tables

    def toggle_sunk_speed(self):

        if self.enable_sunk_recovery.get():
            self.sunk_speed_frame.pack(side="left")
        else:
            self.sunk_speed_frame.pack_forget()

    def get_params(self):
        try:
            # --- strict integer check for days ---
            days_str = self.params["days"].get()
            if not days_str.isdigit():
                raise ValueError("日数は整数で入力してください．")

            params = {
                "activetime": float(self.params["activetime"].get()),
                "inactivetime": float(self.params["inactivetime"].get()),
                "sleeptime": float(self.params["sleeptime"].get()),
                "days": int(days_str),
                "max_money": float(self.params["max_money"].get()),
                "special": float(self.params["special"].get()),
                "initialfuel": float(self.params["initialfuel"].get()),
                "initialammo": float(self.params["initialammo"].get()),
                "initialsteel": float(self.params["initialsteel"].get()),
                "initialbucket": float(self.params["initialbucket"].get()),
                "initialcond": float(self.params["initialcond"].get()),
                "sunk_hourly_rate": float(self.sunk_speed_var.get()),
            }
        except ValueError as e:
            raise ValueError(str(e) if str(e) else "パラメータの値が正しくありません．数値を入力してください．")

        # ---- negativity check for first five parameters ----
        first_five_keys = [
            "activetime",
            "inactivetime",
            "sleeptime",
            "days",
            "max_money"
        ]

        key_labels = {
            "activetime": "稼働時間",
            "inactivetime": "遠征時間",
            "sleeptime": "休息時間",
            "days": "日数",
            "max_money": "最大課金額"
        }

        for key in first_five_keys:
            if params[key] < 0:
                raise ValueError(f"{key_labels[key]} は0以上でなければなりません．")

        return params


    def load_excel(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not path:
            return

        try:
            (
                self.sortie_names,
                self.sortie_weights,
                self.senka,
                self.maxproportion,
                self.sortie_worlds,
                self.sortie_nodes
            ) = load_sorties_from_excel(path)

            self.sortie_excel_label.set(os.path.basename(path))

            messagebox.showinfo(
                "エクセル読込み成功",
                f"{len(self.sortie_weights)}種の出撃が読込まれました."
            )
        except Exception as e:
            messagebox.showerror("出撃エクセル読み込みエラー", str(e))

    def load_drop_excel(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )

        if not path:
            return

        try:

            self.drop_data = load_drop_data_from_excel(path)

            self.drop_excel_label.set(os.path.basename(path))

            messagebox.showinfo(
                "ドロップエクセル読込み成功",
                "ドロップデータが読込まれました."
            )

        except Exception as e:
            messagebox.showerror(
                "ドロップエクセル読込みエラー",
                str(e)
            )

    def run(self):
        if self.sortie_weights is None or self.senka is None or self.maxproportion is None:
            messagebox.showerror(
                "エクセル不備",
                "最適化を実行する前に，出撃データをエクセルから読込んでください。"
            )
            return
        if self.drop_excel_label.get() == "No file loaded":
            messagebox.showerror(
                "エクセル不備",
                "最適化を実行する前に，ドロップデータをエクセルから読込んでください。"
            )
            return

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        redirector = TextRedirector(self.console)
        sys.stdout = redirector
        sys.stderr = redirector

        self.console.config(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.config(state="disabled")

        try:
            print("Starting optimization...\n")
            params = self.get_params()
            (
                senka_value,
                sortie_vals,
                run_vals,
                off_vals,
                sleep_vals,
                shop_vals,
                spent_from_sorties,
                earned_from_expeds,
                bought_from_shop,
                remaining,
                sortie_withdrop, # new items from here
                drops_sunk,
                drops_scrap,
                earned_from_scrap,
                earned_from_sunk,
            ) = solve_senka(
                self.sortie_weights,
                self.drop_data,
                self.sortie_worlds,
                self.sortie_nodes,
                self.senka,
                self.maxproportion,
                enable_short_bucket=self.enable_short_bucket.get(),
                enable_sunk_recovery=self.enable_sunk_recovery.get(),
                **params
            )
            print("\nOptimization finished.")

            print("Sortie schedule:", sortie_vals)
            print("Expeditions (run + off):", {i: run_vals[i]+off_vals[i] for i in run_vals})
            print("Expeditions (sleep):", sleep_vals)
            print("Shop purchases:", shop_vals)

            self.result.set(f"特別戦果＋出撃戦果: {senka_value:.2f}")

            # Show detailed window
            self.show_results_window(
                self.sortie_names,
                sortie_vals,
                run_vals,
                off_vals,
                sleep_vals,
                shop_vals,
                spent_from_sorties,
                earned_from_expeds,
                bought_from_shop,
                remaining,
                sortie_withdrop, # new items from here
                drops_sunk,
                drops_scrap,
                earned_from_scrap,
                earned_from_sunk,
            )

        except Exception as e:
            print("\nERROR:")
            print(e)
            messagebox.showerror("Error", str(e))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr



if __name__ == "__main__":
    App().mainloop()
