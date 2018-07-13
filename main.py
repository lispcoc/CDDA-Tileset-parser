import os, sys, time, shutil, json, copy
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
from pathlib import Path
from PIL import Image

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
TILESET_TXT_TILE = "tiles.png" # 現在はもう使われてません

#
# 汎用リストボックスクラス
#
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

    def __init__(self, master, **key):
        tk.LabelFrame.__init__(self, master)
        self.lb = tk.Listbox(self)
        self.lb.configure(**key)
        # Scrollbar の生成
        self.sb1 = tk.Scrollbar(self, orient = 'v', command = self.lb.yview)
        # Listbox の設定
        self.lb.configure(yscrollcommand = self.sb1.set)
        self.lb.configure(selectmode="single")

        self.subframe1 = ttk.Frame(self, padding=10)
        self.up = tk.Button(self.subframe1, text="▲", command= self.up_selected)
        self.down = tk.Button(self.subframe1, text="▼", command= self.down_selected)

        self.lb.grid(row = 1, column = 0, sticky = tk.NSEW)
        self.sb1.grid(row = 1, column = 1, sticky = tk.NS)
        self.subframe1.grid(row = 2, column = 0)
        self.up.grid(row = 0, column = 0)
        self.down.grid(row = 0, column = 1)

        self.columnconfigure(0,weight=0)
        self.rowconfigure(1,weight=0)

#
# メインウィンドウ
#
def main():
    # メインウィンドウ作成
    root = tk.Tk()

    #メインウィンドウのタイトルを変更
    root.title("C:DDA Tile parser")

    #メインウィンドウを640x480にする
    root.geometry("800x400")

    # フレーム
    frame1 = ttk.Frame(root, padding=10)
    frame1.grid()

    tk.Label(frame1, text=u"タイルセットオーダー(下のタイルが優先されます)").grid(row=0, column=0)
    # タイルセットのリストボックス
    tileset_lb = GenericListBox(frame1, width=50,height=10)
    tileset_lb.grid(row=1, column=0)
    tileset_lb_reflesh(tileset_lb.lb)

    # リスト更新ボタン
    tilesets_reflesh_button = tk.Button(\
        frame1, text="リスト更新(タイルセットはtilesetsフォルダに入れてください)",\
        command= lambda : tileset_lb_reflesh(tileset_lb.lb))
    tilesets_reflesh_button.grid(row=2, column=0)

    # オーダー保存ボタン
    tileset_order_save_button = tk.Button(\
        frame1, text="タイルセットオーダーを保存",\
        command= lambda : tileset_order_save(get_list_from_listbox(tileset_lb.lb)))
    tileset_order_save_button.grid(row=3, column=0)

    tk.Label(frame1, text=u"Json設定ファイル(下のファイルが優先されます)").grid(row=0, column=1)
    # Json設定ファイルのリストボックス
    json_only_lb = GenericListBox(frame1, width=50,height=10)
    json_only_lb.grid(row=1, column=1)
    json_only_lb_reflesh(json_only_lb.lb)

    # リスト更新ボタン
    json_only_lb_reflesh_button = tk.Button(\
        frame1, text="リスト更新(Json設定ファイルはjson_onlyフォルダに入れてください)",\
        command= lambda : json_only_lb_reflesh(json_only_lb.lb))
    json_only_lb_reflesh_button.grid(row=2, column=1)

    # オーダー保存ボタン
    json_only_order_save_button = tk.Button(\
        frame1, text="Json設定ファイルオーダーを保存",\
        command= lambda : json_only_order_save(get_list_from_listbox(json_only_lb.lb)))
    json_only_order_save_button.grid(row=3, column=1)


    # タイルセット出力ボタン
    tileset_output_button = tk.Button(\
        frame1, text="タイルセットを出力",\
        command= lambda :\
            tileset_output(\
                get_list_from_listbox(tileset_lb.lb),\
                get_list_from_listbox(json_only_lb.lb)))
    tileset_output_button.grid(row=4, column=1)

    #メインウィンドウを表示し無限ループ
    root.mainloop()

#
# タイルセットの読み込み・書き出し処理
#
def tileset_order_load():
    order = []
    try:
        order_file = open(TILESET_ORDER_FILE , 'r')
    except IOError:
        print(TILESET_ORDER_FILE + " not found")
    else:
        order = json.load(order_file)
    return order

def tileset_order_save(order):
    try:
        order_file = open(TILESET_ORDER_FILE , 'w')
    except IOError:
        print(TILESET_ORDER_FILE + " cant open")
    else:
        order_file.write(json.dumps(order))

def tilesets_load():
    found = []
    new_order = []
    for filepath in walk_files_with('json', TILESET_DIR):
        found.append(filepath)
    order = tileset_order_load()
    if order:
        for a in order:
            if a in found:
                new_order.append(a)
                found.remove(a)
    for a in found:
        new_order.append(a)
    return new_order

def tileset_lb_reflesh(tileset_lb):
    tileset_lb.delete(0,tk.END)
    new_lb = tilesets_load()
    for val in new_lb:
        tileset_lb.insert(tk.END, val)

#
# Json設定ファイルの読み込み・書き出し処理
#
def json_only_order_load():
    order = []
    try:
        order_file = open(JSON_ONLY_ORDER_FILE , 'r')
    except IOError:
        print(JSON_ONLY_ORDER_FILE + " not found")
    else:
        order = json.load(order_file)
    return order

def json_only_order_save(order):
    try:
        order_file = open(JSON_ONLY_ORDER_FILE , 'w')
    except IOError:
        print(JSON_ONLY_ORDER_FILE + " cant open")
    else:
        order_file.write(json.dumps(order))

def json_only_load():
    found = []
    new_order = []
    for filepath in walk_files_with('json', JSON_ONLY_DIR):
        found.append(filepath)
    order = json_only_order_load()
    for a in order:
        if a in found:
            new_order.append(a)
            found.remove(a)
    for a in found:
        new_order.append(a)
    return new_order

def json_only_lb_reflesh(json_only_lb):
    json_only_lb.delete(0,tk.END)
    new_lb = json_only_load()
    for val in new_lb:
        json_only_lb.insert(tk.END, val)

#
# リストボックスに関する関数
#
def get_list_from_listbox(lb):
    newlist = list(lb.get(0, tk.END))
    return newlist

#
# エラーハンドラ
#
def ask_continue(title, msg):
    return tkmsg.askokcancel(title, msg)

def json_error(filename):
    tkmsg.showerror('エラー',\
        '解釈できないJsonファイルです！\n' +\
        filename)

def file_error(filename):
    tkmsg.showerror('エラー',\
        'ファイルを開けません！\n' +\
        filename)

def os_error(e):
    tkmsg.showerror('エラー', e)

#
# FileSystem Wrapper
#
def copy_wrapper(src, dest):
    try:
        shutil.copyfile(src, dest)
    except FileNotFoundError:
        file_error(src)
        return False
    else:
        return True

#
# スプライト番号の処理関数
#
def offset_sn(list_or_int, offset):
    if type(list_or_int) is int:
        return list_or_int + offset
    if type(list_or_int) is list:
        new_list = copy.deepcopy(list_or_int)
        if type(new_list[0]) is dict:
            for m in new_list:
                m["sprite"] += offset
        else:
            for n in new_list:
                n += offset
        return new_list

#
# カスタムタイル出力部本体
#
def tileset_output(tileset_order, json_only_order):
    
    # ヘルパー関数
    def exit_output_tileset():
        tkmsg.showerror("エラー", 'タイルセットの生成を中止します。')

    def success_output_tileset():
        tkmsg.showinfo("完了", 'タイルセットの生成が完了しました。')

    if os.path.exists(OUTPUT_DIR):
        if not ask_continue(\
            "確認",\
            "既に" + OUTPUT_DIR_NAME + "フォルダが存在します。上書きしますか？"):
            return
        else:
            try:
                shutil.rmtree(OUTPUT_DIR)
            except OSError as e:
                os_error(e)
                return

    # タイルセットのjsonをロードする
    tile_num = 0
    new_tile_config = {}
    new_ascii_tile = None
    new_ascii_file = None

    sprite_offset = 0
    for filename in tileset_order:
        tile_num += 1
        try:
            file = open(filename, 'r')
            json_data = json.load(file)

            if "tile_info" in json_data:
                new_tile_config["tile_info"] = copy.deepcopy(json_data["tile_info"])

            if "overlay_ordering" in json_data:
                new_tile_config["overlay_ordering"] = copy.deepcopy(json_data["overlay_ordering"])

            if not "tiles-new" in new_tile_config:
                new_tile_config["tiles-new"] = []

            src_dir = os.path.dirname(filename) + "/"
            dest_dir = OUTPUT_DIR + str(tile_num) +"/"
            os.makedirs(dest_dir)
            num_spr = 0
            for tile_setting in json_data["tiles-new"]:
                if not tile_setting["file"]:
                    json_error(filename)
                    exit_output_tileset()
                    return

                if "ascii" in tile_setting:
                    #asciiタイルは特別扱いらしいので最後に追加する
                    new_ascii_tile = copy.deepcopy(tile_setting)
                    new_ascii_file = src_dir + tile_setting["file"]
                    continue

                status = copy_wrapper(src_dir + tile_setting["file"], dest_dir + tile_setting["file"])
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
                new_tile_setting["file"] = str(tile_num) + "/" + new_tile_setting["file"]
                new_tile_config["tiles-new"].append(new_tile_setting)
                print(new_tile_setting["file"])
                print(num_spr)

            sprite_offset += num_spr
            print(sprite_offset)
        except IOError:
            file_error(filename)
            exit_output_tileset()
            return
        except json.JSONDecodeError:
            json_error(filename)
            exit_output_tileset()
            return
        except TypeError:
            json_error(filename)
            exit_output_tileset()
            return

    #Json設定ファイルの適用
    for filename in json_only_order:
        try:
            file = open(filename, 'r')
            json_data = json.load(file)
        except IOError:
            file_error(filename)
            exit_output_tileset()
            return
        except json.JSONDecodeError:
            json_error(filename)
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

    # asciiファイルの適用
    if new_ascii_tile != None:
        new_tile_config["tiles-new"].append(new_ascii_tile)
        status = copy_wrapper(new_ascii_file, OUTPUT_DIR + new_ascii_tile["file"])
        if not status:
            exit_output_tileset()
            return

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

#
# ファイル検索用関数
#
def walk_files_with(extension, directory='.'):
    """Generate paths of all files that has specific extension in a directory. 

    Arguments:
    extension -- [str] File extension without dot to find out
    directory -- [str] Path to target directory

    Return:
    filepath -- [str] Path to file found
    """
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.lower().endswith('.' + extension):
                yield os.path.normpath(os.path.join(root, filename))

#
# メインウィンドウ呼び出し
#
main()