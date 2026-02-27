import tkinter as tk
from tkinter import ttk


# --- Layout definition (same as your PowerShell script) ---
CORE_LAYOUT = [
    {"id": 0, "type": "P", "x": 20,  "y": 20},
    {"id": 1, "type": "P", "x": 220, "y": 20},
    {"id": 2, "type": "E", "x": 225, "y": 70},
    {"id": 3, "type": "E", "x": 305, "y": 70},
    {"id": 4, "type": "E", "x": 225, "y": 120},
    {"id": 5, "type": "E", "x": 305, "y": 120},
    {"id": 6, "type": "P", "x": 20,  "y": 170},
    {"id": 7, "type": "P", "x": 220, "y": 170},
    {"id": 8, "type": "P", "x": 20,  "y": 220},
    {"id": 9, "type": "P", "x": 220, "y": 220},
    {"id": 10,"type": "E", "x": 25,  "y": 270},
    {"id": 11,"type": "E", "x": 105, "y": 270},
    {"id": 12,"type": "E", "x": 25,  "y": 320},
    {"id": 13,"type": "E", "x": 105, "y": 320},
    {"id": 14,"type": "E", "x": 225, "y": 270},
    {"id": 15,"type": "E", "x": 305, "y": 270},
    {"id": 16,"type": "E", "x": 225, "y": 320},
    {"id": 17,"type": "E", "x": 305, "y": 320},
    {"id": 18,"type": "P", "x": 20,  "y": 370},
    {"id": 19,"type": "P", "x": 220, "y": 370},
]


import tkinter as tk
from tkinter import messagebox
import psutil

def select_cores_for_process(proc_name):
    try:
        procs = [p for p in psutil.process_iter(['name','pid']) if proc_name.lower() in p.info['name'].lower()]
        if not procs:
            messagebox.showerror("Error", f"No process found with name '{proc_name}'")
            return
        
        if len(procs) > 1:
            pid_list = "\n".join(f"{p.info['pid']} : {p.info['name']}" for p in procs)
            pid_input = input(f"Multiple processes found:\n{pid_list}\nEnter PID: ")
            pid = int(pid_input)
        else:
            pid = procs[0].info['pid']
        
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return
    
    selected_cores = set()
    
    root = tk.Tk()
    root.title("Select Cores")
    root.geometry("420x560")
    root.configure(bg='whitesmoke')

    def toggle_core(core_id, btn):
        if core_id in selected_cores:
            selected_cores.remove(core_id)
            set_core_style(btn, False, CORE_LAYOUT[core_id]['type'])
        else:
            selected_cores.add(core_id)
            set_core_style(btn, True, CORE_LAYOUT[core_id]['type'])

    def set_core_style(btn, selected, core_type):
        if selected:
            btn.configure(bg='pale green', relief='solid', bd=3)
        else:
            if core_type == 'P':
                btn.configure(bg='light sky blue', relief='flat', bd=1)
            else:
                btn.configure(bg='khaki', relief='flat', bd=1)

    for core in CORE_LAYOUT:
        w = 160 if core['type']=='P' else 70
        btn = tk.Button(root, text=f"{core['id']}\n{core['type']}",
                        width=w//10, height=2,
                        command=lambda cid=core['id'], b=None: toggle_core(cid, b))
        btn.place(x=core['x'], y=core['y'])
        # Hack to pass button itself to lambda
        btn.configure(command=lambda cid=core['id'], b=btn: toggle_core(cid, b))
        set_core_style(btn, False, core['type'])

    def apply_affinity():
        if not selected_cores:
            messagebox.showwarning("Warning", "No cores selected")
            return
        try:
            proc = psutil.Process(pid)
            proc.cpu_affinity(list(selected_cores))
            messagebox.showinfo("Success", f"Affinity set for PID {pid} to cores: {sorted(selected_cores)}")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    apply_btn = tk.Button(root, text="Apply and Close", width=40, height=2,
                          bg='light green', command=apply_affinity)
    apply_btn.place(x=20, y=470)

    root.mainloop()
