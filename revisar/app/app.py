from ui.menu import show_main_menu
from ui.metrics_screen import show_metrics_screen
from system.cpu_topology import get_cpu_layout
from system.process_utils import find_pid_by_name
from ui.core_selector import select_cores_for_process
def main():
    while True:
        choice = show_main_menu()

        if choice == "1":
            cpu_layout = get_cpu_layout()
            show_metrics_screen(cpu_layout)

        elif choice == "2":
            print("\n[Potentiometer placeholder]")
            input("Press Enter to return to menu...")

        elif choice == "3":
            name = input("Enter process name: ")
            select_cores_for_process(name)
            

        elif choice == "4":
            print("Exiting.")
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
