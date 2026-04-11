def _run() -> None:
    from main.prelaunch import prepare_prelaunch

    prepare_prelaunch()
    from main.entry import main as run_main

    run_main()


if __name__ == "__main__":
    _run()
