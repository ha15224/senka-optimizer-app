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

    if df.shape[0] < 9 or df.shape[1] < 2:
        raise ValueError("データの形式が正しくありません．少なくとも9行2列以上のデータが必要です．")

    sortie_names = []
    sortie_weights = []
    senka = []
    maxproportion = []

    for col in range(1, df.shape[1]):  # start from column B
        column = df.iloc[:, col]

        if column.iloc[0:9].isnull().any():
            raise ValueError(f"列 {col + 1} が完成されていません．最初の9行にすべて値が入っている必要があります．")

        name = column.iloc[0]
        if not isinstance(name, str):
            raise ValueError(f"列 {col + 1} の出撃の名前が文字列ではありません．")

        try:
            weights = [float(x) for x in column.iloc[1:7]]  # rows 2–7
            s = float(column.iloc[7])                      # row 8
            m = float(column.iloc[8])                    # row 9 (max proportion)
        except Exception:
            raise ValueError(
                f"列 {col + 1} に数値以外の値が入っています (行2～8)."
            )

        if m < 0 or m > 1:
            raise ValueError(
                f"列 {col + 1} の最大割合は0～1の間でなければなりません．"
            )

        sortie_names.append(name)
        sortie_weights.append(weights)
        senka.append(s)
        maxproportion.append(m)

    return sortie_names, sortie_weights, senka, maxproportion

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("月間戦果最適化計算機 v0.1")
        self.geometry("700x800")

        self.sortie_names = None
        self.sortie_weights = None
        self.senka = None
        self.maxproportion = None
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
            tk.Label(param_frame, text=label).grid(row=i, column=0, sticky="w", padx=(0, 5))

            var = tk.StringVar(value=str(default))
            tk.Entry(param_frame, textvariable=var, width=10).grid(
                row=i, column=1, sticky="w", padx=(0, 10)
            )

            tk.Label(
                param_frame,
                text=note,
                fg="gray",
                anchor="w",
                justify="left",
                wraplength=500,   # adjust if needed
            ).grid(row=i, column=2, sticky="w")

            self.params[key] = var

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame,
            text="エクセルを読み込む",
            command=self.load_excel
        ).pack(side="left")

        self.excel_label = tk.StringVar(value="No file loaded")
        tk.Label(
            btn_frame,
            textvariable=self.excel_label,
            font=("Consolas", 9),
            fg="gray"
        ).pack(side="left", padx=10)

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

    def show_results_window(self, sortie_names, sortie_vals, run_vals, off_vals, sleep_vals, shop_vals):
        win = tk.Toplevel(self)
        win.title("最適化結果")
        win.geometry("1000x600")  # wider window to fit horizontally

        # Define each section
        sections = [
            ("出撃数", sortie_names, sortie_vals),
            ("稼働する遠征の時間数", ["長距離", "長距離キラ", "海峡警備キラ", "ブルネイ哨戒キラ", "海上護衛", "海上護衛キラ", "鼠輸送", "鼠輸送キラ", "北方鼠", "北方鼠キラ", "東京急行", "東京急行キラ", "東京急行(弐)", "東京急行(弐)キラ"], 
            [run_vals[i]+off_vals[i] for i in run_vals]),
            ("休息時間の遠征選択", ["長距離", "長距離キラ", "海峡警備キラ", "ブルネイ哨戒キラ", "海上護衛", "海上護衛キラ", "鼠輸送", "鼠輸送キラ", "北方鼠", "北方鼠キラ", "東京急行", "東京急行キラ", "東京急行(弐)", "東京急行(弐)キラ"], 
            [sleep_vals[i] for i in sleep_vals]),
            ("アイテム屋からの購入数", ["タンカー徴用", "弾薬", "高速修復材", "出撃セット", "間宮", "工廠セット"], 
            [shop_vals[i] for i in shop_vals])
        ]

        # Arrange sections in columns
        col = 0
        for title, names, values in sections:
            # Section title
            tk.Label(win, text=title, font=("Consolas", 12, "bold")).grid(row=0, column=col, columnspan=2, pady=(10,0))

            # Column headers
            tk.Label(win, text="Name").grid(row=1, column=col, sticky="w", padx=5)
            tk.Label(win, text="Value").grid(row=1, column=col+1, sticky="w", padx=5)

            # Entries / labels
            for i, name in enumerate(names):
                name_var = tk.StringVar(value=name)
                tk.Label(win, text=name, width=20, anchor="w").grid(row=i+2, column=col, padx=5, pady=2, sticky="w")
                tk.Label(win, text=f"{values[i]:.2f}", width=10, anchor="w").grid(row=i+2, column=col+1, padx=5, pady=2, sticky="w")

            col += 2  # move to the next section column

    def get_params(self):
        try:
            return {
                "activetime": float(self.params["activetime"].get()),
                "inactivetime": float(self.params["inactivetime"].get()),
                "sleeptime": float(self.params["sleeptime"].get()),
                "days": int(self.params["days"].get()),
                "max_money": float(self.params["max_money"].get()),
                "special": float(self.params["special"].get()),
                "initialfuel": float(self.params["initialfuel"].get()),
                "initialammo": float(self.params["initialammo"].get()),
                "initialsteel": float(self.params["initialsteel"].get()),
                "initialbucket": float(self.params["initialbucket"].get()),
                "initialcond": float(self.params["initialcond"].get()),
            }
        except ValueError:
            raise ValueError("パラメータの値が正しくありません．数値を入力してください．")


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
                self.maxproportion
            ) = load_sorties_from_excel(path)

            self.excel_label.set(os.path.basename(path))

            messagebox.showinfo(
                "エクセル読み込み成功",
                f"{len(self.sortie_weights)}種の出撃が読み込まれました."
            )
        except Exception as e:
            messagebox.showerror("エクセル読み込みエラー", str(e))


    def run(self):
        if self.sortie_weights is None or self.senka is None or self.maxproportion is None:
            messagebox.showerror(
                "エクセル不備",
                "最適化を実行する前に，出撃データをエクセルから読み込んでください。"
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
            senka_value, sortie_vals, run_vals, off_vals, sleep_vals, shop_vals = solve_senka(
                self.sortie_weights,
                self.senka,
                self.maxproportion,
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
                shop_vals
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
