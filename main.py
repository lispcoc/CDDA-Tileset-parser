import os
import sys
import time
import shutil
import json
import copy
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
from pathlib import Path
from PIL import Image

# -----------------------------------------------------------------
#
# 定数定義等
#
# -----------------------------------------------------------------
TILESET_DIR = "./tilesets"
TILESET_ORDER_FILE = "./tileset_order.json"

JSON_ONLY_DIR = "./json_only/"
JSON_ONLY_ORDER_FILE = "./json_only_order.json"

OUTPUT_DIR_NAME = "CustomTile"
OUTPUT_DIR = "./" + OUTPUT_DIR_NAME + "/"
OUTPUT_CONFIG_JSON = "tile_config.json"
OUTPUT_TILESET_TXT = "tileset.txt"

TILESET_TXT_NAME = "Custom Tileset"
TILESET_TXT_VIEW = "CustomTileset"
TILESET_TXT_JSON = OUTPUT_CONFIG_JSON
TILESET_TXT_TILE = "tiles.png"  # 現在はもう使われてません


# -----------------------------------------------------------------
#
# 標準出力リダイレクトボックスクラス
#
# -----------------------------------------------------------------


class StdoutRedirector(object):
    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.insert('end', string)
        self.text_space.see('end')

# -----------------------------------------------------------------
#
# 汎用リストボックスクラス
#
# -----------------------------------------------------------------


class GenericListBox(tk.LabelFrame):
    def up_selected(self):
        selects = self.lb.curselection()
        if len(selects) == 0:
            return
        selected = selects[0]
        if selected < 1:
            return
        elem = self.lb.get(selected)
        self.lb.delete(selected)
        self.lb.insert(selected - 1, elem)
        self.lb.select_set(selected - 1)

    def down_selected(self):
        selects = self.lb.curselection()
        if len(selects) == 0:
            return
        selected = selects[0]
        if selected >= self.lb.size() - 1:
            return
        elem = self.lb.get(selected)
        self.lb.delete(selected)
        self.lb.insert(selected + 1, elem)
        self.lb.select_set(selected + 1)

    def get_list(self):
        newlist = list(self.lb.get(0, tk.END))
        return newlist

    def __init__(self, master, **key):
        tk.LabelFrame.__init__(self, master)
        self.lb = tk.Listbox(self)
        self.lb.configure(**key)
        # Scrollbar の生成
        self.sb1 = tk.Scrollbar(self, orient='v', command=self.lb.yview)
        # Listbox の設定
        self.lb.configure(yscrollcommand=self.sb1.set)
        self.lb.configure(selectmode="single")

        self.subframe1 = ttk.Frame(self, padding=10)
        self.up = tk.Button(self.subframe1, text="▲", command=self.up_selected)
        self.down = tk.Button(self.subframe1, text="▼",
                              command=self.down_selected)

        self.lb.grid(row=1, column=0, sticky=tk.NSEW)
        self.sb1.grid(row=1, column=1, sticky=tk.NS)
        self.subframe1.grid(row=2, column=0)
        self.up.grid(row=0, column=0)
        self.down.grid(row=0, column=1)

        self.columnconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)

# -----------------------------------------------------------------
#
# メインウィンドウ
#
# -----------------------------------------------------------------


class FileOrder():
    def __init__(self, folder, default_order_file):
        self.order = []
        self.default_order = []
        self.folder = folder
        self.default_order_file = default_order_file

    def default_order_load(self, file):
        try:
            default_order_file = open(file, 'r')
            self.default_order = json.load(default_order_file)
        except IOError:
            print(TILESET_ORDER_FILE + " not found")

        return self.default_order

    def load(self):
        found = []
        new_order = []
        if self.folder:
            for filepath in self.walk_files_with('json', self.folder):
                found.append(filepath)
        if self.default_order_file:
            self.default_order_load(self.default_order_file)

        if self.default_order:
            for a in self.default_order:
                if a in found:
                    new_order.append(a)
                    found.remove(a)
        for a in found:
            new_order.append(a)
        self.order = new_order

        return self.order

    def default_order_save(self, new_order=None, order_file=None):
        if order_file:
            self.default_order_file = order_file
        if new_order:
            self.default_order = new_order
        try:
            order_file = open(self.default_order_file, 'w')
            order_file.write(json.dumps(self.default_order))
        except IOError:
            file_error(order_file)

    def walk_files_with(self, extension, directory='.'):
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.lower().endswith('.' + extension):
                    yield os.path.normpath(os.path.join(root, filename))


class MainWindow(tk.Tk):
    def walk_files_with(self, extension, directory='.'):
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.lower().endswith('.' + extension):
                    yield os.path.normpath(os.path.join(root, filename))

    def lb_reflesh(self, lb, order):
        lb.delete(0, tk.END)
        for val in order.load():
            lb.insert(tk.END, val)

    def __init__(self, **key):
        # メインウィンドウ作成
        tk.Tk.__init__(self, **key)

        # メインウィンドウのタイトルを変更
        self.title("C:DDA Tile parser")

        # メインウィンドウを640x480にする
        self.geometry("800x480")

        # フレーム
        frame1 = ttk.Frame(self, padding=10)
        frame1.grid()

        tk.Label(frame1, text=u"タイルセットオーダー(下のタイルが優先されます)").grid(
            row=0, column=0)
        # タイルセットのリストボックス
        tileset_lb = GenericListBox(frame1, width=50, height=10)
        tileset_lb.grid(row=1, column=0)
        self.tileset_order = FileOrder(TILESET_DIR, TILESET_ORDER_FILE)
        self.tileset_order.load()
        self.lb_reflesh(tileset_lb.lb, self.tileset_order)

        # リスト更新ボタン
        tilesets_reflesh_button = tk.Button(
            frame1, text="リスト更新(タイルセットはtilesetsフォルダに入れてください)",
            command=lambda: self.lb_reflesh(tileset_lb.lb, self.tileset_order))
        tilesets_reflesh_button.grid(row=2, column=0)

        # オーダー保存ボタン
        tileset_order_save_button = tk.Button(
            frame1, text="タイルセットオーダーを保存",
            command=lambda: self.tileset_order.default_order_save(
                tileset_lb.get_list()))
        tileset_order_save_button.grid(row=3, column=0)

        tk.Label(frame1, text=u"Json設定ファイル(下のファイルが優先されます)").grid(
            row=0, column=1)
        # Json設定ファイルのリストボックス
        json_only_lb = GenericListBox(frame1, width=50, height=10)
        json_only_lb.grid(row=1, column=1)
        self.json_order = FileOrder(JSON_ONLY_DIR, JSON_ONLY_ORDER_FILE)
        self.json_order.load()
        self.lb_reflesh(json_only_lb.lb, self.json_order)

        # リスト更新ボタン
        json_only_lb_reflesh_button = tk.Button(
            frame1, text="リスト更新(Json設定ファイルはjson_onlyフォルダに入れてください)",
            command=lambda: self.lb_reflesh(json_only_lb.lb, self.json_order))
        json_only_lb_reflesh_button.grid(row=2, column=1)

        # オーダー保存ボタン
        json_only_order_save_button = tk.Button(
            frame1, text="Json設定ファイルオーダーを保存",
            command=lambda: self.json_order.default_order_save(
                json_only_lb.get_list()))
        json_only_order_save_button.grid(row=3, column=1)

        # タイルセット出力ボタン
        tileset_output_button = tk.Button(
            frame1, text="タイルセットを出力",
            command=lambda:
            tileset_output(
                tileset_lb.get_list(),
                json_only_lb.get_list()))
        tileset_output_button.grid(row=4, column=1)

        # 標準出力リダイレクトボックス
        self.text_box = tk.Text(frame1, wrap='word', height=3, width=50)
        self.text_box.grid(column=0, row=5, columnspan=2,
                           sticky='NSWE')
        sys.stdout = StdoutRedirector(self.text_box)
        print("*** start debug message ***")
        # メインウィンドウを表示し無限ループ
        self.mainloop()

# -----------------------------------------------------------------
#
# エラーハンドラ
#
# -----------------------------------------------------------------


def ask_continue(title, msg):
    return tkmsg.askokcancel(title, msg)


def json_error(filename, e = ""):
    tkmsg.showerror('エラー',
                    '解釈できないJsonファイルです！\n' +
                    filename)
    print(e)


def file_error(filename, e = ""):
    tkmsg.showerror('エラー',
                    'ファイルを開けません！\n' +
                    filename)
    print(e)


def type_error(filename, e = ""):
    tkmsg.showerror('エラー',
                    'データ型の取り扱いが適切ではありません！\n' +
                    filename)
    print(e)


def os_error(e):
    tkmsg.showerror('エラー', e)

# -----------------------------------------------------------------
#
# FileSystem Wrapper
#
# -----------------------------------------------------------------


def copy_wrapper(src, dest):
    try:
        shutil.copyfile(src, dest)
    except FileNotFoundError:
        file_error(src)
        return False
    else:
        return True

# -----------------------------------------------------------------
#
# スプライト番号の処理関数
#
# -----------------------------------------------------------------


def offset_sn(list_or_int, offset):
    if type(list_or_int) is int:
        return list_or_int + offset
    if type(list_or_int) is list:
        if type(list_or_int[0]) is dict:
            new_list = copy.deepcopy(list_or_int)
            for m in new_list:
                m["sprite"] += offset
            return new_list
        else:
            new_list = []
            for n in list_or_int:
                new_list.append(n + offset)
            return new_list

# -----------------------------------------------------------------
#
# カスタムタイル出力部本体
#
# -----------------------------------------------------------------


def tileset_output(tileset_order, json_only_order):

    # ヘルパー関数
    def exit_output_tileset():
        tkmsg.showerror("エラー", 'タイルセットの生成を中止します。')

    def success_output_tileset():
        tkmsg.showinfo("完了", 'タイルセットの生成が完了しました。')

    if os.path.exists(OUTPUT_DIR):
        if not ask_continue(
            "確認",
                "既に" + OUTPUT_DIR_NAME + "フォルダが存在します。上書きしますか？"):
            return
        else:
            try:
                shutil.rmtree(OUTPUT_DIR)
            except OSError as e:
                os_error(e)
                return

    os.makedirs(OUTPUT_DIR)
    # タイルセットのjsonをロードする
    tile_num = 0
    new_tile_config = {}

    sprite_offset = 0
    for filename in tileset_order:
        tile_num += 1
        try:
            file = open(filename, 'r')
            json_data = json.load(file)

            if "tile_info" in json_data:
                new_tile_config["tile_info"] = copy.deepcopy(
                    json_data["tile_info"])

            if "overlay_ordering" in json_data:
                new_tile_config["overlay_ordering"] = copy.deepcopy(
                    json_data["overlay_ordering"])

            if not "tiles-new" in new_tile_config:
                new_tile_config["tiles-new"] = []

            src_dir = os.path.dirname(filename) + "/"
            dest_dir = OUTPUT_DIR + str(tile_num) + "/"
            os.makedirs(dest_dir)
            num_spr = 0
            for tile_setting in json_data["tiles-new"]:
                if not tile_setting["file"]:
                    json_error(filename)
                    exit_output_tileset()
                    return

                status = copy_wrapper(
                    src_dir + tile_setting["file"], dest_dir + tile_setting["file"])
                if not status:
                    exit_output_tileset()
                    return

                # 画像のスプライト数を調べる
                img = Image.open(src_dir + tile_setting["file"])
                spr_w = new_tile_config["tile_info"][0]["width"]
                spr_h = new_tile_config["tile_info"][0]["height"]
                if "sprite_width" in tile_setting:
                    spr_w = tile_setting["sprite_width"]
                if "sprite_height" in tile_setting:
                    spr_h = tile_setting["sprite_height"]
                w, h = img.size
                num_spr += int(w/spr_w) * int(h/spr_h)

                tiles = tile_setting["tiles"]
                # スプライト番号にオフセット（今までのタイルで消費した番号分）足す
                # また、次のスプライト番号オフセットを求めるためにスプライト番号の最大値を記憶しておく
                for tile in tiles:
                    if "fg" in tile:
                        tile["fg"] = offset_sn(tile["fg"], sprite_offset)
                    if "bg" in tile:
                        tile["bg"] = offset_sn(tile["bg"], sprite_offset)

                    if "additional_tiles" in tile:
                        for at in tile["additional_tiles"]:
                            if "fg" in at:
                                at["fg"] = offset_sn(at["fg"], sprite_offset)
                            if "bg" in at:
                                at["bg"] = offset_sn(at["bg"], sprite_offset)

                new_tile_setting = copy.deepcopy(tile_setting)
                new_tile_setting["file"] = str(
                    tile_num) + "/" + new_tile_setting["file"]
                new_tile_config["tiles-new"].append(new_tile_setting)
                print("file: " + src_dir + tile_setting["file"])
                print("sprites: " + str(num_spr))

            sprite_offset += num_spr
            print("current offset: " + str(sprite_offset))
        except IOError as e:
            file_error(filename, e)
            exit_output_tileset()
            return
        except json.JSONDecodeError as e:
            json_error(filename, e)
            exit_output_tileset()
            return
        except TypeError as e:
            type_error(filename, e)
            exit_output_tileset()
            return

    # Json設定ファイルの適用
    for filename in json_only_order:
        try:
            file = open(filename, 'r')
            json_data = json.load(file)
        except IOError:
            file_error(filename, e)
            exit_output_tileset()
            return
        except json.JSONDecodeError:
            json_error(filename, e)
            exit_output_tileset()
            return
        for json_only in json_data:
            if not "id" in json_only:
                json_error(filename)
                return
            id = json_only["id"]
            if "copy-from" in json_only:
                copy_from = json_only["copy-from"]
                for tile_setting in new_tile_config["tiles-new"]:
                    new_data = None
                    # 既存タイル設定を削除
                    remove_list = []
                    for tile in tile_setting["tiles"]:
                        if type(tile["id"]) is list:
                            if id in tile["id"]:
                                tile["id"].remove(id)
                        if type(tile["id"]) is str:
                            if tile["id"] == id:
                                remove_list.append(tile)
                    for r in remove_list:
                        tile_setting["tiles"].remove(r)

                    # タイル設定をオーバーライド
                    for tile in tile_setting["tiles"]:
                        tmp = tile["id"]
                        if not type(tmp) is list:
                            tmp = [tmp]
                        if copy_from in tmp:
                            new_data = copy.deepcopy(tile)
                            new_data["id"] = id

                    if new_data:
                        tile_setting["tiles"].append(new_data)

    # すべてのタイルセットに問題がなければtileset_configを出力
    new_tile_config_file = open(OUTPUT_DIR + OUTPUT_CONFIG_JSON, 'w')
    new_tile_config_file.write(json.dumps(new_tile_config, indent=2))
    new_tile_config_file.close()

    new_tileset_txt_file = open(OUTPUT_DIR + OUTPUT_TILESET_TXT, 'w')
    new_tileset_txt_file.write("NAME: " + TILESET_TXT_NAME + "\n")
    new_tileset_txt_file.write("VIEW: " + TILESET_TXT_VIEW + "\n")
    new_tileset_txt_file.write("JSON: " + TILESET_TXT_JSON + "\n")
    new_tileset_txt_file.write("TILESET: " + TILESET_TXT_TILE + "\n")
    new_tileset_txt_file.close()

    success_output_tileset()


# -----------------------------------------------------------------
#
# メインウィンドウ呼び出し
#
# -----------------------------------------------------------------
MainWindow()
