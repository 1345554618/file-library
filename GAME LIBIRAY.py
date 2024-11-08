import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import messagebox
import subprocess
import sqlite3
import os
from PIL import Image, ImageTk
from tkinter import filedialog 

# 連接到SQLite資料庫
db_path = os.path.abspath("game_library.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 創建表格
cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        category TEXT,
        icon_path TEXT
    )
''')
conn.commit()

# 初始化 Tkinter GUI
root = TkinterDnD.Tk()
root.title("桌面遊戲庫")
root.geometry("400x500")
root.configure(bg="black")

# Canvas 顯示區域
canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

# 保存遊戲數據的列表
game_data = []

# 設定每行顯示的最大圖標數
icons_per_row = 4
icon_width = 60  # 圖標的寬度
icon_height = 60  # 圖標的高度

# 追蹤當前選中的項目
selected_index = None
icon_images = []
icon_states = {}

def display_games():
    global selected_index
    canvas.delete("all")
    x_position = 10
    y_position = 10
    
    for i, (name, path, icon_path, file_type) in enumerate(game_data):
        try:
            if icon_path and os.path.exists(icon_path):
                original_icon = Image.open(icon_path)
            else:
                original_icon = Image.open(r"C:\Users\jack1\Desktop\assignment\A2\src\屏幕截图 2024-11-06 211618.png")
            
            # 創建圖標
            icon_image = ImageTk.PhotoImage(original_icon.resize((icon_width, icon_height), Image.LANCZOS))
            icon_images.append(icon_image)
            
            enlarged_icon_image = ImageTk.PhotoImage(original_icon.resize((int(icon_width * 1.2), int(icon_height * 1.2)), Image.LANCZOS))
            icon_states[i] = {'normal': icon_image, 'enlarged': enlarged_icon_image}
            
            # 決定初始圖標大小
            current_image = icon_states[i]['enlarged'] if i == selected_index else icon_states[i]['normal']
            
            # 創建圖標
            icon_item = canvas.create_image(x_position, y_position, 
                                          image=current_image, 
                                          anchor="nw", 
                                          tags=(f"icon_{i}",))
            
            # 創建文字
            text_item = canvas.create_text(x_position + icon_width / 2, 
                                         y_position + icon_height + 10,
                                         text=name, 
                                         anchor="n", 
                                         font=("Arial", 10))
            
            # 綁定左鍵點擊事件
            canvas.tag_bind(icon_item, '<Button-1>', lambda event, idx=i: select_item(event, idx))
            canvas.tag_bind(text_item, '<Button-1>', lambda event, idx=i: select_item(event, idx))
            canvas.tag_bind(icon_item, '<Double-1>', lambda event, idx=i: open_item(idx))
            canvas.tag_bind(text_item, '<Double-1>', lambda event, idx=i: open_item(idx))
            
            # 綁定右鍵點擊事件
            canvas.tag_bind(icon_item, '<Button-3>', lambda event, idx=i: create_context_menu(event, idx))
            canvas.tag_bind(text_item, '<Button-3>', lambda event, idx=i: create_context_menu(event, idx))
            
            # 只為非選中的圖標綁定懸停效果
            if i != selected_index:
                canvas.tag_bind(icon_item, '<Enter>', lambda event, idx=i: enlarge_icon(event, idx))
                canvas.tag_bind(icon_item, '<Leave>', lambda event, idx=i: reset_icon(event, idx))
            
        except Exception as e:
            print(f"無法加載圖標: {e}")
            continue
        
        # 更新位置
        x_position += icon_width + 20
        if (i + 1) % icons_per_row == 0:
            x_position = 10
            y_position += icon_height + 40
    
    canvas.update_idletasks()



def enlarge_icon(event=None, idx=None):
    if idx is not None and idx != selected_index:  # 只有非選中狀態的圖標才能被懸停放大
        icon_item = canvas.find_withtag(f"icon_{idx}")[0]
        canvas.itemconfig(icon_item, image=icon_states[idx]['enlarged'])

def reset_icon(event=None, idx=None):
    if idx is not None and idx != selected_index:  # 只有非選中狀態的圖標才能被重置
        icon_item = canvas.find_withtag(f"icon_{idx}")[0]
        canvas.itemconfig(icon_item, image=icon_states[idx]['normal'])

# 加載資料庫中的遊戲
def load_games():
    cursor.execute("SELECT name, path, icon_path FROM games")
    games = cursor.fetchall()
    for name, path, icon_path in games:
        if os.path.isdir(path):
            file_type = "folder"
        elif path.endswith('.exe'):
            file_type = "exe"
        else:
            file_type = "unknown"
        game_data.append((name, path, icon_path, file_type))
    display_games()


def select_item(event, index):
    global selected_index
    
    # 如果點擊的是當前已選中的圖標，不做任何操作
    if selected_index == index:
        return
    
    # 重置之前選中的圖標
    if selected_index is not None:
        # 明確調用 reset_icon 來縮小之前的圖標
        previous_icon = canvas.find_withtag(f"icon_{selected_index}")[0]
        canvas.itemconfig(previous_icon, image=icon_states[selected_index]['normal'])
        
        # 為之前的圖標重新綁定懸停效果
        canvas.tag_bind(f"icon_{selected_index}", '<Enter>', 
                       lambda e, i=selected_index: enlarge_icon(e, i))
        canvas.tag_bind(f"icon_{selected_index}", '<Leave>', 
                       lambda e, i=selected_index: reset_icon(e, i))
    
    # 更新選中的索引
    selected_index = index
    
    # 放大新選中的圖標
    new_icon = canvas.find_withtag(f"icon_{index}")[0]
    canvas.itemconfig(new_icon, image=icon_states[index]['enlarged'])
    
    # 解除新選中圖標的懸停效果
    canvas.tag_unbind(f"icon_{index}", '<Enter>')
    canvas.tag_unbind(f"icon_{index}", '<Leave>')


# 打開項目（根據文件類型）
def open_item(index):
    path, file_type = game_data[index][1], game_data[index][3]
    if file_type == "exe":
        open_game(path)
    elif file_type == "folder":
        open_folder(path)

# 打開遊戲的函數
def open_game(game_path):
    try:
        subprocess.Popen([game_path])
    except Exception as e:
        messagebox.showerror("錯誤", f"無法打開遊戲: {e}")

# 打開文件夾的函數
def open_folder(folder_path):
    try:
        os.startfile(folder_path)
    except Exception as e:
        messagebox.showerror("錯誤", f"無法打開文件夾: {e}")

# 處理文件拖放事件
def on_file_drop(event):
    try:
        file_path = event.data.strip('{}')
        game_name = os.path.splitext(os.path.basename(file_path))[0]
        file_type = "folder" if os.path.isdir(file_path) else "exe" if file_path.endswith('.exe') else "unknown"
        
        # 預設圖標路徑
        default_icon_path = r"C:\Users\jack1\Desktop\assignment\A2\src\屏幕截图 2024-11-06 211618.png"
        
        # 插入遊戲數據到資料庫
        cursor.execute("INSERT INTO games (name, path, icon_path) VALUES (?, ?, ?)", (game_name, file_path, default_icon_path))
        conn.commit()  # 提交變更以確保數據持久化
        print(f"已插入遊戲: {game_name}, 路徑: {file_path}, 圖標: {default_icon_path}")
        
        # 更新內存中的 game_data 並刷新顯示
        game_data.append((game_name, file_path, default_icon_path, file_type))
        display_games()
        
    except Exception as e:
        print(f"添加文件時發生錯誤: {e}")


# 刪除遊戲
def delete_game():
    global selected_index
    if selected_index is not None:
        name, path = game_data[selected_index][0], game_data[selected_index][1]
        cursor.execute("DELETE FROM games WHERE name = ? AND path = ?", (name, path))
        conn.commit()
        game_data.pop(selected_index)
        selected_index = None  # 重置選中項目
        display_games()
    else:
        messagebox.showwarning("警告", "請選擇一個遊戲進行刪除")


def update_game_icon():
    if selected_index is None:
        messagebox.showwarning("警告", "請先選擇要修改圖標的遊戲")
        return
        
    # 打開文件選擇器，限制文件類型為圖片
    file_types = [
        ('PNG files', '*.png'),
        ('JPEG files', '*.jpg;*.jpeg'),
        ('All files', '*.*')
    ]
    new_icon_path = filedialog.askopenfilename(
        title="選擇新的圖標",
        filetypes=file_types
    )
    
    if new_icon_path:  # 確保用戶選擇了文件
        try:
            # 測試是否可以打開圖片
            with Image.open(new_icon_path) as test_image:
                pass
                
            # 更新數據庫中的圖標路徑
            game_name = game_data[selected_index][0]
            game_path = game_data[selected_index][1]
            cursor.execute("""
                UPDATE games 
                SET icon_path = ? 
                WHERE name = ? AND path = ?
            """, (new_icon_path, game_name, game_path))
            conn.commit()
            
            # 更新內存中的遊戲數據
            game_data[selected_index] = (
                game_data[selected_index][0],  # name
                game_data[selected_index][1],  # path
                new_icon_path,                 # new icon_path
                game_data[selected_index][3]   # file_type
            )
            
            # 重新加載並顯示圖標
            display_games()
            messagebox.showinfo("成功", "圖標已成功更新")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"更新圖標時發生錯誤: {e}")

def create_context_menu(event, index):
    # 創建右鍵選單
    context_menu = tk.Menu(root, tearoff=0)
    
    # 將當前點擊的項目設為選中狀態
    select_item(event, index)
    
    # 添加選單項目
    context_menu.add_command(
        label="修改圖標",
        command=update_game_icon
    )
    context_menu.add_command(
        label="刪除遊戲",
        command=delete_game
    )
    
    # 在鼠標位置顯示選單
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        # 設置選單為自動銷毀
        context_menu.grab_release()




# 綁定拖放事件
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_file_drop)

# 加載並顯示遊戲
load_games()

# 運行主循環
root.mainloop()

# 關閉資料庫連接
conn.close()
