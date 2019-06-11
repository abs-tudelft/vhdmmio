from vhdmmio import VhdMmio, RunComplete

if __name__ == '__main__':
    try:
        VhdMmio().run()
    except RunComplete as exc:
        sys.exit(exc.code)
    # TODO: exception pretty-printing
