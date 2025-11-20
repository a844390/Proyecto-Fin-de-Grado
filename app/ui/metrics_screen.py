def show_metrics_screen(cpu_layout, metrics=None):
    print("\n=== CPU Metrics ===")
    
    print("Core layout:")
    for core in cpu_layout:
        print(f" - {core['id']}: {core['type']}")

    if metrics:
        print("\nReal-time metrics:")
        for key, val in metrics.items():
            print(f"{key}: {val}")

    input("\nPress Enter to return to menu...")
