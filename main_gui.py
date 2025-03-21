import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_URL = "http://127.0.0.1:8000"  # адрес нашего FastAPI


def fetch_tasks():
    """Запрос задач с сервера."""
    try:
        response = requests.get(f"{API_URL}/tasks/")
        response.raise_for_status()
        tasks = response.json().get("tasks", [])
        return tasks
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось получить задачи:\n{e}")
        return []


def refresh_task_list():
    """Обновление списка задач в таблице."""
    for row in tree.get_children():
        tree.delete(row)
    tasks = fetch_tasks()
    for task in tasks:
        status = "✅ Да" if task["is_completed"] else "❌ Нет"
        tree.insert("", "end", values=(task["id"], task["title"], status))


def create_task():
    """Создание новой задачи через API."""
    title = title_entry.get().strip()
    description = description_entry.get().strip()

    if not title:
        messagebox.showwarning("Ошибка", "Название задачи не может быть пустым!")
        return

    task_data = {"title": title, "description": description}

    try:
        response = requests.post(f"{API_URL}/tasks/", json=task_data)
        response.raise_for_status()
        messagebox.showinfo("Успех", "Задача успешно добавлена!")
        refresh_task_list()
        title_entry.delete(0, tk.END)
        description_entry.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать задачу:\n{e}")


# --- GUI ---
root = tk.Tk()
root.title("To-Do List GUI")
root.geometry("700x450")

# Фрейм для формы создания задач
input_frame = tk.Frame(root)
input_frame.pack(pady=10, padx=10, fill="x")

tk.Label(input_frame, text="Название задачи:").pack(anchor="w")
title_entry = tk.Entry(input_frame, width=50)
title_entry.pack(fill="x", padx=5, pady=2)

tk.Label(input_frame, text="Описание (необязательно):").pack(anchor="w")
description_entry = tk.Entry(input_frame, width=50)
description_entry.pack(fill="x", padx=5, pady=2)

add_task_btn = tk.Button(input_frame, text="Создать задачу", command=create_task)
add_task_btn.pack(pady=5)

# Создаем таблицу
tree = ttk.Treeview(root, columns=("ID", "Название", "Выполнено"), show="headings")

# Настраиваем заголовки и ширину
tree.heading("ID", text="ID")
tree.heading("Название", text="Заголовок")
tree.heading("Выполнено", text="Статус")

tree.column("ID", width=50, anchor="center")
tree.column("Название", width=400, anchor="center")
tree.column("Выполнено", width=100, anchor="center")

tree.pack(fill="both", expand=True, padx=10, pady=10)

# Кнопка обновления
refresh_btn = tk.Button(root, text="Обновить список", command=refresh_task_list)
refresh_btn.pack(pady=5)

refresh_task_list()
root.mainloop()
